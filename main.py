#!/usr/bin/env python3
"""
TRUE PRIORITY INDEX (TPI) CROSS-PLATFORM APPLICATION (Flet / Flutter)
Implements 100% of the functions from tpi_evaluator.py & Research Report Architecture:
- Top-Down Horizon Mapping (Vision -> Top 5 Goals -> Active Projects -> Weekly Tasks)
- Gate 0 Binary Filter (Habit Guardrail, 2-Min Rule, Type 2 Door, Budget Lock & $0 Prep Split, 25/5, 90% Rule)
- Layer 1 Scoring Engine (Vertical Batch & Single Mode, Fibonacci Anchors, Task Decomposition if Dur >= 20)
- Layer 2 Daily Command Dashboard (Fixed Autopilot Habits with #1 DO FIRST, #1 Frog, 1-3-5 Schedule)
- Weekly Review (Budget Vault Unlock, Type 2 Review & Rollback, Urgency Shift 1->13)
- Reference Class Forecasting (RCF) Historical Memory Logging
- Pre-Fixed Weights Configuration (Criteria Clarity Protocol)
- Full Altitude Map & Methodology Guide
"""

import copy
import os
import sys
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import flet as ft

# Import core business logic, constants, rubrics, and storage from tpi_evaluator
import tpi_evaluator

DATA_FILE = tpi_evaluator.DATA_FILE
RUBRICS = tpi_evaluator.RUBRICS


# =====================================================================
# STORAGE & WORKSPACE HELPERS
# =====================================================================

def get_workspace() -> Dict[str, Any]:
    """Load the workspace safely without CLI blocking."""
    return tpi_evaluator.load_workspace(interactive=False)


def persist_workspace(ws: Dict[str, Any]) -> None:
    """Save workspace to disk with sorted active tasks."""
    tpi_evaluator.save_workspace(ws)


def compute_tpi_val(task: Dict[str, Any], weights: Dict[str, float]) -> float:
    """Calculate TPI score."""
    return tpi_evaluator.compute_tpi(task, weights)


def get_review_cadence_dates() -> Dict[str, str]:
    """Calculate standard cadences from the research report."""
    now = datetime.now()
    days_to_fri = (4 - now.weekday()) % 7
    if days_to_fri == 0:
        days_to_fri = 7
    fri_date = (now + timedelta(days=days_to_fri)).strftime("%Y-%m-%d")

    days_to_sun = (6 - now.weekday()) % 7
    if days_to_sun == 0:
        days_to_sun = 7
    sun_date = (now + timedelta(days=days_to_sun)).strftime("%Y-%m-%d")

    tomorrow_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    week_date = (now + timedelta(days=7)).strftime("%Y-%m-%d")
    two_weeks_date = (now + timedelta(days=14)).strftime("%Y-%m-%d")

    return {
        "Next Friday (Weekly Review)": fri_date,
        "Next Sunday (Weekly Review)": sun_date,
        "Tomorrow (Daily Triage)": tomorrow_date,
        "In 7 Days (1-Week Sprint)": week_date,
        "In 14 Days (2-Week Sprint)": two_weeks_date,
    }


# =====================================================================
# MAIN APPLICATION
# =====================================================================

