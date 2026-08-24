# Curated Conversation Schema

Every curated conversation is one JSON file in `conversations/`, with a combined
human-readable rendering in `CONVERSATIONS.md`.

**One schema, four datasets.** A conversation from HarperValleyBank, ABCD, AppTek or
twcs loads with the same code. Pick whichever source suits what you want to build.

## What this is, and what it is not

These are **real customer-service interactions presented as raw data.** Turns and
fields come straight from the source corpora.

There is deliberately **no commentary, scoring, rating, tagging or interpretation**
anywhere in this set. No conversation is labelled good or bad. Nothing is flagged
for your attention. Reading the interactions and deciding what matters in them is
the work — being told what to look for would replace your judgement with someone
else's.

Where a source ships two related fields — for example the task assigned to an agent
and the task the agent actually recorded — **both are reproduced and left
uncompared.** Drawing the comparison is yours to do.

### One thing the shared schema does *not* give you

Uniform **loading** is not uniform **meaning**. A tweet and a ten-minute phone call
arrive in the same structure, but they are not the same kind of thing: there is no
hold time in a tweet, and no 90-second reply gap in a live call. A quality
definition built for one channel will not transfer to another unchanged. The schema
makes the data easy to read; deciding what is comparable is still your judgement.

---

## The contract

### Required — present on every conversation

```jsonc
{
  "id": "CC-0001",              // stable id within this set
  "source": {
    "dataset": "HarperValleyBank",
    "original_id": "01cefd6f...",  // id in that corpus — always traceable back
    "licence": "CC BY 4.0",
    "url": "https://...",
    "citation": "Wu et al. (2020) ..."
  },
  "modifications": [],          // [] = verbatim. Any alteration is listed here.
  "channel": "voice",           // voice | chat | social
  "turns": [
    { "n": 1, "speaker": "agent", "text": "..." }
  ],
  "source_fields": { }          // dataset-specific, never normalised
}
```

You can rely on those six keys existing on every file.

### Optional — present only when the source actually has it

| Key | Where it appears |
|---|---|
| `agent_id` | HarperValleyBank, AppTek, twcs |
| `customer_id` | HarperValleyBank, ABCD, AppTek |
| `customer_record` | HarperValleyBank, ABCD |
| `turns[].asr_text` | HarperValleyBank |
| `turns[].start_ms`, `turns[].duration_ms` | HarperValleyBank |
| `turns[].start_s`, `turns[].end_s` | AppTek |
| `turns[].speaker_id` | AppTek |
| `turns[].dialog_acts` | HarperValleyBank |
| `turns[].sent_at` | twcs |

**Absent means absent.** A key is omitted rather than set to `null` when the source
has nothing to put in it. A missing key means "this dataset does not record this";
an empty value would wrongly imply the field exists and happened to be blank.

### Two rules that will save you a bug

**Time units are in the field names, and are never converted.** HarperValleyBank
records milliseconds (`start_ms`), AppTek records seconds (`start_s`). They are
deliberately *not* unified into one `start` field, because averaging across the two
would be silently wrong by a factor of 1000. Check the suffix.

**`speaker` has three values, not two.** `agent`, `customer`, and `system_action`.

---

## Capability matrix

What each dataset can and cannot give you. Use this to choose a source.

| | HarperValleyBank | ABCD | AppTek | twcs |
|---|---|---|---|---|
| Channel | voice | chat | voice | social |
| Turns with speaker roles | ✅ | ✅ | ✅ | ✅ |
| Agent identity | ✅ 58 ids | ❌ | ✅ 82 ids | ~35% (sign-off) |
| Customer identity | ✅ | ✅ | ✅ | anonymised int |
| Customer record | ✅ thin | ✅ rich | ❌ | ❌ |
| Per-turn timing | ✅ ms | ❌ | ✅ seconds | message timestamps |
| Gold **and** machine transcript | ✅ | ❌ | ❌ | ❌ |
| Intent / task label | ✅ 8 tasks | ✅ 10 flows, 96 subflows | domain only | ❌ |
| Documented correct procedure | ❌ | ✅ `guidelines.json` | ❌ | ❌ |
| Real calendar dates | 4 days only | ❌ | ❌ | ✅ 3 months |
| Speaker demographics | ❌ | ❌ | ✅ gender, accent | ❌ |
| Committed to this repo | ✅ | ✅ | local only | local only |

Two entries in that table are worth reading twice. **Only HarperValleyBank ships both
a human-verified and a machine transcript**, so it is the only source where you can
measure what speech recognition costs you. And **only twcs has real dates**, so
anything about change over time has to come from there.

---

## Field reference

### `turns[]`

Always `n`, `speaker`, `text`.

