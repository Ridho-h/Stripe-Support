# Evaluation Rubric — Stripe Support Agent Dashboard

Scores the 4-agent pipeline (Triage → Retrieval → Drafting → Escalation) against
`labeled_tickets.json`. Mirrors the eval structure used in Multi-Agent-Coding-Assistant
and Multimodal-Food-Agent: per-stage metrics + a composite score, broken down by
difficulty tier.

---

## 1. Triage Accuracy (weight: 25%)

Scored per ticket against `category` and `urgency` ground truth.

| Metric | Definition | Pass threshold |
|---|---|---|
| Category Accuracy | predicted `category` == ground truth `category` | ≥ 90% |
| Urgency Accuracy (exact) | predicted `urgency` == ground truth `urgency` | ≥ 75% |
| Urgency Accuracy (±1 level) | predicted urgency within one level of ground truth (e.g. `high` vs `critical` counts, `low` vs `critical` doesn't) | ≥ 95% |

Urgency uses the ±1 tolerance as the headline number — mislabeling `high` as
`critical` is a minor miss; mislabeling `critical` as `low` is a real failure and
should show up separately as a "severe urgency miss" count, reported even though
it's rare.

## 2. Retrieval / Citation Quality (weight: 25%)

Scored against `doc_topic` ground truth — this is the field your labeled set exists
to support, so weight it seriously rather than eyeballing it.

| Metric | Definition |
|---|---|
| Citation Precision | Of the doc passages the Retrieval Agent returned, % that are actually relevant to `doc_topic` (manual or keyword-overlap judgment) |
| Citation Recall@3 | Whether the correct `doc_topic` appears anywhere in the top-3 retrieved passages |
| Hallucinated Citation Rate | % of drafted replies that cite a doc source not actually returned by retrieval — this should be 0%; any nonzero value is a correctness bug, not a quality nit |

## 3. Escalation Judgment (weight: 25%)

Scored against `escalate` ground truth (8 of 30 tickets are `true`).

| Metric | Definition | Pass threshold |
|---|---|---|
| Escalation Recall | Of tickets that SHOULD escalate, % correctly flagged | ≥ 90% (false negatives here are the costly failure mode — a missed security/fraud escalation is worse than an unnecessary one) |
| Escalation Precision | Of tickets flagged for escalation, % that actually needed it | ≥ 70% (over-escalating is a lesser but still real cost) |
| Escalation Reasoning Quality | Does the agent's stated reason match the actual driver (security/revenue/complexity) rather than a generic "this seems important"? Score 0-2 per ticket, manually reviewed on the 8 true-escalation tickets |

## 4. Response Draft Quality (weight: 25%)

The one genuinely qualitative axis — score manually (or with an LLM-as-judge you
report separately from the agent under test, never the same model config) on a
0–2 scale per criterion, per ticket:

| Criterion | 0 | 1 | 2 |
|---|---|---|---|
| Factual grounding | Contradicts or invents info | Mostly accurate, minor vagueness | Fully grounded in retrieved doc content |
| Tone/appropriateness | Wrong register (e.g. casual for a critical security ticket) | Acceptable | Matches urgency and audience |
| Actionability | Vague, no next step | Some next step given | Clear, specific next step or fix |

Composite draft score = average of the three, normalized to 0–100%.

---

## Composite Score

```
overall = 0.25*triage_acc + 0.25*citation_recall@3 + 0.25*escalation_recall + 0.25*draft_quality
```

Report this **overall + all four sub-scores**, never the composite alone — a single
number hides whether failures cluster in one stage (e.g. good triage but weak
retrieval), which is the actionable insight for a portfolio reviewer or for you
when iterating on prompts.

## Reporting format

Break results out the same way your other two repos do — by difficulty tier
(easy/medium/hard) and by category — not just a single aggregate, so the eval
table tells a story instead of one flat percentage:

```
| Category            | n  | Triage Acc | Citation Recall@3 | Escalation Rec. | Draft Qual. |
|----------------------|----|------------|--------------------|-----------------|-------------|
| webhooks             | 4  | ...        | ...                | ...             | ...         |
| payments_charges     | 2  | ...        | ...                | ...             | ...         |
| ...                  |    |            |                    |                 |             |
| Overall              | 30 | ...        | ...                | ...             | ...         |
```

## What NOT to do

- Don't average escalation precision and recall into one F1 and stop there — for
  this use case, recall failures (missed critical escalations) and precision
  failures (over-escalation) have very different real-world costs, so report
  both, not a blended number.
- Don't skip the "severe urgency miss" and "hallucinated citation" counts even
  though they're usually zero — a rubric that only reports averages can hide a
  single dangerous failure inside a good-looking aggregate.
