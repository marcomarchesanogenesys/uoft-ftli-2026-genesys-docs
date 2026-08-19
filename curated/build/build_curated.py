#!/usr/bin/env python3
"""Build the curated conversation set from the source datasets.

Reads build/manifest.json (a selection list) and writes:

    curated/conversations/<ID>.json    one file per conversation (canonical)
    curated/CONVERSATIONS.md           human-readable rendering of all of them

Output is RAW DATA ONLY. Turns and fields come straight from the source corpora.
There is no commentary, scoring, tagging or interpretation anywhere in the output
-- deliberately, so that readers form their own view of each interaction.

Where the source ships two related fields (e.g. the task assigned to an agent and
the task the agent actually logged) both are reproduced side by side and left
uncompared. Derived judgements are the reader's to make.

Requires the datasets locally (they are gitignored; see ATTRIBUTION.md).
Run from the repo root:

    python3 curated/build/build_curated.py
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HVB = ROOT / "01-harper-valley-bank" / "data"
ABCD = ROOT / "02-abcd" / "data" / "abcd_v1.1.json"
TWCS = ROOT / "03-twitter-twcs" / "twcs.csv"
APPTEK = ROOT / "04-apptek" / "diarization"
OUT_JSON = ROOT / "curated" / "conversations"
OUT_LOCAL = ROOT / "curated" / "conversations-local"
OUT_MD = ROOT / "curated" / "CONVERSATIONS.md"

SOURCES = {
    "HarperValleyBank": {
        "licence": "CC BY 4.0",
        "url": "https://github.com/cricketclub/gridspace-stanford-harper-valley",
        "citation": "Wu, Nafziger, Scodary & Maas (2020), arXiv:2010.13929",
        "copyright": "Gridspace / Stanford",
        # CC BY 4.0 s.2(a)(1) grants Share of the Licensed Material in whole or in
        # part, subject to the s.3(a) attribution conditions carried in "source".
        "redistributable": True,
    },
    "ABCD": {
        "licence": "MIT",
        "url": "https://github.com/asappresearch/abcd",
        "citation": "Chen et al. (2021), NAACL, arXiv:2104.00783",
        "copyright": "Copyright (c) 2021 ASAPP Research",
        # MIT grants copy/publish/distribute provided the copyright and permission
        # notice are retained -- see NOTICE in CONVERSATIONS.md.
        "redistributable": True,
    },
    "AppTek": {
        "licence": "CC BY-SA 4.0",
        "url": "https://huggingface.co/datasets/apptek-com/apptek_callcenter_dialogues",
        "citation": "AppTek Call-Centre Dialogues, arXiv:2604.27543",
        "copyright": "AppTek",
        # NOT committed by default. BY-SA permits redistribution but requires
        # derivatives stay BY-SA, which conflicts with this repo's CC BY 4.0.
        # Unlike twcs there is no NonCommercial term and the interactions are
        # role-played (no real customer data), so a BY-SA carve-out for these
        # files would be straightforward if we decide to publish them.
        "redistributable": False,
    },
    "twcs": {
        "licence": "CC BY-NC-SA 4.0",
        "url": "https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter",
        "citation": "Customer Support on Twitter, S. Axelbrooke",
        "copyright": "S. Axelbrooke; underlying posts remain their authors'",
        # NOT committed. CC BY-NC-SA would permit redistribution only under
        # BY-NC-SA (conflicting with this repo's CC BY 4.0), the platform terms on
        # republishing post text are unresolved, and the excerpts contain personal
        # details of identifiable people. Regenerated locally instead.
        "redistributable": False,
    },
}

csv.field_size_limit(10**9)


# ---------------------------------------------------------------- extractors


def load_harper_valley(sid: str) -> dict:
    meta = json.loads((HVB / "metadata" / f"{sid}.json").read_text())
    segs = json.loads((HVB / "transcript" / f"{sid}.json").read_text())
    agent = meta.get("agent") or {}
    caller = meta.get("caller") or {}

    turns = []
    for s in segs:
        text = (s.get("human_transcript") or "").strip()
        if not text:
            continue
        turns.append(
            {
                "n": s["index"],
                "speaker": "agent" if s["speaker_role"] == "agent" else "customer",
                "text": text,
                "asr_text": (s.get("transcript") or "").strip() or None,
                "start_ms": s.get("start_ms"),
                "duration_ms": s.get("duration_ms"),
                "dialog_acts": [a.replace("gridspace_", "") for a in (s.get("dialog_acts") or [])],
            }
        )

    return {
        "channel": "voice",
        "agent_id": f"hvb-speaker-{agent.get('speaker_id')}",
        "customer_id": f"hvb-speaker-{caller.get('speaker_id')}",
        "turns": turns,
        # Source fields, reproduced as-is. Not compared.
        "source_fields": {
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
        },
    }


def load_abcd(convo_id: str, _cache: dict = {}) -> dict:
    if not _cache:
        for split in json.loads(ABCD.read_text()).values():
            for c in split:
                _cache[str(c["convo_id"])] = c
    c = _cache[str(convo_id)]

    turns = []
    for n, (speaker, text) in enumerate(c["original"], 1):
        turns.append(
            {
                "n": n,
                # ABCD interleaves the agent's system actions as a third speaker
                "speaker": "system_action" if speaker == "action" else speaker,
                "text": text.strip(),
            }
        )

    return {
        "channel": "chat",
        "agent_id": None,  # ABCD carries no agent identity
        "customer_id": None,
        "turns": turns,
        "source_fields": {
            "flow": c["scenario"]["flow"],
            "subflow": c["scenario"]["subflow"],
            "actions_taken": [
                t["targets"][2]
                for t in c["delexed"]
                if (t.get("targets") or [None, None, None])[2]
            ],
            "scenario_order": c["scenario"].get("order"),
            "scenario_product": c["scenario"].get("product"),
        },
    }


def load_apptek(stem: str) -> dict:
    """Load one AppTek conversation from the diarization split.

    Segments are time-stamped and may OVERLAP across speakers -- 17% of adjacent
    cross-role pairs do. Turns are ordered by start time and `start_s`/`end_s` are
    preserved so that overlap stays visible rather than being flattened away.
    """
    target = f"audio/{stem}.wav"
    for mp in sorted(APPTEK.glob("*/metadata.jsonl")):
        for line in mp.read_text().splitlines():
            if not line.strip():
                continue
            c = json.loads(line)
            if c["file_name"] != target:
                continue

            segs = sorted(c["segments"], key=lambda x: (x["start"], x["end"]))
            turns = []
            for n, sg in enumerate(segs, 1):
                turns.append(
                    {
                        "n": n,
                        "speaker": sg["role"],  # agent | customer
                        "text": sg["text"].strip(),
                        "start_s": sg["start"],
                        "end_s": sg["end"],
                        "speaker_id": sg["speaker_id"],
                    }
                )

            agent_ids = sorted({sg["speaker_id"] for sg in segs if sg["role"] == "agent"})
            return {
                "channel": "voice",
                "agent_id": agent_ids[0] if len(agent_ids) == 1 else (agent_ids or None),
                "customer_id": next(
                    (sg["speaker_id"] for sg in segs if sg["role"] == "customer"), None
                ),
                "turns": turns,
                "source_fields": {
                    "duration_s": c["duration"],
                    "domain": c["domain"],
                    "accent": c["accent"],
                    "agent_gender": next(
                        (sg["gender"] for sg in segs if sg["role"] == "agent"), None
                    ),
                    "customer_gender": next(
                        (sg["gender"] for sg in segs if sg["role"] == "customer"), None
                    ),
                },
            }
    raise SystemExit(f"AppTek: no conversation named {target!r}")


TWCS_SIG = re.compile(r"\^\s*([A-Za-z]{2,3})\s*$")


def load_twcs(brand: str, initials: str, keyword: str) -> dict:
    """Re-locate a thread by brand + agent initials + keyword.

    Tweet ids and text are not stored in the manifest: twcs is CC BY-NC-SA, and
    pinning them in this repo edges toward redistributing the dataset. Re-deriving
    from the local copy keeps this repository link-only for that source.
    """
    cands, want = [], set()
    with TWCS.open(newline="", encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            if r["inbound"] != "False" or r["author_id"] != brand:
                continue
            m = TWCS_SIG.search((r["text"] or "").strip())
            if not m or m.group(1) != initials or not r["in_response_to_tweet_id"]:
                continue
            cands.append(r)
            want |= {r["tweet_id"], r["in_response_to_tweet_id"]}
            if len(cands) >= 600:
                break

    rows = {}
    with TWCS.open(newline="", encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            if r["tweet_id"] in want:
                rows[r["tweet_id"]] = r

    def root(tid):
        r, d = rows.get(tid), 0
        while r and r.get("in_response_to_tweet_id") in rows and d < 12:
            tid = r["in_response_to_tweet_id"]
            r = rows[tid]
            d += 1
        return tid

    seen = set()
    for c in cands:
        rt = root(c["tweet_id"])
        if rt in seen:
            continue
        seen.add(rt)
        chain, cur = [], rt
        while cur in rows and len(chain) < 10:
            chain.append(rows[cur])
            nxt = (rows[cur].get("response_tweet_id") or "").split(",")[0].strip()
            cur = nxt if nxt in rows else None
        if len(chain) < 3:
            continue
        if keyword.lower() not in " ".join(x["text"] for x in chain).lower():
            continue

        turns = []
        for i, r in enumerate(chain, 1):
            turns.append(
                {
                    "n": i,
                    "speaker": "customer" if r["inbound"] == "True" else "agent",
                    # @handle prefix and ^XX sign-off stripped for readability;
                    # the sign-off is preserved in source_fields.agent_signoff
                    "text": TWCS_SIG.sub("", re.sub(r"^@\S+\s*", "", r["text"])).strip(),
                    "sent_at": r["created_at"],
                }
            )

        return {
            "channel": "social",
            "agent_id": f"twcs-{brand}-{initials}",
            "customer_id": None,
            "turns": turns,
            "source_fields": {"brand": brand, "agent_signoff": f"^{initials}"},
        }

    raise SystemExit(f"twcs: no matching thread for {brand} ^{initials} / {keyword!r}")


# ---------------------------------------------------------------- rendering


def render_markdown(convos: list[dict], local_only: list[dict] | None = None) -> str:
    L: list[str] = []
    L.append("# Curated Conversations\n")
    L.append(
        "Real customer-service interactions taken from the three source corpora. "
        "Generated by `curated/build/build_curated.py` — **do not edit by hand.**\n"
    )
    L.append(
        "These are presented **as raw data, without commentary or scoring.** No "
        "conversation here is labelled good or bad, and nothing is flagged for your "
        "attention — reading and interpreting them is the exercise. See "
        "`curated/SCHEMA.md` for the field reference.\n"
    )

    if local_only:
        ids = ", ".join(f"`{c['id']}`" for c in local_only)
        L.append(
            f"> **Not included here: {ids}.** Those come from a source whose licence "
            "does not permit redistribution under this repository's terms. Generate "
            "them on your own machine with `python3 curated/build/build_curated.py` "
            "once you have downloaded the source datasets — they will appear in "
            "`curated/conversations-local/`.\n"
        )

    L.append("## Index\n")
    L.append("| ID | Channel | Source | Turns |")
    L.append("|---|---|---|---|")
    for c in convos:
        L.append(
            f"| [`{c['id']}`](#{c['id'].lower()}) | {c['channel']} "
            f"| {c['source']['dataset']} | {len(c['turns'])} |"
        )
    L.append("")

    for c in convos:
        src = c["source"]
        L.append("---\n")
        L.append(f"## {c['id']}\n")
        L.append(f"- **Channel** {c['channel']} · **Turns** {len(c['turns'])}")
        L.append(
            f"- **Source** {src['dataset']} `{src['original_id']}` — {src['licence']} "
            f"([source]({src['url']}))"
        )
        L.append(
            f"- **Agent** `{c['agent_id']}`"
            if c.get("agent_id")
            else "- **Agent** *not identified in this dataset*"
        )
        mods = c.get("modifications") or []
        L.append(
            f"- **Modified** {'yes — ' + '; '.join(mods) if mods else 'no (verbatim from source)'}\n"
        )

        L.append("### Transcript\n")
        for t in c["turns"]:
            if t["speaker"] == "system_action":
                L.append(f"{t['n']}. *(system: {t['text']})*")
                continue
            who = "**Agent**" if t["speaker"] == "agent" else "Customer"
            stamp = (
                f"  <sub>{t['start_s']:.1f}–{t['end_s']:.1f}s</sub>"
                if t.get("start_s") is not None
                else ""
            )
            L.append(f"{t['n']}. {who}: {t['text']}{stamp}")
        L.append("")

        L.append("### Source fields\n")
        L.append("_Reproduced from the dataset as-is._\n")
        for k, v in c["source_fields"].items():
            if v in (None, {}, []):
                continue
            L.append(f"- `{k}`: {v}")
        L.append("")

    # Required attribution notices (CC BY 4.0 s.3(a); MIT notice retention).
    L.append("---\n")
    L.append("## NOTICE — required attributions\n")
    seen = []
    for c in convos:
        key = c["source"]["dataset"]
        if key in seen:
            continue
        seen.append(key)
        meta = SOURCES[key]
        L.append(f"**{key}** — {c['source']['licence']}")
        L.append(f"- {meta['copyright']}")
        L.append(f"- {meta['citation']}")
        L.append(f"- {meta['url']}")
        L.append(
            "- Excerpts here are unmodified transcripts restructured into JSON; "
            "any alteration to an interaction is recorded in its `modifications` field.\n"
        )
    L.append(
        "Full licence text for this repository is in `LICENSE`; per-dataset "
        "obligations are in `ATTRIBUTION.md`.\n"
    )

    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- main


def main() -> int:
    manifest = json.loads((Path(__file__).parent / "manifest.json").read_text())

    needed = {e["source"]["dataset"] for e in manifest["conversations"]}
    required = [
        p
        for p, ds in ((HVB, "HarperValleyBank"), (ABCD, "ABCD"), (TWCS, "twcs"), (APPTEK, "AppTek"))
        if ds in needed
    ]
    for p in required:
        if not p.exists():
            print(
                f"ERROR: missing {p}\n  Datasets are gitignored — see ATTRIBUTION.md.",
                file=sys.stderr,
            )
            return 2

    OUT_JSON.mkdir(parents=True, exist_ok=True)
    OUT_LOCAL.mkdir(parents=True, exist_ok=True)
    built, local_only = [], []

    for entry in manifest["conversations"]:
        ds = entry["source"]["dataset"]
        oid = entry["source"]["original_id"]

        if ds == "HarperValleyBank":
            core = load_harper_valley(oid)
        elif ds == "ABCD":
            core = load_abcd(oid)
        elif ds == "AppTek":
            core = load_apptek(oid)
        elif ds == "twcs":
            core = load_twcs("VirginTrains", "HP", "booking reference")
        else:
            raise SystemExit(f"unknown dataset {ds!r}")

        meta = SOURCES[ds]
        convo = {
            "id": entry["id"],
            "source": {
                "dataset": ds,
                "original_id": oid,
                "licence": meta["licence"],
                "url": meta["url"],
                "citation": meta["citation"],
            },
            "modifications": entry.get("modifications", []),
            "channel": core["channel"],
            "agent_id": core["agent_id"],
            "customer_id": core["customer_id"],
            "turns": core["turns"],
            "source_fields": core["source_fields"],
        }

        redist = meta["redistributable"]
        target = OUT_JSON if redist else OUT_LOCAL
        (target / f"{entry['id']}.json").write_text(
            json.dumps(convo, indent=2, ensure_ascii=False) + "\n"
        )
        (built if redist else local_only).append(convo)
        print(
            f"  built {entry['id']}  ({ds} {oid}, {len(convo['turns'])} turns)"
            f"{'' if redist else '   [local only -- not committable]'}"
        )

    OUT_MD.write_text(render_markdown(built, local_only))
    print(f"\nwrote {len(built)} committable conversations -> {OUT_JSON}")
    if local_only:
        print(f"wrote {len(local_only)} local-only conversations  -> {OUT_LOCAL}")
    print(f"wrote rendering                    -> {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
