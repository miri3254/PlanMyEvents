---
name: vertical-slice
description: Add or change a persisted field/feature end-to-end in PlanMyEvents (SQLAlchemy model, Alembic migration, Pydantic schema, service/router, Angular API type, UI mapping, backup/exports, tests). Use whenever a task adds/renames a DB column, API field or form field.
---
# Vertical slice checklist (do in order; skip layers that truly don't apply and say so)
Find files via `docs/ai/codemap.md` table. Grep, don't read big files whole.

1. **Model** `FastAPI/app/models/<x>.py` — nullable or with server default so old rows stay valid.
2. **Migration** `FastAPI/alembic/versions/<rev>_<name>.py` — `down_revision` = current head (`grep -l "down_revision" ...` / codemap). Additive only; no data rewrite of approved snapshots. For the local DB copy the `scripts/apply_*_migration.py` pattern (backup SQLite first). Ask before applying to `FastAPI/data/planmyevents.db`.
3. **Schema** `FastAPI/app/schemas/<x>.py` — Create/Update/Response; snake_case.
4. **Service/router** — logic in service; router thin. Formulas only in services/`*_rules.py`.
5. **Frontend contract** `Angular/src/app/core/models/api.models.ts` (+ `index.ts` wrapper if the UI uses camelCase type).
6. **API service** `Angular/src/app/services/api-<x>.service.ts`.
7. **UI mapping both directions** (API→form and form→payload) in the component; check null/0/false survive a save round trip. Hebrew labels, PrimeNG, RTL.
8. **Exports/backup**: backup_service.py, excel-export.service.ts, pdf_generator/routers/events.py if the field should appear in documents.
9. **Tests**: one focused backend test (isolated `DATABASE_URL=sqlite://`) + the component spec if UI logic changed; `npx tsc -p tsconfig.app.json --noEmit` in Angular.
10. Update `docs/ai/codemap.md` only if files/key functions changed; then `/close-task`.
