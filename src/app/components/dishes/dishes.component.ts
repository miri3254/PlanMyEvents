import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Observable, Subject, combineLatest, EMPTY, BehaviorSubject } from 'rxjs';
import { map, takeUntil, catchError, tap } from 'rxjs/operators';
import { ApiDishService } from '../../services/api-dish.service';
import { ApiProductService } from '../../services/api-product.service';
import { ApiLookupService } from '../../services/api-lookup.service';
import { Event } from '../../core/models';
import { ApiDish, ApiProduct, DishCreate, DishUpdate } from '../../core/models/api.models';
import { Dish, DishIngredient, DishEquipment, Product } from '../../core/models';
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
    ScrollPanelModule
  ],
  templateUrl: './dishes.component.html',
  styleUrls: ['./dishes.component.scss'],
  providers: [ConfirmationService, MessageService]
})
export class DishesComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  dishes$!: Observable<Dish[]>;
  products$!: Observable<Product[]>;
  currentEvent$!: Observable<Event | null>;
  filteredDishes$!: Observable<Dish[]>;

  viewMode: 'table' | 'grid' = 'table';
  searchQuery: string = '';
  filterCategory: string = 'הכל';
  filterKosher: string = 'הכל';
  editingDish: Dish | null = null;
  isDialogOpen: boolean = false;
  showShoppingList: boolean = false;

  currentEvent: Event | null = null;
  isEventMode: boolean = false;
  products: Product[] = [];
  shoppingList: any[] = [];

  viewOptions = [
    { icon: 'pi pi-th-large', value: 'grid' },
    { icon: 'pi pi-list', value: 'table' }
  ];

  kosherOptions = [{ label: 'כל סוגי הכשרות', value: 'הכל' }];

  categories: string[] = [];
  kosherTypes: string[] = [];
  units: string[] = [];

  constructor(
    private dishService: ApiDishService,
    private productService: ApiProductService,
    private lookupService: ApiLookupService,
    private confirmationService: ConfirmationService,
    private messageService: MessageService
  ) {
    this.dishes$ = new BehaviorSubject<Dish[]>([]);
    this.products$ = new BehaviorSubject<Product[]>([]);
    this.currentEvent$ = new BehaviorSubject<Event | null>(null);
  }

  ngOnInit(): void {
    this.loadDishes();
    this.loadProducts();
    this.loadLookupData();

    this.products$
      .pipe(takeUntil(this.destroy$))
      .subscribe(products => {
        this.products = products;
      });

    this.currentEvent$
      .pipe(takeUntil(this.destroy$))
      .subscribe(event => {
        this.currentEvent = event;
        this.isEventMode = !!event;
      });

    this.setupFilteredDishes();
  }

  loadDishes(): void {
    this.dishService.getDishes({ is_active: true })
      .pipe(
        takeUntil(this.destroy$),
        map(response => response.items.map(this.mapApiDishToDish)),
        catchError(error => {
          console.error('Error loading dishes:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'שגיאה',
            detail: 'טעינת המנות נכשלה'
          });
          return EMPTY;
        })
      )
      .subscribe(dishes => {
        (this.dishes$ as BehaviorSubject<Dish[]>).next(dishes);
      });
  }

  loadProducts(): void {
    this.productService.getProducts()
      .pipe(
        takeUntil(this.destroy$),
        map(response => response.items.map(this.mapApiProductToProduct)),
        catchError(error => {
          console.error('Error loading products:', error);
          return EMPTY;
        })
      )
      .subscribe(products => {
        (this.products$ as BehaviorSubject<Product[]>).next(products);
      });
  }

  loadLookupData(): void {
    this.lookupService.lookup$
      .pipe(takeUntil(this.destroy$))
      .subscribe(data => {
        this.categories = ['עיקרית', 'ראשונה', 'תוספת', 'קינוח', 'משקה', 'חטיף'];
        this.kosherTypes = data.kosherTypes || ['חלבי', 'בשרי', 'פרווה'];
        this.units = ['גרם', 'ליטר', 'יחידות', 'כפות', 'כוסות', 'מ"ל', 'ק"ג'];
        this.kosherOptions = [
          { label: 'כל סוגי הכשרות', value: 'הכל' },
          ...this.kosherTypes.map(type => ({ label: type, value: type }))
        ];

        if (
          this.filterCategory !== 'הכל' &&
          !this.categories.includes(this.filterCategory)
        ) {
          this.filterCategory = 'הכל';
        }

        if (
          this.filterKosher !== 'הכל' &&
          !this.kosherTypes.includes(this.filterKosher)
        ) {
          this.filterKosher = 'הכל';
        }

        if (this.editingDish) {
          if (!this.categories.includes(this.editingDish.category)) {
            this.editingDish.category = this.categories[0] || this.editingDish.category;
          }
          if (!this.kosherTypes.includes(this.editingDish.kosherType)) {
            this.editingDish.kosherType = this.kosherTypes[0] || this.editingDish.kosherType;
          }
          if (this.editingDish.ingredients?.length) {
            this.editingDish.ingredients = this.editingDish.ingredients.map(ingredient => {
              const unit = this.units.includes(ingredient.unit)
                ? ingredient.unit
                : this.units[0] || ingredient.unit;
              return { ...ingredient, unit };
            });
          }
        }

        this.onFilterChange();
      });

    // Initialize lookup data
    this.lookupService.initializeLookupData();
  }

  // Mapping functions
  mapApiDishToDish = (apiDish: ApiDish): Dish => {
    return {
      id: apiDish.id,
      name: apiDish.name,
      description: apiDish.description,
      estimatedPrice: apiDish.estimated_price,
      category: apiDish.category,
      kosherType: apiDish.kosher_type,
      servingSize: apiDish.serving_size,
      ingredients: apiDish.ingredients?.map(ing => ({
        productName: ing.product?.name || '',
        quantity: ing.quantity,
        unit: ing.unit
      })) || [],
      equipment: apiDish.equipment?.map(eq => ({
        name: eq.tool?.name || '',
        required: true
      })) || [],
      imageUrl: undefined,
      isActive: apiDish.is_active,
      createdDate: new Date(apiDish.created_at || new Date().toISOString()),
      lastModified: new Date(apiDish.updated_at || new Date().toISOString()),
      servingDishes: apiDish.serving_dishes?.map(sd => ({
        name: sd.tool?.name || '',
        quantity: sd.quantity,
        category: sd.tool?.category || ''
      })) || []
    };
  };

  mapApiProductToProduct = (apiProduct: ApiProduct): Product => {
    return {
      id: apiProduct.id,
      name: apiProduct.name,
      inventoryStatus: apiProduct.inventory_status,
      brand: apiProduct.brand || '',
      packageQuantity: apiProduct.package_quantity || 0,
      estimatedPrice: apiProduct.estimated_price,
      category: apiProduct.category,
      supplier: apiProduct.supplier || ''
    };
  };

  private mapDishToCreatePayload(dish: Dish): DishCreate {
    return {
      name: dish.name.trim(),
      description: dish.description?.trim(),
      category: dish.category,
      kosher_type: dish.kosherType,
      serving_size: dish.servingSize,
      estimated_price: dish.estimatedPrice,
      is_active: dish.isActive
    };
  }

  private mapDishToUpdatePayload(dish: Dish): DishUpdate {
    return this.mapDishToCreatePayload(dish);
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  setupFilteredDishes(): void {
    this.filteredDishes$ = combineLatest([
      this.dishes$,
      this.currentEvent$
    ]).pipe(
      map(([dishes, event]) => {
        return dishes.filter(dish => {
          const matchSearch = 
            dish.name.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
            (dish.description?.toLowerCase().includes(this.searchQuery.toLowerCase()) || false);
          
          const matchCategory = this.filterCategory === 'הכל' || dish.category === this.filterCategory;
          const matchKosher = this.filterKosher === 'הכל' || dish.kosherType === this.filterKosher;

          // Event mode filtering
          if (event && event.foodType !== 'כל הסוגים') {
            const eventKosher = dish.kosherType === event.foodType || dish.kosherType === 'פרווה';
            return matchSearch && matchCategory && matchKosher && eventKosher;
          }

          return matchSearch && matchCategory && matchKosher;
        });
      })
    );
  }

  onSearchChange(): void {
    this.setupFilteredDishes();
  }

  onFilterChange(): void {
    this.setupFilteredDishes();
  }

  setCategoryFilter(category: string): void {
    this.filterCategory = category;
    this.onFilterChange();
  }

  clearAllFilters(): void {
    this.searchQuery = '';
    this.filterCategory = 'הכל';
    this.filterKosher = 'הכל';
    this.onFilterChange();
  }

  setViewMode(mode: 'grid' | 'table'): void {
    this.viewMode = mode;
  }

  handleCreateDish(): void {
    const defaultCategory = this.categories[0] || 'עיקרית';
    const defaultKosherType = this.kosherTypes[0] || 'פרווה';
    const defaultUnit = this.units[0] || 'יחידות';

    this.editingDish = {
      id: '',
      name: '',
      description: '',
      estimatedPrice: 0,
      category: defaultCategory,
      kosherType: defaultKosherType,
      servingSize: 1,
      ingredients: [],
      equipment: [],
      isActive: true,
      createdDate: new Date(),
      lastModified: new Date(),
      servingDescription: '',
      servingIngredients: [],
      servingDishes: [],
      waiterNotes: ''
    };

    this.editingDish.ingredients = this.editingDish.ingredients.map(ingredient => ({
      ...ingredient,
      unit: ingredient.unit || defaultUnit
    }));
    this.isDialogOpen = true;
  }

  handleEditDish(dish: Dish): void {
    this.editingDish = { ...dish };
    this.isDialogOpen = true;
  }

  handleSaveDish(): void {
    if (!this.editingDish) return;

    if (!this.editingDish.name.trim()) {
      this.messageService.add({
        severity: 'error',
        summary: 'שגיאה',
        detail: 'יש להזין שם מנה'
      });
      return;
    }

    const isUpdate = !!this.editingDish.id;
    const payload = isUpdate
      ? this.mapDishToUpdatePayload(this.editingDish)
      : this.mapDishToCreatePayload(this.editingDish);

    const request$ = isUpdate
      ? this.dishService.updateDish(this.editingDish.id, payload as DishUpdate)
      : this.dishService.createDish(payload as DishCreate);

    request$
      .pipe(
        takeUntil(this.destroy$),
        catchError(error => {
          console.error('Error saving dish:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'שגיאה',
            detail: 'שמירת המנה נכשלה'
          });
          return EMPTY;
        })
      )
      .subscribe(() => {
        this.messageService.add({
          severity: 'success',
          summary: 'הצלחה',
          detail: isUpdate ? 'המנה עודכנה בהצלחה' : 'המנה נוצרה בהצלחה'
        });
        this.isDialogOpen = false;
        this.editingDish = null;
        this.loadDishes();
      });
  }

  confirmDelete(id: string): void {
    this.confirmationService.confirm({
      message: 'האם למחוק מנה זו? פעולה זו לא ניתנת לביטול.',
      header: 'אישור מחיקה',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'מחק',
      rejectLabel: 'ביטול',
      accept: () => {
        this.handleDeleteDish(id);
      }
    });
  }

  handleDeleteDish(id: string): void {
    this.dishService.deleteDish(id)
      .pipe(
        takeUntil(this.destroy$),
        catchError(error => {
          console.error('Error deleting dish:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'שגיאה',
            detail: 'מחיקת המנה נכשלה'
          });
          return EMPTY;
        })
      )
      .subscribe(() => {
        this.messageService.add({
          severity: 'success',
          summary: 'הצלחה',
          detail: 'המנה נמחקה'
        });
        this.loadDishes();
      });
  }

  // Ingredient management
  handleAddIngredient(): void {
    if (!this.editingDish) return;
    const defaultUnit = this.units[0] || 'יחידות';
    this.editingDish.ingredients.unshift({
      productName: '',
      quantity: 0,
      unit: defaultUnit
    });
  }

  handleUpdateIngredient(index: number, field: keyof DishIngredient, value: any): void {
    if (!this.editingDish) return;
    this.editingDish.ingredients[index] = {
      ...this.editingDish.ingredients[index],
      [field]: value
    };
  }

  handleRemoveIngredient(index: number): void {
    if (!this.editingDish) return;
    this.editingDish.ingredients.splice(index, 1);
  }

  // Equipment management
  handleAddEquipment(): void {
    if (!this.editingDish) return;
    this.editingDish.equipment.push({
      name: '',
      required: true
    });
  }

  handleUpdateEquipment(index: number, field: keyof DishEquipment, value: any): void {
    if (!this.editingDish) return;
    this.editingDish.equipment[index] = {
      ...this.editingDish.equipment[index],
      [field]: value
    };
  }

  handleRemoveEquipment(index: number): void {
    if (!this.editingDish) return;
    this.editingDish.equipment.splice(index, 1);
  }

  // Serving ingredients management
  handleAddServingIngredient(): void {
    if (!this.editingDish) return;
    if (!this.editingDish.servingIngredients) {
      this.editingDish.servingIngredients = [];
    }
    const defaultUnit = this.units[0] || 'יחידות';
    this.editingDish.servingIngredients.unshift({
      productName: '',
      quantity: 0,
      unit: defaultUnit
    });
  }

  handleUpdateServingIngredient(index: number, field: string, value: any): void {
    if (!this.editingDish || !this.editingDish.servingIngredients) return;
    this.editingDish.servingIngredients[index] = {
      ...this.editingDish.servingIngredients[index],
      [field]: value
    };
  }

  handleRemoveServingIngredient(index: number): void {
    if (!this.editingDish || !this.editingDish.servingIngredients) return;
    this.editingDish.servingIngredients.splice(index, 1);
  }

  // Serving dishes management
  handleAddServingDish(): void {
    if (!this.editingDish) return;
    if (!this.editingDish.servingDishes) {
      this.editingDish.servingDishes = [];
    }
    this.editingDish.servingDishes.unshift({
      name: '',
      quantity: 1,
      category: ''
    });
  }

  handleUpdateServingDish(index: number, field: string, value: any): void {
    if (!this.editingDish || !this.editingDish.servingDishes) return;
    this.editingDish.servingDishes[index] = {
      ...this.editingDish.servingDishes[index],
      [field]: value
    };
  }

  handleRemoveServingDish(index: number): void {
    if (!this.editingDish || !this.editingDish.servingDishes) return;
    this.editingDish.servingDishes.splice(index, 1);
  }

  // Cart management
  // Helper methods
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

  // TrackBy function to prevent re-rendering of list items
  trackByIndex(index: number, item: any): number {
    return index;
  }
}
