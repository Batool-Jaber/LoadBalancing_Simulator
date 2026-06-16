import tkinter as tk
from tkinter import ttk, messagebox
import random
import time
import csv
import os
from dataclasses import dataclass, field
from typing import List, Optional
from abc import ABC, abstractmethod

# ─────────────────────────────────────────────
#  COLORS & THEME
# ─────────────────────────────────────────────
BG_DARK      = "#0F1117"
BG_PANEL     = "#1A1D27"
BG_CARD      = "#22263A"
BG_CARD_ALT  = "#1E2235"
ACCENT_BLUE  = "#4F8EF7"
ACCENT_CYAN  = "#00D4FF"
ACCENT_GREEN = "#00E676"
ACCENT_GOLD  = "#FFD600"

TEXT_PRIMARY   = "#EAEAF0"
TEXT_SECONDARY = "#8A8FAD"
TEXT_DIM       = "#4A4F6A"

CLR_GREEN  = "#00C853"
CLR_YELLOW = "#FFD600"
CLR_ORANGE = "#FF6D00"
CLR_RED    = "#F44336"

ALGO_COLORS = {
    "Round Robin":      "#4F8EF7",
    "Central Manager":  "#00E676",
    "Random":           "#FF6B6B",
}

FONT_TITLE  = ("Consolas", 18, "bold")
FONT_HEAD   = ("Consolas", 11, "bold")
FONT_BODY   = ("Consolas", 10)
FONT_SMALL  = ("Consolas", 9)
FONT_MONO   = ("Courier New", 9)

# ─────────────────────────────────────────────
#  DATA CLASSES
# ─────────────────────────────────────────────
@dataclass
class Task:
    id: int
    weight: int          # 1–5  (simulates task heaviness)

    def __str__(self):
        return f"T{self.id:02d}(w={self.weight})"


@dataclass
class Server:
    id: int
    name: str
    capacity: int = 10
    current_load: int = 0
    tasks_assigned: List[int] = field(default_factory=list)

    def reset(self):
        self.current_load = 0
        self.tasks_assigned = []

    def assign(self, task: Task):
        self.current_load += task.weight
        self.tasks_assigned.append(task.id)

    @property
    def load_ratio(self) -> float:
        if self.capacity == 0:
            return 0.0
        return min(self.current_load / (self.capacity * 3), 1.0)

    @property
    def load_color(self) -> str:
        r = self.load_ratio
        if r < 0.4:
            return CLR_GREEN
        elif r < 0.65:
            return CLR_YELLOW
        elif r < 0.85:
            return CLR_ORANGE
        return CLR_RED

    @property
    def load_label(self) -> str:
        r = self.load_ratio
        if r < 0.4:   return "LIGHT"
        elif r < 0.65: return "MEDIUM"
        elif r < 0.85: return "HEAVY"
        return "CRITICAL"


# ─────────────────────────────────────────────
#  LOAD BALANCER ALGORITHMS
# ─────────────────────────────────────────────
class LoadBalancer(ABC):
    def __init__(self, servers: List[Server]):
        self.servers = servers

    @abstractmethod
    def assign(self, task: Task) -> (Server, str):
        """Returns (chosen_server, reason_string)"""
        pass

    def name(self) -> str:
        return self.__class__.__name__


class RoundRobinBalancer(LoadBalancer):
    def __init__(self, servers):
        super().__init__(servers)
        self._index = 0

    def assign(self, task: Task) -> (Server, str):
        server = self.servers[self._index % len(self.servers)]
        reason = f"Round Robin → turn #{self._index + 1} → {server.name}"
        self._index += 1
        server.assign(task)
        return server, reason

    def name(self): return "Round Robin"


class CentralManagerBalancer(LoadBalancer):
    def assign(self, task: Task) -> (Server, str):
        target = min(self.servers, key=lambda s: s.current_load)
        reason = (f"Central Manager → scanned all servers → "
                  f"{target.name} has lowest load ({target.current_load})")
        target.assign(task)
        return target, reason

    def name(self): return "Central Manager"


class RandomBalancer(LoadBalancer):
    def assign(self, task: Task) -> (Server, str):
        target = random.choice(self.servers)
        reason = f"Random → no logic → picked {target.name} by chance"
        target.assign(task)
        return target, reason

    def name(self): return "Random"


