import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';

import { EventDishWizardComponent, WizardStep } from './event-dish-wizard.component';
import { ApiEventService } from '../../services/api-event.service';
import { ApiMenuService } from '../../services/api-menu.service';
import { ApiToolService } from '../../services/api-tool.service';
import { ApiDishService } from '../../services/api-dish.service';
import { MessageService } from 'primeng/api';

const makeStep = (overrides: Partial<WizardStep> = {}): WizardStep => ({
  index: 0,
  title: 'סלטים',
  subMealId: null,
  subMealName: null,
  categoryId: 1,
  categoryName: 'salads',
  categoryNameHebrew: 'סלטים',
  quota: null,
  quotaDescription: null,
  isRequired: false,
  isTrayCategory: false,
  trayPrice: null,
  standardDishes: [],
  upgradeDishes: [],
  loaded: false,
  loading: false,
  selectedDishIds: new Set<number>(),
  ...overrides
});

describe('EventDishWizardComponent', () => {
  let component: EventDishWizardComponent;
  let fixture: ComponentFixture<EventDishWizardComponent>;
  let mockEventService: jasmine.SpyObj<ApiEventService>;
  let mockMenuService: jasmine.SpyObj<ApiMenuService>;
  let mockDishService: jasmine.SpyObj<ApiDishService>;

  beforeEach(async () => {
    mockEventService = jasmine.createSpyObj('ApiEventService', [
      'getEvent',
      'getDishServingSelections',
      'addEventDish',
      'removeEventDish',
      'getEventDishes', 'addDishToEvent', 'removeDishFromEvent', 'updateEventDish', 'getManualTools', 'updateManualTools'
    ]);
    mockMenuService = jasmine.createSpyObj('ApiMenuService', [
      'getMenuByType',
      'getCategoryDishes'
    ]);
    mockDishService = jasmine.createSpyObj('ApiDishService', ['getDishes']);

    mockEventService.getDishServingSelections.and.returnValue(of([]));
    mockEventService.getEvent.and.returnValue(of({
      id: 1,
      name: 'אירוע בדיקה',
      menu_type: 'meat',
      guest_count: 100
    } as any));

    mockMenuService.getMenuByType.and.returnValue(of({
      id: 1,
      name: 'תפריט בשרי',
      is_tray_menu: false,
      sub_meals: [],
      categories: []
    } as any));

    await TestBed.configureTestingModule({
      imports: [
        EventDishWizardComponent,
        RouterTestingModule,
        NoopAnimationsModule
      ],
      providers: [
        {
          provide: ActivatedRoute,
          useValue: {
            params: of({ eventId: '1' })
          }
        },
        { provide: ApiEventService, useValue: mockEventService },
        { provide: ApiMenuService, useValue: mockMenuService },
        { provide: ApiDishService, useValue: mockDishService },
        { provide: ApiToolService, useValue: {getAllTools: () => of([])} },
        MessageService
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(EventDishWizardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('only offers alternatives for the event dishware', () => {
    component.event = {is_real_dishes: true} as any;
    component.servingSets.set(7, [
      {id: 1, name: 'חד פעמי', set_type: 'serving', dishware_type: 'disposable', serving_mode: 'central', is_default: true, items: []},
      {id: 2, name: 'אמיתי', set_type: 'serving', dishware_type: 'real', serving_mode: 'central', is_default: true, items: []}
    ]);
    expect(component.getServingSets(7, 'serving').map(row => row.id)).toEqual([2]);
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load event data on init', () => {
    expect(mockEventService.getEvent).toHaveBeenCalledWith(1);
  });

  it('should load menu template after event loads', () => {
    expect(mockMenuService.getMenuByType).toHaveBeenCalledWith('meat');
  });

  it('should return null for currentStep when steps are empty', () => {
    component.steps = [];
    expect(component.currentStep).toBeNull();
  });

  it('should return first step as currentStep when activeStepIndex is 0', () => {
    component.steps = [makeStep({ index: 0, categoryNameHebrew: 'סלטים' })];
    component.activeStepIndex = 0;
    expect(component.currentStep?.categoryNameHebrew).toBe('סלטים');
  });

  it('should return true for isFirstStep when at index 0', () => {
    component.activeStepIndex = 0;
    expect(component.isFirstStep).toBeTrue();
  });

  it('should return false for isFirstStep when at index > 0', () => {
    component.steps = [makeStep(), makeStep({ index: 1 })];
    component.activeStepIndex = 1;
    expect(component.isFirstStep).toBeFalse();
  });

  it('should return true for isLastStep when at last index', () => {
    component.steps = [makeStep({ index: 0 }), makeStep({ index: 1 })];
    component.activeStepIndex = 1;
    expect(component.isLastStep).toBeTrue();
  });

  it('should return false for isLastStep when not at last index', () => {
    component.steps = [makeStep({ index: 0 }), makeStep({ index: 1 })];
    component.activeStepIndex = 0;
    expect(component.isLastStep).toBeFalse();
  });

  it('should calculate totalSelected across all steps', () => {
    component.steps = [
      makeStep({ selectedDishIds: new Set([1, 2]) }),
      makeStep({ index: 1, selectedDishIds: new Set([3]) })
    ];
    expect(component.totalSelected).toBe(3);
  });

  it('should return zero totalSelected when no dishes are selected', () => {
    component.steps = [
      makeStep({ selectedDishIds: new Set() }),
      makeStep({ index: 1, selectedDishIds: new Set() })
    ];
    expect(component.totalSelected).toBe(0);
  });

  it('should count standard dishes correctly for quota', () => {
    const step = makeStep({
      loaded: true,
      standardDishes: [{ dish_id: 1 } as any, { dish_id: 2 } as any],
      selectedDishIds: new Set([1, 2, 3]) // dish 3 is upgrade
    });
    const count = component.getStandardDishCount(step);
    expect(count).toBe(2); // only standard dish IDs 1 and 2
  });

  it('should group steps by sub meal', () => {
    component.steps = [
      makeStep({ subMealId: 1, subMealName: 'ערב ראשון' }),
      makeStep({ index: 1, subMealId: 1, subMealName: 'ערב ראשון' }),
      makeStep({ index: 2, subMealId: 2, subMealName: 'ערב שני' })
    ];
    const groups = component.subMealGroups;
    expect(groups.length).toBe(2);
    expect(groups[0].steps.length).toBe(2);
    expect(groups[1].steps.length).toBe(1);
  });

  it('adds a catalogue dish outside categories and prevents adding it twice', () => {
    component.event = {id: 1, status: 'טיוטה', dishes: []} as any;
    const updated = {...component.event!, dishes: [{dish_id: 99, category_id: null}]} as any;
    mockEventService.addDishToEvent.and.returnValue(of(updated));
    component.addFreeDish({id: 99, name: 'תוספת', client_price: 12} as any);
    expect(mockEventService.addDishToEvent).toHaveBeenCalledWith(1, {dish_id: 99, quantity: 1, is_upgrade: true, extra_charge: 12});
    component.addFreeDish({id: 99} as any);
    expect(mockEventService.addDishToEvent.calls.count()).toBe(1);
    expect(component.freeDishes.length).toBe(1);
  });

  it('preserves existing manual tools when adding another catalogue tool', () => {
    component.event = {status: 'טיוטה'} as any;
    component.extrasLoaded = true;
    component.manualTools = [{tool_id: 1, quantity: 5, is_reusable: true}];
    component.extraTools = [{id: 2, name: 'כף', sub_category: 'חד פעמי'} as any];
    component.newToolId = 2; component.newToolQuantity = 7;
    mockEventService.updateManualTools.and.returnValue(of({} as any));
    component.addFreeTool();
    expect(mockEventService.updateManualTools.calls.mostRecent().args[1]).toEqual([
      {tool_id: 1, quantity: 5, is_reusable: true},
      {tool_id: 2, name: 'כף', quantity: 7, is_reusable: false}
    ]);
  });

  it('saves an event serving override and supports returning to menu default', () => {
    component.event = {status: 'טיוטה', dishes: [{dish_id: 5}]} as any;
    mockEventService.updateEventDish.and.returnValue(of(component.event!));
    component.setServingMode(5, 'personal');
    expect(mockEventService.updateEventDish).toHaveBeenCalledWith(1, 5, {serving_mode: 'personal'}, undefined);
    component.setServingMode(5, null);
    expect(mockEventService.updateEventDish).toHaveBeenCalledWith(1, 5, {serving_mode: null}, undefined);
    component.event = {status: 'הסתיים'} as any;
    component.setServingMode(5, 'central');
    expect(mockEventService.updateEventDish.calls.count()).toBe(2);
  });
});
