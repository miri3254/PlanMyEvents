"""Central event calculation engine."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, time, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.core.enums import EventStatus, ToolSubCategory
from app.models.calculation import (
    DishCalculationRule,
    DishServingSet,
    EventCalculationSettings,
    EventCalculationSnapshot,
    EventDishServingSelection,
    EventManualToolRow,
    ToolReservation,
)
from app.models.dish import Dish
from app.models.event import Event, EventDish, EventTraySelection
from app.models.product import Product
from app.core.enums import UnitType
from app.services.drink_rules import DRINK_TYPES, drink_quantity
from app.services.tablecloth_rules import calculate_tablecloths, LEGACY_PROFILES
from app.services.roll_rules import calculate_rolls
from app.services.workbook_rules import PRESETS, calculate_preset, clearing_fee, clearing_rate, convert_quantity
from app.repositories.menu_repo import MenuRepository
from app.models.tool import Tool
from app.schemas.calculation import (
    CalculationCharge,
    CalculationRequirement,
    EventCalculationSettingsUpdate,
    EventCalculationSummary,
)


TABLE_SHAPE_LABELS = {"square": "מרובע", "round": "עגול", "rectangle": "מלבן"}
BASIS_LABELS = {"table": "לפי שולחנות", "event": "לאירוע", "guest": "לפי סועדים", "dish_unit": "לפי יחידות מנה",
                "place_setting": "לפי מקומות ערוכים", "serving_group": "כלי לכל 8 ערוכים"}


class EventCalculationService:
    def __init__(self, db: Session):
        self.db = db

    def get_settings(self, event_id: int, create: bool = True) -> EventCalculationSettings | None:
        settings = (
            self.db.query(EventCalculationSettings)
            .filter(EventCalculationSettings.event_id == event_id)
            .first()
        )
        if not settings and create:
            settings = EventCalculationSettings(
                event_id=event_id,
                drink_types={key: True for key in DRINK_TYPES},
            )
            self.db.add(settings)
            self.db.flush()
        return settings

    def update_settings(self, event_id: int, data: EventCalculationSettingsUpdate) -> EventCalculationSettings:
        settings = self.get_settings(event_id, create=True)
        payload = data.model_dump(exclude_unset=True)
        for key, value in payload.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        self.db.flush()
        return settings

    def replace_manual_tools(self, event_id: int, rows: list[Any]) -> None:
        from app.utils.errors import AppException
        payloads = []
        for row in rows:
            payload = row.model_dump() if hasattr(row, "model_dump") else dict(row)
            if payload.get('tool_id'):
                tool = self.db.get(Tool, payload['tool_id'])
                if not tool or tool.is_deleted:
                    raise AppException(422, 'הכלי אינו קיים במלאי')
                payload['is_reusable'] = self._tool_is_reusable(tool)
                payload['name'] = tool.name
            elif not (payload.get('name') or '').strip():
                raise AppException(422, 'יש לבחור כלי או להזין שם')
            payloads.append(payload)
        self.db.query(EventManualToolRow).filter(EventManualToolRow.event_id == event_id).delete()
        for payload in payloads:
            self.db.add(EventManualToolRow(event_id=event_id, **payload))
        self.db.flush()

    def replace_serving_selections(self, event_id: int, selections: list[Any]) -> None:
        from app.utils.errors import AppException
        for selection in selections:
            payload = selection.model_dump() if hasattr(selection, "model_dump") else dict(selection)
            if payload.get("set_id") and not self.db.query(DishServingSet).filter(
                DishServingSet.id == payload["set_id"], DishServingSet.dish_id == payload["dish_id"],
                DishServingSet.set_type == payload.get("set_type", "serving")
            ).first():
                raise AppException(422, "אפשרות ההגשה אינה שייכת למנה")
        self.db.query(EventDishServingSelection).filter(EventDishServingSelection.event_id == event_id).delete()
        for selection in selections:
            payload = selection.model_dump() if hasattr(selection, "model_dump") else dict(selection)
            self.db.add(EventDishServingSelection(event_id=event_id, **payload))
        self.db.flush()

    def summarize(self, event: Event, use_snapshot: bool = True) -> EventCalculationSummary:
        settings = self.get_settings(event.id, create=True)
        snapshots = self._snapshots(event.id)
        operational_summary = self._operational_summary(event, settings)
        if use_snapshot and self._is_approved_or_later(event) and snapshots:
            return EventCalculationSummary(
                event_id=event.id,
                event_name=event.name,
                settings=settings,
                has_approved_snapshot=True,
                **operational_summary,
                product_requirements=snapshots.get("product_requirements", []),
                tool_requirements=snapshots.get("tool_requirements", []),
                charge_requirements=snapshots.get("charge_requirements", []),
                warnings=snapshots.get("warnings", []),
                formula_trace=snapshots.get("formula_trace", []),
            )

        product_requirements: list[CalculationRequirement] = []
        tool_requirements: list[CalculationRequirement] = []
        charges: list[CalculationCharge] = []
        warnings: list[str] = []
        trace: list[dict[str, Any]] = []

        product_requirements.extend(self._calculate_drinks(event, settings, trace, warnings))
        product_requirements.extend(self._calculate_crackers(event, warnings))
        product_requirements.extend(self._calculate_rolls(event, settings, trace, warnings))
        product_requirements.extend(self._calculate_dish_rules(event, settings, trace, warnings))
        tool_requirements.extend(self._calculate_table_settings(event, warnings))
        tool_requirements.extend(self._calculate_serving_sets(event, settings, trace, warnings))
        tool_requirements.extend(self._calculate_tray_packaging(event, settings, trace, warnings))
        tool_requirements.extend(self._calculate_tablecloths(event, settings, trace, warnings))
        tool_requirements.extend(self._calculate_event_tool_set_tools(event, settings, trace))
        tool_requirements.extend(self._manual_tools(event, trace))
        charges.extend(self._calculate_credit_card_fee(event, settings, trace))

        product_requirements = self._enrich_product_requirements(product_requirements)
        warnings.extend(row.details["unit_warning"] for row in product_requirements if (row.details or {}).get("unit_warning"))
        tool_requirements = self._enrich_tool_requirements(event, tool_requirements)

        return EventCalculationSummary(
            event_id=event.id,
            event_name=event.name,
            settings=settings,
            has_approved_snapshot=False,
            **operational_summary,
            product_requirements=product_requirements,
            tool_requirements=tool_requirements,
            charge_requirements=charges,
            warnings=warnings,
            formula_trace=trace,
        )

    def _operational_summary(self, event: Event, settings: EventCalculationSettings | None) -> dict[str, Any]:
        waiter_count = self.waiter_count(event)
        table_count = self.table_count(event)
        production_cost = self._calculate_production_cost(event)
        revenue = event.final_price if event.final_price is not None else (event.calculated_price or event.total_price or 0)
        estimated_profit = round(revenue - production_cost, 2) if production_cost is not None and revenue else None
        is_sweet = self._menu_calculation_profile(event)[0] == "sweet"
        return {
            "waiter_count": waiter_count,
            "table_count": table_count,
            "production_cost": production_cost,
            "estimated_profit": estimated_profit,
            "revenue": revenue,
            "waiter_formula_label": "ceil(אורחים / 50) * 2 מלצרים",
            "table_formula_label": "ceil(אורחים / 16) — שולחן מתוק, חצי" if is_sweet else "ceil(אורחים / 8)",
        }

    def _calculate_production_cost(self, event: Event) -> float | None:
        total = 0.0
        has_cost = False

        # Dish cost is PER PERSON (user decision Q008) → cost × guests. Gifts are not
        # charged to the client but are still produced, so they count as cost (Q009).
        guests = event.guest_count or 0
        for event_dish in event.dishes:
            dish = event_dish.dish
            base_price = event_dish.snapshot_base_price
            if base_price is None and dish:
                base_price = dish.base_price
            if base_price is None:
                continue
            total += float(base_price) * guests
            has_cost = True

        for tray in event.tray_selections:
            dish = tray.dish
            base_price = dish.base_price if dish else None
            if base_price is None:
                continue
            total += float(base_price) * (tray.tray_count or 1)
            has_cost = True

        return round(total, 2) if has_cost else None

    def snapshot_event(self, event: Event) -> None:
        self.db.query(EventCalculationSnapshot).filter(EventCalculationSnapshot.event_id == event.id).delete()
        self.db.flush()
        summary = self.summarize(event, use_snapshot=False)
        payload = summary.model_dump(mode="json")
        for key in [
            "product_requirements",
            "tool_requirements",
            "charge_requirements",
            "warnings",
            "formula_trace",
        ]:
            self.db.add(
                EventCalculationSnapshot(
                    event_id=event.id,
                    calculation_type=key,
                    payload=payload.get(key, []),
                )
            )
        self._replace_reservations(event, summary.tool_requirements)
        self.db.flush()

    def release_reservations(self, event_id: int) -> None:
        self.db.query(ToolReservation).filter(ToolReservation.event_id == event_id).delete()
        self.db.flush()

    def replaced_product_ids(self, event: Event) -> set[int]:
        dish_ids = [ed.dish_id for ed in event.dishes]
        if not dish_ids:
            return set()
        rows = (
            self.db.query(DishCalculationRule.replaces_ingredient_product_id)
            .filter(DishCalculationRule.dish_id.in_(dish_ids))
            .filter(DishCalculationRule.is_active == True)  # noqa: E712
            .filter(DishCalculationRule.replaces_ingredient_product_id.isnot(None))
            .all()
        )
        return {int(row[0]) for row in rows if row[0]}

    def _snapshots(self, event_id: int) -> dict[str, Any]:
        rows = (
            self.db.query(EventCalculationSnapshot)
            .filter(EventCalculationSnapshot.event_id == event_id)
            .all()
        )
        return {row.calculation_type: row.payload for row in rows}

    def _is_approved_or_later(self, event: Event) -> bool:
        status = event.status.value if hasattr(event.status, "value") else str(event.status)
        return status in {
            EventStatus.APPROVED.value,
            EventStatus.COMPLETED.value,
            EventStatus.CANCELLED.value,
        }

    def _guest_count(self, event: Event, settings: EventCalculationSettings | None = None) -> int:
        return event.guest_count or 1

    # Single source for operational counts (event response, PDFs, calc engine).
    @staticmethod
    def waiter_count(event: Event) -> int:
        # Unconfirmed code rule (not from client): 2 waiters per 50 guests.
        return math.ceil(max(1, event.guest_count or 0) / 50) * 2

    def table_count(self, event: Event) -> int:
        # User decision 2026-11-23, per workbook: ceil(guests / 8); sweet menu = half
        # (ceil(ceil(guests/2) / 8) == ceil(guests / 16)). Table shape does not change it.
        return max(1, math.ceil(self._place_setting_count(event) / 8))

    def _calculate_drinks(self, event, settings, trace, warnings) -> list[CalculationRequirement]:
        if settings and not settings.drinks_enabled:
            return []

        active_map = settings.drink_types if settings and settings.drink_types else {}
        active_keys = [key for key in DRINK_TYPES if active_map.get(key, True)]
        if not active_keys:
            warnings.append("לא נבחר אף סוג שתיה פעיל")
            return []

        guests = max(0, event.guest_count or 0)
        requirements: list[CalculationRequirement] = []
        # Menu profile from MenuTemplate (not name text), same as rolls/tablecloths.
        profile = self._menu_calculation_profile(event)[0]
        products = self.db.query(Product).filter(Product.is_deleted == False).all()  # noqa: E712

        for key in active_keys:
            info = DRINK_TYPES[key]
            raw_qty, formula, source_cell = drink_quantity(profile, key, guests)
            qty = math.ceil(raw_qty) if info["round"] == "up" else math.floor(raw_qty)
            if qty <= 0:
                continue
            matches = [p for p in products if p.drink_type == key]
            # Compatibility for an existing unclassified, unambiguous pooled product.
            if not matches:
                matches = [p for p in products if not p.drink_type and p.name == info["name"]]
            product = matches[0] if len(matches) == 1 and matches[0].unit == UnitType.UNIT else None
            if not product:
                warnings.append(f"יש להגדיר מוצר מלאי יחיד לסוג השתייה {info['name']} ביחידות (בקבוקים); המלאי לא קוזז")
            req = self._product_req("drink", info["name"], qty, "יחידות", formula, float(raw_qty), product.id if product else None)
            req.details = {"drink_type": key, "profile": profile, "source_sheet": "חישוב שתיה", "source_cell": source_cell, "rule_version": "2026-11-17"}
            requirements.append(req)
            trace.append({"type": "drink", "formula": formula, "guests": guests, **req.details})
        return requirements

    def _calculate_rolls(self, event, settings, trace, warnings) -> list[CalculationRequirement]:
        profile, template = self._menu_calculation_profile(event)
        raw, total, cell, formula = calculate_rolls(event.guest_count, profile)
        details = {'profile': profile, 'source_sheet': 'חישוב לחמניות', 'source_cell': cell,
                   'rule_version': 'workbook-2026-11-17', 'menu_template_id': template.id if template else None}

        splits = settings.roll_splits if settings and settings.roll_splits else None
        if not splits:
            trace.append({"type": "rolls", "formula": formula, "total": total, **details})
            req = self._product_req("rolls", "לחמניות", total, "יחידות", formula, float(raw))
            req.details = details
            return [req]

        allocations = self._allocate_by_percent(total, splits)
        trace.append({"type": "rolls", "formula": formula, "total": total, "splits": splits, **details})
        requirements: list[CalculationRequirement] = []
        for row, qty in allocations:
            if qty <= 0:
                continue
            product_id = row.get("product_id")
            product = self.db.query(Product).filter(Product.id == product_id).first() if product_id else None
            name = product.name if product else (row.get("name") or "לחמניות")
            req = self._product_req("rolls", name, qty, "יחידות", formula, total, product_id)
            if not product:
                price = float(row.get("price_per_unit") or 0)
                req.details = {**details, "source": "manual", "price_per_unit": price}
                req.estimated_price = round(price * req.quantity, 2)
            else:
                req.details = {**details, "source": "product"}
            requirements.append(req)
        return requirements

    def _allocate_by_percent(self, total: int, rows: list[dict[str, Any]]) -> list[tuple[dict[str, Any], int]]:
        raw = [(row, total * (float(row.get("percent") or 0) / 100.0)) for row in rows]
        floors = [(row, int(math.floor(value)), value - math.floor(value)) for row, value in raw]
        remaining = total - sum(value for _, value, _ in floors)
        ordered = sorted(enumerate(floors), key=lambda item: item[1][2], reverse=True)
        result = [(row, value) for row, value, _ in floors]
        for idx, _ in ordered[:remaining]:
            row, value = result[idx]
            result[idx] = (row, value + 1)
        return result

    def _menu_calculation_profile(self, event):
        # Reuse the stable internal menu classification for workbook rules.
        # The persisted column keeps its original name for DB compatibility.
        template = MenuRepository(self.db).get_template_by_type(event.menu_type)
        profile = template.tablecloth_profile if template else LEGACY_PROFILES.get(event.menu_type, 'regular')
        # Preserve the meaning of already-saved split Shabbat events only.
        if profile == 'shabbat' and event.is_morning_split:
            profile = 'shabbat_split'
        return profile, template

    def _calculate_tablecloths(self, event, settings, trace, warnings) -> list[CalculationRequirement]:
        if not settings:
            return []
        shape = settings.table_shape or "rectangle"
        shape_label = TABLE_SHAPE_LABELS.get(shape, shape)
        profile, template = self._menu_calculation_profile(event)
        raw, base, spare, cell, expression = calculate_tablecloths(event.guest_count, profile)
        quantity = base + spare
        tool = self.db.query(Tool).filter(Tool.id == settings.tablecloth_tool_id).first() if settings.tablecloth_tool_id else None
        name = f"{tool.name} {shape_label}" if tool else f"מפות {shape_label}"
        formula = f"עיגול למעלה({expression}) = {base}; ספייר: עיגול למעלה({base} / 6) = {spare}; שולחן {shape_label}"
        details = {'profile': profile, 'base_quantity': base, 'spare_quantity': spare,
                   'source_sheet': 'חישוב מפות', 'source_cell': cell, 'reserve_cell': 'A8',
                   'rule_version': 'workbook-2026-11-17', 'menu_template_id': template.id if template else None}
        trace.append({"type": "tablecloths", "shape": shape, "formula": formula, **details})
        split = settings.tablecloth_split or {}
        rect, square = int(split.get("rectangle") or 0), int(split.get("square") or 0)
        if rect or square:
            # Caterer: total = portions/8 (+spare); the user marks how many rectangle vs square.
            if rect + square != quantity:
                warnings.append(f"מפות: סומנו {rect} מלבן + {square} מרובע = {rect + square}, אבל לפי החישוב צריך {quantity}")
            base_name = tool.name if tool else "מפות"
            return [
                CalculationRequirement(
                    source_type="tablecloths", item_type="tool", tool_id=tool.id if tool else None,
                    name=f"{base_name} {TABLE_SHAPE_LABELS.get(key, key)}", quantity=count, raw_quantity=float(count),
                    unit="יחידות", formula_label=f"{formula}; חלוקה שסומנה: {count}", details={**details, "split_shape": key},
                    category="מפות", is_reusable=True,
                )
                for key, count in (("rectangle", rect), ("square", square)) if count
            ]
        return [
            CalculationRequirement(
                source_type="tablecloths",
                item_type="tool",
                tool_id=tool.id if tool else None,
                name=name,
                quantity=quantity,
                raw_quantity=float(raw),
                unit="יחידות",
                formula_label=formula,
                details=details,
                category="מפות",
                is_reusable=True,
            )
        ]

    def _calculate_table_settings(self, event, warnings):
        from app.services.table_setting_rules import default_table_setting_items
        settings = self.get_settings(event.id, create=False)
        if settings and settings.event_tool_set_items:
            warnings.append("באירוע נשמרה עריכת כלים ידנית קודמת; היא מחליפה את עריכת התפריט כדי למנוע כפל כלים")
            return []
        profile, template = self._menu_calculation_profile(event)
        if not template or template.is_tray_menu:
            return []
        items = template.table_setting_items if template.table_setting_items is not None else default_table_setting_items(profile)
        places = self._place_setting_count(event)
        key = "real_tool_id" if event.is_real_dishes else "disposable_tool_id"
        result = []
        for item in items:
            qty = float(item.get("quantity") or 0)
            if qty <= 0:
                continue
            tool = self.db.get(Tool, item.get(key)) if item.get(key) else None
            if tool and tool.is_deleted:
                tool = None
            if not tool:
                warnings.append(f"עריכת שולחן: יש לקשר {item['name']} למלאי בעריכת התפריט")
            groups = item.get("quantity_basis") == "serving_group"
            base = math.ceil(places / 8) if groups else places
            label = "קבוצות של עד 8 מקומות" if groups else "מקומות ערוכים"
            result.append(self._tool_req("table_setting", tool.name if tool else item['name'], base * qty,
                "יחידות", f"{base} {label} × {qty}", tool.id if tool else None, self._tool_is_reusable(tool)))
        return result

    def _calculate_event_tool_set_tools(self, event, settings, trace) -> list[CalculationRequirement]:
        if not settings or not settings.event_tool_set_items:
            return []

        guests = event.guest_count or 1
        result: list[CalculationRequirement] = []
        for row in settings.event_tool_set_items:
            per_guest = float(row.get("quantity_per_guest") or 0)
            tool_id = row.get("tool_id")
            if per_guest <= 0 or not tool_id:
                continue

            tool = self.db.query(Tool).filter(Tool.id == tool_id).first()
            name = tool.name if tool else row.get("name") or "כלי אירוע"
            result.append(self._tool_req(
                "event_tool_set",
                name,
                guests * per_guest,
                "יחידות",
                f"סט כלים לאירוע: {guests} סועדים * {per_guest}",
                tool_id,
                self._tool_is_reusable(tool, row.get("is_reusable")),
            ))

        trace.append({"type": "event_tool_set", "guests": guests, "items": settings.event_tool_set_items})
        return result

    def _calculate_crackers(self, event, warnings):
        if self._menu_calculation_profile(event)[0] != 'sweet':
            return []
        raw = max(0, event.guest_count or 0) / 16
        product = self.db.query(Product).filter(Product.name == 'מציות', Product.is_deleted == False).all()
        linked = product[0] if len(product) == 1 and product[0].unit == UnitType.BUNDLE else None
        if not linked:
            warnings.append('מציות: יש לקשר מוצר יחיד בשם מציות ביחידת חבילה')
        row = self._product_req('workbook_crackers', 'מציות', math.ceil(raw), 'חבילה',
            f'{event.guest_count} / 2 / 8, עיגול למעלה', raw, linked.id if linked else None)
        row.details = {'source_sheet': 'חישוב מציות', 'source_cell': 'C4:C5'}
        return [row]

    def _calculate_credit_card_fee(self, event, settings, trace) -> list[CalculationCharge]:
        if not settings or not settings.credit_card_enabled:
            return []
        base_amount = settings.credit_card_amount
        if base_amount is None:
            if event.final_price is not None:
                base_amount = event.final_price
            else:
                # calculated_price already includes the fee after pricing is recalculated.
                base_amount = (event.calculated_price or 0) / (1 + clearing_rate(settings) / 100 * settings.credit_card_vat_multiplier)
        fee = clearing_fee(base_amount, settings)
        formula = f"סכום אשראי × {clearing_rate(settings):g}% × {settings.credit_card_vat_multiplier:g}; {settings.credit_card_installments} תשלומים"
        trace.append({"type": "credit_card_fee", "base_amount": base_amount, "fee": fee, "formula": formula})
        return [CalculationCharge(source_type="credit_card_fee", name="עמלת סליקה", amount=fee, formula_label=formula)]

    def _calculate_dish_rules(self, event, settings, trace, warnings) -> list[CalculationRequirement]:
        result: list[CalculationRequirement] = []
        for ed in event.dishes:
            dish = self.db.query(Dish).filter(Dish.id == ed.dish_id).first()
            if not dish:
                continue
            rules = (
                self.db.query(DishCalculationRule)
                .filter(DishCalculationRule.dish_id == dish.id)
                .filter(DishCalculationRule.is_active == True)  # noqa: E712
                .all()
            )
            for rule in rules:
                params = rule.params or {}
                guests = self._dish_guest_count(event, ed, settings)
                if rule.rule_type == "workbook":
                    key = params.get("formula_key")
                    if key not in PRESETS:
                        warnings.append(f"{dish.name}: נוסחת אקסל אינה מוכרת")
                        continue
                    qty, raw, unit, formula = calculate_preset(key, max(0, event.guest_count or 0), self._menu_calculation_profile(event)[0], params)
                    if not unit:
                        warnings.append(f"{dish.name} — {rule.name}: חסרה יחידת מידה במקור; יש להגדיר יחידה לפני שימוש במלאי")
                        continue
                    item = self._product_req('workbook', rule.name or PRESETS[key]['name'], qty, unit, formula, raw, rule.product_id)
                    item.details = {'source_sheet': PRESETS[key]['sheet'], 'source_cell': PRESETS[key]['cell'], 'formula_key': key, 'dish_id': dish.id}
                    result.append(item)
                elif rule.rule_type == "salad_garnish":
                    table_count = (event.guest_count or 0) / 8 / (2 if self._menu_calculation_profile(event)[0] == 'sweet' else 1)
                    qty = float(params.get("quantity_per_bowl") or params.get("quantity") or 0) * table_count
                    unit = params.get("unit") or "גרם"
                    formula = f"{params.get('label') or 'תוספת'}: {table_count} קערות * {params.get('quantity_per_bowl') or params.get('quantity')}"
                    result.append(self._product_req("salad_garnish", rule.name or "תוספת לסלט", qty, unit, formula, qty, rule.product_id))
                elif rule.rule_type == "meat":
                    qty, unit, formula = self._calculate_meat_rule(params, guests)
                    result.append(self._product_req("meat", rule.name or "בשר", qty, unit, formula, qty, rule.product_id))
                elif rule.rule_type == "custom_product":
                    basis = params.get("basis") or "guest"
                    factor = float(params.get("factor") or 1)
                    base = guests if basis == "guest" else ed.quantity
                    qty = math.ceil(base * factor) if params.get("round") == "up" else base * factor
                    formula = params.get("formula_label") or f"{basis} * {factor}"
                    result.append(self._product_req("custom_product", rule.name or "חישוב מנה", qty, params.get("unit") or "יחידות", formula, qty, rule.product_id))
        if self._menu_calculation_profile(event)[0] == "sweet":
            result.extend(self._calculate_sweet_hot_groups(event, trace))
        return result

    def _dish_guest_count(self, event: Event, ed: EventDish, settings: EventCalculationSettings | None) -> int:
        return event.guest_count or 1

    def _calculate_meat_rule(self, params: dict[str, Any], guests: int) -> tuple[float, str, str]:
        formula_key = params.get("formula")
        if formula_key == "cholent_beef":
            return guests * 0.05, 'ק"ג', "סועדים * 0.05 ק״ג"
        if formula_key == "main_beef":
            return guests / 6, 'ק"ג', "סועדים / 6 ק״ג"
        if formula_key == "roulade":
            return guests / 8, 'ק"ג', "סועדים / 8 ק״ג"
        if formula_key == "chicken_breast":
            return guests / 6, "חצאי חזות", "סועדים / 6 חצאי חזות"
        factor = float(params.get("kg_per_guest") or params.get("factor") or 1)
        return guests * factor, params.get("unit") or 'ק"ג', f"סועדים * {factor}"


    def _calculate_sweet_hot_groups(self, event: Event, trace) -> list[CalculationRequirement]:
        """Calculate selected sweet-table dishes as weighted groups.

        When a dish is not selected, its share is redistributed among the selected
        dishes in the same group while preserving their original ratios.
        """
        definitions = [
            ("בלינצ", "first", 1.7 / 3, "מנות / 3 * 1.7"),
            ("טורט", "first", 1.5 / 3, "מנות / 3 * 1.5"),
            ("פלפל", "first", 1 / 6, "מנות / 6"),
            ("נודל", "hot", 2 / 6, "מנות / 6 * 2"),
            ("אורז", "hot", 2 / 6, "מנות / 6 * 2"),
            ("קוגל איטר", "hot", 3 / 6, "מנות / 6 * 3"),
            ("קוגל תפו", "hot", 3 / 6, "מנות / 6 * 3"),
            ("פשטיד", "hot", 2.5 / 6, "מנות / 6 * 2.5"),
            ("צולנט", "hot", 2 / 6, "מנות / 6 * 2"),
        ]
        selected: list[tuple[Dish, EventDish, str, float, str]] = []
        result: list[CalculationRequirement] = []
        guests = event.guest_count or 1
        for ed in event.dishes:
            dish = self.db.query(Dish).filter(Dish.id == ed.dish_id).first()
            if not dish:
                continue
            normalized_name = dish.name.replace("׳", "").replace("'", "")
            if "סיגר" in normalized_name:
                # Workbook sheet 5 D13 = portions / 2; not part of the hot-group shares (C13 = 0).
                raw = guests / 2
                result.append(CalculationRequirement(
                    source_type="sweet_hot_hot", item_type="product", name=dish.name,
                    quantity=math.ceil(raw), raw_quantity=raw, unit="יחידות",
                    formula_label="מנות / 2", details={"source_cell": "D13"},
                ))
                continue
            for token, group, weight, formula in definitions:
                if token in normalized_name:
                    selected.append((dish, ed, group, weight, formula))
                    break

        first_total = 0
        for group in ("first", "hot"):
            group_rows = [row for row in selected if row[2] == group]
            if not group_rows:
                continue
            all_weight = sum(weight for _, definition_group, weight, _ in definitions if definition_group == group)
            selected_weight = sum(row[3] for row in group_rows)
            redistribution = all_weight / selected_weight
            for dish, ed, _, weight, formula in group_rows:
                # Guest-based formula; ed.quantity is dish units, not a per-guest multiplier.
                raw = guests * weight * redistribution
                equivalent_quantity = math.ceil(raw)
                quantity = equivalent_quantity
                details = {"equivalent_quantity": equivalent_quantity, "redistribution_factor": redistribution}
                result.append(CalculationRequirement(
                    source_type=f"sweet_hot_{group}", item_type="product", name=dish.name,
                    quantity=quantity, raw_quantity=raw, unit="יחידות",
                    formula_label=formula, details=details,
                ))
                if group == "first":
                    first_total += equivalent_quantity

        if first_total > guests:
            extra = first_total - guests
            result.append(self._product_req(
                "sweet_hot_extra_blintzes", "תוספת בלינצ'ס ממנות חמות", extra,
                "יחידות", "סה״כ ראשונות - מנות", extra,
            ))
        trace.append({"type": "sweet_hot_groups", "guests": guests, "first_total": first_total})
        return result

    def _calculate_serving_sets(self, event, settings, trace, warnings) -> list[CalculationRequirement]:
        result: list[CalculationRequirement] = []
        selections = self._selection_map(event.id, "serving")
        for ed in event.dishes:
            selected_set_id = selections.get(("dish", ed.id)) or selections.get(("dish_id", ed.dish_id))
            serving_set = self._resolve_serving_set(event, ed.dish_id, selected_set_id, ed)
            if not serving_set:
                if ed.serving_mode or self._menu_serving_mode(event, ed) or self.db.query(DishServingSet).filter(DishServingSet.dish_id == ed.dish_id, DishServingSet.set_type == "serving", DishServingSet.serving_mode.isnot(None)).first():
                    dish = self.db.get(Dish, ed.dish_id)
                    warnings.append(f"{dish.name if dish else ed.dish_id}: חסרים כלים לסוג הכלים או לצורת ההגשה שנבחרו")
                    continue
                # Backward compatibility: old serving_dishes behave as one default set.
                dish = self.db.query(Dish).filter(Dish.id == ed.dish_id).first()
                if dish:
                    for sd in dish.serving_dishes:
                        tool = self.db.query(Tool).filter(Tool.id == sd.tool_id).first() if sd.tool_id else None
                        result.append(self._tool_req("serving", sd.name or (tool.name if tool else "כלי הגשה"), sd.quantity * ed.quantity, "יחידות", "כלי הגשה ישן * כמות מנה", sd.tool_id, self._tool_is_reusable(tool)))
                continue
            for item in serving_set.items:
                qty = self._quantity_by_basis(item.quantity, item.quantity_basis, event, ed.quantity, settings)
                tool = item.tool or (self.db.query(Tool).filter(Tool.id == item.tool_id).first() if item.tool_id else None)
                requirement = self._tool_req("serving", (tool.name if tool else item.name) or "כלי הגשה", qty, "יחידות", f"{BASIS_LABELS.get(item.quantity_basis, item.quantity_basis)} × {item.quantity:g}", item.tool_id, self._tool_is_reusable(tool, item.is_reusable if not serving_set.serving_mode else None))
                requirement.details = {"event_dish_id": ed.id, "dish_id": ed.dish_id, "set_id": serving_set.id, "serving_mode": serving_set.serving_mode}
                result.append(requirement)
        return result

    def serving_tools_for_document(self, event):
        summary = self.summarize(event)
        result = defaultdict(list)
        if not (self._is_approved_or_later(event) and self._snapshots(event.id)):
            for ed in event.dishes:
                if ed.serving_mode or self._menu_serving_mode(event, ed) or self.db.query(DishServingSet).filter(DishServingSet.dish_id == ed.dish_id, DishServingSet.set_type == "serving", DishServingSet.serving_mode.isnot(None)).first():
                    result[ed.id] = []
        for row in summary.tool_requirements:
            for part in (row.details or {}).get("contributions", []):
                if part.get("event_dish_id"):
                    result[part["event_dish_id"]].append({"name": row.name, "quantity": part["quantity"]})
        return result

    def _menu_serving_mode(self, event, ed):
        from app.models.menu import DishMenuMapping, MenuCategory, MenuSubMeal
        from sqlalchemy import or_
        if not ed or not ed.category_id:
            return None
        template = MenuRepository(self.db).get_template_by_type(event.menu_type)
        if not template:
            return None
        mapping = self.db.query(DishMenuMapping).join(MenuCategory).outerjoin(
            MenuSubMeal, MenuCategory.sub_meal_id == MenuSubMeal.id).filter(
            DishMenuMapping.dish_id == ed.dish_id, DishMenuMapping.category_id == ed.category_id,
            DishMenuMapping.is_deleted == False, MenuCategory.is_deleted == False,
            or_(MenuCategory.template_id == template.id, MenuSubMeal.template_id == template.id)).first()
        return mapping.default_serving_mode if mapping else None

    def _resolve_serving_set(self, event, dish_id, selected_id=None, event_dish=None):
        sets = self.db.query(DishServingSet).filter(
            DishServingSet.dish_id == dish_id, DishServingSet.set_type == "serving"
        ).order_by(DishServingSet.id).all()
        ed = event_dish or next((d for d in event.dishes if d.dish_id == dish_id), None)
        mode = ed.serving_mode if ed else None
        menu_mode = self._menu_serving_mode(event, ed)
        variants = [row for row in sets if row.serving_mode]
        if not variants:
            if mode or menu_mode:
                return None
            return self._resolve_set(dish_id, "serving", selected_id)
        kind = "real" if event.is_real_dishes else "disposable"
        available = [row for row in variants if row.dishware_type == kind]
        if mode:
            return next((row for row in available if row.serving_mode == mode), None)
        selected = next((row for row in sets if row.id == selected_id), None)
        if selected and selected.serving_mode:
            # Preserve the chosen serving mode when the event's dishware changes.
            return next((row for row in available if row.serving_mode == selected.serving_mode), None)
        if menu_mode:
            return next((row for row in available if row.serving_mode == menu_mode), None)
        return next((row for row in available if row.is_default), None) or (available[0] if len(available) == 1 else None)

    def _place_setting_count(self, event):
        guests = max(0, event.guest_count or 0)
        return math.ceil(guests / 2) if self._menu_calculation_profile(event)[0] == "sweet" else guests

    def _calculate_tray_packaging(self, event, settings, trace, warnings) -> list[CalculationRequirement]:
        result: list[CalculationRequirement] = []
        selections = self._selection_map(event.id, "packaging")
        for tray in event.tray_selections:
            selected_set_id = selections.get(("tray", tray.id)) or selections.get(("dish_id", tray.dish_id))
            packaging_set = self._resolve_set(tray.dish_id, "packaging", selected_set_id)
            if packaging_set:
                for item in packaging_set.items:
                    qty = self._quantity_by_basis(item.quantity, item.quantity_basis, event, tray.tray_count, settings)
                    tool = item.tool or (self.db.query(Tool).filter(Tool.id == item.tool_id).first() if item.tool_id else None)
                    result.append(self._tool_req("tray_packaging", item.name or (tool.name if tool else "אריזת מגש"), qty, "יחידות", f"{item.quantity_basis} * {item.quantity}", item.tool_id, self._tool_is_reusable(tool, item.is_reusable)))
            result.append(self._tool_req("tray_leftovers", "קופסת שאריות 1 ליטר", tray.tray_count, "יחידות", "קופסת שאריות אחת לכל מגש", None, False))
        return result

    def _manual_tools(self, event, trace) -> list[CalculationRequirement]:
        rows = self.db.query(EventManualToolRow).filter(EventManualToolRow.event_id == event.id).all()
        result = []
        for row in rows:
            tool = self.db.query(Tool).filter(Tool.id == row.tool_id).first() if row.tool_id else None
            result.append(self._tool_req("manual_tool", row.name or (tool.name if tool else "כלי ידני"), row.quantity, "יחידות", "שורה ידנית באירוע", row.tool_id, row.is_reusable))
        return result

    def _selection_map(self, event_id: int, set_type: str) -> dict[tuple[str, int], int]:
        rows = (
            self.db.query(EventDishServingSelection)
            .filter(EventDishServingSelection.event_id == event_id)
            .filter(EventDishServingSelection.set_type == set_type)
            .all()
        )
        result = {}
        for row in rows:
            if row.event_dish_id:
                result[("dish", row.event_dish_id)] = row.set_id
            if row.event_tray_selection_id:
                result[("tray", row.event_tray_selection_id)] = row.set_id
            result[("dish_id", row.dish_id)] = row.set_id
        return result

    def _resolve_set(self, dish_id: int, set_type: str, selected_set_id: int | None) -> DishServingSet | None:
        if selected_set_id:
            row = self.db.query(DishServingSet).filter(DishServingSet.id == selected_set_id, DishServingSet.dish_id == dish_id, DishServingSet.set_type == set_type).first()
            if row:
                return row
        return (
            self.db.query(DishServingSet)
            .filter(DishServingSet.dish_id == dish_id)
            .filter(DishServingSet.set_type == set_type)
            .filter(DishServingSet.is_default == True)  # noqa: E712
            .first()
        )

    def _quantity_by_basis(self, quantity: float, basis: str, event: Event, unit_count: int, settings) -> float:
        if basis == "place_setting":
            return quantity * self._place_setting_count(event)
        if basis == "serving_group":
            return quantity * math.ceil(self._place_setting_count(event) / 8)
        if basis == "event":
            return quantity
        if basis == "table":
            return quantity * self.table_count(event)
        if basis == "guest":
            return quantity * (event.guest_count or 1)
        return quantity * unit_count

    def _product_req(self, source, name, qty, unit, formula, raw, product_id=None) -> CalculationRequirement:
        return CalculationRequirement(
            source_type=source,
            item_type="product",
            product_id=product_id,
            name=name,
            quantity=round(float(qty), 4),
            raw_quantity=round(float(raw), 4),
            unit=unit,
            formula_label=formula,
        )

    def _tool_req(self, source, name, qty, unit, formula, tool_id=None, is_reusable=False) -> CalculationRequirement:
        return CalculationRequirement(
            source_type=source,
            item_type="tool",
            tool_id=tool_id,
            name=name,
            quantity=math.ceil(float(qty)),
            raw_quantity=round(float(qty), 4),
            unit=unit,
            formula_label=formula,
            is_reusable=is_reusable,
        )

    def _tool_is_reusable(self, tool: Tool | None, override: bool | None = None) -> bool:
        if override is not None:
            return bool(override)
        if not tool:
            return False
        return tool.sub_category == ToolSubCategory.REAL

    def _enrich_product_requirements(self, rows: list[CalculationRequirement]) -> list[CalculationRequirement]:
        grouped: dict[tuple[Any, str, str], CalculationRequirement] = {}
        all_products = self.db.query(Product).all()
        product_by_name = {p.name: p for p in all_products}
        product_by_id = {p.id: p for p in all_products}
        for row in rows:
            product = product_by_id.get(row.product_id) if row.product_id else (None if row.source_type == "drink" or row.source_type.startswith("workbook") else product_by_name.get(row.name))
            if product and row.source_type in ("workbook", "salad_garnish"):
                target_unit = product.unit.value if hasattr(product.unit, 'value') else str(product.unit)
                converted = convert_quantity(row.quantity, row.unit, target_unit)
                if converted is None:
                    row.details = {**(row.details or {}), 'unit_warning': f'לא ניתן להמיר {row.unit} ל־{target_unit}; לא קוזז מלאי'}
                    row.product_id = None
                    product = None
                else:
                    row.details = {**(row.details or {}), 'source_quantity': row.quantity, 'source_unit': row.unit}
                    row.quantity = round(converted, 6)
                    row.raw_quantity = convert_quantity(row.raw_quantity or 0, row.unit, target_unit)
                    row.unit = target_unit
            if product:
                row.product_id = product.id
                row.name = product.name
                row.category = product.category.value if hasattr(product.category, "value") else str(product.category)
                row.package_quantity = product.package_quantity
                row.available_in_stock = product.quantity_in_stock or 0
                row.need_to_buy_quantity = max(0, row.quantity - row.available_in_stock)
                row.packages_to_buy = math.ceil(row.need_to_buy_quantity / product.package_quantity) if product.package_quantity and row.need_to_buy_quantity > 0 else math.ceil(row.need_to_buy_quantity)
                row.estimated_price = round((product.price_per_unit or 0) * row.need_to_buy_quantity, 2)
            else:
                row.available_in_stock = 0
                row.need_to_buy_quantity = row.quantity
                row.packages_to_buy = math.ceil(row.quantity)
                manual_price = (row.details or {}).get("price_per_unit")
                if manual_price is not None:
                    row.estimated_price = round(float(manual_price or 0) * row.need_to_buy_quantity, 2)
            key = (row.product_id, row.name, row.unit)
            if key not in grouped:
                grouped[key] = row
            else:
                existing = grouped[key]
                existing.quantity = round(existing.quantity + row.quantity, 4)
                existing.raw_quantity = round((existing.raw_quantity or 0) + (row.raw_quantity or 0), 4)
                existing.need_to_buy_quantity = max(0, existing.quantity - existing.available_in_stock)
                if existing.package_quantity and existing.need_to_buy_quantity > 0:
                    existing.packages_to_buy = math.ceil(existing.need_to_buy_quantity / existing.package_quantity)
                else:
                    existing.packages_to_buy = math.ceil(existing.need_to_buy_quantity)
                if product:
                    existing.estimated_price = round((product.price_per_unit or 0) * existing.need_to_buy_quantity, 2)
        return list(grouped.values())

    def _enrich_tool_requirements(self, event: Event, rows: list[CalculationRequirement]) -> list[CalculationRequirement]:
        grouped: dict[tuple[Any, str], CalculationRequirement] = {}
        all_tools = self.db.query(Tool).all()
        tool_by_name = {t.name: t for t in all_tools}
        tool_by_id = {t.id: t for t in all_tools}
        reserved = self._reserved_by_tool(event)
        for row in rows:
            row.details = {**(row.details or {}), "contributions": [{"source_type": row.source_type, "quantity": row.quantity, "formula_label": row.formula_label, **(row.details or {})}]}
            tool = tool_by_id.get(row.tool_id) if row.tool_id else (None if row.source_type in ("table_setting", "serving") else tool_by_name.get(row.name))
            if tool:
                row.tool_id = tool.id
                if row.source_type != "tablecloths":
                    row.name = tool.name
                row.category = tool.category.value if hasattr(tool.category, "value") else str(tool.category)
                row.is_reusable = bool(row.is_reusable or self._tool_is_reusable(tool))
                row.available_in_stock = tool.quantity_in_stock or 0
                row.reserved_quantity = reserved.get(tool.id, 0)
                row.available_after_reservations = max(0, row.available_in_stock - row.reserved_quantity) if row.is_reusable else row.available_in_stock
                row.shortage = max(0, row.quantity - row.available_after_reservations)
                row.need_to_buy_quantity = row.shortage
            key = (row.tool_id, row.name)
            if key not in grouped:
                grouped[key] = row
            else:
                existing = grouped[key]
                existing.quantity += row.quantity
                existing.details["contributions"].extend(row.details["contributions"])
                existing.raw_quantity = (existing.raw_quantity or 0) + (row.raw_quantity or 0)
                existing.shortage = max(0, existing.quantity - existing.available_after_reservations)
                existing.need_to_buy_quantity = existing.shortage
        return list(grouped.values())

    def _reserved_by_tool(self, event: Event) -> dict[int, int]:
        if not event.date:
            return {}
        day_start = datetime.combine(event.date.date(), time.min)
        day_end = day_start + timedelta(days=1)
        rows = (
            self.db.query(ToolReservation)
            .filter(ToolReservation.status == "active")
            .filter(ToolReservation.reserved_for_date >= day_start)
            .filter(ToolReservation.reserved_for_date < day_end)
            .filter(ToolReservation.event_id != event.id)
            .all()
        )
        result: dict[int, int] = defaultdict(int)
        for row in rows:
            result[row.tool_id] += row.quantity
        return result

    def _replace_reservations(self, event: Event, tool_requirements: list[CalculationRequirement]) -> None:
        self.release_reservations(event.id)
        for req in tool_requirements:
            if req.is_reusable and req.tool_id and req.quantity > 0 and event.date:
                self.db.add(
                    ToolReservation(
                        event_id=event.id,
                        tool_id=req.tool_id,
                        quantity=math.ceil(req.quantity),
                        reserved_for_date=event.date,
                        status="active",
                    )
                )