# ─────────────────────────────────────────────
#  STATISTICS
# ─────────────────────────────────────────────
def compute_stats(servers: List[Server]) -> dict:
    loads = [s.current_load for s in servers]
    if not loads:
        return {}
    avg  = sum(loads) / len(loads)
    mx   = max(loads)
    mn   = min(loads)
    var  = sum((l - avg) ** 2 for l in loads) / len(loads)
    most = max(servers, key=lambda s: s.current_load)
    return {
        "max_load":        mx,
        "min_load":        mn,
        "avg_load":        round(avg, 2),
        "variance":        round(var, 2),
        "most_overloaded": most.name,
        "loads":           loads,
    }


# ─────────────────────────────────────────────
#  SERVER CARD WIDGET
# ─────────────────────────────────────────────
class ServerCard(tk.Frame):
    CARD_W = 160
    CARD_H = 130

    def __init__(self, parent, server: Server, **kwargs):
        super().__init__(parent, bg=BG_CARD,
                         width=self.CARD_W, height=self.CARD_H,
                         bd=0, highlightthickness=2,
                         highlightbackground=TEXT_DIM,
                         highlightcolor=ACCENT_BLUE, **kwargs)
        self.pack_propagate(False)
        self.server = server
        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=BG_CARD_ALT, height=28)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        self._name_lbl = tk.Label(hdr, text=self.server.name,
                                   font=FONT_HEAD,
                                   bg=BG_CARD_ALT, fg=ACCENT_CYAN)
        self._name_lbl.pack(side="left", padx=8, pady=4)

        self._status_lbl = tk.Label(hdr, text="IDLE",
                                     font=("Consolas", 7, "bold"),
                                     bg=BG_CARD_ALT, fg=CLR_GREEN)
        self._status_lbl.pack(side="right", padx=6)

        # Load bar background
        bar_frame = tk.Frame(self, bg=BG_CARD, pady=6)
        bar_frame.pack(fill="x", padx=10)

        self._bar_bg = tk.Canvas(bar_frame, height=14,
                                  bg=BG_DARK, bd=0,
                                  highlightthickness=0)
        self._bar_bg.pack(fill="x")
        self._bar_fill = self._bar_bg.create_rectangle(
            0, 0, 0, 14, fill=CLR_GREEN, outline="")

        # Stats
        stats = tk.Frame(self, bg=BG_CARD)
        stats.pack(fill="x", padx=10)

        self._load_lbl = tk.Label(stats, text="Load: 0",
                                   font=FONT_SMALL,
                                   bg=BG_CARD, fg=TEXT_PRIMARY)
        self._load_lbl.pack(anchor="w")

        self._tasks_lbl = tk.Label(stats, text="Tasks: 0",
                                    font=FONT_SMALL,
                                    bg=BG_CARD, fg=TEXT_SECONDARY)
        self._tasks_lbl.pack(anchor="w")

        # Flash label
        self._flash_lbl = tk.Label(self, text="",
                                    font=("Consolas", 8, "bold"),
                                    bg=BG_CARD, fg=ACCENT_GOLD)
        self._flash_lbl.pack(pady=(2, 0))

    def refresh(self):
        s = self.server
        color = s.load_color
        label = s.load_label

        self._status_lbl.config(text=label, fg=color)
        self._load_lbl.config(
            text=f"Load:  {s.current_load}",
            fg=color)
        self._tasks_lbl.config(
            text=f"Tasks: {len(s.tasks_assigned)}",
            fg=TEXT_SECONDARY)

        # Update bar
        w = self._bar_bg.winfo_width()
        if w < 2:
            w = self.CARD_W - 20
        filled = int(w * s.load_ratio)
        self._bar_bg.coords(self._bar_fill, 0, 0, filled, 14)
        self._bar_bg.itemconfig(self._bar_fill, fill=color)

        # Border glow
        self.config(highlightbackground=color if s.current_load > 0 else TEXT_DIM)

    def flash(self, task: Task):
        self._flash_lbl.config(text=f"◀ {task}", fg=ACCENT_GOLD)
        self.config(highlightbackground=ACCENT_GOLD)
        self.after(600, self._unflash)

    def _unflash(self):
        self._flash_lbl.config(text="")
        self.refresh()

    def reset_display(self):
        self._status_lbl.config(text="IDLE", fg=CLR_GREEN)
        self._load_lbl.config(text="Load: 0", fg=TEXT_PRIMARY)
        self._tasks_lbl.config(text="Tasks: 0", fg=TEXT_SECONDARY)
        self._flash_lbl.config(text="")
        self._bar_bg.coords(self._bar_fill, 0, 0, 0, 14)
        self.config(highlightbackground=TEXT_DIM)


