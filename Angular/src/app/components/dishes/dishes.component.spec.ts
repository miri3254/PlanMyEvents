import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { ActivatedRoute } from '@angular/router';
import { of, BehaviorSubject } from 'rxjs';

import { DishesComponent } from './dishes.component';
import { ApiDishService } from '../../services/api-dish.service';
import { ApiProductService } from '../../services/api-product.service';
import { ApiToolService } from '../../services/api-tool.service';
import { ApiLookupService } from '../../services/api-lookup.service';
import { ApiEventService } from '../../services/api-event.service';
import { ApiMenuService } from '../../services/api-menu.service';
import { UnitConversionService } from '../../core/services/unit-conversion.service';
import { ConfirmationService, MessageService } from 'primeng/api';
import { Dish } from '../../core/models';

const makeDish = (overrides: Partial<Dish> = {}): Dish => ({
  id: 1,
  name: 'מנת בדיקה',
  description: 'תיאור',
  kosherType: 'בשרי',
  basePrice: 50,
  clientPrice: 80,
  servingSize: 1,
  servingDescription: '',
  waiterNotes: '',
  isActive: true,
  ingredients: [],
  servingDishes: [],
  menuMappings: [],
  hasNoProducts: true,
  ...overrides
} as Dish);

const mockLookupSnapshot = {
  kosherTypes: ['בשרי', 'חלבי', 'פרווה'],
  units: ['יחידות', 'ק"ג', 'ליטר'],
  productCategories: [],
  inventoryStatuses: [],
  eventStatuses: [],
  toolCategories: [],
  toolSubCategories: []
};

describe('DishesComponent', () => {
  let component: DishesComponent;
  let fixture: ComponentFixture<DishesComponent>;
  let mockDishService: jasmine.SpyObj<ApiDishService>;
  let mockProductService: jasmine.SpyObj<ApiProductService>;
  let mockToolService: jasmine.SpyObj<ApiToolService>;
  let mockEventService: jasmine.SpyObj<ApiEventService>;
  let mockMenuService: jasmine.SpyObj<ApiMenuService>;
  let mockUnitConversionService: jasmine.SpyObj<UnitConversionService>;

  beforeEach(async () => {
    mockDishService = jasmine.createSpyObj('ApiDishService', [
      'getDishes',
      'createDish',
      'updateDish',
      'deleteDish',
      'getServingSets',
      'getCalculationRules', 'getWorkbookPresets'
    ]);
    mockProductService = jasmine.createSpyObj('ApiProductService', ['getProducts']);
    mockToolService = jasmine.createSpyObj('ApiToolService', ['getAllTools']);
    mockEventService = jasmine.createSpyObj('ApiEventService', ['getEvent', 'addEventDish', 'removeEventDish']);
    mockMenuService = jasmine.createSpyObj('ApiMenuService', ['getAllCategoriesGrouped']);
    mockUnitConversionService = jasmine.createSpyObj('UnitConversionService', ['getAll']);

    const mockLookupService = {
      lookup$: new BehaviorSubject(mockLookupSnapshot).asObservable(),
      initializeLookupData: jasmine.createSpy('initializeLookupData'),
      getLookupCategory: jasmine.createSpy('getLookupCategory').and.returnValue(of([]))
    };

    mockDishService.getWorkbookPresets.and.returnValue(of([]));
    mockDishService.getDishes.and.returnValue(of({ items: [], total: 0 } as any));
    mockDishService.getServingSets.and.returnValue(of([]));
    mockDishService.getCalculationRules.and.returnValue(of([]));
    mockProductService.getProducts.and.returnValue(of({ items: [], total: 0, skip: 0, limit: 200 } as any));
    mockToolService.getAllTools.and.returnValue(of([]));
    mockMenuService.getAllCategoriesGrouped.and.returnValue(of([]));
    mockUnitConversionService.getAll.and.returnValue(of({ items: [], total: 0 } as any));

    await TestBed.configureTestingModule({
      imports: [
        DishesComponent,
        RouterTestingModule,
        NoopAnimationsModule
      ],
      providers: [
        {
          provide: ActivatedRoute,
          useValue: { params: of({}) }
        },
        { provide: ApiDishService, useValue: mockDishService },
        { provide: ApiProductService, useValue: mockProductService },
        { provide: ApiToolService, useValue: mockToolService },
        { provide: ApiLookupService, useValue: mockLookupService },
        { provide: ApiEventService, useValue: mockEventService },
        { provide: ApiMenuService, useValue: mockMenuService },
        { provide: UnitConversionService, useValue: mockUnitConversionService },
        ConfirmationService,
        MessageService
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(DishesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load dishes on init', () => {
    expect(mockDishService.getDishes).toHaveBeenCalled();
  });

  it('should load products on init', () => {
    expect(mockProductService.getProducts).toHaveBeenCalled();
  });

  it('should load tools on init', () => {
    expect(mockToolService.getAllTools).toHaveBeenCalled();
  });

  it('should start with view mode "table"', () => {
    expect(component.viewMode).toBe('table');
  });

  it('should start filtering for all kosher types', () => {
    expect(component.filterKosher).toBe('הכל');
  });

  it('should clear all filters', () => {
    component.searchQuery = 'מנה';
    component.filterKosher = 'בשרי';
    component.clearAllFilters();
    expect(component.searchQuery).toBe('');
    expect(component.filterKosher).toBe('הכל');
  });

  it('should return true when dish is selected', () => {
    component.selectedDishIds = new Set([1, 2, 3]);
    expect(component.isDishSelected(2)).toBeTrue();
  });

  it('should return false when dish is not selected', () => {
    component.selectedDishIds = new Set([1, 3]);
    expect(component.isDishSelected(2)).toBeFalse();
  });

  it('should open dialog when handleCreateDish is called', () => {
    component.handleCreateDish();
    expect(component.isDialogOpen).toBeTrue();
    expect(component.editingDish).toBeTruthy();
    expect(component.editingDish!.name).toBe('');
  });

  it('should open edit dialog with dish data', () => {
    const dish = makeDish({ id: 5, name: 'קציצות', kosherType: 'בשרי' });
    component.handleEditDish(dish);
    expect(component.isDialogOpen).toBeTrue();
    expect(component.editingDish!.name).toBe('קציצות');
    expect(component.editingDish!.kosherType).toBe('בשרי');
  });

  it('should convert identical units without transformation', () => {
    component.unitConversions = [];
    const result = component.convertUnits(5, 'ק"ג', 'ק"ג');
    expect(result).toBe(5);
  });

  it('should return null when no conversion is found', () => {
    component.unitConversions = [];
    const result = component.convertUnits(5, 'ק"ג', 'ליטר');
    expect(result).toBeNull();
  });

  it('should translate menu type to Hebrew', () => {
    expect(component.getMenuTypeHebrew('meat')).toBe('תפריט בשרי');
    expect(component.getMenuTypeHebrew('milk')).toBe('תפריט חלבי');
    expect(component.getMenuTypeHebrew('shabbat')).toBe('שבת');
  });

  it('should return original value for unknown menu type', () => {
    expect(component.getMenuTypeHebrew('unknown')).toBe('unknown');
  });
});
