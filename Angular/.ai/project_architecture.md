# Project architecture — verified map
2026-11-23: the compact, current index is `docs/ai/codemap.md`; this file keeps detail and history. Trap found: `FastAPI/app/models/menu_template.py` holds an unused duplicate `MenuCategory` (active one: models/menu.py). Alembic head: o8d9e0f1a2b3.
Inspected 2026-11-15 against current working files. Paths below are workspace-relative. Code presence is not runtime verification.

2026-11-17 calculation-workbook audit (analysis only): `docs/catering-todo/excel-review-2026-11-17/report.md` and `report.html` map all 11 original sheets and 176 populated rows to current code. `tasks/19-calculations-workbook-review.md` records scope and checks. No application code was changed. In particular, event serving selections are saved by `event-dish-wizard`, but waiter/catering PDF assembly still reads legacy `dish.serving_dishes`; do not assume it consumes the selected serving set. Product requirement enrichment currently lacks unit normalization before stock subtraction.

## Frontend
- Angular/package.json: Angular ~20.3, PrimeNG 20, RxJS 7.8, TypeScript 5.9, Chart.js, Hebcal, xlsx. Parent package has different dependencies; do not confuse them.
- Angular/src/main.ts -> bootstrapApplication(App, appConfig).
- Angular/src/app/app.config.ts: router, HTTP, animations, Hebrew locale, PrimeNG Aura. No AppModule bootstrap.
- Angular/src/app/app.routes.ts: lazy loadComponent routes for dashboard, dishes, event dish wizard, products, tools, settings, events, menus and backup.
- Angular/src/app/components/events/events.component.ts (+ HTML/SCSS/spec): event editor, API/UI mapping, calculations, delivery fields and exports.
- Angular/src/app/components/event-dish-wizard/: event menu/dish selection.
- Angular/src/app/components/dishes/: dish editor including ingredients/equipment/rules.
- Angular/src/app/components/menus/: templates/categories/mappings; backend supports sub-meals.
- Angular/src/app/components/products/ and tools/: stock/catalog screens.
- Angular/src/app/shared/components/navigation/: navigation; shared/loading-overlay/: shared loading UI.
- Angular/src/app/services/api-{event,dish,product,tool,menu,lookup,dashboard}.service.ts: active domain APIs.
- Angular/src/app/core/services/base-api.service.ts: HTTP base; unit-conversion.service.ts handles unit conversion. The unused profit-calculator.service.ts was removed on 2026-11-17.
- Angular/src/app/core/models/api.models.ts: API contracts; index.ts: frontend wrappers/re-exports; enums.ts: enum values.
- Angular/src/app/models/{dish,product,menu}.model.ts also exist; trace imports before choosing where to add a type.
- EventsComponent uses ApiEventService. The unreferenced localStorage event.service.ts and obsolete models/dish.model.ts and models/product.model.ts were removed on 2026-11-17.
- Angular/src/app/services/inventory.service.ts is receipt inventory integration, not the event calculation engine.
- Angular/src/app/services/excel-export.service.ts and backup.service.ts: exports and data lifecycle.

