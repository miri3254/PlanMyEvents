import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Dish, DishIngredient, DishEquipment, EventDishSelection, ShoppingListItem } from '../../models/dish.model';
import { Product } from '../../models/product.model';
import { EventService, Event, CartItem } from '../../services/event.service';
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
import { TooltipModule } from 'primeng/tooltip';
import { SelectButtonModule } from 'primeng/selectbutton';
import { RippleModule } from 'primeng/ripple';
import { CheckboxModule } from 'primeng/checkbox';
import { DividerModule } from 'primeng/divider';
import { FloatLabelModule } from 'primeng/floatlabel';
import { TextareaModule } from 'primeng/textarea';
import { PanelModule } from 'primeng/panel';
import { AccordionModule } from 'primeng/accordion';
import { BadgeModule } from 'primeng/badge';
import { MultiSelectModule } from 'primeng/multiselect';
import { InputGroupModule } from 'primeng/inputgroup';
import { InputGroupAddonModule } from 'primeng/inputgroupaddon';
import { FieldsetModule } from 'primeng/fieldset';
import { SplitterModule } from 'primeng/splitter';

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
    TooltipModule,
    SelectButtonModule,
    RippleModule,
    CheckboxModule,
    DividerModule,
    FloatLabelModule,
    TextareaModule,
    PanelModule,
    AccordionModule,
    BadgeModule,
    MultiSelectModule,
    InputGroupModule,
    InputGroupAddonModule,
    FieldsetModule,
    SplitterModule
  ],
  templateUrl: './dishes.html',
  styleUrls: ['./dishes.scss'],
  providers: [ConfirmationService, MessageService]
})
export class DishesComponent implements OnInit {
  // Main data arrays
  dishes: Dish[] = [];
  filteredDishes: Dish[] = [];
  availableProducts: Product[] = [];
  
  // Event and cart data
  currentEvent: Event | null = null;
  cartItems: CartItem[] = [];
  showCart: boolean = false;
  
  // UI state
  viewMode: 'table' | 'cards' = 'cards';
  currentView: 'management' | 'event-selection' = 'management';
  
  // Dialog states
  dishDialog: boolean = false;
  eventSelectionDialog: boolean = false;
  shoppingListDialog: boolean = false;
  dishIngredientsDialog: boolean = false;
  
  // Current dish for ingredients editing
  currentDishForIngredients: Dish | null = null;
  
  // Form data
  dish: Dish = this.createEmptyDish();
  submitted: boolean = false;
  
  // Search and filtering
  searchValue: string = '';
  selectedCategories: string[] = [];
  selectedKosherTypes: string[] = [];
  
  // Event selection
  eventDishSelections: EventDishSelection[] = [];
  totalEventPrice: number = 0;
  shoppingList: ShoppingListItem[] = [];
  eventName: string = '';
  
  // Categories and units
  dishCategories = [
    { label: 'מנה עיקרית', value: 'מנה עיקרית' },
    { label: 'מנה ראשונה', value: 'מנה ראשונה' },
    { label: 'תוספת', value: 'תוספת' },
    { label: 'קינוח', value: 'קינוח' },
    { label: 'משקה', value: 'משקה' },
    { label: 'חטיף', value: 'חטיף' }
  ];

  kosherTypes = [
    { label: 'חלבי', value: 'חלבי', icon: 'pi pi-heart-fill', color: '#007bff' },
    { label: 'בשרי', value: 'בשרי', icon: 'pi pi-star-fill', color: '#dc3545' },
    { label: 'פרווה', value: 'פרווה', icon: 'pi pi-circle-fill', color: '#28a745' }
  ];
  
  units = [
    { label: 'גרם', value: 'גרם' },
    { label: 'קילוגרם', value: 'ק"ג' },
    { label: 'ליטר', value: 'ליטר' },
    { label: 'מ"ל', value: 'מ"ל' },
    { label: 'יחידות', value: 'יחידות' },
    { label: 'כפות', value: 'כפות' },
    { label: 'כוסות', value: 'כוסות' }
  ];

  constructor(
    private confirmationService: ConfirmationService,
    private messageService: MessageService,
    private eventService: EventService
  ) {}

  ngOnInit(): void {
    this.loadMockData();
    this.loadCurrentEvent();
    this.loadCart();
  }

  loadCurrentEvent(): void {
    this.currentEvent = this.eventService.getCurrentEvent();
    if (this.currentEvent) {
      this.currentView = 'event-selection';
    }
  }

