import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { MatDialogModule, MatDialog } from '@angular/material/dialog';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { of, BehaviorSubject } from 'rxjs';

import { NavigationComponent } from './navigation.component';
import { ApiEventService } from '../../../services/api-event.service';
import { ApiMenuService } from '../../../services/api-menu.service';
import { ConnectionStatusService, ConnectionStatus } from '../../../core/services/connection-status.service';
import { InventoryService } from '../../../services/inventory.service';
import { ApiLookupService, ServerLookupData } from '../../../services/api-lookup.service';

describe('NavigationComponent', () => {
  let component: NavigationComponent;
  let fixture: ComponentFixture<NavigationComponent>;
  let mockEventService: jasmine.SpyObj<ApiEventService>;
  let mockMenuService: jasmine.SpyObj<ApiMenuService>;
  let mockConnectionStatusService: jasmine.SpyObj<ConnectionStatusService>;
  let mockInventoryService: jasmine.SpyObj<InventoryService>;
  let mockLookupService: jasmine.SpyObj<ApiLookupService>;

  const mockConnectionStatus: ConnectionStatus = {
    isConnected: true,
    lastChecked: new Date(),
    message: 'מחובר'
  };

  beforeEach(async () => {
    mockEventService = jasmine.createSpyObj('ApiEventService', ['getEvents', 'createEvent']);
    mockMenuService = jasmine.createSpyObj('ApiMenuService', ['getMenuTemplates']);
    mockConnectionStatusService = jasmine.createSpyObj('ConnectionStatusService', ['forceCheck'], {
      status$: new BehaviorSubject<ConnectionStatus>(mockConnectionStatus).asObservable()
    });
    mockInventoryService = jasmine.createSpyObj('InventoryService', ['updateInventoryFromReceipt']);
    mockLookupService = jasmine.createSpyObj('ApiLookupService', ['getAllLookupData']);

    mockEventService.getEvents.and.returnValue(of({ items: [], total: 0 } as any));
    mockMenuService.getMenuTemplates.and.returnValue(of([]));
    mockLookupService.getAllLookupData.and.returnValue(of({
      event_categories: [],
      kosher_types: [],
      measurement_units: [],
      product_categories: [],
      inventory_statuses: [],
      event_statuses: [],
      tool_categories: [],
      tool_sub_categories: []
    } as ServerLookupData));

    await TestBed.configureTestingModule({
      imports: [
        NavigationComponent,
        RouterTestingModule,
        NoopAnimationsModule,
        MatDialogModule,
        MatSnackBarModule
      ],
      providers: [
        { provide: ApiEventService, useValue: mockEventService },
        { provide: ApiMenuService, useValue: mockMenuService },
        { provide: ConnectionStatusService, useValue: mockConnectionStatusService },
        { provide: InventoryService, useValue: mockInventoryService },
        { provide: ApiLookupService, useValue: mockLookupService }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(NavigationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load quick-create supporting data on init', () => {
    expect(mockMenuService.getMenuTemplates).toHaveBeenCalled();
    expect(mockLookupService.getAllLookupData).toHaveBeenCalled();
  });

  it('should subscribe to connection status on init', () => {
    expect(component.connectionStatus$).toBeDefined();
  });

  it('should return false when form has empty name', () => {
    component.newEvent.name = '';
    component.newEvent.guestCount = 50;
    component.newEvent.eventCategory = 'אירוע פרטי';
    component.newEvent.menuType = 'meat';
    component.newEvent.eventDate = new Date();
    expect(component.isFormValid()).toBeFalse();
  });

  it('should return false when guest count is 0', () => {
    component.newEvent.name = 'אירוע בדיקה';
    component.newEvent.guestCount = 0;
    component.newEvent.menuType = 'meat';
    component.newEvent.eventDate = new Date();
    expect(component.isFormValid()).toBeFalse();
  });

  it('should return false when menu type is empty', () => {
    component.newEvent.name = 'אירוע בדיקה';
    component.newEvent.guestCount = 50;
    component.newEvent.menuType = '';
    component.newEvent.eventDate = new Date();
    expect(component.isFormValid()).toBeFalse();
  });

  it('should return true when all required fields are filled', () => {
    component.newEvent.name = 'אירוע בדיקה';
    component.newEvent.guestCount = 50;
    component.newEvent.eventCategory = 'private-event';
    component.newEvent.menuType = 'meat';
    component.newEvent.eventDate = new Date();
    expect(component.isFormValid()).toBeTrue();
  });

  it('should hide dialog when closeEventDialog is called', () => {
    component.showEventDialog = true;
    component.closeEventDialog();
    expect(component.showEventDialog).toBeFalse();
  });

  it('should reset form when closeEventDialog is called', () => {
    component.newEvent.name = 'שם אירוע';
    component.closeEventDialog();
    expect(component.newEvent.name).toBe('');
  });

  it('should update hebrew date when onDateChange is called', () => {
    const testDate = new Date('2025-05-15');
    component.onDateChange(testDate);
    expect(component.newEvent.hebrewDate).toBeTruthy();
    expect(typeof component.newEvent.hebrewDate).toBe('string');
  });

  it('should dismiss connection banner', () => {
    component.showConnectionBanner = true;
    component.dismissBanner();
    expect(component.showConnectionBanner).toBeFalse();
  });
});
