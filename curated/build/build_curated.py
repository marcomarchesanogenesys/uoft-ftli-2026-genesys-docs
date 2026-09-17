#!/usr/bin/env python3
"""Build the curated conversation set from the source datasets.

Reads build/manifest.json (a declarative sampler) and writes, per dataset:

    curated/conversations/<ID>.json        redistributable sources (committed)
    curated/conversations-local/<ID>.json  share-alike sources (gitignored)
    curated/CONVERSATIONS.md               index across everything built
    curated/conversations-<dataset>.md     readable rendering, one file per dataset

Output is RAW DATA ONLY, in the shape documented by curated/SCHEMA.md. There is no
commentary, scoring, tagging or interpretation anywhere in it — deliberately, so
readers form their own view of each interaction.

Where a source ships two related fields (e.g. the task assigned to an agent and the
task the agent actually recorded) both are reproduced side by side and left
uncompared.

Requires the datasets locally (they are gitignored; see ATTRIBUTION.md).
Run from the repo root:

    python3 curated/build/build_curated.py
"""

from __future__ import annotations

import ast
import csv
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HVB = ROOT / "01-harper-valley-bank" / "data"
ABCD = ROOT / "02-abcd" / "data" / "abcd_v1.1.json"
TWCS = ROOT / "03-twitter-twcs" / "twcs.csv"
APPTEK = ROOT / "04-apptek" / "diarization"
OUT_JSON = ROOT / "curated" / "conversations"
OUT_LOCAL = ROOT / "curated" / "conversations-local"
OUT_DIR = ROOT / "curated"

SOURCES = {
    "HarperValleyBank": {
        "prefix": "HVB",
        "licence": "CC BY 4.0",
        "url": "https://github.com/cricketclub/gridspace-stanford-harper-valley",
        "citation": "Wu, Nafziger, Scodary & Maas (2020), arXiv:2010.13929",
        "copyright": "Gridspace / Stanford",
        # CC BY 4.0 s.2(a)(1) grants Share of the Licensed Material in whole or in
        # part, subject to the s.3(a) attribution conditions carried in "source".
        "redistributable": True,
    },
    "ABCD": {
        "prefix": "ABCD",
        "licence": "MIT",
        "url": "https://github.com/asappresearch/abcd",
        "citation": "Chen et al. (2021), NAACL, arXiv:2104.00783",
        "copyright": "Copyright (c) 2021 ASAPP Research",
        # MIT grants copy/publish/distribute provided the copyright and permission
        # notice are retained -- see NOTICE in CONVERSATIONS.md.
        "redistributable": True,
    },
    "AppTek": {
        "prefix": "APPTEK",
        "licence": "CC BY-SA 4.0",
        "url": "https://huggingface.co/datasets/apptek-com/apptek_callcenter_dialogues",
        "citation": "AppTek Call-Centre Dialogues, arXiv:2604.27543",
        "copyright": "AppTek",
        # BY-SA requires derivatives stay BY-SA, which conflicts with this repo's
        # CC BY 4.0. No NonCommercial term and the interactions are role-played, so a
        # BY-SA carve-out would be straightforward if we decide to publish these.
        "redistributable": False,
    },
    "twcs": {
        "prefix": "TWCS",
        "licence": "CC BY-NC-SA 4.0",
        "url": "https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter",
        "citation": "Customer Support on Twitter, S. Axelbrooke",
        "copyright": "S. Axelbrooke; underlying posts remain their authors'",
        # Share-alike conflicts with CC BY 4.0, platform terms on republishing post
        # text are unresolved, and excerpts contain personal details of identifiable
        # people. Regenerated locally instead.
        "redistributable": False,
    },
}

csv.field_size_limit(10**9)


def prune(d: dict) -> dict:
    """Drop keys whose value is absent.

    SCHEMA.md contract: a missing key means the dataset does not record this. An
    empty value would wrongly imply the field exists and happened to be blank.
    """
    return {k: v for k, v in d.items() if v not in (None, "", {}, [])}


# ============================================================ HarperValleyBank


