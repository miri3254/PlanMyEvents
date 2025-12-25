// Main Event Service - Complete state management with LocalStorage

import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, of, throwError } from 'rxjs';
import { delay, map } from 'rxjs/operators';
import { StorageService } from './storage.service';
import { Event, CartItem, Dish, Product, ShoppingListItem, EventStatus, HebrewDateParts } from '../models';
import {
  hebrewPartsToGregorian,
  renderHebrewLabelFromDate,
  renderHebrewLabelFromParts,
  sanitizeHebrewParts
} from '../utils/hebrew-date.util';

type EventDatePayload = {
  eventDate?: Date | string;
  hebrewDate?: string;
  hebrewParts?: HebrewDateParts;
};

type CreateEventPayload = {
  name: string;
  participants: number;
  eventType: string;
  foodType: string;
  notes?: string;
  status?: EventStatus;
} & EventDatePayload;

type UpdateEventPayload = Partial<CreateEventPayload>;

@Injectable({
  providedIn: 'root'
})
export class EventService {
  private readonly calendarFetchDelay = 350;
  // State as BehaviorSubjects
  private eventsSubject = new BehaviorSubject<Event[]>([]);
  private currentEventIdSubject = new BehaviorSubject<string | null>(null);
  private cartSubject = new BehaviorSubject<CartItem[]>([]);
  private dishesSubject = new BehaviorSubject<Dish[]>([]);
  private productsSubject = new BehaviorSubject<Product[]>([]);

  // Public observables
  events$ = this.eventsSubject.asObservable();
  currentEventId$ = this.currentEventIdSubject.asObservable();
  cart$ = this.cartSubject.asObservable();
  dishes$ = this.dishesSubject.asObservable();
  products$ = this.productsSubject.asObservable();

  // Computed observables
  currentEvent$ = this.currentEventId$.pipe(
    map(id => id ? this.eventsSubject.value.find(e => e.id === id) || null : null)
  );

  currentCart$ = this.cart$.pipe(
    map(cart => {
      const currentId = this.currentEventIdSubject.value;
      return currentId ? cart.filter(item => item.eventId === currentId) : [];
    })
  );

  constructor(private storage: StorageService) {
    this.loadFromStorage();
  }

  private loadFromStorage(): void {
    // Load events
    const events = this.storage.get<Event[]>('events') || [];
    this.persistEvents(events);

    // Load current event
    const currentEventId = this.storage.get<string>('currentEvent');
    this.currentEventIdSubject.next(currentEventId);

    // Load cart
    const cart = this.storage.get<CartItem[]>('cart') || [];
    this.cartSubject.next(cart);

    // Load dishes (or generate demo data)
    const dishes = this.storage.get<Dish[]>('dishes');
    if (dishes && dishes.length > 0) {
      this.dishesSubject.next(dishes);
    } else {
      const demoDishes = this.generateDemoDishes();
      this.dishesSubject.next(demoDishes);
      this.storage.set('dishes', demoDishes);
    }

    // Load products (or generate demo data)
    const products = this.storage.get<Product[]>('products');
    if (products && products.length > 0) {
      this.productsSubject.next(products);
    } else {
      const demoProducts = this.generateDemoProducts();
      this.productsSubject.next(demoProducts);
      this.storage.set('products', demoProducts);
    }
  }

  // Event Management
  createEvent(eventData: CreateEventPayload): string {
    const { eventDate, hebrewDate } = this.resolveEventDates(eventData);
    const newEvent: Event = {
      id: Date.now().toString(),
      name: eventData.name,
      participants: eventData.participants,
      eventType: eventData.eventType,
      foodType: eventData.foodType,
      dishes: [],
      createdAt: new Date(),
      eventDate,
      hebrewDate,
      status: eventData.status ?? 'בהמתנה לאישור',
      notes: eventData.notes
    };

    const events = [...this.eventsSubject.value, newEvent];
    this.persistEvents(events);
    return newEvent.id;
  }

