# Product Vision

This document captures the philosophy behind this platform's recommendations
and its long-term direction. For what's actually built today, see the
[README](../README.md) and [Architecture Overview](./architecture/overview.md).
For what's planned and when, see [ROADMAP.md](./ROADMAP.md).

## The explainability principle

The AI never says:

> "You must become a software engineer."

Instead, every recommendation this platform produces explains:

- **Why the career matches** — the specific psychometric and vocational
  dimensions driving the recommendation
- **What evidence supports it** — the underlying similarity, interest
  alignment, and market data behind the score
- **Confidence level** — how strongly the evidence supports this specific
  recommendation, not a false sense of certainty applied uniformly
- **Assumptions made** — what the system inferred versus what the user
  explicitly told it
- **Factors reducing confidence** — gaps in the profile, incomplete
  assessment data, or weak signal on a given dimension
- **Factors increasing confidence** — strong alignment across multiple
  independent signals, not just one

This is a deliberate design constraint, not a UI nicety. A system that tells
someone what career to pursue, full stop, is making a claim it usually
cannot back up. A system that shows its work — including where it's
uncertain — builds trust and lets the person weigh the recommendation
against what they know about themselves that the system doesn't.

**Current implementation status:** the recommendation and explainability
engines (see `apps/backend/src/ai/explainability/`) already produce a
per-factor score breakdown, a confidence band (high/medium/low), driver
labels per factor, and a plain-language summary — see
[`docs/api/reference.md`](./api/reference.md#career-endpoints) for the exact
response shape. The more granular **assumptions-made** and
**confidence-increasing/-reducing factor lists** described above are a
richer version of this system and are tracked as an explicit enhancement —
see the roadmap below — rather than claimed as already shipped.

## Technical architecture: built versus planned

The platform's AI layer is designed around seven cooperating engines.
**Four are built.** Three are part of the long-term vision and are not yet
implemented — they're listed here because the architecture is designed to
accommodate them, not because they exist today.

| Engine | Status | What it does |
|---|---|---|
| Psychometric Engine | ✅ Built | Big Five + RIASEC scoring from assessment responses |
| Recommendation Engine | ✅ Built | FAISS similarity search + multi-factor weighted ranking |
| Explainability Engine | ✅ Built | Per-factor breakdown, confidence bands, plain-language summaries |
| Career Ontology Engine | 🟡 Partial | O*NET taxonomy data is integrated as a seed dataset; a dedicated ontology service with ESCO integration and richer taxonomy relationships is not yet built |
| Behavioral Engine | ⚪ Planned | Pattern recognition from how a user interacts with the platform over time — not from a one-time assessment |
| Skill Gap Engine | ⚪ Planned | Compares a user's current skills against a target career's requirements and surfaces the specific gap |
| Labor Market Engine | ⚪ Planned | Deeper market-signal integration beyond the current static outlook percentile — real-time demand signals, regional variation |

This honesty matters: a reader evaluating this project should be able to
tell, at a glance, what's running in production versus what's on the
drawing board.

## Long-term vision: from tool to companion

The platform is designed to evolve from a one-time career recommendation
tool into a **lifelong AI career companion**.

Instead of a single assessment producing a static result, the intended end
state is a system that:

- Continuously learns from a user's actual growth — new skills, completed
  courses, career moves — rather than only their initial assessment
- Adapts recommendations as the user's stated goals change over time
- Adapts to a changing labor market, not just a static snapshot taken once
- Acts as a running guide through a person's education and professional
  life, not a single point-in-time verdict

The objective underlying all of this is the same principle described
above, extended over time: help people make **informed, explainable,
evidence-based** career decisions — while being honest about uncertainty —
in service of their long-term fulfillment and adaptability, not a single
"correct answer" delivered once and never revisited.

This is a direction, not a committed timeline. See
[`docs/ROADMAP.md`](./ROADMAP.md) for the phases currently being built
toward it.