| Field | Type | Notes |
|---|---|---|
| `n` | int | 1-based position. For AppTek, ordered by start time — and segments may **overlap**, so `n` is sequence, not exclusive occupancy |
| `speaker` | string | `agent` \| `customer` \| `system_action` |
| `text` | string | the human-verified transcript where two exist |
| `asr_text` | string | the machine transcript of the same turn (HarperValleyBank) |
| `start_ms`, `duration_ms` | int | **milliseconds** (HarperValleyBank) |
| `start_s`, `end_s` | float | **seconds** (AppTek) |
| `speaker_id` | string | per-segment speaker (AppTek) |
| `dialog_acts` | string[] | the dataset's own 16-tag annotation (HarperValleyBank) |
| `sent_at` | string | original timestamp string (twcs) |

### `speaker: "system_action"`

ABCD interleaves the agent's *system actions* with speech as a third speaker — for
example `Account has been pulled up for Norman Bouchard.` These are not spoken
turns; they record what the agent did in their tooling. They are what makes it
possible to see the sequence of steps an agent took.

### `customer_record`

The customer data attached to the interaction. It appears in two different shapes,
and the difference is worth understanding.

**A read — a record that existed before the call** (ABCD). The agent looks it up and
can verify the customer against it:

```jsonc
"customer_record": {
  "customer_name": "albert sanders",
  "username": "albertsanders187",
  "email": "albertsanders187@email.com",
  "phone": "(810) 186-0026",
  "member_level": "gold",
  "address": { "street": "...", "city": "...", "state": "...",
               "zip_code": "...", "full_address": "..." },
  "order": {
    "order_id": "0258746938",
    "purchase_date": "2020-02-19",
    "payment_method": "credit card",   // null when the source has none
    "packaging": "yes",
    "num_products": "3",
    "products": [ { "brand": "michael_kors",
                    "product_type": "jacket", "amount": 74 } ]
  }
}
```

**A write — a record created by the call** (HarperValleyBank). `captured_by_agent`
is what the agent entered into their tooling as a result of the conversation:

```jsonc
"customer_record": {
  "customer_name": "Robert Johnson",
  "captured_by_agent": {
    "transfer source account": "savings",
    "transfer destination account": "checking",
    "transfer amount": "135"
  }
}
```

Note the one formatting liberty taken anywhere in this set: ABCD stores `products`
as a Python-repr **string**, and it is parsed into real JSON here. The values are
unchanged.

### `source_fields`

Dataset-specific, reproduced as-is and never normalised. This is the escape hatch —
anything a source records that does not fit the shared schema lands here rather than
being dropped or bent into shape.

| Dataset | Fields |
|---|---|
| HarperValleyBank | `task_assigned`, `task_logged_by_agent`, `labels`, `session`, `agent_survey_response`, `customer_survey_response` |
| ABCD | `flow`, `subflow`, `actions_taken` |
| AppTek | `duration_s`, `domain`, `accent`, `agent_gender`, `customer_gender` |
| twcs | `brand`, `agent_signoff` |

ABCD's documented procedure for each subflow — what an agent is *supposed* to do, in
order — is in `02-abcd/data/guidelines.json`. Note it covers 55 of the 96 subflow
values present in the data.

For twcs, the `@handle` prefix and trailing `^XX` sign-off are stripped from `text`
for readability; the sign-off is preserved in `source_fields.agent_signoff`.

---

## What is not in this set

**AnonymousBank is deliberately excluded.** It has 444,448 real calls with real
agents and a full year of dates, but **no turns and no transcript of any kind** —
only the timing skeleton of each call (IVR, queue and service boundaries) plus an
outcome. It cannot be expressed as a conversation without inventing the
conversation, so it is not forced into this schema. Use it directly from
`05-anonymousbank/` if you want per-agent operational trends.

---

## Regenerating and extending

Selections live in `build/manifest.json`. Append entries and re-run:

```bash
python3 curated/build/build_curated.py
```

Content is always extracted from the source datasets, never hand-typed, so the set
can be regenerated and diffed against the originals at any time. The manifest holds
only selections — an id, a source dataset, an original id, and any modifications.

---

## Licence

Each conversation carries the licence of its source dataset — see `ATTRIBUTION.md`
for the full obligations. Sources differ on whether excerpts may be redistributed:

- **HarperValleyBank** (CC BY 4.0) and **ABCD** (MIT) — redistribution permitted
  with attribution. These are committed to `conversations/`.
- **twcs** (CC BY-NC-SA 4.0) and **AppTek** (CC BY-SA 4.0) — share-alike, which
  conflicts with this repository's CC BY 4.0. These are written to
  `conversations-local/` and are not committed; regenerate them yourself after
  downloading the sources.

The build script decides this from the source licence, so a new dataset is routed
correctly by declaring its licence rather than by remembering to special-case it.
