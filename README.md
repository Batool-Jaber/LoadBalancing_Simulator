# LoadBalancing_Simulator
A visual, interactive Python GUI application that simulates and compares three load balancing algorithms in real time — built for a Distributed Systems university project.

---

## Project Overview

This simulator demonstrates how different load balancing algorithms distribute tasks across multiple servers. The user can watch the assignment process step by step, see server loads change in real time, and compare algorithm performance through a results table and bar chart.

The goal is to make the difference between algorithms **visible** — not just theoretical.

---

## Features

- 🎯 **Three algorithms** — Round Robin, Central Manager, Random
- 🎬 **Animated task assignment** — tasks appear one by one with a 700ms delay
- 🎨 **Color-coded server cards** — Green → Yellow → Orange → Red based on load
- 📋 **Real-time decision log** — every assignment is logged with its reason
- 📊 **Bar chart** — shows final load distribution per server after each run
- 📈 **Comparison table** — Max Load, Avg Load, Variance, Most Overloaded Server
- 🏆 **Automatic winner highlight** — best algorithm highlighted in green
- 🔁 **Fair comparison** — all algorithms run on the exact same task set (same random seed)
- ⚙️ **Configurable** — control number of servers (3–6) and tasks (5–20) via sliders
- 🔄 **Reset button** — generates a completely new random task set

---

## Algorithms Explained

### 1. Round Robin 🔵
Assigns tasks in a fixed sequential rotation — Server 1, Server 2, Server 3, then back to Server 1.

- ✅ Simple and predictable
- ✅ No overhead — no need to check server state
- ❌ Completely ignores current server load
- ❌ Unfair when tasks have different weights

### 2. Central Manager 🟢 *(Least Loaded)*
The manager scans all servers and always picks the one with the lowest current load.

- ✅ Most balanced distribution
- ✅ Adapts to task weight differences
- ✅ Lowest variance in results
- ❌ Single point of failure — if the manager crashes, the system stops
- ❌ O(n) scan on every assignment — slow for very large server pools

### 3. Random 🔴
Picks a server at random with no logic or awareness of load.

- ✅ Zero overhead
- ✅ Useful as a baseline comparison
- ❌ Unpredictable — can severely overload some servers
- ❌ Highest variance — worst distribution on average

---
## How to Run

### Requirements
- Python 3.x (tested on Python 3.13)
- No external libraries needed — everything uses Python's standard library

### Run
```bash
python load_balancer_simulator.py
```

### On Windows
```
Double-click load_balancer_simulator.py
— or —
Open terminal in project folder → python load_balancer_simulator.py
```

---

## How to Use

1. **Set servers** — use the Servers slider (3 to 6)
2. **Set tasks** — use the Tasks slider (5 to 20)
3. **Click an algorithm button** — Round Robin, Central Manager, or Random
4. **Watch** — tasks are assigned one by one with animation
5. **Read the log** — every decision is explained on the right panel
6. **Check results** — comparison table and bar chart appear automatically
7. **Compare** — click a different algorithm to rerun with the same tasks
8. **Reset** — click "New Simulation" to generate a fresh task set

---
## 📚 Libraries Used

| Library | Purpose | External? |
|---------|---------|-----------|
| `tkinter` | GUI — window, buttons, canvas, sliders | ✅ Built-in |
| `random` | Generate random tasks, Random algorithm | ✅ Built-in |
| `dataclasses` | Simplify Task and Server class definitions | ✅ Built-in |
| `abc` | Abstract base class for LoadBalancer | ✅ Built-in |
| `typing` | Type hints (List, Optional) for clarity | ✅ Built-in |
| `time` | Imported as backup — animation uses `after()` | ✅ Built-in |
| `os` | Imported as legacy — not actively used | ✅ Built-in |

> **No pip install required.** The project runs on a clean Python installation.