  setCurrentEvent(eventId: string | null): void {
    this.currentEventIdSubject.next(eventId);
    if (eventId) {
      this.storage.set('currentEvent', eventId);
    } else {
      this.storage.remove('currentEvent');
    }
  }

  deleteEvent(id: string): void {
    const events = this.eventsSubject.value.filter(e => e.id !== id);
    this.persistEvents(events);

    // Remove cart items for this event
    const cart = this.cartSubject.value.filter(item => item.eventId !== id);
    this.cartSubject.next(cart);
    this.storage.set('cart', cart);

    if (this.currentEventIdSubject.value === id) {
      this.setCurrentEvent(null);
    }
  }

  getCurrentEvent(): Event | null {
    const currentId = this.currentEventIdSubject.value;
    return currentId ? this.eventsSubject.value.find(e => e.id === currentId) || null : null;
  }

  getEventById(eventId: string): Event | undefined {
    return this.eventsSubject.value.find(event => event.id === eventId);
  }

  fetchEventsForMonth(referenceDate: Date): Observable<Event[]> {
    const { start, end } = this.buildMonthlyRange(referenceDate);
    return this.fetchEventsByRange(start, end);
  }

  fetchEventsByRange(start: Date, end: Date): Observable<Event[]> {
    const rangeStart = this.startOfDay(start);
    const rangeEnd = this.endOfDay(end);
    const events = this.eventsSubject.value.filter(event => {
      const eventDate = this.startOfDay(this.toDate(event.eventDate));
      return eventDate >= rangeStart && eventDate <= rangeEnd;
    });

    return of(events).pipe(delay(this.calendarFetchDelay));
  }

  updateEventStatus(eventId: string, nextStatus: EventStatus): Observable<Event> {
    const events = [...this.eventsSubject.value];
    const eventIndex = events.findIndex(event => event.id === eventId);
    if (eventIndex === -1) {
      return throwError(() => new Error('האירוע לא נמצא'));
    }

    const target = events[eventIndex];
    if (!this.canModifyStatus(target)) {
      return throwError(() => new Error('לא ניתן לעדכן אירוע שהסתיים או בוטל לאחר שעבר התאריך.'));
    }

    const updated: Event = this.normalizeEvent({ ...target, status: nextStatus });
    events[eventIndex] = updated;
    this.persistEvents(events);
    return of(updated).pipe(delay(this.calendarFetchDelay));
  }

  updateEventDetails(eventId: string, changes: UpdateEventPayload): Observable<Event> {
    const events = [...this.eventsSubject.value];
    const eventIndex = events.findIndex(event => event.id === eventId);
    if (eventIndex === -1) {
      return throwError(() => new Error('האירוע לא נמצא'));
    }

    const target = events[eventIndex];
    const { eventDate, hebrewDate } = this.resolveEventDates({
      eventDate: changes.eventDate ?? target.eventDate,
      hebrewDate: changes.hebrewDate ?? target.hebrewDate,
      hebrewParts: changes.hebrewParts
    });

    const updated: Event = this.normalizeEvent({
      ...target,
      ...changes,
      eventDate,
      hebrewDate,
      notes: changes.notes ?? target.notes
    });

    events[eventIndex] = updated;
    this.persistEvents(events);
    return of(updated).pipe(delay(this.calendarFetchDelay));
  }

  canModifyStatus(event: Event | null | undefined): boolean {
    if (!event) {
      return false;
    }

    const isPast = this.isPastDate(event.eventDate);
    const immutableStatuses: EventStatus[] = ['הסתיים', 'התבטל'];
    return !(isPast && immutableStatuses.includes(event.status));
  }

  isPastEvent(event: Event | null | undefined): boolean {
    if (!event) {
      return false;
    }
    return this.isPastDate(event.eventDate);
  }

