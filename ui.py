
# ui.py
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, date, timedelta
import os

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

from services.task_service import (
    add_task, list_tasks, toggle_done, delete_task, update_priority,
    rename_task, set_start_date, set_due_date, set_progress, get_mini_stats,
    log_focus_session, list_folders, create_folder, rename_folder,
    delete_folder, move_task_to_folder
)
from services.settings_service import get_setting, set_setting

# --------- Pastel themes ----------
THEMES = {
    "White": {"bg": "#E9EEF5","fg":"#0F172A","muted":"#6B7280","accent":"#3B82F6","card":"#DEE6F1","border":"#C7D2E2","header":"#CBD5E1"},
    "Blush": {"bg": "#F9DCE8","fg":"#1F2937","muted":"#6B7280","accent":"#F472B6","card":"#F4C8DA","border":"#ECABC8","header":"#EFBFD4"},
    "Lilac": {"bg": "#E3DAFF","fg":"#1F2937","muted":"#6B7280","accent":"#8B5CF6","card":"#D7CBFF","border":"#C8B8FF","header":"#CDC1FF"},
    "Mint":  {"bg": "#D4F6E9","fg":"#1F2937","muted":"#6B7280","accent":"#10B981","card":"#C3F0DE","border":"#AEE8D0","header":"#B8EBD6"},
    "Sky":   {"bg": "#CFE1FF","fg":"#0F172A","muted":"#475569","accent":"#3B82F6","card":"#BCD3FF","border":"#9FBEFF","header":"#A9C6FF"},
    "Sand":  {"bg": "#EFE2C9","fg":"#1F2937","muted":"#6B7280","accent":"#D97706","card":"#E5D6B8","border":"#D5C49C","header":"#DCCCA9"},
    # New!
    #"Peach": {"bg":"#FFE3D1","fg":"#1F2937","muted":"#6B7280","accent":"#FB923C","card":"#FFD3B8","border":"#FFC19A","header":"#FFC9A6"},
    #"Sage":  {"bg":"#DCEFE3","fg":"#1F2937","muted":"#6B7280","accent":"#34D399","card":"#CCE6D6","border":"#B8DAC7","header":"#C6E2D2"},
    #"Periwinkle":{"bg":"#E0E4FF","fg":"#1F2937","muted":"#6B7280","accent":"#6366F1","card":"#D2D7FF","border":"#BEC6FF","header":"#C7CDFE"},
    #"Seafoam":{"bg":"#DFF9F3","fg":"#1F2937","muted":"#6B7280","accent":"#14B8A6","card":"#D0F3EC","border":"#BCEAE2","header":"#C7EEE8"},
}

def pick_first_available_font(root, candidates):
    available = set(tkfont.families(root))
    for name in candidates:
        if name in available:
            return name
    return "Times New Roman"

PRIORITY_ORDER = {"Low": 0, "Medium": 1, "High": 2}
PROGRESS_ORDER = {"Not started": 0, "In progress": 1, "Completed": 2}

