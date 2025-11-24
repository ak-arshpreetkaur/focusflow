# config.py
import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME  = os.getenv("FOCUSFLOW_DB", "focusflow")
DB_HOST  = os.getenv("FOCUSFLOW_HOST", "localhost")
DB_USER  = os.getenv("FOCUSFLOW_USER", "root")
DB_PASS  = os.getenv("FOCUSFLOW_PASSWORD", "")

WORK_MIN        = int(os.getenv("WORK_MIN", 25))
SHORT_BREAK_MIN = int(os.getenv("SHORT_BREAK_MIN", 5))
LONG_BREAK_MIN  = int(os.getenv("LONG_BREAK_MIN", 15))
