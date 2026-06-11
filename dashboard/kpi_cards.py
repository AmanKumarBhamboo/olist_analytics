"""KPI metric computations for the Olist dashboard."""
from src.database import run_query


def build_filters(sel_states, y1, y2, prefix_o="o", prefix_c="c"):
    """Build a WHERE clause fragment and params dict from sidebar filter state."""
    clauses = []
    params = {}
    if sel_states:
        clauses.append(f"{prefix_c}.customer_state IN :states")
        params["states"] = tuple(sel_states)
    clauses.append(
        f"EXTRACT(YEAR FROM ({prefix_o}.order_purchase_timestamp)::timestamp)::int "
        f"BETWEEN :y1 AND :y2"
    )
    params["y1"] = y1
    params["y2"] = y2
    return " AND ".join(clauses), params


def get_crr(clause, params):
    df = run_query(f"""
        WITH active AS (
            SELECT DISTINCT c.customer_unique_id,
                   EXTRACT(YEAR FROM (o.order_purchase_timestamp)::timestamp)::int AS year
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_purchase_timestamp IS NOT NULL AND o.order_purchase_timestamp != ''
              AND o.order_status NOT IN ('canceled','unavailable')
              AND {clause}
        )
        SELECT ROUND((COUNT(DISTINCT b.customer_unique_id)::numeric
               / NULLIF(COUNT(DISTINCT a.customer_unique_id),0)) * 100, 2) AS val
        FROM active a
        LEFT JOIN active b ON a.customer_unique_id = b.customer_unique_id AND b.year = a.year + 1
        WHERE a.year BETWEEN :y1 AND :y2
    """, params)
    return df["val"].iloc[0] if not df.empty and df["val"].notna().any() else None


def get_rpr(clause, params):
    df = run_query(f"""
        WITH cte AS (
            SELECT c.customer_unique_id, COUNT(DISTINCT o.order_id) AS cnt
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            WHERE {clause}
            GROUP BY c.customer_unique_id
        )
        SELECT ROUND((COUNT(*) FILTER (WHERE cnt > 1)::numeric / COUNT(*)) * 100, 2) AS val
        FROM cte
    """, params)
    return df["val"].iloc[0] if not df.empty and df["val"].notna().any() else None


def get_churn(clause, params):
    df = run_query(f"""
        WITH cte AS (
            SELECT c.customer_unique_id,
                   MIN(EXTRACT(YEAR FROM (o.order_purchase_timestamp)::timestamp)::int) AS first_yr,
                   MAX(EXTRACT(YEAR FROM (o.order_purchase_timestamp)::timestamp)::int) AS last_yr
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_purchase_timestamp IS NOT NULL AND o.order_purchase_timestamp != ''
              AND o.order_status NOT IN ('canceled','unavailable')
              AND {clause}
            GROUP BY c.customer_unique_id
        ),
        mx AS (SELECT MAX(last_yr) AS yr FROM cte)
        SELECT ROUND((COUNT(*) FILTER (WHERE last_yr < (SELECT yr FROM mx))::numeric
               / NULLIF(COUNT(*),0)) * 100, 2) AS val
        FROM cte
    """, params)
    return df["val"].iloc[0] if not df.empty and df["val"].notna().any() else None


def get_ltv(clause, params):
    df = run_query(f"""
        SELECT ROUND(AVG(total)::numeric, 2) AS val
        FROM (
            SELECT c.customer_unique_id, SUM(oi.price) AS total
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.order_purchase_timestamp IS NOT NULL AND o.order_purchase_timestamp != ''
              AND o.order_status NOT IN ('canceled','unavailable')
              AND {clause}
            GROUP BY c.customer_unique_id
        ) sub
    """, params)
    return df["val"].iloc[0] if not df.empty and df["val"].notna().any() else None


def get_csat(clause, params):
    df = run_query(f"""
        SELECT ROUND((COUNT(*) FILTER (WHERE r.review_score >= 4)::numeric / COUNT(*)) * 100, 2) AS val
        FROM order_reviews r
        JOIN orders o ON r.order_id = o.order_id
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE {clause}
    """, params)
    return df["val"].iloc[0] if not df.empty and df["val"].notna().any() else None


def get_nps(clause, params):
    df = run_query(f"""
        WITH sg AS (
            SELECT COUNT(*) FILTER (WHERE r.review_score = 5) AS promoters,
                   COUNT(*) FILTER (WHERE r.review_score BETWEEN 1 AND 3) AS detractors,
                   COUNT(*) AS total
            FROM order_reviews r
            JOIN orders o ON r.order_id = o.order_id
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE {clause}
        )
        SELECT ROUND(((promoters::numeric - detractors::numeric) / NULLIF(total,0)) * 100, 2) AS val
        FROM sg
    """, params)
    return df["val"].iloc[0] if not df.empty and df["val"].notna().any() else None
