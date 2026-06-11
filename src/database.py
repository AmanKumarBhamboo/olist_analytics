"""Database engine and query execution layer."""
from sqlalchemy import create_engine, text
import pandas as pd
from src.config import DB_URL

_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(DB_URL)
    return _engine

def run_query(sql, params=None):
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)

def load_filter_options():
    """Load distinct years, states, and categories for sidebar filters."""
    years = run_query("""
        SELECT DISTINCT EXTRACT(YEAR FROM (order_purchase_timestamp)::timestamp)::int AS year
        FROM orders WHERE order_purchase_timestamp IS NOT NULL AND order_purchase_timestamp != ''
        ORDER BY year
    """)
    states = run_query("SELECT DISTINCT customer_state FROM customers ORDER BY customer_state")
    cats = run_query("""
        SELECT DISTINCT COALESCE(pct.product_category_name_english, p.product_category_name) AS category
        FROM products p
        LEFT JOIN product_category_translation pct ON p.product_category_name = pct.product_category_name
        WHERE p.product_category_name IS NOT NULL ORDER BY category
    """)
    return (
        sorted(years["year"].tolist()),
        states["customer_state"].tolist(),
        cats["category"].tolist(),
    )
