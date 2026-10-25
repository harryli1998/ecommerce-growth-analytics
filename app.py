from pathlib import Path
import json
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title='Commerce | Growth Analytics',page_icon='📈',layout='wide')
st.title('Commerce / Growth & Retention')
st.caption('Independent portfolio study • UCI Online Retail • GBP • Historical transactions, 2010–2011')
if not (ROOT/'outputs/summary.json').exists():
    st.info('Run python src/pipeline.py to build the analysis first.')
    st.stop()
s = json.loads((ROOT/'outputs/summary.json').read_text())
monthly = pd.read_csv(ROOT/'outputs/monthly.csv',parse_dates=['month'])
cohorts = pd.read_csv(ROOT/'outputs/cohorts.csv')
segments = pd.read_csv(ROOT/'outputs/segments.csv')
a,b,c,d = st.columns(4)
a.metric('Gross purchase sales',f"£{s['gross_sales']/1_000_000:.2f}M",help=f"£{s['gross_sales']:,.2f}")
b.metric('Purchase orders',f"{s['orders']:,.0f}")
c.metric('Average order value',f"£{s['aov']:,.2f}")
d.metric('90-day repeat rate',f"{s['repeat_90_rate']:.1%}")
st.caption(f"Repeat denominator: {s['eligible_customers']:,.0f} identified customers with a full 90-day window. Sales exclude cancellations and nonpositive quantity/price; these are not net revenue.")
trend,retention,action,quality = st.tabs(['Sales trends','Customer retention','Marketing actions','Data & limitations'])
with trend:
    st.subheader('Monthly sales')
    include = st.checkbox('Include partial December 2011',value=False)
    view = monthly if include else monthly[monthly.month < pd.Timestamp('2011-12-01')]
    metric = st.selectbox('Metric',['gross_sales','orders','aov','identified_customers'],format_func=lambda x: {'gross_sales':'Gross purchase sales (GBP)','orders':'Purchase orders','aov':'Average order value (GBP)','identified_customers':'Identified customers'}[x])
    st.plotly_chart(px.line(view,x='month',y=metric,markers=True),use_container_width=True)
    st.caption('Seasonality and a single historical year limit trend extrapolation. Customer counts exclude missing IDs.')
    st.dataframe(view,hide_index=True)
with retention:
    st.subheader('Observed monthly purchase retention')
    matrix = cohorts.pivot(index='cohort',columns='month_index',values='retention')
    st.plotly_chart(px.imshow(matrix, zmin=0,zmax=1,color_continuous_scale='Teal',labels={'x':'Months since first observed purchase','y':'Cohort','color':'Retention'}),use_container_width=True)
    st.caption('December 2011 is excluded because it is incomplete. Blank cells are future, unobserved months; zero means an observed month with no returning customers. Cohort 0 = 100%.')
    st.dataframe(cohorts,hide_index=True)
with action:
    counts = segments.groupby('segment',as_index=False).agg(customers=('customer_id','count'),gross_sales=('monetary','sum'))
    st.plotly_chart(px.bar(counts,x='segment',y='customers',color='segment'),use_container_width=True)
    st.dataframe(counts,hide_index=True)
    st.markdown('**Proposed experiments, not demonstrated uplift**\n\n- Lapsed repeat: randomized win-back offer with a no-message holdout.\n- One-time observed: test a second-purchase reminder, with eligibility based on consent and recency.\n- Active repeat: test relevant product recommendations against business-as-usual.\n\nMeasure incremental repeat rate and contribution profit over 90 days. Predefine sample size, exclusions and guardrails before launch.')
with quality:
    st.json(s)
    st.warning('No sessions, funnel events, ad spend, channel attribution or margin data. Visitor conversion, CAC, ROAS and profit cannot be calculated from this dataset.')
    st.markdown('[Source and CC BY 4.0 attribution](https://archive.ics.uci.edu/dataset/352/online+retail) · Daqing Chen (2015), DOI: 10.24432/C5BW33. Cleaning and aggregation are modifications.')

