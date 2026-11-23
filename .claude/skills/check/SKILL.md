---
name: check
description: Run the cheapest sufficient verification for PlanMyEvents changes (focused pytest with isolated DB, Angular type-check, focused spec, build). Use after code edits before reporting done.
---
# Focused checks — pick only what matches the touched files
Backend (any FastAPI/app change) — ALWAYS isolated DB, set before import:
```
cd FastAPI && DATABASE_URL=sqlite:// .venv/Scripts/python.exe -m pytest tests/<matching_file>.py -q
```
Mapping: calc/rules → test_event_calculations.py + test_<topic>_workbook.py · serving → test_serving_alternatives.py · events CRUD/status/stock → test_deep_crud_flows.py · delivery PDF → test_delivery_sheet_pdf.py · fees/presets/tool import → test_workbook_remaining.py.
Import smoke (when no test fits): `DATABASE_URL=sqlite:// .venv/Scripts/python.exe -c "import app.main"`.

Frontend (any Angular/src change):
```
cd Angular && npx tsc -p tsconfig.app.json --noEmit
cd Angular && npm test -- --watch=false --browsers=ChromeHeadless --include=src/app/components/<name>/**/*.spec.ts
```
`npm run build` only for routing/config/large changes (production build may fail on Google Fonts TLS — known, not your bug).

PDF changes: generate the PDF from a test DB and look at it (Read the PDF) — byte success ≠ correct RTL layout.
UI behavior: only if asked or risky — start servers (see CLAUDE.md) and use the built-in browser.

Report: list exactly which commands ran and pass/fail counts; say what was NOT checked.
