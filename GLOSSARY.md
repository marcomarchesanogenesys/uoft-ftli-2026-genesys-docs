# CX Platform and Contact Center Glossary

> Reference for the FTLI (U of T) × Genesys student project. Transcribed from the
> project's Confluence page, [FTLI (U of T) Genesys Partner Project](https://genesys-confluence.atlassian.net/wiki/spaces/~712020f73dd49b1bb047caa4878c0aeaaac98b/pages/2158592506/FTLI+U+of+T+Genesys+Partner+Project).
> Confluence remains the source of truth — if the two disagree, trust Confluence.

## Why this matters

Every organization depends on how well it serves its customers. A **contact center (CC)** manages live interactions across voice and digital channels, while a **customer relationship management (CRM)** system stores customer information and history.

These systems are typically integrated so agents can immediately see who is contacting them, understand the customer's context, and resolve issues without unnecessary repetition.

The terms in this glossary describe the technology behind that experience: routing interactions, recording and transcribing conversations, analyzing quality, and helping agents improve. Ultimately, it all exists to help organizations understand customers and respond effectively when they reach out.

---

# Part I — Foundations

These sections describe the basic entities and structures that appear throughout contact-center systems.

## 1. CX and Contact Center Fundamentals

| Term | Definition |
| --- | --- |
| **CX - Customer Experience** | The overall experience a customer has with an organization across interactions, channels, products, and services. |
| **Contact Center** | A modern call center. It manages inbound and outbound customer communications through a variety of channels — not only voice, but also email, chat, messaging, and social. |
| **Call Center** | A location or operation that handles a high volume of telephone calls, typically voice only. A contact center is the broader, multi-channel version. |
| **CCaaS - Contact Center as a Service** | A cloud-based customer experience solution that lets a company use a provider's contact-center software instead of running its own. |
| **CRM - Customer Relationship Management** | The system of record for customer data — who they are, what they bought, open tickets, past contacts. The contact center handles the live interaction; the CRM holds the history. A **screen pop** shows the agent that record when the customer connects. |
| **Omnichannel** | A model in which channels are connected and customer context can follow the customer between them. |
| **Multichannel** | Supporting many interaction types — voice, web chat, email, callback, and social — even if those channels do not share context. |
| **Voice Channels** | Phone calls, voicemail, and callbacks. The primary artifact is audio, which has to be transcribed before anything downstream can read "what was said" (see §5). |
| **Digital Channels** | Text-based interactions such as web chat, messaging, social, and email. Verbatim — what the participant sent is what you have. Some are synchronous (chat), others asynchronous (messaging, email), which changes what response-time metrics mean. |
| **Interaction / Conversation** | A communication, or series of communications, between two or more parties — which may include a system such as an IVR or bot — on a channel such as a call, chat, email, or message. *Conversation* is the precise unit in data models and APIs: one ID covering every participant, transfer, and media session. *Interaction* is the looser word, and can mean the whole conversation or just one part of it, such as the stretch a single agent handled. |
| **Customer Journey** | Everything a customer does with an organization over time, across every **touchpoint** — any point of contact, from a website visit to a phone call to an email. One interaction is a single step in a longer journey, which is why a call that went well can still sit inside a bad journey. |
| **Inbound** | An interaction initiated by the customer. |
| **Outbound** | An interaction initiated by the organization. |
| **Interaction Purpose** | The operational category of the contact — service, sales, collections, or retention. Different from **intent** (§4), which comes from the customer's words. |
| **Agent** | The person who is the primary point of human customer contact. Handles inbound or outbound calls and other interactions. Also called a customer service representative (CSR). |
| **Queue** | A waiting line of interactions. Despite the name, it is not FIFO: priority, skill matching, and wait-time-based expansion all reorder it, so arrival order does not determine who is served next. |
| **IVR - Interactive Voice Response** | A telephony industry term for the customer experience options pertaining to call flows, DTMF (keypad tones) and speech entry, menus, and audio prompting. Callers can **barge in** — speak or press a key during a prompt and have that response recognized. |
| **Self-Service** | The automated handling a customer goes through before reaching an agent — an IVR menu or bot following a preset set of steps and branches called a **flow**. Resolving the issue with no human is **containment**; steering the customer to a cheaper channel is **deflection**; failing means it escalates to an agent. Containment and deflection look like wins in a dashboard, but neither proves the problem was solved. |

