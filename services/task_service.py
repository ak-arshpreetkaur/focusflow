

# # services/task_service.py
# from typing import List, Optional, Tuple
# from datetime import date, datetime
# from database import _db_connection

# # --------- Create / Read ------------------------------------------------------

# def add_task(title: str, notes: str = "", due_date: Optional[date] = None,
#              priority: str = "Low"):
#     cn = _db_connection(); cur = cn.cursor()
#     cur.execute(
#         "INSERT INTO tasks (title, notes, due_date, priority) VALUES (%s,%s,%s,%s)",
#         (title.strip(), notes.strip(), due_date, priority)
#     )
#     cn.commit()
#     cur.close(); cn.close()

# def list_tasks(include_done: bool = True) -> List[Tuple]:
#     cn = _db_connection(); cur = cn.cursor()
#     cols = "id, title, notes, start_date, due_date, priority, progress, is_done"
#     if include_done:
#         cur.execute(f"SELECT {cols} FROM tasks ORDER BY created_at DESC")
#     else:
#         cur.execute(f"SELECT {cols} FROM tasks WHERE is_done=0 ORDER BY created_at DESC")
#     rows = cur.fetchall()
#     cur.close(); cn.close()
#     return rows

# # --------- Update helpers -----------------------------------------------------

# # def toggle_done(task_id: int, done: bool):
# #     cn = _db_connection(); cur = cn.cursor()
# #     cur.execute("UPDATE tasks SET is_done=%s WHERE id=%s", (1 if done else 0, task_id))
# #     cn.commit(); cur.close(); cn.close()

# def toggle_done(task_id: int, done: bool):
#     cn = _db_connection(); cur = cn.cursor()
#     if done:
#         cur.execute("UPDATE tasks SET is_done=1, completed_at=NOW() WHERE id=%s", (task_id,))
#     else:
#         cur.execute("UPDATE tasks SET is_done=0, completed_at=NULL WHERE id=%s", (task_id,))
#     cn.commit(); cur.close(); cn.close()

# def get_mini_stats():
#     """Return (done_today_count:int, focus_minutes_this_week:int)."""
#     cn = _db_connection(); cur = cn.cursor()

#     # Done today: completed_at is today
#     cur.execute("SELECT COUNT(*) FROM tasks WHERE is_done=1 AND DATE(completed_at)=CURDATE()")
#     (done_today,) = cur.fetchone()

#     # Focus this week: sum of session minutes in current ISO week (mode=1)
#     cur.execute("""
#         SELECT COALESCE(SUM(duration_minutes), 0)
#         FROM focus_sessions
#         WHERE YEARWEEK(started_at, 1) = YEARWEEK(CURDATE(), 1)
#     """)
#     (week_minutes,) = cur.fetchone()

#     cur.close(); cn.close()
#     return int(done_today or 0), int(week_minutes or 0)

# ##########

# def delete_task(task_id: int):
#     cn = _db_connection(); cur = cn.cursor()
#     cur.execute("DELETE FROM tasks WHERE id=%s", (task_id,))
#     cn.commit(); cur.close(); cn.close()

# def update_priority(task_id: int, priority: str):
#     cn = _db_connection(); cur = cn.cursor()
#     cur.execute("UPDATE tasks SET priority=%s WHERE id=%s", (priority, task_id))
#     cn.commit(); cur.close(); cn.close()

# def rename_task(task_id: int, new_title: str):
#     cn = _db_connection(); cur = cn.cursor()
#     cur.execute("UPDATE tasks SET title=%s WHERE id=%s", (new_title.strip(), task_id))
#     cn.commit(); cur.close(); cn.close()

# def set_start_date(task_id: int, d: Optional[date]):
#     cn = _db_connection(); cur = cn.cursor()
#     cur.execute("UPDATE tasks SET start_date=%s WHERE id=%s", (d, task_id))
#     cn.commit(); cur.close(); cn.close()

# def set_due_date(task_id: int, d: Optional[date]):
#     cn = _db_connection(); cur = cn.cursor()
#     cur.execute("UPDATE tasks SET due_date=%s WHERE id=%s", (d, task_id))
#     cn.commit(); cur.close(); cn.close()

# def set_progress(task_id: int, progress: str):
#     cn = _db_connection(); cur = cn.cursor()
#     cur.execute("UPDATE tasks SET progress=%s WHERE id=%s", (progress, task_id))
#     cn.commit(); cur.close(); cn.close()

# def log_focus_session(task_id: int | None, started_at: datetime, ended_at: datetime, duration_minutes: int):
#     """Insert a focus session; task_id can be None."""
#     cn = _db_connection(); cur = cn.cursor()
#     cur.execute(
#         "INSERT INTO focus_sessions (task_id, started_at, ended_at, duration_minutes) VALUES (%s,%s,%s,%s)",
#         (task_id, started_at, ended_at, int(duration_minutes))
#     )
#     cn.commit()
#     cur.close(); cn.close()



from datetime import date, datetime
from database import _db_connection

# ---------- Folders ----------
def list_folders():
    cn = _db_connection(); cur = cn.cursor()
    cur.execute("SELECT id, name FROM folders ORDER BY name ASC")
    rows = cur.fetchall()
    cur.close(); cn.close()
    return rows  # [(id, name), ...]

def create_folder(name: str) -> int:
    cn = _db_connection(); cur = cn.cursor()
    cur.execute("INSERT INTO folders (name) VALUES (%s)", (name,))
    cn.commit()
    fid = cur.lastrowid
    cur.close(); cn.close()
    return fid