class ThemeManager:
    def __init__(self, root):
        self.root = root
        self.style = ttk.Style(root)
        try: self.style.theme_use("clam")
        except Exception: pass

    def apply(self, p: dict):
        self.root.configure(bg=p["bg"])
        # Base
        self.style.configure(".", background=p["bg"], foreground=p["fg"])
        self.style.configure("TFrame", background=p["bg"])
        self.style.configure("Toolbar.TFrame", background=p["bg"])
        self.style.configure("Card.TFrame", background=p["card"])
        self.style.configure("TLabel", background=p["bg"], foreground=p["fg"])
        self.style.configure("Muted.TLabel", background=p["bg"], foreground=p["muted"])
        self.style.configure("TEntry", fieldbackground=p["card"], foreground=p["fg"])
        self.style.configure("TButton", padding=6)
        self.style.configure("Accent.TButton", background=p["accent"], foreground="#FFFFFF")
        # Spinbox (timer pickers) – soften to card color
        self.style.configure("TSpinbox", fieldbackground=p["card"], foreground=p["fg"], background=p["card"])
        # Progressbar + table
        self.style.configure("Accent.Horizontal.TProgressbar", troughcolor=p["card"], background=p["accent"], bordercolor=p["border"])
        self.style.configure("Treeview", background=p["bg"], fieldbackground=p["bg"], foreground=p["fg"], bordercolor=p["border"])
        #self.style.configure("Treeview.Heading", background=p["header"], foreground=p["fg"], relief="flat")
        
        self.style.configure("Treeview.Heading", background=p["header"], foreground=p["fg"],
                     relief="flat", font=("Helvetica", 10, "bold"))


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.logo_small = None
        self._load_logo()

        # Theme
        self.tm = ThemeManager(root)
        self.theme_name = get_setting("theme_name", "Sky")
        self.palette = THEMES.get(self.theme_name, THEMES["Sky"])
        self.tm.apply(self.palette)

        # Header (title + theme + folder picker)
        # header = ttk.Frame(root, style="TFrame"); header.pack(fill="x", padx=12, pady=(10, 6))
        # serif_stack = ["Georgia","Times New Roman","Times","Palatino Linotype","Palatino","Cambria","DejaVu Serif","Liberation Serif","Noto Serif"]
        # family = pick_first_available_font(self.root, serif_stack)
        # self.header_font = tkfont.Font(family=family, size=20, weight="normal")
        # ttk.Label(header, text="FocusFlow", font=self.header_font).pack(side="left", padx=(0, 12))
        header = ttk.Frame(root, style="TFrame")
        header.pack(fill="x", padx=12, pady=(10, 6))

        # LOGO ONLY — no text label
        if self.logo_small:
            ttk.Label(header, image=self.logo_small, style="TLabel").pack(side="left", padx=(0, 12))

        # Folder picker
        folder_bar = ttk.Frame(header, style="TFrame"); folder_bar.pack(side="left")
        ttk.Label(folder_bar, text="Folder:").pack(side="left", padx=(0,6))
        self.folder_var = tk.StringVar()
        self.folder_id = None
        self.folder_combo = ttk.Combobox(folder_bar, textvariable=self.folder_var, state="readonly", width=16)
        self.folder_combo.pack(side="left")
        self.folder_combo.bind("<<ComboboxSelected>>", self.on_folder_change)
        ttk.Button(folder_bar, text="New", command=self.on_add_folder).pack(side="left", padx=4)
        ttk.Button(folder_bar, text="Rename", command=self.on_rename_folder).pack(side="left", padx=4)
        ttk.Button(folder_bar, text="Delete", command=self.on_delete_folder).pack(side="left", padx=4)

        right = ttk.Frame(header, style="TFrame"); right.pack(side="right")
        ttk.Label(right, text="Theme:").pack(side="left", padx=(0, 6))
        self.theme_var = tk.StringVar(value=self.theme_name)
        tcombo = ttk.Combobox(right, textvariable=self.theme_var, values=list(THEMES.keys()), state="readonly", width=10)
        tcombo.pack(side="left"); tcombo.bind("<<ComboboxSelected>>", self.on_theme_change)

        # Top toolbar: Filters dropdown + priority filter + stats/goal
        tools = ttk.Frame(root, style="Toolbar.TFrame"); tools.pack(fill="x", padx=12, pady=(0, 6))

        ttk.Label(tools, text="Filters:").pack(side="left", padx=(0,6))
        self.filter_mode = get_setting("filter_mode", "all")
        self.filter_var = tk.StringVar(value=self.filter_mode)
        self.filter_combo = ttk.Combobox(
            tools, textvariable=self.filter_var, state="readonly", width=14,
            values=["all","today","week","overdue","done","p_not","p_in","p_done"]
        )
        self.filter_combo.pack(side="left")
        self.filter_combo.bind("<<ComboboxSelected>>", lambda e: self.on_set_filter(self.filter_var.get()))

        ttk.Label(tools, text="  |  Priority:", style="Muted.TLabel").pack(side="left", padx=(8, 6))
        self.priority_filter = get_setting("priority_filter", "All")
        self.priority_var_filter = tk.StringVar(value=self.priority_filter)
        pcombo = ttk.Combobox(tools, textvariable=self.priority_var_filter, values=["All","High","Medium","Low"], state="readonly", width=8)
        pcombo.pack(side="left")
        pcombo.bind("<<ComboboxSelected>>", lambda e: self.on_set_priority_filter(self.priority_var_filter.get()))

        # Stats + goal
        stats = ttk.Frame(root, style="Toolbar.TFrame"); stats.pack(fill="x", padx=12, pady=(0, 6))
        self.done_today_var = tk.StringVar(value="Done today: 0")
        ttk.Label(stats, textvariable=self.done_today_var).pack(side="left", padx=(0, 12))
        self.week_minutes_var = tk.StringVar(value="Focus this week: 0 min")
        ttk.Label(stats, textvariable=self.week_minutes_var).pack(side="left", padx=(0, 8))
        self.weekly_goal = int(get_setting("weekly_goal_min", "300") or "300")
        self.goal_label = ttk.Label(stats, text=f"Goal: {self.weekly_goal} min", style="Muted.TLabel")
        self.goal_label.pack(side="left", padx=(8, 8))
        ttk.Button(stats, text="Set goal", command=self.on_set_goal).pack(side="left")
        self.pb = ttk.Progressbar(stats, style="Accent.Horizontal.TProgressbar", orient="horizontal",
                                  length=220, mode="determinate", maximum=self.weekly_goal, value=0)
        self.pb.pack(side="left", padx=(8,0))

        # Add task
        card = ttk.Frame(root, style="Card.TFrame"); card.pack(fill="x", padx=12, pady=(0, 8))
        self.title_var = tk.StringVar(); self.priority_var = tk.StringVar(value="Low")
        ttk.Label(card, text="New Task").grid(row=0, column=0, padx=8, pady=10, sticky="w")
        ttk.Entry(card, textvariable=self.title_var, width=42).grid(row=0, column=1, padx=8, pady=10)
        ttk.Label(card, text="Priority").grid(row=0, column=2, padx=6, pady=10, sticky="e")
        self.priority_combo = ttk.Combobox(card, textvariable=self.priority_var, width=10, values=["Low","Medium","High"], state="readonly")
        self.priority_combo.grid(row=0, column=3, padx=6, pady=10)
        ttk.Button(card, text="Add", style="Accent.TButton", command=self.add_task_click).grid(row=0, column=4, padx=8, pady=10)

        # Main content (table + pomodoro)
        content = ttk.Frame(root, style="TFrame"); content.pack(fill="both", expand=True, padx=12, pady=8)

        # Table (left)
        table_frame = ttk.Frame(content, style="TFrame"); table_frame.pack(side="left", fill="both", expand=True)
        self.tree = ttk.Treeview(table_frame, columns=("title","start","due","priority","progress","done"), show="headings", height=14)
        # for col, txt, w in [("title","Title",320),("start","Start Date",120),("due","Due Date",120),
        #                     ("priority","Priority",110),("progress","Progress",140),("done","Done",80)]:
        #     self.tree.heading(col, text=txt)
        #     self.tree.column(col, width=w, anchor="center")
        
        for col, txt, w in [("title","Title",320),("start","Start Date",120),("due","Due Date",120),
                    ("priority","Priority",110),("progress","Progress",140),("done","Done",80)]:
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=w, anchor="center")
            
        self.tree.tag_configure("header_font", font=("Helvetica", 10, "bold"))


        
        self.tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview); sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

        # Right-click menu (with Move to folder)
        self.ctx = tk.Menu(self.root, tearoff=0)
        self.move_menu = tk.Menu(self.ctx, tearoff=0)  # populated on open
        self.ctx.add_command(label="Rename", command=self.rename_selected)
        self.ctx.add_cascade(label="Move to folder", menu=self.move_menu)
        self.ctx.add_separator()
        self.ctx.add_command(label="Mark Done", command=self.mark_done)
        self.ctx.add_command(label="Mark Undone", command=self.mark_undone)
        psubmenu = tk.Menu(self.ctx, tearoff=0)
        for lvl in ["Low","Medium","High"]:
            psubmenu.add_command(label=lvl, command=lambda v=lvl: self.set_priority(v))
        self.ctx.add_cascade(label="Priority", menu=psubmenu)
        gsubmenu = tk.Menu(self.ctx, tearoff=0)
        for st in ["Not started","In progress","Completed"]:
            gsubmenu.add_command(label=st, command=lambda v=st: self.set_progress(v))
        self.ctx.add_cascade(label="Progress", menu=gsubmenu)
        self.ctx.add_command(label="Set Start Date…", command=lambda: self.set_date(kind="start"))
        self.ctx.add_command(label="Set Due Date…", command=lambda: self.set_date(kind="due"))
        self.ctx.add_separator(); self.ctx.add_command(label="Delete", command=self.delete_task_click)
        self.tree.bind("<Button-3>", self.show_context); self.tree.bind("<Button-2>", self.show_context)

        # Pomodoro (right)
        self.timer_mode = tk.StringVar(value=get_setting("timer_mode", "work"))  # work/break
        self.auto_start_break = tk.BooleanVar(value=(get_setting("auto_start_break", "0") == "1"))

        def _get_int(k, default):
            try: return int(get_setting(k, str(default)) or default)
            except: return default
        self.work_h = tk.StringVar(value=str(_get_int("work_h", 0)))
        self.work_m = tk.StringVar(value=str(_get_int("work_m", 25)))
        self.work_s = tk.StringVar(value=str(_get_int("work_s", 0)))
        self.break_h = tk.StringVar(value=str(_get_int("break_h", 0)))
        self.break_m = tk.StringVar(value=str(_get_int("break_m", 10)))
        self.break_s = tk.StringVar(value=str(_get_int("break_s", 0)))

        self.remaining = 0; self.timer_after_id = None
        self.timer_running = False; self.timer_paused = False
        self.timer_started_at: datetime | None = None
        self.timer_link_task_id: int | None = None
        self.timer_link_task_title = tk.StringVar(value="(no task linked)")
        self.timer_display = tk.StringVar(value="25:00")

        pom = ttk.Frame(content, style="Card.TFrame"); pom.pack(side="right", fill="y", padx=(8, 0))
        ttk.Label(pom, text="Pomodoro", font=("Helvetica", 12, "bold")).pack(padx=10, pady=(10, 6))

        link_row = ttk.Frame(pom, style="Card.TFrame"); link_row.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Label(link_row, text="Linked task:", style="Muted.TLabel").pack(side="left")
        ttk.Label(link_row, textvariable=self.timer_link_task_title).pack(side="left", padx=(6,0))
        ttk.Button(link_row, text="Link current", command=self.link_current_task).pack(side="right")

        mode_row = ttk.Frame(pom, style="Card.TFrame"); mode_row.pack(fill="x", padx=10, pady=(0, 6))
        ttk.Radiobutton(mode_row, text="Work", value="work", variable=self.timer_mode, command=self.on_change_mode).pack(side="left")
        ttk.Radiobutton(mode_row, text="Break", value="break", variable=self.timer_mode, command=self.on_change_mode).pack(side="left", padx=6)

        # Themed ttk.Spinbox (no harsh black)
        def tspin(parent, var, frm, to, w=3):
            sb = ttk.Spinbox(parent, textvariable=var, from_=frm, to=to, wrap=True, width=w, justify="center")
            return sb

        # (pom, style="Card.TFrame"); picker.pack(fill="x", padx=10, pady=(0, 6))
        # ttk.Label(picker, text="Work:", width=8).grid(row=0, column=0, sticky="w", padx=(0,6), pady=2)
        # tspin(picker, self.work_h, 0, 23).grid(row=0, column=1); ttk.Label(picker, text="h").grid(row=0, column=2, padx=(2,8))
        # tspin(picker, self.work_m, 0, 59).grid(row=0, column=3); ttk.Label(picker, text="m").grid(row=0, column=4, padx=(2,8))
        # tspin(picker, self.work_s, 0, 59).grid(row=0, column=5); ttk.Label(picker, text="s").grid(row=0, column=6, padx=(2,8))

        # ttk.Label(picker, text="Break:", width=8).grid(row=1, column=0, sticky="w", padx=(0,6), pady=2)
        # tspin(picker, self.break_h, 0, 23).grid(row=1, column=1); ttk.Label(picker, text="h").grid(row=1, column=2, padx=(2,8))
        # tspin(picker, self.break_m, 0, 59).grid(row=1, column=3); ttk.Label(picker, text="m").grid(row=1, column=4, padx=(2,8))
        # tspin(picker, self.break_s, 0, 59).grid(row=1, column=5); ttk.Label(picker, text="s").grid(row=1, column=6, padx=(2,8))

        # def _load_logo(self):
        # #"""Load the app icon from assets/icon and scale it for the header.
        # #Also sets the window icon (macOS Dock icon may not change, that’s normal).
        # #"""
        #     try:
        #         icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon", "focusflow_icon_256.png")
        #         if not os.path.exists(icon_path):
        #             print("Icon not found at:", icon_path)
        #             return
