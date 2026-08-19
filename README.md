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
| **4** | [AppTek Call-Centre Dialogues](https://huggingface.co/datasets/apptek-com/apptek_callcenter_dialogues) | 873 recorded support **calls**, 94,679 speaker-labelled segments with per-turn timings. 82 agent ids, 14 English accents, 16 industries. | 23 MB |
| **3** *(optional)* | [Customer Support on Twitter](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter) | 2.8M **public messages** between customers and 108 brands, Oct–Dec 2017. Timestamps, thread structure, and agent sign-off initials on some replies. | 493 MB |

Datasets 1, 2 and 4 are role-played scenarios recorded with real people. Dataset 3
is real production traffic.

**We only use text and metadata — no audio.** That keeps the whole thing to about
600 MB instead of 55 GB.

## Setting up

One command, and nothing to install beyond Python 3.8+:

```bash
python3 scripts/download_data.py
```

On Windows use `python scripts\download_data.py`.

That fetches the three core datasets (1, 2 and 4) into `01-harper-valley-bank/`,
`02-abcd/` and `04-apptek/`. Re-running it is safe — files already downloaded are
skipped, so an interrupted download just needs another run.

Useful flags: `--list` to see what it would fetch without writing anything,
`--only abcd` for a single dataset, `--all` to include the optional one below.

### The optional fourth dataset

**Dataset 3 (Twitter) needs a free Kaggle account**, which is why it isn't in the
default download. It's worth getting if you can: it's the only one of the four that
is real production traffic rather than role-play, and the only one with **real dates**
and **per-agent identity** — so anything measuring change over time needs it.

Run `python3 scripts/download_data.py --all` and the script prints step-by-step
instructions for creating the token. It never blocks: without credentials the other
three still download normally.

All dataset folders are gitignored, so nothing you download can be committed by
accident. Each has a `PREVIEW.md` describing its layout once downloaded.

## What's in this repo

| Path | What it is |
|---|---|
| `curated/CONVERSATIONS.md` | A handful of complete conversations pulled from the datasets, formatted for reading. Raw data — no commentary or scoring. |
| `curated/SCHEMA.md` | Field reference for those conversations. |
| `curated/build/` | The script that generates them. Run it to regenerate, or extend `manifest.json` to add more. |
| `scripts/download_data.py` | Fetches the datasets. Standard library only — no pip installs. |
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
   built on the Twitter data. AppTek is CC BY-SA 4.0 — commercial use is fine, but
   share-alike applies to anything you redistribute.

## Questions

Ask in the weekly standup, or open an issue on this repo.
