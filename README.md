# FTLI × Genesys — Agent Coaching Project (2026)

Reference material and data sources for the University of Toronto student team.

**The brief:** build a tool that helps contact-centre agents improve their own
performance against configurable quality criteria, and shows whether they are
improving over time.

---

## The three datasets

None of them are in this repo — they are too large, and some licences don't permit
redistribution. Download each from its source below.

| # | Dataset | What it contains | Size |
|---|---|---|---|
| **1** | [HarperValleyBank](https://github.com/cricketclub/gridspace-stanford-harper-valley) | 1,446 recorded bank support **calls**. Audio (one file per speaker), a human-verified transcript *and* a machine transcript, per-turn timings, 8 task types, 58 agent ids. | 2.6 GB |
| **2** | [ABCD](https://github.com/asappresearch/abcd) | 10,042 retail support **chats**. Agent/customer turns plus the agent's system actions, and the documented procedure each agent was meant to follow (`data/guidelines.json`). | 79 MB |
| **3** | [Customer Support on Twitter](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter) | 2.8M **public messages** between customers and 108 brands, Oct–Dec 2017. Timestamps, thread structure, and agent sign-off initials on some replies. | 493 MB |

Datasets 1 and 2 are role-played scenarios recorded with real people. Dataset 3 is
real production traffic.

## Setting up

Download each dataset and unpack it into the matching folder at the repo root:

```
01-harper-valley-bank/    ← HarperValleyBank (git clone)
02-abcd/                  ← ABCD (git clone, then gunzip data/abcd_v1.1.json.gz)
03-twitter-twcs/          ← twcs.csv from Kaggle
```

Those folders are gitignored, so nothing you download will be committed by accident.

Each dataset folder has a `PREVIEW.md` describing its layout and fields once you've
downloaded it.

## What's in this repo

| Path | What it is |
|---|---|
| `curated/CONVERSATIONS.md` | A handful of complete conversations pulled from the datasets, formatted for reading. Raw data — no commentary or scoring. |
| `curated/SCHEMA.md` | Field reference for those conversations. |
| `curated/build/` | The script that generates them. Run it to regenerate, or extend `manifest.json` to add more. |
| `ATTRIBUTION.md` | Every dataset's licence, citation, and what you must credit. |
| `LICENSE` | This repository's own licence (CC BY 4.0). Does **not** cover the datasets. |

To regenerate the curated conversations once you have the data:

```bash
python3 curated/build/build_curated.py
```

## Three things to know about the licences

Read `ATTRIBUTION.md` before you publish anything. The short version:

1. **Cite HarperValleyBank** if you use it — Wu et al. (2020), arXiv:2010.13929.
2. **Twitter data is non-commercial** (CC BY-NC-SA 4.0). Fine for coursework;
   it restricts what you can do with the results commercially.
3. **HarperValleyBank and ABCD permit commercial use** (CC BY 4.0 and MIT). If you
   want to keep that option open, keep work built on those two separate from work
   built on the Twitter data.

## Questions

Ask in the weekly standup, or open an issue on this repo.