---

## 2. Conversation Data Model

Contact-center data is usually hierarchical. Understanding this structure is essential when working with analytics APIs, transcripts, recordings, or evaluation data.

| Term | Definition |
| --- | --- |
| **Participant** | A party in an interaction. The external participant is normally the customer; the internal participant is normally an agent or employee. An IVR or bot can also be a participant. |
| **Session** | A participant's connection to a conversation using a particular medium. A participant may have more than one session. |
| **Segment** | A discrete portion of a session representing a state such as alerting, interacting, hold, or wrap-up. Many duration metrics are calculated from segments. |
| **Conversation Detail Record** | The analytics record of a completed conversation: participants, sessions, segments, timestamps, and metrics. Older voice systems call this a **CDR** (Call Detail Record). Its conversation ID is the key you join on — the transcript, recording, metadata, and evaluations are stored separately. |
| **Metadata** | Structured facts about an interaction, such as queue, agent, timestamps, duration, routing information, and wrap-up code. |
| **Interaction Content** | The actual content of an interaction — audio, transcript text, messages, and attachments. |
| **Disposition** | The outcome class of an interaction, such as resolved, sold, or no answer. Agents typically record it by selecting a **wrap-up code**. |

---

## 3. Routing and Interaction Management

| Term | Definition |
| --- | --- |
| **ACD - Automatic Call Distribution** | The system that answers incoming interactions and assigns waiting interactions to the most appropriate agent using routing rules. ACD interactions are associated with a queue. Often confused with the **IVR**: the ACD routes, the IVR does self-service. |
| **Routing** | Deciding which resource should receive an interaction — a queue, a particular agent, a bot, or an outside number — and when. Because the decision uses skills, priority, and who is free at that moment, two identical requests a minute apart can land in different places. |
| **Skills-Based Routing** | Matching a customer to the agent best equipped to help them, using requested language, skills, and the nature of the request. |
| **Callback** | Offering the customer a return call instead of waiting on the line. A **virtual queue** holds their place without keeping them connected. |
| **Concurrency - configured capacity** | The maximum number of interactions an agent is set up to handle at once, per channel. An agent juggling five chats writes shorter replies with longer gaps than one on a single chat. |
| **Presence / Status** | The work mode an agent selects — available for interactions, on a break, in a meeting, offline. The exact names vary by platform. |
| **Routing Status** | Whether an agent is currently eligible to receive routed interactions. Set by the system from the agent's activity rather than chosen by the agent, so it can disagree with their selected presence. |
| **After Call Work - ACW** | Work an agent performs immediately after an interaction — notes, wrap-up codes, updating records. If the agent must finish it before taking the next contact, ACW is included in average handle time. |
| **Wrap-Up Code** | Agents use wrap-up codes to classify each interaction they handle. For example, complaints, wrong numbers, or orders. Tracked for reporting, and used to see why customers are contacting the organization. |
| **Transfer** | Handing a live interaction to another agent, queue, or outside destination rather than continuing to handle it. |

---

# Part II — How Interactions Are Understood

These sections cover AI, speech processing, analytics, and measurable conversational behaviors.

## 4. Artificial Intelligence and Automation

| Term | Definition |
| --- | --- |
| **Intent** | What the customer is trying to do, inferred from their language — "cancel my policy," "where is my order." Different from **interaction purpose** (§1), which is the operational category of the contact (sales vs service). |
| **Bot** | A program designed to simulate conversation with a human user, over text or voice. |
| **Virtual Agent / AI Agent** | An AI-powered conversational bot that handles customer interactions on voice or digital channels and can hand off to a live agent. Different from **agent**, which normally means a person. |
| **Agent Assist / Copilot** | An AI assistant that gives a human agent real-time information, suggestions, and automated actions during an interaction. |
| **Sentiment Analysis** | Estimating positive, negative, or neutral emotional expression in language. |
| **Empathy Detection** | Evaluating language or behaviors associated with empathetic communication. Detects empathetic *phrasing*, which is not the same as empathy. |