st.divider()
st.header('Decision lab')
if not (ROOT/'outputs/model_evaluation.csv').exists():
    st.info('Rerun the pipeline to build advanced analytics.')
else:
    finance,basket,model,planner=st.tabs(['Sales reconciliation','Cross-sell discovery','Repurchase backtest','Campaign economics'])
    with finance:
        bridge=pd.read_csv(ROOT/'outputs/revenue_bridge.csv')
        st.plotly_chart(px.bar(bridge,x='month',y=['gross_purchase_sales','negative_quantity_value','signed_ledger_value'],barmode='group',labels={'value':'GBP'}),use_container_width=True)
        st.dataframe(bridge,hide_index=True)
        st.caption('Gross purchase sales − negative-quantity value + exception value = signed ledger value. Negative lines are recorded by invoice date and are not matched to original orders. This is not recognized net revenue or profit.')
    with basket:
        rules=pd.read_csv(ROOT/'outputs/basket_rules.csv')
        min_conf=st.slider('Minimum conditional co-purchase rate',0.0,1.0,.2,.05)
        rules=rules[rules.confidence>=min_conf]
        st.dataframe(rules,hide_index=True)
        st.caption('Directional association A → B, not causation. Confidence = P(B | A); lift = P(B | A) / P(B). Only top 100 product-like SKUs, baskets with 2–50 distinct SKUs and at least 30 joint baskets. The exported table contains at most 100 rules ranked by lift. Product variants and wholesale behavior can inflate associations; validate bundles experimentally.')
    with model:
        scores=pd.read_csv(ROOT/'outputs/model_evaluation.csv')
        st.subheader('Will an existing customer purchase in the next 60 days?')
        st.dataframe(scores,hide_index=True)
        comparison=px.bar(scores,x='cutoff',y='lift_top20',color='model',barmode='group',labels={'lift_top20':'Top 20% purchase-propensity lift','cutoff':'Evaluation snapshot'})
        comparison.update_xaxes(type='category')
        comparison.update_layout(legend={'orientation':'h','y':1.15,'x':0},legend_title_text='')
        comparison.add_hline(y=1,line_dash='dot',annotation_text='Random ranking')
        st.plotly_chart(comparison,use_container_width=True)
        cal=pd.read_csv(ROOT/'outputs/calibration.csv')
        st.plotly_chart(px.scatter(cal,x='predicted',y='observed',size='customers',color='cutoff',hover_data=['probability_band'],range_x=[0,1],range_y=[0,1]),use_container_width=True)
        st.caption('Train: April 1 snapshot. Evaluate: July 1 and October 1 snapshots; each uses an exclusive 60-day future window. Features use only earlier purchases; scaler fits on training data. Coefficients are descriptive conditional associations. These same customers may occur across dates: this tests recurring-customer scoring, not unseen-customer performance. No hyperparameter tuning or marketing experiment. Top-20% lift measures purchase propensity, not incremental persuasion.')
        st.dataframe(pd.read_csv(ROOT/'outputs/model_coefficients.csv'),hide_index=True)
    with planner:
        st.subheader('What incremental response would make a campaign worthwhile?')
        contacts=st.number_input('Eligible contacts',min_value=0,value=1000,step=100)
        cost=st.number_input('Cost per contact (GBP)',min_value=0.0,value=.20,step=.05)
        profit=st.number_input('Contribution per incremental order after discount (GBP)',min_value=.01,value=20.0,step=1.0)
        uplift=st.slider('Assumed incremental order-rate uplift (percentage points)',0.0,10.0,1.0,.1)/100
        scenario=contacts*(uplift*profit-cost)
        st.write(f'**Scenario contribution after contact cost: £{scenario:,.2f}**')
        st.write(f'Break-even uplift: **{cost/profit:.2%}**; expected incremental orders: **{contacts*uplift:,.1f}**.')
        st.warning('Scenario inputs are assumptions, not estimated campaign effects. Contact counts require actual consent and eligibility. At most one incremental order per contact is modeled; fixed costs, timing and uncertainty are omitted. Purchase propensity scores cannot substitute for experimental uplift.')
