"""Chart query and rendering helpers for the Olist dashboard."""
import plotly.express as px
from datetime import datetime
from src.database import run_query


def top_states_chart(clause, params):
    df = run_query(f"""
        SELECT c.customer_state,
               COUNT(DISTINCT o.order_id) AS orders,
               ROUND(SUM(oi.price)::numeric, 2) AS revenue
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.order_purchase_timestamp IS NOT NULL AND o.order_purchase_timestamp != ''
          AND o.order_status NOT IN ('canceled','unavailable')
          AND {clause}
        GROUP BY c.customer_state
        ORDER BY revenue DESC LIMIT 10
    """, params)
    if df.empty:
        return None
    return px.bar(df, x="customer_state", y="revenue", color="orders",
                  labels={"customer_state": "", "revenue": "Revenue (BRL)"})


def revenue_trend_chart(clause, params, sel_cats):
    cat_filter = ""
    cat_params = {}
    if sel_cats:
        cat_filter = "AND cat.category IN :cats"
        cat_params["cats"] = tuple(sel_cats)
    df = run_query(f"""
        WITH cat AS (
            SELECT oi.order_id, oi.price,
                   COALESCE(pct.product_category_name_english, p.product_category_name) AS category
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            LEFT JOIN product_category_translation pct ON p.product_category_name = pct.product_category_name
            WHERE p.product_category_name IS NOT NULL
        )
        SELECT EXTRACT(YEAR FROM (o.order_purchase_timestamp)::timestamp)::int AS year,
               ROUND(SUM(cat.price)::numeric, 2) AS revenue
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN cat ON o.order_id = cat.order_id
        WHERE o.order_purchase_timestamp IS NOT NULL AND o.order_purchase_timestamp != ''
          AND o.order_status NOT IN ('canceled','unavailable')
          AND {clause} {cat_filter}
        GROUP BY year ORDER BY year
    """, {**params, **cat_params})
    if df.empty:
        return None
    fig = px.line(df, x="year", y="revenue", markers=True,
                  labels={"year": "Year", "revenue": "Revenue (BRL)"})
    fig.update_traces(line_shape="linear")
    return fig


def customer_acquisition_chart(clause, params):
    df = run_query(f"""
        WITH fp AS (
            SELECT c.customer_unique_id,
                   MIN((o.order_purchase_timestamp)::timestamp) AS first_order
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            WHERE {clause}
            GROUP BY c.customer_unique_id
        )
        SELECT DATE_TRUNC('month', first_order)::date AS month,
               COUNT(*) AS new_customers
        FROM fp GROUP BY month ORDER BY month
    """, params)
    if df.empty:
        return None
    return px.bar(df, x="month", y="new_customers",
                  labels={"month": "", "new_customers": "New Customers"})


def best_month_chart(clause, params):
    df = run_query(f"""
        WITH mr AS (
            SELECT EXTRACT(YEAR FROM (o.order_purchase_timestamp)::timestamp)::int AS year,
                   EXTRACT(MONTH FROM (o.order_purchase_timestamp)::timestamp)::int AS month,
                   ROUND(SUM(oi.price)::numeric, 2) AS revenue
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.order_purchase_timestamp IS NOT NULL AND o.order_purchase_timestamp != ''
              AND o.order_status NOT IN ('canceled','unavailable')
              AND {clause}
            GROUP BY year, month
        ),
        rk AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY year ORDER BY revenue DESC) AS rn FROM mr)
        SELECT year, month, revenue FROM rk WHERE rn = 1 ORDER BY year
    """, params)
    if df.empty:
        return None
    df["label"] = df["year"].astype(str) + " " + df["month"].apply(
        lambda m: datetime(2000, int(m), 1).strftime("%b")
    )
    return px.bar(df, x="label", y="revenue", text="revenue",
                  labels={"label": "", "revenue": "Revenue (BRL)"})


def top_categories_chart(clause, params, sel_cats):
    cat_where = ""
    cat_params = {}
    if sel_cats:
        cat_where = "AND cat.category IN :cats"
        cat_params["cats"] = tuple(sel_cats)
    df = run_query(f"""
        SELECT cat.category,
               ROUND(SUM(cat.price)::numeric, 2) AS revenue,
               COUNT(DISTINCT o.order_id) AS orders
        FROM orders o
        JOIN (
            SELECT oi.order_id, oi.price,
                   COALESCE(pct.product_category_name_english, p.product_category_name) AS category
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            LEFT JOIN product_category_translation pct ON p.product_category_name = pct.product_category_name
            WHERE p.product_category_name IS NOT NULL
        ) cat ON o.order_id = cat.order_id
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.order_purchase_timestamp IS NOT NULL AND o.order_purchase_timestamp != ''
          AND o.order_status NOT IN ('canceled','unavailable')
          AND {clause} {cat_where}
        GROUP BY cat.category
        ORDER BY revenue DESC LIMIT 10
    """, {**params, **cat_params})
    if df.empty:
        return None
    return px.bar(df, x="revenue", y="category", color="orders",
                  labels={"revenue": "Revenue (BRL)", "category": ""}, orientation="h")


def review_scores_chart(clause, params):
    df = run_query(f"""
        SELECT r.review_score, COUNT(*) AS cnt
        FROM order_reviews r
        JOIN orders o ON r.order_id = o.order_id
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE {clause}
        GROUP BY r.review_score ORDER BY r.review_score
    """, params)
    if df.empty:
        return None
    return px.bar(df, x="review_score", y="cnt", text="cnt",
                  labels={"review_score": "Score", "cnt": "Count"})