---

## 5. Speech and Transcription

| Term | Definition |
| --- | --- |
| **ASR - Automatic Speech Recognition** | The translation of spoken words into text. Also called speech to text (STT). |
| **Transcript / Transcription** | The transcript is the text record of a conversation; transcription is the process that produces one from audio. Text channels have a transcript with no transcription step, which is why the two words are not interchangeable. |
| **Verbatim Text vs. Transcribed Text** | Chat and messaging logs are verbatim — exactly what the person typed. ASR transcripts are reconstructions with word errors and dropped words. Comparing a behavioral metric across the two shows differences caused by the transcription, not the agent. |
| **Confidence Score** | A numeric value ASR emits alongside each recognized word or phrase, indicating how sure the recognizer is. Not a probability of correctness unless calibrated to be one; low-confidence tokens are the ones most likely to be wrong. |
| **Real-Time vs. Post-Call Transcription** | A transcript produced during the conversation versus after it ends. Real-time allows live assistance but is less accurate; post-call has the whole recording to work from. |
| **Speaker Diarization** | Working out which parts of the audio each speaker said. Every per-speaker metric depends on getting this right — talk-to-listen ratio, interruptions, who said a required phrase. Labels are more reliable when the two sides were recorded on separate channels. |
| **Word Timing / Utterance Timestamp** | Time offsets associating transcript text with the original audio. These timestamps enable measurement of pauses, talk-over, speech rate, and other conversational behavior. Text-channel reply gaps come from message timestamps, not word timings. |
| **Redacted Transcript** | A transcript with sensitive information (PII, payment-card numbers, health data) removed or masked. Treat the gaps as missing text, not as silence. Redaction applies to this artifact; it is not anonymization of the customer record as a whole. |

---

## 6. Speech and Text Analytics

| Term | Definition |
| --- | --- |
| **Interaction Analytics** | Turning unstructured data from voice, email, chat, and other channels into structured data that can be searched and analyzed. |
| **Topic** | A subject identified within interactions, either predefined or discovered automatically. |
| **Sentiment Trend** | How detected sentiment changes over the course of an interaction. Usually more informative than a single overall score, since recovery and deterioration look identical in an average. |

---

## 7. Conversation Behaviors and Transcript Metrics

These metrics are commonly used by quality, coaching, analytics, and AI systems. Rows marked (voice) depend on audio or word-level timings; the rest work on any transcript, including text channels.

| Term | Definition |
| --- | --- |
| **Talk-to-Listen Ratio** (voice) | Agent talk time : customer talk time, often written 60:40. Not the same as the agent's share of all speech (agent talk / total talk). A **monologue** is the same concern measured locally — one participant talking without a break past a chosen threshold. |
| **Overtalk / Interruption** (voice) | Both participants speaking at once. Counted either as total overlapping time (overtalk) or as how often one starts while the other is still going (interruption rate). |
| **Reply Gap / Response Latency** | The average time between turns within one conversation. **FRT** (§10) covers only the first reply; this is the per-turn version, and the one that still works on an asynchronous thread where gaps run to minutes or hours instead of seconds. |
| **Speech Rate** (voice) | The rate at which someone speaks, commonly measured in words per minute. |
| **Script Adherence** | Whether an agent followed the script — the written words and logic they are supposed to use while handling the interaction. |
| **Required Disclosure / Compliance Phrase** | Wording that must be communicated for regulatory, contractual, or policy reasons. Presence or absence is usually binary and auditable, which makes this the most defensible category of automated detection. |

---

# Part III — How People Are Managed

These sections cover how agents are scheduled, evaluated, and coached.

## 8. Workforce Engagement Management

