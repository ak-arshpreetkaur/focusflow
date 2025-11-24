# services/settings_service.py
from typing import Optional
from database import _db_connection

def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    cn = _db_connection(); cur = cn.cursor()
    cur.execute("SELECT v FROM settings WHERE k=%s", (key,))
    row = cur.fetchone()
    cur.close(); cn.close()
    return row[0] if row else default

def set_setting(key: str, value: str) -> None:
    cn = _db_connection(); cur = cn.cursor()
    cur.execute("REPLACE INTO settings (k, v) VALUES (%s, %s)", (key, value))
    cn.commit()
    cur.close(); cn.close()
