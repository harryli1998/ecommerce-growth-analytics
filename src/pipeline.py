"""Download original public data and build reproducible analytics artifacts."""
from pathlib import Path
import hashlib
import io
import json
import zipfile
import duckdb
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://archive.ics.uci.edu/static/public/352/online+retail.zip'

def clean(raw):
    df = raw.drop_duplicates().copy()
    df['InvoiceNo'] = df.InvoiceNo.astype(str)
    df['CustomerID'] = df.CustomerID.astype('Int64').astype('string')
    df['InvoiceDate'] = pd.to_datetime(df.InvoiceDate)
    purchases = df.loc[(df.Quantity > 0) & (df.UnitPrice > 0) &
                       ~df.InvoiceNo.str.upper().str.startswith('C')].copy()
    return df, purchases

def run():
    raw_dir, out = ROOT/'data/raw', ROOT/'outputs'
    raw_dir.mkdir(parents=True, exist_ok=True)
    out.mkdir(exist_ok=True)
    archive = raw_dir/'online-retail.zip'
    if not archive.exists():
        response = requests.get(URL, timeout=180)
        response.raise_for_status()
        archive.write_bytes(response.content)
    with zipfile.ZipFile(archive) as z:
        name = next(n for n in z.namelist() if n.endswith('.xlsx'))
        raw = pd.read_excel(io.BytesIO(z.read(name)), engine='openpyxl')
    df, purchases = clean(raw)
    con = duckdb.connect(str(out/'analytics.duckdb'))
    con.register('purchases', purchases)
    con.execute((ROOT/'sql/metrics.sql').read_text())
    for table in ['monthly','cohorts','customers','segments','repeat_90']:
        con.sql(f'SELECT * FROM {table}').df().to_csv(out/f'{table}.csv', index=False)
    metrics = con.sql('SELECT count(*) orders, sum(revenue) gross_sales, sum(revenue)/count(*) aov FROM orders').df().iloc[0].to_dict()
    repeat = con.sql('SELECT count(*) eligible_customers, avg(repeated) repeat_90_rate FROM repeat_90').df().iloc[0].to_dict()
    audit = {'raw_rows':len(raw),'exact_duplicates_removed':len(raw)-len(df),
             'purchase_rows':len(purchases),'excluded_nonpurchase_rows':len(df)-len(purchases),
             'missing_customer_purchase_rows':int(purchases.CustomerID.isna().sum()),
             'negative_quantity_value':float(-(df.loc[df.Quantity<0,'Quantity']*df.loc[df.Quantity<0,'UnitPrice']).sum()),
             'source_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
             'data_start':str(df.InvoiceDate.min()),'data_end':str(df.InvoiceDate.max()),
             **metrics,**repeat}
    (out/'summary.json').write_text(json.dumps(audit,indent=2))
    # Reconciliation prevents lost orders or duplicated sales in aggregation.
    assert abs(metrics['gross_sales'] - (purchases.Quantity*purchases.UnitPrice).sum()) < .01
    assert con.sql('SELECT count(*) FROM orders').fetchall()[0][0] == purchases.InvoiceNo.nunique()
    assert con.sql('SELECT count(*) FROM cohorts WHERE retention < 0 OR retention > 1').fetchall()[0][0] == 0
    from advanced import run_advanced
    run_advanced(df, purchases, con)
    con.close()
    from report import write_report
    write_report()
    print(json.dumps(audit,indent=2))

if __name__ == '__main__':
    run()
