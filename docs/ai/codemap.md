# Code map — where things are (verified 2026-11-23)
Line counts tell you whether to Read whole (<300) or grep + offset/limit (≥300). Paths workspace-relative.
Update this file when you add/move/delete a file or a key function. Do not add history here.

## Task → files (open these first, nothing else)
| Task | Backend | Frontend | Test |
|---|---|---|---|
| Event fields/details | models/event.py, schemas/event.py, services/event_service.py `create_event/update_event/_build_response` | components/events/events.component.ts (grep mapping fn), services/api-event.service.ts | test_deep_crud_flows.py |
| Event dish selection | event_service `add_dish_to_event/bulk_save_dishes/finalize_drafts`, models/menu.py (quota) | components/event-dish-wizard/ | events/wizard specs |
| Calculations (drinks/rolls/tablecloths/tools/fees) | services/event_calculation_service.py `summarize` + `*_rules.py` | events.component.ts calc panel | test_event_calculations.py, test_*_workbook.py |
| Workbook formula presets | services/workbook_rules.py, routers/dishes.py `/calculation-presets` | dishes.component.ts rules editor | test_workbook_remaining.py |
| Serving tools / sets | models/calculation.py DishServingSet*, calc `_calculate_serving_sets/_resolve_serving_set` | dishes.component.ts, event-dish-wizard | test_serving_alternatives.py |
| Menus | models/menu.py, services/menu_service.py, routers/menus.py | components/menus/, services/api-menu.service.ts, models/menu.model.ts | menus spec |
| Dishes/recipes | models/dish.py, services/dish_service.py, routers/dishes.py | components/dishes/ | dishes spec |
| Products/stock | models/product.py, services/product_service.py, unit_conversion_service.py | components/products/ | products spec |
| Tools/equipment | models/tool.py, services/tool_service.py | components/tools/ | tools spec |
| Status lifecycle / stock deduction | event_service `change_status/_snapshot_prices/_deduct_inventory/restore_stock/complete_past_approved_events`, calc `snapshot_event/release_reservations`, core/constants.py | events.component.ts | test_deep_crud_flows.py |
| Pricing / credit fee | event_service `_recalc_total`, calc `_calculate_credit_card_fee`, workbook_rules (installments) | events.component.ts | test_workbook_remaining.py |
| Shopping list | event_service `get_shopping_list/_merge_shopping_items` (~L861-1033), routers/events.py shopping-pdf | events.component.ts | — |
| PDFs | utils/pdf_generator.py (`generate_waiter_pdf` L660, `generate_shopping_pdf` L903, `generate_delivery_sheet_pdf` L1211), assembled in routers/events.py (delivery L356, waiter L395, catering L533, shopping L665) | api-event.service.ts | test_delivery_sheet_pdf.py |
| Excel export / backup | services/backup_service.py, routers/backup.py | services/excel-export.service.ts, backup.service.ts, components/backup/ | backup spec |
| Receipts OCR (AI) | services/ocr_service.py, receipt_ai_service.py, ollama_service.py, routers/receipts.py | components/receipt-scan-dialog/, services/inventory.service.ts | — |
| Dashboard | services/dashboard_service.py, routers/dashboard.py | components/dashboard/ | dashboard spec |
| Lookups/settings | routers/lookup.py, models/lookup.py | components/settings/settings.ts, core/services/lookup.service.ts | — |