  loadCart(): void {
    this.eventService.cart$.subscribe(cart => {
      this.cartItems = this.eventService.getCartForCurrentEvent();
    });
  }

  loadMockData(): void {
    // Load mock products (in real app, this would come from a service)
    this.availableProducts = [
      {
        name: 'לחם אחיד',
        inventoryStatus: 'במלאי',
        brand: 'אנגל',
        packageQuantity: 1,
        estimatedPrice: 12,
        category: 'מוצרי מזון',
        supplier: 'ספק לחמים בע"מ'
      },
      {
        name: 'חלב 3%',
        inventoryStatus: 'במלאי',
        brand: 'תנובה',
        packageQuantity: 1,
        estimatedPrice: 7,
        category: 'מוצרי חלב',
        supplier: 'תנובה בע"מ'
      },
      {
        name: 'ביצים',
        inventoryStatus: 'במלאי',
        brand: 'חוות העוף',
        packageQuantity: 12,
        estimatedPrice: 18,
        category: 'מוצרי חלב',
        supplier: 'חוות העוף'
      },
      {
        name: 'קמח לבן',
        inventoryStatus: 'במלאי',
        brand: 'מולינו',
        packageQuantity: 1,
        estimatedPrice: 8,
        category: 'מוצרי מזון',
        supplier: 'מולינו'
      }
    ];

    // Load mock dishes
    this.dishes = [
      {
        id: '1',
        name: 'פנקייק קלאסי',
        description: 'פנקייק רך וטעים לארוחת בוקר',
        estimatedPrice: 25,
        category: 'מנה ראשונה',
        kosherType: 'חלבי',
        servingSize: 4,
        ingredients: [
          { productName: 'קמח לבן', quantity: 200, unit: 'גרם' },
          { productName: 'חלב 3%', quantity: 300, unit: 'מ"ל' },
          { productName: 'ביצים', quantity: 2, unit: 'יחידות' }
        ],
        equipment: [
          { name: 'מחבת', required: true },
          { name: 'קערת ערבוב', required: true },
          { name: 'מטרפה', required: true }
        ],
        isActive: true,
        createdDate: new Date(),
        lastModified: new Date()
      },
      {
        id: '2',
        name: 'טוסט פרנצ׳',
        description: 'טוסט מטוגן בביצה וחלב',
        estimatedPrice: 18,
        category: 'מנה ראשונה',
        kosherType: 'חלבי',
        servingSize: 2,
        ingredients: [
          { productName: 'לחם אחיד', quantity: 4, unit: 'יחידות' },
          { productName: 'ביצים', quantity: 3, unit: 'יחידות' },
          { productName: 'חלב 3%', quantity: 100, unit: 'מ"ל' }
        ],
        equipment: [
          { name: 'מחבת גדולה', required: true },
          { name: 'קערת ערבוב', required: true }
        ],
        isActive: true,
        createdDate: new Date(),
        lastModified: new Date()
      },
      {
        id: '3',
        name: 'שניצל עוף',
        description: 'שניצל עוף פריך וטעים',
        estimatedPrice: 35,
        category: 'מנה עיקרית',
        kosherType: 'בשרי',
        servingSize: 4,
        ingredients: [
          { productName: 'חזה עוף', quantity: 800, unit: 'גרם' },
          { productName: 'קמח לבן', quantity: 100, unit: 'גרם' },
          { productName: 'ביצים', quantity: 2, unit: 'יחידות' },
          { productName: 'פירורי לחם', quantity: 150, unit: 'גרם' }
        ],
        equipment: [
          { name: 'מחבת עמוקה', required: true },
          { name: 'קערות ערבוב', required: true },
          { name: 'פטיש בשר', required: false }
        ],
        isActive: true,
        createdDate: new Date(),
        lastModified: new Date()
      },
      {
        id: '4',
        name: 'סלט ירקות',
        description: 'סלט ירקות טריים וצבעוניים',
        estimatedPrice: 12,
        category: 'תוספת',
        kosherType: 'פרווה',
        servingSize: 6,
        ingredients: [
          { productName: 'עגבניות', quantity: 3, unit: 'יחידות' },
          { productName: 'מלפפונים', quantity: 2, unit: 'יחידות' },
          { productName: 'בצל', quantity: 1, unit: 'יחידות' },
          { productName: 'שמן זית', quantity: 50, unit: 'מ"ל' }
        ],
        equipment: [
          { name: 'קערת סלט', required: true },
          { name: 'סכין חד', required: true }
        ],
        isActive: true,
        createdDate: new Date(),
        lastModified: new Date()
      },
      {
        id: '5',
        name: 'עוגת שוקולד',
        description: 'עוגת שוקולד עשירה וטעימה',
        estimatedPrice: 40,
        category: 'קינוח',
        kosherType: 'חלבי',
        servingSize: 8,
        ingredients: [
          { productName: 'קמח לבן', quantity: 250, unit: 'גרם' },
          { productName: 'חלב 3%', quantity: 200, unit: 'מ"ל' },
          { productName: 'ביצים', quantity: 4, unit: 'יחידות' },
          { productName: 'שוקולד מריר', quantity: 200, unit: 'גרם' }
        ],
        equipment: [
          { name: 'תבנית עוגה', required: true },
          { name: 'מיקסר', required: true },
          { name: 'תנור', required: true }
        ],
        isActive: true,
        createdDate: new Date(),
        lastModified: new Date()
      }
    ];
    
    this.filteredDishes = [...this.dishes];
  }

