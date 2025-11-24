# PlanMyEvents - Angular Implementation

## ✅ Completed Implementation

### 1. Core Architecture
- ✅ Core models in `src/app/core/models/index.ts`
- ✅ App constants in `src/app/core/constants/app.constants.ts`
- ✅ StorageService with localStorage wrapper
- ✅ EventService with full state management and demo data
- ✅ RTL configuration in index.html
- ✅ Global styles with kosher badges and design system
- ✅ Navigation component with event management
- ✅ Dashboard component with statistics and charts
- ✅ App routing configuration

### 2. Features Implemented
- **LocalStorage Integration**: All data persists with `planmyevents_` prefix
- **Demo Data**: 6 demo dishes and 20 demo products auto-generate
- **RTL Support**: Full Hebrew RTL layout configured
- **Event Management**: Create, select, delete events
- **State Management**: RxJS BehaviorSubjects for reactive state

### 3. Design System
- Orange gradient primary theme (HSL values)
- Kosher type color coding:
  - חלבי (Dairy): Blue `hsl(210, 100%, 56%)`
  - בשרי (Meat): Orange `hsl(24, 95%, 53%)`
  - פרווה (Parve): Green `hsl(142, 76%, 48%)`
- Gradient cards with hover effects
- Professional navigation with event selector

## 🚧 Components to Complete

### Dishes Component (`src/app/components/dishes/dishes.ts`)
**Current Status**: Needs major updates

**Required Features**:
1. Display dishes in grid/table view with toggle
2. Filter by category and kosher type
3. Event mode filtering (show only compatible kosher types)
4. Add to cart button (only visible when event selected)
5. CRUD operations with PrimeNG Dialog
6. Multi-tab form for dish editing:
   - Details tab
   - Ingredients tab (with product selector from EventService)
   - Equipment tab
7. Kosher badges for each dish
8. Active/inactive toggle

**Key Implementation Notes**:
```typescript
// Get dishes from EventService
dishes$ = this.eventService.dishes$;
currentEvent$ = this.eventService.currentEvent$;

// Filter logic for event mode
getFilteredDishes(dishes: Dish[], event: Event | null): Dish[] {
  if (!event) return dishes;
  
  // If event is חלבי or בשרי, show that type + פרווה
  if (event.foodType === 'חלבי') {
    return dishes.filter(d => d.kosherType === 'חלבי' || d.kosherType === 'פרווה');
  }
  // Similar for בשרי
  // If כל הסוגים, show all
}

// Add to cart
addToCart(dish: Dish) {
  this.eventService.addDishToCart(
    dish.id,
    dish.name,
    1,
    dish.estimatedPrice
  );
}
```

### Products Component (`src/app/components/products/products.ts`)
**Current Status**: Needs major updates

**Required Features**:
1. DataTable with all products
2. Inventory status badges with colors:
   - במלאי: Green
   - מלאי-נמוך: Yellow/Orange
   - אזל: Red
3. CRUD operations
4. Statistics cards showing inventory breakdown
5. Search and filter functionality

### Cart Component (`src/app/components/cart/cart.ts`)
**Current Status**: Needs major updates

**Required Features**:
1. Display cart items for current event only
2. Quantity adjustment (+/- buttons)
3. Remove item button
4. Total price calculation
5. Clear cart button
6. Shopping list generation button
7. Shopping List Dialog showing:
   - Aggregated ingredients by product name
   - Total quantities with units
   - Which dishes use each ingredient
   - Estimated price per product
   - Total estimated cost

**Key Implementation**:
```typescript
cartItems$ = this.eventService.currentCart$;

// Get total price
totalPrice = this.eventService.getTotalCartPrice();

// Generate shopping list
showShoppingList() {
  const shoppingList = this.eventService.getShoppingList();
  // Display in dialog
}
```

## 📦 Required Dependencies

All dependencies are already in the project:
- **PrimeNG 20.3.0**: UI component library
- **PrimeFlex 4.0.0**: Utility CSS
- **PrimeIcons 7.0.0**: Icon library
- **Chart.js 4.5.1**: For dashboard charts
- **RxJS 7.8.0**: Reactive programming

## 🎨 Styling Guidelines

