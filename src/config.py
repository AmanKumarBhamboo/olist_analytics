"""Project-wide configuration loaded from environment variables or Streamlit secrets."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass


def get_db_url():
    """Return the database URL, checking Streamlit secrets first, then env vars."""
    try:
        import streamlit as st
        return st.secrets["db_url"]
    except Exception:
        return os.getenv("OLIST_DB_URL", "postgresql:///olist")


DB_URL = get_db_url()
