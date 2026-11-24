import { WorkbookPreset } from '../../core/models/api.models';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Observable, Subject, combineLatest, EMPTY, BehaviorSubject, forkJoin, of } from 'rxjs';
import { map, takeUntil, catchError, finalize, switchMap } from 'rxjs/operators';
import { LoadingOverlayComponent } from '../../shared/loading-overlay/loading-overlay.component';
import { ApiDishService } from '../../services/api-dish.service';
import { ApiProductService } from '../../services/api-product.service';
import { ApiToolService } from '../../services/api-tool.service';
import { ApiLookupService } from '../../services/api-lookup.service';
import { ApiEventService } from '../../services/api-event.service';
import { ApiMenuService } from '../../services/api-menu.service';
import { UnitConversionService } from '../../core/services/unit-conversion.service';
import { ApiDish, ApiProduct, ApiTool, ApiEvent, DishCreate, DishUpdate, EventDishCreate, DishServingSet, DishCalculationRule } from '../../core/models/api.models';
import { Dish, DishIngredient, ServingDish, Product, Tool, Event, DishMenuMappingInfo, UnitConversion } from '../../core/models';
import { KOSHER_TYPES, UNIT_TYPES, KosherType } from '../../core/models/enums';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { InputNumberModule } from 'primeng/inputnumber';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ToastModule } from 'primeng/toast';
import { ConfirmationService, MessageService } from 'primeng/api';
import { SelectModule } from 'primeng/select';
import { TableModule } from 'primeng/table';
import { Tabs, TabPanel, TabList, TabPanels, Tab } from 'primeng/tabs';
import { CheckboxModule } from 'primeng/checkbox';
import { DividerModule } from 'primeng/divider';
import { ScrollPanelModule } from 'primeng/scrollpanel';
import { TextareaModule } from 'primeng/textarea';
import { AccordionModule } from 'primeng/accordion';
import { DishMenuMappingCreate } from '../../models/menu.model';

@Component({
  selector: 'app-dishes',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ButtonModule,
    DialogModule,
    InputTextModule,
    InputNumberModule,
    CardModule,
    TagModule,
    ConfirmDialogModule,
    ToastModule,
    SelectModule,
    TableModule,
    Tabs,
    TabPanel,
    TabList,
    TabPanels,
    Tab,
    CheckboxModule,
    DividerModule,
    ScrollPanelModule,
    TextareaModule,
    AccordionModule,
    LoadingOverlayComponent
  ],
  templateUrl: './dishes.component.html',
  styleUrls: ['./dishes.component.scss'],
  providers: [ConfirmationService, MessageService]
})
export class DishesComponent implements OnInit, OnDestroy {
    /** מיפוי שמות תפריט לאפשרות בעברית */
    menuTypeHebrewMap: { [key: string]: string } = {
      'meat': 'תפריט בשרי',
      'MEAT_MENU': 'תפריט בשרי',
      'milk': 'תפריט חלבי',
      'MILK_MENU': 'תפריט חלבי',
      'sweet': 'תפריט מתוק',
      'SWEET_MENU': 'תפריט מתוק',
      'shabbat': 'שבת',
      'SHABBAT': 'שבת',
      'parve': 'תפריט פרווה',
      'PARVE_MENU': 'תפריט פרווה',
      'fish': 'תפריט דגים',
      'FISH_MENU': 'תפריט דגים',
      'vegan': 'תפריט טבעוני',
      'VEGAN_MENU': 'תפריט טבעוני',
      'vegetarian': 'תפריט צמחוני',
      'VEGETARIAN_MENU': 'תפריט צמחוני',
      'מגשי אירוח': 'מגשי אירוח',
      'HOSTING_TRAYS': 'מגשי אירוח',
      'תפריט בשרי': 'תפריט בשרי',
      'תפריט חלבי': 'תפריט חלבי',
      'תפריט מתוק': 'תפריט מתוק',
      'שבת': 'שבת',
      'פרווה': 'תפריט פרווה',
      'דגים': 'תפריט דגים',
      'טבעוני': 'תפריט טבעוני',
      'צמחוני': 'תפריט צמחוני',
      '123': 'תפריט מיוחד',
      'SPECIAL_MENU': 'תפריט מיוחד'
    };

    getMenuTypeHebrew(menuType: string): string {
      return this.menuTypeHebrewMap[menuType] || menuType;
    }
  private destroy$ = new Subject<void>();
  private filterChange$ = new BehaviorSubject<void>(undefined);

  dishes$!: Observable<Dish[]>;
  products$!: Observable<Product[]>;
  tools$!: Observable<Tool[]>;
  currentEvent$!: Observable<Event | null>;
  filteredDishes$!: Observable<Dish[]>;

  viewMode: 'table' | 'grid' = 'table';
  searchQuery: string = '';
  filterKosher: string = 'הכל';
  editingDish: Dish | null = null;
  isDialogOpen: boolean = false;
  isLoading = true;

  currentEvent: Event | null = null;
  isEventMode: boolean = false;
  eventId: number | null = null;
  selectedDishIds: Set<number> = new Set();
  products: Product[] = [];
  tools: Tool[] = [];
  originalIngredients: DishIngredient[] = [];
  originalServingDishes: any[] = [];
  dishServingSets: DishServingSet[] = [];
  workbookPresets: WorkbookPreset[] = [];
  workbookPresetKey = '';
  dishCalculationRules: Array<DishCalculationRule & { paramsJson?: string }> = [];

  // Menu mapping state
  allCategoriesGrouped: any[] = [];
  selectedCategoryIds: Set<number> = new Set();
  originalMappings: DishMenuMappingInfo[] = [];
  filterMenuType: string = 'הכל';
  
  // Upgrade settings per category: categoryId -> { isUpgrade, extraCharge }
  categoryUpgradeSettings: Map<number, { isUpgrade: boolean; extraCharge: number | null }> = new Map();

