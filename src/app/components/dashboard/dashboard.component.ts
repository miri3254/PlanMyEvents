import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { CardModule } from 'primeng/card';
import { ChartModule } from 'primeng/chart';
import { ButtonModule } from 'primeng/button';
import { Observable, combineLatest, EMPTY, of } from 'rxjs';
import { map, catchError, tap } from 'rxjs/operators';
import { ApiDashboardService } from '../../services/api-dashboard.service';
import { ApiEventService } from '../../services/api-event.service';
import { ApiDishService } from '../../services/api-dish.service';
import { ApiLookupService } from '../../services/api-lookup.service';
import { ApiProductService } from '../../services/api-product.service';
import { 
  DashboardStats, 
  UpcomingEvent, 
  LowStockAlert,
  ApiEvent,
  ApiDish
} from '../../core/models/api.models';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, CardModule, ChartModule, ButtonModule],
  template: `
    <div class="dashboard-container" dir="rtl">
      <h1 class="dashboard-title">לוח בקרה</h1>
      
      <!-- Statistics Cards -->
      <div class="stats-grid">
        <div class="stat-card gradient-card">
          <div class="stat-content">
            <div class="stat-icon">
              <i class="pi pi-calendar"></i>
            </div>
            <div class="stat-details">
              <h3>{{ (dashboardStats$ | async)?.total_events || 0 }}</h3>
              <p>סה"כ אירועים</p>
            </div>
          </div>
        </div>

        <div class="stat-card gradient-card">
          <div class="stat-content">
            <div class="stat-icon">
              <i class="pi pi-clock"></i>
            </div>
            <div class="stat-details">
              <h3>{{ (dashboardStats$ | async)?.upcoming_events || 0 }}</h3>
              <p>אירועים קרובים</p>
            </div>
          </div>
        </div>

        <div class="stat-card gradient-card">
          <div class="stat-content">
            <div class="stat-icon">
              <i class="pi pi-star"></i>
            </div>
            <div class="stat-details">
              <h3>{{ (dashboardStats$ | async)?.active_dishes || 0 }}</h3>
              <p>מנות פעילות</p>
            </div>
          </div>
        </div>

        <div class="stat-card gradient-card">
          <div class="stat-content">
            <div class="stat-icon">
              <i class="pi pi-exclamation-triangle"></i>
            </div>
            <div class="stat-details">
              <h3>{{ (dashboardStats$ | async)?.low_stock_products || 0 }}</h3>
              <p>מוצרים במלאי נמוך</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Charts Section -->
      <div class="charts-grid">
        <div class="chart-card card">
          <h3>התפלגות מנות לפי קטגוריה</h3>
          <p-chart type="pie" [data]="dishCategoryData" [options]="chartOptions"></p-chart>
        </div>

        <div class="chart-card card">
          <h3>התפלגות מנות לפי כשרות</h3>
          <p-chart type="doughnut" [data]="kosherTypeData" [options]="chartOptions"></p-chart>
        </div>

        <div class="chart-card card">
          <h3>אירועים לפי סטטוס</h3>
          <p-chart type="bar" [data]="eventStatusData" [options]="barChartOptions"></p-chart>
        </div>
      </div>

      <!-- Upcoming Events Section -->
      <div *ngIf="(upcomingEvents$ | async) as events" class="upcoming-events-section card">
        <h2>אירועים קרובים (7 ימים הקרובים)</h2>
        <div class="events-list">
          <div *ngFor="let event of events" class="event-item">
            <div class="event-details">
              <h4>{{ event.name }}</h4>
              <div class="event-meta">
                <span><i class="pi pi-calendar"></i> {{ formatDate(event.event_date) }}</span>
                <span><i class="pi pi-clock"></i> {{ event.event_time }}</span>
                <span><i class="pi pi-users"></i> {{ event.guest_count }} אורחים</span>
                <span class="status-badge" [ngClass]="'status-' + event.status">{{ getStatusDisplay(event.status) }}</span>
              </div>
            </div>
            <div class="event-actions">
              <p-button 
                label="פרטים"
                icon="pi pi-eye"
                [routerLink]="['/events', event.id]"
                size="small"
                [outlined]="true">
              </p-button>
            </div>
          </div>
        </div>
      </div>

      <!-- Low Stock Alerts -->
      <div *ngIf="(lowStockAlerts$ | async) as alerts" class="low-stock-section card">
        <h2>התראות מלאי נמוך</h2>
        <div *ngIf="alerts.length === 0" class="no-alerts">
          <i class="pi pi-check-circle" style="color: green; font-size: 2rem;"></i>
          <p>כל המוצרים במלאי מספיק</p>
        </div>
        <div *ngIf="alerts.length > 0" class="alerts-list">
          <div *ngFor="let alert of alerts" class="alert-item">
            <div class="alert-icon">
              <i class="pi pi-exclamation-triangle" style="color: orange;"></i>
            </div>
            <div class="alert-details">
              <h4>{{ alert.name }}</h4>
              <p>קטגוריה: {{ alert.category }}</p>
              <span class="inventory-status" [ngClass]="'inventory-' + alert.inventory_status">
                {{ alert.inventory_status }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Links -->
      <div class="quick-links">
        <h3>גישה מהירה</h3>
        <div class="links-grid">
          <a routerLink="/events" class="quick-link-card card">
            <i class="pi pi-calendar"></i>
            <span>נהל אירועים</span>
          </a>
          <a routerLink="/dishes" class="quick-link-card card">
            <i class="pi pi-star"></i>
            <span>נהל מנות</span>
          </a>
          <a routerLink="/products" class="quick-link-card card">
            <i class="pi pi-shopping-cart"></i>
            <span>נהל מוצרים</span>
          </a>
          <a routerLink="/tools" class="quick-link-card card">
            <i class="pi pi-wrench"></i>
            <span>נהל כלים</span>
          </a>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .dashboard-container {
      padding: 20px;
    }

    .dashboard-title {
      margin-bottom: 30px;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 20px;
      margin-bottom: 30px;
    }

    .stat-card {
      padding: 24px;
    }

    .stat-content {
      display: flex;
      align-items: center;
      gap: 20px;
    }

    .stat-icon {
      width: 60px;
      height: 60px;
      background: linear-gradient(135deg, var(--primary), var(--primary-dark));
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 1.8rem;
    }

    .stat-details h3 {
      margin: 0;
      font-size: 2rem;
      font-weight: 700;
      color: var(--primary);
    }

    .stat-details p {
      margin: 4px 0 0 0;
      color: var(--muted-foreground);
      font-size: 0.9rem;
    }

    .charts-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
      gap: 20px;
      margin-bottom: 30px;
    }

    .chart-card {
      padding: 24px;
    }

    .chart-card h3 {
      margin-bottom: 20px;
      color: var(--foreground);
    }

    .upcoming-events-section,
    .low-stock-section {
      padding: 24px;
      margin-bottom: 30px;
    }

    .upcoming-events-section h2,
    .low-stock-section h2 {
      margin-bottom: 20px;
      color: var(--primary);
    }

    .events-list {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .event-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px;
      background: var(--background);
      border-radius: 8px;
      border: 1px solid var(--border);
    }

    .event-details h4 {
      margin: 0 0 8px 0;
      color: var(--primary);
    }

    .event-meta {
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
      font-size: 0.9rem;
      color: var(--muted-foreground);
    }

    .event-meta span {
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .status-badge {
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 0.8rem;
      font-weight: 600;
    }

    .status-pending { background: hsl(45, 100%, 90%); color: hsl(45, 100%, 30%); }
    .status-scheduled { background: hsl(210, 100%, 90%); color: hsl(210, 100%, 30%); }
    .status-in-progress { background: hsl(24, 95%, 90%); color: hsl(24, 95%, 30%); }
    .status-completed { background: hsl(142, 76%, 90%); color: hsl(142, 76%, 30%); }
    .status-cancelled { background: hsl(0, 84%, 90%); color: hsl(0, 84%, 30%); }

    .no-alerts {
      text-align: center;
      padding: 40px;
    }

    .no-alerts p {
      margin-top: 12px;
      color: var(--muted-foreground);
    }

    .alerts-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .alert-item {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 16px;
      background: var(--background);
      border-radius: 8px;
      border: 1px solid var(--border);
    }

    .alert-details h4 {
      margin: 0 0 4px 0;
      color: var(--primary);
    }

    .alert-details p {
      margin: 0 0 8px 0;
      color: var(--muted-foreground);
      font-size: 0.9rem;
    }

    .inventory-status {
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 0.8rem;
      font-weight: 600;
    }

    .inventory-במלאי { background: hsl(142, 76%, 90%); color: hsl(142, 76%, 30%); }
    .inventory-מלאי-נמוך { background: hsl(45, 100%, 90%); color: hsl(45, 100%, 30%); }
    .inventory-אזל { background: hsl(0, 84%, 90%); color: hsl(0, 84%, 30%); }

    .chart-card {
      padding: 24px;
    }

    .chart-card h3 {
      margin-bottom: 20px;
      color: var(--foreground);
    }

    .current-event-section {
      padding: 24px;
      margin-bottom: 30px;
    }

    .current-event-section h2 {
      margin-bottom: 20px;
      color: var(--primary);
    }

    .event-details {
      display: flex;
      gap: 24px;
      margin-bottom: 20px;
      flex-wrap: wrap;
    }

    .detail-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      background: var(--background);
      border-radius: 8px;
    }

    .detail-item i {
      color: var(--primary);
    }

    .event-actions {
      display: flex;
      gap: 12px;
    }

    .no-event-section {
      padding: 60px 24px;
      text-align: center;
    }

    .no-event-section h2 {
      margin: 20px 0 10px 0;
    }

    .no-event-section p {
      color: var(--muted-foreground);
    }

    .quick-links {
      margin-top: 30px;
    }

    .quick-links h3 {
      margin-bottom: 20px;
    }

    .links-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 20px;
    }

    .quick-link-card {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 12px;
      padding: 30px;
      text-decoration: none;
      color: var(--foreground);
      transition: all 0.3s ease;
    }

    .quick-link-card:hover {
      transform: translateY(-4px);
      box-shadow: var(--shadow-hover);
    }

    .quick-link-card i {
      font-size: 2rem;
      color: var(--primary);
    }

    .quick-link-card span {
      font-weight: 600;
    }

    @media (max-width: 768px) {
      .stats-grid,
      .charts-grid,
      .links-grid {
        grid-template-columns: 1fr;
      }

      .event-details {
        flex-direction: column;
        gap: 12px;
      }

      .event-actions {
        flex-direction: column;
      }
    }
  `]
})
export class DashboardComponent implements OnInit {
  dashboardStats$!: Observable<DashboardStats>;
  upcomingEvents$!: Observable<UpcomingEvent[]>;
  lowStockAlerts$!: Observable<LowStockAlert[]>;