| Term | Definition |
| --- | --- |
| **WEM - Workforce Engagement Management** | The broader set of tools for quality, coaching, performance, and employee engagement, together with workforce management. |
| **WFM - Workforce Management** | Putting the right people in the right places at the right times — typically forecasting, scheduling, and skills management. |
| **Adherence** | How closely an employee's actual activity matches what was scheduled at that time. Working the right total hours at the wrong times still counts as poor adherence. |
| **Shrinkage** | Time that agents are scheduled to work but are not available to handle interactions. Coaching time is shrinkage — which is the structural reason coaching is chronically under-scheduled. |

---

## 9. Quality Management and Coaching

| Term | Definition |
| --- | --- |
| **QM - Quality Management** | Tools and processes to ensure interactions are handled effectively. Includes recording, monitoring, evaluation, reporting, and calibration. |
| **Quality Evaluation** | A structured review of one interaction against defined criteria, producing a score. Normally done after the interaction ended, by a supervisor or a dedicated evaluator, on a sampled subset rather than on everything. |
| **Quality Evaluation Score** | The percentage score an evaluation produces, and the number a coaching program trends over time. |
| **Agent Scorecard** | A consolidated view of one agent's metrics and evaluation results over a period, rather than for a single interaction. The unit a coaching program tracks change against. |
| **Peer Comparison** | An agent's results set against a reference group — usually their queue or team — rather than against a fixed target. Comparable only where the agents involved handle a similar mix of interaction types and purposes. |
| **Evaluation Form** | The scorecard an evaluation is filled out against. Questions are grouped into sections; each question offers answer options worth points, and questions or sections can be weighted so some count for more than others. |
| **Quality Expectations** | What counts as good handling: which criteria are evaluated, the weight each one carries, and the score thresholds that pass or fail. **Configurable** means an administrator can change all three without a developer, which is why they are stored as form data instead of written into code. |
| **Survey** | The form sent to the *customer* after an interaction, and the completed response they submit. Distinct from an evaluation, which scores the agent. CSAT and CES are usually collected this way. |
| **Evaluator** | A user assigned to complete quality evaluations and calibration evaluations. |
| **Self-Evaluation** | An agent scoring their own interaction, often using the same form as an evaluator. The gap between self-score and evaluator score is frequently more instructive than either alone. |
| **Calibration** | A quality feature for scoring consistency. Administrators assign the same recorded interaction to multiple evaluators; results are compared so variation is easy to see. |
| **Sampling** | Selecting a subset of interactions for evaluation. Manual QM usually reviews only a small fraction of total interactions, often well under 5%, which is the central limitation automated scoring claims to address. |
| **AI Scoring [Genesys]** | Genesys name for AI that answers evaluation-form questions from the transcript, so interactions can be scored at scale without a human reading each one. Industry name: automated quality management (AQM). A supervisor still reviews and approves the result. |
| **AI Summarization [Genesys]** | Genesys name for an AI-generated short narrative of a call or chat, so someone can see the point without reading the whole transcript. |
| **AI Insights [Genesys]** | Genesys name for structured findings pulled from the same transcript: reason for contact, resolution, action items, and why sentiment moved. A summary is a paragraph; insights are labeled fields you can filter and trend. |
| **Interaction Recording** | Recording voice or digital interactions for quality, compliance, analytics, training, or dispute resolution. |
| **Coaching** | Feedback given to agents as part of quality management and training. It can be a regular performance review, or happen in real time during a customer interaction. |
| **Gamification** | Applying mechanics such as points, challenges, achievements, or leaderboards to employee engagement. |

### Live supervisor assistance

Distinct from the retrospective sense of coaching above. The overloading of the word *coach* is a genuine source of confusion in project discussions.

| Term | Definition |
| --- | --- |
| **Monitor / Silent Monitoring** | A supervisor listens to an in-progress interaction in real time without being heard. |
| **Coach / Whisper** | A supervisor speaks to the agent during a live interaction while remaining inaudible to the customer. |
| **Barge-In (live)** | A supervisor joins the interaction as an audible participant. Different from IVR barge-in (§1), where the *caller* speaks during a prompt. |

