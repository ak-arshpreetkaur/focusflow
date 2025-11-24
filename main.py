# main.py
import tkinter as tk
from tkinter import messagebox
from database import init_db
from ui import create_ui

def main():
    print("Starting FocusFlow…")

    # Database init
    try:
        init_db()
        print("✅ Database initialized.")
    except Exception as e:
        print("❌ Database init failed:", e)
        messagebox.showerror("Database Error", f"{e}")
        return

    # Launch UI
    try:
        root = tk.Tk()
        root.title("FocusFlow")
        app = create_ui(root)
        root.minsize(640, 480)
        print("✅ UI launched. Showing window...")
        root.mainloop()
    except Exception as e:
        print("❌ UI Error:", e)
        messagebox.showerror("UI Error", f"{e}")

if __name__ == "__main__":
    main()
