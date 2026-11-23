import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';

import { EventsComponent } from './events.component';
import { ApiEventService } from '../../services/api-event.service';
import { ApiLookupService } from '../../services/api-lookup.service';
import { ApiMenuService } from '../../services/api-menu.service';
import { ApiProductService } from '../../services/api-product.service';
import { ApiToolService } from '../../services/api-tool.service';
import { MessageService, ConfirmationService } from 'primeng/api';
import { Event, EventStatus } from '../../core/models';

const makeEvent = (overrides: Partial<Event> = {}): Event => ({
  id: 1,
  name: 'אירוע בדיקה',
  guestCount: 100,
  menuType: 'תפריט בשרי',
  date: '2025-12-31',
  status: 'מאושר' as EventStatus,
  owners: [],
  dishes: [],
  ...overrides
});

describe('EventsComponent', () => {
  let component: EventsComponent;
  let fixture: ComponentFixture<EventsComponent>;
  let mockEventService: jasmine.SpyObj<ApiEventService>;
  let mockLookupService: jasmine.SpyObj<ApiLookupService>;
  let mockMenuService: jasmine.SpyObj<ApiMenuService>;
  let mockProductService: jasmine.SpyObj<ApiProductService>;
  let mockToolService: jasmine.SpyObj<ApiToolService>;

  beforeEach(async () => {
    mockEventService = jasmine.createSpyObj('ApiEventService', [
      'getEvents',
      'createEvent',
      'updateEvent',
      'deleteEvent',
      'updateEventStatus',
      'getDeliveryNoteTemplates',
      'toggleMorningSplit',
      'getCalculationSummary'
    ]);
    mockLookupService = jasmine.createSpyObj('ApiLookupService', ['getLookupCategory', 'getAllLookupData']);
    mockMenuService = jasmine.createSpyObj('ApiMenuService', ['getMenuTemplates']);
    mockProductService = jasmine.createSpyObj('ApiProductService', ['getProducts']);
    mockToolService = jasmine.createSpyObj('ApiToolService', ['getTools']);

    mockEventService.getEvents.and.returnValue(of({ items: [], total: 0 } as any));
    mockEventService.getDeliveryNoteTemplates.and.returnValue(of([]));
    mockLookupService.getLookupCategory.and.returnValue(of([]));
    mockLookupService.getAllLookupData.and.returnValue(of({ event_categories: [] } as any));
    mockMenuService.getMenuTemplates.and.returnValue(of([]));
    mockProductService.getProducts.and.returnValue(of({ items: [], total: 0 } as any));
    mockToolService.getTools.and.returnValue(of({ items: [], total: 0 } as any));

    await TestBed.configureTestingModule({
      imports: [
        EventsComponent,
        RouterTestingModule,
        NoopAnimationsModule
      ],
      providers: [
        {
          provide: ActivatedRoute,
          useValue: {
            queryParams: of({}),
            params: of({})
          }
        },
        { provide: ApiEventService, useValue: mockEventService },
        { provide: ApiLookupService, useValue: mockLookupService },
        { provide: ApiMenuService, useValue: mockMenuService },
        { provide: ApiProductService, useValue: mockProductService },
        { provide: ApiToolService, useValue: mockToolService },
        MessageService,
        ConfirmationService
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(EventsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('loads and displays tablecloths automatically when event details open', () => {
    mockEventService.getCalculationSummary.and.returnValue(of({
      event_id: 1, product_requirements: [{ source_type: 'rolls', quantity: 105, formula_label: 'מנות * 1.5' }], charge_requirements: [], warnings: [],
      tool_requirements: [{ source_type: 'tablecloths', quantity: 11, formula_label: '9 + 2' }]
    } as any));
    component.openEventDetails(makeEvent({ status: 'טיוטה' as EventStatus, guestCount: 70 }));
    fixture.detectChanges();
    expect(mockEventService.getCalculationSummary).toHaveBeenCalledWith(1);
    expect(component.activeDetailTab).toBe('overview');
    expect(fixture.nativeElement.textContent).toContain('מפות כולל ספייר');
    expect(fixture.nativeElement.textContent).toContain('11 מפות');
    expect(fixture.nativeElement.textContent).toContain('105 לחמניות');
  });

  it('should load events on init', () => {
    expect(mockEventService.getEvents).toHaveBeenCalled();
  });

  it('should start with "all" filter selected', () => {
    expect(component.selectedFilter).toBe('all');
  });

  it('should change selected filter when setFilter is called', () => {
    component.setFilter('past');
    expect(component.selectedFilter).toBe('past');
  });

  it('should filter for cancelled events', () => {
    component.events = [
      makeEvent({ id: 1, name: 'אירוע פעיל', status: 'מאושר' }),
      makeEvent({ id: 2, name: 'אירוע מבוטל', status: 'בוטל' })
    ];
    component.setFilter('cancelled');
    expect(component.filteredEvents.every(e => e.status === 'בוטל')).toBeTrue();
  });

  it('should show all events when filter is "all"', () => {
    component.events = [
      makeEvent({ id: 1, status: 'טיוטה' }),
      makeEvent({ id: 2, status: 'מאושר' }),
      makeEvent({ id: 3, status: 'בוטל' })
    ];
    component.setFilter('all');
    expect(component.filteredEvents.length).toBe(3);
  });

  it('should start in list-first page layout', () => {
    expect(component.pageLayout).toBe('list-first');
  });

  it('should navigate to next month when changeMonth(1) is called', () => {
    const originalMonth = new Date(component.currentMonth);
    component.changeMonth(1);
    expect(component.currentMonth.getMonth()).toBe((originalMonth.getMonth() + 1) % 12);
  });

  it('should navigate to previous month when changeMonth(-1) is called', () => {
    const month = component.currentMonth;
    const originalMonth = month.getMonth();
    component.changeMonth(-1);
    const expected = originalMonth === 0 ? 11 : originalMonth - 1;
    expect(component.currentMonth.getMonth()).toBe(expected);
  });

  it('should reset to today when goToToday is called', () => {
    component.changeMonth(3);
    component.goToToday();
    const now = new Date();
    expect(component.currentMonth.getMonth()).toBe(now.getMonth());
    expect(component.currentMonth.getFullYear()).toBe(now.getFullYear());
  });

  it('should load menu templates on init', () => {
    expect(mockMenuService.getMenuTemplates).toHaveBeenCalled();
  });
});
