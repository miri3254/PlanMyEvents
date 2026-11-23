"""
Dashboard schemas — comprehensive profitability and analytics models.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


# ─── Basic Stats ──────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_events: int = 0
    total_dishes: int = 0
    total_products: int = 0
    total_tools: int = 0
    upcoming_events: int = 0
    events_by_status: dict = {}
    active_dishes: int = 0
    low_stock_products: int = 0
    low_stock_tools: int = 0


class UpcomingEvent(BaseModel):
    id: int
    name: str
    menu_type: Optional[str] = None
    status: Optional[str] = None
    date: Optional[datetime] = None
    event_time: Optional[str] = None
    guest_count: int = 0
    city: Optional[str] = None


class LowStockAlert(BaseModel):
    entity_type: str          # "product" or "tool"
    id: int
    name: str
    category: Optional[str] = None
    quantity_in_stock: float = 0
    min_stock_level: float = 0
    inventory_status: str


# ─── Profitability Models ──────────────────────────────────────────────

class EventProfitability(BaseModel):
    """Profitability data for a single event."""
    event_id: int
    event_name: str
    event_date: Optional[datetime] = None
    guest_count: int = 0
    menu_type: Optional[str] = None
    status: Optional[str] = None
    
    # Revenue (what client paid)
    revenue: float = 0.0
    
    # Costs breakdown
    food_cost: float = 0.0           # Cost of ingredients/products
    labor_cost: float = 0.0          # Estimated labor
    equipment_cost: float = 0.0      # Equipment rental/usage
    
    # Profitability
    total_cost: float = 0.0
    gross_profit: float = 0.0
    profit_margin_percent: float = 0.0
    profit_per_guest: float = 0.0


class MonthlyProfitSummary(BaseModel):
    """Monthly profit summary for trends."""
    year: int
    month: int
    month_name: str                  # e.g., "ינואר 2026"
    
    # Event counts
    total_events: int = 0
    completed_events: int = 0
    total_guests: int = 0
    
    # Financials
    total_revenue: float = 0.0
    total_cost: float = 0.0
    gross_profit: float = 0.0
    profit_margin_percent: float = 0.0
    
    # Averages
    avg_revenue_per_event: float = 0.0
    avg_profit_per_event: float = 0.0
    avg_revenue_per_guest: float = 0.0


class ExpenseBreakdown(BaseModel):
    """Expense breakdown by category."""
    category: str                    # e.g., "בשר", "ירקות", "מוצרי חלב"
    amount: float = 0.0
    percentage: float = 0.0
    item_count: int = 0


class ProfitabilityDashboard(BaseModel):
    """Complete profitability dashboard data."""
    
    # Period info
    period_start: date
    period_end: date
    period_label: str                # e.g., "החודש האחרון"
    
    # Overview KPIs
    total_revenue: float = 0.0
    total_cost: float = 0.0
    total_profit: float = 0.0
    profit_margin_percent: float = 0.0
    
    # Comparisons
    revenue_vs_last_period: float = 0.0       # % change
    profit_vs_last_period: float = 0.0        # % change
    events_vs_last_period: float = 0.0        # % change
    
    # Event stats
    total_events: int = 0
    completed_events: int = 0
    total_guests: int = 0
    avg_revenue_per_event: float = 0.0
    avg_profit_per_event: float = 0.0
    avg_profit_per_guest: float = 0.0
    
    # Top performers
    most_profitable_event: Optional[EventProfitability] = None
    highest_margin_event: Optional[EventProfitability] = None
    
    # Expense breakdown
    expense_by_category: List[ExpenseBreakdown] = []
    
    # Monthly trends (last 6-12 months)
    monthly_trends: List[MonthlyProfitSummary] = []
    
    # Individual events
    events_profitability: List[EventProfitability] = []


class InventorySummary(BaseModel):
    """Inventory status summary."""
    total_products: int = 0
    total_value: float = 0.0              # Total inventory value
    
    low_stock_count: int = 0
    out_of_stock_count: int = 0
    healthy_stock_count: int = 0
    
    # By category
    value_by_category: List[ExpenseBreakdown] = []
    
    # Alerts
    low_stock_items: List[dict] = []
    out_of_stock_items: List[dict] = []


class RevenueChartData(BaseModel):
    """Data for revenue/profit charts."""
    labels: List[str] = []                # Month labels
    revenue_data: List[float] = []        # Monthly revenue
    cost_data: List[float] = []           # Monthly costs
    profit_data: List[float] = []         # Monthly profit
    event_count_data: List[int] = []      # Events per month


class ExpenseChartData(BaseModel):
    """Data for expense breakdown charts."""
    labels: List[str] = []                # Category labels
    values: List[float] = []              # Values
    colors: List[str] = []                # Chart colors
