import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { StorageService } from '../core/services/storage.service';

export interface Event {
  id: string;
  name: string;
  participants: number;
  eventType: string;
  foodType: string;
  dishes: any[];
  createdAt: Date;
  eventDate: Date | string;  // Actual date of the event
}

export interface CartItem {
  dishId: string;
  dishName: string;
  peopleCount: number;  // Number of people this dish serves
  eventId: string;
}

@Injectable({
  providedIn: 'root'
})
export class EventService {
  private eventsSubject = new BehaviorSubject<Event[]>([]);
  private cartSubject = new BehaviorSubject<CartItem[]>([]);
  private currentEventSubject = new BehaviorSubject<string | null>(null);

  public events$ = this.eventsSubject.asObservable();
  public cart$ = this.cartSubject.asObservable();
  public currentEvent$ = this.currentEventSubject.asObservable();

  constructor(private storageService: StorageService) {
    this.loadFromStorage();
  }

  private loadFromStorage(): void {
    const events = this.storageService.get<Event[]>('events') || [];
    let cart = this.storageService.get<CartItem[]>('cart') || [];
    const currentEventId = this.storageService.get<string>('currentEventId');

    // Migrate old cart data: convert quantity to peopleCount if needed
    cart = cart.map((item: any) => {
      if ('quantity' in item && !('peopleCount' in item)) {
        // Old format - migrate to new format
        return {
          dishId: item.dishId,
          dishName: item.dishName,
          peopleCount: item.quantity || 1,
          eventId: item.eventId
        };
      }
      // Ensure all required fields exist
      return {
        dishId: item.dishId,
        dishName: item.dishName,
        peopleCount: item.peopleCount || 1,
        eventId: item.eventId
      };
    });

    this.eventsSubject.next(events);
    this.cartSubject.next(cart);
    this.currentEventSubject.next(currentEventId || null);
    
    // Save migrated data
    this.saveToStorage();
  }

  private saveToStorage(): void {
    this.storageService.set('events', this.eventsSubject.value);
    this.storageService.set('cart', this.cartSubject.value);
    this.storageService.set('currentEventId', this.currentEventSubject.value);
  }

  createEvent(event: Omit<Event, 'id' | 'createdAt' | 'dishes' | 'eventDate'> & { eventDate?: Date | string }): string {
    const newEvent: Event = {
      id: Date.now().toString(),
      ...event,
      dishes: [],
      createdAt: new Date(),
      eventDate: event.eventDate || new Date()  // Use provided date or current date
    };

    const events = [...this.eventsSubject.value, newEvent];
    this.eventsSubject.next(events);
    this.currentEventSubject.next(newEvent.id);
    this.saveToStorage();

    return newEvent.id;
  }

  getCurrentEvent(): Event | null {
    const currentEventId = this.currentEventSubject.value;
    if (!currentEventId) return null;
    
    return this.eventsSubject.value.find(event => event.id === currentEventId) || null;
  }

  setCurrentEvent(eventId: string): void {
    this.currentEventSubject.next(eventId);
    this.saveToStorage();
  }

  addDishToCart(dishId: string, dishName: string, peopleCount: number): void {
    const currentEventId = this.currentEventSubject.value;
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
    const existingItem = cart.find(item => 
      item.dishId === dishId && item.eventId === currentEventId
    );

    // Prevent duplicates - dish can only be added once per event
    if (existingItem) {
      console.log('Dish already in cart:', dishId);
      return; // Dish already in cart, do nothing
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
    this.saveToStorage();
  }

  removeDishFromCart(dishId: string): void {
    const currentEventId = this.currentEventSubject.value;
    if (!currentEventId) {
      console.warn('No current event selected for removal');
      return;
    }

    console.log('Removing dish from cart:', { dishId, eventId: currentEventId });

    // Remove dish from current event's cart
    const cart = this.cartSubject.value.filter(item => 
      !(item.dishId === dishId && item.eventId === currentEventId)
    );

    console.log('Cart after removal:', cart);
    this.cartSubject.next(cart);
    this.saveToStorage();
  }

  // Quantity updates removed - single-selection model with fixed peopleCount

  getCartForCurrentEvent(): CartItem[] {
    const currentEventId = this.currentEventSubject.value;
    if (!currentEventId) return [];

    return this.cartSubject.value.filter(item => item.eventId === currentEventId);
  }

  isDishInCurrentEvent(dishId: string): boolean {
    const currentEventId = this.currentEventSubject.value;
    if (!currentEventId) return false;

    return this.cartSubject.value.some(item => 
      item.dishId === dishId && item.eventId === currentEventId
    );
  }

  clearCart(): void {
    const currentEventId = this.currentEventSubject.value;
    if (!currentEventId) {
      console.warn('No current event selected for clearing cart');
      return;
    }

    console.log('Clearing cart for event:', currentEventId);

    // Remove all dishes from current event's cart
    const cart = this.cartSubject.value.filter(item => item.eventId !== currentEventId);
    
    console.log('Cart after clearing:', cart);
    this.cartSubject.next(cart);
    this.saveToStorage();
  }

  getAllEvents(): Event[] {
    return this.eventsSubject.value;
  }

  getEventsSorted(): Event[] {
    const currentId = this.currentEventSubject.value;
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

  getEvent(id: string): Event | undefined {
    return this.eventsSubject.value.find(event => event.id === id);
  }

  deleteEvent(id: string): void {
    const events = this.eventsSubject.value.filter(event => event.id !== id);
    const cart = this.cartSubject.value.filter(item => item.eventId !== id);
    
    this.eventsSubject.next(events);
    this.cartSubject.next(cart);
    
    if (this.currentEventSubject.value === id) {
      this.currentEventSubject.next(null);
    }
    
    this.saveToStorage();
  }
}