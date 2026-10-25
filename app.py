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