## Backend `FastAPI/app/` (routers -> services -> repositories/models; schemas = Pydantic contracts)
- main.py (105): app, `/api` prefix, lifespan create_all + unit-conversion seed. `/api/health`.
- core/: config.py (DATABASE_URL default `sqlite:///FastAPI/data/planmyevents.db`, env-overridable), enums.py (EventStatus Hebrew values, UnitType, ProductCategory, ToolCategory/SubCategory, KosherType), constants.py (ALLOWED_STATUS_TRANSITIONS).
- db/: base.py, engine.py, session.py = active wiring (core/database.py is a thin legacy shim).
- models/: event.py (216: Event, EventOwner, EventDish[is_gift, quantity, snapshot prices], EventTraySelection, DeliveryNoteTemplate, EventDeliveryNote, EventBox) · menu.py (119: MenuTemplate[min_guests, tablecloth_profile, table_setting_items], MenuSubMeal, MenuCategory[quota, tray_quantity, tray_price], DishMenuMapping) · dish.py (84: Dish[base_price, client_price, serving_size], DishIngredient[quantity, unit, is_serving_component], legacy ServingDish) · product.py (Product[unit, package_quantity, quantity_in_stock, drink_type]) · tool.py (Tool[category, sub_category, quantity_in_stock]) · calculation.py (122: EventCalculationSettings, EventCalculationSnapshot, DishServingSet[serving_mode]/Item[quantity_basis], EventDishServingSelection, DishCalculationRule, EventManualToolRow, ToolReservation) · unit_conversion.py, lookup.py, audit.py. **menu_template.py = unused duplicate, ignore.**
- services/: event_service.py (1061) · event_calculation_service.py (862) · dashboard_service.py (525) · menu_service.py (469) · unit_conversion_service.py (348) · dish/product/tool_service.py (~100-140) · pure Fraction-based rules: drink_rules.py, roll_rules.py, tablecloth_rules.py, table_setting_rules.py, workbook_rules.py · workbook_tool_import.py · backup_service.py.
- routers/: events.py (717; PDFs assembled here), dishes.py (297), menus.py (216), lookup.py, receipts.py, unit_conversions.py, dashboard.py, products.py, tools.py, backup.py.
- schemas/: event.py (386), dish.py (217), calculation.py (177), dashboard.py, menu.py, product.py, tool.py, receipt.py, unit_conversion.py, common.py.
- utils/pdf_generator.py (1409, ReportLab, Hebrew via `_bidi`, fonts/backgrounds in app/assets/).
- alembic/versions/: head = `o8d9e0f1a2b3_workbook_clearing`. New migration: down_revision = current head; additive; local apply via scripts/apply_*_migration.py pattern (backup first).
- scripts/: `prepare_*`/`apply_*` are guarded (dry-run + backup). `seed_*`, `clean_wipe_*`, `reset_data`, `new_clear_db` are destructive — only on explicit user request.
- FastAPI/*.py at root (check_*, fix_*, populate_db, clear_db_runner, debug_*) = ad-hoc helpers, not app code.

## Frontend `Angular/src/app/` (standalone, lazy `loadComponent` routes)
- Routes: '' dashboard · dishes · dishes/event/:eventId · events/:eventId/select-dishes (wizard) · products · tools · settings · events · menus · backup.
- components/: events (2397!) · dishes (1181) · menus (831) · settings/settings.ts (810) · tools (741) · dashboard (732 + dashboard.ts 334) · products (725) · event-dish-wizard (550) · backup (266) · receipt-scan-dialog (231).
- services/: api-event (189), api-dish (146), api-lookup, api-menu, api-product, api-tool, api-dashboard, excel-export, backup, inventory (receipts), receipt-scan.
- core/: services/base-api.service.ts (environment.apiUrl), lookup.service.ts (303), unit-conversion, theme, connection-status, storage; models/api.models.ts (770, snake_case API contracts), index.ts (UI wrappers), enums.ts; constants/app.constants.ts; utils/hebrew-date.util.ts.
- models/menu.model.ts is still used — check imports before adding types.
- shared/: components/navigation (778), loading-overlay. Theme tokens: src/styles.scss.

## Tests
Backend `FastAPI/tests/` (always `DATABASE_URL=sqlite://` before import): test_event_calculations.py (engine) · test_drinks_workbook.py · test_rolls_workbook.py · test_tablecloth_workbook.py · test_workbook_remaining.py (presets, fees, tool import) · test_serving_alternatives.py · test_delivery_sheet_pdf.py · test_deep_crud_flows.py (API CRUD + lifecycle) · test_prepare_drink_products.py · test_comprehensive.py.
Frontend: `*.spec.ts` beside each component (11). E2E Playwright in Angular/tests (no webServer/baseURL configured).
