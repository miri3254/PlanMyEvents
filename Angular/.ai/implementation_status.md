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
| Serving tools | DishServingSet real/disposable × personal/central; auto pick by event dish type; wizard saves selections; central per place_settings/8, sweet = half | 24 |
| Table settings | MenuTemplate.table_setting_items (bases place_setting / serving_group), editable in menu UI | 24, 25 |
| Workbook presets | 23 formulas in workbook_rules.py (sides, sauces, live salads, salads to send), editable in dish UI; g↔kg, ml↔l normalized before stock | 25 |
| Crackers (מציות) | sweet menu: ceil(N/16) packages | 25 |
| Credit fee | installments 1–6 per workbook rates × VAT, alternative rate in settings | 25 |
| Workbook tools import | 40 tools, 48 options, 4 menu table settings; new stock 0; repeatable, no overwrite | 25 |
| Menus | `שולחן מתוק` (id 7) and `תפריט שבת` (id 4) exist locally; split-Shabbat as event option was removed by user | — |
Alembic head: o8d9e0f1a2b3. All migrations applied locally with backups.

## Legacy / partial (don't assume correct)
- Waiter/catering PDFs: use aggregated tool contributions; old events without contribution metadata fall back to legacy `dish.serving_dishes`.
- `_effective_guests_for_tables` = ceil(guests×0.6) in sweet; shape capacities (square 12, round/rect 8) still in old table paths.
- Unconfirmed code rules (not from client): waiters ceil(guests/50)×2; sweet hot-dish name detection/regrouping (`_calculate_sweet_hot_groups`).
- Shopping list: get_shopping_list multiplies ingredient qty × EventDish.quantity × guests; client complained of two shopping lists — purpose unresolved (task 18).
- `_calculate_production_cost` skips is_gift dishes (gifts still cost money) — task 16.
- Food requirements don't net out other events' commitments; ToolReservation is per-day reservation, not real return tracking.

## Known bugs (reproduced in service tests, NOT fixed)
- `restore_stock` (only via POST /events/{id}/restore-stock, not called from UI): double restore adds twice; restores full amount even if deduction was floored at 0; with ingredient replaced by prepared product both were deducted.
- `_deduct_inventory` deducts recipe ingredients AND calc product_requirements — verify double counting before stock work.
Proposal (not approved): `docs/catering-todo/inventory-simplification-review.md`.

## Not started (open tasks)
01–04 menus · 05–08 recipe imports · 09 prepared inventory (do first) · 10 waiter page · 11 packing · 12 installment fees (partly by 25) · 13–14 delivery out/return · 15 desserts · 16 bonuses · 17 branding · 18 document purpose. Sweet dish package: postponed by user.

## Open business decisions (ask; never invent)
- O01 Tablecloths: base/rounding/spare DECIDED (task 21); shape split (rect/square) still open.
- O02 Stock unit for salad/rice/sauce/kugel and relation to a person portion; live-salad units missing in workbook.
- O03 Desserts: 3 vs 4 types, which events, rounding, substitution when out of stock (1.5/person target).
- O04 Central-dish ratio per diners beyond /8; personal tools for mains; two kugel types; "?" rows in tools sheets.
- O05 "One spare" = unit or package; meaning of "per dish"; general item quantities.
- O06 Fees: workbook 2.74%/3.87%×1.18 vs email 2.75%/3.90% incl.; base and whether it replaces the clearing fee.
- O07 Purpose of event summary; which two shopping lists the client saw.
- O08 Which bonuses are automatic, quantities, client display.
- O09 Valid recipe version on conflicts, missing yields, alternatives, "above 60/70" thresholds, menu selection limits.
- O10 Parties' identity, seat/table counts per side.
- O11 Night return location, no-answer handling, digital tracking need.
- Other source conflicts: cigars 125 not in dish summary; snacks 0.05 vs "1 package".
