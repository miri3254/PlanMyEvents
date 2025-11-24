import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { CardModule } from 'primeng/card';
import { ChartModule } from 'primeng/chart';
import { ButtonModule } from 'primeng/button';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { EventService } from '../../core/services/event.service';
import { Event, Dish, Product } from '../../core/models';

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
              <h3>{{ (events$ | async)?.length || 0 }}</h3>
              <p>אירועים פעילים</p>
            </div>
          </div>
        </div>

        <div class="stat-card gradient-card">
          <div class="stat-content">
            <div class="stat-icon">
              <i class="pi pi-star"></i>
            </div>
            <div class="stat-details">
              <h3>{{ activeDishesCount$ | async }}</h3>
              <p>מנות פעילות</p>
            </div>
          </div>
        </div>

        <div class="stat-card gradient-card">
          <div class="stat-content">
            <div class="stat-icon">
              <i class="pi pi-shopping-cart"></i>
            </div>
            <div class="stat-details">
              <h3>{{ productsInStockCount$ | async }}</h3>
              <p>מוצרים במלאי</p>
            </div>
          </div>
        </div>

        <div class="stat-card gradient-card">
          <div class="stat-content">
            <div class="stat-icon">
              <i class="pi pi-shopping-bag"></i>
            </div>
            <div class="stat-details">
              <h3>{{ cartItemsCount$ | async }}</h3>
              <p>פריטים בעגלה</p>
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
      </div>

      <!-- Current Event Section -->
      <div *ngIf="currentEvent$ | async as event" class="current-event-section card">
        <h2>אירוע נוכחי: {{ event.name }}</h2>
        <div class="event-details">
          <div class="detail-item">
            <i class="pi pi-users"></i>
            <span>{{ event.participants }} משתתפים</span>
          </div>
          <div class="detail-item">
            <i class="pi pi-tag"></i>
            <span>{{ event.eventType }}</span>
          </div>
          <div class="detail-item">
            <span class="kosher-badge" [ngClass]="getKosherClass(event.foodType)">
              {{ event.foodType }}
            </span>
          </div>
        </div>
        <div class="event-actions">
          <p-button 
            label="נהל מנות"
            icon="pi pi-star"
            routerLink="/dishes"
            [outlined]="true">
          </p-button>
          <p-button 
            label="עבור לעגלה"
            icon="pi pi-shopping-bag"
            routerLink="/cart"
            severity="primary">
          </p-button>
        </div>
      </div>

      <!-- No Event Selected -->
      <div *ngIf="!(currentEvent$ | async)" class="no-event-section card">
        <i class="pi pi-calendar-plus" style="font-size: 3rem; color: var(--muted-foreground);"></i>
        <h2>לא נבחר אירוע</h2>
        <p>בחר או צור אירוע חדש כדי להתחיל לתכנן</p>
      </div>

      <!-- Quick Links -->
      <div class="quick-links">
        <h3>גישה מהירה</h3>
        <div class="links-grid">
          <a routerLink="/dishes" class="quick-link-card card">
            <i class="pi pi-star"></i>
            <span>נהל מנות</span>
          </a>
          <a routerLink="/products" class="quick-link-card card">
            <i class="pi pi-shopping-cart"></i>
            <span>נהל מוצרים</span>
          </a>
          <a routerLink="/cart" class="quick-link-card card">
            <i class="pi pi-shopping-bag"></i>
            <span>עגלת קניות</span>
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
      grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
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
  events$!: Observable<Event[]>;
  currentEvent$!: Observable<Event | null>;
  activeDishesCount$!: Observable<number>;
  productsInStockCount$!: Observable<number>;
  cartItemsCount$!: Observable<number>;

  dishCategoryData: any;
  kosherTypeData: any;
  chartOptions: any;

  constructor(private eventService: EventService) {}

  ngOnInit(): void {
    this.events$ = this.eventService.events$;
    this.currentEvent$ = this.eventService.currentEvent$;
    
    this.activeDishesCount$ = this.eventService.dishes$.pipe(
      map(dishes => dishes.filter(d => d.isActive).length)
    );

    this.productsInStockCount$ = this.eventService.products$.pipe(
      map(products => products.filter(p => p.inventoryStatus === 'במלאי').length)
    );

    this.cartItemsCount$ = this.eventService.currentCart$.pipe(
      map(cart => cart.length)
    );

    // Initialize charts
    this.setupCharts();
  }

  setupCharts(): void {
    this.eventService.dishes$.subscribe(dishes => {
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
        kosherCount[dish.kosherType] = (kosherCount[dish.kosherType] || 0) + 1;
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
  }

  getKosherClass(kosherType: string): string {
    switch (kosherType) {
      case 'חלבי': return 'kosher-badge-dairy';
      case 'בשרי': return 'kosher-badge-meat';
      case 'פרווה': return 'kosher-badge-parve';
      default: return '';
    }
  }
}