  createEmptyDish(): Dish {
    return {
      name: '',
      description: '',
      estimatedPrice: 0,
      category: 'מנה עיקרית',
      kosherType: 'פרווה',
      servingSize: 1,
      ingredients: [],
      equipment: [],
      isActive: true,
      createdDate: new Date(),
      lastModified: new Date()
    };
  }

  // Search and filtering methods
  onSearch(): void {
    if (this.searchValue.trim()) {
      this.filteredDishes = this.dishes.filter(dish =>
        dish.name.toLowerCase().includes(this.searchValue.toLowerCase()) ||
        dish.description?.toLowerCase().includes(this.searchValue.toLowerCase()) ||
        dish.category.toLowerCase().includes(this.searchValue.toLowerCase())
      );
    } else {
      this.filteredDishes = [...this.dishes];
    }
    this.applyFilters();
  }

  clearSearch(): void {
    this.searchValue = '';
    this.filteredDishes = [...this.dishes];
    this.applyFilters();
  }

  filterByCategory(): void {
    this.applyFilters();
  }

  filterByKosherType(): void {
    this.applyFilters();
  }

  applyFilters(): void {
    let filtered = [...this.dishes];
    
    if (this.searchValue.trim()) {
      filtered = filtered.filter(dish =>
        dish.name.toLowerCase().includes(this.searchValue.toLowerCase()) ||
        dish.description?.toLowerCase().includes(this.searchValue.toLowerCase()) ||
        dish.category.toLowerCase().includes(this.searchValue.toLowerCase()) ||
        dish.kosherType.toLowerCase().includes(this.searchValue.toLowerCase())
      );
    }
    
    if (this.selectedCategories.length > 0) {
      filtered = filtered.filter(dish => this.selectedCategories.includes(dish.category));
    }

    if (this.selectedKosherTypes.length > 0) {
      filtered = filtered.filter(dish => this.selectedKosherTypes.includes(dish.kosherType));
    }
    
    this.filteredDishes = filtered;
  }

  // CRUD operations
  openNew(): void {
    this.dish = this.createEmptyDish();
    this.submitted = false;
    this.dishDialog = true;
  }

  editDish(dish: Dish): void {
    this.dish = { ...dish };
    this.dishDialog = true;
  }

  deleteDish(dish: Dish): void {
    this.confirmationService.confirm({
      message: `האם אתה בטוח שברצונך למחוק את המנה "${dish.name}"?`,
      header: 'אישור מחיקה',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'כן',
      rejectLabel: 'לא',
      accept: () => {
        this.dishes = this.dishes.filter(d => d.id !== dish.id);
        this.applyFilters();
        this.messageService.add({
          severity: 'success',
          summary: 'הצלחה',
          detail: 'המנה נמחקה בהצלחה'
        });
      }
    });
  }

  hideDialog(): void {
    this.dishDialog = false;
    this.submitted = false;
  }