  // Cart Management
  addDishToCart(dishId: string, dishName: string, peopleCount: number): void {
    const currentEventId = this.currentEventIdSubject.value;
    if (!currentEventId) {
      console.error('No current event selected');
      throw new Error('No current event selected');
    }

    if (!dishId || !dishName) {
      console.error('Invalid dish data:', { dishId, dishName });
      throw new Error('Invalid dish data');
    }

    const cart = [...this.cartSubject.value];
    
    // Check if dish already exists in current event's cart
    const existingItem = cart.find(
      item => item.dishId === dishId && item.eventId === currentEventId
    );

    // Prevent duplicates - dish can only be added once per event
    if (existingItem) {
      console.log('Dish already in cart:', dishId);
      return;
    }

    // Add dish with its fixed peopleCount (serving size)
    const newItem: CartItem = {
      dishId,
      dishName,
      peopleCount: peopleCount || 1,
      eventId: currentEventId
    };
    
    cart.push(newItem);
    console.log('Added to cart:', newItem);

    this.cartSubject.next(cart);
    this.storage.set('cart', cart);
  }

  removeDishFromCart(dishId: string, eventId?: string): void {
    const targetEventId = eventId ?? this.currentEventIdSubject.value;
    if (!targetEventId) return;

    const cart = this.cartSubject.value.filter(
      item => !(item.dishId === dishId && item.eventId === targetEventId)
    );
    this.cartSubject.next(cart);
    this.storage.set('cart', cart);
  }

  updateCartItemPeopleCount(dishId: string, peopleCount: number): void {
    const currentEventId = this.currentEventIdSubject.value;
    if (!currentEventId) return;

    if (peopleCount <= 0) {
      this.removeDishFromCart(dishId);
      return;
    }

    const cart = this.cartSubject.value.map(item =>
      item.dishId === dishId && item.eventId === currentEventId
        ? { ...item, peopleCount }
        : item
    );
    this.cartSubject.next(cart);
    this.storage.set('cart', cart);
  }

  clearCart(eventId?: string): void {
    const targetEventId = eventId ?? this.currentEventIdSubject.value;
    if (!targetEventId) return;

    const cart = this.cartSubject.value.filter(item => item.eventId !== targetEventId);
    this.cartSubject.next(cart);
    this.storage.set('cart', cart);
  }

  getTotalCartPrice(): number {
    const currentEventId = this.currentEventIdSubject.value;
    if (!currentEventId) return 0;

    return this.cartSubject.value
      .filter(item => item.eventId === currentEventId)
      .reduce((sum, item) => {
        const dish = this.getDishById(item.dishId);
        return sum + (dish?.estimatedPrice || 0);
      }, 0);
  }

  getCartForCurrentEvent(): CartItem[] {
    const currentEventId = this.currentEventIdSubject.value;
    if (!currentEventId) return [];
    return this.cartSubject.value.filter(item => item.eventId === currentEventId);
  }

  isDishInCurrentEvent(dishId: string): boolean {
    const currentEventId = this.currentEventIdSubject.value;
    if (!currentEventId) return false;

    return this.cartSubject.value.some(item => 
      item.dishId === dishId && item.eventId === currentEventId
    );
  }

  // Dish Management
  saveDish(dish: Dish): void {
    const dishes = this.dishesSubject.value;
    const index = dishes.findIndex(d => d.id === dish.id);

    if (index >= 0) {
      dishes[index] = { ...dish, lastModified: new Date() };
    } else {
      dishes.push({ ...dish, id: Date.now().toString(), createdDate: new Date(), lastModified: new Date() });
    }

    this.dishesSubject.next([...dishes]);
    this.storage.set('dishes', dishes);
  }

  deleteDish(id: string): void {
    const dishes = this.dishesSubject.value.filter(d => d.id !== id);
    this.dishesSubject.next(dishes);
    this.storage.set('dishes', dishes);

    // Remove from cart as well
    const cart = this.cartSubject.value.filter(item => item.dishId !== id);
    this.cartSubject.next(cart);
    this.storage.set('cart', cart);
  }

