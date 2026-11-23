"""
Dashboard service — comprehensive profitability analytics and business intelligence.
"""

from datetime import datetime, timedelta, date, timezone
from dateutil.relativedelta import relativedelta
from typing import List, Optional, Tuple
from collections import defaultdict

from sqlalchemy import func, and_, extract
from sqlalchemy.orm import Session, joinedload

from app.models.event import Event, EventDish, EventTraySelection
from app.models.dish import Dish, DishIngredient
from app.models.product import Product
from app.models.tool import Tool
from app.core.enums import EventStatus
from app.core.constants import INVENTORY_OUT_OF_STOCK, INVENTORY_LOW_STOCK

# Hebrew month names
HEBREW_MONTHS = [
    "", "ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני",
    "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"
]

# Category colors for charts
CATEGORY_COLORS = [
    "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF",
    "#FF9F40", "#E7E9ED", "#7CFC00", "#DC143C", "#00CED1",
    "#FF69B4", "#8B4513"
]


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def _sync_event_statuses(self) -> None:
        from app.services.event_service import EventService

        EventService(self.db).complete_past_approved_events()

    def _active(self, model):
        return self.db.query(model).filter(model.is_deleted == False)  # noqa: E712

    # ─── Basic Stats ─────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        self._sync_event_statuses()

        total_events = self._active(Event).count()
        total_dishes = self._active(Dish).count()
        total_products = self._active(Product).count()
        total_tools = self._active(Tool).count()

        cancelled = (
            self._active(Event)
            .filter(Event.status == EventStatus.CANCELLED)
            .count()
        )
        approved = (
            self._active(Event)
            .filter(Event.status == EventStatus.APPROVED)
            .count()
        )
        draft = (
            self._active(Event)
            .filter(Event.status == EventStatus.DRAFT)
            .count()
        )
        completed = (
            self._active(Event)
            .filter(Event.status == EventStatus.COMPLETED)
            .count()
        )

        return {
            "total_events": total_events,
            "total_dishes": total_dishes,
            "total_products": total_products,
            "total_tools": total_tools,
            "events_by_status": {
                "draft": draft,
                "cancelled": cancelled,
                "approved": approved,
                "completed": completed,
            },
        }

    def get_upcoming_events(self, days: int = 30) -> list[dict]:
        self._sync_event_statuses()

        today = datetime.now(timezone.utc).date()
        end = today + timedelta(days=days)

        events = (
            self._active(Event)
            .filter(Event.date >= today, Event.date <= end)
            .order_by(Event.date)
            .all()
        )
        return [
            {
                "id": e.id,
                "name": e.name,
                "date": e.date.isoformat() if e.date else None,
                "event_time": e.event_time,
                "hebrew_date": e.hebrew_date,
                "guest_count": e.guest_count,
                "menu_type": e.menu_type.value if hasattr(e.menu_type, "value") else str(e.menu_type),
                "status": e.status.value if hasattr(e.status, "value") else str(e.status),
                "city": e.city,
            }
            for e in events
        ]

    def get_low_stock_alerts(self) -> dict:
        products = (
            self._active(Product)
            .filter(Product.quantity_in_stock <= Product.min_stock_level)
            .all()
        )
        tools = (
            self._active(Tool)
            .filter(Tool.quantity_in_stock <= Tool.min_stock_level)
            .all()
        )
        return {
            "products": [
                {
                    "id": p.id, "name": p.name,
                    "quantity_in_stock": p.quantity_in_stock,
                    "min_stock_level": p.min_stock_level,
                    "category": p.category.value if hasattr(p.category, "value") else str(p.category),
                }
                for p in products
            ],
            "tools": [
                {
                    "id": t.id, "name": t.name,
                    "quantity_in_stock": t.quantity_in_stock,
                    "min_stock_level": t.min_stock_level,
                    "category": t.category.value if hasattr(t.category, "value") else str(t.category),
                }
                for t in tools
            ],
        }

    # ─── Profitability Calculations ──────────────────────────────────────

    def _calculate_event_food_cost(self, event: Event) -> float:
        """Calculate total food cost for an event based on dishes and ingredients."""
        total_cost = 0.0
        
        # Process regular dishes
        for event_dish in event.dishes:
            dish = event_dish.dish
            if not dish:
                continue
            
            quantity = event_dish.quantity or 1
            
            # Use dish base_price as cost if available
            if dish.base_price:
                total_cost += dish.base_price * quantity
            else:
                # Calculate from ingredients
                for ingredient in dish.ingredients:
                    if ingredient.product and ingredient.product.price_per_unit:
                        ing_cost = (ingredient.quantity or 0) * ingredient.product.price_per_unit
                        total_cost += ing_cost * quantity
        
        # Process tray selections
        for tray in event.tray_selections:
            dish = tray.dish
            if not dish:
                continue
            
            tray_count = tray.tray_count or 1
            
            if dish.base_price:
                total_cost += dish.base_price * tray_count
        
        return total_cost

    def _calculate_event_profitability(self, event: Event) -> dict:
        """Calculate full profitability metrics for a single event."""
        revenue = event.total_price or 0.0
        food_cost = self._calculate_event_food_cost(event)
        
        # Estimate labor cost (could be configurable - using 15% of revenue as estimate)
        labor_cost = revenue * 0.15 if revenue > 0 else 0
        
        # Equipment cost (minimal estimate)
        equipment_cost = 0.0
        
        total_cost = food_cost + labor_cost + equipment_cost
        gross_profit = revenue - total_cost
        profit_margin = (gross_profit / revenue * 100) if revenue > 0 else 0
        profit_per_guest = gross_profit / event.guest_count if event.guest_count > 0 else 0

        return {
            "event_id": event.id,
            "event_name": event.name,
            "event_date": event.date.isoformat() if event.date else None,
            "guest_count": event.guest_count or 0,
            "menu_type": event.menu_type.value if hasattr(event.menu_type, "value") else str(event.menu_type),
            "status": event.status.value if hasattr(event.status, "value") else str(event.status),
            "revenue": round(revenue, 2),
            "food_cost": round(food_cost, 2),
            "labor_cost": round(labor_cost, 2),
            "equipment_cost": round(equipment_cost, 2),
            "total_cost": round(total_cost, 2),
            "gross_profit": round(gross_profit, 2),
            "profit_margin_percent": round(profit_margin, 1),
            "profit_per_guest": round(profit_per_guest, 2),
        }

    def _get_period_events(self, start_date: date, end_date: date) -> List[Event]:
        """Get all completed/approved events in a date range."""
        return (
            self._active(Event)
            .filter(
                Event.date >= start_date,
                Event.date <= end_date,
                Event.status.in_([EventStatus.APPROVED, EventStatus.COMPLETED])
            )
            .options(
                joinedload(Event.dishes).joinedload(EventDish.dish).joinedload(Dish.ingredients),
                joinedload(Event.tray_selections).joinedload(EventTraySelection.dish)
            )
            .all()
        )

    # ─── Main Profitability Dashboard ────────────────────────────────────

    def get_profitability_dashboard(self, months: int = 1) -> dict:
        """Get comprehensive profitability dashboard for the last N months."""
        self._sync_event_statuses()

        today = date.today()
        period_end = today
        period_start = today - relativedelta(months=months)
        
        # Previous period for comparison
        prev_period_end = period_start - timedelta(days=1)
        prev_period_start = prev_period_end - relativedelta(months=months)
        
        # Get events for both periods
        current_events = self._get_period_events(period_start, period_end)
        prev_events = self._get_period_events(prev_period_start, prev_period_end)
        
        # Calculate profitability for current period
        events_profitability = [self._calculate_event_profitability(e) for e in current_events]
        
        # Aggregate metrics
        total_revenue = sum(ep["revenue"] for ep in events_profitability)
        total_cost = sum(ep["total_cost"] for ep in events_profitability)
        total_profit = sum(ep["gross_profit"] for ep in events_profitability)
        total_guests = sum(ep["guest_count"] for ep in events_profitability)
        completed_count = len([ep for ep in events_profitability if ep["status"] == EventStatus.COMPLETED.value])
        
        # Previous period metrics
        prev_profitability = [self._calculate_event_profitability(e) for e in prev_events]
        prev_revenue = sum(ep["revenue"] for ep in prev_profitability)
        prev_profit = sum(ep["gross_profit"] for ep in prev_profitability)
        prev_events_count = len(prev_events)
        
        # Calculate comparisons (% change)
        def calc_change(current: float, previous: float) -> float:
            if previous == 0:
                return 100.0 if current > 0 else 0.0
            return round(((current - previous) / previous) * 100, 1)
        
        revenue_change = calc_change(total_revenue, prev_revenue)
        profit_change = calc_change(total_profit, prev_profit)
        events_change = calc_change(len(current_events), prev_events_count)
        
        # Find top performers
        most_profitable = max(events_profitability, key=lambda x: x["gross_profit"]) if events_profitability else None
        highest_margin = max(events_profitability, key=lambda x: x["profit_margin_percent"]) if events_profitability else None
        
        # Expense breakdown by category
        expense_breakdown = self._get_expense_breakdown(current_events)
        
        # Monthly trends
        monthly_trends = self._get_monthly_trends(6)
        
        # Period label
        if months == 1:
            period_label = "החודש האחרון"
        elif months == 3:
            period_label = "3 החודשים האחרונים"
        elif months == 6:
            period_label = "חצי שנה אחרונה"
        elif months == 12:
            period_label = "שנה אחרונה"
        else:
            period_label = f"{months} החודשים האחרונים"

        return {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "period_label": period_label,
            
            # Overview KPIs
            "total_revenue": round(total_revenue, 2),
            "total_cost": round(total_cost, 2),
            "total_profit": round(total_profit, 2),
            "profit_margin_percent": round((total_profit / total_revenue * 100) if total_revenue > 0 else 0, 1),
            
            # Comparisons
            "revenue_vs_last_period": revenue_change,
            "profit_vs_last_period": profit_change,
            "events_vs_last_period": events_change,
            
            # Event stats
            "total_events": len(current_events),
            "completed_events": completed_count,
            "total_guests": total_guests,
            "avg_revenue_per_event": round(total_revenue / len(current_events), 2) if current_events else 0,
            "avg_profit_per_event": round(total_profit / len(current_events), 2) if current_events else 0,
            "avg_profit_per_guest": round(total_profit / total_guests, 2) if total_guests > 0 else 0,
            
            # Top performers
            "most_profitable_event": most_profitable,
            "highest_margin_event": highest_margin,
            
            # Detailed data
            "expense_by_category": expense_breakdown,
            "monthly_trends": monthly_trends,
            "events_profitability": sorted(events_profitability, key=lambda x: x["event_date"] or "", reverse=True),
        }

    def _get_expense_breakdown(self, events: List[Event]) -> List[dict]:
        """Get expense breakdown by product category."""
        category_expenses = defaultdict(lambda: {"amount": 0.0, "item_count": 0})
        
        for event in events:
            for event_dish in event.dishes:
                dish = event_dish.dish
                if not dish:
                    continue
                
                quantity = event_dish.quantity or 1
                
                for ingredient in dish.ingredients:
                    if ingredient.product:
                        cat_name = ingredient.product.category.value if hasattr(ingredient.product.category, "value") else str(ingredient.product.category)
                        cost = (ingredient.quantity or 0) * (ingredient.product.price_per_unit or 0) * quantity
                        category_expenses[cat_name]["amount"] += cost
                        category_expenses[cat_name]["item_count"] += 1
        
        total = sum(c["amount"] for c in category_expenses.values())
        
        result = []
        for i, (category, data) in enumerate(sorted(category_expenses.items(), key=lambda x: x[1]["amount"], reverse=True)):
            result.append({
                "category": category,
                "amount": round(data["amount"], 2),
                "percentage": round((data["amount"] / total * 100) if total > 0 else 0, 1),
                "item_count": data["item_count"],
                "color": CATEGORY_COLORS[i % len(CATEGORY_COLORS)]
            })
        
        return result

    def _get_monthly_trends(self, months: int = 6) -> List[dict]:
        """Get monthly profit trends for the last N months."""
        today = date.today()
        trends = []
        
        for i in range(months - 1, -1, -1):
            # Calculate month boundaries
            month_date = today - relativedelta(months=i)
            month_start = date(month_date.year, month_date.month, 1)
            if i == 0:
                month_end = today
            else:
                next_month = month_start + relativedelta(months=1)
                month_end = next_month - timedelta(days=1)
            
            # Get events for this month
            events = self._get_period_events(month_start, month_end)
            profitability = [self._calculate_event_profitability(e) for e in events]
            
            # Aggregate
            total_revenue = sum(ep["revenue"] for ep in profitability)
            total_cost = sum(ep["total_cost"] for ep in profitability)
            total_profit = sum(ep["gross_profit"] for ep in profitability)
            total_guests = sum(ep["guest_count"] for ep in profitability)
            
            trends.append({
                "year": month_start.year,
                "month": month_start.month,
                "month_name": f"{HEBREW_MONTHS[month_start.month]} {month_start.year}",
                "total_events": len(events),
                "completed_events": len([ep for ep in profitability if ep["status"] == EventStatus.COMPLETED.value]),
                "total_guests": total_guests,
                "total_revenue": round(total_revenue, 2),
                "total_cost": round(total_cost, 2),
                "gross_profit": round(total_profit, 2),
                "profit_margin_percent": round((total_profit / total_revenue * 100) if total_revenue > 0 else 0, 1),
                "avg_revenue_per_event": round(total_revenue / len(events), 2) if events else 0,
                "avg_profit_per_event": round(total_profit / len(events), 2) if events else 0,
                "avg_revenue_per_guest": round(total_revenue / total_guests, 2) if total_guests > 0 else 0,
            })
        
        return trends

    # ─── Chart Data ──────────────────────────────────────────────────────

    def get_revenue_chart_data(self, months: int = 6) -> dict:
        """Get data formatted for revenue/profit line charts."""
        self._sync_event_statuses()

        trends = self._get_monthly_trends(months)
        
        return {
            "labels": [t["month_name"] for t in trends],
            "revenue_data": [t["total_revenue"] for t in trends],
            "cost_data": [t["total_cost"] for t in trends],
            "profit_data": [t["gross_profit"] for t in trends],
            "event_count_data": [t["total_events"] for t in trends],
        }

    def get_expense_chart_data(self, months: int = 1) -> dict:
        """Get data formatted for expense breakdown pie/doughnut charts."""
        self._sync_event_statuses()

        today = date.today()
        period_start = today - relativedelta(months=months)
        events = self._get_period_events(period_start, today)
        
        breakdown = self._get_expense_breakdown(events)
        
        return {
            "labels": [b["category"] for b in breakdown],
            "values": [b["amount"] for b in breakdown],
            "colors": [b["color"] for b in breakdown],
        }

    # ─── Inventory Summary ───────────────────────────────────────────────

    def get_inventory_summary(self) -> dict:
        """Get comprehensive inventory status summary."""
        products = self._active(Product).all()
        
        total_value = 0.0
        low_stock_items = []
        out_of_stock_items = []
        healthy_count = 0
        category_values = defaultdict(float)
        
        for p in products:
            # Calculate inventory value
            value = (p.quantity_in_stock or 0) * (p.price_per_unit or p.estimated_price or 0)
            total_value += value
            
            cat_name = p.category.value if hasattr(p.category, "value") else str(p.category)
            category_values[cat_name] += value
            
            # Check stock status
            if p.quantity_in_stock <= 0:
                out_of_stock_items.append({
                    "id": p.id,
                    "name": p.name,
                    "category": cat_name,
                    "min_stock_level": p.min_stock_level,
                })
            elif p.quantity_in_stock <= p.min_stock_level:
                low_stock_items.append({
                    "id": p.id,
                    "name": p.name,
                    "category": cat_name,
                    "quantity_in_stock": p.quantity_in_stock,
                    "min_stock_level": p.min_stock_level,
                })
            else:
                healthy_count += 1
        
        # Category breakdown
        value_by_category = []
        for i, (cat, val) in enumerate(sorted(category_values.items(), key=lambda x: x[1], reverse=True)):
            value_by_category.append({
                "category": cat,
                "amount": round(val, 2),
                "percentage": round((val / total_value * 100) if total_value > 0 else 0, 1),
                "item_count": 0,
                "color": CATEGORY_COLORS[i % len(CATEGORY_COLORS)]
            })
        
        return {
            "total_products": len(products),
            "total_value": round(total_value, 2),
            "low_stock_count": len(low_stock_items),
            "out_of_stock_count": len(out_of_stock_items),
            "healthy_stock_count": healthy_count,
            "value_by_category": value_by_category,
            "low_stock_items": low_stock_items[:10],  # Limit to top 10
            "out_of_stock_items": out_of_stock_items[:10],
        }

    # ─── Legacy Revenue Summary (kept for backwards compatibility) ───────

    def get_revenue_summary(self) -> dict:
        """Simple revenue summary based on approved/completed events."""
        self._sync_event_statuses()

        approved_events = (
            self._active(Event)
            .filter(Event.status.in_([EventStatus.APPROVED, EventStatus.COMPLETED]))
            .all()
        )

        total_revenue = sum((e.total_price or 0) for e in approved_events)
        total_guests = sum((e.guest_count or 0) for e in approved_events)

        return {
            "total_revenue": total_revenue,
            "total_events": len(approved_events),
            "total_guests": total_guests,
            "avg_revenue_per_event": total_revenue / len(approved_events) if approved_events else 0,
            "avg_revenue_per_guest": total_revenue / total_guests if total_guests else 0,
        }
