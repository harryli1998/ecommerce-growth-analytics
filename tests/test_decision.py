import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
import pandas as pd
import pytest
from decision import policy_comparison
from contracts import validate_input, validate_source_hash, SOURCE_SHA256


def test_paired_identical_policies_have_zero_difference():
    f = pd.DataFrame({'customer_id':list('abcd'), 'returned':[1,0,1,0],
                      'probability':[.9,.7,.5,.1], 'recency':[1,2,3,4]})
    r = policy_comparison(f, fractions=(.25,1), draws=100)
    assert (r[['precision_difference','difference_ci_low','difference_ci_high']] == 0).all().all()
    assert r.selected_customers.tolist() == [1,4]


def test_policy_rejects_duplicate_customers_and_invalid_budget():
    f = pd.DataFrame({'customer_id':['a','a'], 'returned':[0,1], 'probability':[.2,.9], 'recency':[2,1]})
    with pytest.raises(ValueError, match='One row'): policy_comparison(f)
    with pytest.raises(ValueError, match='Budget'): policy_comparison(f.iloc[:1], fractions=(0,))


def test_contract_blocks_changed_source_and_schema():
    validate_source_hash(SOURCE_SHA256)
    with pytest.raises(ValueError, match='checksum'): validate_source_hash('different')
    with pytest.raises(ValueError, match='Missing'): validate_input(pd.DataFrame({'Quantity':[1]}))


def test_input_contract_rejects_nonfinite_amounts():
    f = pd.DataFrame({'InvoiceNo':['1'], 'StockCode':['12345'], 'Description':['item'],
                      'Quantity':[1], 'UnitPrice':[float('inf')], 'InvoiceDate':['2011-01-01'],
                      'CustomerID':[None], 'Country':['UK']})
    with pytest.raises(ValueError, match='Nonfinite'): validate_input(f)
    f['UnitPrice'] = 10
    validate_input(f)  # Missing customer identity is allowed, not fabricated.


def test_quality_gate_detects_invoice_grain_collision():
    import duckdb
    from contracts import quality_checks
    purchases = pd.DataFrame({'InvoiceNo':['1','1'], 'InvoiceDate':pd.to_datetime(['2011-01-01','2011-01-02']),
                              'Quantity':[1,1], 'UnitPrice':[10.,20.]})
    con = duckdb.connect()
    con.register('purchases', purchases)
    con.execute("CREATE TABLE orders AS SELECT '1' order_id, 10. revenue UNION ALL SELECT '1',20.")
    con.execute('CREATE TABLE monthly AS SELECT 30. gross_sales')
    con.execute('CREATE TABLE cohorts AS SELECT 0.5 retention')
    con.execute('CREATE TABLE repeat_90 AS SELECT 1 customer_id')
    checks = {r['check']:r['status'] for r in quality_checks(con, purchases)}
    assert checks['unique_invoice_grain'] == 'FAIL'
    assert checks['invoice_calendar_day_consistency'] == 'FAIL'
    assert checks['line_to_order_sales'] == 'PASS'