---

# Part IV — Measuring Results

These sections cover the metrics used to report on performance and customer experience.

## 10. Contact Center Performance Metrics

| Term | Definition |
| --- | --- |
| **Offered** | An interaction that entered a queue and was made available to be answered. It is the denominator for answer rate and abandon rate, so what does and does not count as offered decides what those percentages actually mean. |
| **AHT - Average Handle Time** | The average time agents spent handling interactions, including talk, hold, and after-call work. Falling AHT can mean improved efficiency, or rushed customers who contact you again. |
| **Talk Time** | The time an agent spends actually talking with the customer, excluding hold and after-call work. Short talk time next to poor first-contact resolution is the classic warning sign — it may indicate rushed handling rather than efficiency. |
| **ASA - Average Speed of Answer** | The average time an interaction waits in queue before an agent answers. Answered interactions only, which is why it differs from **average wait time** — that also counts interactions the customer abandoned or that left the queue. Neither includes time before the interaction entered the queue. |
| **FRT - First Response Time** | How long the organization takes to reply to a customer inquiry after it arrives. The digital counterpart to ASA, especially useful on asynchronous channels where responsiveness is measured between messages rather than by queue wait. |
| **Service Level** | The percentage of conversations answered within a defined time threshold, usually written as a pair — 80/20 means 80% answered within 20 seconds. This is the target most contact centers are staffed and managed against. |
| **Answer % / Answer Rate** | The share of interactions offered that were answered — answered divided by **offered**. The remainder are abandons and, where the metric is scoped to an agent, interactions the agent declined or let time out. |
| **Average Alert Time** | How long an offered interaction alerts before the agent accepts it, averaged across alerts. It measures the agent alone, with no queue or customer behavior mixed in, which makes it straightforward to coach on. |
| **Abandon Rate** | The share of interactions that disconnected before reaching an agent, out of those **offered**. An inbound abandon entered the queue and dropped while waiting. |
| **FCR - First Contact Resolution** | Percentage of customer issues resolved without requiring another contact. Difficult to measure honestly, since it requires knowing the customer did not return through any channel for the same reason. |
| **Transfer Rate** | The share of interactions an agent answered and then transferred, blind or consult. Platforms differ on which queue the transfer is counted against. |
| **Hold Time** | The total time an agent places a customer on hold during an interaction. The denominator matters: some averages divide by every interaction handled, others only by the ones actually put on hold, and the two produce very different numbers. |
| **Hold and ACW Ratios** | Hold time or after-call work expressed as a share of total handle time instead of in seconds. Ratios compare fairly between agents who handle interactions of very different lengths, which raw durations do not. |
| **Interactions per Hour** | Interactions handled divided by on-queue time. A throughput measure, so it rises both when an agent genuinely gets more efficient and when they start rushing people. |
| **Occupancy / Utilization** | Two ways of measuring how busy agents are. Occupancy divides handling time by time logged in and available; utilization divides it by all paid time, including training and other logged-out work. The larger denominator makes utilization the lower number. |
| **Concurrency Rate - observed** | The average or actual number of simultaneous interactions being handled, especially in digital channels. Where available, this is what you use to control for the configured-concurrency confounder described in Section 3. |

---

## 11. Customer Experience Metrics

| Term | Definition |
| --- | --- |
| **CSAT - Customer Satisfaction** | A measure of customer satisfaction, commonly collected through a post-interaction survey. Response rates are typically low and skewed toward the very satisfied and the very angry. |
| **CES - Customer Effort Score** | A measure of how much effort customers believe was required to accomplish their objective. |
| **NPS - Net Promoter Score** | A measure based on how likely a customer is to recommend the company, product, or service. Asked about the relationship overall rather than one interaction, so it moves slowly and is hard to attribute to a single agent. |

---

*Generated with assistance from Claude and the [Genesys Cloud glossary](https://help.genesys.cloud/glossary).*