  dishCategoryData: any;
  kosherTypeData: any;
  eventStatusData: any;
  chartOptions: any;
  barChartOptions: any;

  constructor(
    private dashboardService: ApiDashboardService,
    private eventService: ApiEventService,
    private dishService: ApiDishService,
    private lookupService: ApiLookupService,
    private productService: ApiProductService
  ) {}

  ngOnInit(): void {
    this.loadDashboardData();
    this.setupCharts();
  }

  loadDashboardData(): void {
    this.dashboardStats$ = this.dashboardService.getDashboardStats().pipe(
      tap(stats => this.updateEventStatusChart(stats.events_by_status)),
      catchError(error => {
        console.error('Error loading dashboard stats:', error);
        return EMPTY;
      })
    );

    this.upcomingEvents$ = this.dashboardService.getUpcomingEvents().pipe(
      catchError(error => {
        if (error?.status === 404) {
          // Fallback for environments where the dedicated endpoint is missing
          return this.loadUpcomingEventsFromEventsApi();
        }

        console.error('Error loading upcoming events:', error);
        return EMPTY;
      })
    );

    this.lowStockAlerts$ = this.dashboardService.getLowStockAlerts().pipe(
      catchError(error => {
        if (error?.status === 404) {
          // Fallback for environments where the dedicated endpoint is missing
          return this.loadLowStockFromProducts();
        }

        console.error('Error loading low stock alerts:', error);
        return EMPTY;
      })
    );
  }

