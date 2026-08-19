# Curated Conversation Format

Each conversation is one JSON file in `conversations/`, with a combined
human-readable rendering in `CONVERSATIONS.md`.

## What this is, and what it is not

These are **real customer-service interactions presented as raw data.** Turns and
fields come straight from the source corpora.

There is deliberately **no commentary, scoring, rating, tagging or interpretation**
anywhere in this set. No conversation is labelled good or bad. Nothing is flagged
for your attention. Reading the interactions and deciding what matters in them is
the work — being told what to look for would replace your judgement with someone
else's.

Where a source ships two related fields — for example the task assigned to an
agent and the task the agent actually recorded — **both are reproduced and left
uncompared.** Drawing the comparison is yours to do.

## Regenerating and extending

Selections live in `build/manifest.json`. Append entries and re-run:

```bash
python3 curated/build/build_curated.py
```

Content is always extracted from the source datasets, never hand-typed, so the set
can be regenerated and diffed against the originals at any time.

## Fields

```jsonc
{
  "id": "CC-0001",                    // stable id for this set
  "source": {
    "dataset": "HarperValleyBank",
    "original_id": "01cefd6f...",     // id in that corpus — always traceable back
    "licence": "CC BY 4.0",
    "url": "https://...",
    "citation": "Wu et al. (2020) ..."
  },
  "modifications": [],                // [] = verbatim. Any alteration is listed here.
  "channel": "voice",                 // voice | chat | social
  "agent_id": "hvb-speaker-58",       // null where the dataset has no agent identity
  "customer_id": "hvb-speaker-33",
  "turns": [ ... ],
  "source_fields": { ... }            // per-dataset, see below
}
```

### `turns[]`

Always present: `n`, `speaker`, `text`.

`speaker` is `agent`, `customer`, or `system_action`.

Voice conversations additionally carry:

| Field | Meaning |
|---|---|
| `asr_text` | the machine transcript of the same turn; `text` is the human-verified one |
| `start_ms`, `duration_ms` | timing within the call |
| `dialog_acts` | the dataset's own 16-tag annotation |

Social conversations carry `sent_at` (the original timestamp string).

### `speaker: "system_action"`

ABCD interleaves the agent's *system actions* with speech as a third speaker —
for example `Account has been pulled up for Norman Bouchard.` These are not
spoken turns; they record what the agent did in their tooling.

### `source_fields`

Dataset-specific fields, reproduced as-is.

**voice** (HarperValleyBank) — `task_assigned`, `task_logged_by_agent`, `labels`,
`session`, `agent_survey_response`, `customer_survey_response`.

Note that HarperValleyBank ships both a human-verified and a machine transcript
for most turns (`text` and `asr_text`), which makes it possible to compare
behaviour on clean versus recognised text.

**chat** (ABCD) — `flow`, `subflow`, `actions_taken`, `scenario_order`,
`scenario_product`.

The documented procedure for each subflow — what an agent is supposed to do, in
order — is in `02-abcd/data/guidelines.json`.

**social** (twcs) — `brand`, `agent_signoff`.

The `@handle` prefix and the trailing `^XX` sign-off are stripped from `text` for
readability; the sign-off itself is preserved in `agent_signoff`.

## Licence

Each conversation carries the licence of its source dataset — see
`ATTRIBUTION.md` for full obligations. The sources differ on redistribution:

- **HarperValleyBank** (CC BY 4.0) and **ABCD** (MIT) — redistribution permitted
  with attribution.
- **twcs** (CC BY-NC-SA 4.0) — share-alike, so excerpts cannot be relicensed under
  this repository's CC BY 4.0.

The build script therefore re-derives twcs threads from a local copy rather than
storing identifiers or text, keeping this repository link-only for that source.
