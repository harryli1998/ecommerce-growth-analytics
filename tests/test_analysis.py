import importlib.util
from pathlib import Path
import duckdb
import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pipeline',ROOT/'src/pipeline.py')
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)

def test_clean_and_cohort_censoring():
    raw = pd.DataFrame([
        ['1','A',1,10,'2011-01-01',1,'UK'],
        ['1','A',1,10,'2011-01-01',1,'UK'],
        ['2','A',1,20,'2011-03-01',1,'UK'],
        ['3','A',1,30,'2011-05-15',2,'UK'],
        ['C4','A',-1,10,'2011-05-15',1,'UK'],
        ['5','A',1,0,'2011-05-15',2,'UK'],
    ],columns=['InvoiceNo','StockCode','Quantity','UnitPrice','InvoiceDate','CustomerID','Country'])
    clean,purchases = pipeline.clean(raw)
    assert len(clean)==5 and len(purchases)==3
    con=duckdb.connect()
    con.register('purchases',purchases)
    con.execute((ROOT/'sql/metrics.sql').read_text())
    assert con.sql('SELECT sum(revenue) FROM orders').fetchall()[0][0]==60
    assert con.sql('SELECT count(*),sum(repeated) FROM repeat_90').fetchall()[0]==(1,1)
    assert con.sql("SELECT retention FROM cohorts WHERE month_index=1").fetchall()[0][0]==0
    assert con.sql('SELECT max(month_index) FROM cohorts').fetchall()[0][0]==3

def test_dashboard():
    app=AppTest.from_file(str(ROOT/'app.py')).run(timeout=30)
    assert not app.exception
    assert len(app.metric)==4
    app.checkbox[0].check().run()
    app.selectbox[0].select('aov').run()
    assert not app.exception
    app.slider[0].set_value(.5).run()
    app.number_input[0].set_value(0).run()
    assert not app.exception

def test_snapshot_does_not_leak_future():
    import sys
    sys.path.insert(0,str(ROOT/'src'))
    from advanced import snapshot
    orders=pd.DataFrame({'customer_id':['a','a','a','b'],'order_id':['1','2','3','4'],
                         'ordered_at':pd.to_datetime(['2011-03-01','2011-04-01','2011-05-31','2011-04-10']),
                         'revenue':[10.,999.,100.,20.]})
    frame=snapshot(orders,'2011-04-01').set_index('customer_id')
    assert list(frame.index)==['a']
    assert frame.loc['a','sales_90']==10
    assert frame.loc['a','orders_90']==1
    assert frame.loc['a','returned']==1
    # Exact exclusive horizon endpoint must not count.
    assert snapshot(orders[orders.order_id!='2'],'2011-04-01').returned.iloc[0]==0

def test_signed_bridge_reconciles():
    con=duckdb.connect()
    ledger=pd.DataFrame({'InvoiceNo':['1','C2','C3','4'],'Quantity':[2,-1,1,2],
                        'UnitPrice':[10.,10.,5.,-3.],
                        'InvoiceDate':pd.to_datetime(['2011-01-01']*4)})
    con.register('ledger',ledger)
    con.execute((ROOT/'sql/advanced.sql').read_text())
    row=con.sql('SELECT * FROM revenue_bridge').df().iloc[0]
    assert row.signed_ledger_value==9
    assert row.gross_purchase_sales-row.negative_quantity_value+row.exception_value==row.signed_ledger_value
