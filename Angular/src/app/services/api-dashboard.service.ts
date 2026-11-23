import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { BaseApiService } from '../core/services/base-api.service';
import { 
  DashboardStats,
  UpcomingEvent,
  LowStockAlert,
  LowStockResponse,
  ProfitabilityDashboard,
  RevenueChartData,
  ExpenseChartData,
  InventorySummary
} from '../core/models/api.models';

@Injectable({
  providedIn: 'root'
})
export class ApiDashboardService extends BaseApiService {

  // ─── Basic Statistics ─────────────────────────────────────────────────

  getDashboardStats(): Observable<DashboardStats> {
    return this.get<DashboardStats>('/dashboard/stats');
  }

  getUpcomingEvents(days: number = 30): Observable<UpcomingEvent[]> {
    return this.get<UpcomingEvent[]>(`/dashboard/upcoming?days=${days}`);
  }

  getLowStockAlerts(): Observable<LowStockResponse> {
    return this.get<LowStockResponse>('/dashboard/low-stock');
  }

  // ─── Profitability Analytics ──────────────────────────────────────────

  /**
   * Get comprehensive profitability dashboard data
   * @param months Number of months to analyze (default: 1)
   */
  getProfitabilityDashboard(months: number = 1): Observable<ProfitabilityDashboard> {
    return this.get<ProfitabilityDashboard>(`/dashboard/profitability?months=${months}`);
  }

  /**
   * Get revenue/profit chart data for line charts
   * @param months Number of months for trend (default: 6)
   */
  getRevenueChartData(months: number = 6): Observable<RevenueChartData> {
    return this.get<RevenueChartData>(`/dashboard/profitability/chart/revenue?months=${months}`);
  }

  /**
   * Get expense breakdown chart data for pie/doughnut charts
   * @param months Number of months to analyze (default: 1)
   */
  getExpenseChartData(months: number = 1): Observable<ExpenseChartData> {
    return this.get<ExpenseChartData>(`/dashboard/profitability/chart/expenses?months=${months}`);
  }

  // ─── Inventory ────────────────────────────────────────────────────────

  /**
   * Get comprehensive inventory status summary
   */
  getInventorySummary(): Observable<InventorySummary> {
    return this.get<InventorySummary>('/dashboard/inventory');
  }
}