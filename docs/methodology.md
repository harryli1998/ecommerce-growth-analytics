# Advanced analytics methodology

## Signed-sales bridge

`sql/advanced.sql` reconciles gross purchase sales, negative-quantity value and residual exceptions to the signed value of every deduplicated ledger line. Negative lines may include returns, cancellations and inventory adjustments. Without original-order linkage, tax policy and fulfillment data this is not recognized net revenue. Month is the date of the recorded line, not the original purchase month.

## Product association rules

Use invoices as baskets, deduplicate product presence per invoice, restrict product codes to five digits with an optional alphabetic suffix, and exclude baskets outside 2–50 unique products. Select the 100 most frequently purchased eligible SKUs. Candidate directed pairs must appear in at least 30 baskets and have lift above one. Keep 100 strongest rules. Support divides joint basket count by all eligible baskets, including those without a top-100 SKU. Confidence divides joint baskets by antecedent baskets. Lift divides confidence by consequent prevalence.

This bounded search is reproducible but omits the long tail and single-product baskets. It is exploratory on the full dataset, not held-out evidence of profitable recommendation quality. Size variants, seasonality and wholesale purchasing are confounders. Test availability, margin, relevance and incremental contribution before acting.

## Temporal repurchase prediction

**Task:** among identified customers with at least one previous observed purchase, predict another purchase in [cutoff, cutoff + 60 days).

**Features:** days since last purchase; order count and gross purchase value in the prior 90 days; days since first observed purchase. Apply log1p, training-only standardization and logistic regression with fixed C=1. No feature can use purchases at or after its cutoff. Positive purchase orders only; a returned order may still count as a purchase.

**Time separation:** train at April 1, 2011 (labels end exclusively May 31); evaluate at July 1 (labels end August 30) and October 1 (labels end November 30). All horizons end before the dataset endpoint. Training label availability precedes both test cutoffs. Same identities can recur because the use case is scoring an existing customer base. This is not an unseen-customer test. Single training date and two test periods do not establish production stability. No tuning on test outcomes.

**Evaluation:** compare ROC AUC, average precision and top-20% precision/lift with a recency-only ranking. Report Brier score and fixed probability-band calibration for logistic regression. Random selection has expected lift 1 and average precision near population prevalence. Ranking ties use stable order. No confidence interval is claimed, and correlated customers/cohort seasonality should be considered before statistical comparisons. A weaker model should remain visible rather than being hidden or retuned after seeing the tests.

Reference: [scikit-learn average precision definition](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html).

**Decision limit:** high purchase probability is not high incremental campaign response. A naturally returning customer might receive an unnecessary discount. Randomized treatment/control data are required for uplift modeling.

## Campaign economics

The interactive scenario uses contacts × (assumed incremental order-rate uplift × contribution per incremental order − contact cost). Break-even uplift = contact cost / contribution per incremental order. This is transparent planning arithmetic, not a measured forecast. No real campaign, customer engagement or commercial result is asserted.
