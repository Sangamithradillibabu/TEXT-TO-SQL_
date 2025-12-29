import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "database" / "text_to_sql.db"
USER_DB_PATH = BASE_DIR / "database" / "user.db"

OPENROUTER_API_KEY =" PUT API KEY HERE"
OPENROUTER_MODEL = "gpt-4o-mini"


