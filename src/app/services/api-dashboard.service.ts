import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { BaseApiService } from '../core/services/base-api.service';
import { 
  DashboardStats,
  UpcomingEvent,
  LowStockAlert
} from '../core/models/api.models';

@Injectable({
  providedIn: 'root'
})
export class ApiDashboardService extends BaseApiService {

  // Dashboard Statistics
  getDashboardStats(): Observable<DashboardStats> {
    return this.get<DashboardStats>('/dashboard/stats');
  }

  // Upcoming Events (next 7 days)
  getUpcomingEvents(): Observable<UpcomingEvent[]> {
    return this.get<UpcomingEvent[]>('/dashboard/upcoming-events');
  }

  // Low Stock Alerts
  getLowStockAlerts(): Observable<LowStockAlert[]> {
    return this.get<LowStockAlert[]>('/dashboard/low-stock-alerts');
  }
}