### Use Existing CSS Classes
```html
<!-- Kosher Badges -->
<span class="kosher-badge kosher-badge-dairy">חלבי</span>
<span class="kosher-badge kosher-badge-meat">בשרי</span>
<span class="kosher-badge kosher-badge-parve">פרווה</span>

<!-- Inventory Status -->
<span class="status-badge status-in-stock">במלאי</span>
<span class="status-badge status-low-stock">מלאי-נמוך</span>
<span class="status-badge status-out-of-stock">אזל</span>

<!-- Cards -->
<div class="card">Content</div>
<div class="gradient-card">Gradient content</div>
```

### RTL Considerations
- Use PrimeNG `[rtl]="true"` on dialogs
- All layouts automatically RTL due to global styles
- Icons appear on the correct side in RTL

## 🔧 Development Commands

```bash
# Start development server
npm start
# or
ng serve

# Build for production
npm run build
# or
ng build

# Run tests
npm test
```

## 📊 LocalStorage Structure

```
planmyevents_events      → Array<Event>
planmyevents_cart        → Array<CartItem>
planmyevents_dishes      → Array<Dish>
planmyevents_products    → Array<Product>
planmyevents_currentEvent → string (event ID)
```

## 🎯 Critical Implementation Patterns

### 1. Accessing Data from EventService
```typescript
constructor(private eventService: EventService) {}

ngOnInit() {
  // Subscribe to observables
  this.dishes$ = this.eventService.dishes$;
  this.currentEvent$ = this.eventService.currentEvent$;
  
  // Or use async pipe in template
}
```

### 2. CRUD Operations
```typescript
// Create/Update Dish
saveDish(dish: Dish) {
  this.eventService.saveDish(dish);
}

// Delete Dish
deleteDish(id: string) {
  this.eventService.deleteDish(id);
}

// Same patterns for products
```

### 3. Cart Operations
```typescript
// Add to cart (from dishes component)
this.eventService.addDishToCart(dishId, dishName, quantity, price);

// Update quantity (from cart component)
this.eventService.updateCartItemQuantity(dishId, newQuantity);

// Remove from cart
this.eventService.removeDishFromCart(dishId);

// Clear cart
this.eventService.clearCart();
```

### 4. Event Selection
```typescript
// The navigation component already handles this
// Other components just need to observe:
this.currentEvent$ = this.eventService.currentEvent$;
```

## 🎨 PrimeNG Components to Use

### Dishes Component
- `p-dataview` with grid/list templates
- `p-dialog` for CRUD forms
- `p-tabview` for multi-tab form
- `p-dropdown` for selectors
- `p-button` for actions
- `p-multiselect` for ingredient selection

### Products Component
- `p-table` with sorting/filtering
- `p-dialog` for CRUD forms
- `p-inputtext` for form fields
- `p-inputnumber` for numbers

### Cart Component
- `p-table` for cart items
- `p-button` for actions
- `p-inputnumber` for quantity
- `p-dialog` for shopping list

## ⚠️ Important Notes

1. **Never change localStorage key prefix**: Always use `planmyevents_`
2. **Kosher filtering logic**: פרווה is compatible with everything
3. **Cart is event-scoped**: Only show items for current event
4. **Demo data**: Auto-generates if storage is empty
5. **All text in Hebrew**: UI must be fully Hebrew RTL
6. **Forms validation**: Use Angular Forms with validators

## 🚀 Next Steps

1. Complete Dishes component with all CRUD operations
2. Complete Products component with inventory management
3. Complete Cart component with shopping list
4. Test all LocalStorage operations
5. Test event switching and cart isolation
6. Add loading states and error handling
7. Add toast notifications for user feedback
8. Test responsive design on mobile

## 📝 Testing Checklist

- [ ] Create event → dishes appear
- [ ] Add dishes to cart → verify cart updates
- [ ] Switch events → cart shows correct items
- [ ] Delete event → cart clears for that event
- [ ] Generate shopping list → ingredients aggregate correctly
- [ ] Edit dish → changes persist in localStorage
- [ ] Filter dishes by kosher type in event mode
- [ ] Inventory status displays correctly with colors
- [ ] All Hebrew text displays RTL
- [ ] Navigation event selector works
- [ ] Charts display on dashboard

## 🎓 Key Angular Concepts Used

- **Standalone Components**: No NgModules
- **Lazy Loading**: Routes use loadComponent
- **RxJS**: BehaviorSubjects for state
- **Async Pipe**: Template subscriptions
- **Reactive Programming**: Observable streams
- **Services**: Singleton state management with providedIn: 'root'
- **LocalStorage**: Browser persistence
- **TypeScript**: Strong typing throughout

---

**Project Status**: Core architecture complete, UI components need implementation with full CRUD operations.