  saveDish(): void {
    this.submitted = true;

    if (this.dish.name?.trim() && this.dish.ingredients.length > 0) {
      this.dish.lastModified = new Date();
      
      if (this.dish.id) {
        // Edit existing
        const index = this.dishes.findIndex(d => d.id === this.dish.id);
        if (index !== -1) {
          this.dishes[index] = { ...this.dish };
        }
      } else {
        // Add new
        this.dish.id = Date.now().toString();
        this.dish.createdDate = new Date();
        this.dishes.push({ ...this.dish });
      }
      
      this.applyFilters();
      this.messageService.add({
        severity: 'success',
        summary: 'הצלחה',
        detail: this.dish.id ? 'המנה עודכנה בהצלחה' : 'המנה נוספה בהצלחה'
      });
      
      this.dishDialog = false;
      this.dish = this.createEmptyDish();
    }
  }

  // Ingredient management
  addIngredient(): void {
    this.dish.ingredients.push({ productName: '', quantity: 1, unit: 'גרם' });
  }

  removeIngredient(index: number): void {
    this.dish.ingredients.splice(index, 1);
  }

  // Equipment management
  addEquipment(): void {
    this.dish.equipment.push({ name: '', required: true });
  }

  removeEquipment(index: number): void {
    this.dish.equipment.splice(index, 1);
  }

  // View management
  toggleView(): void {
    this.viewMode = this.viewMode === 'table' ? 'cards' : 'table';
  }

  switchToEventSelection(): void {
    this.currentView = 'event-selection';
    this.eventDishSelections = [];
    this.totalEventPrice = 0;
  }

  switchToManagement(): void {
    this.currentView = 'management';
  }

  // Event selection methods
  addToEvent(dish: Dish): void {
    if (!this.currentEvent) {
      this.messageService.add({
        severity: 'warn',
        summary: 'שגיאה',
        detail: 'לא נבחר אירוע. אנא צור אירוע חדש תחילה.'
      });
      return;
    }

    try {
      this.eventService.addDishToCart(dish.id!, dish.name, 1);
      this.messageService.add({
        severity: 'success',
        summary: 'נוסף בהצלחה',
        detail: `${dish.name} נוסף לתפריט האירוע`
      });
    } catch (error) {
      this.messageService.add({
        severity: 'error',
        summary: 'שגיאה',
        detail: 'אירעה שגיאה בהוספת המנה'
      });
    }
  }

  removeFromCart(dishId: string): void {
    this.eventService.removeDishFromCart(dishId);
    this.messageService.add({
      severity: 'info',
      summary: 'הוסר',
      detail: 'המנה הוסרה מהתפריט'
    });
  }

  updateCartQuantity(dishId: string, quantity: number): void {
    this.eventService.updateCartItemQuantity(dishId, quantity);
  }

  toggleCart(): void {
    this.showCart = !this.showCart;
  }

  getCartTotal(): number {
    return this.cartItems.reduce((total, item) => {
      const dish = this.dishes.find(d => d.id === item.dishId);
      return total + (dish?.estimatedPrice || 0) * item.quantity;
    }, 0);
  }

  getCartItemsCount(): number {
    return this.cartItems.reduce((total, item) => total + item.quantity, 0);
  }

  clearCart(): void {
    this.confirmationService.confirm({
      message: 'האם אתה בטוח שברצונך לנקות את כל התפריט?',
      header: 'אישור ניקוי',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'כן',
      rejectLabel: 'לא',
      accept: () => {
        this.eventService.clearCart();
        this.messageService.add({
          severity: 'info',
          summary: 'נוקה',
          detail: 'התפריט נוקה בהצלחה'
        });
      }
    });
  }

  getDishFromCart(dishId: string): { dish: Dish, quantity: number } | null {
    const cartItem = this.cartItems.find(item => item.dishId === dishId);
    if (!cartItem) return null;
    
    const dish = this.dishes.find(d => d.id === dishId);
    if (!dish) return null;
    
    return { dish, quantity: cartItem.quantity };
  }

  // Legacy methods for backward compatibility with template
  updateEventDishQuantity(selection: any): void {
    // This method is kept for template compatibility but uses cart system
    if (selection && selection.dish && selection.quantity) {
      this.updateCartQuantity(selection.dish.id, selection.quantity);
    }
  }

  removeFromEvent(dishId: string): void {
    // This method is kept for template compatibility but uses cart system
    this.removeFromCart(dishId);
  }

  // Helper method for template calculations
  getCartItemTotal(dishId: string, quantity: number): number {
    const dish = this.dishes.find(d => d.id === dishId);
    return (dish?.estimatedPrice || 0) * quantity;
  }

