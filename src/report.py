"""Generate findings from artifacts rather than hand-copying headline figures."""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def write_report():
    out=ROOT/'outputs'
    s=json.loads((out/'summary.json').read_text())
    m=pd.read_csv(out/'monthly.csv')
    full=m[m.month < '2011-12-01']
    peak=full.loc[full.gross_sales.idxmax()]
    prior=full.iloc[-2]
    last=full.iloc[-1]
    segments=pd.read_csv(out/'segments.csv')
    counts=segments.segment.value_counts()
    text=f'''# Findings and decisions

## Executive readout

- Gross purchase sales were £{s['gross_sales']:,.2f} across {s['orders']:,.0f} purchase orders; AOV was £{s['aov']:,.2f}. These figures do not deduct returns or cancellations.
- {s['repeat_90_rate']:.1%} of {s['eligible_customers']:,.0f} eligible identified customers made a later purchase within 90 days of first observed purchase. Customers without full follow-up are excluded.
- The strongest complete month was {peak['month']}, with £{peak['gross_sales']:,.0f} in gross purchase sales.
- November versus October sales grew {last.gross_sales/prior.gross_sales-1:.1%}, while orders grew {last.orders/prior.orders-1:.1%} and AOV changed {last.aov/prior.aov-1:.1%}. This decomposition is descriptive; it does not demonstrate campaign impact.

## Marketing decisions to test

There are {counts.get('Lapsed repeat',0):,} customers in the illustrative lapsed-repeat segment. Test a win-back campaign against a randomized holdout, subject to consent and current contact eligibility. Evaluate incremental 90-day repeat and contribution profit, rather than gross attributed revenue alone.

The one-time-observed segment has {counts.get('One-time observed',0):,} customers. Some entered near the extract end, so this count is not a fair failure-to-retain rate. Use mature acquisition cohorts and sufficient follow-up before targeting or comparing performance.

Retention varies by cohort age; compare cohorts at the same month index and keep unobserved future months blank. December 2011 is incomplete and is excluded from retention and the default sales trend.

## Data quality and interpretation

The source contains {s['raw_rows']:,} rows. The pipeline removes {s['exact_duplicates_removed']:,} exact duplicates and excludes {s['excluded_nonpurchase_rows']:,} remaining nonpurchase rows. {s['missing_customer_purchase_rows']:,} retained purchase rows lack a customer ID: sales include these, customer analyses do not. Wholesaler behavior and invoice charges may affect AOV and repeat patterns.

No visitor-conversion, CAC, ROAS, campaign uplift or profit result is supported by these records. See measurement-plan.md for required instrumentation. No marketing experiment was executed and no business outcome is claimed.

## Interview discussion

Explain order versus line grain, why purchase sales differ from net revenue, why first observed purchase differs from acquisition, how right censoring changes the repeat denominator, and how to distinguish association from incremental campaign effect. These methods were implemented with AI assistance and should be reviewed before presenting as a portfolio.
'''
    (ROOT/'docs/findings.md').write_text(text)

if __name__=='__main__':
    write_report()