  kosherOptions = [{ label: 'כל סוגי הכשרות', value: 'הכל' }];
  kosherTypes: string[] = [...KOSHER_TYPES];
  units: string[] = [...UNIT_TYPES];
  yieldUnits: string[] = [];  // lookup dish_yield_units (settings)
  
  // Unit conversion cache
  unitConversions: UnitConversion[] = [];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private dishService: ApiDishService,
    private productService: ApiProductService,
    private toolService: ApiToolService,
    private lookupService: ApiLookupService,
    private eventService: ApiEventService,
    private menuService: ApiMenuService,
    private unitConversionService: UnitConversionService,
    private confirmationService: ConfirmationService,
    private messageService: MessageService
  ) {
    this.dishes$ = new BehaviorSubject<Dish[]>([]);
    this.products$ = new BehaviorSubject<Product[]>([]);
    this.tools$ = new BehaviorSubject<Tool[]>([]);
    this.currentEvent$ = new BehaviorSubject<Event | null>(null);
  }

  ngOnInit(): void {
    this.route.params.pipe(takeUntil(this.destroy$)).subscribe(params => {
      if (params['eventId']) {
        this.eventId = +params['eventId'];
        this.loadEventDetails(this.eventId);
      }
    });

    this.loadDishes();
    this.loadProducts();
    this.loadTools();
    this.loadLookupData();
    this.loadCategoriesGrouped();
    this.loadUnitConversions();
    this.dishService.getWorkbookPresets().pipe(takeUntil(this.destroy$)).subscribe({next: presets => this.workbookPresets = presets, error: () => this.messageService.add({severity: 'error', summary: 'לא ניתן לטעון את נוסחאות האקסל'})});

    this.products$.pipe(takeUntil(this.destroy$)).subscribe(products => {
      this.products = products;
    });

    this.tools$.pipe(takeUntil(this.destroy$)).subscribe(tools => {
      this.tools = tools;
    });

    this.currentEvent$.pipe(takeUntil(this.destroy$)).subscribe(event => {
      this.currentEvent = event;
      this.isEventMode = !!event;
      this.filterChange$.next();
    });

    this.setupFilteredDishes();
  }

  // ========================================
  // Data Loading
  // ========================================

  loadEventDetails(eventId: number): void {
    this.eventService.getEvent(eventId)
      .pipe(
        takeUntil(this.destroy$),
        catchError(error => {
          console.error('Error loading event:', error);
          this.messageService.add({ severity: 'error', summary: 'שגיאה', detail: 'טעינת פרטי האירוע נכשלה' });
          return EMPTY;
        })
      )
      .subscribe((apiEvent: ApiEvent) => {
        const event: Event = {
          id: apiEvent.id,
          name: apiEvent.name,
          menuType: apiEvent.menu_type,
          guestCount: apiEvent.guest_count,
          date: apiEvent.date,
          eventTime: apiEvent.event_time,
          hebrewDate: apiEvent.hebrew_date,
          status: apiEvent.status,
          address: apiEvent.address,
          city: apiEvent.city,
          notes: apiEvent.notes,
          totalPrice: apiEvent.total_price,
          owners: apiEvent.owners?.map(o => ({ id: o.id, name: o.name, phone: o.phone, email: o.email, order: o.order })) || [],
          dishes: apiEvent.dishes?.map(d => ({
            dishId: d.dish_id,
            quantity: d.quantity,
            isDraft: d.is_draft,
            snapshotBasePrice: d.snapshot_base_price,
            snapshotClientPrice: d.snapshot_client_price,
            dishName: d.dish_name,
            dishKosherType: d.dish_kosher_type,
            categoryNameHebrew: d.category_name_hebrew
          })) || []
        };

        this.selectedDishIds = new Set(event.dishes?.map(d => d.dishId) || []);
        (this.currentEvent$ as BehaviorSubject<Event | null>).next(event);
      });
  }

  loadDishes(): void {
    this.isLoading = true;
    this.dishService.getDishes({ is_active: true, limit: 200 })
      .pipe(
        takeUntil(this.destroy$),
        map(response => response.items.map(this.mapApiDishToDish)),
        catchError(error => {
          console.error('Error loading dishes:', error);
          this.messageService.add({ severity: 'error', summary: 'שגיאה', detail: 'טעינת המנות נכשלה' });
          return EMPTY;
        }),
        finalize(() => this.isLoading = false)
      )
      .subscribe(dishes => {
        (this.dishes$ as BehaviorSubject<Dish[]>).next(dishes);
      });
  }

  loadProducts(): void {
    this.productService.getProducts({ limit: 200 })
      .pipe(
        takeUntil(this.destroy$),
        map(response => response.items.map(this.mapApiProductToProduct)),
        catchError(() => EMPTY)
      )
      .subscribe(products => {
        (this.products$ as BehaviorSubject<Product[]>).next(products);
      });
  }

  loadTools(): void {
    this.toolService.getAllTools()
      .pipe(
        takeUntil(this.destroy$),
        map(tools => tools.map(this.mapApiToolToTool)),
        catchError(() => EMPTY)
      )
      .subscribe(tools => {
        (this.tools$ as BehaviorSubject<Tool[]>).next(tools);
      });
  }

  loadLookupData(): void {
    this.lookupService.lookup$
      .pipe(takeUntil(this.destroy$))
      .subscribe(data => {
        if (data.units?.length) this.units = data.units;
        if (data.kosherTypes?.length) this.kosherTypes = data.kosherTypes;
        this.yieldUnits = data.dishYieldUnits || [];

        this.kosherOptions = [
          { label: 'כל סוגי הכשרות', value: 'הכל' },
          ...this.kosherTypes.map(type => ({ label: type, value: type }))
        ];

        this.filterChange$.next();
      });

    this.lookupService.initializeLookupData();
  }

  loadCategoriesGrouped(): void {
    this.menuService.getAllCategoriesGrouped()
      .pipe(takeUntil(this.destroy$), catchError(() => of([])))
      .subscribe(data => {
        this.allCategoriesGrouped = data;
      });
  }

  loadUnitConversions(): void {
    this.unitConversionService.getAll()
      .pipe(takeUntil(this.destroy$), catchError(() => of({ items: [], total: 0 })))
      .subscribe(response => {
        this.unitConversions = response.items;
      });
  }

  /**
   * המרת יחידות מקומית באמצעות מטמון ההמרות
   * @param quantity הכמות להמרה
   * @param fromUnit יחידה מקורית
   * @param toUnit יחידת יעד
   * @returns הכמות המומרת, או null אם אין המרה
   */
  convertUnits(quantity: number, fromUnit: string, toUnit: string): number | null {
    // אותה יחידה - ללא המרה
    if (fromUnit === toUnit) {
      return quantity;
    }

    // חיפוש המרה ישירה
    const directConversion = this.unitConversions.find(
      c => c.fromUnit === fromUnit && c.toUnit === toUnit
    );
    if (directConversion) {
      return quantity * directConversion.factor;
    }

    // חיפוש המרה דרך יחידת בסיס (גרם)
    const toBase = this.unitConversions.find(
      c => c.fromUnit === fromUnit && c.toUnit === 'גרם'
    );
    const fromBase = this.unitConversions.find(
      c => c.fromUnit === 'גרם' && c.toUnit === toUnit
    );
    if (toBase && fromBase) {
      return quantity * toBase.factor * fromBase.factor;
    }

    // המרה עם ק"ג כיחידת בסיס
    const toKg = this.unitConversions.find(
      c => c.fromUnit === fromUnit && c.toUnit === 'ק"\u05d2'
    );
    const fromKg = this.unitConversions.find(
      c => c.fromUnit === 'ק"\u05d2' && c.toUnit === toUnit
    );
    if (toKg && fromKg) {
      return quantity * toKg.factor * fromKg.factor;
    }

    // ניסיון המרה דרך גרם לק"ג (כף -> גרם -> ק"ג)
    const toGram = this.unitConversions.find(
      c => c.fromUnit === fromUnit && c.toUnit === 'גרם'
    );
    const gramToKg = this.unitConversions.find(
      c => c.fromUnit === 'גרם' && c.toUnit === 'ק"\u05d2'
    );
    if (toGram && gramToKg && toUnit === 'ק"\u05d2') {
      return quantity * toGram.factor * gramToKg.factor;
    }

    // אם אין המרה - מחזיר null
    return null;
  }

  // ========================================
  // Mapping Functions
  // ========================================

  mapApiDishToDish = (apiDish: ApiDish): Dish => {
    const ingredients = apiDish.ingredients?.map(ing => ({
      id: ing.id,
      productId: ing.product_id || ing.product?.id,
      productName: ing.name || ing.product?.name || '',
      quantity: ing.quantity ?? null,
      unit: ing.unit ?? null,
      isServingComponent: ing.is_serving_component || false,
      note: ing.note ?? null
    })) || [];

    return {
      id: apiDish.id,
      name: apiDish.name,
      description: apiDish.description,
      kosherType: apiDish.kosher_type,
      basePrice: apiDish.base_price,
      clientPrice: apiDish.client_price,
      servingSize: apiDish.serving_size ?? null,
      yieldQuantity: apiDish.yield_quantity ?? null,
      yieldUnit: apiDish.yield_unit ?? null,
      notes: apiDish.notes ?? null,
      servingDescription: apiDish.serving_description || '',
      waiterNotes: apiDish.waiter_notes || '',
      isActive: apiDish.is_active,
      createdDate: apiDish.created_at ? new Date(apiDish.created_at) : undefined,
      lastModified: apiDish.updated_at ? new Date(apiDish.updated_at) : undefined,
      ingredients,
      servingDishes: apiDish.serving_dishes?.map(sd => ({
        id: sd.id,
        toolId: sd.tool_id || sd.tool?.id,
        name: sd.name || sd.tool?.name || '',
        quantity: sd.quantity
      })) || [],
      menuMappings: apiDish.menu_mappings?.map(m => ({
        mappingId: m.mapping_id,
        categoryId: m.category_id,
        categoryNameHebrew: m.category_name_hebrew,
        menuType: m.menu_type,
        templateName: m.template_name,
        subMealName: m.sub_meal_name,
        isUpgrade: m.is_upgrade,
        extraCharge: m.extra_charge,
        displayOrder: m.display_order
      })) || [],
      // Warning: no products
      hasNoProducts: ingredients.length === 0 || !ingredients.some(i => i.productId)
    };
  };

  mapApiProductToProduct = (apiProduct: ApiProduct): Product => ({
    id: apiProduct.id,
    name: apiProduct.name,
    category: apiProduct.category,
    unit: apiProduct.unit || 'יחידות',
    inventoryStatus: apiProduct.inventory_status || 'במלאי',
    brand: apiProduct.brand,
    packageQuantity: apiProduct.package_quantity,
    estimatedPrice: apiProduct.estimated_price || 0,
    supplier: apiProduct.supplier,
    kosherType: apiProduct.kosher_type,
    quantityInStock: apiProduct.quantity_in_stock,
    minStockLevel: apiProduct.min_stock_level,
    pricePerUnit: apiProduct.price_per_unit,
    barcode: apiProduct.barcode,
    notes: apiProduct.notes,
    description: apiProduct.description
  });

  mapApiToolToTool = (apiTool: ApiTool): Tool => ({
    id: apiTool.id,
    name: apiTool.name,
    brand: apiTool.brand,
    category: apiTool.category,
    subCategory: apiTool.sub_category,
    inventoryStatus: apiTool.inventory_status,
    quantityInStock: apiTool.quantity_in_stock,
    minStockLevel: apiTool.min_stock_level,
    pricePerUnit: apiTool.price_per_unit,
    description: apiTool.description,
    color: apiTool.color,
    size: apiTool.size
  });

  private mapDishToCreatePayload(dish: Dish): DishCreate {
    return {
      name: dish.name.trim(),
      description: dish.description?.trim() || undefined,
      kosher_type: dish.kosherType as KosherType,
      base_price: dish.basePrice || undefined,
      client_price: dish.clientPrice || undefined,
      serving_size: dish.servingSize ?? null,
      yield_quantity: dish.yieldQuantity ?? null,
      yield_unit: dish.yieldUnit || null,
      notes: dish.notes?.trim() || null,
      serving_description: dish.servingDescription?.trim() || undefined,
      waiter_notes: dish.waiterNotes?.trim() || undefined,
      is_active: dish.isActive
    };
  }

  // ========================================
  // Filtering
  // ========================================

  setupFilteredDishes(): void {
    this.filteredDishes$ = combineLatest([
      this.dishes$,
      this.currentEvent$,
      this.filterChange$
    ]).pipe(
      map(([dishes, event]) => {
        return dishes.filter(dish => {
          const searchLower = this.searchQuery.toLowerCase();
          const matchSearch =
            dish.name.toLowerCase().includes(searchLower) ||
            (dish.description?.toLowerCase().includes(searchLower) || false);

          const matchKosher = this.filterKosher === 'הכל' || dish.kosherType === this.filterKosher;

          // הוספת לוגיקה של התאמת כשרות לאירוע
          let matchEventKosher = true;
          if (event && this.isEventMode) {
            const eventMenuType = event.menuType?.toString().toLowerCase();
            if (eventMenuType?.includes('חלבי') || eventMenuType?.includes('dairy')) {
              // אירוע חלבי - יוצגו מנות פרווה ומנות חלביות
              matchEventKosher = dish.kosherType === 'פרווה' || dish.kosherType === 'חלבי';
            } else if (eventMenuType?.includes('בשרי') || eventMenuType?.includes('meat')) {
              // אירוע בשרי - יוצגו מנות בשרי ומנות פרווה
              matchEventKosher = dish.kosherType === 'בשרי' || dish.kosherType === 'פרווה';
            } else if (eventMenuType?.includes('פרווה') || eventMenuType?.includes('parve')) {
              // אירוע פרווה - יוצגו רק מנות פרווה
              matchEventKosher = dish.kosherType === 'פרווה';
            }
          }

          return matchSearch && matchKosher && matchEventKosher;
        });
      })
    );
  }

  onSearchChange(): void { this.filterChange$.next(); }
  onFilterChange(): void { this.filterChange$.next(); }

  clearAllFilters(): void {
    this.searchQuery = '';
    this.filterKosher = 'הכל';
    this.onFilterChange();
  }

  // ========================================
  // Event Mode - Dish Selection
  // ========================================

  isDishSelected(dishId: number): boolean {
    return this.selectedDishIds.has(dishId);
  }

  /** מנה נשמרת מיד לאירוע כשעושים V בצ'קבוקס */
  toggleDishSelection(dish: Dish): void {
    if (!this.eventId || !this.currentEvent) return;

    const isCurrentlySelected = this.selectedDishIds.has(dish.id);

    if (isCurrentlySelected) {
      this.eventService.removeDishFromEvent(this.eventId, dish.id)
        .pipe(takeUntil(this.destroy$), catchError(() => EMPTY))
        .subscribe(() => {
          this.selectedDishIds.delete(dish.id);
          this.messageService.add({ severity: 'info', summary: 'מנה הוסרה', detail: `${dish.name} הוסרה מהאירוע` });
        });
    } else {
      const quantity = this.calculateDishQuantity(dish);
      const dishData: EventDishCreate = { dish_id: dish.id, quantity };

      this.eventService.addDishToEvent(this.eventId, dishData)
        .pipe(takeUntil(this.destroy$), catchError(() => EMPTY))
        .subscribe(() => {
          this.selectedDishIds.add(dish.id);
          this.messageService.add({ severity: 'success', summary: 'מנה נוספה', detail: `${dish.name} נוספה לאירוע (${quantity} מנות)` });
        });
    }
  }

  calculateDishQuantity(dish: Dish): number {
    if (!this.currentEvent?.guestCount) return 1;
    const servingSize = dish.servingSize || 1;
    return Math.ceil(this.currentEvent.guestCount / servingSize);
  }

  goBackToEvents(openEventPopup: boolean = false): void {
    if (openEventPopup && this.eventId) {
      this.router.navigate(['/events'], { queryParams: { openEvent: this.eventId } });
    } else {
      this.router.navigate(['/events']);
    }
  }

  finishSelection(): void {
    this.goBackToEvents(true);
  }

  // ========================================
  // CRUD Operations
  // ========================================

  setViewMode(mode: 'grid' | 'table'): void {
    this.viewMode = mode;
  }

  handleCreateDish(): void {
    const defaultKosherType = this.kosherTypes[0] || 'פרווה';
    const defaultUnit = this.units[0] || 'יחידות';

    this.editingDish = {
      id: 0,
      name: '',
      description: '',
      kosherType: defaultKosherType as KosherType,
      basePrice: 0,
      clientPrice: 0,
      servingSize: 1,
      servingDescription: '',
      waiterNotes: '',
      ingredients: [],
      servingDishes: [],
      isActive: true,
      hasNoProducts: true,
      menuMappings: []
    };

    this.originalIngredients = [];
    this.originalServingDishes = [];
    this.originalMappings = [];
    this.dishServingSets = [];
    this.dishCalculationRules = [];
    this.selectedCategoryIds = new Set();
    this.categoryUpgradeSettings = new Map();
    this.isDialogOpen = true;
  }

  handleEditDish(dish: Dish): void {
    this.editingDish = {
      ...dish,
      ingredients: dish.ingredients?.map(ing => ({ ...ing })) || [],
      servingDishes: dish.servingDishes?.map(sd => ({ ...sd })) || []
    };
    this.originalIngredients = dish.ingredients?.map(ing => ({ ...ing })) || [];
    this.originalServingDishes = dish.servingDishes?.map(sd => ({ ...sd })) || [];
    this.originalMappings = dish.menuMappings?.map(m => ({ ...m })) || [];
    this.selectedCategoryIds = new Set(this.originalMappings.map(m => m.categoryId));
    forkJoin({
      sets: this.dishService.getServingSets(dish.id),
      rules: this.dishService.getCalculationRules(dish.id)
    }).pipe(takeUntil(this.destroy$)).subscribe(({ sets, rules }) => {
      this.dishServingSets = sets;
      this.dishCalculationRules = rules.map(rule => ({ ...rule, paramsJson: JSON.stringify(rule.params || {}, null, 2) }));
    });
    
    // Initialize upgrade settings from existing mappings
    this.categoryUpgradeSettings = new Map();
    for (const mapping of this.originalMappings) {
      this.categoryUpgradeSettings.set(mapping.categoryId, {
        isUpgrade: mapping.isUpgrade || false,
        extraCharge: mapping.extraCharge || null
      });
    }
    
    this.isDialogOpen = true;
  }

  addDishServingSet(type: 'serving' | 'packaging'): void {
    this.dishServingSets.push({ name: '', set_type: type, dishware_type: type === 'serving' ? 'disposable' : undefined, serving_mode: type === 'serving' ? 'central' : undefined, is_default: this.dishServingSets.every(s => s.set_type !== type), items: [] });
  }

  addDishServingSetItem(set: DishServingSet): void {
    set.items.push({ quantity: 1, quantity_basis: set.set_type === 'packaging' ? 'tray' : (set.serving_mode === 'central' ? 'serving_group' : 'guest') });
  }

  saveDishServingSet(set: DishServingSet): void {
    if (!this.editingDish?.id) return;
    if (set.serving_mode && (!set.items.length || set.items.some(item => !item.tool_id))) {
      this.messageService.add({ severity: 'warn', summary: 'יש לקשר כלי מהמלאי בכל שורה' });
      return;
    }
    if (!set.name.trim()) set.name = `${set.dishware_type === 'real' ? 'אמיתי' : 'חד פעמי'} — ${set.serving_mode === 'personal' ? 'הגשה אישית' : 'הגשה מרכזית'}`;
    this.dishService.saveServingSet(this.editingDish.id, set).pipe(takeUntil(this.destroy$)).subscribe({
      next: saved => {
        if (saved.is_default) this.dishServingSets.filter(row => row !== set && row.set_type === saved.set_type && row.dishware_type === saved.dishware_type).forEach(row => row.is_default = false);
        this.dishServingSets[this.dishServingSets.indexOf(set)] = saved;
        this.messageService.add({ severity: 'success', summary: 'הכלים הנדרשים להגשת המנה נשמרו' });
      },
      error: error => this.messageService.add({ severity: 'error', summary: 'ההגדרה לא נשמרה', detail: typeof error.error?.detail === 'string' ? error.error.detail : 'יש לבדוק את השדות ולנסות שוב' })
    });
  }

  deleteDishServingSet(set: DishServingSet): void {
    const index = this.dishServingSets.indexOf(set);
    if (!set.id) { this.dishServingSets.splice(index, 1); return; }
    this.dishService.deleteServingSet(this.editingDish!.id, set.id).pipe(takeUntil(this.destroy$)).subscribe(() => this.dishServingSets.splice(index, 1));
  }

  addWorkbookRule(): void {
    const preset = this.workbookPresets.find(item => item.key === this.workbookPresetKey);
    if (!preset) return;
    this.dishCalculationRules.push({rule_type: 'workbook', name: preset.name, is_active: true,
      params: {formula_key: preset.key, factor: preset.factor, divisor: preset.divisor,
        unit: preset.unit || '', audience_fraction: preset.audience_fraction, round_up: false,
        source_sheet: preset.sheet, source_cell: preset.cell}});
  }

  addDishCalculationRule(): void {
    this.dishCalculationRules.push({ rule_type: 'custom_product', is_active: true, params: {}, paramsJson: '{}' });
  }

  saveDishCalculationRule(rule: DishCalculationRule & { paramsJson?: string }): void {
    if (!this.editingDish?.id) return;
    try { if (rule.rule_type !== 'workbook') rule.params = JSON.parse(rule.paramsJson || '{}'); }
    catch { this.messageService.add({ severity: 'error', summary: 'שגיאה', detail: 'JSON לא תקין בפרמטרי החוק' }); return; }
    this.dishService.saveCalculationRule(this.editingDish.id, rule).pipe(takeUntil(this.destroy$)).subscribe({next: saved => {
      const index = this.dishCalculationRules.indexOf(rule);
      this.dishCalculationRules[index] = { ...saved, paramsJson: JSON.stringify(saved.params || {}, null, 2) };
      this.messageService.add({severity: 'success', summary: 'החישוב נשמר'});
    }, error: err => this.messageService.add({severity: 'error', summary: 'החישוב לא נשמר', detail: typeof err?.error?.detail === 'string' ? err.error.detail : 'בדקו שהכמות והמחלק תקינים ונסו שוב'})});
  }

  deleteDishCalculationRule(rule: DishCalculationRule): void {
    const index = this.dishCalculationRules.indexOf(rule);
    if (!rule.id) { this.dishCalculationRules.splice(index, 1); return; }
    this.dishService.deleteCalculationRule(this.editingDish!.id, rule.id).pipe(takeUntil(this.destroy$)).subscribe(() => this.dishCalculationRules.splice(index, 1));
  }

  handleSaveDish(): void {
    if (!this.editingDish) return;

    if (!this.editingDish.name.trim()) {
      this.messageService.add({ severity: 'error', summary: 'שגיאה', detail: 'יש להזין שם מנה' });
      return;
    }

    // Warning for empty products (not blocking)
    const hasProducts = this.editingDish.ingredients.some(i => i.productId);
    if (!hasProducts && this.editingDish.ingredients.length === 0) {
      this.messageService.add({ severity: 'warn', summary: 'אזהרה', detail: '⚠️ מנה ללא מוצרים - ניתן להוסיף מוצרים מאוחר יותר' });
    }

    const isUpdate = !!this.editingDish.id;
    this.recalculateBasePrice();
    const payload = this.mapDishToCreatePayload(this.editingDish);

    const request$ = isUpdate
      ? this.dishService.updateDish(this.editingDish.id, payload as DishUpdate).pipe(map(() => this.editingDish!.id))
      : this.dishService.createDish(payload as DishCreate).pipe(map(res => res.id));

    request$
      .pipe(
        switchMap(dishId => this.syncDishIngredients(dishId, this.editingDish!.ingredients).pipe(
          switchMap(() => this.syncServingDishes(dishId, this.editingDish!.servingDishes || [])),
          switchMap(() => this.syncMenuMappings(dishId)),
          map(() => dishId)
        )),
        takeUntil(this.destroy$),
        catchError(error => {
          console.error('Error saving dish:', error);
          this.messageService.add({ severity: 'error', summary: 'שגיאה', detail: 'שמירת המנה נכשלה' });
          return EMPTY;
        })
      )
      .subscribe(() => {
        this.messageService.add({ severity: 'success', summary: 'הצלחה', detail: isUpdate ? 'המנה עודכנה בהצלחה' : 'המנה נוצרה בהצלחה' });
        this.isDialogOpen = false;
        this.editingDish = null;
        this.originalIngredients = [];
        this.originalServingDishes = [];
        this.originalMappings = [];
        this.selectedCategoryIds = new Set();
        this.loadDishes();
      });
  }

  confirmDelete(id: number): void {
    this.confirmationService.confirm({
      message: 'האם למחוק מנה זו? פעולה זו לא ניתנת לביטול.',
      header: 'אישור מחיקה',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'מחק',
      rejectLabel: 'ביטול',
      accept: () => this.handleDeleteDish(id)
    });
  }

  handleDeleteDish(id: number): void {
    this.dishService.deleteDish(id)
      .pipe(takeUntil(this.destroy$), catchError(() => EMPTY))
      .subscribe(() => {
        this.messageService.add({ severity: 'success', summary: 'הצלחה', detail: 'המנה נמחקה' });
        this.loadDishes();
      });
  }

  // ========================================
  // Ingredient Management
  // ========================================

  handleAddIngredient(): void {
    if (!this.editingDish) return;
    const defaultUnit = this.units[0] || 'יחידות';
    this.editingDish.ingredients.unshift({
      id: undefined,
      productId: undefined,
      productName: '',
      quantity: 0,
      unit: defaultUnit,
      isServingComponent: false
    });
  }

  handleIngredientProductChange(index: number, productId: number): void {
    if (!this.editingDish) return;
    const product = this.products.find(p => p.id === productId);
    this.editingDish.ingredients[index].productId = productId;
    this.editingDish.ingredients[index].productName = product?.name || '';
    if (product?.unit) {
      this.editingDish.ingredients[index].unit = product.unit;
    }
    this.recalculateBasePrice();
  }

  handleUpdateIngredient(index: number, field: keyof DishIngredient, value: any): void {
    if (!this.editingDish) return;
    this.editingDish.ingredients[index] = { ...this.editingDish.ingredients[index], [field]: value };
    if (field === 'quantity') this.recalculateBasePrice();
  }

  handleRemoveIngredient(index: number): void {
    if (!this.editingDish) return;
    this.editingDish.ingredients.splice(index, 1);
    this.recalculateBasePrice();
  }

  isProductAlreadySelected(productId: number, currentIndex: number): boolean {
    if (!this.editingDish) return false;
    return this.editingDish.ingredients.some((ing, idx) => idx !== currentIndex && ing.productId === productId);
  }

  /** חישוב מחיר עלות פנימי (base_price) מסכום מרכיבים עם המרת יחידות */
  calculateBasePrice(): number {
    if (!this.editingDish?.ingredients?.length) return 0;
    let total = 0;
    for (const ingredient of this.editingDish.ingredients) {
      if (ingredient.quantity == null || !ingredient.unit) continue;  // amount missing in recipe
      const product = this.products.find(p => p.id === ingredient.productId);
      if (product?.estimatedPrice) {
        const packageQty = product.packageQuantity || 1;
        // מחיר ליחידת מוצר (מחיר אריזה / כמות באריזה)
        const pricePerProductUnit = product.estimatedPrice / packageQty;
        
        // המרת כמות מרכיב ליחידת מוצר
        const convertedQuantity = this.convertUnits(
          ingredient.quantity,
          ingredient.unit,
          product.unit || 'גרם'
        );
        
        if (convertedQuantity !== null) {
          total += pricePerProductUnit * convertedQuantity;
        } else {
          // אם אין המרה, משתמש בכמות ישירה (התנהגות קודמת)
          total += pricePerProductUnit * ingredient.quantity;
        }
      }
    }
    return Math.round(total * 100) / 100;
  }

  recalculateBasePrice(): void {
    if (this.editingDish) {
      this.editingDish.basePrice = this.calculateBasePrice();
    }
  }

  getIngredientPriceInfo(ingredient: DishIngredient): { pricePerUnit: number; totalPrice: number; converted: boolean } | null {
    if (ingredient.quantity == null || !ingredient.unit) return null;
    const product = this.products.find(p => p.id === ingredient.productId);
    if (!product?.estimatedPrice) return null;
    const packageQty = product.packageQuantity || 1;
    const pricePerProductUnit = product.estimatedPrice / packageQty;
    
    // המרת כמות מרכיב ליחידת מוצר
    const convertedQuantity = this.convertUnits(
      ingredient.quantity,
      ingredient.unit,
      product.unit || 'גרם'
    );
    
    const wasConverted = convertedQuantity !== null && ingredient.unit !== product.unit;
    const quantityToUse = convertedQuantity !== null ? convertedQuantity : ingredient.quantity;
    const totalPrice = pricePerProductUnit * quantityToUse;
    
    return {
      pricePerUnit: Math.round(pricePerProductUnit * 100) / 100,
      totalPrice: Math.round(totalPrice * 100) / 100,
      converted: wasConverted
    };
  }

  isToolAlreadySelected(toolId: number, currentIndex: number): boolean {
    if (!this.editingDish) return false;
    const items = this.editingDish.servingDishes || [];
    return items.some((item, idx) => idx !== currentIndex && (item as any).toolId === toolId);
  }

  // ========================================
  // Serving Dishes Management
  // ========================================

  handleAddServingDish(): void {
    if (!this.editingDish) return;
    if (!this.editingDish.servingDishes) this.editingDish.servingDishes = [];
    this.editingDish.servingDishes.unshift({ name: '', toolId: undefined, quantity: 1 });
  }

  handleServingDishToolChange(index: number, toolId: number): void {
    if (!this.editingDish?.servingDishes) return;
    const tool = this.tools.find(t => t.id === toolId);
    this.editingDish.servingDishes[index].toolId = toolId;
    this.editingDish.servingDishes[index].name = tool?.name || '';
  }

  handleUpdateServingDish(index: number, field: string, value: any): void {
    if (!this.editingDish?.servingDishes) return;
    this.editingDish.servingDishes[index] = { ...this.editingDish.servingDishes[index], [field]: value };
  }

  handleRemoveServingDish(index: number): void {
    if (!this.editingDish?.servingDishes) return;
    this.editingDish.servingDishes.splice(index, 1);
  }

  // ========================================
  // Sync Operations (ingredients/equipment/serving)
  // ========================================

  private resolveProductId(ingredient: DishIngredient): number | null {
    if (ingredient.productId) return ingredient.productId;
    const matched = this.products.find(p => p.name === ingredient.productName);
    return matched?.id ?? null;
  }

  private isIngredientChanged(original: DishIngredient, current: DishIngredient): boolean {
    return original.quantity !== current.quantity || original.unit !== current.unit || original.isServingComponent !== current.isServingComponent;
  }

  private syncDishIngredients(dishId: number, ingredients: DishIngredient[]): Observable<void> {
    const ops: Observable<any>[] = [];
    const originalMap = new Map<number, DishIngredient>();
    this.originalIngredients.filter(ing => !!ing.id).forEach(ing => originalMap.set(ing.id as number, ing));
    const processedIds = new Set<number>();

    ingredients.forEach(ing => {
      const productId = this.resolveProductId(ing);
      const ingredientName = ing.productName || '';
      if (!productId && !ingredientName.trim()) return;

      if (ing.id && originalMap.has(ing.id)) {
        const original = originalMap.get(ing.id)!;
        processedIds.add(ing.id);
        const originalProductId = this.resolveProductId(original);
        const productChanged = productId !== originalProductId;

        if (productChanged) {
          ops.push(this.wrapOp(this.dishService.removeIngredient(dishId, ing.id)));
          ops.push(this.wrapOp(this.dishService.addIngredient(dishId, {
            product_id: productId || undefined,
            name: ingredientName || undefined,
            quantity: ing.quantity,
            unit: ing.unit,
            is_serving_component: ing.isServingComponent || false,
            note: ing.note ?? null
          })));
        } else if (this.isIngredientChanged(original, ing)) {
          ops.push(this.wrapOp(this.dishService.updateIngredient(dishId, ing.id, {
            product_id: productId || undefined,
            name: ingredientName || undefined,
            quantity: ing.quantity,
            unit: ing.unit,
            is_serving_component: ing.isServingComponent || false,
            note: ing.note ?? null
          })));
        }
      } else {
        ops.push(this.wrapOp(this.dishService.addIngredient(dishId, {
          product_id: productId || undefined,
          name: ingredientName || undefined,
          quantity: ing.quantity,
          unit: ing.unit,
          is_serving_component: ing.isServingComponent || false,
          note: ing.note ?? null
        })));
      }
    });

    this.originalIngredients
      .filter(ing => ing.id && !processedIds.has(ing.id))
      .forEach(ing => ops.push(this.wrapOp(this.dishService.removeIngredient(dishId, ing.id as number))));

    return ops.length === 0 ? of(void 0) : forkJoin(ops).pipe(map(() => void 0));
  }

  private syncServingDishes(dishId: number, servingDishes: any[]): Observable<void> {
    const ops: Observable<any>[] = [];
    const originalMap = new Map<number, any>();
    this.originalServingDishes.filter(sd => !!sd.id).forEach(sd => originalMap.set(sd.id, sd));
    const processedIds = new Set<number>();

    servingDishes.forEach(sd => {
      if (!sd.name?.trim() && !sd.toolId) return;

      if (sd.id && originalMap.has(sd.id)) {
        const original = originalMap.get(sd.id)!;
        processedIds.add(sd.id);
        if (sd.toolId !== original.toolId) {
          ops.push(this.wrapOp(this.dishService.removeServingDish(dishId, sd.id)));
          ops.push(this.wrapOp(this.dishService.addServingDish(dishId, { tool_id: sd.toolId || undefined, name: sd.name || undefined, quantity: sd.quantity })));
        } else if (original.name !== sd.name || original.quantity !== sd.quantity) {
          ops.push(this.wrapOp(this.dishService.updateServingDish(dishId, sd.id, { name: sd.name, quantity: sd.quantity, tool_id: sd.toolId || undefined })));
        }
      } else {
        ops.push(this.wrapOp(this.dishService.addServingDish(dishId, { tool_id: sd.toolId || undefined, name: sd.name || undefined, quantity: sd.quantity })));
      }
    });

    this.originalServingDishes
      .filter(sd => sd.id && !processedIds.has(sd.id))
      .forEach(sd => ops.push(this.wrapOp(this.dishService.removeServingDish(dishId, sd.id))));

    return ops.length === 0 ? of(void 0) : forkJoin(ops).pipe(map(() => void 0));
  }

  // ========================================
  // Menu Mappings Sync
  // ========================================

  isCategorySelected(categoryId: number): boolean {
    return this.selectedCategoryIds.has(categoryId);
  }

  toggleCategoryMapping(categoryId: number): void {
    if (this.selectedCategoryIds.has(categoryId)) {
      this.selectedCategoryIds.delete(categoryId);
      // Keep upgrade settings in case user re-selects the category
    } else {
      this.selectedCategoryIds.add(categoryId);
      // Initialize default upgrade settings if not already set
      if (!this.categoryUpgradeSettings.has(categoryId)) {
        this.categoryUpgradeSettings.set(categoryId, { isUpgrade: false, extraCharge: null });
      }
    }
  }

  // Get upgrade setting for a category
  getCategoryIsUpgrade(categoryId: number): boolean {
    return this.categoryUpgradeSettings.get(categoryId)?.isUpgrade || false;
  }

  // Set upgrade setting for a category
  setCategoryIsUpgrade(categoryId: number, isUpgrade: boolean): void {
    const current = this.categoryUpgradeSettings.get(categoryId) || { isUpgrade: false, extraCharge: null };
    this.categoryUpgradeSettings.set(categoryId, { ...current, isUpgrade });
    // Clear extra charge if not an upgrade
    if (!isUpgrade) {
      this.categoryUpgradeSettings.set(categoryId, { isUpgrade: false, extraCharge: null });
    }
  }

  // Get extra charge for a category
  getCategoryExtraCharge(categoryId: number): number | null {
    return this.categoryUpgradeSettings.get(categoryId)?.extraCharge || null;
  }

  // Set extra charge for a category
  setCategoryExtraCharge(categoryId: number, extraCharge: number | null): void {
    const current = this.categoryUpgradeSettings.get(categoryId) || { isUpgrade: true, extraCharge: null };
    this.categoryUpgradeSettings.set(categoryId, { ...current, extraCharge });
  }

  getMenuMappingsCount(): number {
    return this.selectedCategoryIds.size;
  }

  getUniqueMenuTypes(): string[] {
    if (!this.editingDish?.menuMappings) return [];
    const types = new Set(this.editingDish.menuMappings
      .filter(m => this.selectedCategoryIds.has(m.categoryId))
      .map(m => m.menuType));
    // Also add menu types from newly selected categories
    for (const group of this.allCategoriesGrouped) {
      for (const cat of group.categories) {
        if (this.selectedCategoryIds.has(cat.id)) {
          types.add(group.menu_type);
        }
      }
    }
    return [...types];
  }

  private syncMenuMappings(dishId: number): Observable<void> {
    const ops: Observable<any>[] = [];

    // Mappings to remove: were in original but no longer selected
    for (const orig of this.originalMappings) {
      if (!this.selectedCategoryIds.has(orig.categoryId)) {
        ops.push(this.wrapOp(this.menuService.removeDishFromCategory(orig.mappingId)));
      }
    }

    // Build a map of original mappings by category id for quick lookup
    const originalMappingByCategory = new Map(this.originalMappings.map(m => [m.categoryId, m]));

    for (const categoryId of this.selectedCategoryIds) {
      const upgradeSettings = this.categoryUpgradeSettings.get(categoryId) || { isUpgrade: false, extraCharge: null };
      const originalMapping = originalMappingByCategory.get(categoryId);
      
      if (!originalMapping) {
        // New mapping - add it with upgrade settings
        const mapping: DishMenuMappingCreate = {
          dish_id: dishId,
          category_id: categoryId,
          is_upgrade: upgradeSettings.isUpgrade,
          extra_charge: upgradeSettings.isUpgrade ? (upgradeSettings.extraCharge || 0) : undefined,
          display_order: 0
        };
        ops.push(this.wrapOp(this.menuService.addDishToCategory(mapping)));
      } else {
        // Existing mapping - check if upgrade settings changed
        const hasChanged = originalMapping.isUpgrade !== upgradeSettings.isUpgrade ||
                          originalMapping.extraCharge !== (upgradeSettings.isUpgrade ? upgradeSettings.extraCharge : null);
        if (hasChanged) {
          // Update the mapping with new upgrade settings
          ops.push(this.wrapOp(this.menuService.updateDishMapping(originalMapping.mappingId, {
            is_upgrade: upgradeSettings.isUpgrade,
            extra_charge: upgradeSettings.isUpgrade ? (upgradeSettings.extraCharge || 0) : undefined
          })));
        }
      }
    }

    return ops.length === 0 ? of(void 0) : forkJoin(ops).pipe(map(() => void 0));
  }

  private wrapOp<T>(obs: Observable<T>): Observable<null> {
    return obs.pipe(map(() => null), catchError(err => err?.status === 404 ? of(null) : (() => { throw err; })()));
  }

  // ========================================
  // Helper Methods
  // ========================================

  getKosherClass(type: string): string {
    switch (type) {
      case 'חלבי': return 'kosher-badge-dairy';
      case 'בשרי': return 'kosher-badge-meat';
      case 'פרווה': return 'kosher-badge-parve';
      default: return '';
    }
  }

  getKosherIcon(type: string): string {
    switch (type) {
      case 'חלבי': return 'pi pi-heart';
      case 'בשרי': return 'pi pi-star';
      case 'פרווה': return 'pi pi-circle';
      default: return '';
    }
  }

  getMenuTypeSeverity(type: string): 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast' {
    switch (type) {
      case 'שבת': return 'info';
      case 'תפריט בשרי': return 'danger';
      case 'תפריט חלבי': return 'success';
      case 'תפריט מתוק': return 'warn';
      default: return type.includes('מגשי') ? 'secondary' : 'info';
    }
  }

  /** Get distinct menu type names for a dish */
  getDishMenuTypes(dish: Dish): string[] {
    if (!dish.menuMappings?.length) return [];
    return [...new Set(dish.menuMappings.map(m => m.menuType))];
  }

  /** Count how many categories are selected in a template group */
  getCategoryCountForTemplate(group: any): number {
    return group.categories.filter((cat: any) => this.selectedCategoryIds.has(cat.id)).length;
  }

  trackByIndex(index: number): number {
    return index;
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
