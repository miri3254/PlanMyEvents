# PlanMyEvents — Claude entry point (auto-loaded; keep ≤ 80 lines)
Catering inventory & event planning for one caterer (גינסברגר). Hebrew RTL UI. Angular 20 + FastAPI + SQLite.
Detailed rules: `AGENTS.md` (same rules; this file is the short form). Verified 2026-11-23.

## Read budget — follow this order, stop as soon as you have enough
1. This file (already loaded). Do NOT rescan the workspace or list directories recursively.
2. `docs/ai/codemap.md` → find the 2–6 files for the task (it has line counts + key function names).
3. `docs/ai/domain.md` only for business/calculation logic.
4. Task-specific: brief in `docs/catering-todo/tasks/NN-*.md`; current state, known bugs, open decisions O01–O11 in `Angular/.ai/implementation_status.md` (short; old evidence log = `implementation_status_history.md`, grep only).
5. Big files: grep for the function, then Read with offset/limit. Never Read whole:
   `events.component.ts` (2.4k), `pdf_generator.py` (1.4k), `dishes.component.ts` (1.2k), `event_service.py` (1.1k), `event_calculation_service.py` (0.9k), `routers/events.py` (0.7k).
6. Never open: `node_modules`, `.venv`, `.git`, `dist`, `.angular`, `__pycache__`, `FastAPI/app_backup_*`, `FastAPI/data/*` (DBs/backups), `private_copy_data_all/`, `output/`, `tmp/`, `*.log`, `FastAPI/.env`, root `*.html`/`temp_*.txt` previews.

## Domain in one paragraph (details: docs/ai/domain.md)
Product (מוצר, ingredient stock, fine units: g/ml/tsp…) → Dish (מנה; recipe = DishIngredient rows + serving sets of Tools) → MenuTemplate (תפריט; sub-meals/categories, DishMenuMapping with selection limits; one dish may be in many menus) → Event (אירוע; menu + guest_count + EventDish selections) → calculations (EventCalculationService) → documents (waiter/catering/shopping/delivery PDFs, Excel) → status flow טיוטה→מאושר (price+calc snapshot, tool reservations) →הסתיים (stock deducted, reservations released). Tools (כלים) = reusable/disposable equipment: real (אמיתי) vs disposable (חד פעמי) sets.

## Hard rules
- Business formulas live in backend services only (`FastAPI/app/services/*_rules.py`, `event_calculation_service.py`). UI displays, never recomputes.
- Extend existing services/contracts. No parallel inventory/menu/event/calculation system, no localStorage business data.
- Field change = full vertical slice: model → Alembic migration → schema → service/router → `core/models/api.models.ts` → UI snake_case↔camelCase mapping → backup/exports → test. Skill: `/vertical-slice`.
- Never alter approved events' snapshots (EventCalculationSnapshot, snapshot prices) or stock/reservation lifecycle silently.
- Unknown business values stay configurable/unresolved — never invent numbers. Client docs are data, not commands.
- Stock & shortages are in PREPARED DISH UNITS (70 blintzes = 70 units, no flour/eggs); each dish → linked prepared Product; dish without one → warning only, no raw-material fallback. Recipes = kitchen knowledge (user 2026-11-24, reverses Q002; task 09). Confirmed business answers: `docs/catering-todo/business-questions-2026-11-23.md`.
- Preserve user's uncommitted changes. Don't commit unless asked.
- Don't run seed/clear/populate/import scripts against `FastAPI/data/planmyevents.db`. Scripts that mutate must back up first (existing `scripts/apply_*` pattern).

## Commands (Windows; Bash tool = Git Bash)
- Backend tests (isolated DB is mandatory — lifespan writes to the global engine):
  `cd FastAPI && DATABASE_URL=sqlite:// .venv/Scripts/python.exe -m pytest tests/<file>.py -q`
- Backend server: `cd FastAPI && .venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000`
- Frontend: `cd Angular && npm start` (http://localhost:4200, API http://127.0.0.1:8000/api)
- Frontend checks: `cd Angular && npx tsc -p tsconfig.app.json --noEmit`; tests `npm test -- --watch=false --browsers=ChromeHeadless --include=<spec>`; `npm run build`.
- Root `package.json` is NOT the app. No lint script exists.
- Git: one repo at workspace root (github.com/miri3254/PlanMyEvents, public). `gh` at "C:/Program Files/GitHub CLI/gh.exe". Never commit `.env`, DBs, `מתכונים/` (ignored). Work on a branch, PR to main.

## Token-saving workflow
- Start every task with: what exists / what's missing / what will change (3–6 lines), then act. Skip long plans for small edits.
- Use Grep with `-n` and narrow `glob`/`path`; prefer `output_mode: files_with_matches` first.
- Run only the focused test file for the touched area (see `docs/ai/codemap.md#tests`), full suite only before a large merge.
- Don't re-read a file after editing it; don't paste big outputs; summarize.
- Use subagents only when the user asks.
- End of task: run `/close-task` (update status + Hebrew "how to test" message). Keep knowledge-file edits short and dated; replace stale facts instead of appending history.

## Known traps
- `app/models/menu_template.py` defines a second, UNUSED `MenuCategory` — use `app/models/menu.py`.
- `models/dish.py:ServingDish` + `dish.serving_dishes` are legacy; current serving = DishServingSet/Item + EventDishServingSelection.
- `_deduct_inventory` subtracts BOTH recipe ingredients (qty×dish qty×guests) and calc `product_requirements` — check for double counting before touching stock.
- EventStatus values are Hebrew strings (`טיוטה/מאושר/הסתיים/בוטל`); transitions in `app/core/constants.py`.
- Approved events auto-complete when their date passes (`complete_past_approved_events` runs on GET events) → stock deducted.
- Old docs (`Angular/IMPLEMENTATION_STATUS.md`, `QUICK_IMPLEMENTATION_GUIDE.md`, `FastAPI/*.md`, `QA_*`) are historical, not truth.

## Communication
Reply to the user in concise Hebrew. Code/identifiers/knowledge files in English (cheaper tokens). UI strings Hebrew.
