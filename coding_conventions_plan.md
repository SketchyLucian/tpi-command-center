# Coding Conventions Refactoring Plan for `tpi_evaluator.py`

## Audit Summary

After cross-referencing the codebase against the coding convention skills (naming, layout, design principles, error handling, documentation, project structure) and validating all changes against the **Research Document** ("Task Prioritization and Evaluation Systems"), here are the issues found and the planned fixes.

> [!IMPORTANT]
> All changes preserve the research document's architecture: Gate 0 → Layer 1 (TPI Scoring) → Layer 2 (Daily Execution). No domain logic is altered.

---

## 1. Naming Conventions

| Current Name | Issue | Proposed Name | Rationale |
|---|---|---|---|
| `ask_choice` | Vague — doesn't describe *what* is being chosen | `prompt_score_selection` | S-I-D: describes the action (prompt) + domain (score selection) |
| `ask_yes_no` | Acceptable but inconsistent with the rename pattern | `prompt_yes_no` | Consistent verb prefix with `prompt_score_selection` |
| `compute_tpi` | Acceptable ✅ | Keep | Clear domain action |
| `recalculate_all` | Vague "all" | `recalculate_all_tpi_scores` | Explicit about what is recalculated |
| `show_dashboard` | OK but passive | `display_dashboard` | Action verb consistency |
| `screen_single_task_gate_zero` | Too long, mixes detail level | `screen_task_through_gate_zero` | Slightly clearer verb-object shape |
| `score_candidates` | OK ✅ | Keep | Clear domain action |
| `add_tasks_menu` | OK ✅ | Keep | |
| `complete_task_menu` | OK ✅ | Keep | |
| `weekly_review_menu` | OK ✅ | Keep | |
| `manage_foundation_menu` | OK ✅ | Keep | |
| `view_vaults_and_history` | OK ✅ | Keep | |
| `configure_weights_menu` | OK ✅ | Keep | |
| `select_review_date` | OK ✅ | Keep | |
| `format_review_status` | OK ✅ | Keep | |
| `w` (line 373) | Single-letter variable | `weights` | Descriptive, no abbreviation |
| `c` (multiple lines) | Single-letter variable in menus | `choice` | Descriptive |
| `h` (multiple lines) | Single-letter variable | `habit` | Descriptive |
| `p` (multiple lines) | Single-letter variable | `project` | Descriptive |
| `g` (multiple lines) | Single-letter variable | `goal` | Descriptive |
| `t` (multiple lines) | Single-letter variable | `task` | Descriptive |
| `v` (line 819) | Single-letter variable | `vision_text` | Descriptive |
| `raw` (line 675) | Ambiguous in context | `user_input` | Clearer intent |
| `sub` (line 836) | Abbreviation | `sub_choice` | Clearer |
| `rem` (line 845) | Abbreviation | `remove_index` | Clearer |
| `rev_date` (multiple) | Abbreviation | `review_date` | Full word |
| `dep_marker` (line 410) | OK but abbreviated | `dependency_marker` | Full word |
| Magic string `"tpi_workspace.json"` | Module-level constant, OK ✅ | Keep `DATA_FILE` | Already a named constant |

---

## 2. Code Layout Conventions

### Issues Found:
- **Deep nesting** in `complete_task_menu` (line 684–695): nested `if/elif` inside `if` with string parsing
- **Giant function**: `manage_foundation_menu` (lines 794–863) — mixes menu display, input handling, and data mutation in one 70-line function
- **No whitespace grouping** in `show_dashboard` — visual phases (habits, fast-track, tasks, execution plan) are delimited only by comments, not blank lines with clear phase markers
- **Missing guard clauses** in several functions (e.g., `score_candidates` could early-return on empty candidates more prominently)
- **`screen_single_task_gate_zero`** is 85 lines — acceptable for a sequential gate filter, but could benefit from clearer phase markers

### Fixes:
- Add blank-line phase separators with inline phase comments in `show_dashboard`
- Extract `_handle_fast_track_completion` helper from `complete_task_menu`
- Add guard clauses where applicable
- Add whitespace grouping in `manage_foundation_menu`

---

## 3. Error Handling Conventions

### Issues Found:
- **Silent `pass` in encoding setup** (line 21–22): `except Exception: pass` — swallows errors silently
- **Bare `except Exception as e`** in `load_workspace` (line 225): catches everything including `KeyboardInterrupt` if not careful (though `Exception` does exclude `BaseException`)
- **No validation** of workspace data integrity on load — corrupt JSON keys cause silent `KeyError` crashes later
- **No error handling** in `save_workspace` — filesystem errors (disk full, permissions) crash silently

### Fixes:
- Add logging/warning for encoding setup failure
- Add explicit `(json.JSONDecodeError, IOError)` catch in `load_workspace`
- Add `IOError` handling in `save_workspace`
- Add workspace schema validation on load

---

## 4. Documentation Conventions

### Issues Found:
- **Module docstring** exists and is good ✅
- **Most functions lack docstrings** — only `select_review_date` and `format_review_status` have them
- **No docstrings** on `compute_tpi`, `save_workspace`, `load_workspace`, `show_dashboard`, etc.
- `screen_single_task_gate_zero` has a good docstring ✅
- **Comments narrating obvious code** (e.g., "# 1. Fixed Daily Autopilot Habits") — these are acceptable as section markers in a CLI dashboard

### Fixes:
- Add docstrings to all public functions explaining purpose, parameters, and return values
- Keep section marker comments (they serve as visual phase separators in the dashboard)

---

## 5. Design Principles

### Issues Found:
- **SRP**: `main()` is clean — just a dispatcher loop ✅
- **DRY**: The pattern of printing lists with indices repeats across multiple menu functions — could extract a helper, but the repetition is harmless and local
- **YAGNI**: No speculative abstractions ✅
- **KISS**: Overall good — the linear gate filter is straightforward ✅

### Fixes:
- Minor: extract `_print_numbered_list` for repeated list-display pattern (optional, low priority)

---

## Execution Plan

The changes will be applied in this order:
1. **Naming**: Rename functions and variables for clarity
2. **Documentation**: Add docstrings to all public functions
3. **Error handling**: Improve exception handling in I/O functions
4. **Layout**: Add phase separators, extract helpers, add guard clauses