def hvb_index() -> list[dict]:
    """One entry per usable conversation: id, stratum, and the loaded records."""
    out = []
    for mp in sorted((HVB / "metadata").glob("*.json")):
        sid = mp.stem
        tp = HVB / "transcript" / f"{sid}.json"
        if not tp.exists():
            continue
        meta = json.loads(mp.read_text(encoding="utf-8"))
        tasks = [t.get("task_type") for t in (meta.get("tasks") or []) if t.get("task_type")]
        if not tasks:
            continue
        segs = [s for s in json.loads(tp.read_text(encoding="utf-8")) if (s.get("human_transcript") or "").strip()]
        if {s["speaker_role"] for s in segs} != {"agent", "caller"}:
            continue
        aid = (meta.get("agent") or {}).get("speaker_id")
        out.append(
            {
                "original_id": sid,
                "stratum": tasks[0],
                "n_turns": len(segs),
                # speaker_id, NOT agent_name: 52 of 58 speakers appear under multiple
                # display names in this corpus, so the name is not an identity.
                "agent": f"hvb-speaker-{aid}" if aid is not None else None,
            }
        )
    return out


def hvb_load(sid: str) -> dict:
    meta = json.loads((HVB / "metadata" / f"{sid}.json").read_text(encoding="utf-8"))
    segs = json.loads((HVB / "transcript" / f"{sid}.json").read_text(encoding="utf-8"))
    agent = meta.get("agent") or {}
    caller = meta.get("caller") or {}

    turns = []
    for s in segs:
        text = (s.get("human_transcript") or "").strip()
        if not text:
            continue
        turns.append(
            prune(
                {
                    "n": s["index"],
                    "speaker": "agent" if s["speaker_role"] == "agent" else "customer",
                    "text": text,
                    "asr_text": (s.get("transcript") or "").strip(),
                    "start_ms": s.get("start_ms"),
                    "duration_ms": s.get("duration_ms"),
                    "dialog_acts": [
                        a.replace("gridspace_", "") for a in (s.get("dialog_acts") or [])
                    ],
                }
            )
        )

    # customer_record: a WRITE -- what the agent entered as a result of the call.
    captured = {}
    for r in agent.get("responses") or []:
        captured.update(r.get("data") or {})
    captured.pop("task_type", None)  # kept in source_fields as task_logged_by_agent

    return {
        "channel": "voice",
        "agent_id": f"hvb-speaker-{agent.get('speaker_id')}",
        "customer_id": f"hvb-speaker-{caller.get('speaker_id')}",
        "customer_record": prune(
            {
                "customer_name": (caller.get("metadata") or {}).get("first and last name"),
                "captured_by_agent": captured,
            }
        ),
        "turns": turns,
        "source_fields": prune(
            {
                "task_assigned": [t.get("task_type") for t in (meta.get("tasks") or [])],
                "task_logged_by_agent": [
                    (r.get("data") or {}).get("task_type")
                    for r in (agent.get("responses") or [])
                    if (r.get("data") or {}).get("task_type")
                ],
                "labels": meta.get("labels") or {},
                "session": meta.get("session"),
                "agent_survey_response": (agent.get("survey_response") or {}).get("data"),
                "customer_survey_response": (caller.get("survey_response") or {}).get("data"),
            }
        ),
    }


# ============================================================ ABCD

_ABCD_CACHE: dict[str, dict] = {}


def _abcd_all() -> dict[str, dict]:
    if not _ABCD_CACHE:
        for split in json.loads(ABCD.read_text(encoding="utf-8")).values():
            for c in split:
                _ABCD_CACHE[str(c["convo_id"])] = c
    return _ABCD_CACHE


def abcd_index() -> list[dict]:
    out = []
    for cid, c in _abcd_all().items():
        sp = {s for s, _ in c["original"]}
        if not {"agent", "customer"} <= sp:
            continue
        out.append(
            {
                "original_id": cid,
                "stratum": c["scenario"]["flow"],
                "n_turns": len(c["original"]),
                "agent": None,  # ABCD carries no agent identity of any kind
            }
        )
    return out


