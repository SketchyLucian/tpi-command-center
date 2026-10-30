#!/usr/bin/env python3
"""
TRUE PRIORITY INDEX (TPI) PERSISTENT WORKSPACE (v2.0)
Implements the complete Research Report Architecture with Persistent JSON Memory:
- Top-Down Horizon Mapping (Vision -> Top 5 Goals -> Active Projects -> Weekly Tasks)
- Gate 0 Binary Filter (Habit Guardrail, 2-Min Rule, Type 2 Door, Budget Vault Split, 25/5, 90% Rule)
- Layer 1 Scoring Engine (Vertical Batch Mode + Mid-Week Single Homework Insertion)
- Layer 2 Daily Execution Dashboard (Fixed Autopilot Habits + #1 Frog + 1-3-5 Schedule)
- Reference Class Forecasting (RCF) Historical Log upon Task Completion
"""

import copy
import json
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception as exc:
        print(f"Warning: Could not reconfigure stdout to UTF-8: {exc}")

DATA_FILE = "tpi_workspace.json"

# =====================================================================
# EXACT FIBONACCI SCALES & ANCHOR RUBRICS FROM THE RESEARCH REPORT
# =====================================================================

RUBRICS = {
    "why_align": {
        "title": "COLUMN 1: Strategic Alignment & Consequence (Why_Align)",
        "question": "Why must I do this? Which Goal/Horizon does it serve, and what is the consequence if skipped?",
        "allowed": [1, 2, 5, 8, 13],
        "anchors": {
            1: "Category C -- Zero consequence if skipped.",
            2: "Category B / Horizon 2 (20k ft) -- Minor inconvenience; routine maintenance.",
            5: "Horizon 3 (30k ft) -- Supports a 1-2 year goal; noticeable setback if delayed.",
            8: "Category A / Buffett Top 5 Goal -- Critical to 1 of your 5 core goals.",
            13: "Horizons 4-5 (40k-50k ft Vision) -- Highest contribution (>90% Rule)."
        }
    },
    "value_impact": {
        "title": "COLUMN 2: Direct Value & Impact (Value_Impact)",
        "question": "Once completed, how large is the concrete payoff (output, skill, grade, performance)?",
        "allowed": [1, 2, 5, 8, 13],
        "anchors": {
            1: "Minimal -- Barely noticeable impact.",
            2: "Low -- Small improvement to a single workflow.",
            5: "Medium -- Clear, measurable gain in an important area.",
            8: "High -- Major leap in capability, project output, or results.",
            13: "Massive -- Game-changing breakthrough."
        }
    },
    "urgency_cod": {
        "title": "COLUMN 3: Time Criticality & Cost of Inaction (Urgency_CoD)",
        "question": "How fast does value decay if delayed? How much time/value is leaking each week?",
        "allowed": [1, 2, 5, 8, 13],
        "anchors": {
            1: "No deadline -- Value is identical whenever completed.",
            2: "Low COI -- Minimal cost of inaction; can wait for a slow week.",
            5: "Steady Decay / Weekly Leak -- Ongoing friction or weekly time leak if left undone.",
            8: "Closing Window -- Deadline approaching within days or window closing fast.",
            13: "Hard External Deadline -- Immediate deadline; delay forfeits 100% of value or causes heavy penalty."
        }
    },
    "leverage_rroe": {
        "title": "COLUMN 4: Domino Leverage & Risk Reduction (Leverage_RR/OE)",
        "question": "Does doing this make other tasks easier or unnecessary? Does it remove a bottleneck or risk?",
        "allowed": [1, 3, 5, 8, 13],
        "anchors": {
            1: "Standalone -- Unlocks no other tasks and reduces no future risk.",
            3: "Minor -- Slightly reduces friction for 1 follow-up task.",
            5: "Dual-Purpose -- Integrates 2 competing goals ('two birds with one stone').",
            8: "Systemic -- Neutralizes a major technical/project risk or unlocks multiple steps.",
            13: "Lead Domino -- Clears the primary bottleneck or automates downstream work entirely."
        }
    },
    "confidence": {
        "title": "COLUMN 5: Evidence Discount Multiplier (Confidence)",
        "question": "Are your Value, Leverage, and Duration estimates backed by past experience or gut feeling?",
        "allowed": [0.5, 0.8, 1.0],
        "anchors": {
            1.0: "100% (High) -- Clear specs; you have completed similar tasks before.",
            0.8: "80% (Medium) -- Solid reasoning, partially tested assumptions.",
            0.5: "50% (Low) -- Gut feeling or heavy unknowns. (<50% should be researched first)."
        }
    },
    "duration_rcf": {
        "title": "COLUMN 6: Reference Class Forecasting Duration (Duration_RCF)",
        "question": "Based on actual historical time of similar past tasks (NOT best-case optimism), how big is this?",
        "allowed": [1, 2, 3, 5, 8, 13, 20, 40, 100],
        "anchors": {
            1: "Tiny Anchor (~30 minutes).",
            2: "Small (~1 to 2 hours).",
            3: "Medium-Small (~1 deep work block / half day).",
            5: "Medium-Large (~1 to 2 full days).",
            8: "Large (~3 to 5 days).",
            13: "Very Large (~1 to 2 weeks).",
            20: "TOO LARGE (>= 20) -- Mandatory Task Decomposition required!",
            40: "TOO LARGE (>= 40) -- Mandatory Task Decomposition required!",
            100: "TOO LARGE (100) -- Mandatory Task Decomposition required!"
        }
    }
}


# =====================================================================
# PERSISTENT STORAGE & WORKSPACE INITIALIZATION
# =====================================================================

def default_workspace() -> Dict[str, Any]:
    """Return a blank workspace dictionary with all required keys at their default values."""
    return {
        "next_task_id": 1,
        "vision_horizon_4_5": "Not set yet (Configure in Menu 5)",
        "top_5_goals": [],
        "daily_autopilot_habits": [],
        "habits_state": {"date": datetime.now().strftime("%Y-%m-%d"), "completed": []},
        "habit_history": {},
        "habit_settings": {
            "review_time": "21:00",
            "enable_notifications": True,
            "last_notified_date": "",
        },
        "active_projects": [],
        "weights": {"w1": 1.0, "w2": 1.0, "w3": 1.0, "w4": 1.0},
        "active_tasks": [],
        "waiting_next_month": [],
        "fast_track_inbox": [],
        "avoid_25_5_list": [],
        "dropped_90_rule": [],
        "rcf_history": []
    }


def seed_starter_workspace() -> Dict[str, Any]:
    """Build a pre-populated workspace with realistic example data for first-time users.

    Includes sample vision, goals, habits, projects, tasks with TPI scores,
    and one RCF history entry so every feature is immediately demonstrable.
    """
    ws = default_workspace()
    ws["vision_horizon_4_5"] = "Become a high-competence Mechatronics & Power Electronics Engineer working internationally"
    ws["top_5_goals"] = [
        "1. Achieve target foreign language certification (B2/C1)",
        "2. Master practical power electronics, circuit design & instrumentation",
        "3. Excel in core vocational engineering coursework & manual technical drafting",
        "4. Complete modular DIY hardware builds (bench power supply & portable power systems)",
        "5. Maintain peak cognitive focus, physical fitness & disciplined deep-work blocks"
    ]
    ws["daily_autopilot_habits"] = [
        "Morning & Evening Personal Hygiene / Bath / Laundry Reset",
        "30 mins Daily Foreign Language Vocabulary & Flashcards",
        "45 mins Physical Exercise / Workout Block"
    ]
    ws["active_projects"] = [
        "Language Exam Preparation & Workbook Milestones",
        "Variable Bench Power Supply & Battery System Hardware Build",
        "Manual Technical Drawing & Coursework Assignments"
    ]
    ws["waiting_next_month"] = [
        {
            "name": "Order remaining high-current hardware modules & enclosure parts",
            "reason": "Budget constraint until next month",
            "created_at": datetime.now().strftime("%Y-%m-%d")
        }
    ]
    ws["active_tasks"] = [
        {
            "id": 1,
            "name": "Submit mandatory college registration form",
            "project": "Manual Technical Drawing & Coursework Assignments",
            "why_align": 5, "value_impact": 2, "urgency_cod": 13, "leverage_rroe": 3,
            "confidence": 1.0, "duration_rcf": 1, "tpi_score": 23.0,
            "prerequisite_note": "",
            "created_at": datetime.now().strftime("%Y-%m-%d")
        },
        {
            "id": 2,
            "name": "Calculate thermal limits & hand-draw buck converter wiring schematic ($0 prep)",
            "project": "Variable Bench Power Supply & Battery System Hardware Build",
            "why_align": 8, "value_impact": 8, "urgency_cod": 5, "leverage_rroe": 13,
            "confidence": 1.0, "duration_rcf": 2, "tpi_score": 17.0,
            "prerequisite_note": "",
            "created_at": datetime.now().strftime("%Y-%m-%d")
        },
        {
            "id": 3,
            "name": "Complete 20 grammar exercises in Chapter 4 workbook",
            "project": "Language Exam Preparation & Workbook Milestones",
            "why_align": 8, "value_impact": 5, "urgency_cod": 5, "leverage_rroe": 5,
            "confidence": 1.0, "duration_rcf": 2, "tpi_score": 11.5,
            "prerequisite_note": "",
            "created_at": datetime.now().strftime("%Y-%m-%d")
        }
    ]
    ws["next_task_id"] = 4
    ws["rcf_history"] = [
        {
            "name": "Hand-drafted orthographic projection sheet #2",
            "estimated_fib": 2,
            "actual_fib": 3,
            "actual_notes": "Took ~3.5 hours (longer than expected due to compass detailing)",
            "completed_at": datetime.now().strftime("%Y-%m-%d")
        }
    ]
    return ws


BACKUP_FILE = "tpi_workspace.bak"


def save_workspace(ws: Dict[str, Any], create_backup: bool = True) -> None:
    """Sort active tasks by TPI score (descending) and persist workspace to disk.

    Creates an automatic single-step backup before overwriting to allow instant undo/rollback.
    Raises a user-facing warning if the file cannot be written, but does not
    crash the application so the in-memory state remains usable.
    """
    ws["active_tasks"].sort(key=lambda x: x["tpi_score"], reverse=True)
    try:
        if create_backup and os.path.exists(DATA_FILE):
            import shutil
            shutil.copyfile(DATA_FILE, BACKUP_FILE)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(ws, f, indent=2, ensure_ascii=False)
    except IOError as exc:
        print(f"  [!] ERROR: Could not save workspace to '{DATA_FILE}': {exc}")