## Backend
- 2026-11-17 serving tools: task 24 extends DishServingSet with serving_mode and per-dishware defaults. Dish editor manages named inventory links; wizard loads effective selections through GET calculations/dish-serving-selections. EventCalculationService resolves alternatives by is_real_dishes and supports place_setting/serving_group bases. MenuTemplate.table_setting_items (editable menu UI) drives automatic table settings via table_setting_rules.py, with explicit inventory links, unresolved warnings and legacy per-event layout override. Aggregated tool requirements retain contributions for waiter/catering PDF dish rows. Additive migrations m6b7c8d9e0f1 and n7c8d9e0f1a2 applied locally with backups. Historical legacy mapping observations below remain relevant to old data without contribution metadata.
- Rolls: `roll_rules.py` implements original C3:C6 using Fraction and final ceil. `_menu_calculation_profile` is shared by rolls/tablecloths using the persisted internal template classification. No event-category dependency or enable switch for rolls; existing split allocation, stock and snapshot paths remain. Event overview automatically shows total and formula. Task 22 records 148 backend and 12 UI tests.
- Tablecloth UX correction: menu calculation profile is internal/read-only. MenuService assigns it automatically at creation and preserves it on edits; write schemas and menu editor do not expose a choice. Event overview displays the existing summary's tablecloth quantity/formula automatically when event details open.
- Tablecloths: `tablecloth_rules.py` evaluates workbook C3:C6 with Fraction, ceil total base then ceil(base/6) spare. `MenuTemplate.tablecloth_profile` (migration l5a6b7c8d9e0, applied locally with backup) selects the rule via the selected menu, never event_category. Menu APIs/schemas/editor persist it. Existing calculation summaries, tool inventory and approved snapshots remain the integration path. `apply_tablecloth_migration.py` is the guarded local upgrade helper. Task 21 records checks and manual steps.
- Drink catalog preparation: `FastAPI/scripts/prepare_drink_products.py` (dry run by default, `--apply` backs up the configured local SQLite first). Reuses classified/exact-name products, refuses ambiguity, preserves stock/prices/IDs, creates missing types at zero stock, and assigns ProductCategory.DRINKS (`שתיה`). LIQUIDS remains for non-beverage ingredients. Applied locally on 2026-11-17.
- 2026-11-17 drinks implementation: `FastAPI/app/services/drink_rules.py` is the single workbook formula table (C6:G9). Product `drink_type` identifies one active pooled inventory record per type; nullable field + partial unique index added by migration `k4f5a6b7c8d9`. `FastAPI/scripts/apply_drink_inventory_migration.py` supports a guarded local SQLite upgrade with backup. Products UI persists drink_type/camelCase drinkType; events calculation panel exposes the existing morning-split API. Legacy orange_flavored_mode is retained but ignored by new drink calculations; approved snapshots remain unchanged.
- FastAPI/app/main.py: FastAPI app, /api router prefix, lifespan table creation and unit-conversion seed.
- FastAPI/app/routers/: events, dishes, menus, products, tools, lookup, dashboard, backup, unit_conversions, receipts.
- FastAPI/app/services/event_service.py: event CRUD, nested selections, pricing, shopping/equipment lists, lifecycle integration.
- FastAPI/app/services/event_calculation_service.py: requirements, serving sets, drink/roll/tablecloth rules, charges, snapshots, tool reservations.
- FastAPI/app/services/menu_service.py, dish_service.py, product_service.py, tool_service.py: domain workflows.
- FastAPI/app/models/event.py: Event, EventOwner, EventDish (is_gift), trays, boxes/delivery notes.
- FastAPI/app/models/menu.py: MenuTemplate -> MenuSubMeal / MenuCategory -> DishMenuMapping. One dish may map to multiple menus.
- FastAPI/app/models/dish.py: Dish, DishIngredient (is_serving_component), legacy ServingDish.
- FastAPI/app/models/calculation.py: EventCalculationSettings, DishServingSet/Item, EventDishServingSelection, DishCalculationRule, EventManualToolRow, EventCalculationSnapshot, ToolReservation.
- FastAPI/app/schemas/: Pydantic contracts; repositories/: persistence helpers.
- FastAPI/app/db/: active SQLAlchemy wiring. Config defaults to SQLite in FastAPI/data, but .env may override; never assume another .db file is active.
- FastAPI/alembic/versions/: migrations including delivery fields, gifts, serving calculations, serving-component marker, event tool set.
- FastAPI/app/utils/pdf_generator.py: ReportLab Hebrew PDFs, fonts/backgrounds in FastAPI/app/assets/.
- FastAPI/app_backup_20260217_121047/ is backup code, not an implementation target.

## Read only the relevant vertical slice
| Task | First files |
|---|---|
| Menus/import | menus component, api-menu.service.ts, models/menu.py, services/menu_service.py, relevant source |
| Prepared stock/recipes | dishes/products components, models/dish.py + product.py, event_service.get_shopping_list, calculation service |
| Serving/packing | dishes/events components, models/calculation.py, calculation service, events router, pdf_generator |
| Delivery | events component + mapping, models/event.py, schemas/event.py, event_service, delivery PDF |
| Pricing | events component, calculation settings schema/model, event_service._recalc_total, calculation service fee |
| Export/branding | api-event.service.ts, events router, pdf_generator.py, assets, excel-export.service.ts |
| Import reconciliation | relevant source plus מתכונים mapping files; derived mappings are not authoritative |

## Commands and validation
From Angular: npm start; npm run build; npm test -- --watch=false --browsers=ChromeHeadless.
No lint script exists in inspected Angular package; do not invent one.
From FastAPI: .venv/Scripts/python.exe -m pytest tests/test_event_calculations.py -q for calculation changes.
Delivery PDF tests: tests/test_delivery_sheet_pdf.py. API integration: tests/test_deep_crud_flows.py.
Set DATABASE_URL to an isolated temporary database BEFORE app import/startup. Even TestClient dependency overrides do not replace the lifespan global engine.
Frontend E2E: Angular/tests. Playwright config does not start webServer or configure baseURL; inspect test URLs first.
PDF edits require visual RTL/multipage inspection, not just successful byte generation.
Documentation-only changes: validate paths, links and source coverage; do not start/mutate the app.

## Historical context
IMPLEMENTATION_STATUS.md, QUICK_IMPLEMENTATION_GUIDE.md and older README files are historical, not verified current status.
The derived מתכונים/שיוך_תפריטים_לפי_קבצי_המקור.md says one menu per dish; current DishMenuMapping supports many. Resolve source/task intent before applying the older mapping.

## 2026-11-18 — remaining workbook implementation
- `FastAPI/app/services/workbook_rules.py`: 23 reviewed editable presets, Fraction food quantities, explicit mass/volume conversion, installment rates and shared clearing fee. Dish router exposes calculation-presets before dynamic IDs; dish editor has typed fields for workbook rules.
- `workbook_tool_import.py` and `scripts/prepare_workbook_tools.py`: reviewed exact dish mapping for separate real/disposable sheets, non-destructive repeatable import, existing-owner configurations preserved, backup before local apply.
- Calculation settings add installments/rate/VAT (migration o8d9e0f1a2b3). Event UI edits them; EventService and summary share fee implementation.
- Menu table_setting_items now accepts quantity_basis place_setting/serving_group; UI persists it. Automatic crackers use menu profile. Unit normalization for workbook/salad_garnish occurs before inventory/price enrichment.
- Task 25 supersedes earlier observations about unlinked catalog and unnormalized workbook products. Unknown units/ambiguous source rows remain unresolved, not invented. Sweet dish package remains postponed.
