import { Component, OnInit } from '@angular/core';
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

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    ButtonModule,
    CardModule,
    TagModule,
    ChartModule,
    PanelModule,
    DividerModule,
    BadgeModule,
    RippleModule,
    TooltipModule,
    ProgressBarModule
  ],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss'
})
export class DashboardComponent implements OnInit {
  
  // Dashboard stats
  totalDishes: number = 0;
  totalIngredients: number = 0;
  totalEvents: number = 0;
  averageIngredientsPerDish: number = 0;
  
  // Category distribution
  dishCategoriesData: any;
  dishCategoriesOptions: any;
  
  // Kosher type distribution
  kosherTypesData: any;
  kosherTypesOptions: any;
  
  // Quick actions
  quickActions = [
    {
      label: 'מנה חדשה',
      icon: 'pi pi-plus',
      route: '/dishes',
      description: 'הוסף מנה חדשה למערכת',
      color: 'success' as const
    },
    {
      label: 'ניהול מנות',
      icon: 'pi pi-list',
      route: '/dishes',
      description: 'צפה וערוך מנות קיימות',
      color: 'info' as const
    },
    {
      label: 'תכנון אירוע',
      icon: 'pi pi-calendar',
      route: '/dishes',
      description: 'תכנן אירוע חדש',
      color: 'warn' as const
    },
    {
      label: 'ניהול מוצרים',
      icon: 'pi pi-box',
      route: '/products',
      description: 'נהל מלאי מוצרים',
      color: 'secondary' as const
    }
  ];
  
  // Recent activity (mock data for now)
  recentActivity = [
    {
      type: 'dish',
      action: 'נוסף',
      title: 'חומוס ביתי',
      time: 'לפני שעתיים',
      icon: 'pi pi-plus'
    },
    {
      type: 'event',
      action: 'תוכנן',
      title: 'ארוחת שבת',
      time: 'אתמול',
      icon: 'pi pi-calendar'
    },
    {
      type: 'ingredient',
      action: 'עודכן',
      title: 'קמח לבן',
      time: 'לפני 3 ימים',
      icon: 'pi pi-pencil'
    }
  ];

  ngOnInit(): void {
    this.loadDashboardData();
    this.initializeCharts();
  }

  loadDashboardData(): void {
    // TODO: Load real data from services
    // For now using mock data
    this.totalDishes = 12;
    this.totalIngredients = 45;
    this.totalEvents = 3;
    this.averageIngredientsPerDish = 3.8;
    
    this.updateCategoriesChart();
    this.updateKosherTypesChart();
  }
  
  initializeCharts(): void {
    // Common chart options for Hebrew RTL
    const commonOptions = {
      plugins: {
        legend: {
          position: 'bottom' as const,
          labels: {
            usePointStyle: true,
            padding: 20,
            font: {
              family: 'Arial, sans-serif',
              size: 12
            }
          }
        }
      },
      responsive: true,
      maintainAspectRatio: false
    };

    this.dishCategoriesOptions = {
      ...commonOptions,
      plugins: {
        ...commonOptions.plugins,
        title: {
          display: true,
          text: 'התפלגות מנות לפי קטגוריה'
        }
      }
    };

    this.kosherTypesOptions = {
      ...commonOptions,
      plugins: {
        ...commonOptions.plugins,
        title: {
          display: true,
          text: 'התפלגות מנות לפי סוג כשרות'
        }
      }
    };
  }

  updateCategoriesChart(): void {
    this.dishCategoriesData = {
      labels: ['מנה עיקרית', 'מנה ראשונה', 'תוספת', 'קינוח'],
      datasets: [
        {
          data: [5, 3, 2, 2],
          backgroundColor: [
            '#FF6384',
            '#36A2EB', 
            '#FFCE56',
            '#4BC0C0'
          ],
          hoverBackgroundColor: [
            '#FF6384CC',
            '#36A2EBCC',
            '#FFCE56CC', 
            '#4BC0C0CC'
          ]
        }
      ]
    };
  }

  updateKosherTypesChart(): void {
    this.kosherTypesData = {
      labels: ['חלבי', 'בשרי', 'פרווה'],
      datasets: [
        {
          data: [4, 3, 5],
          backgroundColor: [
            '#007bff',
            '#dc3545', 
            '#28a745'
          ],
          hoverBackgroundColor: [
            '#007bffCC',
            '#dc3545CC',
            '#28a745CC'
          ]
        }
      ]
    };
  }

  getActivityIcon(type: string): string {
    switch (type) {
      case 'dish': return 'pi pi-star';
      case 'event': return 'pi pi-calendar';
      case 'ingredient': return 'pi pi-list';
      default: return 'pi pi-info-circle';
    }
  }

  getActivityColor(type: string): "success" | "info" | "warn" | "danger" | "secondary" | "contrast" | null {
    switch (type) {
      case 'dish': return 'success';
      case 'event': return 'warn';
      case 'ingredient': return 'info';
      default: return 'secondary';
    }
  }
}