  private loadUpcomingEventsFromEventsApi(): Observable<UpcomingEvent[]> {
    const today = new Date();
    const inSevenDays = new Date();
    inSevenDays.setDate(today.getDate() + 7);

    return this.eventService.getEvents().pipe(
      map(response => {
        const items = response?.items || [];
        return items
          .map(raw => {
            const eventDate = (raw as any).event_date || (raw as any).date;
            const eventTime = (raw as any).event_time || (raw as any).time || '';
            const guestCount = (raw as any).guest_count || (raw as any).participants || 0;
            const status = this.normalizeStatus((raw as any).status);
            return {
              id: raw.id,
              name: raw.name,
              event_date: eventDate,
              event_time: eventTime,
              guest_count: guestCount,
              status
            } as UpcomingEvent;
          })
          .filter(event => {
            if (!event.event_date) {
              return false;
            }
            const date = new Date(event.event_date);
            return date >= today && date <= inSevenDays;
          })
          .sort((a, b) => new Date(a.event_date).getTime() - new Date(b.event_date).getTime());
      }),
      catchError(fallbackError => {
        console.warn('Fallback upcoming events lookup failed:', fallbackError);
        return of([]);
      })
    );
  }

  private normalizeStatus(status: string | undefined): string {
    if (!status) {
      return 'pending';
    }
    const map: { [key: string]: string } = {
      'בהמתנה לאישור': 'pending',
      'ממתין': 'pending',
      'מתוכנן': 'scheduled',
      'scheduled': 'scheduled',
      'in-progress': 'in-progress',
      'עבר': 'completed',
      'הושלם': 'completed',
      'completed': 'completed',
      'התבטל': 'cancelled',
      'cancelled': 'cancelled'
    };
    const normalized = map[status] || status;
    return normalized;
  }