#picker = ttk.Frame
        #         target_h = 32  # header height for the logo; tweak 28–40 to taste

        #         if 'PIL_AVAILABLE' in globals() and PIL_AVAILABLE:
        #             im = Image.open(icon_path).convert("RGBA")
        #             target_w = round(im.width * (target_h / im.height))
        #             im = im.resize((target_w, target_h), Image.LANCZOS)
        #             self.logo_small = ImageTk.PhotoImage(im)
        #         else:
        #             # Fallback: Tk loader (no smooth scaling)
        #             img = tk.PhotoImage(file=icon_path)
        #             if img.height() > target_h:
        #                 factor = max(1, img.height() // target_h)
        #                 img = img.subsample(factor, factor)
        #             self.logo_small = img

        #         # Set window icon (has effect on Windows/Linux; limited effect on macOS)
        #         try:
        #             self.root.iconphoto(True, self.logo_small)
        #         except Exception:
        #             pass

        #     except Exception as e:
        #         print("Logo load failed:", e)
        #         self.logo_small = None

        def _on_picker_change(*_):
            self._persist_durations()
            if not self.timer_running:
                self.remaining = self._get_duration_seconds(self.timer_mode.get())
                self._update_timer_display()
        for v in [self.work_h, self.work_m, self.work_s, self.break_h, self.break_m, self.break_s]:
            v.trace_add("write", _on_picker_change)

        timer_box = ttk.Frame(pom, style="Card.TFrame"); timer_box.pack(fill="x", padx=10, pady=6)
        # self.timer_font = tkfont.Font(family="Helvetica", size=32, weight="bold")
        # ttk.Label(timer_box, textvariable=self.timer_display, font=self.timer_font).pack(pady=(4, 4))
        
        # ---------- Circular Timer ----------
        canvas_size = 180
        self.canvas = tk.Canvas(pom, width=canvas_size, height=canvas_size,
                        bg=self.palette["card"], highlightthickness=0)
        self.canvas.pack(pady=10)

        # create circular ring background
        self.circle = self.canvas.create_oval(10, 10, canvas_size-10, canvas_size-10,
                                      outline=self.palette["border"], width=12)

        # active progress arc (accent color)
        self.arc = self.canvas.create_arc(10, 10, canvas_size-10, canvas_size-10,
                                  start=90, extent=0, style="arc",
                                  outline=self.palette["accent"], width=12)

        # timer text
        self.timer_font = tkfont.Font(family="Helvetica", size=26, weight="bold")
        self.timer_text = self.canvas.create_text(canvas_size/2, canvas_size/2,
                                          text="25:00", fill=self.palette["fg"],
                                          font=self.timer_font)

        # timer preset selector
        preset_frame = ttk.Frame(pom, style="Card.TFrame"); preset_frame.pack(fill="x", padx=10, pady=(0,10))
        self.preset_var = tk.StringVar(value="25-5")
        ttk.Radiobutton(preset_frame, text="25 min focus / 5 min break", value="25-5", variable=self.preset_var,
                command=self._apply_preset).pack(anchor="w", pady=2)
        ttk.Radiobutton(preset_frame, text="50 min focus / 10 min break", value="50-10", variable=self.preset_var,
                command=self._apply_preset).pack(anchor="w", pady=2)


        controls = ttk.Frame(pom, style="Card.TFrame"); controls.pack(fill="x", padx=10, pady=(0,10))
        ttk.Button(controls, text="Start", style="Accent.TButton", command=self.on_start_timer).pack(side="left")
        ttk.Button(controls, text="Pause", command=self.on_pause_timer).pack(side="left", padx=6)
        ttk.Button(controls, text="Reset", command=self.on_reset_timer).pack(side="left")
        opts = ttk.Frame(pom, style="Card.TFrame"); opts.pack(fill="x", padx=10, pady=(0,10))
        ttk.Checkbutton(opts, text="Auto-start break after work", variable=self.auto_start_break, command=self.on_toggle_auto).pack(side="left")

        # Bottom actions
        actions = ttk.Frame(root, style="TFrame"); actions.pack(fill="x", padx=12, pady=(6, 10))
        ttk.Button(actions, text="Mark Done", command=self.mark_done).pack(side="left")
        ttk.Button(actions, text="Mark Undone", command=self.mark_undone).pack(side="left", padx=6)
        ttk.Button(actions, text="Delete", command=self.delete_task_click).pack(side="left", padx=6)

        self.reload_folders()  # set folder combo + selection
        self.reload_tasks()
        self.refresh_stats()
        self.on_change_mode()

    def _load_logo(self):
        #"""Load the app icon from assets/icon and scale it for the header.
        #Also sets the window icon (macOS Dock icon may not change, that’s normal).
        #"""
            try:
                icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon", "focusflow_icon_256.png")
                if not os.path.exists(icon_path):
                    print("Icon not found at:", icon_path)
                    return

                target_h = 100  # header height for the logo; tweak 28–40 to taste

                if 'PIL_AVAILABLE' in globals() and PIL_AVAILABLE:
                    im = Image.open(icon_path).convert("RGBA")
                    target_w = round(im.width * (target_h / im.height))
                    im = im.resize((target_w, target_h), Image.LANCZOS)
                    self.logo_small = ImageTk.PhotoImage(im)
                else:
                    # Fallback: Tk loader (no smooth scaling)
                    img = tk.PhotoImage(file=icon_path)
                    if img.height() > target_h:
                        factor = max(1, img.height() // target_h)
                        img = img.subsample(factor, factor)
                    self.logo_small = img

                # Set window icon (has effect on Windows/Linux; limited effect on macOS)
                try:
                    self.root.iconphoto(True, self.logo_small)
                except Exception:
                    pass

            except Exception as e:
                print("Logo load failed:", e)
                self.logo_small = None

    # ---------- Folders ----------
    def reload_folders(self):
        folders = list_folders()
        names = [name for (_id, name) in folders]
        ids   = [fid  for (fid, _name) in folders]
        # remember / default to Inbox
        saved = get_setting("current_folder_id", "")
        self.folder_map = dict(zip(names, ids))
        self.folder_combo.configure(values=names)
        if saved and any(fid == int(saved) for fid in ids):
            idx = ids.index(int(saved)); self.folder_combo.set(names[idx]); self.folder_id = ids[idx]
        else:
            # pick Inbox or first
            if "Inbox" in self.folder_map:
                self.folder_combo.set("Inbox"); self.folder_id = self.folder_map["Inbox"]
            elif names:
                self.folder_combo.set(names[0]); self.folder_id = self.folder_map[names[0]]

    def on_folder_change(self, _evt=None):
        name = self.folder_var.get()
        self.folder_id = self.folder_map.get(name)
        if self.folder_id is not None:
            set_setting("current_folder_id", str(self.folder_id))
        self.reload_tasks()

    def on_add_folder(self):
        name = simpledialog.askstring("New folder", "Folder name:", parent=self.root)
        if not name: return
        try:
            fid = create_folder(name.strip())
            self.reload_folders()
            # select it
            self.folder_combo.set(name.strip()); self.folder_id = fid
            set_setting("current_folder_id", str(fid))
            self.reload_tasks()
        except Exception as e:
            messagebox.showerror("Folder", f"Could not create folder:\n{e}")

    def on_rename_folder(self):
        if not self.folder_id: return
        new = simpledialog.askstring("Rename folder", "New name:", initialvalue=self.folder_var.get(), parent=self.root)
        if not new: return
        try:
            rename_folder(self.folder_id, new.strip())
            self.reload_folders(); self.reload_tasks()
        except Exception as e:
            messagebox.showerror("Folder", f"Could not rename folder:\n{e}")

    def on_delete_folder(self):
        if not self.folder_id: return
        if self.folder_var.get() == "Inbox":
            messagebox.showinfo("Folder", "Inbox cannot be deleted."); return
        if not messagebox.askyesno("Delete folder", "Move tasks to Inbox and delete this folder?"):
            return
        try:
            delete_folder(self.folder_id)
            self.reload_folders(); self.reload_tasks()
        except Exception as e:
            messagebox.showerror("Folder", f"Could not delete folder:\n{e}")

    # ---------- Filters / priority ----------
    def on_set_filter(self, key: str):
        self.filter_mode = key; set_setting("filter_mode", key)
        self.reload_tasks(); self.refresh_stats()

    def on_set_priority_filter(self, value: str):
        self.priority_filter = value; set_setting("priority_filter", value)
        self.reload_tasks()

    # ---------- Theme / stats ----------
    # def on_theme_change(self, _evt=None):
    #     name = self.theme_var.get()
    #     self.theme_name = name; self.palette = THEMES[name]
    #     set_setting("theme_name", name); self.tm.apply(self.palette)
    
    def on_theme_change(self, _evt=None):
        name = self.theme_var.get()
        self.theme_name = name
        self.palette = THEMES[name]

        # Save and apply theme
        set_setting("theme_name", name)
        self.tm.apply(self.palette)

        # 🎨 Update Pomodoro colors (circle, arc, timer text)
        if hasattr(self, "canvas"):
            p = self.palette
            self.canvas.config(bg=p["card"])
            self.canvas.itemconfig(self.circle, outline=p["border"])
            self.canvas.itemconfig(self.arc, outline=p["accent"])
            self.canvas.itemconfig(self.timer_text, fill=p["fg"])


    def refresh_stats(self):
        done_today, week_minutes = get_mini_stats()
        self.done_today_var.set(f"Done today: {done_today}")
        self.week_minutes_var.set(f"Focus this week: {week_minutes} min")
        self.pb.configure(maximum=self.weekly_goal, value=min(week_minutes, self.weekly_goal))

    def on_set_goal(self):
        val = simpledialog.askinteger("Weekly goal", "Minutes per week:", initialvalue=self.weekly_goal, minvalue=30, maxvalue=10080, parent=self.root)
        if val:
            self.weekly_goal = int(val)
            set_setting("weekly_goal_min", str(self.weekly_goal))
            self.goal_label.configure(text=f"Goal: {self.weekly_goal} min")
            self.pb.configure(maximum=self.weekly_goal)

    # ---------- Tasks ----------
    def add_task_click(self):
        title = self.title_var.get().strip()
        if not title:
            messagebox.showwarning("Missing title", "Please type a task title."); return
        add_task(title, priority=(self.priority_var.get() or "Low"), folder_id=self.folder_id)
        self.title_var.set(""); self.priority_var.set("Low")
        self.reload_tasks()

    def reload_tasks(self):
        rows = self._apply_filters(list_tasks(include_done=True, folder_id=self.folder_id))
        self.tree.delete(*self.tree.get_children())
        for (tid, title, _notes, start_date, due_date, priority, progress, is_done) in rows:
            start_str = start_date.strftime("%Y-%m-%d") if start_date else ""
            due_str   = due_date.strftime("%Y-%m-%d") if due_date else ""
            self.tree.insert("", "end", iid=str(tid), values=(title, start_str, due_str, priority, progress, "✓" if is_done else ""))
        self.tree.update_idletasks(); self.root.update_idletasks()

    def _selected_id(self) -> int | None:
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def mark_done(self):
        tid = self._selected_id()
        if tid is None: return
        toggle_done(tid, True); self.reload_tasks(); self.refresh_stats()

    def mark_undone(self):
        tid = self._selected_id()
        if tid is None: return
        toggle_done(tid, False); self.reload_tasks(); self.refresh_stats()

    def delete_task_click(self):
        tid = self._selected_id()
        if tid is None: return
        if messagebox.askyesno("Delete", "Delete selected task?"):
            delete_task(tid); self.reload_tasks(); self.refresh_stats()

    # ---------- Right-click actions ----------
    def show_context(self, event):
        # rebuild Move-to-folder submenu with current folders
        self.move_menu.delete(0, "end")
        for fid, name in list_folders():
            self.move_menu.add_command(label=name, command=lambda f=fid: self.move_to_folder(f))
        row = self.tree.identify_row(event.y)
        if row: self.tree.selection_set(row)
        try:
            self.ctx.tk_popup(event.x_root, event.y_root)
        finally:
            self.ctx.grab_release()

    def move_to_folder(self, folder_id: int):
        tid = self._selected_id()
        if tid is None: return
        move_task_to_folder(tid, folder_id)
        self.reload_tasks()

    def set_priority(self, level: str):
        tid = self._selected_id()
        if tid is None: return
        update_priority(tid, level); self.reload_tasks()

    def set_progress(self, state: str):
        tid = self._selected_id()
        if tid is None: return
        set_progress(tid, state); self.reload_tasks()

    def rename_selected(self):
        tid = self._selected_id()
        if tid is None: return
        cur_vals = self.tree.item(str(tid), "values")
        current_title = cur_vals[0] if cur_vals else ""
        new_title = simpledialog.askstring("Rename Task", "New title:", initialvalue=current_title, parent=self.root)
        if new_title and new_title.strip():
            rename_task(tid, new_title.strip()); self.reload_tasks()

    def set_date(self, kind: str):
        tid = self._selected_id()
        if tid is None: return
        prompt = "Start date (YYYY-MM-DD, blank to clear):" if kind == "start" else "Due date (YYYY-MM-DD, blank to clear):"
        s = simpledialog.askstring("Set Date", prompt, parent=self.root)
        if s is None: return
        s = s.strip()
        if s == "":
            (set_start_date if kind == "start" else set_due_date)(tid, None); self.reload_tasks(); return
        try:
            dt = datetime.strptime(s, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Invalid date", "Please use YYYY-MM-DD."); return
        (set_start_date if kind == "start" else set_due_date)(tid, dt); self.reload_tasks()

    # ---------- Filtering ----------
    def _apply_filters(self, rows):
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        def in_week(d): return d is not None and start_of_week <= d <= end_of_week

        mode = self.filter_mode
        out = []
        for (tid, title, _notes, start_date, due_date, priority, progress, is_done) in rows:
            keep = True
            if   mode == "today":   keep = (due_date == today)
            elif mode == "week":    keep = in_week(due_date)
            elif mode == "overdue": keep = (due_date is not None and due_date < today and not is_done)
            elif mode == "done":    keep = bool(is_done)
            elif mode == "p_not":   keep = (progress == "Not started")
            elif mode == "p_in":    keep = (progress == "In progress")
            elif mode == "p_done":  keep = (progress == "Completed")
            if not keep: continue
            if self.priority_filter != "All" and priority != self.priority_filter: continue
            out.append((tid, title, _notes, start_date, due_date, priority, progress, is_done))
        return out

    # ---------- Timer ----------
    def _get_duration_seconds(self, mode: str) -> int:
        if mode == "work":
            h, m, s = self.work_h.get(), self.work_m.get(), self.work_s.get()
        else:
            h, m, s = self.break_h.get(), self.break_m.get(), self.break_s.get()
        try: return max(int(h)*3600 + int(m)*60 + int(s), 0)
        except Exception: return 0

    def _persist_durations(self):
        for k, v in {
            "work_h": self.work_h.get(), "work_m": self.work_m.get(), "work_s": self.work_s.get(),
            "break_h": self.break_h.get(), "break_m": self.break_m.get(), "break_s": self.break_s.get(),
        }.items():
            set_setting(k, str(v))

    def on_change_mode(self):
        mode = self.timer_mode.get()
        set_setting("timer_mode", mode)
        total = self._get_duration_seconds(mode)
        if not self.timer_running or not self.timer_paused:
            self.remaining = total
        self._update_timer_display()
        
    def _apply_preset(self):
        preset = self.preset_var.get()
        if preset == "25-5":
            self.work_m.set("25")
            self.break_m.set("5")
        elif preset == "50-10":
            self.work_m.set("50")
            self.break_m.set("10")
        self.on_change_mode()

    def link_current_task(self):
        tid = self._selected_id()
        if tid is None:
            self.timer_link_task_id = None
            self.timer_link_task_title.set("(no task linked)"); return
        vals = self.tree.item(str(tid), "values")
        self.timer_link_task_id = tid
        self.timer_link_task_title.set(vals[0] or f"Task #{tid}")

    def on_toggle_auto(self):
        set_setting("auto_start_break", "1" if self.auto_start_break.get() else "0")

    def on_start_timer(self):
        self._persist_durations()
        if self.timer_link_task_id is None: self.link_current_task()
        if not self.timer_running:
            if self.remaining <= 0: self.on_change_mode()
            self.timer_running = True; self.timer_paused = False
            self.timer_started_at = datetime.now(); self._tick()
        elif self.timer_paused:
            self.timer_paused = False; self._tick()

    def on_pause_timer(self):
        if not self.timer_running: return
        self.timer_paused = True
        if self.timer_after_id: self.root.after_cancel(self.timer_after_id); self.timer_after_id = None

    def on_reset_timer(self):
        if self.timer_after_id: self.root.after_cancel(self.timer_after_id); self.timer_after_id = None
        self.timer_running = False; self.timer_paused = False; self.timer_started_at = None
        self.on_change_mode()

    def _tick(self):
        if not self.timer_running or self.timer_paused: return
        if self.remaining <= 0: self._handle_session_complete(); return
        self.remaining -= 1; self._update_timer_display()
        self.timer_after_id = self.root.after(1000, self._tick)

    # def _update_timer_display(self):
    #     m = max(self.remaining, 0) // 60; s = max(self.remaining, 0) % 60
    #     self.timer_display.set(f"{m:02d}:{s:02d}")

    def _update_timer_display(self):
        m = max(self.remaining, 0) // 60
        s = max(self.remaining, 0) % 60
        self.timer_display.set(f"{m:02d}:{s:02d}")
        # Update canvas timer text
        self.canvas.itemconfig(self.timer_text, text=f"{m:02d}:{s:02d}")
        # Update progress arc (clockwise)
        total = self._get_duration_seconds(self.timer_mode.get())
        if total > 0:
            progress = (1 - self.remaining / total) * 360
            self.canvas.itemconfig(self.arc, extent=-progress)  # negative = clockwise



    def _handle_session_complete(self):
        self.timer_running = False; self.timer_paused = False
        end_time = datetime.now()
        if self.timer_started_at and self.timer_mode.get() == "work":
            duration = int(round((end_time - self.timer_started_at).total_seconds() / 60.0))
            if duration > 0:
                try: log_focus_session(self.timer_link_task_id, self.timer_started_at, end_time, duration)
                except Exception as e: print("Focus session log failed:", e)
                self.refresh_stats()
        try: self.root.bell()
        except Exception: pass
        messagebox.showinfo("Session complete", "Time's up!")
        if self.timer_mode.get() == "work" and self.auto_start_break.get():
            self.timer_mode.set("break"); self.on_change_mode(); self.on_start_timer()
        else:
            self.on_change_mode()

def create_ui(root: tk.Tk):
    return App(root)