def main(page: ft.Page):
    # Window and page configuration
    page.title = "True Priority Index (TPI) Command Center"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0

    # Load workspace
    ws: Dict[str, Any] = get_workspace()

    # Load persistent History Tree (Macro Reversibility Filter & Time-Travel)
    history_tree: Dict[str, Any] = tpi_evaluator.load_history_tree(ws)

    # Active view index
    current_nav_index = 0

    # Background end-of-day habit notification watcher
    watcher_stop_event = threading.Event()

    def habit_notification_watcher():
        while not watcher_stop_event.is_set():
            try:
                now = datetime.now()
                today_str = now.strftime("%Y-%m-%d")
                habit_settings = ws.get("habit_settings", {})
                if habit_settings.get("enable_notifications", True):
                    review_time_str = habit_settings.get("review_time", "21:00")
                    cur_time_str = now.strftime("%H:%M")
                    if cur_time_str >= review_time_str:
                        last_notified = habit_settings.get("last_notified_date", "")
                        today_logged = today_str in ws.get("habit_history", {})
                        if last_notified != today_str and not today_logged:
                            ok = tpi_evaluator.send_system_notification(
                                "TPI End-of-Day Habit Review",
                                "Time for your daily reflection! Open the app to log your daily autopilot habits."
                            )
                            if ok:
                                habit_settings["last_notified_date"] = today_str
                                persist_workspace(ws)
            except Exception:
                pass
            time.sleep(30)

    watcher_thread = threading.Thread(target=habit_notification_watcher, daemon=True)
    watcher_thread.start()

    # Undo & Redo History Stacks (Supports multi-level rollback with descriptions & timestamps)
    undo_stack: List[Dict[str, Any]] = []
    redo_stack: List[Dict[str, Any]] = []

    def push_undo_state(description: str = "Action"):
        undo_stack.append({
            "workspace": copy.deepcopy(ws),
            "description": description,
            "time": datetime.now().strftime("%H:%M:%S"),
        })
        if len(undo_stack) > 50:
            undo_stack.pop(0)
        redo_stack.clear()

    def undo():
        if not undo_stack:
            toast("Nothing to undo.", is_error=True)
            return
        entry = undo_stack.pop()
        prev_state = entry["workspace"] if isinstance(entry, dict) and "workspace" in entry else entry
        desc = entry.get("description", "previous action") if isinstance(entry, dict) else "previous action"
        redo_stack.append({
            "workspace": copy.deepcopy(ws),
            "description": desc,
            "time": datetime.now().strftime("%H:%M:%S"),
        })
        ws.clear()
        ws.update(prev_state)
        persist_workspace(ws)
        toast(f"Undone: Reverted {desc}.")
        render_main()

    def redo():
        if not redo_stack:
            toast("Nothing to redo.", is_error=True)
            return
        entry = redo_stack.pop()
        next_state = entry["workspace"] if isinstance(entry, dict) and "workspace" in entry else entry
        desc = entry.get("description", "action") if isinstance(entry, dict) else "action"
        undo_stack.append({
            "workspace": copy.deepcopy(ws),
            "description": desc,
            "time": datetime.now().strftime("%H:%M:%S"),
        })
        ws.clear()
        ws.update(next_state)
        persist_workspace(ws)
        toast(f"Redone: Re-applied {desc}.")
        render_main()

    def rollback_to_index(target_idx: int):
        nonlocal undo_stack
        if target_idx < 0 or target_idx >= len(undo_stack):
            return
        entry = undo_stack[target_idx]
        target_state = entry["workspace"] if isinstance(entry, dict) and "workspace" in entry else entry
        desc = entry.get("description", "checkpoint") if isinstance(entry, dict) else "checkpoint"
        redo_stack.append({
            "workspace": copy.deepcopy(ws),
            "description": f"State before rollback to {desc}",
            "time": datetime.now().strftime("%H:%M:%S"),
        })
        ws.clear()
        ws.update(target_state)
        undo_stack = undo_stack[:target_idx]
        persist_workspace(ws)
        close_dialog()
        toast(f"Rolled back to state before: '{desc}'.")
        render_main()

    # Keyboard shortcuts: Ctrl+Z (Undo) and Ctrl+Y / Ctrl+Shift+Z (Redo)
    def handle_keyboard(e: ft.KeyboardEvent):
        if e.ctrl and e.key.lower() == "z":
            if e.shift:
                redo()
            else:
                undo()
        elif e.ctrl and e.key.lower() == "y":
            redo()

    page.on_keyboard_event = handle_keyboard

    # Helper: Show Floating Toast with auto-dismiss (4s), explicit close (X), and UNDO
    def toast(msg: str, is_error: bool = False, action: Optional[str] = None, on_action=None):
        def handle_dismiss(e):
            if sb in page.overlay:
                page.overlay.remove(sb)
            sb.open = False
            try:
                page.update()
            except Exception:
                pass

        def handle_action(e):
            if sb in page.overlay:
                page.overlay.remove(sb)
            sb.open = False
            try:
                page.update()
            except Exception:
                pass
            if on_action:
                on_action(e)

        # Remove prior snackbars so they never accumulate or re-open on page update
        for old_c in list(page.overlay):
            if isinstance(old_c, ft.SnackBar):
                old_c.open = False
                page.overlay.remove(old_c)

        sb = ft.SnackBar(
            content=ft.Row(
                [
                    ft.Icon(
                        ft.Icons.ERROR_OUTLINE if is_error else ft.Icons.CHECK_CIRCLE,
                        color=ft.Colors.RED_300 if is_error else ft.Colors.GREEN_300,
                        size=20,
                    ),
                    ft.Text(msg, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500, expand=True, size=13),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=10,
            ),
            bgcolor=ft.Colors.RED_900 if is_error else ft.Colors.SURFACE_CONTAINER_HIGHEST,
            behavior=ft.SnackBarBehavior.FLOATING,
            duration=ft.Duration(seconds=4),
            persist=False,
            show_close_icon=True,
            close_icon_color=ft.Colors.GREY_300,
            action=action,
            on_action=handle_action if action else None,
            on_dismiss=handle_dismiss,
            open=True,
            margin=16,
            elevation=6,
        )
        page.overlay.append(sb)
        page.update()

        # Background watchdog to guarantee dismissal and removal from page.overlay even if events lag
        def auto_cleanup():
            time.sleep(4.5)
            if sb in page.overlay:
                page.overlay.remove(sb)
                sb.open = False
                try:
                    page.update()
                except Exception:
                    pass

        threading.Thread(target=auto_cleanup, daemon=True).start()

    # Helper: Show Alert Dialog
    def show_dialog(title: str, content: ft.Control, actions: Optional[List[ft.Control]] = None):
        if actions is None:
            actions = [ft.FilledButton("Close", on_click=lambda e: close_dialog())]
        dlg = ft.AlertDialog(
            title=ft.Text(title, weight=ft.FontWeight.BOLD),
            content=content,
            actions=actions,
        )
        page.show_dialog(dlg)
        page.update()

    def close_dialog():
        page.pop_dialog()
        page.update()

    # Helper: Open Rollback & History Log Dialog (Bezos Two-Way Door)
    def open_history_rollback_dialog():
        if not undo_stack:
            content = ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.HISTORY, size=48, color=ft.Colors.GREY_500),
                        ft.Text("No action history in this session yet.", italic=True, size=14),
                        ft.Text("Actions you take (adding, completing, deleting) will appear here.", size=12, color=ft.Colors.GREY_400),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                ),
                padding=24,
                width=500,
            )
            show_dialog("Action History & Rollback", content)
            return

        history_rows = []
        for i in reversed(range(len(undo_stack))):
            entry = undo_stack[i]
            desc = entry.get("description", "Action") if isinstance(entry, dict) else "Action"
            t_str = entry.get("time", "") if isinstance(entry, dict) else ""
            is_latest = (i == len(undo_stack) - 1)

            history_rows.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.RADIO_BUTTON_CHECKED if is_latest else ft.Icons.RESTORE_ROUNDED,
                                color=ft.Colors.PRIMARY if is_latest else ft.Colors.GREY_400,
                                size=20,
                            ),
                            ft.Column(
                                [
                                    ft.Text(desc, weight=ft.FontWeight.W_500, size=13),
                                    ft.Text(f"Recorded at {t_str}" if t_str else f"Step #{i+1}", size=11, color=ft.Colors.GREY_400),
                                ],
                                expand=True,
                                spacing=2,
                            ),
                            ft.FilledTonalButton(
                                "Undo (Ctrl+Z)" if is_latest else "Revert Here",
                                icon=ft.Icons.UNDO,
                                on_click=lambda e, idx=i: rollback_to_index(idx),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH if is_latest else ft.Colors.SURFACE_CONTAINER,
                    padding=10,
                    border_radius=8,
                )
            )

        content = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Two-Way Door: Action History & Instant Rollback", weight=ft.FontWeight.BOLD, size=16),
                    ft.Text(
                        "Jeff Bezos Reversibility Filter (Research Doc p. 6): Every action is an easily reversible Two-Way Door. "
                        "You can undo step-by-step or jump directly back to any historical point below.",
                        size=12,
                        color=ft.Colors.GREY_300,
                    ),
                    ft.Divider(),
                    ft.Container(content=ft.Column(history_rows, scroll=ft.ScrollMode.AUTO, spacing=8), height=320),
                ],
                spacing=10,
            ),
            width=540,
        )
        actions = [
            ft.TextButton("Close", on_click=lambda e: close_dialog()),
            ft.FilledButton("Undo Last Action (Ctrl+Z)", icon=ft.Icons.UNDO, on_click=lambda e: (close_dialog(), undo())),
        ]
        show_dialog("Action History & Rollback", content, actions)

    # =================================================================
    # PERSISTENT HISTORY TREE & CHECKPOINT VAULT (MACRO TIME TRAVEL)
    # =================================================================

    def open_create_checkpoint_dialog():
        title_tf = ft.TextField(
            label="Checkpoint Title",
            value=f"Snapshot -- {datetime.now().strftime('%b %d, %H:%M')}",
            autofocus=True,
        )
        reason_tf = ft.TextField(
            label="Reason / Notes (Optional)",
            hint_text="e.g. Before restructuring Q4 engineering goals",
        )

        def save_checkpoint(e):
            title = title_tf.value.strip() or f"Manual Snapshot -- {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            reason = reason_tf.value.strip()
            node_id = tpi_evaluator.commit_history_node(
                history_tree, ws, title=title, tag="MANUAL", reason=reason
            )
            close_dialog()
            toast(f"Saved Checkpoint: '{title}' into History Tree.")
            open_history_tree_dialog()

        dlg_content = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Create Named Checkpoint (Snapshot)", weight=ft.FontWeight.BOLD, size=16),
                    ft.Text(
                        "Freeze the current workspace state into the persistent History Tree. "
                        "You can restore back to this exact point at any time, even across sessions.",
                        size=12,
                        color=ft.Colors.GREY_300,
                    ),
                    title_tf,
                    reason_tf,
                ],
                spacing=14,
            ),
            width=480,
        )
        actions = [
            ft.TextButton("Cancel", on_click=lambda e: (close_dialog(), open_history_tree_dialog())),
            ft.FilledButton("Save Checkpoint", icon=ft.Icons.SAVE, on_click=save_checkpoint),
        ]
        show_dialog("New Checkpoint", dlg_content, actions)

    def inspect_snapshot_dialog(node: Dict[str, Any]):
        snapshot = node.get("workspace_snapshot", {})
        m = node.get("metrics", {})
        
        vision = snapshot.get("vision_horizon_4_5", "None")
        goals = snapshot.get("top_5_goals", [])
        projects = snapshot.get("active_projects", [])
        habits = snapshot.get("daily_autopilot_habits", [])
        active_tasks = snapshot.get("active_tasks", [])
        rcf_logs = snapshot.get("rcf_history", [])

        details_col = ft.Column(
            [
                ft.Text(f"Snapshot: {node.get('title')}", weight=ft.FontWeight.BOLD, size=15),
                ft.Text(f"Timestamp: {node.get('timestamp')} | Branch: {node.get('branch', 'main')}", size=12, color=ft.Colors.GREY_400),
                ft.Divider(),
                ft.Text("3-5 Year Vision:", weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY),
                ft.Text(vision if vision else "(None)", italic=not bool(vision)),
                ft.Text(f"Top Goals ({len(goals)}):", weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY),
                ft.Column([ft.Text(f"• {g}") for g in goals] if goals else [ft.Text("(Empty)", italic=True)]),
                ft.Text(f"Active Projects ({len(projects)}):", weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY),
                ft.Column([ft.Text(f"• {p}") for p in projects] if projects else [ft.Text("(Empty)", italic=True)]),
                ft.Text(f"Daily Habits ({len(habits)}):", weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY),
                ft.Column([ft.Text(f"• {h}") for h in habits] if habits else [ft.Text("(Empty)", italic=True)]),
                ft.Text(f"Active Tasks ({len(active_tasks)}):", weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY),
                ft.Column([ft.Text(f"• [{t.get('tpi_score', 0):.2f} TPI] {t['name']}") for t in active_tasks] if active_tasks else [ft.Text("(Empty)", italic=True)]),
                ft.Text(f"RCF Completed Tasks ({len(rcf_logs)}):", weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY),
                ft.Column([ft.Text(f"• [{r.get('completed_at')}] {r['name']} (Est {r.get('estimated_fib')} -> Act {r.get('actual_fib')})") for r in rcf_logs] if rcf_logs else [ft.Text("(Empty)", italic=True)]),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=8,
        )

        content = ft.Container(content=details_col, width=580, height=420)
        actions = [
            ft.TextButton("Back to History Tree", on_click=lambda e: (close_dialog(), open_history_tree_dialog())),
            ft.FilledButton(
                "Restore This Snapshot",
                icon=ft.Icons.RESTORE_ROUNDED,
                on_click=lambda e: confirm_restore_node_dialog(node["id"]),
            ),
        ]
        show_dialog(f"Snapshot Details: {node.get('title')[:30]}", content, actions)

    def confirm_restore_node_dialog(target_node_id: str):
        if target_node_id not in history_tree["nodes"]:
            return
        target_node = history_tree["nodes"][target_node_id]

        def do_restore(e):
            push_undo_state(f"Restored checkpoint: '{target_node['title']}'")
            restored_ws = tpi_evaluator.restore_history_node(history_tree, target_node_id, ws)
            if restored_ws:
                ws.clear()
                ws.update(restored_ws)
                persist_workspace(ws)
            close_dialog()
            toast(f"Switched workspace to checkpoint: '{target_node['title']}'", action="UNDO", on_action=lambda e: undo())
            render_main()

        content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(f"Restore workspace to '{target_node['title']}'?", weight=ft.FontWeight.BOLD, size=15),
                    ft.Text(f"Created: {target_node['timestamp']} | Branch: {target_node.get('branch', 'main')}", size=12, color=ft.Colors.GREY_300),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.CYAN_300),
                                ft.Text(
                                    "Two-Way Door Guarantee (Research Doc p. 6):\n"
                                    "Your current workspace state will be committed as a safety checkpoint "
                                    "in the History Tree before restoring. You can return back at any time.\n\n"
                                    "Micro-undo (Ctrl+Z) will also allow you to immediately step back.",
                                    size=12,
                                    color=ft.Colors.CYAN_100,
                                    expand=True,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                        padding=12,
                        border_radius=8,
                    ),
                ],
                spacing=12,
            ),
            width=500,
        )
        actions = [
            ft.TextButton("Cancel", on_click=lambda e: (close_dialog(), open_history_tree_dialog())),
            ft.FilledButton(
                "Confirm Restore",
                icon=ft.Icons.RESTORE_PAGE,
                style=ft.ButtonStyle(bgcolor=ft.Colors.CYAN_800),
                on_click=do_restore,
            ),
        ]
        show_dialog("Restore Checkpoint", content, actions)

    def open_history_tree_dialog():
        current_id = history_tree.get("current_node_id", "node_root")
        nodes_list = sorted(
            history_tree["nodes"].values(),
            key=lambda n: n.get("timestamp", ""),
            reverse=True,
        )

        timeline_cards = []
        for n in nodes_list:
            is_current = (n["id"] == current_id)
            tag = n.get("tag", "MANUAL")
            
            tag_color = ft.Colors.BLUE_900
            if tag == "TYPE 1 SAFEGUARD":
                tag_color = ft.Colors.RED_900
            elif tag == "WEEKLY REVIEW":
                tag_color = ft.Colors.AMBER_900
            elif tag == "AUTO":
                tag_color = ft.Colors.GREY_800

            m = n.get("metrics", {})
            metrics_row = ft.Row(
                [
                    ft.Chip(label=ft.Text(f"{m.get('active_tasks', 0)} Tasks", size=10)),
                    ft.Chip(label=ft.Text(f"{m.get('top_5_goals', 0)} Goals", size=10)),
                    ft.Chip(label=ft.Text(f"{m.get('active_projects', 0)} Projects", size=10)),
                    ft.Chip(label=ft.Text(f"{m.get('habits', 0)} Habits", size=10)),
                    ft.Chip(label=ft.Text(f"{m.get('rcf_history', 0)} History", size=10)),
                ],
                spacing=4,
                wrap=True,
            )

            card_border = ft.Border.all(2, ft.Colors.PRIMARY) if is_current else None

            action_buttons = (
                ft.Row(
                    [
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_400, size=18),
                        ft.Text("Active Head (Current Workspace)", color=ft.Colors.GREEN_300, weight=ft.FontWeight.BOLD, size=12),
                    ],
                    spacing=6,
                )
                if is_current
                else ft.Row(
                    [
                        ft.FilledTonalButton(
                            "Restore / Jump Here",
                            icon=ft.Icons.RESTORE_ROUNDED,
                            on_click=lambda e, nid=n["id"]: confirm_restore_node_dialog(nid),
                        ),
                        ft.OutlinedButton(
                            "Inspect Details",
                            icon=ft.Icons.VISIBILITY_OUTLINED,
                            on_click=lambda e, node_item=n: inspect_snapshot_dialog(node_item),
                        ),
                    ],
                    spacing=8,
                )
            )

            timeline_cards.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Row(
                                        [
                                            ft.Icon(
                                                ft.Icons.RADIO_BUTTON_CHECKED if is_current else ft.Icons.RADIO_BUTTON_UNCHECKED,
                                                color=ft.Colors.PRIMARY if is_current else ft.Colors.GREY_400,
                                                size=16,
                                            ),
                                            ft.Text(
                                                "● CURRENT HEAD" if is_current else "○ Checkpoint",
                                                weight=ft.FontWeight.BOLD,
                                                size=12,
                                                color=ft.Colors.PRIMARY if is_current else ft.Colors.GREY_300,
                                            ),
                                            ft.Chip(label=ft.Text(f"🌿 {n.get('branch', 'main')}", size=10)),
                                            ft.Chip(label=ft.Text(tag, size=10), bgcolor=tag_color),
                                        ],
                                        spacing=8,
                                    ),
                                    ft.Text(n.get("timestamp", ""), size=11, color=ft.Colors.GREY_400),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Text(n.get("title", "Checkpoint"), weight=ft.FontWeight.BOLD, size=14),
                            ft.Text(f"Context: {n.get('reason')}", size=11, italic=True, color=ft.Colors.GREY_300) if n.get("reason") else ft.Container(),
                            metrics_row,
                            ft.Divider(height=1),
                            action_buttons,
                        ],
                        spacing=6,
                    ),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST if is_current else ft.Colors.SURFACE_CONTAINER,
                    border=card_border,
                    border_radius=8,
                    padding=12,
                )
            )

        header_row = ft.Row(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.ACCOUNT_TREE_ROUNDED, color=ft.Colors.PRIMARY, size=24),
                        ft.Column(
                            [
                                ft.Text("History Tree & Checkpoint Vault", weight=ft.FontWeight.BOLD, size=16),
                                ft.Text(
                                    f"Branching timeline: {len(nodes_list)} checkpoints | Jeff Bezos Reversibility Filter (p. 6)",
                                    size=11,
                                    color=ft.Colors.GREY_400,
                                ),
                            ],
                            spacing=1,
                        ),
                    ],
                    spacing=10,
                ),
                ft.FilledButton(
                    "Create Checkpoint",
                    icon=ft.Icons.ADD_A_PHOTO,
                    on_click=lambda e: open_create_checkpoint_dialog(),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        modal_body = ft.Container(
            content=ft.Column(
                [
                    header_row,
                    ft.Divider(),
                    ft.Container(
                        content=ft.Column(timeline_cards, scroll=ft.ScrollMode.AUTO, spacing=10),
                        height=420,
                    ),
                ],
                spacing=8,
            ),
            width=700,
        )
        actions = [
            ft.TextButton("Close", on_click=lambda e: close_dialog()),
        ]
        show_dialog("History Tree & Checkpoint Vault", modal_body, actions)

    # =================================================================
    # VIEW BUILDERS
    # =================================================================

    # -----------------------------------------------------------------
    # 1. METHODOLOGY GUIDE MODAL [H]
    # -----------------------------------------------------------------
    def open_research_guide_dialog():
        guide_content = ft.Container(
            content=ft.Column(
                [
                    ft.Text("THE 6 HORIZONS OF FOCUS (David Allen GTD -- pp. 3-4)", weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY),
                    ft.Text("• Horizon 5 (50,000 ft): Purpose & Core Principles (Invariable, Lifelong)"),
                    ft.Text("• Horizon 4 (40,000 ft): 3-5 Year Vision (Master identity, benchmark standards)"),
                    ft.Text("• Horizon 3 (30,000 ft): Top 5 Core Goals (12-24 Months -- Buffett 25/5 Strategy)"),
                    ft.Text("• Horizon 2 (20,000 ft): Areas of Focus & Autopilot Habits (Maintenance -- Never Scored!)"),
                    ft.Text("• Horizon 1 (10,000 ft): Active Projects (<12 Months -- Slicing ground tasks)"),
                    ft.Text("• Ground / Runway (0 ft): Next Physical Tasks (30m - 2h scored by TPI)"),
                    ft.Divider(),
                    ft.Text("HOW TO FRAME 3-5 YEAR VISION (Horizon 4-5):", weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY),
                    ft.Text("Template: 'Become a [Role / Mastery Level] achieving [Capstone / Benchmark] while adhering to [Core Standard].'"),
                    ft.Divider(),
                    ft.Text("WARREN BUFFETT 25/5 RULE (Horizon 3):", weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY),
                    ft.Text("Force-rank top 25 ambitions. Circle ONLY the Top 5. Goals 6-25 are strictly quarantined into the AVOID-AT-ALL-COSTS list."),
                    ft.Divider(),
                    ft.Text("TPI FORMULA & CRITERIA CLARITY:", weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY),
                    ft.Text("TPI = [(W1 * Why_Align) + (W2 * Value_Impact) + (W3 * Urgency_CoD) + (W4 * Leverage_RR/OE)] * Confidence / Duration_RCF"),
                ],
                scroll=ft.ScrollMode.AUTO,
                spacing=10,
            ),
            width=650,
            height=420,
        )
        show_dialog("Research Methodology Guide", guide_content)

    # -----------------------------------------------------------------
    # 2. TASK COMPLETION & RCF LOGGING DIALOG
    # -----------------------------------------------------------------
    def open_complete_task_dialog(task: Dict[str, Any]):
        est_fib = int(task["duration_rcf"])
        actual_dropdown = ft.Dropdown(
            label="Actual Fibonacci Duration",
            options=[
                ft.dropdown.Option("1", "1 -- Tiny (~30 mins)"),
                ft.dropdown.Option("2", "2 -- Small (~1 to 2 hours)"),
                ft.dropdown.Option("3", "3 -- Medium (~half day)"),
                ft.dropdown.Option("5", "5 -- Medium-Large (~1-2 days)"),
                ft.dropdown.Option("8", "8 -- Large (~3-5 days)"),
                ft.dropdown.Option("13", "13 -- Very Large (~1-2 weeks)"),
                ft.dropdown.Option("20", "20 -- Huge (Overrun)"),
            ],
            value=str(est_fib) if est_fib <= 20 else "20",
        )
        notes_field = ft.TextField(
            label="Notes on Actual Time (Optional)",
            hint_text="e.g. Took 2.5 hours due to compass detailing",
        )

        def submit_completion(e):
            act_fib = int(actual_dropdown.value)
            note_val = notes_field.value.strip() or "Completed"
            push_undo_state(f"Completed Task: '{task['name']}'")
            ws["rcf_history"].append({
                "name": task["name"],
                "estimated_fib": est_fib,
                "actual_fib": act_fib,
                "actual_notes": note_val,
                "completed_at": datetime.now().strftime("%Y-%m-%d"),
            })
            ws["active_tasks"] = [t for t in ws["active_tasks"] if t["id"] != task["id"]]
            persist_workspace(ws)
            close_dialog()
            toast(f"Awesome! Logged '{task['name']}' into RCF Memory.", action="UNDO", on_action=lambda e: undo())
            render_main()

        dlg_content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(f"Completing: {task['name']}", weight=ft.FontWeight.BOLD, size=15),
                    ft.Text(f"Initial Estimated Duration: {est_fib} (Fibonacci)", color=ft.Colors.GREY_400),
                    actual_dropdown,
                    notes_field,
                ],
                spacing=14,
            ),
            width=500,
        )
        actions = [
            ft.TextButton("Cancel", on_click=lambda e: close_dialog()),
            ft.FilledButton("Log Completion", icon=ft.Icons.CHECK_CIRCLE, on_click=submit_completion),
        ]
        show_dialog("Complete Task & Log RCF Memory", dlg_content, actions)

    # -----------------------------------------------------------------
    # 3. FAST-TRACK ITEM ACTION DIALOGS
    # -----------------------------------------------------------------
    def complete_fast_track_item(index: int):
        push_undo_state()
        removed = ws["fast_track_inbox"].pop(index)
        persist_workspace(ws)
        toast(f"Marked Fast-Track item completed: '{removed['name']}'", action="UNDO", on_action=lambda e: undo())
        render_main()

    def clear_all_fast_track():
        push_undo_state()
        ws["fast_track_inbox"] = []
        persist_workspace(ws)
        toast("Cleared all Fast-Track inbox items.", action="UNDO", on_action=lambda e: undo())
        render_main()

    def open_type2_review_dialog(index: int, item: Dict[str, Any]):
        cadences = get_review_cadence_dates()
        resched_dropdown = ft.Dropdown(
            label="Reschedule Date",
            options=[ft.dropdown.Option(d, f"{k} ({d})") for k, d in cadences.items()],
            value=list(cadences.values())[0],
        )

        def on_action_select(action_type: str):
            push_undo_state()
            if action_type == "keep":
                ws["fast_track_inbox"].pop(index)
                persist_workspace(ws)
                toast(f"Success confirmed! '{item['name']}' marked completed.", action="UNDO", on_action=lambda e: undo())
            elif action_type == "rollback":
                ws["fast_track_inbox"].pop(index)
                persist_workspace(ws)
                toast(f"Rollback triggered: Reverted and discarded '{item['name']}'.", action="UNDO", on_action=lambda e: undo())
            elif action_type == "reschedule":
                new_date = resched_dropdown.value
                item["review_date"] = new_date
                item["action"] = f"Type 2 Fast Execution (Review: {new_date} | Rollback: {item.get('rollback', 'Revert')})"
                persist_workspace(ws)
                toast(f"Rescheduled review to {new_date}.", action="UNDO", on_action=lambda e: undo())
            close_dialog()
            render_main()

        dlg_content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(f"Experiment / Decision: {item['name']}", weight=ft.FontWeight.BOLD),
                    ft.Text(f"Action: {item.get('action', '')}"),
                    ft.Text(f"Review Status: {tpi_evaluator.format_review_status(item.get('review_date', ''))}"),
                    ft.Divider(),
                    ft.Text("Choose Outcome:", weight=ft.FontWeight.BOLD),
                    ft.FilledButton("[1] Kept / Success (Complete Task)", icon=ft.Icons.CHECK, on_click=lambda e: on_action_select("keep")),
                    ft.FilledTonalButton("[2] Trigger Rollback (Revert & Discard)", icon=ft.Icons.UNDO, on_click=lambda e: on_action_select("rollback")),
                    ft.Divider(),
                    ft.Text("Or Reschedule Review:", weight=ft.FontWeight.BOLD),
                    resched_dropdown,
                    ft.OutlinedButton("[3] Reschedule Review Date", icon=ft.Icons.SCHEDULE, on_click=lambda e: on_action_select("reschedule")),
                ],
                spacing=10,
            ),
            width=520,
        )
        show_dialog("Review Type 2 Reversible Decision", dlg_content)

    # -----------------------------------------------------------------
    # 3b. END-OF-DAY HABIT BATCH REVIEW DIALOG
    # -----------------------------------------------------------------
    def open_habit_review_dialog(initial_date: Optional[str] = None):
        habits = ws.get("daily_autopilot_habits", [])
        if not habits:
            toast("No daily habits configured yet. Add them in Foundation!", is_error=True)
            return

        today_str = datetime.now().strftime("%Y-%m-%d")
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        target_date = initial_date or today_str
        history = ws.get("habit_history", {})
        existing_entry = history.get(target_date, {})
        previously_completed = set(existing_entry.get("completed", []))

        selected_habits = set(previously_completed)

        status_text = ft.Text(
            f"Completed: {len(selected_habits)}/{len(habits)} ({(len(selected_habits)/len(habits))*100:.0f}%)" if habits else "0/0",
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.CYAN_200,
            size=13,
        )

        def update_status():
            rate = (len(selected_habits) / len(habits)) if habits else 0.0
            status_text.value = f"Completed: {len(selected_habits)}/{len(habits)} ({rate*100:.0f}%)"
            status_text.color = ft.Colors.GREEN_300 if rate >= 0.75 else (ft.Colors.AMBER_300 if rate >= 0.5 else ft.Colors.RED_300)
            page.update()

        checkboxes = []
        for idx, habit in enumerate(habits, 1):
            is_done = habit in selected_habits
            badge = ft.Chip(label=ft.Text("DO FIRST - Morning Anchor", size=10), bgcolor=ft.Colors.RED_900) if idx == 1 else None

            def make_toggle(h):
                def toggle(e):
                    if e.control.value:
                        selected_habits.add(h)
                    else:
                        selected_habits.discard(h)
                    update_status()
                return toggle

            checkboxes.append(
                ft.Container(
                    bgcolor=ft.Colors.SURFACE_CONTAINER,
                    border_radius=8,
                    padding=ft.Padding.symmetric(vertical=6, horizontal=10),
                    content=ft.Row(
                        [
                            ft.Checkbox(
                                label=f"[Routine {idx}] {habit}",
                                value=is_done,
                                on_change=make_toggle(habit),
                                expand=True,
                            ),
                            badge if badge else ft.Container(),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                )
            )

        notes_field = ft.TextField(
            label="Evening Reflection Notes (Wins, energy level, friction points)",
            value=existing_entry.get("notes", ""),
            multiline=True,
            min_lines=2,
            max_lines=3,
            hint_text="e.g. Good morning focus; felt tired around 9 PM so skipped routine 4 screen cutoff.",
        )

        date_dropdown = ft.Dropdown(
            label="Review Date",
            width=200,
            options=[
                ft.dropdown.Option(today_str, f"Today ({today_str})"),
                ft.dropdown.Option(yesterday_str, f"Yesterday ({yesterday_str})"),
            ],
            value=target_date,
        )

        def on_date_change(e):
            nonlocal target_date
            target_date = e.control.value
            entry = history.get(target_date, {})
            selected_habits.clear()
            selected_habits.update(entry.get("completed", []))
            notes_field.value = entry.get("notes", "")
            close_dialog()
            open_habit_review_dialog(target_date)

        date_dropdown.on_select = on_date_change

        def on_save_click(e):
            push_undo_state(f"Recorded Habit Review for {target_date}")
            tpi_evaluator.log_habit_review(ws, target_date, list(selected_habits), notes_field.value)
            persist_workspace(ws)
            close_dialog()
            rate = len(selected_habits) / len(habits) if habits else 0.0
            toast(
                f"Saved End-of-Day Review for {target_date} ({len(selected_habits)}/{len(habits)} Done · {rate*100:.0f}%)!",
                action="UNDO",
                on_action=lambda ev: undo(),
            )
            render_main()

        content = ft.Container(
            width=560,
            content=ft.Column(
                [
                    ft.Row([
                        ft.Icon(ft.Icons.NIGHTLIGHT_ROUND, color=ft.Colors.AMBER, size=24),
                        ft.Column([
                            ft.Text("End-of-Day Habit Reflection & Check-in", weight=ft.FontWeight.BOLD, size=16),
                            ft.Text("Batch review: Preserves deep work focus and prevents daytime context switches.", size=11, color=ft.Colors.GREY_300),
                        ], spacing=2),
                    ]),
                    ft.Row([date_dropdown, status_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Divider(),
                    ft.Text("Select which routines were completed:", weight=ft.FontWeight.W_500, size=13),
                    ft.Column(checkboxes, spacing=6),
                    ft.Divider(),
                    notes_field,
                ],
                spacing=10,
                tight=True,
            ),
        )

        def on_delete_this_day(e):
            def confirm_delete(ev):
                tpi_evaluator.commit_history_node(
                    history_tree,
                    ws,
                    title=f"Pre-Deletion: Habit Log {target_date}",
                    tag="TYPE 1 SAFEGUARD",
                    reason=f"Safeguard prior to deleting habit log for {target_date}",
                )
                push_undo_state(f"Deleted Habit Log for {target_date}")
                tpi_evaluator.delete_habit_log(ws, target_date)
                close_dialog()
                toast(f"Deleted habit record for {target_date}.", action="UNDO", on_action=lambda ev2: undo())
                render_main()

            show_dialog(
                f"Delete Log for {target_date}?",
                ft.Text(f"Are you sure you want to delete the habit completion record for {target_date}? This will update your streak and graph metrics."),
                [
                    ft.TextButton("Keep Log", on_click=lambda ev: close_dialog()),
                    ft.FilledButton("Yes, Delete Log", bgcolor=ft.Colors.RED_900, on_click=confirm_delete),
                ],
            )

        actions = [
            ft.TextButton("Cancel", on_click=lambda e: close_dialog()),
        ]
        if target_date in history:
            actions.append(
                ft.OutlinedButton(
                    "Delete This Day",
                    icon=ft.Icons.DELETE_OUTLINE,
                    style=ft.ButtonStyle(color=ft.Colors.RED_400),
                    on_click=on_delete_this_day,
                )
            )
        actions.append(
            ft.FilledButton("Save & Record Review", icon=ft.Icons.CHECK, on_click=on_save_click)
        )

        show_dialog("Daily Habit Review", content, actions)

    # -----------------------------------------------------------------
    # 3b-1. PURGE PAST TEST/DEMO HABIT DATA DIALOG
    # -----------------------------------------------------------------
    def open_purge_past_habit_data_dialog():
        history = ws.get("habit_history", {})
        today_str = datetime.now().strftime("%Y-%m-%d")
        past_dates = sorted([d for d in history.keys() if d != today_str])
        if not past_dates:
            toast("No past test or habit records found to purge.", is_error=False)
            return

        def submit_purge(e):
            tpi_evaluator.commit_history_node(
                history_tree,
                ws,
                title=f"Pre-Purge: {len(past_dates)} Past Habit History Records",
                tag="TYPE 1 SAFEGUARD",
                reason=f"Safeguard prior to purging {len(past_dates)} past habit records (demo/test data)",
            )
            push_undo_state(f"Purged {len(past_dates)} Past Habit Logs")
            purged = tpi_evaluator.purge_past_habit_history(ws, keep_today=True)
            close_dialog()
            toast(f"Purged {purged} past habit logs (preserved today).", action="UNDO", on_action=lambda ev: undo())
            render_main()

        show_dialog(
            "Purge Past Habit / Test Data?",
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text(f"Permanently delete all {len(past_dates)} past habit records prior to today?", weight=ft.FontWeight.BOLD, size=15),
                        ft.Text(f"• Target dates to delete: {', '.join(past_dates)}\n• Today's record ({today_str}) will be kept intact.\n• This cleans demo bars from your graphs while maintaining a fresh slate.", size=12, color=ft.Colors.GREY_300),
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.SECURITY_ROUNDED, color=ft.Colors.CYAN),
                                ft.Text("Research Note (Page 18 - Two-Way Door): This action saves a safety checkpoint to the History Tree and can be reversed via Undo (Ctrl+Z).", size=11, color=ft.Colors.CYAN_100, expand=True),
                            ]),
                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                            padding=10,
                            border_radius=8,
                        ),
                    ],
                    spacing=12,
                ),
                width=520,
            ),
            [
                ft.TextButton("Cancel", on_click=lambda ev: close_dialog()),
                ft.FilledButton("Yes, Purge Past Data", bgcolor=ft.Colors.RED_900, icon=ft.Icons.DELETE_SWEEP, on_click=submit_purge),
            ],
        )

    # -----------------------------------------------------------------
    # 3b-2. WORKSPACE APP DATA MANAGEMENT DIALOG
    # -----------------------------------------------------------------
    def open_workspace_data_manager_dialog():
        habit_count = len(ws.get("habit_history", {}))
        rcf_count = len(ws.get("rcf_history", []))
        wait_count = len(ws.get("waiting_next_month", []))
        avoid_count = len(ws.get("avoid_25_5_list", []))
        drop_count = len(ws.get("dropped_90_rule", []))
        tree_count = len(history_tree.get("nodes", []))

        content = ft.Container(
            width=620,
            content=ft.Column(
                [
                    ft.Row([
                        ft.Icon(ft.Icons.STORAGE_ROUNDED, color=ft.Colors.PRIMARY, size=24),
                        ft.Column([
                            ft.Text("Workspace & Application Data Management", weight=ft.FontWeight.BOLD, size=16),
                            ft.Text("Two-Way Door Safeguards (Research Paper pp. 6, 18-19): Every deletion auto-saves checkpoints.", size=11, color=ft.Colors.GREY_300),
                        ], spacing=2),
                    ]),
                    ft.Divider(),
                    # Store 1: Habit History
                    ft.Container(
                        bgcolor=ft.Colors.SURFACE_CONTAINER,
                        border_radius=8,
                        padding=12,
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.BAR_CHART_ROUNDED, color=ft.Colors.CYAN, size=20),
                                ft.Text(f"Daily Autopilot Habit History ({habit_count} Days Logged)", weight=ft.FontWeight.BOLD),
                            ]),
                            ft.Text("Maintenance logs from daily reviews. Purging unneeded test records cleans up analytics graphs.", size=11, color=ft.Colors.GREY_400),
                            ft.Row([
                                ft.OutlinedButton("Purge Past Test Data", icon=ft.Icons.AUTO_DELETE_OUTLINED, style=ft.ButtonStyle(color=ft.Colors.AMBER_400), on_click=lambda e: (close_dialog(), open_purge_past_habit_data_dialog())),
                                ft.FilledTonalButton("Manage Date Logs", icon=ft.Icons.LIST_ALT_ROUNDED, on_click=lambda e: (close_dialog(), open_manage_habit_logs_dialog())),
                            ], spacing=8, wrap=True),
                        ], spacing=6),
                    ),
                    # Store 2: RCF History
                    ft.Container(
                        bgcolor=ft.Colors.SURFACE_CONTAINER,
                        border_radius=8,
                        padding=12,
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.HISTORY_EDU, color=ft.Colors.GREEN_400, size=20),
                                ft.Text(f"Reference Class Forecasting Task History ({rcf_count} Completed Tasks)", weight=ft.FontWeight.BOLD),
                            ]),
                            ft.Text("Empirical task completion logs protecting against the Planning Fallacy (Kahneman & Tversky).", size=11, color=ft.Colors.GREY_400),
                            ft.Row([
                                ft.FilledTonalButton("View Memory Tab", icon=ft.Icons.INVENTORY_2_ROUNDED, on_click=lambda e: (close_dialog(), navigate_to(5))),
                            ], spacing=8),
                        ], spacing=6),
                    ),
                    # Store 3: Vaults & Lists
                    ft.Container(
                        bgcolor=ft.Colors.SURFACE_CONTAINER,
                        border_radius=8,
                        padding=12,
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.LOCK_ROUNDED, color=ft.Colors.AMBER_400, size=20),
                                ft.Text(f"Pruned Lists & Vaults ({wait_count} Waiting · {avoid_count} Avoid · {drop_count} Dropped)", weight=ft.FontWeight.BOLD),
                            ]),
                            ft.Text("Deprioritized items parked under the Buffett 25/5 and McKeown 90% rules.", size=11, color=ft.Colors.GREY_400),
                            ft.Row([
                                ft.FilledTonalButton("View Vaults & Lists", icon=ft.Icons.FOLDER_SPECIAL_ROUNDED, on_click=lambda e: (close_dialog(), navigate_to(5))),
                            ], spacing=8),
                        ], spacing=6),
                    ),
                    # Store 4: History Tree Checkpoints
                    ft.Container(
                        bgcolor=ft.Colors.SURFACE_CONTAINER,
                        border_radius=8,
                        padding=12,
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.ALT_ROUTE_ROUNDED, color=ft.Colors.PURPLE_300, size=20),
                                ft.Text(f"History Tree Safety Checkpoints ({tree_count} Checkpoints)", weight=ft.FontWeight.BOLD),
                            ]),
                            ft.Text("Git-like branching timeline enabling instantaneous rollback to any prior workspace state.", size=11, color=ft.Colors.GREY_400),
                            ft.Row([
                                ft.FilledTonalButton("Open History Tree", icon=ft.Icons.TIMELINE_ROUNDED, on_click=lambda e: (close_dialog(), open_history_tree_dialog())),
                            ], spacing=8),
                        ], spacing=6),
                    ),
                ],
                spacing=10,
                tight=True,
            ),
        )

        show_dialog("App Data Management", content, [ft.FilledButton("Close", on_click=lambda e: close_dialog())])

    # -----------------------------------------------------------------
    # 3c. MANAGE & DELETE HABIT LOGS DIALOG (Two-Way Door Data Management)
    # -----------------------------------------------------------------
    def open_manage_habit_logs_dialog():
        history = ws.get("habit_history", {})
        habits = ws.get("daily_autopilot_habits", [])

        if not history:
            content = ft.Container(
                width=520,
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.INVENTORY_2_OUTLINED, size=48, color=ft.Colors.GREY_500),
                        ft.Text("No habit history records currently stored.", italic=True, size=15),
                        ft.Text("Daily logs from your end-of-day reflections will appear here for auditing and management.", size=12, color=ft.Colors.GREY_400),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                padding=20,
            )
            show_dialog("Manage Habit History Logs", content, [ft.FilledButton("Close", on_click=lambda e: close_dialog())])
            return

        sorted_dates = sorted(list(history.keys()), reverse=True)
        today_str = datetime.now().strftime("%Y-%m-%d")
        selected_to_delete = set()

        def delete_date_entry(target_date: str):
            def confirm_del(ev):
                tpi_evaluator.commit_history_node(
                    history_tree,
                    ws,
                    title=f"Pre-Deletion: Habit Log {target_date}",
                    tag="TYPE 1 SAFEGUARD",
                    reason=f"Safeguard prior to deleting habit log for {target_date}",
                )
                push_undo_state(f"Deleted Habit Log for {target_date}")
                tpi_evaluator.delete_habit_log(ws, target_date)
                close_dialog()
                toast(f"Deleted habit log for {target_date}.", action="UNDO", on_action=lambda ev2: undo())
                render_main()
                if ws.get("habit_history"):
                    open_manage_habit_logs_dialog()

            show_dialog(
                f"Delete Habit Record: {target_date}?",
                ft.Text(f"Are you sure you want to permanently delete the habit log for {target_date}? This will update streaks and graphs."),
                [
                    ft.TextButton("Cancel", on_click=lambda ev: close_dialog()),
                    ft.FilledButton("Delete", bgcolor=ft.Colors.RED_900, on_click=confirm_del),
                ],
            )

        def delete_selected_entries(ev):
            if not selected_to_delete:
                toast("No dates selected to delete.", is_error=True)
                return
            del_list = sorted(list(selected_to_delete))

            def confirm_del_batch(ev2):
                tpi_evaluator.commit_history_node(
                    history_tree,
                    ws,
                    title=f"Pre-Deletion: {len(del_list)} Habit Logs",
                    tag="TYPE 1 SAFEGUARD",
                    reason=f"Safeguard prior to deleting {len(del_list)} habit logs: {del_list}",
                )
                push_undo_state(f"Deleted {len(del_list)} Habit Logs")
                purged = tpi_evaluator.delete_multiple_habit_logs(ws, del_list)
                close_dialog()
                toast(f"Deleted {purged} habit records.", action="UNDO", on_action=lambda ev3: undo())
                render_main()
                if ws.get("habit_history"):
                    open_manage_habit_logs_dialog()

            show_dialog(
                f"Delete {len(del_list)} Selected Habit Records?",
                ft.Text(f"Are you sure you want to delete habit records for:\n{', '.join(del_list)}?"),
                [
                    ft.TextButton("Cancel", on_click=lambda ev3: close_dialog()),
                    ft.FilledButton(f"Delete ({len(del_list)})", bgcolor=ft.Colors.RED_900, on_click=confirm_del_batch),
                ],
            )

        log_rows = []
        for d in sorted_dates:
            entry = history[d]
            rate = entry.get("rate", 0.0)
            completed = entry.get("completed", [])
            total = entry.get("total", len(habits))
            notes = entry.get("notes", "")

            rate_color = ft.Colors.GREEN_400 if rate >= 1.0 else (ft.Colors.TEAL_400 if rate >= 0.75 else (ft.Colors.AMBER_400 if rate >= 0.5 else ft.Colors.RED_400))
            notes_text = f"Notes: {notes}" if notes else ""

            def make_cb_handler(dt_val):
                def cb_change(e):
                    if e.control.value:
                        selected_to_delete.add(dt_val)
                    else:
                        selected_to_delete.discard(dt_val)
                return cb_change

            cb = ft.Checkbox(on_change=make_cb_handler(d), tooltip=f"Select {d} for batch deletion")

            log_rows.append(
                ft.Container(
                    bgcolor=ft.Colors.SURFACE_CONTAINER,
                    border_radius=8,
                    padding=10,
                    content=ft.Row(
                        [
                            cb,
                            ft.Column(
                                [
                                    ft.Row([
                                        ft.Text(d, weight=ft.FontWeight.BOLD, size=14),
                                        ft.Chip(label=ft.Text(f"{len(completed)}/{total} Done ({rate*100:.0f}%)", size=10, color=rate_color)),
                                        ft.Text("(Today)", size=11, color=ft.Colors.CYAN, weight=ft.FontWeight.BOLD) if d == today_str else ft.Container(),
                                    ], spacing=8),
                                    ft.Text(f"Completed: {', '.join(completed) if completed else '(None)'}", size=11, color=ft.Colors.GREY_300),
                                    ft.Text(notes_text, size=11, italic=True, color=ft.Colors.GREY_400) if notes_text else ft.Container(),
                                ],
                                expand=True,
                                spacing=3,
                            ),
                            ft.Row(
                                [
                                    ft.IconButton(
                                        ft.Icons.EDIT_OUTLINED,
                                        tooltip="Edit this day's review",
                                        on_click=lambda e, dt=d: (close_dialog(), open_habit_review_dialog(dt)),
                                    ),
                                    ft.IconButton(
                                        ft.Icons.DELETE_OUTLINE,
                                        tooltip="Delete this day's log",
                                        icon_color=ft.Colors.RED_400,
                                        on_click=lambda e, dt=d: delete_date_entry(dt),
                                    ),
                                ],
                                spacing=0,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                )
            )

        def clear_all_habits_action(e):
            def confirm_all_clear(ev):
                tpi_evaluator.commit_history_node(
                    history_tree,
                    ws,
                    title="Pre-Deletion: All Habit History",
                    tag="TYPE 1 SAFEGUARD",
                    reason="Safeguard prior to clearing entire habit history",
                )
                push_undo_state("Cleared All Habit History")
                tpi_evaluator.clear_all_habit_history(ws)
                close_dialog()
                toast("Cleared all habit history records.", action="UNDO", on_action=lambda ev2: undo())
                render_main()

            show_dialog(
                "Clear ALL Habit History?",
                ft.Text("Are you sure you want to delete ALL habit history records? This cannot be undone except via History Tree rollback or Undo."),
                [
                    ft.TextButton("Cancel", on_click=lambda ev: close_dialog()),
                    ft.FilledButton("Yes, Clear Everything", bgcolor=ft.Colors.RED_900, on_click=confirm_all_clear),
                ],
            )

        content = ft.Container(
            width=650,
            height=490,
            content=ft.Column(
                [
                    ft.Row([
                        ft.Icon(ft.Icons.LIST_ALT_ROUNDED, color=ft.Colors.CYAN, size=24),
                        ft.Column([
                            ft.Text(f"Manage Habit History Logs ({len(sorted_dates)} Days Logged)", weight=ft.FontWeight.BOLD, size=16),
                            ft.Text("Audit, edit, select to batch delete, or delete individual date records.", size=11, color=ft.Colors.GREY_300),
                        ], spacing=2),
                    ]),
                    ft.Row(
                        [
                            ft.OutlinedButton("Purge Past Test Data", icon=ft.Icons.AUTO_DELETE_OUTLINED, style=ft.ButtonStyle(color=ft.Colors.AMBER_400), tooltip="Delete all logs prior to today", on_click=lambda e: (close_dialog(), open_purge_past_habit_data_dialog())),
                            ft.FilledTonalButton("Delete Selected", icon=ft.Icons.DELETE, style=ft.ButtonStyle(color=ft.Colors.RED_400), tooltip="Delete all dates checked with checkboxes", on_click=delete_selected_entries),
                        ],
                        spacing=8,
                    ),
                    ft.Divider(),
                    ft.Container(
                        content=ft.ListView(log_rows, spacing=8),
                        expand=True,
                    ),
                ],
                spacing=8,
            ),
        )

        actions = [
            ft.TextButton("Close", on_click=lambda e: close_dialog()),
            ft.OutlinedButton("Clear All Habit Data", icon=ft.Icons.DELETE_SWEEP, style=ft.ButtonStyle(color=ft.Colors.RED_400), on_click=clear_all_habits_action),
        ]

        show_dialog("Manage Habit History Logs", content, actions)

    # -----------------------------------------------------------------
    # 4. VIEW: DASHBOARD (Menu 1)
    # -----------------------------------------------------------------
    def build_dashboard_view() -> ft.Control:
        weights = ws["weights"]
        tasks = ws["active_tasks"]

        # --- Top Vision & Weights Banner ---
        banner_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.FLAG_ROUNDED, color=ft.Colors.PRIMARY, size=24),
                                ft.Text("3-5 Year Vision (Horizon 4-5):", weight=ft.FontWeight.BOLD, size=15),
                                ft.IconButton(ft.Icons.EDIT, tooltip="Edit Vision", on_click=lambda e: navigate_to(3)),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        ft.Text(ws["vision_horizon_4_5"], size=14, color=ft.Colors.GREY_300),
                        ft.Divider(),
                        ft.Row(
                            [
                                ft.Text("Active Criteria Weights:", weight=ft.FontWeight.W_500),
                                ft.Chip(label=ft.Text(f"W1(Why)={weights['w1']}")),
                                ft.Chip(label=ft.Text(f"W2(Val)={weights['w2']}")),
                                ft.Chip(label=ft.Text(f"W3(Urg)={weights['w3']}")),
                                ft.Chip(label=ft.Text(f"W4(Lev)={weights['w4']}")),
                                ft.IconButton(ft.Icons.TUNE, tooltip="Configure Weights", on_click=lambda e: navigate_to(6)),
                            ],
                            wrap=True,
                            spacing=6,
                        ),
                    ],
                    spacing=8,
                ),
                padding=16,
            )
        )

        # --- Phase D: Layer 2 Today's Execution Plan (#1 Frog + 1-3-5) ---
        frog_content = None
        if tasks:
            top_frog = tasks[0]
            big_tasks = [t for t in tasks if t["duration_rcf"] >= 3]
            med_tasks = [t for t in tasks if t["duration_rcf"] == 2]
            small_tasks = [t for t in tasks if t["duration_rcf"] == 1]

            big_name = big_tasks[0]["name"] if big_tasks else top_frog["name"]
            med_str = ", ".join(t["name"] for t in med_tasks[:3]) or "None currently in queue"
            small_str = ", ".join(t["name"] for t in small_tasks[:5]) or "Use Fast-Track / Admin Batch items"

            frog_content = ft.Card(
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.EMOJI_NATURE_ROUNDED, color=ft.Colors.AMBER, size=24),
                                    ft.Text("LAYER 2: TODAY'S EXECUTION PLAN (Attention Protection)", weight=ft.FontWeight.BOLD, size=15),
                                ]
                            ),
                            ft.Container(
                                bgcolor=ft.Colors.GREEN_900,
                                border_radius=ft.BorderRadius.all(8),
                                padding=12,
                                content=ft.Row(
                                    [
                                        ft.Icon(ft.Icons.STAR_ROUNDED, color=ft.Colors.YELLOW_ACCENT, size=28),
                                        ft.Column(
                                            [
                                                ft.Text("MORNING DEEP WORK BLOCK (90-120 Mins -- #1 EAT THAT FROG):", weight=ft.FontWeight.BOLD, size=13),
                                                ft.Text(f"[ID {top_frog['id']}] \"{top_frog['name']}\"", weight=ft.FontWeight.BOLD, size=16),
                                                ft.Text(f"TPI Score: {top_frog['tpi_score']} | Est. Duration: {int(top_frog['duration_rcf'])} Fibonacci", size=12, color=ft.Colors.GREY_300),
                                            ],
                                            expand=True,
                                        ),
                                        ft.FilledButton("Complete Frog", icon=ft.Icons.CHECK, on_click=lambda e: open_complete_task_dialog(top_frog)),
                                    ]
                                ),
                            ),
                            ft.Text("TODAY'S 1-3-5 ALLOCATION:", weight=ft.FontWeight.BOLD, size=13),
                            ft.Text(f"• 1 BIG Task (Dur >= 3)    : {big_name}"),
                            ft.Text(f"• 3 MEDIUM Tasks (Dur = 2): {med_str}"),
                            ft.Text(f"• 5 SMALL Tasks (Dur = 1) : {small_str}"),
                        ],
                        spacing=10,
                    ),
                    padding=16,
                )
            )
        else:
            frog_content = ft.Card(
                content=ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.BLUE_400),
                            ft.Text("Scored queue is empty. Add tasks to calculate your #1 Frog and 1-3-5 plan!"),
                            ft.FilledButton("Add Tasks", icon=ft.Icons.ADD, on_click=lambda e: navigate_to(1)),
                        ]
                    ),
                    padding=16,
                )
            )

        # --- Phase A: Fixed Daily Autopilot Habits (Horizon 2 -- End-of-Day Batch Review) ---
        today_str = datetime.now().strftime("%Y-%m-%d")
        if "habits_state" not in ws or not isinstance(ws.get("habits_state"), dict):
            ws["habits_state"] = {"date": today_str, "completed": []}
            persist_workspace(ws)
        elif ws["habits_state"].get("date") != today_str:
            ws["habits_state"] = {"date": today_str, "completed": []}
            persist_workspace(ws)

        history = ws.get("habit_history", {})
        habit_settings = ws.get("habit_settings", {})
        review_time = habit_settings.get("review_time", "21:00")
        streaks = tpi_evaluator.calculate_habit_streaks(ws)
        analytics_7 = tpi_evaluator.calculate_habit_analytics(ws, days=7)

        today_logged = today_str in history
        today_entry = history.get(today_str, {})
        completed_habits = today_entry.get("completed", ws["habits_state"].get("completed", []))

        total_habits = len(ws["daily_autopilot_habits"])
        done_habits = len(completed_habits)
        rate = (done_habits / total_habits) if total_habits > 0 else 0.0

        habits_display_rows = []
        if ws["daily_autopilot_habits"]:
            for idx, habit in enumerate(ws["daily_autopilot_habits"], 1):
                is_done = habit in completed_habits
                if today_logged:
                    status_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_400, size=18) if is_done else ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED, color=ft.Colors.GREY_500, size=18)
                else:
                    status_icon = ft.Icon(ft.Icons.SCHEDULE, color=ft.Colors.CYAN_300, size=18)

                badge_chip = ft.Chip(label=ft.Text("DO FIRST - Morning Anchor", size=10), bgcolor=ft.Colors.RED_900) if idx == 1 else None
                habits_display_rows.append(
                    ft.Container(
                        bgcolor=ft.Colors.SURFACE_CONTAINER,
                        border_radius=6,
                        padding=ft.Padding.symmetric(vertical=6, horizontal=10),
                        content=ft.Row(
                            [
                                ft.Row([
                                    status_icon,
                                    ft.Text(f"[Routine {idx}] {habit}", weight=ft.FontWeight.W_500, color=ft.Colors.GREEN_200 if (today_logged and is_done) else ft.Colors.ON_SURFACE),
                                ], spacing=8),
                                badge_chip if badge_chip else ft.Container(),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                    )
                )
        else:
            habits_display_rows.append(ft.Text("(No daily habits set yet. Add them in Foundation!)", italic=True))

        if today_logged:
            status_chip = ft.Chip(
                label=ft.Text(f"✅ Reviewed: {done_habits}/{total_habits} Done ({rate*100:.0f}%)", size=11, color=ft.Colors.GREEN_200, weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.GREEN_900,
            )
            review_btn_text = "Edit Today's Review"
        else:
            status_chip = ft.Chip(
                label=ft.Text(f"⏳ Pending Evening Review (@ {review_time})", size=11, color=ft.Colors.AMBER_200, weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.AMBER_900,
            )
            review_btn_text = "Check Finished Habits (End-of-Day Review)"

        habits_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Row([
                                    ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, color=ft.Colors.CYAN, size=22),
                                    ft.Text("[A] FIXED DAILY AUTOPILOT HABITS (Horizon 2) — END-OF-DAY REVIEW:", weight=ft.FontWeight.BOLD),
                                    status_chip,
                                ], wrap=True, spacing=6),
                                ft.TextButton("Manage", icon=ft.Icons.TUNE, on_click=lambda e: navigate_to(3)),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Container(
                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                            border_radius=6,
                            padding=8,
                            content=ft.Row([
                                ft.Icon(ft.Icons.SHIELD_ROUNDED, size=16, color=ft.Colors.TEAL_300),
                                ft.Text(
                                    "Attention Hygiene: Habits are batched for evening review to eliminate daytime micro-interruptions (Gloria Mark, 2008).",
                                    size=11,
                                    color=ft.Colors.GREY_300,
                                ),
                            ], spacing=8),
                        ),
                        ft.Row(
                            [
                                ft.Chip(label=ft.Text(f"🔥 Streak: {streaks['current_streak']} Days", size=11)),
                                ft.Chip(label=ft.Text(f"📈 7-Day Adherence: {analytics_7['avg_7_day_rate']*100:.0f}%", size=11)),
                                ft.Chip(label=ft.Text(f"⏰ Daily Review: {review_time}", size=11)),
                                ft.Chip(label=ft.Text(f"🛡️ ~{total_habits * 20}m/day Focus Saved", size=11, color=ft.Colors.TEAL_200)),
                            ],
                            wrap=True,
                            spacing=6,
                        ),
                        ft.Column(habits_display_rows, spacing=4),
                        ft.Row(
                            [
                                ft.FilledButton(
                                    review_btn_text,
                                    icon=ft.Icons.CHECK_CIRCLE,
                                    on_click=lambda e: open_habit_review_dialog(),
                                ),
                                ft.FilledTonalButton(
                                    "Habit Analytics & Graphs",
                                    icon=ft.Icons.INSIGHTS_ROUNDED,
                                    on_click=lambda e: navigate_to(4),
                                ),
                            ],
                            spacing=10,
                        ),
                    ],
                    spacing=10,
                ),
                padding=16,
            )
        )

        # --- Phase B: Fast-Track / Type 2 Reversible Queue ---
        ft_items_controls = []
        if ws["fast_track_inbox"]:
            for idx, item in enumerate(ws["fast_track_inbox"]):
                rev_date = item.get("review_date")
                status = tpi_evaluator.format_review_status(rev_date) if rev_date else ""
                status_color = ft.Colors.RED_400 if "OVERDUE" in status else (ft.Colors.AMBER_400 if "DUE TODAY" in status else ft.Colors.BLUE_400)

                ft_items_controls.append(
                    ft.Container(
                        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                        border_radius=ft.BorderRadius.all(8),
                        padding=10,
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(f"[FT-{idx+1}] {item['name']}", weight=ft.FontWeight.BOLD),
                                        ft.Text(f"Action: {item.get('action', '')}", size=12, color=ft.Colors.GREY_300),
                                        ft.Text(status, size=12, color=status_color, weight=ft.FontWeight.BOLD) if status else ft.Container(),
                                    ],
                                    expand=True,
                                ),
                                ft.FilledTonalButton("Complete", on_click=lambda e, i=idx: complete_fast_track_item(i)),
                                ft.OutlinedButton("Review", on_click=lambda e, i=idx, it=item: open_type2_review_dialog(i, it)) if rev_date else ft.Container(),
                            ]
                        ),
                    )
                )

        fast_track_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.BOLT_ROUNDED, color=ft.Colors.AMBER, size=20),
                                ft.Text(f"[B] FAST-TRACK / ADMIN BATCH ITEMS ({len(ws['fast_track_inbox'])}):", weight=ft.FontWeight.BOLD),
                                ft.TextButton("Clear All", on_click=lambda e: clear_all_fast_track()) if ws["fast_track_inbox"] else ft.Container(),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Column(ft_items_controls if ft_items_controls else [ft.Text("(Fast-track inbox is empty)", italic=True)], spacing=6),
                    ],
                    spacing=8,
                ),
                padding=16,
            )
        )

        # --- Phase C: Ranked Active TPI Task Queue ---
        task_rows = []
        for idx, task in enumerate(tasks, 1):
            prereq_str = f" [Prereq: {task['prerequisite_note']}]" if task.get("prerequisite_note") else ""
            task_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(f"#{idx}", weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(str(task["id"]))),
                        ft.DataCell(
                            ft.Column(
                                [
                                    ft.Text(task["name"], weight=ft.FontWeight.W_500),
                                    ft.Text(f"Project: {task.get('project') or 'General'}{prereq_str}", size=11, color=ft.Colors.GREY_400),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                            )
                        ),
                        ft.DataCell(ft.Text(str(int(task["why_align"])))),
                        ft.DataCell(ft.Text(str(int(task["value_impact"])))),
                        ft.DataCell(ft.Text(str(int(task["urgency_cod"])))),
                        ft.DataCell(ft.Text(str(int(task["leverage_rroe"])))),
                        ft.DataCell(ft.Text(f"{task['confidence']:.1f}")),
                        ft.DataCell(ft.Text(str(int(task["duration_rcf"])))),
                        ft.DataCell(
                            ft.Container(
                                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                                border_radius=ft.BorderRadius.all(4),
                                padding=ft.Padding.symmetric(vertical=4, horizontal=8),
                                content=ft.Text(f"{task['tpi_score']:.2f}", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_PRIMARY_CONTAINER),
                            )
                        ),
                        ft.DataCell(
                            ft.FilledButton(
                                "Done",
                                icon=ft.Icons.CHECK_CIRCLE,
                                on_click=lambda e, t=task: open_complete_task_dialog(t),
                            )
                        ),
                    ]
                )
            )

        task_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Rank")),
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Task Name & Details")),
                ft.DataColumn(ft.Text("Why")),
                ft.DataColumn(ft.Text("Val")),
                ft.DataColumn(ft.Text("Urg")),
                ft.DataColumn(ft.Text("Lev")),
                ft.DataColumn(ft.Text("Conf")),
                ft.DataColumn(ft.Text("Dur")),
                ft.DataColumn(ft.Text("TPI Score")),
                ft.DataColumn(ft.Text("Action")),
            ],
            rows=task_rows,
            heading_row_color=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        )

        ranked_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.FORMAT_LIST_NUMBERED_ROUNDED, color=ft.Colors.PRIMARY, size=20),
                                ft.Text(f"[C] LAYER 1: ACTIVE TPI TASK QUEUE ({len(tasks)} tasks):", weight=ft.FontWeight.BOLD),
                                ft.FilledButton("Add New Task", icon=ft.Icons.ADD, on_click=lambda e: navigate_to(1)),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Row([task_table], scroll=ft.ScrollMode.AUTO) if tasks else ft.Text("(Scored task queue is empty. Click 'Add New Task' to begin!)", italic=True),
                    ],
                    spacing=8,
                ),
                padding=16,
            )
        )

        return ft.ListView(
            controls=[
                banner_card,
                frog_content,
                habits_card,
                fast_track_card,
                ranked_card,
            ],
            spacing=16,
            padding=16,
            expand=True,
        )

    # -----------------------------------------------------------------
    # 5. VIEW: ADD TASKS (Gate 0 Screening + Layer 1 Scoring Engine)
    # -----------------------------------------------------------------
    def build_add_tasks_view() -> ft.Control:
        # State for candidate entry and Gate 0
        raw_name_input = ft.TextField(
            label="Candidate Task Name",
            hint_text="e.g. Calculate thermal limits & hand-draw buck converter wiring schematic",
            expand=True,
        )
        project_dropdown = ft.Dropdown(
            label="Link to Active Project (Optional)",
            options=[ft.dropdown.Option("", "(None / General)")] + [
                ft.dropdown.Option(p, p) for p in ws["active_projects"]
            ],
            value="",
            expand=True,
        )

        # Batch queue
        batch_tasks: List[Dict[str, Any]] = []
        batch_list_view = ft.Column(spacing=6)

        def refresh_batch_list():
            batch_list_view.controls.clear()
            for idx, item in enumerate(batch_tasks):
                batch_list_view.controls.append(
                    ft.Container(
                        bgcolor=ft.Colors.SURFACE_CONTAINER,
                        border_radius=ft.BorderRadius.all(6),
                        padding=8,
                        content=ft.Row(
                            [
                                ft.Text(f"{idx+1}. {item['name']}", weight=ft.FontWeight.BOLD, expand=True),
                                ft.Text(f"[{item.get('project') or 'General'}]", color=ft.Colors.GREY_400),
                                ft.IconButton(
                                    ft.Icons.DELETE_OUTLINE,
                                    on_click=lambda e, i=idx: remove_batch_item(i),
                                ),
                            ]
                        ),
                    )
                )
            page.update()

        def remove_batch_item(idx: int):
            batch_tasks.pop(idx)
            refresh_batch_list()

        # Gate 0 Dialog Step through
        def run_gate_zero_for_name(candidate_name: str, proj: str, on_pass_callback):
            cadences = get_review_cadence_dates()

            # Dialog steps container
            dlg_body = ft.Column(spacing=12, scroll=ft.ScrollMode.AUTO)

            def show_gate_step(step_idx: int):
                dlg_body.controls.clear()

                if step_idx == 0:
                    # Check 0: Habit Guardrail
                    dlg_body.controls.extend([
                        ft.Text("Check 0: Habit / Routine Guardrail", weight=ft.FontWeight.BOLD, size=16),
                        ft.Text("Is this a recurring habit/hygiene/exercise routine with no one-time finish line?"),
                        ft.Row([
                            ft.FilledButton("Yes (Recurring Routine)", on_click=lambda e: habit_route()),
                            ft.OutlinedButton("No (One-time Task)", on_click=lambda e: show_gate_step(1)),
                        ]),
                    ])
                elif step_idx == 1:
                    # Check 1a: GTD 2-Minute Rule
                    dlg_body.controls.extend([
                        ft.Text("Check 1a: GTD 2-Minute Rule", weight=ft.FontWeight.BOLD, size=16),
                        ft.Text("Can this task be finished in under 2 minutes right now?"),
                        ft.Row([
                            ft.FilledButton("Yes (< 2 mins)", on_click=lambda e: two_min_route()),
                            ft.OutlinedButton("No (Takes longer)", on_click=lambda e: show_gate_step(2)),
                        ]),
                    ])
                elif step_idx == 2:
                    # Check 1b: Bezos Type 2 Decision
                    review_date_dd = ft.Dropdown(
                        label="Review Cadence",
                        options=[ft.dropdown.Option(d, f"{k} ({d})") for k, d in cadences.items()],
                        value=list(cadences.values())[0],
                    )
                    rollback_tf = ft.TextField(label="Rollback Trigger (Condition to undo)", value="Revert if metric drops")

                    dlg_body.controls.extend([
                        ft.Text("Check 1b: Bezos Type 2 Reversible Decision", weight=ft.FontWeight.BOLD, size=16),
                        ft.Text("Is this a quick reversible decision or experiment (<30m to decide/test) with >=70% information?"),
                        review_date_dd,
                        rollback_tf,
                        ft.Row([
                            ft.FilledButton("Yes (Type 2 Fast-Track)", on_click=lambda e: type2_route(review_date_dd.value, rollback_tf.value)),
                            ft.OutlinedButton("No (Substantial Task)", on_click=lambda e: show_gate_step(3)),
                        ]),
                    ])
                elif step_idx == 3:
                    # Check 2a: Hard Constraints
                    dlg_body.controls.extend([
                        ft.Text("Check 2a: Hard Constraint (Safety / Health / Ethics)", weight=ft.FontWeight.BOLD, size=16),
                        ft.Text("Does this violate a permanent safety, health, or ethical boundary?"),
                        ft.Row([
                            ft.FilledButton("Yes (Violates Boundary)", on_click=lambda e: reject_route()),
                            ft.OutlinedButton("No (Safe & Ethical)", on_click=lambda e: show_gate_step(4)),
                        ]),
                    ])
                elif step_idx == 4:
                    # Check 2b: Budget / Tool Lock
                    reason_tf = ft.TextField(label="When will budget/parts unlock?", value="Next month stipend")
                    prep_tf = ft.TextField(label="$0 Prep Task Name (Design/Calculation)", value="")

                    dlg_body.controls.extend([
                        ft.Text("Check 2b: Temporary Budget / Resource Lock", weight=ft.FontWeight.BOLD, size=16),
                        ft.Text("Is this blocked by money or missing parts until next month?"),
                        reason_tf,
                        ft.Text("Zero-Cost Prep Split: Can you extract a $0 design/schematic/math task right now?"),
                        prep_tf,
                        ft.Row([
                            ft.FilledButton("Yes (Blocked -- Vault it)", on_click=lambda e: budget_route(reason_tf.value, prep_tf.value)),
                            ft.OutlinedButton("No (Resources Ready)", on_click=lambda e: show_gate_step(5)),
                        ]),
                    ])
                elif step_idx == 5:
                    # Check 3: Buffett 25/5 Rule
                    dlg_body.controls.extend([
                        ft.Text("Check 3: Warren Buffett 25/5 Strategy", weight=ft.FontWeight.BOLD, size=16),
                        ft.Text("Does this serve your Top 5 Core Goals or mandatory coursework/work?"),
                        ft.Row([
                            ft.FilledButton("Yes (Serves Top 5 / Work)", on_click=lambda e: show_gate_step(6)),
                            ft.OutlinedButton("No (Distraction / Goal 6-25)", on_click=lambda e: avoid_route()),
                        ]),
                    ])
                elif step_idx == 6:
                    # Check 4: McKeown 90% Rule
                    dlg_body.controls.extend([
                        ft.Text("Check 4: McKeown 90% Rule & Sunk Cost", weight=ft.FontWeight.BOLD, size=16),
                        ft.Text("Is this a high-impact contribution (>= 90%), OR worth signing up for today from scratch?"),
                        ft.Row([
                            ft.FilledButton("Yes (Passes 90% Rule)", on_click=lambda e: pass_route()),
                            ft.OutlinedButton("No (Drop it)", on_click=lambda e: drop_route()),
                        ]),
                    ])
                page.update()

            def habit_route():
                push_undo_state()
                ws["daily_autopilot_habits"].append(candidate_name)
                persist_workspace(ws)
                close_dialog()
                toast(f"Routed to Daily Autopilot Habits: '{candidate_name}'", action="UNDO", on_action=lambda e: undo())
                render_main()

            def two_min_route():
                push_undo_state()
                ws["fast_track_inbox"].append({
                    "name": candidate_name,
                    "action": "2-Minute Immediate / Afternoon Admin Batch",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                })
                persist_workspace(ws)
                close_dialog()
                toast(f"Fast-Tracked: '{candidate_name}' added to 2-Min / Admin Batch.", action="UNDO", on_action=lambda e: undo())
                render_main()

            def type2_route(rev_date: str, rollback: str):
                push_undo_state()
                ws["fast_track_inbox"].append({
                    "name": candidate_name,
                    "action": f"Type 2 Fast Execution (Review: {rev_date} | Rollback: {rollback})",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "review_date": rev_date,
                    "rollback": rollback,
                })
                persist_workspace(ws)
                close_dialog()
                toast(f"Fast-Tracked: Type 2 reversible decision scheduled for review on {rev_date}.", action="UNDO", on_action=lambda e: undo())
                render_main()

            def reject_route():
                close_dialog()
                toast("REJECTED: Unsafe/unethical tasks are never permitted into queue.", is_error=True)

            def budget_route(reason: str, prep_name: str):
                push_undo_state()
                ws["waiting_next_month"].append({
                    "name": candidate_name,
                    "reason": reason.strip() or "Next month",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                })
                persist_workspace(ws)
                close_dialog()
                if prep_name.strip():
                    toast(f"Vaulted '{candidate_name}'. Routing $0 prep task '{prep_name}' to scoring!")
                    on_pass_callback({"name": prep_name.strip(), "project": proj})
                else:
                    toast(f"Saved '{candidate_name}' to Waiting Vault.", action="UNDO", on_action=lambda e: undo())
                    render_main()

            def avoid_route():
                push_undo_state()
                ws["avoid_25_5_list"].append(candidate_name)
                persist_workspace(ws)
                close_dialog()
                toast(f"Quarantined '{candidate_name}' into 25/5 Avoid List.", action="UNDO", on_action=lambda e: undo())
                render_main()

            def drop_route():
                push_undo_state()
                ws["dropped_90_rule"].append(candidate_name)
                persist_workspace(ws)
                close_dialog()
                toast(f"Dropped '{candidate_name}' (sub-90% contribution).", action="UNDO", on_action=lambda e: undo())
                render_main()

            def pass_route():
                close_dialog()
                toast(f"Passed Gate 0: '{candidate_name}' is ready for Layer 1 Scoring!")
                on_pass_callback({"name": candidate_name, "project": proj})

            show_gate_step(0)
            show_dialog(f"Gate 0 Binary Screening: '{candidate_name}'", ft.Container(content=dlg_body, width=540))

        # Layer 1 Scoring Engine Dialog (Vertical Batch across tasks)
        def start_scoring_flow(candidates: List[Dict[str, Any]]):
            if not candidates:
                return

            columns_order = [
                "why_align",
                "value_impact",
                "urgency_cod",
                "leverage_rroe",
                "confidence",
                "duration_rcf",
            ]
            current_col_idx = [0]
            scores_store: Dict[str, Dict[str, float]] = {c["name"]: {} for c in candidates}
            prereq_store: Dict[str, str] = {c["name"]: "" for c in candidates}

            score_dlg_content = ft.Column(spacing=12, scroll=ft.ScrollMode.AUTO)

            def render_col_step():
                score_dlg_content.controls.clear()
                col_key = columns_order[current_col_idx[0]]
                rubric = RUBRICS[col_key]

                # Anchor descriptions
                anchor_items = [
                    ft.Text(f"[{val}] : {desc}", size=12)
                    for val, desc in rubric["anchors"].items()
                ]

                # Relative anchors from existing tasks
                rel_items = []
                if ws["active_tasks"]:
                    rel_items.append(ft.Text("Existing Active Tasks (For Relative Anchor Comparison):", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.PRIMARY))
                    for existing in ws["active_tasks"][:4]:
                        rel_items.append(ft.Text(f"• [{existing[col_key]}] {existing['name']}", size=11))

                # RCF Memory if duration
                rcf_items = []
                if col_key == "duration_rcf" and ws["rcf_history"]:
                    rcf_items.append(ft.Text("Historical RCF Memory (Past Tasks):", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.AMBER))
                    for hist in ws["rcf_history"][-3:]:
                        rcf_items.append(ft.Text(f"• '{hist['name']}' -> Est: {hist['estimated_fib']} | Actual: {hist['actual_fib']} ({hist['actual_notes']})", size=11))

                # Controls for each candidate
                input_controls = []
                for cand in candidates:
                    val_dropdown = ft.Dropdown(
                        label=f"Score for: '{cand['name']}'",
                        options=[ft.dropdown.Option(str(v), f"{v} -- {rubric['anchors'].get(v, '')[:40]}") for v in rubric["allowed"]],
                        value=str(rubric["allowed"][0]),
                        expand=True,
                    )
                    scores_store[cand["name"]][col_key] = val_dropdown
                    input_controls.append(val_dropdown)

                score_dlg_content.controls.extend([
                    ft.Text(rubric["title"], weight=ft.FontWeight.BOLD, size=15),
                    ft.Text(f"Question: \"{rubric['question']}\"", italic=True, size=13),
                    ft.Card(content=ft.Container(content=ft.Column(anchor_items, spacing=3), padding=10)),
                    ft.Column(rel_items, spacing=2) if rel_items else ft.Container(),
                    ft.Column(rcf_items, spacing=2) if rcf_items else ft.Container(),
                    ft.Divider(),
                    ft.Text("Select Scores:", weight=ft.FontWeight.BOLD),
                    ft.Column(input_controls, spacing=8),
                    ft.Row(
                        [
                            ft.FilledButton(
                                "Next Column ->" if current_col_idx[0] < len(columns_order) - 1 else "Finish & Calculate TPI",
                                icon=ft.Icons.ARROW_FORWARD,
                                on_click=lambda e: next_column(),
                            )
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ])
                page.update()

            def next_column():
                col_key = columns_order[current_col_idx[0]]
                # Collect scores
                for cand in candidates:
                    dd_ctrl = scores_store[cand["name"]][col_key]
                    val = float(dd_ctrl.value) if "." in dd_ctrl.value else int(dd_ctrl.value)

                    # Check mandatory task decomposition
                    if col_key == "duration_rcf" and val >= 20:
                        toast(f"'{cand['name']}' has duration >= 20. Decomposing into milestone.")
                        cand["name"] = f"{cand['name']} (Milestone 1)"
                        val = 8 # Sliced to manageable size

                    cand[col_key] = val

                if current_col_idx[0] < len(columns_order) - 1:
                    current_col_idx[0] += 1
                    render_col_step()
                else:
                    # Final step: Prerequisites & TPI computation
                    finalize_scoring(candidates)

            def finalize_scoring(finished_candidates: List[Dict[str, Any]]):
                push_undo_state()
                for cand in finished_candidates:
                    cand["id"] = ws["next_task_id"]
                    ws["next_task_id"] += 1
                    cand["tpi_score"] = compute_tpi_val(cand, ws["weights"])
                    cand["prerequisite_note"] = prereq_store.get(cand["name"], "")
                    cand["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    ws["active_tasks"].append(cand)

                persist_workspace(ws)
                close_dialog()
                toast(f"Saved {len(finished_candidates)} task(s) into Persistent TPI Queue!", action="UNDO", on_action=lambda e: undo())
                navigate_to(0)

            render_col_step()
            show_dialog("Layer 1 Vertical Scoring Engine", ft.Container(content=score_dlg_content, width=620, height=520))

        # Action handlers
        def on_single_entry_click(e):
            name = raw_name_input.value.strip()
            if not name:
                toast("Please enter a task name.", is_error=True)
                return
            proj = project_dropdown.value
            raw_name_input.value = ""
            run_gate_zero_for_name(name, proj, lambda task_dict: start_scoring_flow([task_dict]))

        def on_add_to_batch_click(e):
            name = raw_name_input.value.strip()
            if not name:
                toast("Please enter a task name.", is_error=True)
                return
            proj = project_dropdown.value
            raw_name_input.value = ""

            def on_batch_pass(task_dict):
                batch_tasks.append(task_dict)
                refresh_batch_list()
                toast(f"Added '{task_dict['name']}' to Weekly Batch Queue.")

            run_gate_zero_for_name(name, proj, on_batch_pass)

        def on_score_batch_click(e):
            if not batch_tasks:
                toast("Weekly batch queue is empty.", is_error=True)
                return
            to_score = list(batch_tasks)
            batch_tasks.clear()
            refresh_batch_list()
            start_scoring_flow(to_score)

        # Context Banner Card
        goals_text = "\n".join(f"• {g}" for g in ws["top_5_goals"]) if ws["top_5_goals"] else "(None set yet)"
        proj_text = "\n".join(f"• {p}" for p in ws["active_projects"]) if ws["active_projects"] else "(None set yet)"

        context_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row([
                            ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, color=ft.Colors.AMBER),
                            ft.Text("TOP-DOWN GOALS & PROJECTS (Slicing Reference)", weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Text(f"Vision (Horizon 4-5): {ws['vision_horizon_4_5']}", size=12, color=ft.Colors.GREY_300),
                        ft.Row(
                            [
                                ft.Column([ft.Text("Top 5 Core Goals (Horizon 3):", weight=ft.FontWeight.BOLD, size=12), ft.Text(goals_text, size=11)], expand=True),
                                ft.Column([ft.Text("Active Projects (Horizon 1):", weight=ft.FontWeight.BOLD, size=12), ft.Text(proj_text, size=11)], expand=True),
                            ]
                        ),
                    ],
                    spacing=8,
                ),
                padding=14,
            )
        )

        entry_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("ADD TASKS: GATE 0 & LAYER 1 SCORING", weight=ft.FontWeight.BOLD, size=16),
                        ft.Row([raw_name_input, project_dropdown]),
                        ft.Row(
                            [
                                ft.FilledButton("Single Task Triage -> Gate 0", icon=ft.Icons.FLASH_ON, on_click=on_single_entry_click),
                                ft.FilledTonalButton("Screen & Add to Weekly Batch", icon=ft.Icons.QUEUE, on_click=on_add_to_batch_click),
                            ],
                            spacing=12,
                        ),
                        ft.Divider(),
                        ft.Row(
                            [
                                ft.Text("Weekly Review Batch Queue (Survivors of Gate 0 ready for Vertical Scoring):", weight=ft.FontWeight.BOLD),
                                ft.FilledButton("Score Entire Batch Vertically", icon=ft.Icons.PLAY_ARROW, on_click=on_score_batch_click),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        batch_list_view,
                    ],
                    spacing=12,
                ),
                padding=16,
            )
        )

        return ft.ListView(
            controls=[context_card, entry_card],
            spacing=16,
            padding=16,
            expand=True,
        )

    # -----------------------------------------------------------------
    # 6. VIEW: WEEKLY REVIEW (Menu 4)
    # -----------------------------------------------------------------
    def build_weekly_review_view() -> ft.Control:
        # Step 1: Waiting Vault
        vault_items = []
        if ws["waiting_next_month"]:
            for idx, item in enumerate(ws["waiting_next_month"]):
                vault_items.append(
                    ft.Container(
                        bgcolor=ft.Colors.SURFACE_CONTAINER,
                        border_radius=ft.BorderRadius.all(8),
                        padding=12,
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(item["name"], weight=ft.FontWeight.BOLD),
                                        ft.Text(f"Unlock Condition: {item.get('reason')} (Added: {item.get('created_at')})", size=12, color=ft.Colors.GREY_300),
                                    ],
                                    expand=True,
                                ),
                                ft.FilledButton(
                                    "Budget Arrived? Score Task",
                                    icon=ft.Icons.LOCK_OPEN,
                                    on_click=lambda e, i=idx, it=item: unlock_vault_item(i, it),
                                ),
                            ]
                        ),
                    )
                )

        def unlock_vault_item(idx: int, item: Dict[str, Any]):
            push_undo_state()
            ws["waiting_next_month"].pop(idx)
            # Launch scoring for the unlocked item
            cand = {"name": item["name"], "project": ""}
            # Add to active tasks with default scoring
            cand["why_align"] = 5
            cand["value_impact"] = 5
            cand["urgency_cod"] = 8
            cand["leverage_rroe"] = 5
            cand["confidence"] = 1.0
            cand["duration_rcf"] = 2
            cand["id"] = ws["next_task_id"]
            ws["next_task_id"] += 1
            cand["tpi_score"] = compute_tpi_val(cand, ws["weights"])
            cand["prerequisite_note"] = ""
            cand["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            ws["active_tasks"].append(cand)
            persist_workspace(ws)
            toast(f"Unlocked '{item['name']}' from vault to Active Queue.", action="UNDO", on_action=lambda e: undo())
            render_main()

        vault_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row([
                            ft.Icon(ft.Icons.LOCK_CLOCK, color=ft.Colors.AMBER),
                            ft.Text("[STEP 1] WAITING / NEXT-MONTH VAULT (Budget & Resource Blocked):", weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Column(vault_items if vault_items else [ft.Text("(Waiting vault is currently empty)", italic=True)], spacing=8),
                    ],
                    spacing=10,
                ),
                padding=16,
            )
        )

        # Step 1b: Type 2 Review
        ft_reviews = []
        if ws["fast_track_inbox"]:
            for idx, item in enumerate(ws["fast_track_inbox"]):
                rev_date = item.get("review_date")
                status = tpi_evaluator.format_review_status(rev_date) if rev_date else ""
                ft_reviews.append(
                    ft.Container(
                        bgcolor=ft.Colors.SURFACE_CONTAINER,
                        border_radius=ft.BorderRadius.all(8),
                        padding=12,
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(item["name"], weight=ft.FontWeight.BOLD),
                                        ft.Text(f"Action: {item.get('action')}", size=12, color=ft.Colors.GREY_300),
                                        ft.Text(status, size=12, color=ft.Colors.AMBER_400, weight=ft.FontWeight.BOLD) if status else ft.Container(),
                                    ],
                                    expand=True,
                                ),
                                ft.FilledButton("Review / Decide", icon=ft.Icons.RATE_REVIEW, on_click=lambda e, i=idx, it=item: open_type2_review_dialog(i, it)),
                            ]
                        ),
                    )
                )

        type2_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row([
                            ft.Icon(ft.Icons.SCIENCE_ROUNDED, color=ft.Colors.CYAN),
                            ft.Text("[STEP 1b] TYPE 2 REVERSIBLE EXPERIMENTS REVIEW:", weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Column(ft_reviews if ft_reviews else [ft.Text("(No active experiments due for review)", italic=True)], spacing=8),
                    ],
                    spacing=10,
                ),
                padding=16,
            )
        )

        # Step 2: Urgency Stepping
        urgency_rows = []
        for task in ws["active_tasks"]:
            urg_dropdown = ft.Dropdown(
                options=[
                    ft.dropdown.Option("1", "1 -- No deadline"),
                    ft.dropdown.Option("2", "2 -- Low COI"),
                    ft.dropdown.Option("5", "5 -- Steady Decay / Weekly Leak"),
                    ft.dropdown.Option("8", "8 -- Closing Window (< 1 week)"),
                    ft.dropdown.Option("13", "13 -- Hard External Deadline"),
                ],
                value=str(int(task["urgency_cod"])),
                width=240,
                on_select=lambda e, t=task: update_task_urgency(t, int(e.control.value)),
            )
            urgency_rows.append(
                ft.Row(
                    [
                        ft.Text(f"[ID {task['id']}] {task['name']}", weight=ft.FontWeight.BOLD, expand=True),
                        urg_dropdown,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )

        def update_task_urgency(task: Dict[str, Any], new_urg: int):
            push_undo_state()
            task["urgency_cod"] = new_urg
            tpi_evaluator.recalculate_all_tpi_scores(ws)
            toast(f"Updated Urgency for '{task['name']}' to {new_urg}. Re-sorted queue.", action="UNDO", on_action=lambda e: undo())
            render_main()

        urgency_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row([
                            ft.Icon(ft.Icons.UPDATE, color=ft.Colors.RED_400),
                            ft.Text("[STEP 2] UPDATE URGENCY SCORES (As deadlines approach: 1 -> 2 -> 5 -> 8 -> 13):", weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Column(urgency_rows if urgency_rows else [ft.Text("(No active tasks to review)", italic=True)], spacing=8),
                    ],
                    spacing=10,
                ),
                padding=16,
            )
        )

        return ft.ListView(
            controls=[vault_card, type2_card, urgency_card],
            spacing=16,
            padding=16,
            expand=True,
        )

    # -----------------------------------------------------------------
    # 7. VIEW: TOP-DOWN FOUNDATION (Menu 5)
    # -----------------------------------------------------------------
    def build_foundation_view() -> ft.Control:
        # Vision edit
        vision_input = ft.TextField(
            label="3-5 Year Vision (Horizon 4-5 | 40k-50k ft)",
            value=ws["vision_horizon_4_5"],
            multiline=True,
            expand=True,
        )

        def save_vision(e):
            val = vision_input.value.strip()
            if val:
                push_undo_state()
                ws["vision_horizon_4_5"] = val
                persist_workspace(ws)
                toast("Saved 3-5 Year Vision!", action="UNDO", on_action=lambda e: undo())
                render_main()

        vision_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row([
                            ft.Icon(ft.Icons.TRACK_CHANGES, color=ft.Colors.PRIMARY),
                            ft.Text("HORIZON 4-5: 3-5 YEAR VISION (Identity, Trajectory & Benchmark Standards)", weight=ft.FontWeight.BOLD),
                        ]),
                        vision_input,
                        ft.Row([ft.FilledButton("Save Vision", icon=ft.Icons.SAVE, on_click=save_vision)], alignment=ft.MainAxisAlignment.END),
                    ],
                    spacing=10,
                ),
                padding=16,
            )
        )

        # Top 5 Goals (Horizon 3)
        goal_inputs = []
        for i in range(5):
            existing_goal = ws["top_5_goals"][i] if i < len(ws["top_5_goals"]) else ""
            clean_text = existing_goal.split(". ", 1)[1] if ". " in existing_goal else existing_goal
            goal_inputs.append(ft.TextField(label=f"Goal #{i+1} (12-24 Months)", value=clean_text, expand=True))

        def save_goals(e):
            new_goals = []
            for i, tf in enumerate(goal_inputs, 1):
                txt = tf.value.strip()
                if txt:
                    new_goals.append(f"{i}. {txt}")
            push_undo_state()
            ws["top_5_goals"] = new_goals
            persist_workspace(ws)
            toast(f"Saved {len(new_goals)} Core Goals (Horizon 3)!", action="UNDO", on_action=lambda e: undo())
            render_main()

        goals_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row([
                            ft.Icon(ft.Icons.FLAG, color=ft.Colors.AMBER),
                            ft.Text("HORIZON 3: TOP 5 CORE GOALS (12-24 Months -- Buffett 25/5 Strategy)", weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Column(goal_inputs, spacing=8),
                        ft.Row([ft.FilledButton("Save Top 5 Goals", icon=ft.Icons.SAVE, on_click=save_goals)], alignment=ft.MainAxisAlignment.END),
                    ],
                    spacing=10,
                ),
                padding=16,
            )
        )

        # Active Projects (Horizon 1)
        new_proj_input = ft.TextField(label="Add New Active Project", expand=True)

        def add_project(e):
            txt = new_proj_input.value.strip()
            if txt:
                push_undo_state(f"Added Project: '{txt}'")
                ws["active_projects"].append(txt)
                persist_workspace(ws)
                new_proj_input.value = ""
                toast(f"Added Project: '{txt}'", action="UNDO", on_action=lambda e: undo())
                render_main()

        def remove_project(idx: int):
            removed = ws["active_projects"][idx]
            push_undo_state(f"Removed Project: '{removed}'")
            ws["active_projects"].pop(idx)
            persist_workspace(ws)
            toast(f"Removed Project: '{removed}'", action="UNDO", on_action=lambda e: undo())
            render_main()

        proj_items = []
        for idx, p in enumerate(ws["active_projects"]):
            proj_items.append(
                ft.Row(
                    [
                        ft.Text(f"[{idx+1}] {p}", weight=ft.FontWeight.W_500, expand=True),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, tooltip="Remove Project", on_click=lambda e, i=idx: remove_project(i)),
                    ]
                )
            )

        projects_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row([
                            ft.Icon(ft.Icons.FOLDER_SPECIAL, color=ft.Colors.CYAN),
                            ft.Text("HORIZON 1: ACTIVE PROJECTS (<12 Months / 2-8 Week Milestones)", weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Row([new_proj_input, ft.FilledButton("Add", icon=ft.Icons.ADD, on_click=add_project)]),
                        ft.Column(proj_items if proj_items else [ft.Text("(No active projects set yet)", italic=True)], spacing=6),
                    ],
                    spacing=10,
                ),
                padding=16,
            )
        )

        # Daily Autopilot Habits (Horizon 2) with Reorder Controls
        new_habit_input = ft.TextField(label="Add Daily Baseline Habit", expand=True)

        def add_habit(e):
            txt = new_habit_input.value.strip()
            if txt:
                push_undo_state(f"Added Habit: '{txt}'")
                ws["daily_autopilot_habits"].append(txt)
                persist_workspace(ws)
                new_habit_input.value = ""
                toast(f"Added Habit: '{txt}'", action="UNDO", on_action=lambda e: undo())
                render_main()

        def remove_habit(idx: int):
            removed = ws["daily_autopilot_habits"][idx]
            push_undo_state(f"Removed Habit: '{removed}'")
            ws["daily_autopilot_habits"].pop(idx)
            persist_workspace(ws)
            toast(f"Removed Habit: '{removed}'", action="UNDO", on_action=lambda e: undo())
            render_main()

        def make_habit_first(idx: int):
            promoted = ws["daily_autopilot_habits"][idx]
            push_undo_state(f"Promoted Habit #1: '{promoted}'")
            ws["daily_autopilot_habits"].pop(idx)
            ws["daily_autopilot_habits"].insert(0, promoted)
            persist_workspace(ws)
            toast(f"'{promoted}' is now Habit #1 (DO FIRST)!", action="UNDO", on_action=lambda e: undo())
            render_main()

        def move_habit(idx: int, direction: int):
            target = idx + direction
            if 0 <= target < len(ws["daily_autopilot_habits"]):
                push_undo_state("Reordered Habits")
                ws["daily_autopilot_habits"][idx], ws["daily_autopilot_habits"][target] = (
                    ws["daily_autopilot_habits"][target],
                    ws["daily_autopilot_habits"][idx],
                )
                persist_workspace(ws)
                toast("Habits reordered.", action="UNDO", on_action=lambda e: undo())
                render_main()

        habit_items = []
        for idx, h in enumerate(ws["daily_autopilot_habits"]):
            is_first = (idx == 0)
            habit_items.append(
                ft.Row(
                    [
                        ft.Chip(label=ft.Text("DO FIRST"), bgcolor=ft.Colors.RED_900) if is_first else ft.Chip(label=ft.Text(f"#{idx+1}")),
                        ft.Text(h, weight=ft.FontWeight.W_500, expand=True),
                        ft.IconButton(ft.Icons.VERTICAL_ALIGN_TOP, tooltip="Make #1 (DO FIRST)", on_click=lambda e, i=idx: make_habit_first(i)) if not is_first else ft.Container(),
                        ft.IconButton(ft.Icons.ARROW_UPWARD, tooltip="Move Up", on_click=lambda e, i=idx: move_habit(i, -1)) if idx > 0 else ft.Container(),
                        ft.IconButton(ft.Icons.ARROW_DOWNWARD, tooltip="Move Down", on_click=lambda e, i=idx: move_habit(i, 1)) if idx < len(ws["daily_autopilot_habits"]) - 1 else ft.Container(),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, tooltip="Remove", on_click=lambda e, i=idx: remove_habit(i)),
                    ]
                )
            )

        habits_mgmt_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row([
                            ft.Icon(ft.Icons.SETTINGS_BACKUP_RESTORE, color=ft.Colors.GREEN_400),
                            ft.Text("HORIZON 2: FIXED DAILY AUTOPILOT HABITS (Organize & Reorder Sequence)", weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Row([new_habit_input, ft.FilledButton("Add", icon=ft.Icons.ADD, on_click=add_habit)]),
                        ft.Column(habit_items if habit_items else [ft.Text("(No habits set yet)", italic=True)], spacing=6),
                    ],
                    spacing=10,
                ),
                padding=16,
            )
        )

        return ft.ListView(
            controls=[vision_card, goals_card, projects_card, habits_mgmt_card],
            spacing=16,
            padding=16,
            expand=True,
        )

    # -----------------------------------------------------------------
    # 7b. VIEW: HABIT ANALYTICS & ATTENTION PROTECTION ENGINE
    # -----------------------------------------------------------------
    analytics_period_days = 14

    def build_analytics_view() -> ft.Control:
        nonlocal analytics_period_days
        analytics = tpi_evaluator.calculate_habit_analytics(ws, days=analytics_period_days)
        habits = ws.get("daily_autopilot_habits", [])
        streaks = tpi_evaluator.calculate_habit_streaks(ws)
        habit_settings = ws.get("habit_settings", {})
        review_time = habit_settings.get("review_time", "21:00")
        notifs_enabled = habit_settings.get("enable_notifications", True)

        def set_period(days: int):
            nonlocal analytics_period_days
            analytics_period_days = days
            render_main()

        period_segmented = ft.SegmentedButton(
            selected=[str(analytics_period_days)],
            segments=[
                ft.Segment(value="7", label=ft.Text("7 Days")),
                ft.Segment(value="14", label=ft.Text("14 Days")),
                ft.Segment(value="30", label=ft.Text("30 Days")),
            ],
            on_change=lambda e: set_period(int(list(e.control.selected)[0])) if e.control.selected else None,
        )

        header_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Row([
                                    ft.Icon(ft.Icons.INSIGHTS_ROUNDED, color=ft.Colors.PRIMARY, size=26),
                                    ft.Column([
                                        ft.Text("HORIZON 2 HABIT ANALYTICS & ATTENTION ENGINE", weight=ft.FontWeight.BOLD, size=16),
                                        ft.Text("Empirical tracking & cognitive diagnostics from 'Task Prioritization and Evaluation Systems'", size=12, color=ft.Colors.GREY_300),
                                    ], spacing=2),
                                ], spacing=10),
                                period_segmented,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            wrap=True,
                        ),
                    ],
                    spacing=8,
                ),
                padding=16,
            )
        )

        def make_kpi_card(title: str, val: str, sub: str, icon: ft.Icons, color: ft.Colors):
            return ft.Card(
                expand=True,
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Row([ft.Icon(icon, color=color, size=20), ft.Text(title, weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.GREY_300)], alignment=ft.MainAxisAlignment.START),
                            ft.Text(val, weight=ft.FontWeight.BOLD, size=24, color=color),
                            ft.Text(sub, size=11, color=ft.Colors.GREY_400),
                        ],
                        spacing=4,
                    ),
                    padding=14,
                ),
            )

        kpis_row = ft.Row(
            [
                make_kpi_card("CURRENT STREAK", f"{analytics['current_streak']} Days", "Target: >= 75% completed daily", ft.Icons.LOCAL_FIRE_DEPARTMENT_ROUNDED, ft.Colors.AMBER_400),
                make_kpi_card("BEST STREAK", f"{analytics['best_streak']} Days", "Longest automaticity run", ft.Icons.EMOJI_EVENTS_ROUNDED, ft.Colors.YELLOW_400),
                make_kpi_card("PERIOD ADHERENCE", f"{analytics['avg_completion_rate']*100:.0f}%", f"Logged across {analytics['logged_days']} days", ft.Icons.TRENDING_UP_ROUNDED, ft.Colors.GREEN_400),
                make_kpi_card("FOCUS SAVED", f"~{analytics['time_saved_mins_per_day']}m/day", "Gloria Mark context penalty avoided", ft.Icons.SHIELD_ROUNDED, ft.Colors.CYAN_400),
            ],
            spacing=12,
        )

        daily_records = analytics["daily_records"]
        chart_bars = []
        for rec in daily_records:
            rate = rec["rate"]
            is_logged = rec["is_logged"]
            d_str = rec["date"]
            day_name = rec["day_name"]

            if not is_logged:
                bar_color = ft.Colors.SURFACE_CONTAINER_HIGHEST
                border_side = ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)
                label_text = "-"
            elif rate >= 1.0:
                bar_color = ft.Colors.GREEN_ACCENT_700
                border_side = None
                label_text = "100%"
            elif rate >= 0.75:
                bar_color = ft.Colors.TEAL_400
                border_side = None
                label_text = f"{int(rate*100)}%"
            elif rate >= 0.50:
                bar_color = ft.Colors.AMBER_400
                border_side = None
                label_text = f"{int(rate*100)}%"
            else:
                bar_color = ft.Colors.RED_400
                border_side = None
                label_text = f"{int(rate*100)}%"

            bar_height = max(6, int(rate * 100)) if is_logged else 6
            notes_snippet = f"\nNotes: {rec['notes']}" if rec['notes'] else ""
            status_desc = f"{len(rec['completed'])}/{rec['total']} Routines Done ({rate*100:.0f}%)" if is_logged else "Not logged yet"
            tooltip_msg = f"{d_str} ({day_name})\n{status_desc}{notes_snippet}\n[Click to log or edit]"

            bar_col = ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK,
                tooltip=tooltip_msg,
                on_tap=lambda e, d=d_str: open_habit_review_dialog(d),
                content=ft.Column(
                    [
                        ft.Text(label_text, size=9, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_300),
                        ft.Container(
                            width=28,
                            height=105,
                            alignment=ft.Alignment(0, 1),
                            content=ft.Container(
                                width=24,
                                height=bar_height,
                                bgcolor=bar_color,
                                border=ft.Border.all(border_side.width, border_side.color) if border_side else None,
                                border_radius=ft.BorderRadius.vertical(top=4, bottom=2),
                            ),
                        ),
                        ft.Text(d_str[5:], size=10, weight=ft.FontWeight.W_500),
                        ft.Text(day_name, size=9, color=ft.Colors.GREY_400),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                ),
            )
            chart_bars.append(bar_col)

        legend_row = ft.Row(
            [
                ft.Row([ft.Container(width=12, height=12, bgcolor=ft.Colors.GREEN_ACCENT_700, border_radius=2), ft.Text("100% Perfect", size=11)]),
                ft.Row([ft.Container(width=12, height=12, bgcolor=ft.Colors.TEAL_400, border_radius=2), ft.Text(">=75% High", size=11)]),
                ft.Row([ft.Container(width=12, height=12, bgcolor=ft.Colors.AMBER_400, border_radius=2), ft.Text(">=50% Moderate", size=11)]),
                ft.Row([ft.Container(width=12, height=12, bgcolor=ft.Colors.RED_400, border_radius=2), ft.Text("<50% Low", size=11)]),
                ft.Row([ft.Container(width=12, height=12, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, border=ft.Border.all(1, ft.Colors.OUTLINE), border_radius=2), ft.Text("Unlogged", size=11)]),
            ],
            spacing=14,
            wrap=True,
        )

        chart_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Row([
                                    ft.Icon(ft.Icons.BAR_CHART_ROUNDED, color=ft.Colors.CYAN),
                                    ft.Text(f"DAILY HABIT COMPLETION RATE TREND (Last {analytics_period_days} Days):", weight=ft.FontWeight.BOLD),
                                ]),
                                ft.Row(
                                    [
                                        ft.OutlinedButton("Purge Past Test Data", icon=ft.Icons.AUTO_DELETE_OUTLINED, style=ft.ButtonStyle(color=ft.Colors.AMBER_400), tooltip="Delete seeded test logs prior to today (e.g. 10-23 to 10-29)", on_click=lambda e: open_purge_past_habit_data_dialog()),
                                        ft.FilledTonalButton("Manage & Delete Logs", icon=ft.Icons.LIST_ALT_ROUNDED, tooltip="Audit, edit or delete specific date records", on_click=lambda e: open_manage_habit_logs_dialog()),
                                        ft.FilledButton("Log Today", icon=ft.Icons.CHECK, on_click=lambda e: open_habit_review_dialog()),
                                    ],
                                    spacing=8,
                                    wrap=True,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            wrap=True,
                        ),
                        ft.Text("Click any day's bar to view reflection notes or update check-ins.", size=11, color=ft.Colors.GREY_400),
                        ft.Container(
                            content=ft.Row(chart_bars, spacing=8, scroll=ft.ScrollMode.AUTO),
                            padding=ft.Padding.symmetric(vertical=8),
                        ),
                        legend_row,
                    ],
                    spacing=8,
                ),
                padding=16,
            )
        )

        breakdown_rows = []
        for h in analytics["habit_breakdown"]:
            tier_color = ft.Colors.GREEN_400 if h["tier_code"] == "OPTIMAL" else (ft.Colors.CYAN_300 if h["tier_code"] == "FORMING" else ft.Colors.RED_400)
            chip_bg = ft.Colors.GREEN_900 if h["tier_code"] == "OPTIMAL" else (ft.Colors.CYAN_900 if h["tier_code"] == "FORMING" else ft.Colors.RED_900)
            first_badge = ft.Chip(label=ft.Text("DO FIRST", size=9), bgcolor=ft.Colors.RED_900) if h["is_first"] else None

            breakdown_rows.append(
                ft.Container(
                    bgcolor=ft.Colors.SURFACE_CONTAINER,
                    border_radius=8,
                    padding=12,
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Row([
                                        ft.Text(f"[Routine {h['index']}] {h['name']}", weight=ft.FontWeight.BOLD),
                                        first_badge if first_badge else ft.Container(),
                                    ], spacing=6),
                                    ft.Chip(label=ft.Text(h["tier"], size=10, color=tier_color), bgcolor=chip_bg),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                wrap=True,
                            ),
                            ft.ProgressBar(value=h["rate"], color=tier_color, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST),
                            ft.Row(
                                [
                                    ft.Text(f"Adherence: {h['completed_count']} / {h['total_days']} Days Logged", size=11, color=ft.Colors.GREY_400),
                                    ft.Text(f"{h['rate']*100:.1f}%", weight=ft.FontWeight.BOLD, size=12, color=tier_color),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                        ],
                        spacing=6,
                    ),
                )
            )

        breakdown_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row([
                            ft.Icon(ft.Icons.CHECKLIST_ROUNDED, color=ft.Colors.AMBER),
                            ft.Text("ROUTINE-BY-ROUTINE ADHERENCE & AUTOMATICITY TIERS:", weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Column(breakdown_rows if breakdown_rows else [ft.Text("(No habits configured yet)", italic=True)], spacing=8),
                    ],
                    spacing=10,
                ),
                padding=16,
            )
        )

        history_map = ws.get("habit_history", {})
        today_date = datetime.now().date()
        heatmap_days = [today_date - timedelta(days=i) for i in range(27, -1, -1)]

        day_headers = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        header_cells = [ft.Container(width=34, height=20, alignment=ft.Alignment(0, 0), content=ft.Text(d, size=10, color=ft.Colors.GREY_400, weight=ft.FontWeight.BOLD)) for d in day_headers]

        heatmap_rows = [ft.Row(header_cells, spacing=4)]
        week_cells = []
        for d in heatmap_days:
            d_str = d.strftime("%Y-%m-%d")
            entry = history_map.get(d_str)
            if not entry:
                c_color = ft.Colors.SURFACE_CONTAINER_HIGHEST
                c_border = ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
                t_msg = f"{d_str} ({d.strftime('%a')}): Not logged"
            else:
                c_border = None
                r = entry.get("rate", 0.0)
                if r >= 1.0:
                    c_color = ft.Colors.GREEN_600
                elif r >= 0.75:
                    c_color = ft.Colors.TEAL_600
                elif r >= 0.5:
                    c_color = ft.Colors.AMBER_700
                else:
                    c_color = ft.Colors.RED_800
                t_msg = f"{d_str} ({d.strftime('%a')}): {entry.get('completed_count', len(entry.get('completed', [])))}/{entry.get('total', len(habits))} Done ({r*100:.0f}%)"

            tile = ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK,
                tooltip=f"{t_msg}\nClick to log/edit",
                on_tap=lambda e, dt=d_str: open_habit_review_dialog(dt),
                content=ft.Container(
                    width=34,
                    height=30,
                    bgcolor=c_color,
                    border=c_border,
                    border_radius=4,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text(str(d.day), size=10, color=ft.Colors.ON_SURFACE),
                ),
            )
            week_cells.append(tile)
            if len(week_cells) == 7:
                heatmap_rows.append(ft.Row(list(week_cells), spacing=4))
                week_cells.clear()
        if week_cells:
            heatmap_rows.append(ft.Row(list(week_cells), spacing=4))

        heatmap_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row([
                            ft.Icon(ft.Icons.CALENDAR_MONTH_ROUNDED, color=ft.Colors.PRIMARY),
                            ft.Text("28-DAY CONSISTENCY HEATMAP (Daily Execution Matrix):", weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Column(heatmap_rows, spacing=4),
                    ],
                    spacing=10,
                ),
                padding=16,
            )
        )

        insights_controls = []
        morning_rate = analytics.get("morning_anchor_rate", 0.0)
        evening_rate = analytics.get("evening_anchor_rate", 0.0)
        insights_controls.append(
            ft.Container(
                bgcolor=ft.Colors.SURFACE_CONTAINER,
                border_radius=8,
                padding=12,
                content=ft.Column(
                    [
                        ft.Row([
                            ft.Icon(ft.Icons.PSYCHOLOGY_ROUNDED, color=ft.Colors.CYAN),
                            ft.Text("Decision Fatigue & Diurnal Willpower (Research Finding: Page 2)", weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Text(
                            f"Morning Anchor Routine #1 Adherence: {morning_rate*100:.0f}%  |  Evening Routine Adherence: {evening_rate*100:.0f}%\n"
                            "The research report documents that decision fatigue accumulates toward the end of the day. "
                            "Morning routines benefit from cognitive surplus after sleep, which is why Routine #1 is strictly designated '[DO FIRST]'.",
                            size=12,
                            color=ft.Colors.GREY_300,
                        ),
                    ],
                    spacing=6,
                ),
            )
        )

        if analytics["strategic_withdrawal_alerts"]:
            for alert in analytics["strategic_withdrawal_alerts"]:
                insights_controls.append(
                    ft.Container(
                        bgcolor=ft.Colors.RED_900,
                        border_radius=8,
                        padding=12,
                        content=ft.Column(
                            [
                                ft.Row([
                                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.AMBER_400),
                                    ft.Text(f"Strategic Withdrawal Recommended: Routine #{alert['index']} '{alert['habit']}'", weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_200),
                                ]),
                                ft.Text(
                                    f"Status: {alert['reason']}\n"
                                    f"Protocol (Research Page 19): In GTD Horizon 2, baseline routines are meant to maintain your engine, not induce psychological guilt. "
                                    f"{alert['recommendation']}",
                                    size=12,
                                    color=ft.Colors.GREY_300,
                                ),
                            ],
                            spacing=6,
                        ),
                    )
                )
        else:
            insights_controls.append(
                ft.Container(
                    bgcolor=ft.Colors.GREEN_900,
                    border_radius=8,
                    padding=12,
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_400),
                        ft.Text("Optimal Baseline Stability: All active routines maintain healthy automaticity without excessive friction.", size=12, color=ft.Colors.GREEN_200),
                    ], spacing=8),
                )
            )

        insights_controls.append(
            ft.Container(
                bgcolor=ft.Colors.SURFACE_CONTAINER,
                border_radius=8,
                padding=12,
                content=ft.Column(
                    [
                        ft.Row([
                            ft.Icon(ft.Icons.TIMER_OUTLINED, color=ft.Colors.TEAL_300),
                            ft.Text("Attention Hygiene & Context-Switch Protection (Gloria Mark, 2008)", weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Text(
                            f"Saved: ~{analytics['time_saved_mins_per_day']} minutes per day.\n"
                            "Each daytime interruption to log or verify a task inflicts an average 23m 15s recovery penalty to resume deep focus. "
                            "By batching habit reflection to a single end-of-day checkpoint, your daytime cognitive capacity is fully reserved for Layer 1 Frog execution.",
                            size=12,
                            color=ft.Colors.GREY_300,
                        ),
                    ],
                    spacing=6,
                ),
            )
        )

        research_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row([
                            ft.Icon(ft.Icons.AUTO_STORIES_ROUNDED, color=ft.Colors.PRIMARY),
                            ft.Text("COGNITIVE SCIENCE & STRATEGIC INSIGHTS:", weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Column(insights_controls, spacing=8),
                    ],
                    spacing=10,
                ),
                padding=16,
            )
        )

        review_time_dropdown = ft.Dropdown(
            label="Daily Evening Review Time",
            options=[
                ft.dropdown.Option("18:00", "18:00 (6:00 PM) - Workday Close"),
                ft.dropdown.Option("19:00", "19:00 (7:00 PM) - Evening Triage"),
                ft.dropdown.Option("20:00", "20:00 (8:00 PM) - Post-Dinner"),
                ft.dropdown.Option("20:30", "20:30 (8:30 PM)"),
                ft.dropdown.Option("21:00", "21:00 (9:00 PM) - Screen Wind-Down"),
                ft.dropdown.Option("21:30", "21:30 (9:30 PM)"),
                ft.dropdown.Option("22:00", "22:00 (10:00 PM) - Bedtime Reflection"),
                ft.dropdown.Option("22:30", "22:30 (10:30 PM)"),
            ],
            value=review_time,
            width=280,
        )

        def on_time_select(e):
            push_undo_state("Updated Review Time")
            ws.setdefault("habit_settings", {})["review_time"] = e.control.value
            persist_workspace(ws)
            toast(f"Review notification scheduled for {e.control.value} daily.")
            render_main()

        review_time_dropdown.on_select = on_time_select

        notif_switch = ft.Switch(
            label="Windows Desktop Toast Notifications",
            value=notifs_enabled,
        )

        def on_notif_toggle(e):
            push_undo_state("Toggled Notifications")
            ws.setdefault("habit_settings", {})["enable_notifications"] = e.control.value
            persist_workspace(ws)
            toast(f"Notifications {'enabled' if e.control.value else 'disabled'}.")
            render_main()

        notif_switch.on_change = on_notif_toggle

        def on_test_notif(e):
            ok = tpi_evaluator.send_system_notification(
                "TPI Habit Review Reminder (Test)",
                f"This is a test notification! Your daily habit review is set for {review_time}.",
            )
            if ok:
                toast("Desktop notification fired successfully! Check your Windows Action Center.")
            else:
                toast("Could not trigger toast. Please verify Windows Notification settings.", is_error=True)

        def on_seed_demo(e):
            push_undo_state("Seeded Demo Habit History")
            tpi_evaluator.seed_demo_habit_history(ws, 14)
            toast("Seeded 14 days of realistic habit history for demonstration!", action="UNDO", on_action=lambda ev: undo())
            render_main()

        def on_clear_history(e):
            def confirm_clear(ev):
                push_undo_state("Cleared Habit History")
                ws["habit_history"] = {}
                persist_workspace(ws)
                close_dialog()
                toast("Cleared all habit history.", action="UNDO", on_action=lambda ev2: undo())
                render_main()

            show_dialog(
                "Clear Habit History?",
                ft.Text("Are you sure you want to clear all recorded habit logs? This cannot be undone except via undo."),
                [
                    ft.TextButton("Cancel", on_click=lambda ev: close_dialog()),
                    ft.FilledButton("Yes, Clear History", bgcolor=ft.Colors.RED_900, on_click=confirm_clear),
                ],
            )

        settings_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row([
                            ft.Icon(ft.Icons.SETTINGS_ROUNDED, color=ft.Colors.PRIMARY),
                            ft.Text("NOTIFICATION & SCHEDULE CONTROLS:", weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Row([review_time_dropdown, notif_switch], alignment=ft.MainAxisAlignment.START, spacing=16, wrap=True),
                        ft.Row(
                            [
                                ft.FilledTonalButton("Test Windows Toast", icon=ft.Icons.NOTIFICATIONS_ACTIVE, on_click=on_test_notif),
                            ],
                            wrap=True,
                        ),
                        ft.Divider(),
                        ft.Row([
                            ft.Icon(ft.Icons.STORAGE_ROUNDED, color=ft.Colors.CYAN),
                            ft.Text("HABIT DATA MANAGEMENT & REVERSIBILITY (Research Doc p. 18):", weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Row(
                            [
                                ft.OutlinedButton("Purge Past Test Data", icon=ft.Icons.AUTO_DELETE_OUTLINED, style=ft.ButtonStyle(color=ft.Colors.AMBER_400), tooltip="Delete seeded test logs (10-23 to 10-29) and preserve today", on_click=lambda e: open_purge_past_habit_data_dialog()),
                                ft.FilledTonalButton("Manage & Delete Date Logs", icon=ft.Icons.LIST_ALT_ROUNDED, tooltip="Audit, edit or delete specific date records", on_click=lambda e: open_manage_habit_logs_dialog()),
                                ft.OutlinedButton("Seed 14-Day Demo History", icon=ft.Icons.PLAYLIST_ADD_CHECK, on_click=on_seed_demo),
                                ft.TextButton("Clear All Habit History", icon=ft.Icons.DELETE_OUTLINE, style=ft.ButtonStyle(color=ft.Colors.RED_400), on_click=on_clear_history),
                            ],
                            wrap=True,
                            spacing=10,
                        ),
                    ],
                    spacing=12,
                ),
                padding=16,
            )
        )

        return ft.ListView(
            controls=[
                header_card,
                kpis_row,
                chart_card,
                heatmap_card,
                breakdown_card,
                research_card,
                settings_card,
            ],
            spacing=16,
            padding=16,
            expand=True,
        )

    # -----------------------------------------------------------------
    # 8. VIEW: VAULTS, AVOID LIST & RCF HISTORY (Menu 6)
    # -----------------------------------------------------------------
    def build_vaults_and_history_view() -> ft.Control:
        # 1. Waiting vault
        def remove_waiting_item(idx: int):
            removed = ws["waiting_next_month"][idx]
            tpi_evaluator.commit_history_node(
                history_tree,
                ws,
                title=f"Pre-Pruning: Waiting Vault '{removed['name']}'",
                tag="TYPE 1 SAFEGUARD",
                reason=f"Safeguard prior to removing '{removed['name']}' from Waiting Vault",
            )
            push_undo_state(f"Removed '{removed['name']}' from Waiting Vault")
            ws["waiting_next_month"].pop(idx)
            persist_workspace(ws)
            toast(f"Removed from Waiting Vault: '{removed['name']}'", action="UNDO", on_action=lambda e: undo())
            render_main()

        vault_items = [
            ft.Row(
                [
                    ft.Text(f"• {item['name']} (Unlocks: {item.get('reason')})", expand=True),
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE,
                        tooltip="Remove from Waiting Vault",
                        icon_color=ft.Colors.GREY_400,
                        on_click=lambda e, i=idx: remove_waiting_item(i),
                    ),
                ]
            )
            for idx, item in enumerate(ws["waiting_next_month"])
        ]
        vault_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row([ft.Icon(ft.Icons.LOCK), ft.Text("1. WAITING / NEXT-MONTH VAULT (Budget Constrained):", weight=ft.FontWeight.BOLD)]),
                        ft.Column(vault_items if vault_items else [ft.Text("(Empty)", italic=True)]),
                    ],
                    spacing=8,
                ),
                padding=16,
            )
        )

        # 2. 25/5 Avoid list
        def remove_avoid_item(idx: int):
            removed = ws["avoid_25_5_list"][idx]
            tpi_evaluator.commit_history_node(
                history_tree,
                ws,
                title=f"Pre-Pruning: Avoid Item '{removed}'",
                tag="TYPE 1 SAFEGUARD",
                reason=f"Safeguard prior to removing '{removed}' from 25/5 Avoid List",
            )
            push_undo_state(f"Removed '{removed}' from Avoid List")
            ws["avoid_25_5_list"].pop(idx)
            persist_workspace(ws)
            toast(f"Removed from Avoid List: '{removed}'", action="UNDO", on_action=lambda e: undo())
            render_main()

        avoid_items = [
            ft.Row(
                [
                    ft.Text(f"• {a}", expand=True),
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE,
                        tooltip="Remove from Avoid List",
                        icon_color=ft.Colors.RED_400,
                        on_click=lambda e, i=idx: remove_avoid_item(i),
                    ),
                ]
            )
            for idx, a in enumerate(ws["avoid_25_5_list"])
        ]
        avoid_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row([ft.Icon(ft.Icons.BLOCK, color=ft.Colors.RED_400), ft.Text("2. BUFFETT 25/5 AVOID-AT-ALL-COSTS LIST (Goals 6-25):", weight=ft.FontWeight.BOLD)]),
                        ft.Column(avoid_items if avoid_items else [ft.Text("(Empty)", italic=True)]),
                    ],
                    spacing=8,
                ),
                padding=16,
            )
        )

        # 3. 90% Dropped list
        def remove_dropped_item(idx: int):
            removed = ws.get("dropped_90_rule", [])[idx]
            tpi_evaluator.commit_history_node(
                history_tree,
                ws,
                title=f"Pre-Pruning: Dropped Item '{removed}'",
                tag="TYPE 1 SAFEGUARD",
                reason=f"Safeguard prior to removing '{removed}' from 90% Dropped List",
            )
            push_undo_state(f"Removed '{removed}' from Dropped List")
            ws.get("dropped_90_rule", []).pop(idx)
            persist_workspace(ws)
            toast(f"Removed from Dropped List: '{removed}'", action="UNDO", on_action=lambda e: undo())
            render_main()

        dropped_items = [
            ft.Row(
                [
                    ft.Text(f"• {d}", expand=True),
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE,
                        tooltip="Remove from Dropped List",
                        icon_color=ft.Colors.AMBER_400,
                        on_click=lambda e, i=idx: remove_dropped_item(i),
                    ),
                ]
            )
            for idx, d in enumerate(ws.get("dropped_90_rule", []))
        ]
        dropped_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row([ft.Icon(ft.Icons.HIGHLIGHT_OFF, color=ft.Colors.AMBER_400), ft.Text("3. MCKEOWN 90% RULE DROPPED LIST:", weight=ft.FontWeight.BOLD)]),
                        ft.Column(dropped_items if dropped_items else [ft.Text("(Empty)", italic=True)]),
                    ],
                    spacing=8,
                ),
                padding=16,
            )
        )

        # 4. RCF History Table & Deletion Controls (Type 1 Decision Safeguards)
        def open_delete_single_history_dialog(idx: int):
            if idx < 0 or idx >= len(ws["rcf_history"]):
                return
            target_entry = ws["rcf_history"][idx]
            task_name = target_entry.get("name", "Task")
            completed_date = target_entry.get("completed_at", "N/A")
            est_fib = target_entry.get("estimated_fib", "-")
            act_fib = target_entry.get("actual_fib", "-")
            notes = target_entry.get("actual_notes", "")

            def submit_single_delete(e):
                tpi_evaluator.commit_history_node(
                    history_tree,
                    ws,
                    title=f"Pre-Deletion: Task History '{task_name}'",
                    tag="TYPE 1 SAFEGUARD",
                    reason=f"Safeguard prior to deleting RCF record for '{task_name}'",
                )
                push_undo_state(f"Deleted task history: '{task_name}'")
                ws["rcf_history"].pop(idx)
                persist_workspace(ws)
                close_dialog()
                toast(f"Deleted task history: '{task_name}'", action="UNDO", on_action=lambda e: undo())
                render_main()

            dlg_content = ft.Container(
                content=ft.Column(
                    [
                        ft.Text(f"Delete task history record for '{task_name}'?", weight=ft.FontWeight.BOLD, size=15),
                        ft.Text(
                            f"• Completed Date: {completed_date}\n"
                            f"• Duration: Estimated {est_fib} Fib → Actual {act_fib} Fib\n"
                            f"• Notes: {notes if notes else 'None'}",
                            size=12,
                            color=ft.Colors.GREY_300,
                        ),
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.AMBER_400),
                                    ft.Text(
                                        "Type 1 Reversibility Warning (Research Doc p. 6 & 18):\n"
                                        "Under the Reversibility Filter (Jeff Bezos / Research Paper p. 6), "
                                        "deleting baseline data removes empirical reference points for "
                                        "Reference Class Forecasting (RCF), which protects against the Planning Fallacy.\n\n"
                                        "You can restore this record using Undo (Ctrl+Z) immediately after deletion.",
                                        size=11,
                                        color=ft.Colors.AMBER_100,
                                        expand=True,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.START,
                            ),
                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                            padding=10,
                            border_radius=8,
                        ),
                    ],
                    spacing=12,
                ),
                width=480,
            )

            actions = [
                ft.TextButton("Cancel", on_click=lambda e: close_dialog()),
                ft.FilledButton(
                    "Delete Entry",
                    icon=ft.Icons.DELETE_FOREVER,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED_800),
                    on_click=submit_single_delete,
                ),
            ]
            show_dialog("Delete Task History Entry", dlg_content, actions)

        def open_clear_all_history_dialog():
            if not ws["rcf_history"]:
                return
            total_count = len(ws["rcf_history"])

            def submit_clear_all(e):
                tpi_evaluator.commit_history_node(
                    history_tree,
                    ws,
                    title=f"Pre-Purge: All {total_count} Task History Records",
                    tag="TYPE 1 SAFEGUARD",
                    reason="Safeguard prior to clearing all RCF task completion logs",
                )
                push_undo_state(f"Cleared all {total_count} task history records")
                ws["rcf_history"] = []
                persist_workspace(ws)
                close_dialog()
                toast(f"Cleared all {total_count} task history records.", action="UNDO", on_action=lambda e: undo())
                render_main()

            dlg_content = ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            f"Permanently clear all {total_count} task history records?",
                            weight=ft.FontWeight.BOLD,
                            size=15,
                        ),
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.DANGEROUS_ROUNDED, color=ft.Colors.RED_400),
                                    ft.Text(
                                        "Type 1 Reversibility Warning (One-Way Door - Research Doc p. 6):\n"
                                        "Purging all RCF task completion logs wipes the entire historical dataset. "
                                        "Future Fibonacci sizing will lack empirical reference anchors to correct for the Planning Fallacy (p. 7 & 18).\n\n"
                                        "You can restore all records using Undo (Ctrl+Z) immediately after clearing.",
                                        size=11,
                                        color=ft.Colors.RED_100,
                                        expand=True,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.START,
                            ),
                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                            padding=10,
                            border_radius=8,
                        ),
                    ],
                    spacing=12,
                ),
                width=480,
            )

            actions = [
                ft.TextButton("Cancel", on_click=lambda e: close_dialog()),
                ft.FilledButton(
                    "Clear All History",
                    icon=ft.Icons.DELETE_SWEEP,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED_800),
                    on_click=submit_clear_all,
                ),
            ]
            show_dialog("Clear All Task History", dlg_content, actions)

        # 4. RCF History (Type 1 Decision Safeguards)
        rcf_items = []
        for idx, h in enumerate(ws["rcf_history"]):
            t_name = h.get("name", "Task")
            t_date = h.get("completed_at", "N/A")
            est = h.get("estimated_fib", "-")
            act = h.get("actual_fib", "-")
            nt = h.get("actual_notes", "")
            rcf_items.append(
                ft.Container(
                    bgcolor=ft.Colors.SURFACE_CONTAINER,
                    border_radius=8,
                    padding=12,
                    content=ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Text(t_name, weight=ft.FontWeight.BOLD, size=14),
                                            ft.Chip(label=ft.Text(f"Est: {est} Fib → Act: {act} Fib", size=10, color=ft.Colors.GREEN_400)),
                                        ],
                                        spacing=8,
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    ),
                                    ft.Text(f"Completed Date: {t_date}", size=11, color=ft.Colors.GREY_300),
                                    ft.Text(f"Notes: {nt}", size=11, italic=True, color=ft.Colors.GREY_400) if nt else ft.Container(width=0, height=0),
                                ],
                                expand=True,
                                spacing=4,
                            ),
                            ft.IconButton(
                                ft.Icons.DELETE_OUTLINE,
                                icon_color=ft.Colors.RED_400,
                                tooltip="Delete this task history entry",
                                on_click=lambda e, i=idx: open_delete_single_history_dialog(i),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            )

        rcf_header = ft.Row(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.HISTORY_EDU, color=ft.Colors.PRIMARY),
                        ft.Text("4. REFERENCE CLASS FORECASTING (RCF) TASK HISTORY:", weight=ft.FontWeight.BOLD),
                    ],
                    expand=True,
                ),
                ft.OutlinedButton(
                    "Clear All History",
                    icon=ft.Icons.DELETE_SWEEP,
                    style=ft.ButtonStyle(color=ft.Colors.RED_400),
                    tooltip="Clear all task history records (Type 1 operation with undo)",
                    on_click=lambda e: open_clear_all_history_dialog(),
                ) if ws["rcf_history"] else ft.Container(width=0, height=0),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        rcf_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        rcf_header,
                        ft.Column(rcf_items, spacing=8) if rcf_items else ft.Text("(No completed tasks logged yet)", italic=True),
                    ],
                    spacing=8,
                ),
                padding=16,
            )
        )

        # 5. Daily Autopilot Habit History Cards & Controls (Horizon 2 Maintenance History)
        habit_history = ws.get("habit_history", {})
        sorted_habit_dates = sorted(list(habit_history.keys()), reverse=True)
        today_date_str = datetime.now().strftime("%Y-%m-%d")

        def open_delete_single_habit_dialog(dt: str):
            def submit_single_habit_del(e):
                tpi_evaluator.commit_history_node(
                    history_tree,
                    ws,
                    title=f"Pre-Deletion: Habit Log {dt}",
                    tag="TYPE 1 SAFEGUARD",
                    reason=f"Safeguard prior to deleting daily habit record for {dt}",
                )
                push_undo_state(f"Deleted habit log for {dt}")
                tpi_evaluator.delete_habit_log(ws, dt)
                close_dialog()
                toast(f"Deleted habit record for {dt}.", action="UNDO", on_action=lambda ev: undo())
                render_main()

            entry_data = habit_history.get(dt, {})
            c_list = entry_data.get("completed", [])
            tot = entry_data.get("total", len(ws.get("daily_autopilot_habits", [])))
            rate_pct = int(entry_data.get("rate", 0.0) * 100)
            nt = entry_data.get("notes", "")

            dlg_content = ft.Container(
                content=ft.Column(
                    [
                        ft.Text(f"Delete daily habit log for '{dt}'?", weight=ft.FontWeight.BOLD, size=15),
                        ft.Text(
                            f"• Completion: {len(c_list)}/{tot} Done ({rate_pct}%)\n"
                            f"• Routines: {', '.join(c_list) if c_list else '(None)'}\n"
                            f"• Reflection Notes: {nt if nt else 'None'}",
                            size=12,
                            color=ft.Colors.GREY_300,
                        ),
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.AMBER_400),
                                    ft.Text(
                                        "Two-Way Door Safeguard (Research Doc pp. 6, 18):\n"
                                        "Deleting this log updates streaks and trend graphs. "
                                        "You can restore it via Undo (Ctrl+Z) immediately after deletion.",
                                        size=11,
                                        color=ft.Colors.AMBER_100,
                                        expand=True,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.START,
                            ),
                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                            padding=10,
                            border_radius=8,
                        ),
                    ],
                    spacing=12,
                ),
                width=480,
            )

            actions = [
                ft.TextButton("Cancel", on_click=lambda e: close_dialog()),
                ft.FilledButton(
                    "Delete Entry",
                    icon=ft.Icons.DELETE_FOREVER,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED_800),
                    on_click=submit_single_habit_del,
                ),
            ]
            show_dialog(f"Delete Habit Record: {dt}", dlg_content, actions)

        habit_item_controls = []
        for dt in sorted_habit_dates:
            entry = habit_history[dt]
            rate = entry.get("rate", 0.0)
            completed_list = entry.get("completed", [])
            total_habits = entry.get("total", len(ws.get("daily_autopilot_habits", [])))
            notes_str = entry.get("notes", "")

            rate_color = ft.Colors.GREEN_400 if rate >= 1.0 else (ft.Colors.TEAL_400 if rate >= 0.75 else (ft.Colors.AMBER_400 if rate >= 0.5 else ft.Colors.RED_400))
            badge_bg = ft.Colors.GREEN_900 if rate >= 1.0 else (ft.Colors.TEAL_900 if rate >= 0.75 else (ft.Colors.AMBER_900 if rate >= 0.5 else ft.Colors.RED_900))
            is_today = (dt == today_date_str)

            date_header_row = [
                ft.Text(dt, weight=ft.FontWeight.BOLD, size=14),
                ft.Container(
                    content=ft.Text(f"{len(completed_list)}/{total_habits} Done ({int(rate*100)}%)", size=10, weight=ft.FontWeight.BOLD, color=rate_color),
                    bgcolor=badge_bg,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    border_radius=6,
                ),
            ]
            if is_today:
                date_header_row.append(
                    ft.Container(
                        content=ft.Text("TODAY", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN),
                        bgcolor=ft.Colors.CYAN_900,
                        padding=ft.Padding.symmetric(horizontal=6, vertical=3),
                        border_radius=4,
                    )
                )

            col_details = [
                ft.Row(date_header_row, spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Text(
                    f"Completed Routines: {', '.join(completed_list) if completed_list else '(None)'}",
                    size=11,
                    color=ft.Colors.GREY_300,
                ),
            ]
            if notes_str:
                col_details.append(
                    ft.Text(
                        f"Reflection Notes: {notes_str}",
                        size=11,
                        italic=True,
                        color=ft.Colors.GREY_400,
                    )
                )

            habit_item_controls.append(
                ft.Container(
                    bgcolor=ft.Colors.SURFACE_CONTAINER,
                    border_radius=8,
                    padding=12,
                    content=ft.Row(
                        [
                            ft.Column(col_details, expand=True, spacing=4),
                            ft.Row(
                                [
                                    ft.IconButton(
                                        ft.Icons.EDIT_OUTLINED,
                                        tooltip=f"Edit {dt} Review",
                                        icon_size=20,
                                        on_click=lambda e, d=dt: open_habit_review_dialog(d),
                                    ),
                                    ft.IconButton(
                                        ft.Icons.DELETE_OUTLINE,
                                        icon_color=ft.Colors.RED_400,
                                        icon_size=20,
                                        tooltip=f"Delete habit record for {dt}",
                                        on_click=lambda e, d=dt: open_delete_single_habit_dialog(d),
                                    ),
                                ],
                                spacing=0,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            )

        habit_action_buttons = []
        if sorted_habit_dates:
            habit_action_buttons.append(
                ft.OutlinedButton(
                    "Purge Past Test Data",
                    icon=ft.Icons.AUTO_DELETE_OUTLINED,
                    style=ft.ButtonStyle(color=ft.Colors.AMBER_400),
                    tooltip="Delete all past demo logs prior to today (e.g. 10-23 to 10-29)",
                    on_click=lambda e: open_purge_past_habit_data_dialog(),
                )
            )
        habit_action_buttons.append(
            ft.FilledTonalButton(
                "Manage Date Logs",
                icon=ft.Icons.LIST_ALT_ROUNDED,
                tooltip="Open full habit logs audit and deletion modal",
                on_click=lambda e: open_manage_habit_logs_dialog(),
            )
        )
        if sorted_habit_dates:
            habit_action_buttons.append(
                ft.OutlinedButton(
                    "Clear All Habit History",
                    icon=ft.Icons.DELETE_SWEEP,
                    style=ft.ButtonStyle(color=ft.Colors.RED_400),
                    tooltip="Clear all habit completion logs (Type 1 operation with undo)",
                    on_click=lambda e: open_manage_habit_logs_dialog(),
                )
            )

        habit_header = ft.Row(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.BAR_CHART_ROUNDED, color=ft.Colors.CYAN),
                        ft.Text(f"5. DAILY AUTOPILOT HABIT LOGS (Horizon 2 Maintenance History · {len(sorted_habit_dates)} Days):", weight=ft.FontWeight.BOLD),
                    ],
                    expand=True,
                ),
                ft.Row(
                    habit_action_buttons,
                    spacing=8,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        habit_history_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        habit_header,
                        ft.Text(
                            "Research Grounding (Page 19: Horizon 2 Maintenance & Strategic Withdrawal):\n"
                            "Daily autopilot routines maintain baseline cognitive capacity. Purging irregular or demo data "
                            "ensures adherence analytics accurately reflect true habits.",
                            size=11,
                            color=ft.Colors.GREY_300,
                        ),
                        ft.Column(habit_item_controls, spacing=8) if habit_item_controls else ft.Text("(No habit history logged yet)", italic=True),
                    ],
                    spacing=8,
                ),
                padding=16,
            )
        )

        return ft.ListView(
            controls=[vault_card, avoid_card, dropped_card, rcf_card, habit_history_card],
            spacing=16,
            padding=16,
            expand=True,
        )

    # -----------------------------------------------------------------
    # 9. VIEW: CONFIGURE WEIGHTS (Menu 7)
    # -----------------------------------------------------------------
    def build_weights_view() -> ft.Control:
        w = ws["weights"]

        w1_slider = ft.Slider(min=1, max=5, divisions=4, value=w["w1"], label="{value}")
        w2_slider = ft.Slider(min=1, max=5, divisions=4, value=w["w2"], label="{value}")
        w3_slider = ft.Slider(min=1, max=5, divisions=4, value=w["w3"], label="{value}")
        w4_slider = ft.Slider(min=1, max=5, divisions=4, value=w["w4"], label="{value}")

        def apply_balanced(e):
            push_undo_state()
            ws["weights"] = {"w1": 1.0, "w2": 1.0, "w3": 1.0, "w4": 1.0}
            tpi_evaluator.recalculate_all_tpi_scores(ws)
            persist_workspace(ws)
            toast("Weights reset to Balanced Mode (Default WSJF: W1=1, W2=1, W3=1, W4=1)!", action="UNDO", on_action=lambda e: undo())
            render_main()

        def apply_custom(e):
            push_undo_state()
            ws["weights"] = {
                "w1": float(w1_slider.value),
                "w2": float(w2_slider.value),
                "w3": float(w3_slider.value),
                "w4": float(w4_slider.value),
            }
            tpi_evaluator.recalculate_all_tpi_scores(ws)
            persist_workspace(ws)
            toast("Hierarchical Weights saved & active task scores recalculated!", action="UNDO", on_action=lambda e: undo())
            render_main()

        weights_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("CRITERIA CLARITY PROTOCOL: PRE-FIXED WEIGHTS", weight=ft.FontWeight.BOLD, size=16),
                        ft.Text("Define criterion importance before evaluating candidates to prevent confirmation bias.", italic=True),
                        ft.Divider(),
                        ft.Text("Preset: Balanced Mode (Default WSJF)", weight=ft.FontWeight.BOLD),
                        ft.FilledTonalButton("Set Balanced Weights (1.0 each)", icon=ft.Icons.BALANCE, on_click=apply_balanced),
                        ft.Divider(),
                        ft.Text("Custom Hierarchical Mode (1 to 5):", weight=ft.FontWeight.BOLD),
                        ft.Text("W1 - Strategic Alignment & Consequence (Why_Align):"),
                        w1_slider,
                        ft.Text("W2 - Direct Payoff & Impact (Value_Impact):"),
                        w2_slider,
                        ft.Text("W3 - Time Criticality & Cost of Inaction (Urgency_CoD):"),
                        w3_slider,
                        ft.Text("W4 - Domino Leverage & Risk Reduction (Leverage_RR/OE):"),
                        w4_slider,
                        ft.FilledButton("Save Hierarchical Weights & Recalculate", icon=ft.Icons.SAVE, on_click=apply_custom),
                    ],
                    spacing=12,
                ),
                padding=20,
            )
        )

        return ft.ListView(
            controls=[weights_card],
            spacing=16,
            padding=16,
            expand=True,
        )

    # =================================================================
    # NAVIGATION & SHELL ROUTING
    # =================================================================

    content_area = ft.Container(expand=True)

    def navigate_to(index: int):
        nonlocal current_nav_index
        current_nav_index = index
        render_main()

    def toggle_theme():
        page.theme_mode = ft.ThemeMode.LIGHT if page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
        page.update()

    def render_main():
        # Undo button styling & context
        last_desc = (
            undo_stack[-1].get("description", "last action")
            if (undo_stack and isinstance(undo_stack[-1], dict))
            else "last action"
        )
        undo_control = (
            ft.FilledTonalButton(
                f"Undo ({len(undo_stack)})",
                icon=ft.Icons.UNDO_ROUNDED,
                tooltip=f"Undo: {last_desc} (Ctrl+Z)",
                on_click=lambda e: undo(),
            )
            if len(undo_stack) > 0
            else ft.IconButton(
                ft.Icons.UNDO_ROUNDED,
                tooltip="Undo (Ctrl+Z) - Nothing to undo",
                disabled=True,
            )
        )

        history_control = ft.IconButton(
            ft.Icons.HISTORY_ROUNDED,
            tooltip=f"Action History & Rollback ({len(undo_stack)} steps)",
            disabled=len(undo_stack) == 0,
            on_click=lambda e: open_history_rollback_dialog(),
        )

        history_tree_control = ft.FilledTonalButton(
            f"History Tree ({len(history_tree.get('nodes', {}))})",
            icon=ft.Icons.ACCOUNT_TREE_ROUNDED,
            tooltip="Two-Way Door History Tree & Checkpoints (Macro Time-Travel)",
            on_click=lambda e: open_history_tree_dialog(),
        )

        # Update top appbar
        page.appbar = ft.AppBar(
            leading=ft.Icon(ft.Icons.AUTO_GRAPH_ROUNDED, color=ft.Colors.PRIMARY),
            title=ft.Column(
                [
                    ft.Text("TPI Persistent Command Center", weight=ft.FontWeight.BOLD, size=18),
                    ft.Text("True Priority Index | Research-Backed Altitude Architecture", size=11, color=ft.Colors.GREY_400),
                ],
                spacing=1,
            ),
            actions=[
                undo_control,
                history_tree_control,
                history_control,
                ft.IconButton(
                    ft.Icons.STORAGE_ROUNDED,
                    tooltip="Workspace & App Data Management",
                    on_click=lambda e: open_workspace_data_manager_dialog(),
                ),
                ft.IconButton(
                    ft.Icons.REDO_ROUNDED,
                    tooltip="Redo action (Ctrl+Y)",
                    disabled=len(redo_stack) == 0,
                    on_click=lambda e: redo(),
                ),
                ft.IconButton(ft.Icons.HELP_OUTLINE, tooltip="Research Methodology Guide [H]", on_click=lambda e: open_research_guide_dialog()),
                ft.IconButton(
                    ft.Icons.DARK_MODE if page.theme_mode == ft.ThemeMode.LIGHT else ft.Icons.LIGHT_MODE,
                    tooltip="Toggle Dark/Light Mode",
                    on_click=lambda e: toggle_theme(),
                ),
                ft.Container(width=10),
            ],
            bgcolor=ft.Colors.SURFACE_CONTAINER,
        )

        # Update body view
        if current_nav_index == 0:
            content_area.content = build_dashboard_view()
        elif current_nav_index == 1:
            content_area.content = build_add_tasks_view()
        elif current_nav_index == 2:
            content_area.content = build_weekly_review_view()
        elif current_nav_index == 3:
            content_area.content = build_foundation_view()
        elif current_nav_index == 4:
            content_area.content = build_analytics_view()
        elif current_nav_index == 5:
            content_area.content = build_vaults_and_history_view()
        elif current_nav_index == 6:
            content_area.content = build_weights_view()

        # Navigation Rail (Desktop)
        nav_rail = ft.NavigationRail(
            selected_index=current_nav_index,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=90,
            destinations=[
                ft.NavigationRailDestination(icon=ft.Icons.DASHBOARD_ROUNDED, label="Dashboard"),
                ft.NavigationRailDestination(icon=ft.Icons.ADD_TASK_ROUNDED, label="Add Tasks"),
                ft.NavigationRailDestination(icon=ft.Icons.EVENT_REPEAT_ROUNDED, label="Review"),
                ft.NavigationRailDestination(icon=ft.Icons.ACCOUNT_TREE_ROUNDED, label="Foundation"),
                ft.NavigationRailDestination(icon=ft.Icons.INSIGHTS_ROUNDED, label="Analytics"),
                ft.NavigationRailDestination(icon=ft.Icons.INVENTORY_2_ROUNDED, label="Memory"),
                ft.NavigationRailDestination(icon=ft.Icons.TUNE_ROUNDED, label="Weights"),
            ],
            on_change=lambda e: navigate_to(e.control.selected_index),
        )

        page.controls.clear()
        page.controls.append(
            ft.Row(
                [
                    nav_rail,
                    ft.VerticalDivider(width=1),
                    content_area,
                ],
                expand=True,
                spacing=0,
            )
        )
        page.update()

    # Initial render
    render_main()


if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    else:
        ft.app(target=main)
