# Findings and decisions

## Executive readout

- Gross purchase sales were £10,642,110.80 across 19,960 purchase orders; AOV was £533.17. These figures do not deduct returns or cancellations.
- 47.5% of 3,370 eligible identified customers made a later purchase within 90 days of first observed purchase. Customers without full follow-up are excluded.
- The strongest complete month was 2011-11-01, with £1,503,867 in gross purchase sales.
- November versus October sales grew 30.6%, while orders grew 35.7% and AOV changed -3.8%. This decomposition is descriptive; it does not demonstrate campaign impact.

## Marketing decisions to test

There are 285 customers in the illustrative lapsed-repeat segment. Test a win-back campaign against a randomized holdout, subject to consent and current contact eligibility. Evaluate incremental 90-day repeat and contribution profit, rather than gross attributed revenue alone.

The one-time-observed segment has 1,493 customers. Some entered near the extract end, so this count is not a fair failure-to-retain rate. Use mature acquisition cohorts and sufficient follow-up before targeting or comparing performance.

Retention varies by cohort age; compare cohorts at the same month index and keep unobserved future months blank. December 2011 is incomplete and is excluded from retention and the default sales trend.

## Data quality and interpretation

The source contains 541,909 rows. The pipeline removes 5,268 exact duplicates and excludes 11,763 remaining nonpurchase rows. 132,186 retained purchase rows lack a customer ID: sales include these, customer analyses do not. Wholesaler behavior and invoice charges may affect AOV and repeat patterns.

No visitor-conversion, CAC, ROAS, campaign uplift or profit result is supported by these records. See measurement-plan.md for required instrumentation. No marketing experiment was executed and no business outcome is claimed.

## Interview discussion

Explain order versus line grain, why purchase sales differ from net revenue, why first observed purchase differs from acquisition, how right censoring changes the repeat denominator, and how to distinguish association from incremental campaign effect. These methods were implemented with AI assistance and should be reviewed before presenting as a portfolio.