def abcd_load(cid: str) -> dict:
    c = _abcd_all()[str(cid)]
    sc = c["scenario"]
    per = sc.get("personal") or {}
    order = sc.get("order") or {}

    # The source stores products as a Python-repr string; parse to real JSON.
    # Values unchanged -- this is the one formatting liberty in the set.
    try:
        prods = ast.literal_eval(order.get("products") or "[]")
    except (ValueError, SyntaxError):
        prods = []

    turns = [
        {
            "n": n,
            # ABCD interleaves the agent's system actions as a third speaker
            "speaker": "system_action" if sp == "action" else sp,
            "text": t.strip(),
        }
        for n, (sp, t) in enumerate(c["original"], 1)
    ]

    # customer_record: a READ -- the record existed before the call and the agent
    # looks it up.
    return {
        "channel": "chat",
        "agent_id": None,  # ABCD carries no agent identity
        "customer_id": per.get("username"),
        "customer_record": prune(
            {
                "customer_name": per.get("customer_name"),
                "username": per.get("username"),
                "email": per.get("email"),
                "phone": per.get("phone"),
                "member_level": per.get("member_level"),
                "address": prune(
                    {
                        "street": order.get("street_address"),
                        "city": order.get("city"),
                        "state": order.get("state"),
                        "zip_code": order.get("zip_code"),
                        "full_address": order.get("full_address"),
                    }
                ),
                "order": prune(
                    {
                        "order_id": order.get("order_id"),
                        "purchase_date": order.get("purchase_date"),
                        "payment_method": order.get("payment_method"),
                        "packaging": order.get("packaging"),
                        "num_products": order.get("num_products"),
                        "products": [
                            prune(
                                {
                                    "brand": p.get("brand"),
                                    "product_type": p.get("product_type"),
                                    "amount": p.get("amount"),
                                }
                            )
                            for p in prods
                        ],
                    }
                ),
            }
        ),
        "turns": turns,
        "source_fields": prune(
            {
                "flow": sc.get("flow"),
                "subflow": sc.get("subflow"),
                "actions_taken": [
                    t["targets"][2]
                    for t in c["delexed"]
                    if (t.get("targets") or [None, None, None])[2]
                ],
            }
        ),
    }


# ============================================================ AppTek

_APPTEK_CACHE: dict[str, dict] = {}


def _apptek_all() -> dict[str, dict]:
    if not _APPTEK_CACHE:
        for mp in sorted(APPTEK.glob("*/metadata.jsonl")):
            for line in mp.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                c = json.loads(line)
                stem = Path(c["file_name"]).stem
                _APPTEK_CACHE[stem] = c
    return _APPTEK_CACHE


def apptek_index() -> list[dict]:
    out = []
    for stem, c in _apptek_all().items():
        segs = c["segments"]
        if {"agent", "customer"} - {s["role"] for s in segs}:
            continue
        agents = sorted({s["speaker_id"] for s in segs if s["role"] == "agent"})
        out.append(
            {
                "original_id": stem,
                "stratum": c["domain"],
                "n_turns": len(segs),
                "agent": agents[0] if len(agents) == 1 else None,
            }
        )
    return out


def apptek_load(stem: str) -> dict:
    c = _apptek_all()[stem]
    # Segments are time-stamped and may OVERLAP across speakers. Ordered by start
    # time; start_s/end_s preserved so overlap stays visible rather than flattened.
    segs = sorted(c["segments"], key=lambda x: (x["start"], x["end"]))
    turns = [
        {
            "n": n,
            "speaker": sg["role"],
            "text": sg["text"].strip(),
            "start_s": sg["start"],
            "end_s": sg["end"],
            "speaker_id": sg["speaker_id"],
        }
        for n, sg in enumerate(segs, 1)
    ]
    agents = sorted({s["speaker_id"] for s in segs if s["role"] == "agent"})
    return {
        "channel": "voice",
        "agent_id": agents[0] if len(agents) == 1 else (agents or None),
        "customer_id": next(
            (s["speaker_id"] for s in segs if s["role"] == "customer"), None
        ),
        "customer_record": {},  # AppTek records no customer data
        "turns": turns,
        "source_fields": prune(
            {
                "duration_s": c.get("duration"),
                "domain": c.get("domain"),
                "accent": c.get("accent"),
                "agent_gender": next(
                    (s["gender"] for s in segs if s["role"] == "agent"), None
                ),
                "customer_gender": next(
                    (s["gender"] for s in segs if s["role"] == "customer"), None
                ),
            }
        ),
    }


# ============================================================ twcs

TWCS_SIG = re.compile(r"\^\s*([A-Za-z]{2,3})\s*$")
_TWCS_THREADS: dict[str, dict] | None = None