  getDishById(id: string): Dish | undefined {
    return this.dishesSubject.value.find(d => d.id === id);
  }

  // Product Management
  saveProduct(product: Product): void {
    const products = this.productsSubject.value;
    const index = products.findIndex(p => p.id === product.id);

    if (index >= 0) {
      products[index] = product;
    } else {
      products.push({ ...product, id: Date.now().toString() });
    }

    this.productsSubject.next([...products]);
    this.storage.set('products', products);
  }

  deleteProduct(id: string): void {
    const products = this.productsSubject.value.filter(p => p.id !== id);
    this.productsSubject.next(products);
    this.storage.set('products', products);
  }

  getProductById(id: string): Product | undefined {
    return this.productsSubject.value.find(p => p.id === id);
  }

  // Shopping List
  getShoppingList(): ShoppingListItem[] {
    const currentEventId = this.currentEventIdSubject.value;
    if (!currentEventId) return [];

    const currentCart = this.cartSubject.value.filter(item => item.eventId === currentEventId);
    const dishes = this.dishesSubject.value;
    const products = this.productsSubject.value;
    const shoppingMap = new Map<string, ShoppingListItem>();

    currentCart.forEach(cartItem => {
      const dish = dishes.find(d => d.id === cartItem.dishId);
      if (!dish) return;

      dish.ingredients.forEach(ingredient => {
        const key = ingredient.productName;
        const existing = shoppingMap.get(key);

        if (existing) {
          // Use peopleCount for calculation
          existing.totalQuantity += ingredient.quantity * (cartItem.peopleCount || 1);
          if (!existing.dishes.includes(dish.name)) {
            existing.dishes.push(dish.name);
          }
        } else {
          const product = products.find(p => p.name === ingredient.productName);
          shoppingMap.set(key, {
            productName: ingredient.productName,
            totalQuantity: ingredient.quantity * (cartItem.peopleCount || 1),
            unit: ingredient.unit,
            estimatedPrice: product?.estimatedPrice || 0,
            dishes: [dish.name]
          });
        }
      });
    });

    return Array.from(shoppingMap.values());
  }

  // Helper to get events sorted with active event first
  getEventsSorted(): Event[] {
    const currentId = this.currentEventIdSubject.value;
    const events = [...this.eventsSubject.value];
    
    if (!currentId) {
      // No active event - sort by creation date (newest first)
      return events.sort((a, b) => {
        const dateA = a.createdAt ? new Date(a.createdAt).getTime() : 0;
        const dateB = b.createdAt ? new Date(b.createdAt).getTime() : 0;
        return dateB - dateA;
      });
    }
    
    // Active event exists - put it first, then sort rest by creation date
    return events.sort((a, b) => {
      if (a.id === currentId) return -1;
      if (b.id === currentId) return 1;
      const dateA = a.createdAt ? new Date(a.createdAt).getTime() : 0;
      const dateB = b.createdAt ? new Date(b.createdAt).getTime() : 0;
      return dateB - dateA;
    });
  }

  private persistEvents(events: readonly Event[]): void {
    const normalized = events.map(event => this.normalizeEvent(event));
    this.writeEvents(normalized);
  }

  private writeEvents(events: Event[]): void {
    this.eventsSubject.next(events);
    this.storage.set('events', events);
  }

  private normalizeEvent(event: Event): Event {
    const createdAt = this.toDate(event.createdAt);
    const eventDate = this.toDate(event.eventDate);

    const normalized: Event = {
      ...event,
      dishes: event.dishes || [],
      createdAt,
      eventDate,
      hebrewDate: event.hebrewDate || renderHebrewLabelFromDate(eventDate),
      status: event.status ?? 'בהמתנה לאישור'
    };

    return this.applyAutomaticStatus(normalized);
  }

