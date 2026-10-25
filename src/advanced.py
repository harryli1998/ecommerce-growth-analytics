"""Decision-oriented extensions: ledger bridge, basket rules and temporal scoring."""
from pathlib import Path
import json
import math
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ['recency','orders_90','sales_90','tenure']

def snapshot(orders, cutoff):
    """Features strictly precede cutoff; labels use [cutoff, cutoff + 60 days)."""
    cutoff = pd.Timestamp(cutoff)
    past = orders[orders.ordered_at < cutoff]
    recent = past[past.ordered_at >= cutoff-pd.Timedelta(days=90)]
    base = past.groupby('customer_id').agg(first=('ordered_at','min'),last=('ordered_at','max'))
    base['recency'] = (cutoff-base['last']).dt.total_seconds()/86400
    base['tenure'] = (cutoff-base['first']).dt.total_seconds()/86400
    r = recent.groupby('customer_id').agg(orders_90=('order_id','nunique'),sales_90=('revenue','sum'))
    base = base.join(r).fillna({'orders_90':0,'sales_90':0})
    future = orders[(orders.ordered_at >= cutoff)&(orders.ordered_at < cutoff+pd.Timedelta(days=60))]
    base['returned'] = base.index.isin(future.customer_id).astype(int)
    return base.reset_index()

def evaluation(y, score, name, cutoff):
    n = max(1, math.ceil(len(y)*.2))
    selected = np.argsort(-np.asarray(score),kind='stable')[:n]
    prevalence = float(np.mean(y))
    precision = float(np.asarray(y)[selected].mean())
    return {'cutoff':cutoff,'model':name,'customers':len(y),'base_rate':prevalence,
            'roc_auc':float(roc_auc_score(y,score)),
            'average_precision':float(average_precision_score(y,score)),
            'precision_top20':precision,'lift_top20':precision/prevalence,
            'selected_customers':n}

def run_advanced(df, purchases, con):
    out = ROOT/'outputs'
    con.register('ledger',df)
    con.execute((ROOT/'sql/advanced.sql').read_text())
    bridge=con.sql('SELECT * FROM revenue_bridge ORDER BY month').df()
    assert np.allclose(bridge.gross_purchase_sales-bridge.negative_quantity_value+bridge.exception_value,bridge.signed_ledger_value,atol=.001,rtol=0)
    bridge.to_csv(out/'revenue_bridge.csv',index=False)
    # Basket mining has explicit SKU and basket-size bounds to avoid service codes
    # and extreme wholesale baskets dominating cross-sell suggestions.
    items = purchases[purchases.StockCode.astype(str).str.fullmatch(r'[0-9]{5}[A-Za-z]?')].copy()
    sizes = items.groupby('InvoiceNo').StockCode.nunique()
    items = items[items.InvoiceNo.isin(sizes[(sizes>=2)&(sizes<=50)].index)]
    counts = items.groupby('StockCode').InvoiceNo.nunique().sort_values(ascending=False)
    top = counts.head(100).index
    binary = (pd.crosstab(items.InvoiceNo,items.StockCode).reindex(columns=top,fill_value=0)>0).astype('int64')
    total = len(binary)
    together = binary.T.dot(binary)
    names = items.groupby('StockCode').Description.last().to_dict()
    rules=[]
    for a in top:
        for b in top:
            joint=int(together.loc[a,b])
            if a==b or joint<30:
                continue
            confidence=joint/int(together.loc[a,a])
            lift=confidence/(int(together.loc[b,b])/total)
            if lift>1:
                rules.append({'antecedent':str(a),'consequent':str(b),'antecedent_name':names[a],
                              'consequent_name':names[b],'joint_baskets':joint,'support':joint/total,
                              'confidence':confidence,'lift':lift,'eligible_baskets':total})
    pd.DataFrame(rules).sort_values(['lift','joint_baskets'],ascending=False).head(100).to_csv(out/'basket_rules.csv',index=False)
    orders = con.sql('SELECT * FROM orders WHERE customer_id IS NOT NULL ORDER BY customer_id,ordered_at,order_id').df()
    orders['ordered_at'] = pd.to_datetime(orders.ordered_at)
    train = snapshot(orders,'2011-04-01')
    model = make_pipeline(StandardScaler(),LogisticRegression(C=1,max_iter=1000,random_state=42))
    model.fit(np.log1p(train[FEATURES]),train.returned)
    metrics=[]
    predictions=[]
    calibration=[]
    for cutoff in ['2011-07-01','2011-10-01']:
        test = snapshot(orders,cutoff)
        p = model.predict_proba(np.log1p(test[FEATURES]))[:,1]
        metrics.append(evaluation(test.returned,p,'Logistic regression',cutoff))
        metrics.append(evaluation(test.returned,-test.recency.to_numpy(),'Recency ranking baseline',cutoff))
        metrics[-2]['brier_score']=float(brier_score_loss(test.returned,p))
        # The same historical customers may recur; this measures existing-customer
        # scoring over time, not generalization to entirely unseen identities.
        test['probability']=p
        test['cutoff']=cutoff
        predictions.append(test[['customer_id','cutoff',*FEATURES,'returned','probability']])
        test['probability_band']=pd.cut(p,bins=[0,.2,.4,.6,.8,1],include_lowest=True).astype(str)
        cal=test.groupby('probability_band').agg(customers=('returned','size'),predicted=('probability','mean'),observed=('returned','mean')).reset_index()
        cal['cutoff']=cutoff
        calibration.append(cal)
    pd.DataFrame(metrics).to_csv(out/'model_evaluation.csv',index=False)
    pd.concat(predictions).to_csv(out/'backtest_predictions.csv',index=False)
    pd.concat(calibration).to_csv(out/'calibration.csv',index=False)
    pd.DataFrame({'feature':FEATURES,'standardized_log_coefficient':model[-1].coef_[0]}).to_csv(out/'model_coefficients.csv',index=False)
    (out/'advanced_metadata.json').write_text(json.dumps({'training_cutoff':'2011-04-01','training_label_end_exclusive':'2011-05-31',
      'test_cutoffs':['2011-07-01','2011-10-01'],'horizon_days':60,'basket_top_skus':100,
      'basket_size_range':[2,50],'basket_min_joint':30,'eligible_baskets':total},indent=2))