  generateShoppingList(): void {
    const shoppingMap = new Map<string, ShoppingListItem>();
    
    this.eventDishSelections.forEach(selection => {
      selection.dish.ingredients.forEach(ingredient => {
        const key = ingredient.productName;
        const totalNeeded = ingredient.quantity * selection.quantity;
        
        if (shoppingMap.has(key)) {
          const item = shoppingMap.get(key)!;
          item.totalQuantity += totalNeeded;
          item.dishes.push(selection.dish.name);
        } else {
          const product = this.availableProducts.find(p => p.name === ingredient.productName);
          shoppingMap.set(key, {
            productName: ingredient.productName,
            totalQuantity: totalNeeded,
            unit: ingredient.unit,
            estimatedPrice: product?.estimatedPrice || 0,
            dishes: [selection.dish.name]
          });
        }
      });
    });
    
    this.shoppingList = Array.from(shoppingMap.values());
    this.shoppingListDialog = true;
  }

  // Utility methods
  getCategorySeverity(category: string): "success" | "info" | "warn" | "danger" | "secondary" | "contrast" | null {
    switch (category) {
      case 'מנה עיקרית':
        return 'contrast';
      case 'מנה ראשונה':
        return 'info';
      case 'תוספת':
        return 'secondary';
      case 'קינוח':
        return 'warn';
      default:
        return 'info';
    }
  }

  getKosherTypeSeverity(kosherType: string): "success" | "info" | "warn" | "danger" | "secondary" | "contrast" | null {
    switch (kosherType) {
      case 'חלבי':
        return 'info';
      case 'בשרי':
        return 'danger';
      case 'פרווה':
        return 'success';
      default:
        return 'secondary';
    }
  }

  getKosherTypeIcon(kosherType: string): string {
    switch (kosherType) {
      case 'חלבי':
        return 'pi pi-heart-fill';
      case 'בשרי':
        return 'pi pi-star-fill';
      case 'פרווה':
        return 'pi pi-circle-fill';
      default:
        return 'pi pi-circle';
    }
  }

  getAvailableProducts(): any[] {
    return this.availableProducts.map(product => ({
      label: product.name,
      value: product.name
    }));
  }

  getShoppingListTotal(): number {
    return this.shoppingList.reduce((total, item) => total + (item.estimatedPrice * item.totalQuantity), 0);
  }

  // Dish-specific ingredients management
  openDishIngredientsDialog(dish: Dish): void {
    this.currentDishForIngredients = { ...dish };
    this.dishIngredientsDialog = true;
  }

  closeDishIngredientsDialog(): void {
    this.dishIngredientsDialog = false;
    this.currentDishForIngredients = null;
  }

  saveDishIngredients(): void {
    if (this.currentDishForIngredients) {
      const index = this.dishes.findIndex(d => d.id === this.currentDishForIngredients!.id);
      if (index !== -1) {
        this.dishes[index] = { ...this.currentDishForIngredients };
        this.applyFilters();
        this.messageService.add({
          severity: 'success',
          summary: 'הצלחה',
          detail: 'רשימת המרכיבים עודכנה בהצלחה'
        });
      }
    }
    this.closeDishIngredientsDialog();
  }

  addDishIngredient(): void {
    if (this.currentDishForIngredients) {
      this.currentDishForIngredients.ingredients.push({ 
        productName: '', 
        quantity: 1, 
        unit: 'גרם' 
      });
    }
  }

  removeDishIngredient(index: number): void {
    if (this.currentDishForIngredients) {
      this.currentDishForIngredients.ingredients.splice(index, 1);
    }
  }

  // Table editing methods
  onRowEditInit(dish: Dish): void {
    // Clone the dish for potential rollback
    this.clonedDishes[dish.id!] = { ...dish };
  }

  onRowEditSave(dish: Dish): void {
    if (dish.name?.trim()) {
      delete this.clonedDishes[dish.id!];
      this.messageService.add({
        severity: 'success', 
        summary: 'הצלחה', 
        detail: 'המנה עודכנה בהצלחה'
      });
    } else {
      this.messageService.add({
        severity: 'error', 
        summary: 'שגיאה', 
        detail: 'שם המנה נדרש'
      });
    }
  }

  onRowEditCancel(dish: Dish, index: number): void {
    if (this.clonedDishes[dish.id!]) {
      this.dishes[index] = this.clonedDishes[dish.id!];
      delete this.clonedDishes[dish.id!];
    }
  }

  private clonedDishes: { [s: string]: Dish } = {};
}