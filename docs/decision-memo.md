# Decision memo: choose an experiment, not a revenue promise

**Decision owner:** hypothetical retail retention manager. **Status:** offline recommendation; no campaign or client engagement occurred.

## The decision

If a retailer can contact only a fraction of its eligible existing customers, does a fitted purchase-propensity ranking identify more likely purchasers than a simple recency rule? Evaluate at 5%, 10%, 20% and 40% capacity. These fractions are sensitivity scenarios, not actual marketing budgets.

The model is fixed after an April 2011 training snapshot. July and October are separate future evaluations. Only customers observed before each cutoff are scored; labels require a complete subsequent 60-day observation window. Different snapshots contain overlapping customers and must not be pooled as independent replications.

## Evidence to inspect

- `outputs/policy_comparison.csv`: selected counts, model and recency purchase rates, random-selection expected rate, paired differences and 95% bootstrap intervals.
- `outputs/model_evaluation.csv`: ranking metrics beyond one contact capacity.
- `outputs/calibration.csv`: score calibration by probability band.
- `outputs/quality_report.json`: explicit aggregate checks and failure details.
- `outputs/run_manifest.json`: actual run time, source hash, library versions and artifact/code hashes. This records a current computation, not historical employment.

The customer bootstrap resamples the same customers for both policies within a snapshot, reselecting each policy's top fraction in every draw. The interval is conditional on a fitted model, observed customers and historical market. It omits training uncertainty, temporal shifts and correlated households. It does not turn a propensity difference into a treatment effect. Stable customer-ID ordering resolves score ties without looking at labels.

## Recommendation and stop rules

Use the comparison to decide whether the additional modeling complexity warrants an experiment. Do not assume likely purchasers are persuadable: a recency or model policy can select customers who would buy anyway. A negative or wide interval should reduce confidence in a policy advantage. Reviewing multiple budgets after outcomes is exploratory; freeze the chosen policy and capacity before a new evaluation.

For a real pilot, obtain lawful contact eligibility, contemporary store data, margin assumptions and an agreed question. Randomize eligible customers within the chosen population to treatment and business-as-usual holdout. Specify one primary outcome, follow-up horizon, exclusions, minimum detectable effect and sample size before launch. Measure incremental contribution after discounts, contact and fulfillment costs. Track unsubscribes and returns as guardrails. No claim of incremental profit is supported until that experiment exists.

## Operational boundaries

The pipeline stops on a changed source checksum or broken source schema; missing customer IDs remain allowed and disclosed. The current extract has 42 invoices with same-day timestamp variation; order time is the earliest line timestamp. This is a recorded warning. Cross-day variation blocks a release. Sales and invoice grain must reconcile; retention must stay in bounds. These checks cannot prove accounting correctness or identify legitimate identical invoice lines. The local DuckDB file is a rebuildable analytical cache, not a production warehouse. Authentication, tenant isolation, deployment monitoring and client-data ingestion are outside this portfolio's implemented scope.