  private applyAutomaticStatus(event: Event): Event {
    if (this.isPastDate(event.eventDate) && event.status !== 'התבטל') {
      return { ...event, status: 'הסתיים' };
    }
    return event;
  }

  private toDate(value: Date | string | undefined): Date {
    if (value instanceof Date) {
      return new Date(value.getTime());
    }

    if (typeof value === 'string') {
      const parsed = new Date(value);
      if (!Number.isNaN(parsed.getTime())) {
        return parsed;
      }
    }

    return new Date();
  }

  private isPastDate(value: Date | string): boolean {
    const eventDate = this.startOfDay(this.toDate(value));
    return eventDate.getTime() < this.startOfDay(new Date()).getTime();
  }

  private startOfDay(date: Date): Date {
    const normalized = new Date(date);
    normalized.setHours(0, 0, 0, 0);
    return normalized;
  }

  private buildMonthlyRange(reference: Date): { start: Date; end: Date } {
    const start = new Date(reference.getFullYear(), reference.getMonth(), 1);
    start.setHours(0, 0, 0, 0);

    const end = new Date(reference.getFullYear(), reference.getMonth() + 1, 0);
    end.setHours(23, 59, 59, 999);

    return { start, end };
  }

  private resolveEventDates(payload: EventDatePayload): { eventDate: Date; hebrewDate: string } {
    if (payload.eventDate) {
      const eventDate = this.toDate(payload.eventDate);
      return {
        eventDate,
        hebrewDate: payload.hebrewDate || renderHebrewLabelFromDate(eventDate)
      };
    }

    if (payload.hebrewParts) {
      const sanitized = sanitizeHebrewParts(payload.hebrewParts, new Date().getFullYear());
      const eventDate = hebrewPartsToGregorian(sanitized);
      return {
        eventDate,
        hebrewDate: payload.hebrewDate || renderHebrewLabelFromParts(sanitized)
      };
    }

    const fallback = new Date();
    return {
      eventDate: fallback,
      hebrewDate: payload.hebrewDate || renderHebrewLabelFromDate(fallback)
    };
  }

  private endOfDay(date: Date): Date {
    const normalized = new Date(date);
    normalized.setHours(23, 59, 59, 999);
    return normalized;
  }