# ─────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────
class SimulatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Load Balancing Simulator — Distributed Systems")
        self.geometry("1280x720")
        self.minsize(1100, 680)
        self.configure(bg=BG_DARK)
        self.resizable(True, True)

        # State
        self._seed       = random.randint(0, 99999)
        self._tasks: List[Task]   = []
        self._servers: List[Server] = []
        self._cards: List[ServerCard] = []
        self._results: dict = {}          # algo_name → stats dict
        self._running    = False
        self._after_id   = None

        self._build_ui()
        self._generate_tasks()

    # ── UI BUILD ───────────────────────────────
    def _build_ui(self):
        # ── TITLE BAR ──
        title_bar = tk.Frame(self, bg=BG_PANEL, height=50)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)

        tk.Label(title_bar,
                 text="⚡ LOAD BALANCING SIMULATOR",
                 font=FONT_TITLE,
                 bg=BG_PANEL, fg=ACCENT_CYAN).pack(side="left", padx=20, pady=10)

        tk.Label(title_bar,
                 text="Distributed Systems — Algorithm Comparison",
                 font=FONT_SMALL,
                 bg=BG_PANEL, fg=TEXT_SECONDARY).pack(side="left", padx=5, pady=18)

        # ── CONTROL PANEL ──
        ctrl = tk.Frame(self, bg=BG_PANEL, height=70)
        ctrl.pack(fill="x", pady=(2, 0))
        ctrl.pack_propagate(False)

        # Sliders
        sl_frame = tk.Frame(ctrl, bg=BG_PANEL)
        sl_frame.pack(side="left", padx=20, pady=10)

        tk.Label(sl_frame, text="Servers", font=FONT_SMALL,
                 bg=BG_PANEL, fg=TEXT_SECONDARY).grid(row=0, column=0, padx=(0,4))
        self._srv_var = tk.IntVar(value=4)
        self._srv_slider = tk.Scale(sl_frame, from_=3, to=6,
                                     orient="horizontal", length=100,
                                     variable=self._srv_var,
                                     bg=BG_PANEL, fg=TEXT_PRIMARY,
                                     troughcolor=BG_DARK,
                                     highlightthickness=0,
                                     activebackground=ACCENT_BLUE,
                                     command=lambda _: self._on_config_change())
        self._srv_slider.grid(row=0, column=1)

        tk.Label(sl_frame, text="Tasks", font=FONT_SMALL,
                 bg=BG_PANEL, fg=TEXT_SECONDARY).grid(row=0, column=2, padx=(16,4))
        self._tsk_var = tk.IntVar(value=10)
        self._tsk_slider = tk.Scale(sl_frame, from_=5, to=20,
                                     orient="horizontal", length=100,
                                     variable=self._tsk_var,
                                     bg=BG_PANEL, fg=TEXT_PRIMARY,
                                     troughcolor=BG_DARK,
                                     highlightthickness=0,
                                     activebackground=ACCENT_BLUE,
                                     command=lambda _: self._on_config_change())
        self._tsk_slider.grid(row=0, column=3)



        # Algo buttons
        btn_frame = tk.Frame(ctrl, bg=BG_PANEL)
        btn_frame.pack(side="left", padx=30, pady=12)

        algo_defs = [
            ("Round Robin",     "Sequential rotation — ignores server load",
             lambda: self._run_algo("Round Robin")),
            ("Central Manager", "Assigns to least loaded server",
             lambda: self._run_algo("Central Manager")),
            ("Random",          "Random selection — no intelligence",
             lambda: self._run_algo("Random")),
        ]
        self._algo_btns = []
        for label, tip, cmd in algo_defs:
            col = ALGO_COLORS[label]
            btn = tk.Button(btn_frame, text=label,
                            font=FONT_HEAD, width=16,
                            bg=BG_CARD, fg=col,
                            activebackground=col,
                            activeforeground=BG_DARK,
                            bd=0, relief="flat",
                            cursor="hand2",
                            command=cmd)
            btn.pack(side="left", padx=6)
            self._create_tooltip(btn, tip)
            self._algo_btns.append(btn)

        # Right buttons
        right_frame = tk.Frame(ctrl, bg=BG_PANEL)
        right_frame.pack(side="right", padx=20, pady=12)

        tk.Button(right_frame, text="↺  New Simulation",
                  font=FONT_HEAD,
                  bg="#2A1F4A", fg=ACCENT_GOLD,
                  activebackground=ACCENT_GOLD, activeforeground=BG_DARK,
                  bd=0, relief="flat", cursor="hand2",
                  command=self._new_simulation).pack(side="left", padx=6)


        # ── MAIN BODY ──
        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=8, pady=4)

        # Left: servers + queue
        left_col = tk.Frame(body, bg=BG_DARK)
        left_col.pack(side="left", fill="both", expand=True)

        # Server area label
        srv_hdr = tk.Frame(left_col, bg=BG_DARK)
        srv_hdr.pack(fill="x", padx=4)
        tk.Label(srv_hdr, text="▌ SERVER POOL",
                 font=FONT_HEAD, bg=BG_DARK, fg=ACCENT_BLUE).pack(side="left")
        self._algo_label = tk.Label(srv_hdr, text="",
                                     font=FONT_HEAD, bg=BG_DARK, fg=ACCENT_CYAN)
        self._algo_label.pack(side="left", padx=12)

        # Server cards container
        self._cards_frame = tk.Frame(left_col, bg=BG_DARK)
        self._cards_frame.pack(fill="x", padx=4, pady=4)

        # Task queue
        q_frame = tk.Frame(left_col, bg=BG_PANEL, bd=0)
        q_frame.pack(fill="x", padx=4, pady=(4,2))
        tk.Label(q_frame, text="▌ TASK QUEUE",
                 font=FONT_HEAD, bg=BG_PANEL, fg=ACCENT_BLUE).pack(anchor="w", padx=8, pady=4)
        self._queue_canvas = tk.Canvas(q_frame, bg=BG_PANEL,
                                        height=50, highlightthickness=0)
        self._queue_canvas.pack(fill="x", padx=8, pady=(0,6))

        # Summary line
        self._summary_lbl = tk.Label(left_col, text="",
                                      font=("Consolas", 10, "bold"),
                                      bg=BG_DARK, fg=ACCENT_GOLD,
                                      wraplength=700, justify="left")
        self._summary_lbl.pack(anchor="w", padx=8, pady=2)

        # Bar chart
        chart_lbl_frame = tk.Frame(left_col, bg=BG_DARK)
        chart_lbl_frame.pack(fill="x", padx=4)
        tk.Label(chart_lbl_frame, text="▌ LOAD DISTRIBUTION CHART",
                 font=FONT_HEAD, bg=BG_DARK, fg=ACCENT_BLUE).pack(side="left")

        self._last_chart_servers = []
        self._last_chart_algo    = ""

        self._chart_canvas = tk.Canvas(left_col, bg=BG_PANEL,
                                        height=100, highlightthickness=0)
        self._chart_canvas.pack(fill="x", padx=4, pady=2)

        # Comparison table
        tbl_frame = tk.Frame(left_col, bg=BG_DARK)
        tbl_frame.pack(fill="x", padx=4, pady=4)
        tk.Label(tbl_frame, text="▌ COMPARISON TABLE",
                 font=FONT_HEAD, bg=BG_DARK, fg=ACCENT_BLUE).pack(anchor="w")
        self._build_table(tbl_frame)

        # Right: decision log
        log_col = tk.Frame(body, bg=BG_PANEL, width=330)
        log_col.pack(side="right", fill="y", padx=(4,4))
        log_col.pack_propagate(False)

        tk.Label(log_col, text="▌ DECISION LOG",
                 font=FONT_HEAD, bg=BG_PANEL, fg=ACCENT_BLUE).pack(anchor="w", padx=8, pady=6)

        log_inner = tk.Frame(log_col, bg=BG_PANEL)
        log_inner.pack(fill="both", expand=True, padx=4)

        scrollbar = tk.Scrollbar(log_inner, bg=BG_DARK, troughcolor=BG_DARK)
        scrollbar.pack(side="right", fill="y")

        self._log_text = tk.Text(log_inner, bg=BG_PANEL,
                                  fg=TEXT_PRIMARY,
                                  font=FONT_MONO,
                                  wrap="word",
                                  bd=0, relief="flat",
                                  state="disabled",
                                  yscrollcommand=scrollbar.set,
                                  insertbackground=ACCENT_CYAN)
        self._log_text.pack(fill="both", expand=True)
        scrollbar.config(command=self._log_text.yview)

        # Tag colors for log
        self._log_text.tag_config("header",  foreground=ACCENT_CYAN,  font=("Consolas",10,"bold"))
        self._log_text.tag_config("assign",  foreground=TEXT_PRIMARY)
        self._log_text.tag_config("server",  foreground=ACCENT_GREEN)
        self._log_text.tag_config("reason",  foreground=TEXT_SECONDARY, font=FONT_MONO)
        self._log_text.tag_config("done",    foreground=ACCENT_GOLD,   font=("Consolas",9,"bold"))
        self._log_text.tag_config("rr",      foreground=ALGO_COLORS["Round Robin"])
        self._log_text.tag_config("cm",      foreground=ALGO_COLORS["Central Manager"])
        self._log_text.tag_config("rnd",     foreground=ALGO_COLORS["Random"])

        # Build initial servers
        self._rebuild_servers()

    def _build_table(self, parent):
        cols = ["Algorithm", "Max Load", "Avg Load", "Variance", "Most Overloaded"]
        self._tbl_frame = tk.Frame(parent, bg=BG_PANEL)
        self._tbl_frame.pack(fill="x", pady=2)

        # Header row
        for c, col in enumerate(cols):
            tk.Label(self._tbl_frame, text=col,
                     font=("Consolas", 9, "bold"),
                     bg=BG_CARD_ALT, fg=TEXT_SECONDARY,
                     padx=8, pady=4, anchor="w",
                     relief="flat").grid(row=0, column=c,
                                         sticky="ew", padx=1, pady=1)
            self._tbl_frame.columnconfigure(c, weight=1)

        # Data rows (3 algos)
        self._tbl_cells = {}
        algo_names = ["Round Robin", "Central Manager", "Random"]
        for r, aname in enumerate(algo_names, start=1):
            color = ALGO_COLORS[aname]
            tk.Label(self._tbl_frame, text=aname,
                     font=("Consolas", 9, "bold"),
                     bg=BG_CARD, fg=color,
                     padx=8, pady=4, anchor="w").grid(
                row=r, column=0, sticky="ew", padx=1, pady=1)

            row_cells = []
            for c in range(1, len(cols)):
                lbl = tk.Label(self._tbl_frame, text="—",
                               font=FONT_MONO,
                               bg=BG_CARD, fg=TEXT_DIM,
                               padx=8, pady=4, anchor="w")
                lbl.grid(row=r, column=c, sticky="ew", padx=1, pady=1)
                row_cells.append(lbl)
            self._tbl_cells[aname] = row_cells

    # ── SERVER MANAGEMENT ──────────────────────
    def _rebuild_servers(self):
        for w in self._cards_frame.winfo_children():
            w.destroy()
        self._cards = []
        self._servers = []
        n = self._srv_var.get()
        for i in range(n):
            s = Server(id=i+1, name=f"SRV-{i+1}")
            self._servers.append(s)
            card = ServerCard(self._cards_frame, s)
            card.pack(side="left", padx=6, pady=4)
            self._cards.append(card)

    def _reset_servers(self):
        for s in self._servers:
            s.reset()
        for card in self._cards:
            card.reset_display()

    def _on_config_change(self):
        if self._running:
            return
        self._rebuild_servers()
        self._generate_tasks()
        self._summary_lbl.config(text="")
        self._clear_chart()

    # ── TASK GENERATION ────────────────────────
    def _generate_tasks(self):
        random.seed(self._seed)
        n = self._tsk_var.get()
        self._tasks = [Task(id=i+1, weight=random.randint(1, 5))
                       for i in range(n)]
        self._draw_queue(self._tasks)

    def _draw_queue(self, tasks: List[Task]):
        c = self._queue_canvas
        c.delete("all")
        x = 6
        for t in tasks:

            max_w = 5
            ratio = (t.weight - 1) / max(max_w - 1, 1)
            if ratio < 0.25:   col, fg = "#1a4a2e", CLR_GREEN
            elif ratio < 0.5:  col, fg = "#2a4a1a", "#8BC34A"
            elif ratio < 0.75: col, fg = "#4a3a0a", CLR_YELLOW
            elif ratio < 0.9:  col, fg = "#4a2a0a", CLR_ORANGE
            else:               col, fg = "#4a0a0a", CLR_RED
            c.create_rectangle(x, 8, x+44, 42, fill=col, outline=fg, width=1)
            c.create_text(x+22, 22, text=f"T{t.id:02d}", fill=fg,
                          font=("Consolas",8,"bold"))
            c.create_text(x+22, 34, text=f"w={t.weight}", fill=TEXT_DIM,
                          font=("Consolas",7))
            x += 50
            if x > 1200:
                break

    def _remove_from_queue(self, task_idx: int):
        """Grey out the task at position task_idx in the queue."""
        c = self._queue_canvas
        x = 6 + task_idx * 50
        c.create_rectangle(x, 8, x+44, 42, fill=BG_DARK, outline=TEXT_DIM, width=1)
        c.create_text(x+22, 25, text="✓", fill=TEXT_DIM,
                      font=("Consolas",12,"bold"))

    # ── ALGORITHM RUNNER ───────────────────────
    def _run_algo(self, algo_name: str):
        if self._running:
            return
        self._running = True
        self._set_buttons_state("disabled")

        # Reset servers visually
        self._reset_servers()
        self._draw_queue(self._tasks)
        self._summary_lbl.config(text="")
        self._clear_chart()
        self._algo_label.config(text=f"[ {algo_name} ]",
                                 fg=ALGO_COLORS[algo_name])

        # Build fresh servers for this run (same names)
        run_servers = [Server(id=s.id, name=s.name) for s in self._servers]
        # Map name → card
        card_map = {card.server.name: card for card in self._cards}

        # Create balancer
        random.seed(self._seed)
        if algo_name == "Round Robin":
            balancer = RoundRobinBalancer(run_servers)
            tag = "rr"
        elif algo_name == "Central Manager":
            balancer = CentralManagerBalancer(run_servers)
            tag = "cm"
        else:
            balancer = RandomBalancer(run_servers)
            tag = "rnd"

        # Log header
        self._log_clear()
        self._log_append(f"\n{'─'*36}\n", "reason")
        self._log_append(f" ▶ {algo_name}\n", tag)
        self._log_append(f" Tasks: {len(self._tasks)}  Servers: {len(run_servers)}\n", "reason")
        self._log_append(f"{'─'*36}\n", "reason")

        # Animation loop
        delay = 700  # ثابت 700 مللي ثانية بين كل مهمة

        def step(idx):
            if idx >= len(self._tasks):
                # Done
                stats = compute_stats(run_servers)
                self._results[algo_name] = stats
                self._log_append(f"\n✔ Done — Variance: {stats['variance']}\n", "done")
                self._update_table(algo_name, stats)
                self._draw_chart(run_servers, algo_name)
                self._show_summary(algo_name, stats)
                self._running = False
                self._set_buttons_state("normal")
                return

            task = self._tasks[idx]
            server, reason = balancer.assign(task)

            # Update card
            # Sync card's server object
            card = card_map[server.name]
            card.server.current_load = server.current_load
            card.server.tasks_assigned = list(server.tasks_assigned)
            card.refresh()
            card.flash(task)

            # Grey out queue
            self._remove_from_queue(idx)

            # Log
            self._log_append(f"\n Task {task.id:02d} (w={task.weight})\n", "assign")
            self._log_append(f"  → {server.name}\n", "server")
            short = reason.split("→")[-1].strip()
            self._log_append(f"  {short}\n", "reason")

            self._after_id = self.after(delay, lambda: step(idx + 1))

        step(0)

    # ── TABLE UPDATE ───────────────────────────
    def _update_table(self, algo_name: str, stats: dict):
        cells = self._tbl_cells[algo_name]
        cells[0].config(text=str(stats["max_load"]),  fg=TEXT_PRIMARY)
        cells[1].config(text=str(stats["avg_load"]),  fg=TEXT_PRIMARY)
        cells[2].config(text=str(stats["variance"]),  fg=TEXT_PRIMARY)
        cells[3].config(text=stats["most_overloaded"], fg=TEXT_PRIMARY)

        # Highlight best variance across completed algos
        if len(self._results) >= 2:
            best_algo = min(self._results, key=lambda a: self._results[a]["variance"])
            for aname, row in self._tbl_cells.items():
                if aname in self._results:
                    highlight = (aname == best_algo)
                    bg = "#162616" if highlight else BG_CARD
                    fg = ACCENT_GREEN if highlight else TEXT_PRIMARY
                    for cell in row:
                        cell.config(bg=bg, fg=fg)

    # ── CHART ──────────────────────────────────
    def _clear_chart(self):
        self._chart_canvas.delete("all")
        self._last_chart_servers = []
        self._last_chart_algo    = ""

    def _draw_chart(self, servers: List[Server], algo_name: str):
        self._last_chart_servers = servers
        self._last_chart_algo    = algo_name

        c = self._chart_canvas
        c.delete("all")
        self.update_idletasks()
        W = c.winfo_width()
        H = c.winfo_height()
        if W < 10: W = 800
        if H < 10: H = 100

        color = ALGO_COLORS[algo_name]
        max_l = max((s.current_load for s in servers), default=1) or 1
        n     = len(servers)
        pad   = 30
        bar_w = max(20, (W - 2*pad) // n - 8)

        for i, s in enumerate(servers):
            x     = pad + i * ((W - 2*pad) // n) + 4
            bar_h = int((s.current_load / max_l) * (H - 30))
            y0    = H - 20 - bar_h
            y1    = H - 20
            c.create_rectangle(x, y0, x+bar_w, y1, fill=color, outline="")
            c.create_text(x + bar_w//2, y0 - 7,
                          text=str(s.current_load),
                          fill=TEXT_PRIMARY, font=("Consolas",8,"bold"))
            c.create_text(x + bar_w//2, H - 8,
                          text=s.name.replace("SRV-","S"),
                          fill=TEXT_SECONDARY, font=("Consolas",7))

    # ── SUMMARY ────────────────────────────────
    def _show_summary(self, algo_name: str, stats: dict):
        var = stats["variance"]
        if var < 2:
            quality = "✦ Excellent — highly balanced distribution"
        elif var < 6:
            quality = "◈ Good — reasonably balanced"
        elif var < 12:
            quality = "▲ Fair — noticeable imbalance"
        else:
            quality = "✖ Poor — significant overloading on some servers"

        self._summary_lbl.config(
            text=f"{algo_name}  |  Variance: {var}  |  {quality}",
            fg=ALGO_COLORS[algo_name])

    # ── LOG HELPERS ────────────────────────────
    def _log_clear(self):
        self._log_text.config(state="normal")
        self._log_text.delete("1.0", "end")
        self._log_text.config(state="disabled")

    def _log_append(self, text: str, tag: str = "assign"):
        self._log_text.config(state="normal")
        self._log_text.insert("end", text, tag)
        self._log_text.see("end")
        self._log_text.config(state="disabled")

    # ── NEW SIMULATION ─────────────────────────
    def _new_simulation(self):
        if self._running:
            if self._after_id:
                self.after_cancel(self._after_id)
            self._running = False

        self._seed = random.randint(0, 99999)
        self._results = {}
        self._rebuild_servers()
        self._generate_tasks()
        self._summary_lbl.config(text="")
        self._clear_chart()
        self._log_clear()
        self._algo_label.config(text="")

        # Reset table
        for row in self._tbl_cells.values():
            for cell in row:
                cell.config(text="—", fg=TEXT_DIM, bg=BG_CARD)

        self._set_buttons_state("normal")
        self._log_append("New simulation ready.\nChoose an algorithm to start.\n", "reason")

    # ── EXPORT ─────────────────────────────────


    # ── HELPERS ────────────────────────────────
    def _set_buttons_state(self, state: str):
        for btn in self._algo_btns:
            btn.config(state=state)

    def _create_tooltip(self, widget, text: str):
        tip = None

        def show(event):
            nonlocal tip
            tip = tk.Toplevel(widget)
            tip.wm_overrideredirect(True)
            tip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            tk.Label(tip, text=text,
                     font=FONT_SMALL,
                     bg="#2A2E44", fg=TEXT_PRIMARY,
                     padx=8, pady=4,
                     relief="flat", bd=0).pack()

        def hide(event):
            nonlocal tip
            if tip:
                tip.destroy()
                tip = None

        widget.bind("<Enter>", show)
        widget.bind("<Leave>", hide)


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = SimulatorApp()
    app.mainloop()