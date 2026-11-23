---
name: calc-rule
description: Add or change a catering calculation (drinks, rolls, tablecloths, table settings, serving tools, dish quantities, fees, stock requirements) in PlanMyEvents. Use for any formula/quantity/rounding change.
---
# Calculation rule workflow
1. **Source first**: find the authoritative value — user decision in chat, workbook review `docs/catering-todo/excel-review-2026-11-17/report.md` (grep the sheet/cell), or task brief. If missing or conflicting → ask the user; never invent a number. Record the source (sheet+cell or quote) in the task file.
2. **Where**: pure formula in a small rules module (`FastAPI/app/services/<topic>_rules.py` or `workbook_rules.py`), wired from `event_calculation_service.py` (grep `def _calculate_<topic>`). Use `fractions.Fraction`; round (ceil/floor per source) only at the end. Profile comes from `_menu_calculation_profile` (menu), not event category.
3. **Don't break**: approved events read `EventCalculationSnapshot` — never recompute or rewrite them. Keep legacy fields readable. Check unit normalization before stock math (`unit_conversion_service`). Check `_deduct_inventory` for double counting if requirements change.
4. **UI**: Angular only displays `calculations/summary` results; no duplicate formula in TS.
5. **Tests**: add cases to the matching `FastAPI/tests/test_<topic>_workbook.py` or `test_event_calculations.py` with source-derived expected values (incl. rounding edges). Run that file only:
   `cd FastAPI && DATABASE_URL=sqlite:// .venv/Scripts/python.exe -m pytest tests/<file>.py -q`
6. Update `docs/ai/domain.md` "Calculation engine" line for the rule (replace, don't append), then `/close-task`.
