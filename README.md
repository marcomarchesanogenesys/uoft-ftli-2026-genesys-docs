# FTLI × Genesys — Agent Coaching Project (2026)

Reference material and data sources for the University of Toronto student team.

**The brief:** build a tool that helps contact-centre agents improve their own
performance against configurable quality criteria, and shows whether they are
improving over time.

---

## Start here

**Clone the repo and you already have 200 real conversations** — no downloads, no
setup. They are in [`curated/conversations/`](curated/conversations/), one JSON file
each; [`curated/CONVERSATIONS.md`](curated/CONVERSATIONS.md) is the index.

For the full set of 400, plus the raw datasets to sample more from:

```bash
python3 scripts/download_data.py        # ~90 MB of text — no pip installs
python3 curated/build/build_curated.py  # rebuilds all 400, ~12 seconds
```

Python 3.8+ and nothing else. On Windows use `python scripts\download_data.py`.

Re-running the download is safe — files already fetched are skipped, so an
interrupted download just needs another run.

## The curated conversations

400 real customer-service interactions — 100 from each dataset — all in **one
schema**, so the same loading code works across every source. Field reference is in
[`curated/SCHEMA.md`](curated/SCHEMA.md).

**Raw data only.** No commentary, no scores, no tags, nothing flagged for your
attention. Deciding what matters in an interaction is the work; being told what to
look for would replace your judgement with someone else's.

Three of the four datasets are selected **by agent** — the ten busiest agents, ten
conversations each. That gives enough per agent to look at one person's work
together, and enough agents to compare them. ABCD has no agent identity at all, so
it is spread evenly across its ten conversation types instead.

| Dataset | Channel | In repo? |
|---|---|---|
| HarperValleyBank | voice | ✅ committed |
| ABCD | chat | ✅ committed |
| AppTek | voice | after download — share-alike licence |
| twcs | social | after download — share-alike licence |

The two share-alike datasets can't be redistributed under this repo's licence, so
those 200 files are generated locally into `curated/conversations-local/`
(gitignored). Run the build and they appear.

### Sampling more

Everything is driven by [`curated/build/manifest.json`](curated/build/manifest.json)
— counts, per-agent caps, turn-length filters, and the random seed. Change a number,
rerun the build. The headroom is large:

| Dataset | Available | Agents |
|---|---|---|
| HarperValleyBank | 1,418 conversations | 58 |
| ABCD | 10,030 | none recorded |
| AppTek | 873 | 82 |
| twcs | 106,935 threads | 1,362 |

Content is always extracted from the source datasets, never hand-typed, so the set
can be regenerated and diffed against the originals at any time.

The build also writes a readable prose rendering per dataset —
`curated/conversations-<dataset>.md` — which is easier to skim than JSON. Those are
gitignored rather than committed, because they duplicate the JSON line for line; run
the build and they appear.

## The datasets

None are in this repo — they're too large, and some licences don't permit
redistribution.

| # | Dataset | What it contains | Download |
|---|---|---|---|
| **1** | [HarperValleyBank](https://github.com/cricketclub/gridspace-stanford-harper-valley) | 1,446 bank support **calls**. A human-verified transcript *and* a machine transcript, per-turn timings in ms, 8 task types, 58 agent ids. | 25 MB |
| **2** | [ABCD](https://github.com/asappresearch/abcd) | 10,042 retail support **chats**. Agent and customer turns plus the agent's system actions, a full customer record per chat, and the documented procedure each agent was meant to follow. | 43 MB |
| **3** | [AppTek Call-Centre Dialogues](https://huggingface.co/datasets/apptek-com/apptek_callcenter_dialogues) | 873 support **calls**, 94,679 speaker-labelled segments with per-turn timings. 82 agent ids, 14 English accents, 16 industries. | 23 MB |
| **4** *(optional)* | [Customer Support on Twitter](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter) | 2.8M **public messages** between customers and 108 brands, Oct–Dec 2017. Real timestamps and thread structure. | 493 MB |

Datasets 1–3 are role-played scenarios recorded with real people. Dataset 4 is real
production traffic.

**We only use text and metadata — no audio.** That keeps the download to about 90 MB
instead of 55 GB.

Useful flags: `--list` shows what would be fetched without writing anything,
`--only abcd` fetches one dataset, `--all` includes the optional fourth.

### The optional fourth dataset

**Twitter needs a free Kaggle account**, which is why it isn't in the default
download. It's worth getting: it is the only one of the four that is real production
traffic rather than role-play, and **the only one with real dates** — so anything
measuring change over genuine time has to come from there.

Run `python3 scripts/download_data.py --all` and the script prints the token steps.
Without credentials it just skips that dataset, and **the build still produces 300
conversations from the other three** rather than failing.

All dataset folders are gitignored, so nothing you download can be committed by
accident.

## What's in this repo

| Path | What it is |
|---|---|
| [`curated/CONVERSATIONS.md`](curated/CONVERSATIONS.md) | **Start here.** Index of the set, what each dataset offers, and conversations per agent. |
| [`curated/SCHEMA.md`](curated/SCHEMA.md) | Field reference. Which fields every conversation has, which are dataset-specific, and the two unit gotchas. |
| `curated/conversations/` | The 200 committed conversations, one JSON file each. |
| `curated/build/` | The build script and its manifest. Edit the manifest to sample more. |
| `scripts/download_data.py` | Fetches the datasets. Standard library only. |
| [`GLOSSARY.md`](GLOSSARY.md) | 102 contact-centre and CX terms. Worth skimming first — the field names in these datasets assume it. |
| [`ATTRIBUTION.md`](ATTRIBUTION.md) | Every dataset's licence, citation, and what you must credit. |
| `LICENSE` | This repository's own licence (CC BY 4.0). Does **not** cover the datasets. |

## Two things about the data that will shape your design

**Nobody has scored these conversations.** No public dataset ships human quality
ratings — they're HR-sensitive and commercially valuable, so they don't get
published. If your tool needs to know whether it agrees with a human, some of you
will have to score a sample by hand.

**Only one dataset has real dates.** HarperValleyBank spans 4 days and AppTek has no
timestamps at all, so a run of conversations there is a sequence, not a timeline.
Improvement over real elapsed time only exists in the Twitter data.

## Three things about the licences

Read [`ATTRIBUTION.md`](ATTRIBUTION.md) before you publish anything. The short
version:

1. **Cite HarperValleyBank** if you use it — Wu et al. (2020), arXiv:2010.13929.
2. **Twitter data is non-commercial** (CC BY-NC-SA 4.0). Fine for coursework; it
   restricts what you can do with the results commercially.
3. **HarperValleyBank and ABCD permit commercial use** (CC BY 4.0 and MIT). If you
   want to keep that option open, keep work built on those two separate from work
   built on the Twitter data. AppTek is CC BY-SA 4.0 — commercial use is fine, but
   share-alike applies to anything you redistribute.

**You own the code you write.** These licences cover the data, not your work.

## Questions

Ask in the weekly standup, or open an issue on this repo.
