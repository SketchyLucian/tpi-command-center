# True Priority Index (TPI) Command Center

> A research-grounded task prioritization, altitude architecture, and cognitive habit analytics system built with Python and [Flet](https://flet.dev) (Flutter).

Designed strictly in accordance with academic and empirical methodologies detailed in [Task Prioritization and Evaluation Systems](doc/Task%20Prioritization%20and%20Evaluation%20Systems.pdf).

---

## Key Methodologies & Architectural Foundations

1. **Altitude Architecture (GTD Horizons 1–5 & Ray Dalio 5-Step Process)**
   - **Horizons 4–5 (3–5 Year Vision)**: High-altitude guiding compass.
   - **Horizon 3 (Top 5 Strategic Goals)**: Warren Buffett 25/5 rule ensures only the Top 5 goals receive cognitive capacity; Goals 6–25 are quarantined in the Avoid-at-All-Costs list.
   - **Horizon 2 (Daily Autopilot Maintenance)**: Non-negotiable habits maintaining baseline executive function.
   - **Horizon 1 (Active Projects & Next Actions)**: Ground-level task queue scored and ranked dynamically.

2. **Gate 0 Binary Screening & WSJF Scoring Engine**
   - **Filter 0**: Routine guardrails, 2-Minute Rule (David Allen), and Budget Locks.
   - **Weighted Shortest Job First (WSJF)**:
     $$\text{TPI Score} = \frac{(W_1 \cdot \text{Why}) + (W_2 \cdot \text{Value}) + (W_3 \cdot \text{Urgency}) + (W_4 \cdot \text{Leverage})}{\text{Fibonacci Duration}}$$
   - Pre-fixed weights ($W_1$ to $W_4$) prevent impulsive mid-week priority shifting.

3. **Diurnal Attention Hygiene & Evening Habit Review (Gloria Mark & Baumeister)**
   - Eliminates mid-day context fragmentation and 23-minute task recovery penalties.
   - Fixed daily habits are batched into an **End-of-Day Review** with customizable native Windows Desktop Toast reminders (default `21:00`).

4. **Horizon 2 Habit Analytics & Cognitive Diagnostics**
   - 7 / 14 / 30-day interactive completion trend column bar charts with color-coded compliance tiers.
   - 28-Day Consistency Heatmap matrix.
   - Morning Anchor vs. Evening habit comparison tracking diurnal willpower fatigue.
   - **Strategic Withdrawal Alerts** (*Research Doc p. 19*): Proactively diagnoses routines slipping below 50% adherence for 2-week strategic withdrawal or atomic downsizing.

5. **Two-Way Door Architecture & Checkpoint Vault (Jeff Bezos Safeguards)**
   - **Type 1 Decisions (One-Way Doors)**: Irreversible data deletion requires explicit safety checks and commits automatic checkpoints to the branching **History Tree**.
   - **Type 2 Decisions (Two-Way Doors)**: Multi-level undo/redo (`Ctrl+Z` / `Ctrl+Y`) with non-intrusive auto-dismissing toast notifications.
   - **Branching Time-Travel**: Interactive History Tree dialog to audit timeline nodes and roll back full workspace states seamlessly.

6. **Reference Class Forecasting (RCF - Kahneman & Tversky)**
   - Mitigates the Planning Fallacy by archiving historical completion records (estimated Fibonacci vs. actual duration) to calibrate future task sizing.

---

## Installation & Setup

### Prerequisites
- Python 3.10+
- Windows 10/11 (for native Windows Toast notifications)

### Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Usage

### 1. Modern Desktop GUI (Flet / Flutter)
Launch the full desktop command center:
```bash
python main.py
```

#### Navigation:
* **Dashboard (Tab 0)**: View 3–5 year vision, active criteria weights, #1 Frog task (Mark Twain), and today's execution plan.
* **Add Tasks (Tab 1)**: Gate 0 binary screening and WSJF multi-criteria evaluation.
* **Review (Tab 2)**: Weekly review triage and budget vault unlocks.
* **Foundation (Tab 3)**: Manage top-down vision, Top 5 goals, active projects, and daily autopilot routines.
* **Analytics (Tab 4)**: 30-day habit trends, consistency heatmaps, attention metrics, notification schedule, and quick test data purge controls.
* **Memory (Tab 5)**: Audit and manage the Waiting Vault, Buffett 25/5 Avoid List, McKeown 90% Dropped List, RCF Task History, and Daily Habit Logs.
* **Weights (Tab 6)**: Configure or balance $W_1$–$W_4$ WSJF scoring weights.

### 2. Terminal CLI Mode
A terminal CLI interface is also available:
```bash
python tpi_evaluator.py
```

---

## Data Management & Safeguards

All application data is persistently saved in `tpi_workspace.json` with micro-backups in `tpi_history_tree.json`.
- **Purge Past Test Data**: One-click purge of seeded test records while preserving today's live state.
- **Audit & Single-Date Deletion**: Edit or delete specific date reviews from the Analytics tab, Memory tab, or top-bar Data Manager.
- **Safety Rollback**: Every deletion automatically records a `TYPE 1 SAFEGUARD` checkpoint and provides instantaneous `Ctrl+Z` undo support.

---

## Research Reference
* **Document**: [`doc/Task Prioritization and Evaluation Systems.pdf`](doc/Task%20Prioritization%20and%20Evaluation%20Systems.pdf)
* **Topics**: Altitude Architecture, Attention Hygiene, Diurnal Willpower, Gate 0 Filtering, WSJF, Two-Way Doors, Reference Class Forecasting, Strategic Withdrawal.

---

## License
MIT License.
