"""Project-wide configuration loaded from environment variables."""
import os

DB_URL = os.getenv("OLIST_DB_URL", "postgresql://apple@localhost:5432/olist")
