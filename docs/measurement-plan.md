# Conversion and marketing measurement plan

The public transaction dataset does not contain funnel traffic, channel attribution, advertising cost, consent or margin. Do not infer conversion rates or marketing ROI from buyers alone.

| Question | Required data | Definition |
|---|---|---|
| Purchase conversion | session_id, session_start, purchase event, bot/internal flags | Eligible sessions with at least one purchase / eligible sessions; align timezone and attribution window |
| Funnel loss | timestamped view_item, add_to_cart, begin_checkout, purchase | Users or sessions reaching next step / those reaching prior step; choose one grain and enforce event order |
| CAC | campaign spend, first-time customer identity | Attributed acquisition spend / genuinely new customers; first observed in a short extract is insufficient |
| ROAS | spend, attributed purchase value, refunds | Attributed net revenue / ad spend; document attribution model and lag |
| Incremental retention | randomized assignment, exposure, purchases | Treatment minus control 90-day repeat rate, with confidence interval |

Use stable anonymous IDs with appropriate consent. Reconcile purchases to order IDs; deduplicate events; separate order time and refund time. Pre-register experiment primary outcome, sample size, minimum detectable effect, refund/unsubscribe guardrails and stopping rule. No experiment has been run in this portfolio.
