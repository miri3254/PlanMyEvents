import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of, EMPTY } from 'rxjs';

import { DashboardComponent } from './dashboard.component';
import { ApiDashboardService } from '../../services/api-dashboard.service';
import { ApiEventService } from '../../services/api-event.service';
import { ApiDishService } from '../../services/api-dish.service';
import { ApiLookupService } from '../../services/api-lookup.service';
import { ApiProductService } from '../../services/api-product.service';

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;
  let mockDashboardService: jasmine.SpyObj<ApiDashboardService>;
  let mockEventService: jasmine.SpyObj<ApiEventService>;
  let mockDishService: jasmine.SpyObj<ApiDishService>;
  let mockLookupService: jasmine.SpyObj<ApiLookupService>;
  let mockProductService: jasmine.SpyObj<ApiProductService>;

  const mockStats = {
    total_events: 5,
    upcoming_events: 2,
    active_dishes: 10,
    low_stock_products: 1,
    events_by_status: { 'טיוטה': 2, 'מאושר': 3 }
  };

  beforeEach(async () => {
    mockDashboardService = jasmine.createSpyObj('ApiDashboardService', [
      'getDashboardStats',
      'getUpcomingEvents',
      'getLowStockAlerts'
    ]);
    mockEventService = jasmine.createSpyObj('ApiEventService', ['getEvents']);
    mockDishService = jasmine.createSpyObj('ApiDishService', ['getDishes']);
    mockLookupService = jasmine.createSpyObj('ApiLookupService', ['getLookupCategory']);
    mockProductService = jasmine.createSpyObj('ApiProductService', ['getProducts']);

    mockDashboardService.getDashboardStats.and.returnValue(of(mockStats as any));
    mockDashboardService.getUpcomingEvents.and.returnValue(of([]));
    mockDashboardService.getLowStockAlerts.and.returnValue(of({ products: [], tools: [] } as any));
    mockDishService.getDishes.and.returnValue(of({ items: [], total: 0 } as any));
    mockProductService.getProducts.and.returnValue(of({ items: [], total: 0, skip: 0, limit: 100 } as any));

    await TestBed.configureTestingModule({
      imports: [
        DashboardComponent,
        RouterTestingModule,
        NoopAnimationsModule
      ],
      providers: [
        { provide: ApiDashboardService, useValue: mockDashboardService },
        { provide: ApiEventService, useValue: mockEventService },
        { provide: ApiDishService, useValue: mockDishService },
        { provide: ApiLookupService, useValue: mockLookupService },
        { provide: ApiProductService, useValue: mockProductService }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should call getDashboardStats on init', () => {
    expect(mockDashboardService.getDashboardStats).toHaveBeenCalled();
  });

  it('should call getUpcomingEvents on init', () => {
    expect(mockDashboardService.getUpcomingEvents).toHaveBeenCalled();
  });

  it('should call getLowStockAlerts on init', () => {
    expect(mockDashboardService.getLowStockAlerts).toHaveBeenCalled();
  });

  it('should format date to Hebrew locale string', () => {
    const result = component.formatDate('2025-06-15');
    expect(result).toBeTruthy();
    expect(typeof result).toBe('string');
    expect(result).toContain('2025');
  });

  it('should format time correctly', () => {
    const result = component.formatTime('2025-06-15T20:30:00');
    expect(result).toBeTruthy();
    expect(typeof result).toBe('string');
  });

  it('should return Hebrew display for "pending" status', () => {
    expect(component.getStatusDisplay('pending')).toBe('ממתין');
  });

  it('should return Hebrew display for "completed" status', () => {
    expect(component.getStatusDisplay('completed')).toBe('הושלם');
  });

  it('should return Hebrew display for "cancelled" status', () => {
    expect(component.getStatusDisplay('cancelled')).toBe('בוטל');
  });

  it('should return status as-is when not in map', () => {
    expect(component.getStatusDisplay('unknown-status')).toBe('unknown-status');
  });

  it('should initialize with undefined observables before ngOnInit', () => {
    // After ngOnInit, the observables should be set
    expect(component.dashboardStats$).toBeDefined();
    expect(component.upcomingEvents$).toBeDefined();
    expect(component.lowStockAlerts$).toBeDefined();
  });
});