def rename_folder(folder_id: int, new_name: str):
    cn = _db_connection(); cur = cn.cursor()
    cur.execute("UPDATE folders SET name=%s WHERE id=%s", (new_name, folder_id))
    cn.commit(); cur.close(); cn.close()

def delete_folder(folder_id: int):
    """Move tasks to Inbox then delete folder."""
    cn = _db_connection(); cur = cn.cursor()
    # Get Inbox id
    cur.execute("SELECT id FROM folders WHERE name='Inbox' LIMIT 1")
    row = cur.fetchone()
    inbox_id = row[0] if row else None
    if inbox_id is None:
        cur.execute("INSERT INTO folders (name) VALUES ('Inbox')")
        inbox_id = cur.lastrowid
    # Reassign tasks
    cur.execute("UPDATE tasks SET folder_id=%s WHERE folder_id=%s", (inbox_id, folder_id))
    # Delete folder
    cur.execute("DELETE FROM folders WHERE id=%s", (folder_id,))
    cn.commit(); cur.close(); cn.close()

def move_task_to_folder(task_id: int, folder_id: int | None):
    cn = _db_connection(); cur = cn.cursor()
    cur.execute("UPDATE tasks SET folder_id=%s WHERE id=%s", (folder_id, task_id))
    cn.commit(); cur.close(); cn.close()

# ---------- Tasks ----------
def add_task(title: str, notes=None, due_date=None, priority="Low", folder_id: int | None = None):
    cn = _db_connection(); cur = cn.cursor()
    cur.execute(
        "INSERT INTO tasks (title, notes, due_date, priority, folder_id) VALUES (%s,%s,%s,%s,%s)",
        (title, notes, due_date, priority, folder_id),
    )
    cn.commit()
    tid = cur.lastrowid
    cur.close(); cn.close()
    return tid

def list_tasks(include_done=True, folder_id: int | None = None):
    cn = _db_connection(); cur = cn.cursor()
    q = ("SELECT id, title, notes, start_date, due_date, priority, progress, is_done "
         "FROM tasks ")
    conds = []
    params = []
    if not include_done:
        conds.append("is_done=0")
    if folder_id is not None:
        conds.append("folder_id=%s"); params.append(folder_id)
    if conds:
        q += "WHERE " + " AND ".join(conds) + " "
    q += "ORDER BY created_at DESC"
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close(); cn.close()
    return rows

def toggle_done(task_id: int, done: bool):
    cn = _db_connection(); cur = cn.cursor()
    if done:
        cur.execute("UPDATE tasks SET is_done=1, completed_at=NOW() WHERE id=%s", (task_id,))
    else:
        cur.execute("UPDATE tasks SET is_done=0, completed_at=NULL WHERE id=%s", (task_id,))
    cn.commit(); cur.close(); cn.close()

def delete_task(task_id: int):
    cn = _db_connection(); cur = cn.cursor()
    cur.execute("DELETE FROM tasks WHERE id=%s", (task_id,))
    cn.commit(); cur.close(); cn.close()

def update_priority(task_id: int, level: str):
    cn = _db_connection(); cur = cn.cursor()
    cur.execute("UPDATE tasks SET priority=%s WHERE id=%s", (level, task_id))
    cn.commit(); cur.close(); cn.close()

def set_progress(task_id: int, state: str):
    cn = _db_connection(); cur = cn.cursor()
    cur.execute("UPDATE tasks SET progress=%s WHERE id=%s", (state, task_id))
    cn.commit(); cur.close(); cn.close()

def rename_task(task_id: int, new_title: str):
    cn = _db_connection(); cur = cn.cursor()
    cur.execute("UPDATE tasks SET title=%s WHERE id=%s", (new_title, task_id))
    cn.commit(); cur.close(); cn.close()

def set_start_date(task_id: int, dt):
    cn = _db_connection(); cur = cn.cursor()
    cur.execute("UPDATE tasks SET start_date=%s WHERE id=%s", (dt, task_id))
    cn.commit(); cur.close(); cn.close()

def set_due_date(task_id: int, dt):
    cn = _db_connection(); cur = cn.cursor()
    cur.execute("UPDATE tasks SET due_date=%s WHERE id=%s", (dt, task_id))
    cn.commit(); cur.close(); cn.close()

# ---------- Stats / Sessions ----------
def get_mini_stats():
    cn = _db_connection(); cur = cn.cursor()
    cur.execute("SELECT COUNT(*) FROM tasks WHERE is_done=1 AND DATE(completed_at)=CURDATE()")
    (done_today,) = cur.fetchone()
    cur.execute("""
        SELECT COALESCE(SUM(duration_minutes), 0)
        FROM focus_sessions
        WHERE YEARWEEK(started_at, 1) = YEARWEEK(CURDATE(), 1)
    """)
    (week_minutes,) = cur.fetchone()
    cur.close(); cn.close()
    return int(done_today or 0), int(week_minutes or 0)

def log_focus_session(task_id: int | None, started_at: datetime, ended_at: datetime, duration_minutes: int):
    cn = _db_connection(); cur = cn.cursor()
    cur.execute(
        "INSERT INTO focus_sessions (task_id, started_at, ended_at, duration_minutes) VALUES (%s,%s,%s,%s)",
        (task_id, started_at, ended_at, int(duration_minutes))
    )
    cn.commit(); cur.close(); cn.close()