def restore_backup() -> Optional[Dict[str, Any]]:
    """Restore workspace from the backup file if available."""
    if not os.path.exists(BACKUP_FILE):
        return None
    try:
        with open(BACKUP_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        base = default_workspace()
        base.update(loaded)
        # Swap backup and current so undoing the restore is possible
        save_workspace(base, create_backup=True)
        return base
    except Exception as exc:
        print(f"Warning: Could not restore from '{BACKUP_FILE}': {exc}")
        return None


# =====================================================================
# PERSISTENT HISTORY TREE & CHECKPOINT VAULT (MACRO TWO-WAY DOOR)
# =====================================================================

HISTORY_FILE = "tpi_history_tree.json"


def compute_workspace_metrics(ws: Dict[str, Any]) -> Dict[str, int]:
    """Extract summary metrics from a workspace snapshot."""
    return {
        "active_tasks": len(ws.get("active_tasks", [])),
        "top_5_goals": len(ws.get("top_5_goals", [])),
        "active_projects": len(ws.get("active_projects", [])),
        "habits": len(ws.get("daily_autopilot_habits", [])),
        "habit_logs": len(ws.get("habit_history", {})),
        "rcf_history": len(ws.get("rcf_history", [])),
        "waiting": len(ws.get("waiting_next_month", [])),
        "avoid": len(ws.get("avoid_25_5_list", [])),
    }


def load_history_tree(current_ws: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Load the persistent History Tree from disk, initializing root if absent."""
    tree: Dict[str, Any] = {"version": 1, "current_node_id": "node_root", "nodes": {}}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict) and "nodes" in loaded and loaded["nodes"]:
                return loaded
        except Exception as exc:
            print(f"Warning: Could not read history tree ({exc}). Reinitializing.")

    root_ws = copy.deepcopy(current_ws) if current_ws else default_workspace()
    root_id = "node_root"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tree["current_node_id"] = root_id
    tree["nodes"] = {
        root_id: {
            "id": root_id,
            "parent_id": None,
            "children_ids": [],
            "timestamp": now_str,
            "title": "Baseline Session Root",
            "tag": "AUTO",
            "reason": "Initial history tree root checkpoint",
            "branch": "main",
            "metrics": compute_workspace_metrics(root_ws),
            "workspace_snapshot": root_ws,
        }
    }
    save_history_tree(tree)
    return tree


def save_history_tree(tree: Dict[str, Any]) -> None:
    """Save the history tree to disk safely."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(tree, f, indent=2, ensure_ascii=False)
    except IOError as exc:
        print(f"Warning: Could not save history tree: {exc}")


def commit_history_node(
    tree: Dict[str, Any],
    ws: Dict[str, Any],
    title: str,
    tag: str = "MANUAL",
    reason: str = "",
    branch: Optional[str] = None,
) -> str:
    """Commit a new snapshot node into the history tree.
    
    Creates a new branch child from the current head node, preserving all historical paths.
    """
    now = datetime.now()
    node_id = f"node_{now.strftime('%Y%m%d_%H%M%S')}_{os.urandom(3).hex()}"
    parent_id = tree.get("current_node_id") or "node_root"
    if parent_id not in tree["nodes"]:
        parent_id = "node_root" if "node_root" in tree["nodes"] else list(tree["nodes"].keys())[0]

    parent_node = tree["nodes"][parent_id]
    
    # Determine branch name
    parent_branch = parent_node.get("branch", "main")
    if branch:
        node_branch = branch
    elif len(parent_node.get("children_ids", [])) > 0:
        node_branch = f"{parent_branch}-fork-{now.strftime('%H%M')}"
    else:
        node_branch = parent_branch

    new_node = {
        "id": node_id,
        "parent_id": parent_id,
        "children_ids": [],
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "title": title,
        "tag": tag,
        "reason": reason,
        "branch": node_branch,
        "metrics": compute_workspace_metrics(ws),
        "workspace_snapshot": copy.deepcopy(ws),
    }

    tree["nodes"][node_id] = new_node
    if node_id not in parent_node.setdefault("children_ids", []):
        parent_node["children_ids"].append(node_id)
    tree["current_node_id"] = node_id
    save_history_tree(tree)
    return node_id


def restore_history_node(
    tree: Dict[str, Any],
    target_node_id: str,
    current_ws: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Restore workspace to a target node in the history tree.
    
    Saves an automatic safety checkpoint of the current state before switching,
    ensuring 100% adherence to Bezos's Two-Way Door reversibility.
    """
    if target_node_id not in tree["nodes"]:
        return None

    if tree.get("current_node_id") == target_node_id:
        return copy.deepcopy(tree["nodes"][target_node_id]["workspace_snapshot"])

    # Commit safety checkpoint of current state before jumping
    commit_history_node(
        tree,
        current_ws,
        title=f"Pre-restore Safety Point (Before jumping to {tree['nodes'][target_node_id]['title']})",
        tag="AUTO",
        reason="Preserve state before tree navigation",
    )

    tree["current_node_id"] = target_node_id
    save_history_tree(tree)
    return copy.deepcopy(tree["nodes"][target_node_id]["workspace_snapshot"])


# =====================================================================
# HORIZON 2 HABIT BATCHING, NOTIFICATIONS & ANALYTICS ENGINE
# =====================================================================

def send_system_notification(title: str, message: str) -> bool:
    """Send a native Windows Desktop Toast Notification via PowerShell without external dependencies.
    
    Adheres to the attention hygiene protocol (Mark, 2008): informs user at the scheduled
    end-of-day batch window without disrupting daytime deep work blocks.
    """
    if sys.platform != "win32":
        return False
    try:
        import subprocess
        safe_title = title.replace('"', '`"').replace("'", "''")
        safe_msg = message.replace('"', '`"').replace("'", "''")
        ps_code = f'''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$xml = $template.GetXml()
$doc = New-Object Windows.Data.Xml.Dom.XmlDocument
$doc.LoadXml($xml)
$nodes = $doc.GetElementsByTagName('text')
$nodes.Item(0).InnerText = "{safe_title}"
$nodes.Item(1).InnerText = "{safe_msg}"
$toast = New-Object Windows.UI.Notifications.ToastNotification($doc)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('TPI Command Center').Show($toast)
'''
        script_path = os.path.join(os.path.dirname(__file__), "_temp_toast.ps1")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(ps_code)
        res = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path], capture_output=True, text=True)
        if os.path.exists(script_path):
            os.remove(script_path)
        return res.returncode == 0
    except Exception:
        return False


def log_habit_review(
    ws: Dict[str, Any],
    date_str: str,
    completed_habits: List[str],
    notes: str = ""
) -> Dict[str, Any]:
    """Record an end-of-day habit review entry in persistent history.
    
    Protects attention hygiene by batching habit check-ins to the end of the day,
    preventing mid-day context switches (Mark, 2008).
    """
    total_habits = len(ws.get("daily_autopilot_habits", []))
    done_count = len(completed_habits)
    rate = (done_count / total_habits) if total_habits > 0 else 0.0
    
    entry = {
        "date": date_str,
        "completed": list(completed_habits),
        "total": total_habits,
        "completed_count": done_count,
        "rate": round(rate, 3),
        "notes": notes.strip(),
        "logged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    if "habit_history" not in ws or not isinstance(ws["habit_history"], dict):
        ws["habit_history"] = {}
    ws["habit_history"][date_str] = entry
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    if date_str == today_str:
        ws["habits_state"] = {"date": today_str, "completed": list(completed_habits)}
        
    save_workspace(ws)
    return entry


def delete_habit_log(ws: Dict[str, Any], date_str: str) -> bool:
    """Delete a specific day's habit completion record from history.
    
    Adheres to Bezos's Two-Way Door principle: safely removes the entry and
    resets today's live completion state if target is today.
    """
    if "habit_history" not in ws or date_str not in ws["habit_history"]:
        return False
    del ws["habit_history"][date_str]
    today_str = datetime.now().strftime("%Y-%m-%d")
    if date_str == today_str and "habits_state" in ws:
        ws["habits_state"]["completed"] = []
    save_workspace(ws)
    return True


def clear_all_habit_history(ws: Dict[str, Any]) -> int:
    """Clear all habit history records from the workspace.
    
    Returns the count of deleted records.
    """
    count = len(ws.get("habit_history", {}))
    ws["habit_history"] = {}
    if "habits_state" in ws:
        ws["habits_state"]["completed"] = []
    save_workspace(ws)
    return count


def purge_past_habit_history(ws: Dict[str, Any], keep_today: bool = True) -> int:
    """Purge past habit history records prior to today (e.g. test or seeded demo logs).
    
    If keep_today is True, today's log (if any) is preserved.
    Returns the count of purged records.
    """
    if "habit_history" not in ws:
        return 0
    today_str = datetime.now().strftime("%Y-%m-%d")
    to_delete = [d for d in list(ws["habit_history"].keys()) if not (keep_today and d == today_str)]
    for d in to_delete:
        del ws["habit_history"][d]
    save_workspace(ws)
    return len(to_delete)


def delete_multiple_habit_logs(ws: Dict[str, Any], date_list: List[str]) -> int:
    """Delete a list of specific dates from habit history.
    
    Returns the count of deleted records.
    """
    if "habit_history" not in ws:
        return 0
    today_str = datetime.now().strftime("%Y-%m-%d")
    deleted = 0
    for d in date_list:
        if d in ws["habit_history"]:
            del ws["habit_history"][d]
            deleted += 1
            if d == today_str and "habits_state" in ws:
                ws["habits_state"]["completed"] = []
    if deleted > 0:
        save_workspace(ws)
    return deleted


def calculate_habit_streaks(ws: Dict[str, Any]) -> Dict[str, int]:
    """Calculate current and longest consecutive habit completion streaks.
    
    A day is counted as a 'success' if its habit completion rate is >= 0.75 (75%).
    If today is pending review, the current streak reflects up to yesterday.
    """
    history = ws.get("habit_history", {})
    if not history:
        return {"current_streak": 0, "best_streak": 0}
        
    today = datetime.now().date()
    today_str = today.strftime("%Y-%m-%d")
    
    streak = 0
    cur_date = today
    
    if today_str in history and history[today_str].get("rate", 0) >= 0.75:
        streak = 1
        cur_date = today - timedelta(days=1)
    elif today_str not in history:
        # Today pending evening review, count up to yesterday
        cur_date = today - timedelta(days=1)
    else:
        # Today was reviewed with rate < 0.75
        cur_date = None
        
    if cur_date:
        while True:
            d_str = cur_date.strftime("%Y-%m-%d")
            if d_str in history and history[d_str].get("rate", 0) >= 0.75:
                streak += 1
                cur_date -= timedelta(days=1)
            else:
                break
                
    # Calculate best streak across all history
    sorted_dates = sorted(
        [datetime.strptime(k, "%Y-%m-%d").date() for k in history.keys() if history[k].get("rate", 0) >= 0.75]
    )
    best_streak = 0
    current_run = 0
    prev_date = None
    for d in sorted_dates:
        if prev_date is None or (d - prev_date).days == 1:
            current_run += 1
        elif (d - prev_date).days > 1:
            current_run = 1
        best_streak = max(best_streak, current_run)
        prev_date = d
        
    best_streak = max(best_streak, streak)
    return {"current_streak": streak, "best_streak": best_streak}


def calculate_habit_analytics(ws: Dict[str, Any], days: int = 30) -> Dict[str, Any]:
    """Compute scientific habit formation, automaticity, and friction analytics.
    
    Based on Task Prioritization and Evaluation Systems research:
    - Horizon 2 Maintenance & Baseline Stability (Allen / GTD)
    - Attention Hygiene: Context switching recovery time saved (Mark, 2008)
    - Strategic Withdrawal / Friction Alert (Page 19)
    - Morning Anchor (DO FIRST) vs Late-Day Decision Fatigue (Page 2)
    """
    history = ws.get("habit_history", {})
    habits = ws.get("daily_autopilot_habits", [])
    streaks = calculate_habit_streaks(ws)
    
    today = datetime.now().date()
    date_range = [today - timedelta(days=i) for i in range(days)]
    date_range.reverse()  # chronological
    
    daily_records = []
    total_rate_sum = 0.0
    logged_days_count = 0
    
    habit_completion_counts = {h: 0 for h in habits}
    
    morning_habit = habits[0] if habits else None
    evening_habit = habits[-1] if len(habits) >= 2 else None
    morning_done = 0
    evening_done = 0
    
    for d in date_range:
        d_str = d.strftime("%Y-%m-%d")
        if d_str in history:
            entry = history[d_str]
            rate = entry.get("rate", 0.0)
            completed = entry.get("completed", [])
            total = entry.get("total", len(habits))
            total_rate_sum += rate
            logged_days_count += 1
            
            for h in habits:
                if h in completed:
                    habit_completion_counts[h] += 1
            if morning_habit and morning_habit in completed:
                morning_done += 1
            if evening_habit and evening_habit in completed:
                evening_done += 1
                
            daily_records.append({
                "date": d_str,
                "day_name": d.strftime("%a"),
                "rate": rate,
                "completed": completed,
                "total": total,
                "is_logged": True,
                "notes": entry.get("notes", ""),
            })
        else:
            daily_records.append({
                "date": d_str,
                "day_name": d.strftime("%a"),
                "rate": 0.0,
                "completed": [],
                "total": len(habits),
                "is_logged": False,
                "notes": "",
            })
            
    avg_rate = (total_rate_sum / logged_days_count) if logged_days_count > 0 else 0.0
    
    recent_7 = daily_records[-7:]
    logged_7 = [r for r in recent_7 if r["is_logged"]]
    avg_7_rate = (sum(r["rate"] for r in logged_7) / len(logged_7)) if logged_7 else 0.0
    
    habit_breakdown = []
    strategic_withdrawal_alerts = []
    
    for idx, h in enumerate(habits, 1):
        c_count = habit_completion_counts.get(h, 0)
        h_rate = (c_count / logged_days_count) if logged_days_count > 0 else 0.0
        
        if h_rate >= 0.85:
            tier = "Automated Routine (Strong Baseline)"
            tier_code = "OPTIMAL"
        elif h_rate >= 0.60:
            tier = "Forming Routine (Requires Cue Stability)"
            tier_code = "FORMING"
        else:
            tier = "High Friction / Atrophy Risk"
            tier_code = "FRICTION"
            if logged_days_count >= 5:
                strategic_withdrawal_alerts.append({
                    "habit": h,
                    "index": idx,
                    "rate": h_rate,
                    "reason": f"Only completed {c_count}/{logged_days_count} days ({h_rate*100:.0f}%).",
                    "recommendation": "Apply research recommendation (Page 19): test 2-week strategic withdrawal or downsize to a 2-minute starter cue.",
                })
                
        habit_breakdown.append({
            "name": h,
            "index": idx,
            "is_first": (idx == 1),
            "completed_count": c_count,
            "total_days": logged_days_count,
            "rate": round(h_rate, 3),
            "tier": tier,
            "tier_code": tier_code,
        })
        
    morning_rate = (morning_done / logged_days_count) if (logged_days_count > 0 and morning_habit) else 0.0
    evening_rate = (evening_done / logged_days_count) if (logged_days_count > 0 and evening_habit) else 0.0
    time_saved_mins = len(habits) * 20
    
    return {
        "period_days": days,
        "logged_days": logged_days_count,
        "avg_completion_rate": round(avg_rate, 3),
        "avg_7_day_rate": round(avg_7_rate, 3),
        "current_streak": streaks["current_streak"],
        "best_streak": streaks["best_streak"],
        "daily_records": daily_records,
        "habit_breakdown": habit_breakdown,
        "strategic_withdrawal_alerts": strategic_withdrawal_alerts,
        "morning_anchor_rate": round(morning_rate, 3),
        "evening_anchor_rate": round(evening_rate, 3),
        "time_saved_mins_per_day": time_saved_mins,
    }


def seed_demo_habit_history(ws: Dict[str, Any], num_days: int = 14) -> None:
    """Populate sample realistic habit completion data for demonstration."""
    import random
    habits = ws.get("daily_autopilot_habits", [])
    if not habits:
        return
    today = datetime.now().date()
    if "habit_history" not in ws or not isinstance(ws["habit_history"], dict):
        ws["habit_history"] = {}
        
    for i in range(num_days, 0, -1):
        d = today - timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        done = []
        for idx, h in enumerate(habits):
            prob = 0.9 if idx == 0 else (0.8 if idx == 1 else 0.7)
            if random.random() < prob:
                done.append(h)
        rate = len(done) / len(habits)
        ws["habit_history"][d_str] = {
            "date": d_str,
            "completed": done,
            "total": len(habits),
            "completed_count": len(done),
            "rate": round(rate, 3),
            "notes": "Evening batch reflection completed.",
            "logged_at": f"{d_str} 21:15:00",
        }
    save_workspace(ws)


def load_workspace(interactive: bool = True) -> Dict[str, Any]:
    """Load workspace from disk, or guide the user through first-time setup.

    On first run (no data file), offers a choice between a pre-built starter
    workspace and a blank one.  On corrupt or unreadable files, falls back to
    a fresh default workspace with a warning.
    """
    if not os.path.exists(DATA_FILE):
        if not interactive:
            ws = seed_starter_workspace()
            save_workspace(ws)
            return ws
        print("\n" + "=" * 78)
        print(" FIRST-TIME SETUP: CREATING PERSISTENT MEMORY ('tpi_workspace.json')")
        print("=" * 78)
        print("No saved workspace found yet. How would you like to initialize your system?")
        print("  [1] Load a Pre-Built Starter Workspace (Recommended -- see real examples & edit anytime)")
        print("  [2] Start with a Completely Blank Workspace")
        choice = input("\nSelect [1 or 2] (default 1): ").strip()
        ws = default_workspace() if choice == "2" else seed_starter_workspace()
        save_workspace(ws)
        print(f"  -> Saved initial workspace to '{DATA_FILE}'.")
        return ws

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        base = default_workspace()
        base.update(loaded)
        if "habit_history" not in base or not isinstance(base.get("habit_history"), dict):
            base["habit_history"] = {}
        if "habit_settings" not in base or not isinstance(base.get("habit_settings"), dict):
            base["habit_settings"] = {
                "review_time": "21:00",
                "enable_notifications": True,
                "last_notified_date": "",
            }
        return base
    except (json.JSONDecodeError, IOError) as exc:
        print(f"Warning: Could not read '{DATA_FILE}' ({exc}). Starting fresh.")
        return default_workspace()


# =====================================================================
# CLI HELPER UTILITIES
# =====================================================================

def print_header(title: str) -> None:
    """Print a prominent section header with separator lines."""
    print("\n" + "=" * 78)
    print(f" {title}")
    print("=" * 78)


def prompt_yes_no(prompt: str) -> bool:
    """Prompt the user for a yes/no answer and return a boolean.

    Repeats until a valid 'y'/'yes' or 'n'/'no' response is given.
    """
    while True:
        ans = input(f"{prompt} [y/n]: ").strip().lower()
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False
        print("  -> Please enter 'y' or 'n'.")


def prompt_score_selection(prompt: str, allowed_values: List[float]) -> float:
    """Prompt the user to select a score from a fixed set of allowed Fibonacci values.

    Repeats until the user enters an exact match from the allowed set.
    """
    allowed_str = ", ".join(str(v) for v in allowed_values)
    while True:
        raw = input(f"{prompt} ({allowed_str}): ").strip()
        try:
            val = float(raw) if "." in raw else int(raw)
            if val in allowed_values:
                return val
        except ValueError:
            pass
        print(f"  -> Invalid input. Choose an exact number from: [{allowed_str}]")


def compute_tpi(task: Dict[str, Any], weights: Dict[str, float]) -> float:
    """Compute the True Priority Index for a single task.

    Formula (from Research Report):
        TPI = [(W1 * Why_Align) + (W2 * Value_Impact)
             + (W3 * Urgency_CoD) + (W4 * Leverage_RR/OE)]
              * Confidence / Duration_RCF
    """
    weighted_num = (
        weights["w1"] * task["why_align"]
        + weights["w2"] * task["value_impact"]
        + weights["w3"] * task["urgency_cod"]
        + weights["w4"] * task["leverage_rroe"]
    )
    discounted = weighted_num * task["confidence"]
    return round(discounted / task["duration_rcf"], 2)


def recalculate_all_tpi_scores(ws: Dict[str, Any]) -> None:
    """Recompute TPI scores for every active task and persist the updated queue."""
    for task in ws["active_tasks"]:
        task["tpi_score"] = compute_tpi(task, ws["weights"])
    save_workspace(ws)


def select_review_date() -> str:
    """Present structured review cadences aligned with the Research Report and return the chosen date.

    Options offered:
    - Next Weekly Review (Friday/Sunday): Primary GTD operational anchor (Doc p. 18)
    - Next Daily Triage (Tomorrow): 24-hr rapid turnaround (Doc p. 17)
    - Timebox Sprint Horizons (7 or 14 days): Agile iteration blocks
    - Custom Date (YYYY-MM-DD or day offset)
    """
    now = datetime.now()

    # Upcoming Friday (Doc p. 18: 'Chiều Thứ Sáu')
    days_to_fri = (4 - now.weekday()) % 7
    if days_to_fri == 0:
        days_to_fri = 7
    fri_date = (now + timedelta(days=days_to_fri)).strftime("%Y-%m-%d")

    # Upcoming Sunday (Doc p. 18: 'Chủ Nhật')
    days_to_sun = (6 - now.weekday()) % 7
    if days_to_sun == 0:
        days_to_sun = 7
    sun_date = (now + timedelta(days=days_to_sun)).strftime("%Y-%m-%d")

    # Tomorrow (Daily Triage - Doc p. 17)
    tomorrow_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    # In 7 Days (1 Week Sprint)
    week_date = (now + timedelta(days=7)).strftime("%Y-%m-%d")

    # In 14 Days (2-Week Cycle)
    two_weeks_date = (now + timedelta(days=14)).strftime("%Y-%m-%d")

    print("\n      --- SELECT FIXED REVIEW DATE (Research Report Cadences) ---")
    print(f"      [1] Next Weekly Review -- Friday ({fri_date}) [Standard Recommended]")
    print(f"      [2] Next Weekly Review -- Sunday ({sun_date})")
    print(f"      [3] Next Daily Triage -- Tomorrow ({tomorrow_date})")
    print(f"      [4] In 7 Days ({week_date})")
    print(f"      [5] In 14 Days (2-Week Sprint: {two_weeks_date})")
    print("      [6] Custom Date (Enter YYYY-MM-DD or days from today)")

    while True:
        choice = input("      Select cadence [1-6] (default 1): ").strip()
        if not choice or choice == "1":
            return fri_date
        elif choice == "2":
            return sun_date
        elif choice == "3":
            return tomorrow_date
        elif choice == "4":
            return week_date
        elif choice == "5":
            return two_weeks_date
        elif choice == "6":
            raw = input("      Enter YYYY-MM-DD or days offset (e.g., 5): ").strip()
            if raw.isdigit():
                return (now + timedelta(days=int(raw))).strftime("%Y-%m-%d")
            try:
                datetime.strptime(raw, "%Y-%m-%d")
                return raw
            except ValueError:
                print("      -> Invalid format. Enter YYYY-MM-DD (e.g., 2026-11-05) or number of days.")
        else:
            print("      -> Invalid choice. Enter a number from 1 to 6.")


def format_review_status(review_date_str: str) -> str:
    """Compute the time delta between today and a review date string.

    Returns a human-readable badge indicating overdue, due today,
    due tomorrow, or the number of days remaining.
    """
    if not review_date_str:
        return ""
    try:
        rev_dt = datetime.strptime(review_date_str[:10], "%Y-%m-%d").date()
        today = datetime.now().date()
        diff = (rev_dt - today).days
        if diff < 0:
            return f"[!] OVERDUE ({abs(diff)}d ago: {review_date_str}) -- Time to Review & Rollback/Keep!"
        elif diff == 0:
            return f"[*] DUE TODAY ({review_date_str}) -- Time to Review & Decide!"
        elif diff == 1:
            return f"[Review: Tomorrow ({review_date_str})]"
        else:
            return f"[Review in {diff} days ({review_date_str})]"
    except Exception:
        return f"[Review: {review_date_str}]"


# =====================================================================
# MENU [1]: VIEW DASHBOARD & TODAY'S EXECUTION PLAN
# =====================================================================

def display_dashboard(ws: Dict[str, Any]) -> None:
    """Render the full Daily Command Dashboard including habits, fast-track items,
    the ranked TPI task queue, and the Layer 2 daily execution plan (1-3-5 Rule).
    """
    print_header("DAILY COMMAND DASHBOARD (PERSISTENT MEMORY LOADED)")
    print(f"3-5 Year Vision : {ws['vision_horizon_4_5']}")
    weights = ws["weights"]
    print(f"Active Weights  : W1(Why)={weights['w1']} | W2(Val)={weights['w2']} | W3(Urg)={weights['w3']} | W4(Lev)={weights['w4']}")

    # --- Phase A: Fixed Daily Autopilot Habits (Horizon 2 -- End-of-Day Batch Review) ---
    today_str = datetime.now().strftime("%Y-%m-%d")
    if "habits_state" not in ws or not isinstance(ws.get("habits_state"), dict) or ws["habits_state"].get("date") != today_str:
        ws["habits_state"] = {"date": today_str, "completed": []}
        save_workspace(ws, create_backup=False)

    history = ws.get("habit_history", {})
    habit_settings = ws.get("habit_settings", {"review_time": "21:00", "enable_notifications": True})
    review_time = habit_settings.get("review_time", "21:00")
    streaks = calculate_habit_streaks(ws)
    today_logged = today_str in history

    completed_habits = ws.get("habits_state", {}).get("completed", [])
    total_habits = len(ws.get("daily_autopilot_habits", []))
    done_count = len(completed_habits)

    status_str = f"[COMPLETED TODAY: {done_count}/{total_habits} Done]" if today_logged else f"[PENDING END-OF-DAY REVIEW @ {review_time}]"
    print(f"\n[A] FIXED DAILY AUTOPILOT HABITS (Horizon 2 -- {status_str}):")
    print(f"    * Attention Hygiene: Habits are batched for evening review to eliminate daytime context switches.")
    print(f"    * Consistency Streak: {streaks['current_streak']} days | Best: {streaks['best_streak']} days")
    if ws["daily_autopilot_habits"]:
        for idx, habit in enumerate(ws["daily_autopilot_habits"], 1):
            check_box = "[X]" if habit in completed_habits else "[ ]"
            badge = " (DO FIRST)" if idx == 1 else ""
            print(f"    {check_box} [Routine {idx}{badge}] {habit}")
    else:
        print("    (No daily habits set yet. Add exercise, hygiene, or daily flashcards in Menu 5!)")

    # --- Phase B: Fast-Track 2-Min / Type 2 Door Queue ---
    if ws["fast_track_inbox"]:
        print("\n[B] FAST-TRACK / ADMIN BATCH ITEMS (Passed via 2-Min or Type 2 Door Rule):")
        for idx, item in enumerate(ws["fast_track_inbox"], 1):
            created_str = f" [Created: {item.get('created_at', 'N/A')}]"
            review_date = item.get("review_date")
            if not review_date and "Review:" in item.get("action", ""):
                try:
                    review_date = item["action"].split("Review:")[1].split("|")[0].strip()
                except Exception:
                    pass
            status_badge = f" -> {format_review_status(review_date)}" if review_date else ""
            print(f"  * [FT-{idx}] {item['name']}{created_str}")
            print(f"         Action: {item['action']}{status_badge}")

    # --- Phase C: Ranked Active Tasks Table (Layer 1) ---
    print("\n[C] LAYER 1: ACTIVE TPI TASK QUEUE (Ranked Highest to Lowest):")
    tasks = ws["active_tasks"]
    if not tasks:
        print("  (Your scored task queue is empty! Choose [2] from the main menu to add tasks.)")
        return

    header = f"{'Rank':<4} | {'ID':<3} | {'Task Name':<34} | {'Why':>3} | {'Val':>3} | {'Urg':>3} | {'Lev':>3} | {'Conf':>4} | {'Dur':>3} | {'TPI':>6}"
    print(header)
    print("-" * len(header))
    for idx, task in enumerate(tasks, 1):
        dependency_marker = "*" if task.get("prerequisite_note") else " "
        short_name = (task["name"])[:33] + dependency_marker
        print(
            f"#{idx:<3} | {task['id']:<3} | {short_name:<34} | "
            f"{int(task['why_align']):>3} | {int(task['value_impact']):>3} | "
            f"{int(task['urgency_cod']):>3} | {int(task['leverage_rroe']):>3} | "
            f"{task['confidence']:>4.1f} | {int(task['duration_rcf']):>3} | "
            f"{task['tpi_score']:>6.2f}"
        )
        meta_items = []
        if task.get("created_at"):
            meta_items.append(f"Created: {task['created_at']}")
        if task.get("prerequisite_note"):
            meta_items.append(f"Dependency: {task['prerequisite_note']}")
        if meta_items:
            print(f"             -> [{' | '.join(meta_items)}]")

    # --- Phase D: Layer 2 Daily Execution Plan (1-3-5 Rule + Morning Deep Work Block) ---
    print("\n[D] LAYER 2: TODAY'S EXECUTION PLAN (Attention Protection):")
    top_frog = tasks[0]
    print(f"  1. MORNING DEEP WORK BLOCK (90-120 Mins, Zero Notifications, Distraction Pad Ready):")
    print(f"     -> #1 EAT THAT FROG: [ID {top_frog['id']}] \"{top_frog['name']}\" (TPI: {top_frog['tpi_score']})")

    big_tasks = [task for task in tasks if task["duration_rcf"] >= 3]
    med_tasks = [task for task in tasks if task["duration_rcf"] == 2]
    small_tasks = [task for task in tasks if task["duration_rcf"] == 1]

    print("\n  2. TODAY'S 1-3-5 ALLOCATION:")
    print(f"     * 1 BIG Task (Dur >= 3)   : {big_tasks[0]['name'] if big_tasks else top_frog['name']}")
    print(f"     * 3 MEDIUM Tasks (Dur = 2): {', '.join(task['name'] for task in med_tasks[:3]) or 'None in queue'}")
    print(f"     * 5 SMALL Tasks (Dur = 1) : {', '.join(task['name'] for task in small_tasks[:5]) or 'Use Fast-Track / Admin Batch'}")


# =====================================================================
# MENU [2]: ADD TASKS (GATE 0 + MID-WEEK SINGLE OR WEEKLY BATCH)
# =====================================================================

def show_goal_context_banner(ws: Dict[str, Any]) -> None:
    """Display the user's top-down goals and active projects as a reference
    for slicing actionable weekly tasks during task entry.
    """
    print("\n--- YOUR TOP-DOWN GOALS & ACTIVE PROJECTS (Slicing Reference) ---")
    if ws.get("vision_horizon_4_5") and ws["vision_horizon_4_5"] != "Not set yet (Configure in Menu 5)":
        print(f"3-5 Year Vision (Horizon 4-5) : {ws['vision_horizon_4_5']}")
    if ws["top_5_goals"]:
        print("Top 5 Core Goals (Horizon 3 -- 12-24 Month Milestones):")
        for goal in ws["top_5_goals"]:
            print(f"  * {goal}")
    if ws["active_projects"]:
        print("Active Projects (Horizon 1 -- <12 Months -- Slice finishable weekly tasks from these!):")
        for idx, project in enumerate(ws["active_projects"], 1):
            print(f"  [{idx}] {project}")
    print("-" * 65)


def screen_task_through_gate_zero(ws: Dict[str, Any], raw_name: str) -> List[Dict[str, Any]]:
    """Screen a candidate task through the Gate 0 binary filter.

    Applies checks in sequence: Habit Guardrail, 2-Min Rule, Type 2 Door,
    Hard Constraints, Budget Lock, Buffett 25/5, and McKeown 90% Rule.

    Returns a list of 0 or 1 surviving task dicts ready for Layer 1 scoring
    (or a $0 prep task if the original task was budget-blocked).
    """
    print(f"\n--- Gate 0 Screening for: '{raw_name}' ---")

    # Check 0: Habit / Routine Guardrail (Question 3 fix)
    if prompt_yes_no("  0.  [Habit Guardrail] Is this a recurring habit/hygiene/exercise routine (no one-time finish line)?"):
        ws["daily_autopilot_habits"].append(raw_name)
        save_workspace(ws)
        print("  -> ROUTED TO DAILY AUTOPILOT: Added to your Fixed Daily Habits list (never scored by math).")
        return []

    # Check 1a: 2-Minute Rule
    if prompt_yes_no("  1a. [GTD 2-Min Rule] Can this be finished in under 2 minutes?"):
        created_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        ws["fast_track_inbox"].append({
            "name": raw_name,
            "action": "2-Minute Immediate / Afternoon Admin Batch",
            "created_at": created_time
        })
        save_workspace(ws)
        print("  -> FAST-TRACKED: Do it right now or in your Afternoon Admin Batch.")
        return []

    # Check 1b: Bezos Type 2 Reversible Decision (<30 min resolution / quick test)
    if prompt_yes_no("  1b. [Bezos Type 2 Decision] Is this a quick reversible decision or experiment (<30m to decide/test) with >=70% info (not a large task)?"):
        review_date = select_review_date()
        rollback = input("      Enter Rollback Trigger (condition to undo): ").strip() or "Revert if metric drops"
        created_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        ws["fast_track_inbox"].append({
            "name": raw_name,
            "action": f"Type 2 Fast Execution (Review: {review_date} | Rollback: {rollback})",
            "created_at": created_time,
            "review_date": review_date,
            "rollback": rollback
        })
        save_workspace(ws)
        print(f"  -> FAST-TRACKED: Execute immediately. Scheduled for review on {review_date}.")
        return []

    # Check 2a: Permanent Hard Constraints (Safety/Ethics)
    if prompt_yes_no("  2a. [Hard Constraint] Does this violate a permanent safety, health, or ethical boundary?"):
        print("  -> REJECTED IMMEDIATELY: Never allow unsafe or unethical tasks into the scoring table.")
        return []

    # Check 2b: Temporary Budget / Tool Constraint until Next Month (Question 4 fix)
    if prompt_yes_no("  2b. [Budget/Resource Lock] Is this blocked by money or missing parts until next month?"):
        reason = input("      When will the budget/parts unlock? (e.g., Next month stipend): ").strip() or "Next month"
        ws["waiting_next_month"].append({
            "name": raw_name,
            "reason": reason,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        save_workspace(ws)
        print(f"  -> SAVED TO 'WAITING / NEXT MONTH' VAULT: '{raw_name}' won't clutter this week's list.")

        if prompt_yes_no("      [Zero-Cost Prep Split] Can you extract a $0 design, schematic, or calculation task to do right now?"):
            prep_name = input("      Enter the $0 prep task name: ").strip()
            if prep_name:
                print(f"  -> GREAT! Routing '{prep_name}' ($0 prep) into the TPI Scoring Queue.")
                raw_name = prep_name
            else:
                return []
        else:
            return []

    # Check 3: Buffett 25/5 Horizon Check
    if not prompt_yes_no("  3.  [Buffett 25/5 Rule] Does this serve your Top 5 Core Goals or mandatory coursework/work?"):
        ws["avoid_25_5_list"].append(raw_name)
        save_workspace(ws)
        print("  -> QUARANTINED: Added to your 'Avoid-At-All-Costs List' (Goals 6-25).")
        return []

    # Check 4: McKeown 90% Rule & Sunk-Cost Check
    if not prompt_yes_no("  4.  [McKeown 90% Rule] Is this a high-impact contribution (>=90%), OR worth signing up for today from scratch?"):
        ws["dropped_90_rule"].append(raw_name)
        save_workspace(ws)
        print("  -> DROPPED: Below 90% threshold. Decline or exit commitment.")
        return []

    project_tag = input("  Optional -- Link to which Active Project/Course? (Press Enter to skip): ").strip()
    print(f"  -> PASSED GATE 0: '{raw_name}' is ready for TPI scoring.")
    return [{"name": raw_name, "project": project_tag}]


def score_candidates(ws: Dict[str, Any], candidates: List[Dict[str, Any]], mode_label: str) -> None:
    """Run the Layer 1 multi-criteria scoring engine on Gate 0 survivors.

    Scores are applied one column at a time across all candidates (vertical
    batch mode) to prevent halo effect bias, per the Research Report.
    """
    if not candidates:
        return

    print_header(f"LAYER 1 SCORING: {mode_label}")
    print("Evaluating one column at a time across your task(s).")

    columns_order = [
        "why_align",
        "value_impact",
        "urgency_cod",
        "leverage_rroe",
        "confidence",
        "duration_rcf"
    ]

    for col_key in columns_order:
        rubric = RUBRICS[col_key]
        print("\n" + "-" * 78)
        print(f" {rubric['title']}")
        print(f" Question: \"{rubric['question']}\"")
        print("-" * 78)
        for score_val, desc in rubric["anchors"].items():
            print(f"   [{score_val:>4}] : {desc}")

        # Show existing active tasks' scores in this column as relative anchors!
        if ws["active_tasks"]:
            print("\n   Your Existing Tasks in This Column (For Relative Comparison):")
            for existing in ws["active_tasks"][:5]:
                print(f"     * [{existing[col_key]:>4}] {existing['name']}")

        # If scoring Duration_RCF, display RCF Historical Completed Tasks!
        if col_key == "duration_rcf" and ws["rcf_history"]:
            print("\n   Your Historical Completed Tasks (Reference Class Forecasting Memory):")
            for hist in ws["rcf_history"][-5:]:
                print(
                    f"     * '{hist['name']}' -> Estimated Fib: {hist['estimated_fib']} | "
                    f"ACTUAL Fib: {hist['actual_fib']} ({hist['actual_notes']})"
                )

        print("-" * 78)

        for idx, task in enumerate(candidates, start=1):
            val = prompt_score_selection(f"  Score [{task['name']}]", rubric["allowed"])

            # Mandatory Decomposition if Duration >= 20
            if col_key == "duration_rcf" and val >= 20:
                print(f"\n  [!] STOP: '{task['name']}' scored {int(val)} (>= 20 -- Too large to estimate accurately).")
                print("      Let's slice it into its FIRST actionable milestone right now.")
                sub_name = input("      Enter the name of the first smaller milestone: ").strip()
                if sub_name:
                    task["name"] = f"{sub_name} (Milestone of: {task['name']})"
                val = prompt_score_selection(f"      Re-score Duration_RCF for '{task['name']}'", [1, 2, 3, 5, 8, 13])

            task[col_key] = val

    # Calculate TPI and insert into persistent workspace
    print("\n--- TPI CALCULATION RESULTS ---")
    for task in candidates:
        task["id"] = ws["next_task_id"]
        ws["next_task_id"] += 1
        task["tpi_score"] = compute_tpi(task, ws["weights"])
        task["prerequisite_note"] = input(
            f"  Does '{task['name']}' (TPI: {task['tpi_score']}) require any prerequisite task first? (Enter note or press Enter): "
        ).strip()
        task["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        ws["active_tasks"].append(task)

    save_workspace(ws)
    print("\n  -> Saved and sorted into your Persistent TPI Queue!")
    display_dashboard(ws)


def add_tasks_menu(ws: Dict[str, Any]) -> None:
    """Present the task entry sub-menu: mid-week single insertion or weekly batch."""
    print_header("ADD TASKS: WEEKLY BATCH OR MID-WEEK HOMEWORK TRIAGE")
    print("  [A] Mid-Week Single Task / Homework Insertion (Fast 30-second triage against current queue)")
    print("  [B] Weekly Review Batch Entry (Enter multiple tasks from your Projects & score vertically)")
    print("  [C] Cancel / Return to Main Menu")

    mode = input("\nSelect [A, B, or C]: ").strip().upper()
    if mode == "C" or mode not in ("A", "B"):
        return

    show_goal_context_banner(ws)

    if mode == "A":
        raw_name = input("\nEnter your new mid-week homework or task (start with an action verb): ").strip()
        if not raw_name:
            return
        surviving = screen_task_through_gate_zero(ws, raw_name)
        if surviving:
            score_candidates(ws, surviving, "MID-WEEK SINGLE TASK INSERTION")
    else:
        candidates = []
        while True:
            raw_name = input("\nEnter candidate task name (or press Enter when finished adding tasks): ").strip()
            if not raw_name:
                break
            surviving = screen_task_through_gate_zero(ws, raw_name)
            candidates.extend(surviving)
        if candidates:
            score_candidates(ws, candidates, "WEEKLY BATCH VERTICAL SCORING")


# =====================================================================
# MENU [3]: COMPLETE A TASK & LOG ACTUAL TIME FOR RCF
# =====================================================================

def _complete_fast_track_item(ws: Dict[str, Any], user_input: str) -> bool:
    """Attempt to complete a fast-track item by its FT-N identifier.

    Returns True if the input matched a fast-track pattern (handled),
    False if the input should be processed as a regular task ID.
    """
    if not (user_input.startswith("FT") or
            (user_input.startswith("F") and len(user_input) > 1 and user_input[1:].isdigit())):
        return False

    clean_num = user_input.replace("FT-", "").replace("FT", "").replace("F", "")
    if not clean_num.isdigit():
        return True

    idx = int(clean_num) - 1
    if 0 <= idx < len(ws["fast_track_inbox"]):
        removed = ws["fast_track_inbox"].pop(idx)
        save_workspace(ws)
        print(f"  -> Marked Fast-Track item completed: '{removed['name']}'!")
    else:
        print("  -> Invalid Fast-Track item number.")
    return True


def complete_task_menu(ws: Dict[str, Any]) -> None:
    """Mark a task as completed and log its actual duration into the RCF history.

    Supports completing scored tasks (by ID), individual fast-track items
    (by FT-N), or clearing all fast-track items at once.
    """
    print_header("COMPLETE A TASK & UPDATE REFERENCE CLASS FORECASTING (RCF) MEMORY")
    if not ws["active_tasks"] and not ws["fast_track_inbox"]:
        print("No active tasks to complete.")
        return

    # Display scored tasks
    if ws["active_tasks"]:
        print("Active Scored Tasks:")
        for idx, task in enumerate(ws["active_tasks"], 1):
            print(f"  [ID {task['id']:<3}] (Rank #{idx}, TPI {task['tpi_score']:>5.2f}, Est. Dur={int(task['duration_rcf'])}) {task['name']}")

    # Display fast-track items
    if ws["fast_track_inbox"]:
        print("\nFast-Track / Type 2 Execution Items:")
        for idx, item in enumerate(ws["fast_track_inbox"], 1):
            review_date = item.get("review_date", "")
            review_badge = f" ({format_review_status(review_date)})" if review_date else ""
            print(f"  [FT-{idx}] {item['name']}{review_badge}")
        print("  [F] Clear all Fast-Track / 2-Minute Admin Batch items")

    user_input = input("\nEnter Task ID to mark COMPLETED (or 'FT-1' for Fast-Track, 'F' for all Fast-Track, Enter to cancel): ").strip().upper()
    if not user_input:
        return

    # Handle bulk fast-track clear
    if user_input == "F":
        ws["fast_track_inbox"] = []
        save_workspace(ws)
        print("  -> Cleared Fast-Track inbox!")
        return

    # Handle individual fast-track completion
    if _complete_fast_track_item(ws, user_input):
        return

    # Handle scored task completion by ID
    try:
        tid = int(user_input)
    except ValueError:
        print("  -> Invalid ID.")
        return

    target = next((task for task in ws["active_tasks"] if task["id"] == tid), None)
    if not target:
        print(f"  -> Task ID {tid} not found.")
        return

    print(f"\nCompleting: '{target['name']}'")
    print(f"Your Initial Estimated Fibonacci Duration was: [{int(target['duration_rcf'])}]")
    print("  (Reminder: 1=~30m, 2=1-2h, 3=Half day, 5=1-2 days, 8=3-5 days, 13=1-2 weeks)")
    actual_fib = prompt_score_selection("What was the ACTUAL Fibonacci Duration it took?", [1, 2, 3, 5, 8, 13, 20])
    notes = input("Optional note on actual time (e.g., 'Took 2 hours, smooth' or 'Took 4 hours due to bug'): ").strip()

    ws["rcf_history"].append({
        "name": target["name"],
        "estimated_fib": int(target["duration_rcf"]),
        "actual_fib": int(actual_fib),
        "actual_notes": notes or "Completed",
        "completed_at": datetime.now().strftime("%Y-%m-%d")
    })
    ws["active_tasks"] = [task for task in ws["active_tasks"] if task["id"] != tid]
    save_workspace(ws)
    print(f"  -> Awesome job! Logged '{target['name']}' into your RCF History and removed from active queue.")


# =====================================================================
# MENU [4]: WEEKLY REVIEW (UPDATE URGENCY & UNLOCK WAITING LIST)
# =====================================================================

def weekly_review_menu(ws: Dict[str, Any]) -> None:
    """Guide the user through the weekly review cycle: unlock budget-blocked tasks,
    review Type 2 experiments, and update Urgency_CoD scores as deadlines shift.
    """
    print_header("WEEKLY REVIEW: UPDATE DEADLINE URGENCY & UNLOCK NEXT-MONTH VAULT")

    # --- Step 1: Check Waiting / Next Month Vault (Question 4 follow-through) ---
    if ws["waiting_next_month"]:
        print("\n[STEP 1] WAITING / NEXT-MONTH VAULT (Budget or Resource Blocked Tasks):")
        remaining_vault = []
        for item in ws["waiting_next_month"]:
            print(f"\n  * Blocked Task : {item['name']}")
            print(f"    Unlock Note  : {item['reason']} (Added: {item['created_at']})")
            if prompt_yes_no("    Has your budget/resource arrived so you can score and do this task this week?"):
                score_candidates(ws, [{"name": item["name"], "project": ""}], "UNLOCKED VAULT TASK")
            else:
                remaining_vault.append(item)
        ws["waiting_next_month"] = remaining_vault
        save_workspace(ws)
    else:
        print("\n[STEP 1] Waiting / Next-Month Vault is currently empty.")

    # --- Step 1b: Review Type 2 Reversible Fast-Track Items Due for Review ---
    if ws["fast_track_inbox"]:
        print("\n[STEP 1b] TYPE 2 REVERSIBLE EXPERIMENTS & FAST-TRACK INBOX:")
        remaining_ft = []
        for item in ws["fast_track_inbox"]:
            review_date = item.get("review_date", "")
            status = format_review_status(review_date) if review_date else ""
            print(f"\n  * Item   : {item['name']}")
            print(f"    Action : {item['action']}")
            if status:
                print(f"    Review : {status}")
            print("    Options: [1] Kept/Success (Complete) | [2] Trigger Rollback (Revert) | [3] Reschedule | [4] Keep as is")
            choice = input("    Select [1-4] (default 4): ").strip()
            if choice == "1":
                print(f"    -> Success confirmed! '{item['name']}' marked completed.")
            elif choice == "2":
                print(f"    -> Rollback triggered: Reverted and discarded '{item['name']}'.")
            elif choice == "3":
                new_date = select_review_date()
                item["review_date"] = new_date
                item["action"] = f"Type 2 Fast Execution (Review: {new_date} | Rollback: {item.get('rollback', 'Revert')})"
                remaining_ft.append(item)
                print(f"    -> Rescheduled review to {new_date}.")
            else:
                remaining_ft.append(item)
        ws["fast_track_inbox"] = remaining_ft
        save_workspace(ws)

    # --- Step 2: Update Urgency_CoD across existing active tasks ---
    if ws["active_tasks"]:
        print("\n[STEP 2] UPDATE URGENCY SCORES (As deadlines get closer, Urgency steps up: 1 -> 2 -> 5 -> 8 -> 13)")
        if prompt_yes_no("Would you like to review and update Urgency_CoD for your active tasks?"):
            for task in ws["active_tasks"]:
                print(f"\n  Task [ID {task['id']}]: {task['name']} (Current Urgency_CoD = {int(task['urgency_cod'])})")
                if prompt_yes_no("    Update Urgency score?"):
                    task["urgency_cod"] = prompt_score_selection("    New Urgency_CoD", [1, 2, 5, 8, 13])
            recalculate_all_tpi_scores(ws)
            print("\n  -> Recalculated and re-sorted all TPI scores!")
    display_dashboard(ws)


# =====================================================================
# MENU [5]: MANAGE TOP-DOWN FOUNDATION (GOALS, PROJECTS, HABITS)
# =====================================================================

def show_horizon_methodology_guide() -> None:
    """Display comprehensive guidance on the Altitude Map and how to choose
    Vision, Top 5 Goals, Projects, and Daily Habits based on the Research Report.
    """
    print_header("RESEARCH GUIDE: THE 6 HORIZONS & GOAL-SETTING METHODOLOGY")
    print("""
[1] THE ALTITUDE MAP (David Allen GTD -- Research Report pp. 3-4):
  -------------------------------------------------------------------------------
  Altitude / Horizon      Timeframe          Focus / Strategic Role
  -------------------------------------------------------------------------------
  Horizon 5 (50,000 ft)   Invariable /       PURPOSE & CORE PRINCIPLES:
                          Lifelong           Why you exist, core values, non-negotiable
                                             ethical boundaries.
  Horizon 4 (40,000 ft)   3 to 5 Years       VISION:
                                             Ideal future state; what success looks &
                                             feels like when Purpose is realized.
  Horizon 3 (30,000 ft)   12 to 24 Months    GOALS & OBJECTIVES (Top 5 Core Goals):
                          (1 to 2 Years)     Concrete, verifiable milestones set annually
                                             and calibrated quarterly (Buffett 25/5).
  Horizon 2 (20,000 ft)   Ongoing /          AREAS OF FOCUS & AUTOPILOT HABITS:
                          Continuous         Operational maintenance (health, sleep,
                                             hygiene, study routines). Never scored!
  Horizon 1 (10,000 ft)   Under 12 Months    ACTIVE PROJECTS:
                          (2 to 8 weeks)     Multi-step finishable outcomes underway.
  Ground / Runway (0 ft)  Daily / Immediate  NEXT PHYSICAL ACTIONS / TASKS:
                                             Atomic tasks (30m - 2h) scored by TPI.
  -------------------------------------------------------------------------------

[2] HOW TO CHOOSE YOUR 3-5 YEAR VISION (Horizon 4-5):
  * Core Question: "Who do I need to become, and what master capability must I possess
    in 3 to 5 years?"
  * Framing Template:
    "Become a [Specific Identity / Expertise Level] capable of [High-Value Benchmark]
     working with [Key Standard / Industry]."
  * Example:
    "Become a high-competence Mechatronics & Power Electronics Engineer working
     internationally with verified PCB design and embedded firmware mastery."

[3] HOW TO CHOOSE YOUR TOP 5 CORE GOALS (Horizon 3 -- 12 to 24 Months / 1-2 Years):
  * Timeframe: Exactly 12 to 24 Months (1 to 2 Years). Set annually, refined quarterly.
  * Method: Warren Buffett's 25/5 Strategy (Research Report pp. 4, 18-19):
      Step A: Brainstorm 25 candidate ambitions across study, career, and life.
      Step B: Force-rank and circle ONLY the TOP 5 most critical goals.
      Step C: Quarantine goals 6 through 25 to the "AVOID-AT-ALL-COSTS LIST".
              (Research finding: Goals 6-25 are the real trap because they are
              attractive enough to distract you from excellence in your top 5!)
  * Criteria: Locke & Latham Goal Specificity (Locke & Latham 2020):
      - Must have a binary, verifiable finish line (NOT "Learn German", but
        "Pass German B2 Goethe Exam by Dec 2027").
      - Must directly move the needle toward your 3-5 year vision.
      - Apply McKeown's 90% Rule: If a candidate goal is only a "good 7/10 or 8/10",
        reject it. Only commit to >= 90% essential goals.

[4] HOW ACTIVE PROJECTS & GROUND TASKS CONNECT:
  * Active Projects (Horizon 1, <12 Months):
      Pick 2 to 4 projects that advance your Top 5 Goals right now (e.g. "Language Exam
      Workbook Unit 1-5" or "Bench Power Supply Prototype Build").
  * Ground Tasks (0 ft Runway):
      During your Weekly Review, look at your Active Projects and slice finishable
      30-minute to 2-hour bite-sized tasks. These tasks pass through Gate 0 and get
      scored by the TPI Engine for daily execution.
""")


def manage_foundation_menu(ws: Dict[str, Any]) -> None:
    """Interactive sub-menu for editing the top-down horizon foundation:
    vision statement, Top 5 goals, active projects, and daily autopilot habits.
    """
    while True:
        print_header("TOP-DOWN HORIZON FOUNDATION & DAILY AUTOPILOT HABITS")

        # --- Current state summary with explicit timeframes ---
        print(f"1. 3-5 Year Vision (Horizon 4-5 | 40k-50k ft)        : {ws['vision_horizon_4_5']}")
        print(f"2. Top 5 Core Goals (Horizon 3 | 30k ft | 1-2 Years)  : {len(ws['top_5_goals'])} set")
        for goal in ws["top_5_goals"]:
            print(f"     * {goal}")
        print(f"3. Active Projects (Horizon 1 | 10k ft | <12 Months)  : {len(ws['active_projects'])} active")
        for project in ws["active_projects"]:
            print(f"     * {project}")
        print(f"4. Fixed Daily Autopilot Habits (Horizon 2 | Baseline): {len(ws['daily_autopilot_habits'])} routines (Executed in sequence)")
        for idx, habit in enumerate(ws["daily_autopilot_habits"], 1):
            badge = " [DO FIRST]" if idx == 1 else ""
            print(f"     [{idx}]{badge} {habit}")

        # --- Options ---
        print("\nOptions:")
        print("  [1] Edit 3-5 Year Vision (Horizon 4-5: Identity, Trajectory & Core Standard)")
        print("  [2] Add / Replace Top 5 Core Goals (Horizon 3: 12-24 Months | Buffett 25/5 Rule)")
        print("  [3] Add / Remove Active Projects (Horizon 1: <12 Months / 2-8 Week Milestones)")
        print("  [4] Manage & Organize Daily Habits (Add, Remove, Reorder which to do first)")
        print("  [H] View Goal-Setting & Horizon Methodology Guide (Research Report Breakdown)")
        print("  [0] Return to Main Menu")

        choice = input("\nSelect option: ").strip().upper()
        if choice in ("0", ""):
            break
        elif choice == "H":
            show_horizon_methodology_guide()
            input("\nPress Enter to return to Foundation Menu...")
        elif choice == "1":
            print("\n--- EDIT 3-5 YEAR VISION (Horizon 4-5 | 40,000 - 50,000 ft) ---")
            print("Timeframe: 3 to 5 Years (anchored by your lifelong purpose & principles).")
            print("Diagnostic Prompt: What specific role, mastery, and benchmark do you want to attain in 3-5 years?")
            print("Template: 'Become a [Role / Mastery Level] achieving [Capstone / Benchmark] while adhering to [Core Standard].'")
            print("Example: 'Become a high-competence Mechatronics & Power Electronics Engineer working internationally.'")
            vision_text = input("\nEnter your 3-5 Year Vision statement: ").strip()
            if vision_text:
                ws["vision_horizon_4_5"] = vision_text
                save_workspace(ws)
                print("  -> Saved 3-5 Year Vision!")
        elif choice == "2":
            print("\n--- TOP 5 CORE GOALS (Horizon 3 | 30,000 ft | 12 to 24 Months) ---")
            print("Timeframe: 1 to 2 Years (set annually, calibrated quarterly).")
            print("Warren Buffett 25/5 Strategy: Pick ONLY the top 5 most critical goals.")
            print("Locke & Latham Specificity: Goals must have concrete, measurable finish lines (NOT vague desires).")
            print("Examples: 'Pass German B2 certification by Q4', 'Draft and submit Engineering Diploma Thesis', 'Build & test 0-30V 5A Bench Power Supply'.")
            print("\nEnter up to 5 Core Goals (press Enter on a blank line when finished):")
            new_goals = []
            for i in range(1, 6):
                goal = input(f"  Goal #{i}: ").strip()
                if not goal:
                    break
                new_goals.append(f"{i}. {goal}")
            if new_goals:
                ws["top_5_goals"] = new_goals
                save_workspace(ws)
                print(f"  -> Saved {len(new_goals)} Core Goals (Horizon 3)!")
        elif choice == "3":
            while True:
                print("\n--- ACTIVE PROJECTS (Horizon 1 | 10,000 ft | Under 12 Months) ---")
                print("Timeframe: Finite multi-step projects (typically 2 to 8 weeks or a single semester).")
                print("These are active focus areas from which you will slice 30-min to 2-hour tasks.")
                print(f"\nCurrent Active Projects ({len(ws['active_projects'])}):")
                if ws["active_projects"]:
                    for idx, project in enumerate(ws["active_projects"], 1):
                        print(f"  [{idx}] {project}")
                else:
                    print("  (No active projects set yet)")
                print("\nOptions:")
                print("  [A] Add Active Project(s) (enter multiple in sequence)")
                print("  [R] Remove a completed Project")
                print("  [0] Done / Return to Foundation Menu")
                sub_choice = input("\nChoice [A/R/0] (default Done): ").strip().upper()
                if sub_choice in ("0", ""):
                    break
                elif sub_choice == "A":
                    print("\nEnter active projects one by one (press Enter on a blank line when done):")
                    added_count = 0
                    while True:
                        project = input(f"  Project #{len(ws['active_projects']) + 1} (or Enter to finish): ").strip()
                        if not project:
                            break
                        ws["active_projects"].append(project)
                        save_workspace(ws)
                        added_count += 1
                        print(f"    + Added: '{project}'")
                    if added_count > 0:
                        print(f"  -> Added {added_count} new project(s)!")
                elif sub_choice == "R":
                    if not ws["active_projects"]:
                        print("  -> No active projects available to remove.")
                        continue
                    for idx, project in enumerate(ws["active_projects"], 1):
                        print(f"    [{idx}] {project}")
                    remove_index = input("  Enter number to remove (or Enter to cancel): ").strip()
                    if remove_index.isdigit() and 1 <= int(remove_index) <= len(ws["active_projects"]):
                        removed = ws["active_projects"].pop(int(remove_index) - 1)
                        save_workspace(ws)
                        print(f"  -> Removed Project: '{removed}'")
        elif choice == "4":
            while True:
                print("\n--- FIXED DAILY AUTOPILOT HABITS (Horizon 2 | 20,000 ft | Ongoing) ---")
                print("Timeframe: Daily / Weekly recurring baseline routines (health, hygiene, review cadences).")
                print("Rule: NEVER scored by math formula -- they protect you from burnout and keep the engine running.")
                print(f"\nCurrent Habits ({len(ws['daily_autopilot_habits'])}):")
                if ws["daily_autopilot_habits"]:
                    for idx, habit in enumerate(ws["daily_autopilot_habits"], 1):
                        badge = " -> [DO FIRST]" if idx == 1 else ""
                        print(f"  [{idx}]{badge} {habit}")
                else:
                    print("  (No habits added yet)")
                print("\nOptions:")
                print("  [A] Add Habit(s) (enter multiple in sequence)")
                print("  [O] Organize / Choose which habit to do first (Reorder sequence)")
                print("  [R] Remove a Habit")
                print("  [0] Done / Return to Foundation Menu")
                sub_choice = input("\nChoice [A/O/R/0] (default Done): ").strip().upper()
                if sub_choice in ("0", ""):
                    break
                elif sub_choice == "A":
                    print("\nEnter daily habits one by one (press Enter on a blank line when done):")
                    added_count = 0
                    while True:
                        habit = input(f"  Habit #{len(ws['daily_autopilot_habits']) + 1} (or Enter to finish): ").strip()
                        if not habit:
                            break
                        ws["daily_autopilot_habits"].append(habit)
                        save_workspace(ws)
                        added_count += 1
                        print(f"    + Added: '{habit}'")
                    if added_count > 0:
                        print(f"  -> Added {added_count} new habit(s)!")
                elif sub_choice == "O":
                    if len(ws["daily_autopilot_habits"]) < 2:
                        print("  -> You need at least 2 habits to reorder/organize.")
                        continue
                    print("\n--- ORGANIZE / REORDER HABIT EXECUTION SEQUENCE ---")
                    print("Choose which habit gets done first, or rearrange the full sequence:")
                    for idx, habit in enumerate(ws["daily_autopilot_habits"], 1):
                        badge = " (Currently #1 - DO FIRST)" if idx == 1 else ""
                        print(f"  [{idx}] {habit}{badge}")
                    print("\nHow would you like to organize?")
                    print("  - Enter a habit number (e.g., '2' or '3') to make that habit #1 (DO FIRST)")
                    print(f"  - OR enter full sequence separated by commas (e.g., '2, 3, 1')")
                    print("  - OR enter 'M' to move an individual habit to a custom position")
                    print("  - Press Enter to cancel")
                    reorder_input = input("\nEnter choice: ").strip()
                    if not reorder_input:
                        continue
                    if reorder_input.isdigit():
                        pick = int(reorder_input)
                        if 1 <= pick <= len(ws["daily_autopilot_habits"]):
                            promoted = ws["daily_autopilot_habits"].pop(pick - 1)
                            ws["daily_autopilot_habits"].insert(0, promoted)
                            save_workspace(ws)
                            print(f"\n  -> SUCCESS: '{promoted}' is now Habit #1 (DO FIRST)!")
                        else:
                            print(f"  -> Invalid habit number: {pick}")
                    elif "," in reorder_input:
                        try:
                            order = [int(p.strip()) for p in reorder_input.split(",") if p.strip()]
                            if sorted(order) == list(range(1, len(ws["daily_autopilot_habits"]) + 1)):
                                ws["daily_autopilot_habits"] = [ws["daily_autopilot_habits"][i - 1] for i in order]
                                save_workspace(ws)
                                print("\n  -> SUCCESS: Habits reordered to new sequence:")
                                for idx, habit in enumerate(ws["daily_autopilot_habits"], 1):
                                    badge = " (DO FIRST)" if idx == 1 else ""
                                    print(f"     [{idx}]{badge} {habit}")
                            else:
                                print(f"  -> Invalid sequence! Must include numbers 1 to {len(ws['daily_autopilot_habits'])} exactly once.")
                        except ValueError:
                            print("  -> Could not parse sequence. Please use numbers separated by commas (e.g. '2, 1, 3').")
                    elif reorder_input.upper() == "M":
                        from_raw = input(f"  Which habit number to move? (1-{len(ws['daily_autopilot_habits'])}): ").strip()
                        to_raw = input(f"  Move to which position? (1-{len(ws['daily_autopilot_habits'])}): ").strip()
                        if from_raw.isdigit() and to_raw.isdigit():
                            from_pos = int(from_raw)
                            to_pos = int(to_raw)
                            if 1 <= from_pos <= len(ws["daily_autopilot_habits"]) and 1 <= to_pos <= len(ws["daily_autopilot_habits"]):
                                moved = ws["daily_autopilot_habits"].pop(from_pos - 1)
                                ws["daily_autopilot_habits"].insert(to_pos - 1, moved)
                                save_workspace(ws)
                                badge = " (DO FIRST)" if to_pos == 1 else ""
                                print(f"\n  -> SUCCESS: Moved '{moved}' to Position #{to_pos}{badge}!")
                            else:
                                print("  -> Position out of range.")
                        else:
                            print("  -> Please enter valid numbers.")
                    else:
                        print("  -> Unrecognized option.")
                elif sub_choice == "R":
                    if not ws["daily_autopilot_habits"]:
                        print("  -> No habits available to remove.")
                        continue
                    for idx, habit in enumerate(ws["daily_autopilot_habits"], 1):
                        print(f"    [{idx}] {habit}")
                    remove_index = input("  Enter number to remove (or Enter to cancel): ").strip()
                    if remove_index.isdigit() and 1 <= int(remove_index) <= len(ws["daily_autopilot_habits"]):
                        removed = ws["daily_autopilot_habits"].pop(int(remove_index) - 1)
                        save_workspace(ws)
                        print(f"  -> Removed Habit: '{removed}'")


# =====================================================================
# MENU [6]: VIEW WAITING VAULT, AVOID LIST & RCF HISTORY
# =====================================================================

def view_vaults_and_history(ws: Dict[str, Any]) -> None:
    """Display the contents of all archival lists: waiting vault,
    Buffett 25/5 avoid list, and RCF completed task history.
    """
    print_header("WAITING VAULT, AVOID-AT-ALL-COSTS LIST & RCF HISTORY")

    print("\n1. WAITING / NEXT MONTH VAULT (Budget or Resource Constrained):")
    if ws["waiting_next_month"]:
        for item in ws["waiting_next_month"]:
            print(f"   * {item['name']} (Unlocks: {item['reason']})")
    else:
        print("   (Empty)")

    print("\n2. BUFFETT 25/5 AVOID-AT-ALL-COSTS LIST (Quarantined Goals 6-25):")
    if ws["avoid_25_5_list"]:
        for item in ws["avoid_25_5_list"]:
            print(f"   * {item}")
    else:
        print("   (Empty)")

    print("\n3. REFERENCE CLASS FORECASTING (RCF) COMPLETED TASK LOG:")
    if ws["rcf_history"]:
        for idx, entry in enumerate(ws["rcf_history"], 1):
            print(
                f"   [{idx}] [{entry['completed_at']}] {entry['name']} | "
                f"Estimated Fib: {entry['estimated_fib']} -> ACTUAL Fib: {entry['actual_fib']} ({entry['actual_notes']})"
            )
        print("\n  Task History Actions: [D] Delete an entry | [C] Clear all history | [Enter] Continue")
        sub_choice = input("  Select action: ").strip().lower()
        if sub_choice == "d":
            entry_input = input(f"  Enter entry number to delete (1-{len(ws['rcf_history'])}) or Enter to cancel: ").strip()
            if entry_input.isdigit() and 1 <= int(entry_input) <= len(ws["rcf_history"]):
                target_idx = int(entry_input) - 1
                target_entry = ws["rcf_history"][target_idx]
                confirm = prompt_yes_no(
                    f"  [Type 1 Decision Warning - Research Doc p. 6 & 18] Deleting baseline data removes empirical RCF calibration.\n"
                    f"  Are you sure you want to delete '{target_entry['name']}'?"
                )
                if confirm:
                    removed = ws["rcf_history"].pop(target_idx)
                    save_workspace(ws)
                    print(f"  -> Deleted task history record: '{removed['name']}'")
        elif sub_choice == "c":
            confirm = prompt_yes_no(
                f"  [Type 1 Decision Warning - Research Doc p. 6 & 18] Clear ALL {len(ws['rcf_history'])} historical RCF task entries?\n"
                f"  This eliminates empirical anchors for Reference Class Forecasting."
            )
            if confirm:
                count = len(ws["rcf_history"])
                ws["rcf_history"] = []
                save_workspace(ws)
                print(f"  -> Cleared all {count} task history records.")
    else:
        print("   (No completed tasks logged yet.)")


# =====================================================================
# MENU [7]: CONFIGURE PRE-FIXED WEIGHTS (CRITERIA CLARITY PROTOCOL)
# =====================================================================

def configure_weights_menu(ws: Dict[str, Any]) -> None:
    """Allow the user to set TPI formula weights: balanced (WSJF default)
    or hierarchical (custom 1-5 per criterion) per the Criteria Clarity Protocol.
    """
    print_header("CRITERIA CLARITY PROTOCOL: CONFIGURE PRE-FIXED WEIGHTS")
    print("  [1] Balanced Mode (Default WSJF): W1=1, W2=1, W3=1, W4=1")
    print("  [2] Hierarchical Mode: Custom pre-fixed weights (1 to 5)")
    mode = input("\nSelect [1 or 2]: ").strip()
    if mode == "1":
        ws["weights"] = {"w1": 1.0, "w2": 1.0, "w3": 1.0, "w4": 1.0}
    elif mode == "2":
        ws["weights"] = {
            "w1": float(prompt_score_selection("  W1 - Strategic Alignment (Why_Align)", [1, 2, 3, 4, 5])),
            "w2": float(prompt_score_selection("  W2 - Direct Value (Value_Impact)", [1, 2, 3, 4, 5])),
            "w3": float(prompt_score_selection("  W3 - Time Criticality (Urgency_CoD)", [1, 2, 3, 4, 5])),
            "w4": float(prompt_score_selection("  W4 - Domino Leverage (Leverage_RR/OE)", [1, 2, 3, 4, 5]))
        }
    recalculate_all_tpi_scores(ws)
    print("  -> Weights updated and all active task TPI scores recalculated!")


def history_tree_menu(ws: Dict[str, Any]) -> None:
    """CLI interface to view History Tree, save manual checkpoints, or restore past nodes."""
    tree = load_history_tree(ws)
    print_header("TWO-WAY DOOR HISTORY TREE & CHECKPOINT VAULT")
    print("Jeff Bezos Reversibility Filter (p. 6): Macro branching time-travel.")
    print(f"Total Checkpoints in Tree: {len(tree['nodes'])} | Current Head: {tree.get('current_node_id')}\n")

    sorted_nodes = sorted(tree["nodes"].values(), key=lambda n: n.get("timestamp", ""), reverse=True)
    for idx, node in enumerate(sorted_nodes, 1):
        is_cur = "● [ACTIVE HEAD]" if node["id"] == tree.get("current_node_id") else "○"
        m = node.get("metrics", {})
        m_str = f"{m.get('active_tasks', 0)} tasks, {m.get('top_5_goals', 0)} goals, {m.get('habits', 0)} habits, {m.get('rcf_history', 0)} RCF"
        print(f"  [{idx}] {is_cur} {node.get('timestamp')} | {node.get('title')} [{node.get('tag')}] ({m_str})")
        if node.get("reason"):
            print(f"       Context: {node.get('reason')}")

    print("\nOptions: [R] Restore a checkpoint | [C] Create new checkpoint | [B] Restore from .bak | [Enter] Return")
    choice = input("Select an option: ").strip().lower()
    if choice == "c":
        title = input("Enter checkpoint title: ").strip() or f"Manual Snapshot -- {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        reason = input("Enter context / notes (optional): ").strip()
        commit_history_node(tree, ws, title=title, tag="MANUAL", reason=reason)
        print("  -> Checkpoint committed to History Tree!")
    elif choice == "r":
        num = input(f"Enter number to restore (1-{len(sorted_nodes)}): ").strip()
        if num.isdigit() and 1 <= int(num) <= len(sorted_nodes):
            target = sorted_nodes[int(num) - 1]
            confirm = prompt_yes_no(f"Restore workspace to '{target['title']}' ({target['timestamp']})?")
            if confirm:
                restored = restore_history_node(tree, target["id"], ws)
                if restored:
                    ws.clear()
                    ws.update(restored)
                    save_workspace(ws)
                    print(f"  -> SUCCESS: Restored workspace to '{target['title']}'!")
                    display_dashboard(ws)
    elif choice == "b":
        restored = restore_backup()
        if restored:
            ws.clear()
            ws.update(restored)
            print("\n  -> SUCCESS: Restored previous workspace state from backup!")
            display_dashboard(ws)


# =====================================================================
# MENU [9]: END-OF-DAY HABIT REVIEW & VISUAL ANALYTICS (CLI)
# =====================================================================

def end_of_day_habit_review_cli(ws: Dict[str, Any]) -> None:
    """CLI interactive flow for end-of-day habit batch review and reflection."""
    print_header("END-OF-DAY HABIT BATCH REVIEW & REFLECTION")
    print("Scientific Principle (Mark 2008 & Research Report):")
    print("Checking habits throughout the day causes ~20+ mins of context-switching recovery per interruption.")
    print("Batching habit review to the end of the day preserves deep focus during peak hours.\n")
    
    habits = ws.get("daily_autopilot_habits", [])
    if not habits:
        print("  (No daily habits configured. Add habits in Menu 5 first!)")
        return
        
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"Date of Review: {today_str}")
    target_date = input(f"Review for today ({today_str}) or enter past date (YYYY-MM-DD): ").strip() or today_str
    
    existing_entry = ws.get("habit_history", {}).get(target_date, {})
    previously_done = existing_entry.get("completed", [])
    
    print("\nCheck off the routines you completed today:")
    completed = []
    for idx, habit in enumerate(habits, 1):
        badge = " [DO FIRST - Morning Anchor]" if idx == 1 else ""
        default_val = "y" if habit in previously_done else "n"
        ans = input(f"  [{idx}]{badge} Did you finish '{habit}'? [y/n] (default {default_val}): ").strip().lower()
        if not ans:
            ans = default_val
        if ans in ("y", "yes"):
            completed.append(habit)
            
    notes = input("\nOptional evening reflection notes / wins / obstacles: ").strip()
    entry = log_habit_review(ws, target_date, completed, notes)
    
    print(f"\n  -> SUCCESS: Recorded End-of-Day Review for {target_date}!")
    print(f"     Completed: {entry['completed_count']}/{entry['total']} ({entry['rate']*100:.0f}%)")
    streaks = calculate_habit_streaks(ws)
    print(f"     Current Consistency Streak: {streaks['current_streak']} days | Best: {streaks['best_streak']} days")


def display_habit_analytics_cli(ws: Dict[str, Any]) -> None:
    """CLI ASCII graphs, trend analysis, and research-backed habit diagnostics."""
    print_header("HORIZON 2 HABIT ANALYTICS & TREND VISUALIZATION")
    analytics = calculate_habit_analytics(ws, days=14)
    
    print(f"Analyzed Period: Last 14 Days | Logged Days: {analytics['logged_days']}")
    print(f"Average Completion Rate: {analytics['avg_completion_rate']*100:.1f}% | 7-Day Rate: {analytics['avg_7_day_rate']*100:.1f}%")
    print(f"Current Streak: {analytics['current_streak']} days | Best Streak: {analytics['best_streak']} days")
    print(f"Attention Time Saved: ~{analytics['time_saved_mins_per_day']} mins/day by avoiding mid-day habit disruptions")
    
    print("\n--- 14-DAY COMPLETION RATE GRAPH ---")
    for r in analytics["daily_records"]:
        bar_len = int(r["rate"] * 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        status = f"{r['rate']*100:>3.0f}% ({len(r['completed'])}/{r['total']})" if r["is_logged"] else "Unlogged"
        print(f"  {r['date']} [{r['day_name']}] | [{bar}] {status}")
        
    print("\n--- HABIT-BY-HABIT ADHERENCE BREAKDOWN ---")
    for h in analytics["habit_breakdown"]:
        first_badge = " [DO FIRST]" if h["is_first"] else ""
        bar_len = int(h["rate"] * 15)
        bar = "█" * bar_len + "-" * (15 - bar_len)
        print(f"  [{h['index']}]{first_badge} {h['name'][:40]:<40} : [{bar}] {h['completed_count']:>2}/{h['total_days']:<2} ({h['rate']*100:>3.0f}%) - {h['tier']}")
        
    if analytics["strategic_withdrawal_alerts"]:
        print("\n--- [!] RESEARCH RECOMMENDATIONS (Page 19: Strategic Withdrawal) ---")
        for alert in analytics["strategic_withdrawal_alerts"]:
            print(f"  * Routine '{alert['habit']}': {alert['reason']}")
            print(f"    -> {alert['recommendation']}")
            
    print("\nOptions:")
    print("  [R] Perform End-of-Day Review (Log habits now)")
    print("  [D] Delete a specific date's habit log")
    print("  [P] Purge past demo/test logs (keep today)")
    print("  [C] Clear ALL habit history records")
    print("  [S] Seed 14-Day Sample History (Demo visualization)")
    print("  [T] Test Windows Toast Notification")
    print("  [0] Return to Main Menu")
    
    sub = input("\nSelect [R/D/P/C/S/T/0]: ").strip().upper()
    if sub == "R":
        end_of_day_habit_review_cli(ws)
    elif sub == "D":
        del_date = input("Enter date to delete (YYYY-MM-DD): ").strip()
        if del_date in ws.get("habit_history", {}):
            if prompt_yes_no(f"Permanently delete habit record for '{del_date}'?"):
                delete_habit_log(ws, del_date)
                print(f"  -> Deleted habit log for {del_date}!")
        else:
            print(f"  -> No habit log found for date '{del_date}'.")
    elif sub == "P":
        if prompt_yes_no("Purge all past demo/test logs prior to today?"):
            purged = purge_past_habit_history(ws, keep_today=True)
            print(f"  -> Purged {purged} past habit records!")
    elif sub == "C":
        if prompt_yes_no("Are you sure you want to CLEAR ALL habit history records?"):
            deleted_count = clear_all_habit_history(ws)
            print(f"  -> Cleared {deleted_count} habit records!")
    elif sub == "S":
        seed_demo_habit_history(ws, 14)
        print("  -> Seeded 14 days of demo habit history! Run [9] again to see the graphs.")
    elif sub == "T":
        ok = send_system_notification("TPI Habit Review Reminder", "Evening batch review: log your daily autopilot habits!")
        print(f"  -> Notification sent: {'Success' if ok else 'Fallback / check Windows settings'}")


# =====================================================================
# MAIN PERSISTENT APPLICATION LOOP
# =====================================================================

def main() -> None:
    """Entry point: load workspace, display dashboard, and run the main menu loop."""
    ws = load_workspace()
    display_dashboard(ws)

    while True:
        print("\n" + "=" * 78)
        print(" TPI PERSISTENT COMMAND CENTER -- MAIN MENU")
        print("=" * 78)
        print("  [1] View Dashboard & Today's Execution Plan (Habits + #1 Frog + 1-3-5 List)")
        print("  [2] Add Tasks -> Gate 0 & TPI Scoring (Mid-Week Single Homework OR Weekly Batch)")
        print("  [3] Complete a Task & Log Actual Time (Builds RCF Historical Memory)")
        print("  [4] Weekly Review: Update Urgency Scores & Unlock Next-Month Budget Vault")
        print("  [5] Manage Top-Down Foundation (Vision, Top 5 Goals, Projects, Daily Habits)")
        print("  [6] View Waiting Vault, 25/5 Avoid List & RCF Completed History")
        print("  [7] Configure Pre-Fixed TPI Weights (W1-W4)")
        print("  [8] History Tree & Checkpoint Vault (Branching Timeline / Restore Past States)")
        print("  [9] End-of-Day Habit Review & Analytics (Log Today's Habits, View Streaks & Graphs)")
        print("  [0] Save & Exit")

        choice = input("\nSelect an option [0-9]: ").strip()
        if choice == "1":
            display_dashboard(ws)
        elif choice == "2":
            add_tasks_menu(ws)
        elif choice == "3":
            complete_task_menu(ws)
        elif choice == "4":
            weekly_review_menu(ws)
        elif choice == "5":
            manage_foundation_menu(ws)
        elif choice == "6":
            view_vaults_and_history(ws)
        elif choice == "7":
            configure_weights_menu(ws)
        elif choice == "8":
            history_tree_menu(ws)
        elif choice == "9":
            display_habit_analytics_cli(ws)
        elif choice == "0":
            save_workspace(ws)
            print(f"\nAll data saved to '{DATA_FILE}'. See you next session!")
            break
        else:
            print("  -> Please enter a number from 0 to 9.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSession closed safely.")
        sys.exit(0)