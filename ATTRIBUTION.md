# Dataset Attribution and Licence Obligations

**This repository contains no dataset files.** Each dataset below must be downloaded from its own
source, and **each retains its own licence** — the licence covering this repository applies only to
the documentation and scripts *in* this repository, and confers no rights over any dataset.

Every licence here was verified from a primary source (the shipped `LICENSE` file, or the provider's
own licence metadata) on 18 August 2026.

---

## Datasets in use

### 1. HarperValleyBank
- **Licence:** CC BY 4.0 — *attribution required. This is **not** public domain.*
- **Source:** https://github.com/cricketclub/gridspace-stanford-harper-valley
- **Obligation — cite the paper:**
  > Mike Wu, Jonathan Nafziger, Anthony Scodary, Andrew Maas.
  > *HarperValleyBank: A Domain-Specific Spoken Dialog Corpus.* arXiv:2010.13929, 2020.
  ```bibtex
  @misc{wu2020harpervalleybank,
    title  = {HarperValleyBank: A Domain-Specific Spoken Dialog Corpus},
    author = {Mike Wu and Jonathan Nafziger and Anthony Scodary and Andrew Maas},
    year   = {2020}, eprint = {2010.13929}, archivePrefix = {arXiv}, primaryClass = {cs.LG}
  }
  ```
- Commercial use: permitted with attribution.

### 2. ABCD — Action-Based Conversations Dataset
- **Licence:** MIT — © 2021 ASAPP Research. Retain the copyright and permission notice.
- **Source:** https://github.com/asappresearch/abcd
- **Cite:** Chen et al., *Action-Based Conversations Dataset*, NAACL 2021, arXiv:2104.00783.
- Commercial use: permitted.

### 3. Customer Support on Twitter (twcs)
- **Licence:** **CC BY-NC-SA 4.0** — attribution, **non-commercial**, **share-alike**.
- **Source:** https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter
- **Author:** Stuart Axelbrooke.
- **Obligations:**
  - **Non-commercial only.** Anything derived from this data is research-use.
  - **Share-alike** applies if you *publish a derivative dataset* (e.g. an annotated or re-scored
    version) — it must also be CC BY-NC-SA 4.0. Publishing analysis, metrics and findings is fine.

### 4. CallCenterEN (AIxBlock, 92k transcripts)
- **Licence:** CC BY-NC 4.0 — attribution, **non-commercial**.
- **Source:** https://huggingface.co/datasets/AIxBlock/92k-real-world-call-center-scripts-english
- **Cite:** Dao, Chawla, Banda & DeLeeuw, *Real-World En Call Center Transcripts Dataset with PII
  Redaction*, arXiv:2507.02958, 2025.
- Note: audio is deliberately not included in the public release.

### 5. Technion SEE Lab — AnonymousBank and USBank
- **Licence:** Free for academic use.
- **Source:** https://seelab.net.technion.ac.il/data/
- **Obligation — this one requires contacting a person.** The provider asks that you notify them and
  acknowledge the source:
  - Prof. Avi Mandelbaum — `avim@ie.technion.ac.il`, or the SEE Research Team — `see@technion.ac.il`
- Commercial use: not granted; ask if needed.

### 6. AppTek Call-Centre Dialogues *(optional — audio and accent coverage)*
- **Licence:** CC BY-SA 4.0 — attribution, **share-alike**.
- **Source:** https://huggingface.co/datasets/apptek-com/apptek_callcenter_dialogues
- **Cite:** arXiv:2604.27543.
- Commercial use: permitted, but derivatives must stay CC BY-SA.

---

## ⚠️ One combination to avoid

**AppTek (CC BY-SA 4.0) and twcs (CC BY-NC-SA 4.0) cannot both be satisfied by a single published
work.** BY-SA requires derivatives remain commercially usable; BY-NC-SA requires they remain
non-commercial. No licence satisfies both. Keep them in separate pipelines and never merge them into
one published artefact.

Everything else composes: merging datasets **privately** carries no restriction at all, since these
licences govern distribution rather than use.

## If you want to use this beyond the course

The students own the code they write. But **"publicly available" is not the same as "unrestricted"** —
two of these datasets are public *and* non-commercial:

- **twcs** (CC BY-NC-SA 4.0) and **CallCenterEN** (CC BY-NC 4.0) are **research-use only.**

So if anyone later wants to open-source the project commercially, put it in a portfolio a company pays
for, take it into a startup, or hand it to Genesys as a product, **anything derived from those two
datasets is a problem.** Whether a trained model inherits its training data's licence is legally
unsettled, and the conservative reading is that it does.

**Practical advice: keep the NC datasets in clearly separated pipelines from day one.** If the
commercially-clean path matters to you, build it on **HarperValleyBank (CC BY 4.0)** and
**ABCD (MIT)** only — both permit commercial use. Retrofitting this separation later means
re-running work; observing it now costs nothing.

## Required attribution block

Include something equivalent to this in any report, paper or presentation:

> This work uses the HarperValleyBank corpus (Wu et al., 2020, CC BY 4.0); the Action-Based
> Conversations Dataset (ASAPP Research, MIT); the Customer Support on Twitter dataset
> (S. Axelbrooke, CC BY-NC-SA 4.0); CallCenterEN (Dao et al., 2025, CC BY-NC 4.0); and operational
> call-centre data from the Technion SEE Laboratory, used with acknowledgement.
