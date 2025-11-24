

# # database.py
# # MySQL init + low-level connection helpers + simple migrations

# import mysql.connector as mysql
# from config import DB_NAME, DB_HOST, DB_USER, DB_PASS

# TABLES = {
#     "tasks": (
#         "CREATE TABLE IF NOT EXISTS tasks ("
#         "  id INT AUTO_INCREMENT PRIMARY KEY,"
#         "  title VARCHAR(255) NOT NULL,"
#         "  notes TEXT,"
#         "  due_date DATE NULL,"
#         "  priority ENUM('Low','Medium','High') DEFAULT 'Medium',"
#         "  is_done BOOLEAN DEFAULT 0,"
#         "  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
#         ") ENGINE=InnoDB"
#     ),
#     "focus_sessions": (
#         "CREATE TABLE IF NOT EXISTS focus_sessions ("
#         "  id INT AUTO_INCREMENT PRIMARY KEY,"
#         "  task_id INT NULL,"
#         "  started_at DATETIME NOT NULL,"
#         "  ended_at DATETIME NOT NULL,"
#         "  duration_minutes INT NOT NULL,"
#         "  FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL"
#         ") ENGINE=InnoDB"
#     ),
#     "settings": (
#         "CREATE TABLE IF NOT EXISTS settings ("
#         "  k VARCHAR(64) PRIMARY KEY,"
#         "  v VARCHAR(255) NOT NULL"
#         ") ENGINE=InnoDB"
#     ),
# }

# def _server_connection():
#     return mysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS)

# def _db_connection():
#     return mysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)

# def init_db():
#     """Create database and tables if missing, then run migrations."""
#     cn = _server_connection()
#     cn.autocommit = True
#     cur = cn.cursor()
#     cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARACTER SET 'utf8mb4'")
#     cur.close(); cn.close()

#     cn = _db_connection()
#     cur = cn.cursor()
#     for _, ddl in TABLES.items():
#         cur.execute(ddl)
#     cn.commit()
#     cur.close(); cn.close()

#     migrate()  # ensure new columns exist


    
# # def migrate():
# #     """Add new columns if they are missing (compatible with MySQL builds without
# #     'ADD COLUMN IF NOT EXISTS')."""
# #     cn = _db_connection()
# #     cur = cn.cursor()

# #     def add_if_missing(table: str, column: str, col_def: str):
# #         cur.execute(
# #             """
# #             SELECT COUNT(*)
# #             FROM information_schema.COLUMNS
# #             WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s
# #             """,
# #             (DB_NAME, table, column),
# #         )
# #         (count,) = cur.fetchone()
# #         if count == 0:
# #             cur.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")

# #     # Add columns to tasks table if absent
# #     add_if_missing("tasks", "start_date", "start_date DATE NULL")
# #     add_if_missing(
# #         "tasks",
# #         "progress",
# #         "progress ENUM('Not started','In progress','Completed') DEFAULT 'Not started'"
# #     )

# #     cn.commit()
# #     cur.close()
# #     cn.close()


# def migrate():
#     """Add new columns if they are missing (works without 'ADD COLUMN IF NOT EXISTS')."""
#     cn = _db_connection()
#     cur = cn.cursor()

#     def add_if_missing(table: str, column: str, col_def: str):
#         cur.execute(
#             """
#             SELECT COUNT(*)
#             FROM information_schema.COLUMNS
#             WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s
#             """,
#             (DB_NAME, table, column),
#         )
#         (count,) = cur.fetchone()
#         if count == 0:
#             cur.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")

#     # existing new columns
#     add_if_missing("tasks", "start_date", "start_date DATE NULL")
#     add_if_missing(
#         "tasks",
#         "progress",
#         "progress ENUM('Not started','In progress','Completed') DEFAULT 'Not started'"
#     )
#     # NEW: track when a task was completed (for 'Done today')
#     add_if_missing("tasks", "completed_at", "completed_at TIMESTAMP NULL")

#     cn.commit()
#     cur.close()
#     cn.close()


import mysql.connector as mysql
from config import DB_NAME, DB_HOST, DB_USER, DB_PASS

TABLES = {
    "folders": (
        "CREATE TABLE IF NOT EXISTS folders ("
        "  id INT AUTO_INCREMENT PRIMARY KEY,"
        "  name VARCHAR(80) NOT NULL UNIQUE"
        ") ENGINE=InnoDB"
    ),
    "tasks": (
        "CREATE TABLE IF NOT EXISTS tasks ("
        "  id INT AUTO_INCREMENT PRIMARY KEY,"
        "  title VARCHAR(255) NOT NULL,"
        "  notes TEXT,"
        "  start_date DATE NULL,"
        "  due_date DATE NULL,"
        "  priority ENUM('Low','Medium','High') DEFAULT 'Medium',"
        "  progress ENUM('Not started','In progress','Completed') DEFAULT 'Not started',"
        "  is_done BOOLEAN DEFAULT 0,"
        "  completed_at TIMESTAMP NULL,"
        "  folder_id INT NULL,"
        "  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "  CONSTRAINT fk_tasks_folder FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE SET NULL"
        ") ENGINE=InnoDB"
    ),
    "focus_sessions": (
        "CREATE TABLE IF NOT EXISTS focus_sessions ("
        "  id INT AUTO_INCREMENT PRIMARY KEY,"
        "  task_id INT NULL,"
        "  started_at DATETIME NOT NULL,"
        "  ended_at DATETIME NOT NULL,"
        "  duration_minutes INT NOT NULL,"
        "  FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL"
        ") ENGINE=InnoDB"
    ),
    "settings": (
        "CREATE TABLE IF NOT EXISTS settings ("
        "  k VARCHAR(64) PRIMARY KEY,"
        "  v VARCHAR(255) NOT NULL"
        ") ENGINE=InnoDB"
    ),
}

def _server_connection():
    return mysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS)

def _db_connection():
    return mysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)

def init_db():
    cn = _server_connection(); cn.autocommit = True
    cur = cn.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARACTER SET 'utf8mb4'")
    cur.close(); cn.close()

    cn = _db_connection(); cur = cn.cursor()
    # Order matters (folders first for FK)
    for name in ["folders", "tasks", "focus_sessions", "settings"]:
        cur.execute(TABLES[name])
    cn.commit(); cur.close(); cn.close()

    migrate()

def migrate():
    """Backfill new columns / tables for older installs."""
    cn = _db_connection(); cur = cn.cursor()

    def add_if_missing(table: str, column: str, col_def: str):
        cur.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s
            """,
            (DB_NAME, table, column),
        )
        (count,) = cur.fetchone()
        if count == 0:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")

    # Ensure folders table exists (and default Inbox)
    cur.execute("CREATE TABLE IF NOT EXISTS folders (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(80) NOT NULL UNIQUE) ENGINE=InnoDB")

    # Add missing columns on tasks
    add_if_missing("tasks", "start_date", "start_date DATE NULL")
    add_if_missing("tasks", "progress", "progress ENUM('Not started','In progress','Completed') DEFAULT 'Not started'")
    add_if_missing("tasks", "completed_at", "completed_at TIMESTAMP NULL")
    add_if_missing("tasks", "folder_id", "folder_id INT NULL")

    # Try to create FK if not present
    try:
        cur.execute(
            "ALTER TABLE tasks ADD CONSTRAINT fk_tasks_folder "
            "FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE SET NULL"
        )
    except Exception:
        pass  # already exists or older MySQL variant

    # Ensure 'Inbox' folder
    cur.execute("INSERT IGNORE INTO folders (name) VALUES ('Inbox')")

    cn.commit()
    cur.close(); cn.close()

