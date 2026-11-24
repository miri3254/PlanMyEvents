import { ApiToolService } from '../../services/api-tool.service';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';

import { MenusComponent } from './menus.component';
import { ApiMenuService } from '../../services/api-menu.service';
import { ApiDishService } from '../../services/api-dish.service';
import { MessageService, ConfirmationService } from 'primeng/api';
import { MenuTemplate } from '../../models/menu.model';

const makeMenuTemplate = (overrides: Partial<MenuTemplate> = {}): MenuTemplate => ({
  id: 1,
  name: 'תפריט בשרי',
  description: 'תיאור תפריט',
  min_guests: 50,
  base_price_per_guest: 120,
  real_dishes_extra_per_guest: undefined,
  is_tray_menu: false,
  kosher_type: 'בשרי',
  sub_meals: [],
  categories: [],
  ...overrides
});

describe('MenusComponent', () => {
  let component: MenusComponent;
  let fixture: ComponentFixture<MenusComponent>;
  let mockMenuService: jasmine.SpyObj<ApiMenuService>;
  let mockDishService: jasmine.SpyObj<ApiDishService>;

  beforeEach(async () => {
    mockMenuService = jasmine.createSpyObj('ApiMenuService', [
      'getMenuTemplates',
      'createMenuTemplate',
      'updateMenuTemplate',
      'deleteMenuTemplate', 'updateDishMapping'
    ]);
    mockDishService = jasmine.createSpyObj('ApiDishService', ['getDishes', 'getAllDishes']);

    mockMenuService.getMenuTemplates.and.returnValue(of([]));
    mockDishService.getDishes.and.returnValue(of({ items: [], total: 0 } as any));

    await TestBed.configureTestingModule({
      imports: [
        MenusComponent,
        NoopAnimationsModule
      ],
      providers: [
        { provide: ApiToolService, useValue: { getAllTools: () => of([]) } },
        { provide: ApiMenuService, useValue: mockMenuService },
        { provide: ApiDishService, useValue: mockDishService },
        MessageService,
        ConfirmationService
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(MenusComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('edits place settings without mutating the loaded menu before save', () => {
    const menu = makeMenuTemplate({table_setting_items: [{name: 'כוס', quantity: 1, disposable_tool_id: 4, real_tool_id: 5}]});
    component.openEditForm(menu);
    component.menuForm.tableSettingItems![0].quantity = 2;
    expect(menu.table_setting_items![0].quantity).toBe(1);
    mockMenuService.updateMenuTemplate.and.returnValue(of(menu));
    component.submitForm();
    expect(mockMenuService.updateMenuTemplate.calls.mostRecent().args[1].table_setting_items![0].quantity).toBe(2);
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('does not send a manual calculation profile when editing a menu', () => {
    const menu = makeMenuTemplate({ tablecloth_profile: 'shabbat' });
    component.openEditForm(menu);
    component.menuForm.name = 'שם חדש';
    mockMenuService.updateMenuTemplate.and.returnValue(of(menu));
    component.submitForm();
    expect(mockMenuService.updateMenuTemplate).toHaveBeenCalledWith(1,
      jasmine.objectContaining({ name: 'שם חדש' }));
    expect(mockMenuService.updateMenuTemplate.calls.mostRecent().args[1].hasOwnProperty('tablecloth_profile')).toBeFalse();
  });

  it('should load menus on init', () => {
    expect(mockMenuService.getMenuTemplates).toHaveBeenCalled();
  });

  it('should set loading to false after menus are loaded', () => {
    expect(component.loading).toBeFalse();
  });

  it('should filter menus by search term', () => {
    component.menus = [
      makeMenuTemplate({ id: 1, name: 'תפריט בשרי' }),
      makeMenuTemplate({ id: 2, name: 'תפריט חלבי' })
    ];

    component.searchTerm = 'בשרי';
    component.applyFilter();

    expect(component.filteredMenus.length).toBe(1);
    expect(component.filteredMenus[0].name).toBe('תפריט בשרי');
  });

  it('should show all menus when search term is empty', () => {
    component.menus = [
      makeMenuTemplate({ id: 1, name: 'תפריט בשרי' }),
      makeMenuTemplate({ id: 2, name: 'תפריט חלבי' })
    ];

    component.searchTerm = '';
    component.applyFilter();

    expect(component.filteredMenus.length).toBe(2);
  });

  it('should open create form with empty values', () => {
    component.openCreateForm();
    expect(component.menuFormVisible).toBeTrue();
    expect(component.menuFormMode).toBe('create');
    expect(component.menuForm.name).toBe('');
  });

  it('should open edit form with existing menu values', () => {
    const menu = makeMenuTemplate({ id: 3, name: 'תפריט שבת', min_guests: 100 });
    component.openEditForm(menu);
    expect(component.menuFormVisible).toBeTrue();
    expect(component.menuFormMode).toBe('edit');
    expect(component.menuForm.name).toBe('תפריט שבת');
    expect(component.menuForm.minGuests).toBe(100);
  });

  it('should close form and reset when closeForm is called', () => {
    component.menuFormVisible = true;
    component.menuForm.name = 'תפריט זמני';
    component.closeForm();
    expect(component.menuFormVisible).toBeFalse();
    expect(component.menuForm.name).toBe('');
  });

  it('should return false for isFormValid when name is empty', () => {
    component.menuForm.name = '';
    expect(component.isFormValid()).toBeFalse();
  });

  it('should return true for isFormValid when required fields are filled', () => {
    component.menuForm.name = 'תפריט תקין';
    component.menuForm.minGuests = 10;
    expect(component.isFormValid()).toBeTrue();
  });

  it('should show error when loadMenus fails', () => {
    mockMenuService.getMenuTemplates.and.returnValue(throwError(() => new Error('שגיאת שרת')));
    component.loadMenus();
    expect(component.loading).toBeFalse();
  });

  it('round trips a per-menu serving default without changing the dish globally', () => {
    const dish = {id: 10, is_upgrade: false, default_serving_mode: 'personal'};
    component.openDishEdit(dish);
    component.dishEditMap[10].default_serving_mode = 'central';
    mockMenuService.updateDishMapping.and.returnValue(of({} as any));
    component.saveDishEdit(dish);
    expect(mockMenuService.updateDishMapping).toHaveBeenCalledWith(10, jasmine.objectContaining({default_serving_mode: 'central'}));
    expect(dish.default_serving_mode).toBe('central');
  });
});