  private loadLowStockFromProducts(): Observable<LowStockAlert[]> {
    return this.productService.getProducts({ inventory_status: 'מלאי נמוך', limit: 200 }).pipe(
      map(response => {
        const items = response?.items || [];
        // Accept also English status variants in case backend differs
        const LOW_STOCK_KEYWORDS = ['מלאי נמוך', 'low'];
        return items
          .filter(product => {
            const status = (product.inventory_status || '').toLowerCase();
            return LOW_STOCK_KEYWORDS.some(key => status.includes(key));
          })
          .map(product => ({
            id: product.id,
            name: product.name,
            category: product.category,
            inventory_status: product.inventory_status
          }));
      }),
      catchError(fallbackError => {
        console.warn('Fallback low stock lookup failed:', fallbackError);
        return of([]);
      })
    );
  }

  setupCharts(): void {
    // Load dishes for category and kosher type charts
    this.dishService.getDishes({ is_active: true }).pipe(
      catchError(error => {
        console.error('Error loading dishes for charts:', error);
        return EMPTY;
      })
    ).subscribe(response => {
      const dishes = response.items;
      
      // Category chart
      const categoryCount: { [key: string]: number } = {};
      dishes.forEach(dish => {
        categoryCount[dish.category] = (categoryCount[dish.category] || 0) + 1;
      });

      this.dishCategoryData = {
        labels: Object.keys(categoryCount),
        datasets: [{
          data: Object.values(categoryCount),
          backgroundColor: [
            'hsla(24, 95%, 53%, 0.8)',
            'hsla(142, 76%, 48%, 0.8)',
            'hsla(210, 100%, 56%, 0.8)',
            'hsla(280, 61%, 56%, 0.8)',
            'hsla(45, 100%, 51%, 0.8)',
            'hsla(0, 84%, 60%, 0.8)'
          ]
        }]
      };

      // Kosher type chart
      const kosherCount: { [key: string]: number } = {};
      dishes.forEach(dish => {
        kosherCount[dish.kosher_type] = (kosherCount[dish.kosher_type] || 0) + 1;
      });

      this.kosherTypeData = {
        labels: Object.keys(kosherCount),
        datasets: [{
          data: Object.values(kosherCount),
          backgroundColor: [
            'hsl(210, 100%, 56%)',   // חלבי
            'hsl(24, 95%, 53%)',     // בשרי
            'hsl(142, 76%, 48%)'     // פרווה
          ]
        }]
      };
    });

    this.chartOptions = {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: 'bottom',
          rtl: true
        }
      }
    };

    this.barChartOptions = {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1
          }
        }
      }
    };
  }

  updateEventStatusChart(eventsByStatus: { [key: string]: number }): void {
    this.eventStatusData = {
      labels: Object.keys(eventsByStatus),
      datasets: [{
        label: 'מספר אירועים',
        data: Object.values(eventsByStatus),
        backgroundColor: [
          'hsl(45, 100%, 51%)',    // pending
          'hsl(210, 100%, 56%)',   // scheduled  
          'hsl(24, 95%, 53%)',     // in-progress
          'hsl(142, 76%, 48%)',    // completed
          'hsl(0, 84%, 60%)'       // cancelled
        ]
      }]
    };
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('he-IL');
  }

  getStatusDisplay(status: string): string {
    const statusMap: { [key: string]: string } = {
      'pending': 'ממתין',
      'scheduled': 'מתוכנן',
      'in-progress': 'בתהליך',
      'completed': 'הושלם',
      'cancelled': 'בוטל'
    };
    return statusMap[status] || status;
  }
}