def _twcs_build_threads() -> dict[str, dict]:
    """Index every signed-agent thread in ONE pass over the 493 MB file.

    The naive approach (two passes per conversation) would mean 200 passes for 100
    conversations. This loads only the rows belonging to brand replies that carry an
    agent sign-off, plus their parents, then reconstructs threads in memory.
    """
    global _TWCS_THREADS
    if _TWCS_THREADS is not None:
        return _TWCS_THREADS

    rows: dict[str, dict] = {}
    parent_of: dict[str, str] = {}
    signed: list[str] = []

    with TWCS.open(newline="", encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            tid = r["tweet_id"]
            rows[tid] = {
                "author": r["author_id"],
                "inbound": r["inbound"] == "True",
                "created_at": r["created_at"],
                "text": r["text"] or "",
                "parent": (r["in_response_to_tweet_id"] or "").strip(),
                "child": (r["response_tweet_id"] or "").split(",")[0].strip(),
            }
            if r["in_response_to_tweet_id"]:
                parent_of[tid] = r["in_response_to_tweet_id"].strip()
            if r["inbound"] == "False" and TWCS_SIG.search((r["text"] or "").strip()):
                signed.append(tid)

    threads: dict[str, dict] = {}
    for tid in signed:
        # walk to the thread root
        root, d = tid, 0
        while root in parent_of and parent_of[root] in rows and d < 12:
            root = parent_of[root]
            d += 1
        if root in threads:
            continue
        chain, cur = [], root
        while cur in rows and len(chain) < 12:
            chain.append((cur, rows[cur]))
            nxt = rows[cur]["child"]
            cur = nxt if nxt in rows else None
        if len(chain) < 3:
            continue
        brand = next((r["author"] for _, r in chain if not r["inbound"]), None)
        sig = None
        for _, r in chain:
            m = TWCS_SIG.search(r["text"].strip())
            if m and not r["inbound"]:
                sig = m.group(1)
                break
        if not brand or not sig:
            continue
        threads[root] = {"chain": chain, "brand": brand, "signoff": sig}

    _TWCS_THREADS = threads
    return threads


def twcs_index() -> list[dict]:
    return [
        {
            "original_id": root,
            "stratum": t["brand"],
            "n_turns": len(t["chain"]),
            "agent": f"twcs-{t['brand']}-{t['signoff']}",
        }
        for root, t in _twcs_build_threads().items()
    ]


def twcs_load(root: str) -> dict:
    t = _twcs_build_threads()[root]
    turns = []
    for i, (_, r) in enumerate(t["chain"], 1):
        # @handle prefix and ^XX sign-off stripped for readability; the sign-off is
        # preserved in source_fields.agent_signoff
        txt = TWCS_SIG.sub("", re.sub(r"^@\S+\s*", "", r["text"])).strip()
        turns.append(
            {
                "n": i,
                "speaker": "customer" if r["inbound"] else "agent",
                "text": txt,
                "sent_at": r["created_at"],
            }
        )
    return {
        "channel": "social",
        "agent_id": f"twcs-{t['brand']}-{t['signoff']}",
        "customer_id": None,  # twcs customer ids are anonymised integers
        "customer_record": {},  # twcs records no customer data
        "turns": turns,
        "source_fields": {"brand": t["brand"], "agent_signoff": f"^{t['signoff']}"},
    }


# ============================================================ registry

DATASETS = {
    "HarperValleyBank": (hvb_index, hvb_load, HVB),
    "ABCD": (abcd_index, abcd_load, ABCD),
    "AppTek": (apptek_index, apptek_load, APPTEK),
    "twcs": (twcs_index, twcs_load, TWCS),
}


def agent_volume_sample(
    pool: list[dict], count: int, cap: int
) -> tuple[list[dict], list[tuple]]:
    """Take the busiest agents, up to `cap` conversations each, until `count`.

    Ranks agents by how many conversations they have and works down that order,
    taking at most `cap` from each. The cap is what makes the set usable in both
    directions at once: without it, per-agent volume is skewed enough that the top
    one or two agents swallow the entire budget (one twcs agent alone has 1,954
    threads), leaving too few agents to compare.

    At cap 10 every dataset yields ~10 agents with ~10 conversations each -- enough
    depth to see a trend within one agent, enough breadth to see that agents differ.

    Deterministic -- no RNG. Agents tie-break on id and conversations are taken in
    id order, so the same pool always yields the same set.
    """
    by_agent: dict[str, list[dict]] = defaultdict(list)
    for item in pool:
        if item.get("agent"):
            by_agent[item["agent"]].append(item)

    # busiest first; agent id breaks ties so the ordering is stable
    ranked = sorted(by_agent.items(), key=lambda kv: (-len(kv[1]), kv[0]))

    picked: list[dict] = []
    used: list[tuple] = []
    for agent, convos in ranked:
        if len(picked) >= count:
            break
        convos.sort(key=lambda x: x["original_id"])
        take = convos[:cap]
        picked.extend(take)
        used.append((agent, len(take), len(convos)))
    return picked, used


def stratified_sample(pool: list[dict], count: int, rng: random.Random) -> list[dict]:
    """Spread `count` picks as evenly as possible across strata.

    Strata are interaction TYPES (task / flow / domain / brand) -- never anything
    about how the interaction went -- so coverage is guaranteed without selecting
    for quality.
    """
    buckets: dict[str, list[dict]] = defaultdict(list)
    for item in pool:
        buckets[item["stratum"]].append(item)
    for b in buckets.values():
        b.sort(key=lambda x: x["original_id"])  # deterministic before shuffling
        rng.shuffle(b)

    picked: list[dict] = []
    keys = sorted(buckets)
    while len(picked) < count and any(buckets[k] for k in keys):
        for k in keys:
            if len(picked) >= count:
                break
            if buckets[k]:
                picked.append(buckets[k].pop())
    return picked


# ============================================================ rendering


def render_dataset(ds: str, convos: list[dict]) -> str:
    meta = SOURCES[ds]
    L = [f"# Curated Conversations — {ds}\n"]
    L.append(
        f"{len(convos)} interactions from **{ds}** ({meta['licence']}). Generated by "
        "`curated/build/build_curated.py` — **do not edit by hand.**\n"
    )
    L.append(
        "Raw data, without commentary or scoring. No conversation here is labelled good "
        "or bad and nothing is flagged for your attention. See `curated/SCHEMA.md` for "
        "the field reference.\n"
    )
    L.append("| ID | Turns | Agent | " + ("Customer record | " if any(c.get("customer_record") for c in convos) else "") + "Source id |")
    L.append("|---|---|---|" + ("---|" if any(c.get("customer_record") for c in convos) else "") + "---|")
    for c in convos:
        row = f"| [`{c['id']}`](#{c['id'].lower()}) | {len(c['turns'])} | `{c.get('agent_id') or '—'}` | "
        if any(x.get("customer_record") for x in convos):
            row += ("yes | " if c.get("customer_record") else "— | ")
        row += f"`{c['source']['original_id']}` |"
        L.append(row)
    L.append("")

    for c in convos:
        L.append("---\n")
        L.append(f"## {c['id']}\n")
        L.append(f"- **Channel** {c['channel']} · **Turns** {len(c['turns'])}")
        L.append(
            f"- **Source** {ds} `{c['source']['original_id']}` — {c['source']['licence']}"
        )
        if c.get("agent_id"):
            L.append(f"- **Agent** `{c['agent_id']}`")
        mods = c.get("modifications") or []
        L.append(
            f"- **Modified** {'yes — ' + '; '.join(mods) if mods else 'no (verbatim from source)'}\n"
        )

        if c.get("customer_record"):
            L.append("### Customer record\n")
            L.append("```json")
            L.append(json.dumps(c["customer_record"], indent=2, ensure_ascii=False))
            L.append("```\n")

        L.append("### Transcript\n")
        for t in c["turns"]:
            if t["speaker"] == "system_action":
                L.append(f"{t['n']}. *(system: {t['text']})*")
                continue
            who = "**Agent**" if t["speaker"] == "agent" else "Customer"
            stamp = ""
            if t.get("start_s") is not None:
                stamp = f"  <sub>{t['start_s']:.1f}–{t['end_s']:.1f}s</sub>"
            L.append(f"{t['n']}. {who}: {t['text']}{stamp}")
        L.append("")

        if c.get("source_fields"):
            L.append("### Source fields\n")
            L.append("_Reproduced from the dataset as-is._\n")
            for k, v in c["source_fields"].items():
                L.append(f"- `{k}`: {v}")
            L.append("")

    L.append("---\n")
    L.append("## NOTICE — required attribution\n")
    L.append(f"**{ds}** — {meta['licence']}")
    L.append(f"- {meta['copyright']}")
    L.append(f"- {meta['citation']}")
    L.append(f"- {meta['url']}")
    L.append(
        "- Excerpts here are unmodified transcripts restructured into JSON; any "
        "alteration to an interaction is recorded in its `modifications` field.\n"
    )
    return "\n".join(L) + "\n"


def render_index(
    by_ds: dict[str, list[dict]],
    agent_counts: dict[str, list[tuple]],
    skipped: list[str] | None = None,
) -> str:
    L = ["# Curated Conversations\n"]
    total = sum(len(v) for v in by_ds.values())
    L.append(
        f"{total} real customer-service interactions across {len(by_ds)} datasets, all in "
        "the same schema — see `curated/SCHEMA.md`. Pick whichever source suits what you "
        "want to build.\n"
    )
    L.append(
        "Raw data only: no commentary, scoring or tagging anywhere in the set. "
        "Generated by `curated/build/build_curated.py` — **do not edit by hand.**\n"
    )
    if skipped:
        L.append(
            "> Built without " + ", ".join(f"**{d}**" for d in skipped) + " — not "
            "downloaded. Run `python3 scripts/download_data.py --all`, then rebuild.\n"
        )
    L.append("| Dataset | Count | Channel | Licence | Committed | Readable rendering |")
    L.append("|---|---|---|---|---|---|")
    for ds, convos in by_ds.items():
        m = SOURCES[ds]
        ch = convos[0]["channel"] if convos else "—"
        com = "yes" if m["redistributable"] else "local only"
        L.append(
            f"| {ds} | {len(convos)} | {ch} | {m['licence']} | {com} | "
            f"[`conversations-{ds.lower()}.md`](conversations-{ds.lower()}.md) |"
        )
    L.append("")
    L.append(
        "**Committed** means the source licence permits redistribution, so the JSON is "
        "in `conversations/` in this repo. *Local only* means share-alike terms conflict "
        "with this repository's CC BY 4.0, so those land in `conversations-local/` "
        "(gitignored) — run the build yourself after downloading the sources.\n"
    )
    L.append("## What each dataset gives you\n")
    L.append("| | Agent id | Customer record | Per-turn timing | Gold + machine transcript | Real dates |")
    L.append("|---|---|---|---|---|---|")
    L.append("| HarperValleyBank | yes | yes (write) | milliseconds | **yes** | 4 days only |")
    L.append("| ABCD | no | yes (read) | no | no | no |")
    L.append("| AppTek | yes | no | seconds | no | no |")
    L.append("| twcs | ~35% | no | message timestamps | no | **yes, 3 months** |")
    L.append("")

    if agent_counts:
        L.append("## Conversations per agent\n")
        L.append(
            "Selected by agent volume: the busiest agents, up to 10 conversations each. "
            "Enough per agent to look at one person's conversations together, and enough "
            "agents to compare. *Available* is how many that agent has in the full "
            "dataset — raise `max_per_agent` in "
            "`build/manifest.json` to pull more.\n"
        )
        for ds, used in agent_counts.items():
            local = "" if SOURCES[ds]["redistributable"] else " — local only"
            L.append(f"**{ds}**{local}\n")
            L.append("| Agent | In this set | Available |")
            L.append("|---|---|---|")
            for agent, n, avail in used:
                L.append(f"| `{agent}` | {n} | {avail} |")
            L.append("")
        if "ABCD" in by_ds:
            L.append(
                "**ABCD** records no agent identity, so it is selected by flow instead "
                "and cannot be grouped by agent at all.\n"
            )
        L.append(
            "Two limits worth knowing before building anything longitudinal: "
            "HarperValleyBank spans **4 days** and AppTek has **no dates**, so a run of "
            "conversations there is a sequence, not a timeline. **twcs is the only "
            "source with real dates** (3 months).\n"
        )

    return "\n".join(L) + "\n"


# ============================================================ main


def main() -> int:
    manifest = json.loads((Path(__file__).parent / "manifest.json").read_text(encoding="utf-8"))
    rng = random.Random(manifest.get("seed", 0))

    # Build whatever is present. A student without Kaggle credentials has no twcs,
    # and that must not stop the other three from building.
    specs, skipped = [], []
    for spec in manifest["samples"]:
        _, _, path = DATASETS[spec["dataset"]]
        (specs if path.exists() else skipped).append(spec)

    if skipped:
        print("Skipping datasets that are not downloaded:")
        for spec in skipped:
            _, _, path = DATASETS[spec["dataset"]]
            try:
                where = path.relative_to(ROOT)
            except ValueError:
                where = path
            print(f"  {spec['dataset']:<18} expected at {where}")
        print("  Run: python3 scripts/download_data.py --all\n")

    if not specs:
        print(
            "ERROR: no datasets found. Datasets are gitignored — run\n"
            "  python3 scripts/download_data.py\n"
            "See ATTRIBUTION.md for licences.",
            file=sys.stderr,
        )
        return 2

    OUT_JSON.mkdir(parents=True, exist_ok=True)
    OUT_LOCAL.mkdir(parents=True, exist_ok=True)
    for old in list(OUT_JSON.glob("*.json")) + list(OUT_LOCAL.glob("*.json")):
        old.unlink()

    by_ds: dict[str, list[dict]] = {}
    agent_counts: dict[str, list[tuple]] = {}

    for spec in specs:
        ds = spec["dataset"]
        index_fn, load_fn, _ = DATASETS[ds]
        meta = SOURCES[ds]
        print(f"\n{ds}")
        print("  indexing ...")
        pool = index_fn()
        lo, hi = spec.get("min_turns", 1), spec.get("max_turns", 10**6)
        pool = [p for p in pool if lo <= p["n_turns"] <= hi]
        print(f"  {len(pool)} conversations pass the structural filter "
              f"({lo}-{hi} turns), {len({p['stratum'] for p in pool})} strata")

        strategy = spec.get("strategy", "stratified")
        if strategy == "agent_volume" and not any(p.get("agent") for p in pool):
            print("  NOTE: this dataset has no agent identity — "
                  "falling back to stratified sampling")
            strategy = "stratified"

        if strategy == "agent_volume":
            cap = spec.get("max_per_agent", 10)
            picked, used = agent_volume_sample(pool, spec["count"], cap)
            tot_agents = len({p["agent"] for p in pool if p.get("agent")})
            print(f"  {tot_agents} agents in pool; took the {len(used)} busiest, "
                  f"max {cap} each")
            for agent, n, avail in used:
                print(f"      {agent:<34} {n:>3} taken  ({avail} available)")
            agent_counts[ds] = used
            picked.sort(key=lambda x: (x["agent"], x["original_id"]))
        else:
            picked = stratified_sample(pool, spec["count"], rng)
            picked.sort(key=lambda x: (x["stratum"], x["original_id"]))
        if len(picked) < spec["count"]:
            print(f"  NOTE: only {len(picked)} available, asked for {spec['count']}")
        convos = []
        for i, item in enumerate(picked, 1):
            core = load_fn(item["original_id"])
            convo = prune(
                {
                    "id": f"{meta['prefix']}-{i:04d}",
                    "source": {
                        "dataset": ds,
                        "original_id": item["original_id"],
                        "licence": meta["licence"],
                        "url": meta["url"],
                        "citation": meta["citation"],
                    },
                    "modifications": [],
                    "channel": core["channel"],
                    "agent_id": core.get("agent_id"),
                    "customer_id": core.get("customer_id"),
                    "customer_record": core.get("customer_record"),
                    "turns": core["turns"],
                    "source_fields": core.get("source_fields"),
                }
            )
            convo.setdefault("modifications", [])  # required key, [] is meaningful
            target = OUT_JSON if meta["redistributable"] else OUT_LOCAL
            with (target / f"{convo['id']}.json").open(
                "w", encoding="utf-8", newline="\n"
            ) as fh:
                fh.write(json.dumps(convo, indent=2, ensure_ascii=False) + "\n")
            convos.append(convo)

        by_ds[ds] = convos
        where = "conversations/" if meta["redistributable"] else "conversations-local/ (not committed)"
        print(f"  wrote {len(convos)} -> {where}")

        md = OUT_DIR / f"conversations-{ds.lower()}.md"
        if meta["redistributable"]:
            with md.open("w", encoding="utf-8", newline="\n") as fh:
                fh.write(render_dataset(ds, convos))
            print(f"  wrote rendering -> {md.name}")
        else:
            if md.exists():
                md.unlink()

    with (OUT_DIR / "CONVERSATIONS.md").open(
        "w", encoding="utf-8", newline="\n"
    ) as fh:
        fh.write(render_index(by_ds, agent_counts, [s["dataset"] for s in skipped]))
    total = sum(len(v) for v in by_ds.values())
    print(f"\n{'-' * 62}")
    print(f"{total} conversations across {len(by_ds)} datasets")
    print(f"index -> curated/CONVERSATIONS.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
