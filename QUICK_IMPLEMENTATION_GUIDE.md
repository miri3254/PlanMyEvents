# PlanMyEvents - Implementation Guide

## 🎯 Project Structure Summary

Your Angular application now has the perfect foundation with:

### ✅ Completed Core Architecture

1. **Models** (`src/app/core/models/index.ts`)
   - All interfaces defined (Dish, Product, Event, CartItem, ShoppingListItem)
   - TypeScript types for all data structures

2. **Constants** (`src/app/core/constants/app.constants.ts`)
   - CATEGORIES, KOSHER_TYPES, EVENT_TYPES, UNITS, INVENTORY_STATUS
   - Type-safe constants for dropdowns and validation

3. **Services**
   - **StorageService** (`src/app/core/services/storage.service.ts`)
     - Wrapper for localStorage with `planmyevents_` prefix
     - Type-safe get/set/remove/clear methods
   
   - **EventService** (`src/app/core/services/event.service.ts`)
     - Complete state management with RxJS BehaviorSubjects
     - Event CRUD operations
     - Cart management (add, remove, update, clear)
     - Dish CRUD operations
     - Product CRUD operations
     - Shopping list generation
     - Demo data auto-generation (6 dishes, 20 products)
     - All data persists to localStorage automatically

4. **Global Styles** (`src/styles.scss`)
   - RTL support configured
   - Orange gradient design system
   - Kosher badge classes (dairy/meat/parve)
   - Inventory status badge classes
   - Card styles with hover effects
   - Complete color palette as CSS variables

5. **Navigation** (`src/app/shared/components/navigation/navigation.component.ts`)
   - Modern gradient navigation bar
   - Event selector dropdown
   - Create new event dialog
   - Responsive menu
   - Current event display badge

6. **Dashboard** (`src/app/components/dashboard/dashboard.component.ts`)
   - Statistics cards (events, dishes, products, cart items)
   - Pie/Doughnut charts for dish distribution
   - Current event display
   - Quick links to other pages

7. **App Setup**
   - RTL configured in `index.html` with `dir="rtl"`
   - Hebrew font (Heebo) loaded
   - Material Icons loaded
   - Routing configured with lazy loading
   - App component simplified to use navigation

## 🔧 Components Requiring Updates

### Dishes Component Updates Needed

**File**: `src/app/components/dishes/dishes.ts`

**Required Changes**:

1. Update imports to use new core structure:
```typescript
import { EventService } from '../../core/services/event.service';
import { Dish, Product } from '../../core/models';
import { CATEGORIES, KOSHER_TYPES, UNITS } from '../../core/constants/app.constants';
```

2. Remove local dish storage logic - use EventService:
```typescript
// Instead of local array:
dishes$ = this.eventService.dishes$;
products$ = this.eventService.products$;
currentEvent$ = this.eventService.currentEvent$;
```

3. Update save method:
```typescript
saveDish(dish: Dish) {
  this.eventService.saveDish(dish);
  this.messageService.add({
    severity: 'success',
    summary: 'הצלחה',
    detail: 'המנה נשמרה בהצלחה'
  });
}
```

4. Update delete method:
```typescript
deleteDish(id: string) {
  this.eventService.deleteDish(id);
}
```

5. Add to cart method:
```typescript
addToCart(dish: Dish) {
  const currentEvent = this.eventService.getCurrentEvent();
  if (!currentEvent) {
    this.messageService.add({
      severity: 'warn',
      summary: 'שים לב',
      detail: 'נא לבחור אירוע תחילה'
    });
    return;
  }
  
  this.eventService.addDishToCart(
    dish.id,
    dish.name,
    1,
    dish.estimatedPrice
  );
  
  this.messageService.add({
    severity: 'success',
    summary: 'נוסף לעגלה',
    detail: `${dish.name} נוסף לעגלה`
  });
}
```

6. Filter dishes by event kosher type:
```typescript
getFilteredDishes(): Observable<Dish[]> {
  return combineLatest([this.dishes$, this.currentEvent$]).pipe(
    map(([dishes, event]) => {
      if (!event) return dishes;
      
      // Filter by kosher compatibility
      if (event.foodType === 'חלבי') {
        return dishes.filter(d => 
          d.kosherType === 'חלבי' || d.kosherType === 'פרווה'
        );
      }
      if (event.foodType === 'בשרי') {
        return dishes.filter(d => 
          d.kosherType === 'בשרי' || d.kosherType === 'פרווה'
        );
      }
      if (event.foodType === 'פרווה') {
        return dishes.filter(d => d.kosherType === 'פרווה');
      }
      // 'כל הסוגים'
      return dishes;
    })
  );
}
```

### Products Component Updates

**File**: `src/app/components/products/products.ts`

**Required Changes**:

1. Update imports:
```typescript
import { EventService } from '../../core/services/event.service';
import { Product } from '../../core/models';
import { INVENTORY_STATUS } from '../../core/constants/app.constants';
```

2. Use EventService for data:
```typescript
products$ = this.eventService.products$;
```

3. Update save/delete methods:
```typescript
saveProduct(product: Product) {
  this.eventService.saveProduct(product);
}

deleteProduct(id: string) {
  this.eventService.deleteProduct(id);
}
```

4. Add inventory statistics:
```typescript
getInventoryStats(): Observable<any> {
  return this.products$.pipe(
    map(products => {
      return {
        inStock: products.filter(p => p.inventoryStatus === 'במלאי').length,
        lowStock: products.filter(p => p.inventoryStatus === 'מלאי-נמוך').length,
        outOfStock: products.filter(p => p.inventoryStatus === 'אזל').length,
        total: products.length
      };
    })
  );
}
```

