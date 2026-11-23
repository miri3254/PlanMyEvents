# Implementation status — current state (condensed 2026-11-23)
Current state only. Full dated log and evidence: `implementation_status_history.md` (grep there, don't read whole). Per-task detail: `docs/catering-todo/tasks/NN-*.md`.
Edit rule: REPLACE the relevant line when status changes (date it); don't append narratives. Code presence ≠ verified behavior.
Note: local DB data is dummy data; the user allows overwriting it when needed (still back it up first).

## Implemented (with tests)
| Area | State | Task |
|---|---|---|
| Drinks | drink_rules.py (workbook C6:G9); 5 pooled products by `drink_type` in category `שתיה`; morning split via is_morning_split; legacy orange_flavored_mode ignored | 20 |
| Rolls | roll_rules.py C3:C6, Fraction, final ceil, no spare; by menu profile; shown in event overview | 22 |
| Tablecloths | tablecloth_rules.py; profile auto-assigned per menu, not user-editable, not event category; ceil + ceil(base/6) spare | 21 |
| Serving tools | 2026-11-23: per-menu mapping default + nullable event dish override, personal/central; wizard also adds catalogue dishes and manual tools outside menu; approved snapshots preserved | 24, 25 |
| Table settings | MenuTemplate.table_setting_items (bases place_setting / serving_group), editable in menu UI | 24, 25 |
| Workbook presets | 23 formulas in workbook_rules.py (sides, sauces, live salads, salads to send), editable in dish UI; g↔kg, ml↔l normalized before stock | 25 |
| Crackers (מציות) | sweet menu: ceil(N/16) packages | 25 |
| Credit fee | installments 1–6 per workbook rates × VAT, alternative rate in settings | 25 |
| Workbook tools import | 40 tools, 48 options, 4 menu table settings; new stock 0; repeatable, no overwrite | 25 |
| Menus | `שולחן מתוק` (id 7) and `תפריט שבת` (id 4) exist locally; split-Shabbat as event option was removed by user | — |
Alembic head: p9e0f1a2b3c4. All migrations applied locally with backups.

## Legacy / partial (don't assume correct)
- Waiter/catering PDFs: use aggregated tool contributions; old events without contribution metadata fall back to legacy `dish.serving_dishes`.
- Tables (user decision 2026-11-23): single `EventCalculationService.table_count` = ceil(guests/8), sweet ceil(guests/16); used by event response, waiter/catering PDFs, calc 'table' basis. 60% rule and shape capacities removed.
- Menu profile (regular/sweet/shabbat) always from MenuTemplate.tablecloth_profile (LEGACY_PROFILES fallback), incl. drinks; no name text matching.
- Unconfirmed code rules (not from client): waiters ceil(guests/50)×2 (single `waiter_count`); sweet hot-dish name detection/regrouping (`_calculate_sweet_hot_groups`).
- Units (user decision 2026-11-23): recipe + Dish.base_price = ONE dish unit serving Dish.serving_size guests; EventDish.quantity = units (wizard ceil(guests/serving_size)); shopping/deduct/restore = ingredient × units (no ×guests); production cost = base_price × units incl. gifts; guest change rescales units still at the auto value. Dashboard revenue = final_price else calculated.
- Shopping list: client complained of two shopping lists — purpose unresolved (task 18).
- `_calculate_production_cost` skips is_gift dishes (gifts still cost money) — task 16.
- Food requirements don't net out other events' commitments; ToolReservation is per-day reservation, not real return tracking.

## Known bugs (reproduced in service tests, NOT fixed)
- `restore_stock` (only via POST /events/{id}/restore-stock, not called from UI): double restore adds twice; restores full amount even if deduction was floored at 0; with ingredient replaced by prepared product both were deducted.
- `_deduct_inventory` deducts recipe ingredients AND calc product_requirements — verify double counting before stock work. Replaced ingredients (`replaced_product_ids`) are skipped since 2026-11-23.
- Min guests (2026-11-23): MenuTemplate.min_guests wins; constants.MIN_GUESTS only when no template.

## Lifecycle rules (2026-11-23, test_event_lifecycle_rules.py)
- Approve → all EventDish.is_draft=False (UI never calls /dishes/finalize). מאושר→טיוטה → delete calc snapshot, clear dish snapshot prices, release reservations, dishes back to draft.
- Approved/completed events: `_ensure_editable` blocks real changes to guest_count/is_real_dishes/is_morning_split/menu_type and all dish/tray mutations (400, "return to draft"). final_price, notes, delivery fields, calc settings still editable.
- Menu change (draft) re-resolves base_price_per_guest + real_dishes_extra from MenuTemplate and reprices.
Proposal (not approved): `docs/catering-todo/inventory-simplification-review.md`.

## Not started (open tasks)
01–04 menus · 05–08 recipe imports · 09 prepared inventory (do first) · 10 waiter page · 11 packing · 12 installment fees (partly by 25) · 13–14 delivery out/return · 15 desserts · 16 bonuses · 17 branding · 18 document purpose. Sweet dish package: postponed by user.

## Open business decisions (ask; never invent)
- O01 Tablecloths: base/rounding/spare DECIDED (task 21); shape split (rect/square) still open.
- O02 Stock unit for salad/rice/sauce/kugel and relation to a person portion; live-salad default units decided 2026-11-23: vegetables kg, leafy greens/mushrooms packages; configurable. Carrots/potatoes packages when configured.
- O03 Desserts: 3 vs 4 types, which events, rounding, substitution when out of stock (1.5/person target).
- O04 2026-11-23: serving mode per menu/event, dedicated linked vessels; double transparent bowl = one named tool; optional sweet potato/salad is manual gift. Two kugel types remain unresolved. Salt shakers/booklets excluded from automatic calculation.
- O05 "One spare" = unit or package; meaning of "per dish"; general item quantities.
- O06 Fees: workbook 2.74%/3.87%×1.18 vs email 2.75%/3.90% incl.; base and whether it replaces the clearing fee.
- O07 Purpose of event summary; which two shopping lists the client saw.
- O08 Which bonuses are automatic, quantities, client display.
- O09 Valid recipe version on conflicts, missing yields, alternatives, "above 60/70" thresholds, menu selection limits.
- O10 Parties' identity, seat/table counts per side.
- O11 Night return location, no-answer handling, digital tracking need.
- O12 Dashboard labor cost = 15% of revenue (code invention, kept) — ask client: real rule or remove.
- O13 Upgrade dish added in wizard with quantity 1 unit (not ceil(guests/serving_size)) — confirm.
- Other source conflicts: cigars 125 not in dish summary; snacks 0.05 vs "1 package".
