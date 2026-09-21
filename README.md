# Speedcubing Session Analytics & Dashboard 🧩

An end-to-end analytics toolkit for speedcubing training sessions based on **[csTimer](https://cstimer.net/)** CSV exports.

Features a fully interactive, client-side **Web Dashboard** (hosted via GitHub Pages with zero installation required) alongside a standalone **Python CLI script** for terminal metrics and high-resolution chart exports.

[![GitHub Pages](https://img.shields.io/badge/Live_Demo-GitHub_Pages-2ea44f?style=flat-square&logo=github)](https://s4ymyn4mee.github.io/speedcubing_stats/)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Chart.js v4](https://img.shields.io/badge/Chart.js-v4.4-FF6384?style=flat-square&logo=chartdotjs&logoColor=white)](https://www.chartjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

---

## Live Web Dashboard

Try the dashboard directly in your browser:  
👉 **[Open Speedcubing Session Analyzer](https://s4ymyn4mee.github.io/speedcubing_stats/)**

---

## Features

### 1. Official WCA Trimmed Means
* **Accurate Rolling Averages:** Computes rolling **Ao5**, **Ao12**, **Ao100**, **Ao500**, and **Ao1000** following official WCA and csTimer specifications:
  * **Ao5 & Ao12:** Drops exactly 1 best and 1 worst attempt.
  * **Ao100, Ao500, Ao1000:** Truncates top and bottom 5% outliers rounded up ($\lceil 0.05 \times N \rceil$).
* **Robust DNF Handling:** A single DNF within a valid window counts as the worst solve. Exceeding the allowed DNF tolerance cleanly sets the average to `DNF` without corrupting dataset calculations.
* **Full Penalty Support:** Automatically parses `+2` penalties and minute-format timestamps (e.g., `1:05.20`).

### 2. Interactive Web Dashboard (`index.html`)
* **100% Client-Side & Privacy-First:** CSV files are processed purely in local browser memory via `PapaParse`. Zero data is transmitted to external servers.
* **PB Progression Milestones:**
  * Stepped progression timeline on a continuous linear scale.
  * 35px magnetic hit-radius around milestone points to guarantee effortless hovering and clicking on dense sessions (2000+ solves).
  * Points render unclipped (`clip: false`) with padded axes for clean edge visibility.
  * Interactive **Milestone Chips Ribbon** above the chart for instant one-click inspection of any historical record.
* **Solve Inspector:**
  * Displays timestamp, scramble notation, user comments, and penalty state.
  * One-click scramble clipboard copy.
  * Keyboard navigation with Arrow keys (`←` / `→`) and solve search by number.
  * Dynamic percentile tags: `🏆 Personal Best`, `⚡ Top 25% (Fast)`, `🐢 Bottom 25% (Slow)`, `⚠️ Worst Solve`.
* **Circadian Speed Analysis:**
  * Hourly speed distribution with a customizable sample-size threshold (`Min solves/hour`) to prevent single-solve hours from skewing the color gradient.
* **Dynamic Cutoff Filter:**
  * Synchronized slider and numeric input for instant real-time fail pruning and chart rescaling.
* **Dual Locale:**
  * One-click toggle between English (`EN`) and Russian (`RU`) persisted in `localStorage`.

### 3. Standalone Python CLI (`get_stat.py`)
* Fast vectorized sliding window calculations via NumPy and Pandas.
* Comprehensive summary statistics, gradient histogram distribution, and Ao trend overlays.
* Generates a clean, presentation-ready PNG image (`speedcubing_stats.png`).

---

## Getting Started

### Option 1: Web Dashboard (Local Usage)

The web dashboard requires zero build steps, bundlers, or Node.js runtime:

```bash
git clone [https://github.com/s4ymyn4mee/speedcubing_stats.git](https://github.com/s4ymyn4mee/speedcubing_stats.git)
cd speedcubing_stats

# Open directly in your browser
xdg-open index.html      # Linux
open index.html          # macOS
start index.html         # Windows

```

---

### Option 2: Python Script

```bash
# 1. Clone repository
git clone [https://github.com/s4ymyn4mee/speedcubing_stats.git](https://github.com/s4ymyn4mee/speedcubing_stats.git)
cd speedcubing_stats

# 2. Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install requirements
pip install -r requirements.txt

# 4. Run analysis
python3 get_stat.py

```

#### CLI Options:

```bash
# Run with custom cutoff threshold (e.g., exclude solves >= 20s):
python3 get_stat.py 20
# or
python3 get_stat.py --cutoff 20

# Run with a specific file and cutoff:
python3 get_stat.py my_session.csv 22

```

---

## 📥 Exporting Data from csTimer

1. Go to **[csTimer.net](https://cstimer.net)**.
2. Click **Export** in the top navigation menu.
3. Select **Export to file**.
4. Choose **CSV** format and save the file.
5. Drag and drop the `.csv` file into the web dashboard or place it in the project root as `times.csv` for the Python script.

---

## ⌨️ Inspector Hotkeys

| Key | Action |
| --- | --- |
| `←` (Left Arrow) | Navigate to previous solve |
| `→` (Right Arrow) | Navigate to next solve |
| `Enter` (inside search box) | Jump to solve number |

---

## 📊 Dashboard Preview

---

## 🛠️ Tech Stack

* **Frontend:** HTML5, Modern CSS3 (Custom Properties, Flexbox, CSS Grid), Vanilla JavaScript (ES6+).
* **Libraries:** [Chart.js v4](https://www.chartjs.org), [PapaParse](https://www.papaparse.com).
* **Python CLI:** Python 3.9+, NumPy, Pandas, Matplotlib, Seaborn.

---

## 📄 License

Distributed under the MIT License. See [LICENSE](https://www.google.com/search?q=LICENSE) for details.

