# Domain model & business flow (verified against code 2026-11-23)
Client requirements (targets): `Angular/.ai/catering_requirements.md` (R-numbers). Open decisions O01–O11: `Angular/.ai/implementation_status.md` (grep "O0"). This file = how the system works NOW.

## Glossary (Hebrew UI ↔ code)
| Hebrew | Code | Notes |
|---|---|---|
| מוצר / חומר גלם | Product | stock `quantity_in_stock` in `unit` (UnitType: g/kg/ml/l/tsp/unit…); `package_quantity`; category ProductCategory (`שתיה` = drinks, `נוזלים` = non-drink liquids) |
| מנה | Dish | `base_price` (internal cost), `client_price`, `serving_size` |
| מתכון / רכיב | DishIngredient | product + quantity + unit per serving; `is_serving_component` |
| כלי / ציוד | Tool | category/sub_category; reusable stock reserved per day |
| סט הגשה (אמיתי / חד"פ) | DishServingSet (+Item) | `serving_mode` personal/central; alternatives chosen by event `is_real_dishes`; Item `quantity_basis` dish_unit/event/table/guest/place_setting/serving_group |
| בחירת סט לאירוע | EventDishServingSelection | saved by wizard |
| כלל חישוב למנה | DishCalculationRule | presets from workbook_rules.py (23 formulas) |
| תפריט | MenuTemplate | name = menu type (free text, e.g. בשרי, שבת, שולחן מתוק); `min_guests`; internal `tablecloth_profile` (auto, not user-editable); `table_setting_items` (עריכה) |
| סעודה | MenuSubMeal | Shabbat meals etc. |
| קטגוריה בתפריט | MenuCategory | `quota` = how many dishes can be chosen (NULL = unlimited); tray fields |
| שיוך מנה לתפריט | DishMenuMapping | one dish ↔ many menus |
| אירוע | Event | menu, guest_count, details, delivery/hall fields, `is_morning_split` (Shabbat split), status |
| מנה באירוע | EventDish | `quantity` multiplier, `is_gift` (bonus — not charged but still costs), snapshot prices |
| מגשים / קרטונים / תעודות משלוח | EventTraySelection / EventBox / EventDeliveryNote | |
| הגדרות חישוב | EventCalculationSettings | installments, rate, VAT, drink choices… |
| שורת כלים ידנית | EventManualToolRow | |
| שריון כלים | ToolReservation | per event/day; released on cancel/complete |
| צילום מצב | EventCalculationSnapshot + EventDish snapshot_*_price | frozen at approval — never mutate |

## Event lifecycle (event_service.change_status; transitions in core/constants.py)
טיוטה → מאושר | בוטל · מאושר → הסתיים | בוטל | טיוטה · בוטל → טיוטה · הסתיים → (none)
- → מאושר: `_snapshot_prices` + `calculations.snapshot_event` (freezes summary, creates ToolReservations).
- מאושר → הסתיים: `_deduct_inventory` (recipe ingredients × EventDish.quantity × guest_count, unit-converted, PLUS calc product_requirements; floor at 0) + release reservations.
- Auto-complete: `complete_past_approved_events` runs inside get_events/get_event/get_events_in_range for approved events dated before today.
- → בוטל: releases reservations only (no food returned). `restore_stock` exists only as POST /events/{id}/restore-stock; known bugs (double restore, over-restore) — see implementation_status "תוספת בדיקת מלאי".

## User flow (UI)
1. Events screen (`/events`): create event, pick menu, fill details (guests, date, hall, delivery).
2. Wizard (`/events/:id/select-dishes`): choose dishes per category within quota; serving set selection.
3. Event overview shows auto calculations: drinks, rolls, tablecloths, table settings, tools, credit fee.
4. Documents: waiter PDF, catering PDF, shopping list (JSON + PDF), delivery sheet PDF, equipment list, Excel.
5. Approve → snapshot; on event day/after → completed → stock deducted.

## Calculation engine (EventCalculationService.summarize)
Base N = guest count (or ordered portions per rule). Menu profile (`_menu_calculation_profile` from MenuTemplate, NOT event category) picks regular/sweet/shabbat variants.
- Drinks: drink_rules.py (workbook C6:G9). 5 types (פפסי, פפסי מקס, מיץ, מים, סודה); one pooled Product per `drink_type`.
- Rolls: roll_rules.py (C3:C6), Fraction, final ceil, no spare.
- Tablecloths: tablecloth_rules.py, ceil(base) + ceil(base/6) spare.
- Table settings (עריכה): table_setting_rules.py from MenuTemplate.table_setting_items; sweet = half.
- Serving tools: DishServingSet resolution; central tools per place_settings/8.
- Workbook presets (sides, sauces, live salads, salads to send): workbook_rules.py; mass/volume normalized before stock.
- Crackers (מציות) in sweet: ceil(N/16) packages.
- Credit fee: installments 1–6 per workbook rates × VAT (settings-editable).
- Legacy still present: `_effective_guests_for_tables` 60% in sweet, `_calculate_sweet_hot_groups`, legacy `serving_dishes` in waiter/catering PDF fallback.
All formulas: Python `Fraction`, round only at the end, as the source workbook does.

## Sources of truth for business values
1. User's explicit decision in chat (record it in the task file). 2. Original workbook `© חישובים קיטרינג גינסברגר © (3).xlsx` (review: docs/catering-todo/excel-review-2026-11-17/report.md). 3. Word menus/recipes (docs/catering-todo/sources.md). Code defaults and old docs are NOT sources. Conflicts → ask, don't pick.
