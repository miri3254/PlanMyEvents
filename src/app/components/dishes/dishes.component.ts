import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Observable, Subject, combineLatest } from 'rxjs';
import { map, takeUntil } from 'rxjs/operators';
import { EventService } from '../../core/services/event.service';
import { Dish, DishIngredient, DishEquipment, Product, Event } from '../../core/models';
import { CATEGORIES, KOSHER_TYPES, UNITS } from '../../core/constants/app.constants';
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
import { SelectButtonModule } from 'primeng/selectbutton';
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
    SelectButtonModule,
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
  currentCart$!: Observable<any[]>;

  viewMode: 'table' | 'grid' = 'grid';
  searchQuery: string = '';
  filterCategory: string = 'הכל';
  filterKosher: string = 'הכל';
  editingDish: Dish | null = null;
  isDialogOpen: boolean = false;
  showShoppingList: boolean = false;
  showCart: boolean = false;

  currentEvent: Event | null = null;
  isEventMode: boolean = false;
  products: Product[] = [];
  cartItems: any[] = [];
  shoppingList: any[] = [];
  totalPrice: number = 0;

  viewOptions = [
    { icon: 'pi pi-th-large', value: 'grid' },
    { icon: 'pi pi-list', value: 'table' }
  ];

  categoryOptions = [
    { label: 'כל הקטגוריות', value: 'הכל' },
    ...CATEGORIES.map(cat => ({ label: cat, value: cat }))
  ];

  kosherOptions = [
    { label: 'כל סוגי הכשרות', value: 'הכל' },
    ...KOSHER_TYPES.map(type => ({ label: type, value: type }))
  ];

  categories = [...CATEGORIES];
  kosherTypes = [...KOSHER_TYPES];
  units = [...UNITS];

  constructor(
    private eventService: EventService,
    private confirmationService: ConfirmationService,
    private messageService: MessageService
  ) {}

  ngOnInit(): void {
    this.dishes$ = this.eventService.dishes$;
    this.products$ = this.eventService.products$;
    this.currentEvent$ = this.eventService.currentEvent$;
    this.currentCart$ = this.eventService.currentCart$;

    // Subscribe to products
    this.products$.pipe(takeUntil(this.destroy$)).subscribe(products => {
      this.products = products;
    });

    // Subscribe to current event
    this.currentEvent$.pipe(takeUntil(this.destroy$)).subscribe(event => {
      this.currentEvent = event;
      this.isEventMode = !!event;
    });

    // Subscribe to cart
    this.currentCart$.pipe(takeUntil(this.destroy$)).subscribe(cart => {
      this.cartItems = cart;
      this.totalPrice = this.eventService.getTotalCartPrice();
    });

    // Setup filtered dishes
    this.setupFilteredDishes();
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

  handleCreateDish(): void {
    this.editingDish = {
      id: Date.now().toString(),
      name: '',
      description: '',
      estimatedPrice: 0,
      category: 'עיקרית',
      kosherType: 'פרווה',
      servingSize: 1,
      ingredients: [],
      equipment: [],
      isActive: true,
      createdDate: new Date(),
      lastModified: new Date()
    };
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

    this.eventService.saveDish(this.editingDish);
    this.messageService.add({
      severity: 'success',
      summary: 'הצלחה',
      detail: 'המנה נשמרה בהצלחה'
    });
    this.isDialogOpen = false;
    this.editingDish = null;
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
    this.eventService.deleteDish(id);
    this.messageService.add({
      severity: 'success',
      summary: 'הצלחה',
      detail: 'המנה נמחקה'
    });
  }

  handleAddToCart(dish: Dish): void {
    console.log('handleAddToCart called with dish:', dish);
    
    if (!this.isEventMode) {
      console.warn('Not in event mode');
      this.messageService.add({
        severity: 'warn',
        summary: 'שים לב',
        detail: 'יש לבחור אירוע תחילה'
      });
      return;
    }

    try {
      // Use dish.servingSize as peopleCount, with fallback to 1
      const servingSize = dish.servingSize || 1;
      console.log('Calling addDishToCart with:', {
        dishId: dish.id,
        dishName: dish.name,
        servingSize
      });
      
      this.eventService.addDishToCart(dish.id, dish.name, servingSize);
      
      this.messageService.add({
        severity: 'success',
        summary: 'נוסף לתפריט',
        detail: `${dish.name} נוסף לעגלה`
      });
    } catch (error) {
      console.error('Error in handleAddToCart:', error);
      this.messageService.add({
        severity: 'error',
        summary: 'שגיאה',
        detail: 'אירעה שגיאה בהוספת המנה'
      });
    }
  }

  // Ingredient management
  handleAddIngredient(): void {
    if (!this.editingDish) return;
    this.editingDish.ingredients.push({
      productName: '',
      quantity: 0,
      unit: 'גרם'
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

  // Cart management
  updateCartPeopleCount(dishId: string, peopleCount: number): void {
    this.eventService.updateCartItemPeopleCount(dishId, peopleCount);
  }

  removeFromCart(dishId: string): void {
    this.eventService.removeDishFromCart(dishId);
  }

  clearCart(): void {
    this.confirmationService.confirm({
      message: 'האם לנקות את כל העגלה?',
      header: 'אישור',
      icon: 'pi pi-question-circle',
      acceptLabel: 'כן',
      rejectLabel: 'לא',
      accept: () => {
        this.eventService.clearCart();
        this.messageService.add({
          severity: 'success',
          summary: 'הצלחה',
          detail: 'העגלה נוקתה'
        });
      }
    });
  }

  openShoppingList(): void {
    this.shoppingList = this.eventService.getShoppingList();
    this.showShoppingList = true;
  }

  getShoppingListTotal(): number {
    return this.shoppingList.reduce((sum, item) => 
      sum + (item.estimatedPrice * item.totalQuantity), 0
    );
  }

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
}
