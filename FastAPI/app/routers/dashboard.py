"""
Dashboard router — comprehensive profitability analytics and statistics.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _svc(db: Session = Depends(get_db)) -> DashboardService:
    return DashboardService(db)


# ─── Basic Stats ─────────────────────────────────────────────────────

@router.get("/stats")
def get_stats(svc: DashboardService = Depends(_svc)):
    """Get basic system statistics."""
    return svc.get_stats()


@router.get("/upcoming")
def get_upcoming_events(
    days: int = Query(30, ge=1, le=365),
    svc: DashboardService = Depends(_svc),
):
    """Get upcoming events for the next N days."""
    return svc.get_upcoming_events(days)


@router.get("/low-stock")
def get_low_stock_alerts(svc: DashboardService = Depends(_svc)):
    """Get low stock alerts for products and tools."""
    return svc.get_low_stock_alerts()


@router.get("/revenue")
def get_revenue_summary(svc: DashboardService = Depends(_svc)):
    """Get simple revenue summary (legacy endpoint)."""
    return svc.get_revenue_summary()


# ─── Profitability Analytics ─────────────────────────────────────────

@router.get("/profitability")
def get_profitability_dashboard(
    months: int = Query(1, ge=1, le=24, description="Number of months to analyze"),
    svc: DashboardService = Depends(_svc),
):
    """
    Get comprehensive profitability dashboard.
    
    Returns complete profit analysis including:
    - Total revenue, costs, and profit
    - Comparison with previous period
    - Top performing events
    - Expense breakdown by category
    - Monthly trends
    - Individual event profitability
    """
    return svc.get_profitability_dashboard(months)


@router.get("/profitability/chart/revenue")
def get_revenue_chart_data(
    months: int = Query(6, ge=1, le=24, description="Number of months for trend"),
    svc: DashboardService = Depends(_svc),
):
    """
    Get revenue/profit chart data for line charts.
    
    Returns monthly data with labels, revenue, costs, and profit.
    """
    return svc.get_revenue_chart_data(months)


@router.get("/profitability/chart/expenses")
def get_expense_chart_data(
    months: int = Query(1, ge=1, le=12, description="Number of months to analyze"),
    svc: DashboardService = Depends(_svc),
):
    """
    Get expense breakdown chart data for pie/doughnut charts.
    
    Returns expense breakdown by product category.
    """
    return svc.get_expense_chart_data(months)


# ─── Inventory ───────────────────────────────────────────────────────

@router.get("/inventory")
def get_inventory_summary(svc: DashboardService = Depends(_svc)):
    """
    Get comprehensive inventory status summary.
    
    Returns:
    - Total inventory value
    - Stock status breakdown (healthy/low/out)
    - Value by category
    - Low stock and out of stock alerts
    """
    return svc.get_inventory_summary()