  // Demo Data Generators
  private generateDemoDishes(): Dish[] {
    const now = new Date();
    return [
      {
        id: '1',
        name: 'עוף בתנור עם תפוחי אדמה',
        description: 'עוף שלם צלוי בתנור עם תפוחי אדמה ותבלינים',
        estimatedPrice: 45,
        category: 'עיקרית',
        kosherType: 'בשרי',
        servingSize: 6,
        ingredients: [
          { productName: 'עוף שלם', quantity: 1.5, unit: 'ק"ג' },
          { productName: 'תפוחי אדמה', quantity: 1, unit: 'ק"ג' },
          { productName: 'שמן זית', quantity: 50, unit: 'מ"ל' },
          { productName: 'פלפל שחור', quantity: 2, unit: 'כפות' },
          { productName: 'מלח', quantity: 1, unit: 'כפות' }
        ],
        equipment: [
          { name: 'תנור', required: true },
          { name: 'תבנית אפייה גדולה', required: true }
        ],
        isActive: true,
        createdDate: now,
        lastModified: now
      },
      {
        id: '2',
        name: 'סלט ירקות טרי',
        description: 'סלט עשיר בירקות טריים ורעננים',
        estimatedPrice: 15,
        category: 'ראשונה',
        kosherType: 'פרווה',
        servingSize: 8,
        ingredients: [
          { productName: 'עגבניות', quantity: 500, unit: 'גרם' },
          { productName: 'מלפפון', quantity: 400, unit: 'גרם' },
          { productName: 'חסה', quantity: 300, unit: 'גרם' },
          { productName: 'שמן זית', quantity: 30, unit: 'מ"ל' },
          { productName: 'מיץ לימון', quantity: 20, unit: 'מ"ל' }
        ],
        equipment: [
          { name: 'קערת סלט', required: true },
          { name: 'סכין חדה', required: true }
        ],
        isActive: true,
        createdDate: now,
        lastModified: now
      },
      {
        id: '3',
        name: 'עוגת שוקולד',
        description: 'עוגת שוקולד עשירה ומפנקת',
        estimatedPrice: 35,
        category: 'קינוח',
        kosherType: 'חלבי',
        servingSize: 12,
        ingredients: [
          { productName: 'קמח', quantity: 300, unit: 'גרם' },
          { productName: 'סוכר', quantity: 250, unit: 'גרם' },
          { productName: 'ביצים', quantity: 4, unit: 'יחידות' },
          { productName: 'חמאה', quantity: 150, unit: 'גרם' },
          { productName: 'שוקולד מריר', quantity: 200, unit: 'גרם' },
          { productName: 'חלב', quantity: 200, unit: 'מ"ל' }
        ],
        equipment: [
          { name: 'תנור', required: true },
          { name: 'מיקסר', required: true },
          { name: 'תבנית עוגה', required: true }
        ],
        isActive: true,
        createdDate: now,
        lastModified: now
      },
      {
        id: '4',
        name: 'אורז לבן',
        description: 'אורז לבן מאודה בטעם עדין',
        estimatedPrice: 10,
        category: 'תוספת',
        kosherType: 'פרווה',
        servingSize: 6,
        ingredients: [
          { productName: 'אורז לבן', quantity: 500, unit: 'גרם' },
          { productName: 'מלח', quantity: 1, unit: 'כפות' },
          { productName: 'שמן צמחי', quantity: 20, unit: 'מ"ל' }
        ],
        equipment: [
          { name: 'סיר בינוני', required: true }
        ],
        isActive: true,
        createdDate: now,
        lastModified: now
      },
      {
        id: '5',
        name: 'דגים אפויים',
        description: 'פילה דג אפוי עם ירקות',
        estimatedPrice: 55,
        category: 'עיקרית',
        kosherType: 'פרווה',
        servingSize: 6,
        ingredients: [
          { productName: 'פילה דג', quantity: 1.2, unit: 'ק"ג' },
          { productName: 'שמן זית', quantity: 40, unit: 'מ"ל' },
          { productName: 'מלח', quantity: 1, unit: 'כפות' },
          { productName: 'פלפל שחור', quantity: 1, unit: 'כפות' },
          { productName: 'לימון', quantity: 2, unit: 'יחידות' }
        ],
        equipment: [
          { name: 'תנור', required: true },
          { name: 'תבנית אפייה', required: true }
        ],
        isActive: true,
        createdDate: now,
        lastModified: now
      },
      {
        id: '6',
        name: 'מיץ תפוזים טבעי',
        description: 'מיץ תפוזים סחוט טרי',
        estimatedPrice: 20,
        category: 'משקה',
        kosherType: 'פרווה',
        servingSize: 8,
        ingredients: [
          { productName: 'תפוזים', quantity: 2, unit: 'ק"ג' },
          { productName: 'סוכר', quantity: 50, unit: 'גרם' }
        ],
        equipment: [
          { name: 'מסחטת מיצים', required: true },
          { name: 'כד', required: true }
        ],
        isActive: true,
        createdDate: now,
        lastModified: now
      }
    ];
  }

