"""Olist Customer Analytics Dashboard — Streamlit entry point."""
import streamlit as st
from src.database import run_query, load_filter_options
from dashboard.kpi_cards import build_filters, get_crr, get_rpr, get_churn, get_ltv, get_csat, get_nps
from dashboard.charts import (
    top_states_chart, revenue_trend_chart, customer_acquisition_chart,
    best_month_chart, top_categories_chart, review_scores_chart,
)

st.set_page_config(page_title="Olist Customer Analytics", layout="wide")

# ---- Load filter options ----
all_years, all_states, all_categories = load_filter_options()

# ---- Sidebar ----
st.sidebar.title("Filters")
yr = st.sidebar.slider("Year Range", min(all_years), max(all_years),
                        (min(all_years), max(all_years)))
sel_states = st.sidebar.multiselect("States", all_states, default=all_states)
sel_cats = st.sidebar.multiselect("Product Categories", all_categories,
                                  default=all_categories[:10])
st.sidebar.markdown("---")
st.sidebar.caption("Data from Olist E-Commerce Dataset")

y1, y2 = yr
clause, params = build_filters(sel_states, y1, y2)

# ---- Title ----
st.title("Olist Customer Analytics Dashboard")
st.markdown("---")

# ---- KPI Row ----
crr = get_crr(clause, params)
rpr = get_rpr(clause, params)
churn = get_churn(clause, params)
ltv = get_ltv(clause, params)
csat = get_csat(clause, params)
nps = get_nps(clause, params)

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("CRR", f"{crr:.1f}%" if crr is not None else "N/A")
k2.metric("RPR", f"{rpr:.1f}%" if rpr is not None else "N/A")
k3.metric("Churn", f"{churn:.1f}%" if churn is not None else "N/A")
k4.metric("Avg LTV", f"${ltv:.2f}" if ltv is not None else "N/A")
k5.metric("CSAT", f"{csat:.1f}%" if csat is not None else "N/A")
k6.metric("NPS", f"{nps:.1f}" if nps is not None else "N/A")
st.markdown("---")

# ---- Charts Row 1 ----
c1, c2 = st.columns(2)
with c1:
    st.subheader("Top 10 States by Revenue")
    fig = top_states_chart(clause, params)
    if fig:
        st.plotly_chart(fig)
with c2:
    st.subheader("Revenue Over Years")
    fig = revenue_trend_chart(clause, params, sel_cats)
    if fig:
        st.plotly_chart(fig)

# ---- Charts Row 2 ----
c3, c4 = st.columns(2)
with c3:
    st.subheader("Customers Acquired per Month")
    fig = customer_acquisition_chart(clause, params)
    if fig:
        st.plotly_chart(fig)
with c4:
    st.subheader("Best Month Each Year")
    fig = best_month_chart(clause, params)
    if fig:
        st.plotly_chart(fig)

# ---- Charts Row 3 ----
c5, c6 = st.columns(2)
with c5:
    st.subheader("Top Categories by Revenue")
    fig = top_categories_chart(clause, params, sel_cats)
    if fig:
        st.plotly_chart(fig)
with c6:
    st.subheader("Review Score Distribution")
    fig = review_scores_chart(clause, params)
    if fig:
        st.plotly_chart(fig)

# ---- Data Tables ----
st.markdown("---")
st.subheader("Raw Data Tables")

with st.expander("CRR by Year"):
    df = run_query("""
        WITH active AS (
            SELECT DISTINCT c.customer_unique_id,
                   EXTRACT(YEAR FROM (o.order_purchase_timestamp)::timestamp)::int AS year
            FROM orders o JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_purchase_timestamp IS NOT NULL AND o.order_purchase_timestamp != ''
              AND o.order_status NOT IN ('canceled','unavailable')
        )
        SELECT a.year, COUNT(DISTINCT a.customer_unique_id) AS active,
               COUNT(DISTINCT b.customer_unique_id) AS retained,
               ROUND((COUNT(DISTINCT b.customer_unique_id)::numeric
                      / NULLIF(COUNT(DISTINCT a.customer_unique_id),0)) * 100, 2) AS crr
        FROM active a
        LEFT JOIN active b ON a.customer_unique_id = b.customer_unique_id AND b.year = a.year + 1
        GROUP BY a.year ORDER BY a.year
    """)
    st.dataframe(df, width='stretch')

with st.expander("Monthly Revenue"):
    df = run_query("""
        SELECT DATE_TRUNC('month', (o.order_purchase_timestamp)::timestamp)::date AS month,
               COUNT(DISTINCT o.order_id) AS orders,
               ROUND(SUM(oi.price)::numeric, 2) AS revenue,
               ROUND(AVG(oi.price)::numeric, 2) AS avg_order_value
        FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.order_purchase_timestamp IS NOT NULL AND o.order_purchase_timestamp != ''
          AND o.order_status NOT IN ('canceled','unavailable')
        GROUP BY month ORDER BY month
    """)
    st.dataframe(df, width='stretch')

with st.expander("Payment Type Distribution"):
    df = run_query("""
        SELECT payment_type, COUNT(*) AS transactions,
               ROUND(SUM(payment_value)::numeric, 2) AS total_value,
               ROUND(AVG(payment_value)::numeric, 2) AS avg_value
        FROM order_payments GROUP BY payment_type ORDER BY total_value DESC
    """)
    st.dataframe(df, width='stretch')

with st.expander("Delivery Performance by Year"):
    df = run_query("""
        SELECT EXTRACT(YEAR FROM (order_purchase_timestamp)::timestamp)::int AS year,
               ROUND(AVG(EXTRACT(EPOCH FROM (
                   (order_delivered_customer_date)::timestamp - (order_purchase_timestamp)::timestamp
               )) / 86400), 1) AS avg_delivery_days
        FROM orders
        WHERE order_purchase_timestamp IS NOT NULL AND order_purchase_timestamp != ''
          AND order_delivered_customer_date IS NOT NULL AND order_delivered_customer_date != ''
          AND order_status = 'delivered'
        GROUP BY year ORDER BY year
    """)
    st.dataframe(df, width='stretch')

with st.expander("Top 3 States × Top 3 Categories"):
    df = run_query("""
        WITH scr AS (
            SELECT c.customer_state,
                   COALESCE(pct.product_category_name_english, p.product_category_name) AS category,
                   ROUND(SUM(oi.price)::numeric, 2) AS revenue,
                   ROW_NUMBER() OVER (PARTITION BY c.customer_state ORDER BY SUM(oi.price) DESC) AS rn
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN products p ON oi.product_id = p.product_id
            LEFT JOIN product_category_translation pct ON p.product_category_name = pct.product_category_name
            GROUP BY c.customer_state, category
        ),
        ts AS (
            SELECT customer_state FROM scr WHERE rn = 1 ORDER BY revenue DESC LIMIT 3
        )
        SELECT ts.customer_state, scr.category, scr.revenue, scr.rn AS rank
        FROM ts JOIN scr ON ts.customer_state = scr.customer_state
        WHERE scr.rn <= 3 ORDER BY ts.customer_state, scr.rn
    """)
    st.dataframe(df, width='stretch')
