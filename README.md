# FTLI × Genesys — Agent Coaching Project (2026)

Reference material and data sources for the University of Toronto student team.

**The brief:** build a tool that helps contact-centre agents improve their own
performance against configurable quality criteria, and shows whether they are
improving over time.

---

## Start here

### 1. Check you have Python

```bash
python3 --version
```

Any **3.8 or newer** is fine.

> **On Windows, type `python` wherever this README says `python3`.** Windows
> installs the command as `python`; `python3` either doesn't exist or opens the
> Microsoft Store. So `python scripts\download_data.py`, and so on.

<details>
<summary><b>"command not found", or nothing printed? Click here.</b></summary>

| OS | How |
|---|---|
| **macOS** | Recent versions already have it. Otherwise [python.org/downloads](https://www.python.org/downloads/), or `brew install python`. |
| **Windows** | [python.org/downloads](https://www.python.org/downloads/) — **tick "Add python.exe to PATH"** on the first installer screen, or nothing below will run. |
| **Linux** | Almost always preinstalled. Otherwise `sudo apt install python3`. |

Two things that trip people up:

- **Restart your terminal after installing**, or it won't see the new command.
- **On Windows the command is `python`, not `python3`.** If `python` opens the
  Microsoft Store, install from python.org with the PATH box ticked.

</details>

### 2. You already have 200 conversations

No downloads, no setup — they're committed to this repo, one JSON file each:

- [`curated/conversations/`](curated/conversations/) — the files
- [`curated/CONVERSATIONS.md`](curated/CONVERSATIONS.md) — the index, **read this first**
- [`curated/SCHEMA.md`](curated/SCHEMA.md) — what every field means

### 3. Optional — get all 400

```bash
python3 scripts/download_data.py        # ~90 MB of text, no pip installs
python3 curated/build/build_curated.py  # rebuilds all 400, ~12 seconds
```

Standard library only — nothing to install after Python itself. Re-running the
download is safe: finished files are skipped, so an interrupted run just needs
another go.

---

## The conversations

400 real customer-service interactions — 100 per dataset — all in **one schema**,
so the same loading code works everywhere.

**Raw data only.** No commentary, no scores, no tags, nothing flagged for your
attention. Deciding what matters in an interaction is the work.

Three of the four are sampled **by agent** (the ten busiest, ten conversations
each) so you can study one person's work and compare people. ABCD has no agent
identity, so it's spread across its ten conversation types instead.

| Dataset | Channel | In repo? |
|---|---|---|
| HarperValleyBank | voice | ✅ committed |
| ABCD | chat | ✅ committed |
| AppTek | voice | after download — share-alike licence |
| twcs | social | after download — share-alike licence |

The two share-alike datasets can't be redistributed here, so those 200 files are
built locally into `curated/conversations-local/` (gitignored). The build also
writes a readable prose version per dataset, easier to skim than JSON.

**To sample more,** edit [`curated/build/manifest.json`](curated/build/manifest.json)
— counts, per-agent caps, turn-length filters, random seed — and rerun the build.
Headroom is large: 1,418 / 10,030 / 873 / 106,935 conversations available across
the four.

## The datasets

Too large to commit, and some licences forbid redistribution. **Text and metadata
only — no audio**, which keeps the download near 90 MB instead of 55 GB.

| # | Dataset | What it contains | Size |
|---|---|---|---|
| **1** | [HarperValleyBank](https://github.com/cricketclub/gridspace-stanford-harper-valley) | 1,446 bank support **calls**. Human *and* machine transcripts, per-turn timings, 8 task types, 58 agents. | 25 MB |
| **2** | [ABCD](https://github.com/asappresearch/abcd) | 10,042 retail support **chats**. Turns plus agent system actions, a customer record each, and the procedure the agent should have followed. | 43 MB |
| **3** | [AppTek](https://huggingface.co/datasets/apptek-com/apptek_callcenter_dialogues) | 873 support **calls**, 94,679 speaker-labelled segments with timings. 82 agents, 14 accents, 16 industries. | 23 MB |
| **4** *(optional)* | [Customer Support on Twitter](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter) | 2.8M **public messages**, 108 brands, Oct–Dec 2017. Real timestamps and thread structure. | 493 MB |

Datasets 1–3 are role-play recorded with real people. Dataset 4 is real
production traffic.

Flags: `--list` previews without writing, `--only abcd` fetches one, `--all`
includes the optional fourth.

### The optional fourth dataset

`--all` adds the Twitter set. **No account needed** — it's out of the default run
only because it's ~490 MB against 90 MB for the other three.

```bash
python3 scripts/download_data.py --all
```

Worth the wait: it's the only one that is real production traffic rather than
role-play, and **the only one with real dates**, so anything measuring change over
genuine time has to come from there.

<details>
<summary>If Kaggle ever starts asking for an account</summary>

It currently serves this dataset anonymously. If that changes, the script says so
and falls back to a free API token:

```bash
python3 scripts/download_data.py --init-env   # creates .env in the repo root
```

Then [kaggle.com](https://www.kaggle.com) → [Settings](https://www.kaggle.com/settings)
→ **API** → **Create New Token**, and copy the two values from the downloaded
`kaggle.json` into `.env`:

```
KAGGLE_USERNAME=your-username
KAGGLE_KEY=your-key
```

`.env` is gitignored, so your key can't be committed by accident. An existing
`~/.kaggle/kaggle.json` works too.

</details>

All dataset folders are gitignored, so nothing you download can be committed by
accident.

## Two things that will shape your design

**Nobody has scored these conversations.** No public dataset ships human quality
ratings — they're HR-sensitive and commercially valuable. If your tool needs to
know whether it agrees with a human, some of you will have to score a sample by
hand.

**Only one dataset has real dates.** HarperValleyBank spans 4 days and AppTek has
no timestamps at all, so a run of conversations there is a sequence, not a
timeline. Improvement over real elapsed time only exists in the Twitter data.

## Licences

Read [`ATTRIBUTION.md`](ATTRIBUTION.md) before you publish anything. The short
version:

1. **Cite HarperValleyBank** if you use it — Wu et al. (2020), arXiv:2010.13929.
2. **Twitter data is non-commercial** (CC BY-NC-SA 4.0). Fine for coursework.
3. **HarperValleyBank and ABCD allow commercial use** (CC BY 4.0, MIT). To keep
   that option open, keep work built on those separate from the Twitter data.
   AppTek is CC BY-SA 4.0 — commercial use is fine, share-alike applies to
   anything you redistribute.

**You own the code you write.** These licences cover the data, not your work.

## What's in this repo

| Path | What it is |
|---|---|
| [`curated/CONVERSATIONS.md`](curated/CONVERSATIONS.md) | **Start here.** Index of the set and conversations per agent. |
| [`curated/SCHEMA.md`](curated/SCHEMA.md) | Field reference, including the two unit gotchas. |
| `curated/conversations/` | The 200 committed conversations. |
| `curated/build/` | Build script and manifest. Edit the manifest to sample more. |
| `scripts/download_data.py` | Fetches the datasets. Standard library only. |
| `.env.example` | Kaggle credential template. Copy it with `--init-env`. |
| [`GLOSSARY.md`](GLOSSARY.md) | 102 contact-centre terms. Skim it — the field names assume it. |
| [`ATTRIBUTION.md`](ATTRIBUTION.md) | Every licence, citation, and what you must credit. |
| `LICENSE` | This repo's licence (CC BY 4.0). Does **not** cover the datasets. |

## Questions

Ask in the weekly standup, or open an issue on this repo.