  private generateDemoProducts(): Product[] {
    return [
      { id: '1', name: 'עוף שלם', inventoryStatus: 'במלאי', brand: 'טיב טעם', packageQuantity: 1.5, estimatedPrice: 25, category: 'בשר ועוף', supplier: 'טיב טעם' },
      { id: '2', name: 'תפוחי אדמה', inventoryStatus: 'במלאי', brand: 'תנובה', packageQuantity: 1, estimatedPrice: 8, category: 'ירקות', supplier: 'תנובה' },
      { id: '3', name: 'שמן זית', inventoryStatus: 'במלאי', brand: 'עין זית', packageQuantity: 1, estimatedPrice: 45, category: 'שמנים', supplier: 'עין זית' },
      { id: '4', name: 'פלפל שחור', inventoryStatus: 'במלאי', brand: 'פרישמן', packageQuantity: 100, estimatedPrice: 12, category: 'תבלינים', supplier: 'פרישמן' },
      { id: '5', name: 'מלח', inventoryStatus: 'במלאי', brand: 'מלח הארץ', packageQuantity: 1, estimatedPrice: 5, category: 'תבלינים', supplier: 'מלח הארץ' },
      { id: '6', name: 'עגבניות', inventoryStatus: 'במלאי', brand: 'חקלאים', packageQuantity: 1, estimatedPrice: 7, category: 'ירקות', supplier: 'חקלאים' },
      { id: '7', name: 'מלפפון', inventoryStatus: 'במלאי', brand: 'חקלאים', packageQuantity: 1, estimatedPrice: 6, category: 'ירקות', supplier: 'חקלאים' },
      { id: '8', name: 'חסה', inventoryStatus: 'מלאי-נמוך', brand: 'חקלאים', packageQuantity: 0.5, estimatedPrice: 8, category: 'ירקות', supplier: 'חקלאים' },
      { id: '9', name: 'מיץ לימון', inventoryStatus: 'במלאי', brand: 'פרימור', packageQuantity: 0.5, estimatedPrice: 10, category: 'משקאות', supplier: 'פרימור' },
      { id: '10', name: 'קמח', inventoryStatus: 'במלאי', brand: 'תבואה', packageQuantity: 1, estimatedPrice: 6, category: 'אפייה', supplier: 'תבואה' },
      { id: '11', name: 'סוכר', inventoryStatus: 'במלאי', brand: 'סוגת', packageQuantity: 1, estimatedPrice: 5, category: 'אפייה', supplier: 'סוגת' },
      { id: '12', name: 'ביצים', inventoryStatus: 'במלאי', brand: 'זוגלובק', packageQuantity: 12, estimatedPrice: 15, category: 'חלבי', supplier: 'זוגלובק' },
      { id: '13', name: 'חמאה', inventoryStatus: 'במלאי', brand: 'תנובה', packageQuantity: 200, estimatedPrice: 12, category: 'חלבי', supplier: 'תנובה' },
      { id: '14', name: 'שוקולד מריר', inventoryStatus: 'במלאי', brand: 'עלית', packageQuantity: 200, estimatedPrice: 18, category: 'ממתקים', supplier: 'עלית' },
      { id: '15', name: 'חלב', inventoryStatus: 'במלאי', brand: 'תנובה', packageQuantity: 1, estimatedPrice: 6, category: 'חלבי', supplier: 'תנובה' },
      { id: '16', name: 'אורז לבן', inventoryStatus: 'במלאי', brand: 'סוגת', packageQuantity: 1, estimatedPrice: 8, category: 'דגנים', supplier: 'סוגת' },
      { id: '17', name: 'שמן צמחי', inventoryStatus: 'במלאי', brand: 'עין זית', packageQuantity: 1, estimatedPrice: 15, category: 'שמנים', supplier: 'עין זית' },
      { id: '18', name: 'פילה דג', inventoryStatus: 'מלאי-נמוך', brand: 'דגי ים תיכון', packageQuantity: 1, estimatedPrice: 45, category: 'דגים', supplier: 'דגי ים תיכון' },
      { id: '19', name: 'תפוזים', inventoryStatus: 'במלאי', brand: 'חקלאים', packageQuantity: 2, estimatedPrice: 12, category: 'פירות', supplier: 'חקלאים' },
      { id: '20', name: 'לימון', inventoryStatus: 'במלאי', brand: 'חקלאים', packageQuantity: 0.5, estimatedPrice: 8, category: 'פירות', supplier: 'חקלאים' }
    ];
  }
}
