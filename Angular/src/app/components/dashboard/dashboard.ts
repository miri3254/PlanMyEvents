import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { ChartModule } from 'primeng/chart';
import { PanelModule } from 'primeng/panel';
import { DividerModule } from 'primeng/divider';
import { BadgeModule } from 'primeng/badge';
import { RippleModule } from 'primeng/ripple';
import { TooltipModule } from 'primeng/tooltip';
import { ProgressBarModule } from 'primeng/progressbar';
import { TableModule } from 'primeng/table';
import { SelectButtonModule } from 'primeng/selectbutton';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';

import { ApiDashboardService } from '../../services/api-dashboard.service';
import {
  DashboardStats,
  ProfitabilityDashboard,
  InventorySummary,
  UpcomingEvent,
  LowStockResponse,
  EventProfitability
} from '../../core/models/api.models';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    ButtonModule,
    CardModule,
    TagModule,
    ChartModule,
    PanelModule,
    DividerModule,
    BadgeModule,
    RippleModule,
    TooltipModule,
    ProgressBarModule,
    TableModule,
    SelectButtonModule
  ],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss'
})
export class DashboardComponent implements OnInit {
  private dashboardService = inject(ApiDashboardService);
  
  // Expose Math to template
  Math = Math;

  // Loading states
  loading = true;
  
  // Period selection
  selectedPeriod = 1;
  periodOptions = [
    { label: 'חודש', value: 1 },
    { label: '3 חודשים', value: 3 },
    { label: '6 חודשים', value: 6 },
    { label: 'שנה', value: 12 }
  ];

  // Basic stats
  stats: DashboardStats | null = null;
  
  // Profitability data
  profitability: ProfitabilityDashboard | null = null;
  
  // Inventory
  inventory: InventorySummary | null = null;
  
  // Upcoming events
  upcomingEvents: UpcomingEvent[] = [];
  
  // Low stock
  lowStock: LowStockResponse | null = null;

  // Charts
  revenueChartData: any;
  revenueChartOptions: any;
  expenseChartData: any;
  expenseChartOptions: any;
  profitTrendChartData: any;
  profitTrendChartOptions: any;

  // Quick actions
  quickActions = [
    {
      label: 'אירוע חדש',
      icon: 'pi pi-plus',
      route: '/events/new',
      description: 'צור אירוע חדש',
      color: 'success' as const
    },
    {
      label: 'ניהול אירועים',
      icon: 'pi pi-calendar',
      route: '/events',
      description: 'צפה באירועים קיימים',
      color: 'info' as const
    },
    {
      label: 'ניהול מוצרים',
      icon: 'pi pi-box',
      route: '/products',
      description: 'נהל מלאי מוצרים',
      color: 'warn' as const
    },
    {
      label: 'ניהול מנות',
      icon: 'pi pi-star',
      route: '/dishes',
      description: 'ערוך מנות קיימות',
      color: 'secondary' as const
    }
  ];

  ngOnInit(): void {
    this.initializeCharts();
    this.loadDashboardData();
  }

  loadDashboardData(): void {
    this.loading = true;
    
    forkJoin({
      stats: this.dashboardService.getDashboardStats(),
      profitability: this.dashboardService.getProfitabilityDashboard(this.selectedPeriod),
      inventory: this.dashboardService.getInventorySummary(),
      upcoming: this.dashboardService.getUpcomingEvents(30),
      lowStock: this.dashboardService.getLowStockAlerts()
    }).subscribe({
      next: (data) => {
        this.stats = data.stats;
        this.profitability = data.profitability;
        this.inventory = data.inventory;
        this.upcomingEvents = data.upcoming;
        this.lowStock = data.lowStock;
        
        this.updateCharts();
        this.loading = false;
      },
      error: (err) => {
        console.error('Failed to load dashboard data:', err);
        this.loading = false;
      }
    });
  }

  onPeriodChange(): void {
    this.dashboardService.getProfitabilityDashboard(this.selectedPeriod).subscribe({
      next: (data) => {
        this.profitability = data;
        this.updateCharts();
      }
    });
  }

