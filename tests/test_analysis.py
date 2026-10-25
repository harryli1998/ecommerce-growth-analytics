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
