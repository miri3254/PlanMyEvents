# API map — inspected 2026-11-15
Actual contracts: FastAPI/app/routers and schemas. Do not copy hypothetical auth/user endpoints from older documentation.

## Transport
- Angular BaseApiService uses environment.apiUrl, currently http://127.0.0.1:8000/api.
- Angular/proxy.conf.json also maps /api to the backend; use depends on environment configuration.
- FastAPI/app/main.py registers routers under /api. /api/health exists.
- Read concrete response schemas: list responses are not uniformly arrays.
- API snake_case is mapped to UI camelCase. Update both directions.

## Events (/api/events)
| Method | Relative path | Purpose |
|---|---|---|
| GET / POST | empty | list/create |
| GET / PUT / DELETE | /{event_id} | detail/update/delete |
| PATCH | /{event_id}/status | lifecycle |
| PATCH | /{event_id}/price | final price |
| POST | /{event_id}/dishes | add dish |
| PUT / DELETE | /{event_id}/dishes/{dish_id} | update/remove; inspect identifier semantics |
| POST | /{event_id}/dishes/bulk | bulk selections |
| POST | /{event_id}/dishes/finalize | finalize |
| POST | /{event_id}/trays | tray selection |
| PATCH | /{event_id}/morning-split | Shabbat split |
| POST | /{event_id}/restore-stock | restore stock |
| GET | /{event_id}/calculations/summary | calculation summary |
| PUT | /{event_id}/calculations/settings | settings |
| PUT | /{event_id}/calculations/dish-serving-selections | serving/packaging sets |
| PUT | /{event_id}/calculations/manual-tools | manual tool rows |
| POST | /{event_id}/calculations/recalculate | recalculate |
| GET | /{event_id}/shopping-list | shopping |
| GET | /{event_id}/equipment-list | equipment |
| GET | /{event_id}/waiter-pdf | waiter PDF |
| GET | /{event_id}/catering-pdf | catering PDF; inspect actual content/purpose |
| GET | /{event_id}/shopping-pdf | shopping PDF |
| GET | /{event_id}/delivery-sheet/pdf | delivery PDF |
| GET | /delivery-note-templates | note templates |

## Other domains
- /api/dishes: CRUD, nested ingredients/equipment, /{dish_id}/serving-sets and /{dish_id}/calculation-rules.
- /api/menus: templates, /sub-meals, /categories, /dish-mappings, /by-type/{menu_type}; inspect verbs.
- Also registered: /api/products, /api/tools, /api/lookup, /api/dashboard, /api/backup, /api/unit-conversions, /api/receipts.
- Receipt inventory UI uses /receipts/products/inventory and /receipts/inventory/bulk-update.
- No auth or login functionality is implied by this map.

## Changing contracts
Model + migration -> Pydantic schema -> service/router -> API TypeScript type -> UI mapping/save -> exports/backup -> focused tests.
Preserve historical snapshots and verify stock/status transitions. Saving a field does not prove it appears in PDFs.