  initializeCharts(): void {
    const commonOptions = {
      plugins: {
        legend: {
          position: 'bottom' as const,
          labels: {
            usePointStyle: true,
            padding: 15,
            font: { family: 'Arial, sans-serif', size: 12 }
          }
        }
      },
      responsive: true,
      maintainAspectRatio: false
    };

    this.revenueChartOptions = {
      ...commonOptions,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (value: number) => '₪' + value.toLocaleString()
          }
        }
      }
    };

    this.expenseChartOptions = {
      ...commonOptions,
      plugins: {
        ...commonOptions.plugins,
        tooltip: {
          callbacks: {
            label: (context: any) => {
              const value = context.raw || 0;
              return `${context.label}: ₪${value.toLocaleString()}`;
            }
          }
        }
      }
    };

    this.profitTrendChartOptions = {
      ...commonOptions,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (value: number) => '₪' + value.toLocaleString()
          }
        }
      }
    };
  }

  updateCharts(): void {
    if (!this.profitability) return;

    // Revenue vs Profit trend chart
    const trends = this.profitability.monthly_trends || [];
    this.revenueChartData = {
      labels: trends.map(t => t.month_name),
      datasets: [
        {
          label: 'הכנסות',
          data: trends.map(t => t.total_revenue),
          borderColor: '#36A2EB',
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          fill: true,
          tension: 0.4
        },
        {
          label: 'עלויות',
          data: trends.map(t => t.total_cost),
          borderColor: '#FF6384',
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          fill: true,
          tension: 0.4
        },
        {
          label: 'רווח',
          data: trends.map(t => t.gross_profit),
          borderColor: '#4BC0C0',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          fill: true,
          tension: 0.4
        }
      ]
    };

    // Expense breakdown chart
    const expenses = this.profitability.expense_by_category || [];
    this.expenseChartData = {
      labels: expenses.map(e => e.category),
      datasets: [{
        data: expenses.map(e => e.amount),
        backgroundColor: expenses.map(e => e.color || '#999'),
        hoverBackgroundColor: expenses.map(e => (e.color || '#999') + 'CC')
      }]
    };

    // Monthly profit trend bar chart
    this.profitTrendChartData = {
      labels: trends.map(t => t.month_name),
      datasets: [{
        label: 'רווח גולמי',
        data: trends.map(t => t.gross_profit),
        backgroundColor: trends.map(t => t.gross_profit >= 0 ? '#4BC0C0' : '#FF6384'),
        borderRadius: 8
      }]
    };
  }

  // Helper methods
  formatCurrency(value: number): string {
    return '₪' + (value || 0).toLocaleString('he-IL', { maximumFractionDigits: 0 });
  }

  formatPercent(value: number): string {
    return (value || 0).toFixed(1) + '%';
  }

  getChangeIcon(value: number): string {
    if (value > 0) return 'pi pi-arrow-up';
    if (value < 0) return 'pi pi-arrow-down';
    return 'pi pi-minus';
  }

  getChangeClass(value: number, positive: boolean = true): string {
    if (value > 0) return positive ? 'text-green-500' : 'text-red-500';
    if (value < 0) return positive ? 'text-red-500' : 'text-green-500';
    return 'text-gray-500';
  }

  getProfitClass(profit: number): string {
    if (profit > 0) return 'text-green-600';
    if (profit < 0) return 'text-red-600';
    return 'text-gray-600';
  }

  getMarginSeverity(margin: number): 'success' | 'info' | 'warn' | 'danger' | 'secondary' {
    if (margin >= 30) return 'success';
    if (margin >= 20) return 'info';
    if (margin >= 10) return 'warn';
    return 'danger';
  }

  getStatusSeverity(status: string): 'success' | 'info' | 'warn' | 'danger' | 'secondary' {
    switch (status) {
      case 'מאושר': return 'success';
      case 'הסתיים': return 'info';
      case 'מחכה לאישור': return 'warn';
      case 'בוטל': return 'danger';
      default: return 'secondary';
    }
  }

  getInventoryHealthPercent(): number {
    if (!this.inventory || this.inventory.total_products === 0) return 0;
    return (this.inventory.healthy_stock_count / this.inventory.total_products) * 100;
  }

  getInventoryHealthColor(): string {
    const percent = this.getInventoryHealthPercent();
    if (percent >= 80) return 'success';
    if (percent >= 50) return 'warning';
    return 'danger';
  }
}