### Cart Component Updates

**File**: `src/app/components/cart/cart.ts`

**Required Changes**:

1. Update imports:
```typescript
import { EventService } from '../../core/services/event.service';
import { CartItem, ShoppingListItem } from '../../core/models';
```

2. Use EventService observables:
```typescript
cartItems$ = this.eventService.currentCart$;
currentEvent$ = this.eventService.currentEvent$;
```

3. Cart operations:
```typescript
updateQuantity(dishId: string, quantity: number) {
  this.eventService.updateCartItemQuantity(dishId, quantity);
}

removeItem(dishId: string) {
  this.eventService.removeDishFromCart(dishId);
}

clearCart() {
  if (confirm('האם אתה בטוח שברצונך לנקות את העגלה?')) {
    this.eventService.clearCart();
  }
}

getTotalPrice(): number {
  return this.eventService.getTotalCartPrice();
}
```

4. Shopping list generation:
```typescript
showShoppingListDialog = false;
shoppingList: ShoppingListItem[] = [];

generateShoppingList() {
  this.shoppingList = this.eventService.getShoppingList();
  this.showShoppingListDialog = true;
}
```

## 🎨 Using Pre-Built CSS Classes

Your global styles now include ready-to-use classes:

### Kosher Badges
```html
<span class="kosher-badge kosher-badge-dairy">חלבי</span>
<span class="kosher-badge kosher-badge-meat">בשרי</span>
<span class="kosher-badge kosher-badge-parve">פרווה</span>
```

### Inventory Status
```html
<span class="status-badge status-in-stock">במלאי</span>
<span class="status-badge status-low-stock">מלאי-נמוך</span>
<span class="status-badge status-out-of-stock">אזל</span>
```

### Cards
```html
<div class="card">Regular card</div>
<div class="gradient-card">Gradient card with hover effect</div>
```

## 🚀 Testing The Application

### Test Scenario 1: Event Management
1. Start the app - demo data auto-loads
2. Click "אירוע חדש" in navigation
3. Create event: "שבת חתן", 50 guests, type "שבת", food "בשרי"
4. Event appears in dropdown and becomes current event

### Test Scenario 2: Dishes & Cart
1. Navigate to "מנות" (Dishes)
2. See 6 demo dishes filtered by event kosher type
3. Click add to cart on a dish
4. Navigate to "עגלה" (Cart)
5. See the dish in cart
6. Adjust quantity with +/- buttons
7. Click "צור רשימת קניות" to see shopping list
8. Shopping list aggregates all ingredients

### Test Scenario 3: Products
1. Navigate to "מוצרים" (Products)
2. See 20 demo products with inventory status
3. Edit a product
4. Status badge color changes based on inventory

### Test Scenario 4: Dashboard
1. Navigate to home (Dashboard)
2. See statistics for events, dishes, products, cart
3. View pie charts for dish distribution
4. Click quick links to navigate

### Test Scenario 5: LocalStorage Persistence
1. Add items to cart
2. Refresh browser (F5)
3. All data persists (events, cart, dishes, products)
4. Open DevTools → Application → LocalStorage
5. See keys: `planmyevents_events`, `planmyevents_cart`, etc.

## 📋 Implementation Checklist

### ✅ Already Done
- [x] Core models and types
- [x] Constants for dropdowns
- [x] StorageService with localStorage
- [x] EventService with full state management
- [x] Demo data generation
- [x] Global RTL styles
- [x] Design system (colors, badges, cards)
- [x] Navigation component
- [x] Dashboard component
- [x] Routing configuration
- [x] App component integration

### 🔄 Need Updates (Using Existing Code)
- [ ] Update Dishes component to use EventService
- [ ] Update Products component to use EventService
- [ ] Update Cart component to use EventService
- [ ] Test event filtering in Dishes
- [ ] Test cart operations
- [ ] Test shopping list generation
- [ ] Test LocalStorage persistence

### 🎯 The Key Principle

**DO NOT rewrite from scratch!** Your existing components have excellent UI and functionality. Just update them to:

1. **Import from new locations**:
   - `../../core/models` instead of `../../models/dish.model`
   - `../../core/services/event.service` instead of `../../services/event.service`
   - `../../core/constants/app.constants` for dropdown options

2. **Use EventService methods instead of local storage**:
   - Replace local `dishes` array with `dishes$ = this.eventService.dishes$`
   - Replace local save logic with `this.eventService.saveDish(dish)`
   - Use `async pipe` in templates: `*ngFor="let dish of dishes$ | async"`

3. **Keep all your existing UI components**:
   - Your PrimeNG dialogs, tables, forms are perfect
   - Your existing layout and styling work great
   - Just connect them to EventService instead of local state

## 🎓 Quick Reference

### Get Data
```typescript
dishes$ = this.eventService.dishes$;
products$ = this.eventService.products$;
cart$ = this.eventService.currentCart$;
events$ = this.eventService.events$;
currentEvent$ = this.eventService.currentEvent$;
```

### Save Data
```typescript
this.eventService.saveDish(dish);
this.eventService.saveProduct(product);
```

### Delete Data
```typescript
this.eventService.deleteDish(id);
this.eventService.deleteProduct(id);
```

### Cart Operations
```typescript
this.eventService.addDishToCart(dishId, dishName, qty, price);
this.eventService.updateCartItemQuantity(dishId, newQty);
this.eventService.removeDishFromCart(dishId);
this.eventService.clearCart();
```

### Get Shopping List
```typescript
const list = this.eventService.getShoppingList();
```

---

**You're 80% done!** The architecture is solid. Just update the component imports and connect them to EventService. The system will work perfectly with full LocalStorage persistence, event management, and shopping list generation! 🎉
