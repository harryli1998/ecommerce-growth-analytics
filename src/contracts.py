"""Fail-closed input contracts and auditable aggregate quality checks."""
import numpy as np
import pandas as pd

SOURCE_SHA256 = 'f5385cbb54bbebf7196389109c6b0621faab0c304e3702548165e71c84aede8b'
REQUIRED = {'InvoiceNo', 'StockCode', 'Description', 'Quantity', 'UnitPrice',
            'InvoiceDate', 'CustomerID', 'Country'}


def validate_source_hash(actual):
    if actual != SOURCE_SHA256:
        raise ValueError('Source checksum changed. Review provenance before updating SOURCE_SHA256.')


def validate_input(raw):
    missing = REQUIRED - set(raw.columns)
    if missing:
        raise ValueError(f'Missing source columns: {sorted(missing)}')
    if raw.empty:
        raise ValueError('Source is empty')
    for col in ['InvoiceNo', 'StockCode', 'InvoiceDate', 'Quantity', 'UnitPrice', 'Country']:
        if raw[col].isna().any():
            raise ValueError(f'Unexpected nulls in {col}')
    for col in ['Quantity', 'UnitPrice']:
        values = pd.to_numeric(raw[col], errors='coerce')
        if not np.isfinite(values).all():
            raise ValueError(f'Nonfinite or nonnumeric {col}')
    if pd.to_datetime(raw.InvoiceDate, errors='coerce').isna().any():
        raise ValueError('Unparseable invoice timestamp')


def quality_checks(con, purchases):
    rows = []
    def check(name, passed, detail):
        rows.append({'check': name, 'status': 'PASS' if passed else 'FAIL', 'detail': detail})
    orders = con.sql('SELECT * FROM orders').df()
    raw_sales = float((purchases.Quantity * purchases.UnitPrice).sum())
    delta = abs(float(orders.revenue.sum()) - raw_sales)
    check('line_to_order_sales', delta < .01, f'Absolute difference GBP {delta:.8f}; tolerance 0.01')
    check('unique_invoice_grain', not orders.order_id.duplicated().any(), 'One customer grouping per purchase invoice')
    spans = con.sql("SELECT InvoiceNo, count(distinct InvoiceDate) timestamps, date_diff('day', min(InvoiceDate), max(InvoiceDate)) AS day_span FROM purchases GROUP BY 1").df()
    multi = int((spans.timestamps > 1).sum())
    check('invoice_calendar_day_consistency', bool((spans.day_span == 0).all()), 'Purchase invoice timestamps must fall on one calendar day')
    rows.append({'check':'within_invoice_timestamp_variation', 'status':'WARN' if multi else 'PASS',
                 'detail':f'{multi} invoices have multiple timestamps; order time uses earliest line timestamp. Same-day variation is accepted, not silently discarded.'})
    check('cohort_bounds', con.sql('SELECT count(*) FROM cohorts WHERE retention < 0 OR retention > 1 OR retention IS NULL').fetchall()[0][0] == 0, 'Observed retention in [0,1]')
    check('monthly_sales_reconcile', abs(float(con.sql('SELECT sum(gross_sales) FROM monthly').fetchall()[0][0]) - raw_sales) < .01, 'Monthly sales reconcile to purchase lines')
    eligible = con.sql('SELECT count(*) FROM repeat_90').fetchall()[0][0]
    check('mature_repeat_population', eligible > 0, f'{eligible} customers with full follow-up')
    return rows
