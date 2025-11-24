import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export interface Event {
  id: string;
  name: string;
  participants: number;
  eventType: string;
  foodType: string;
  dishes: any[];
  createdAt: Date;
}

export interface CartItem {
  dishId: string;
  dishName: string;
  quantity: number;
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

  constructor() {
    this.loadFromStorage();
  }

  private loadFromStorage(): void {
    const events = JSON.parse(localStorage.getItem('events') || '[]');
    const cart = JSON.parse(localStorage.getItem('cart') || '[]');
    const currentEventId = localStorage.getItem('currentEventId');

    this.eventsSubject.next(events);
    this.cartSubject.next(cart);
    this.currentEventSubject.next(currentEventId);
  }

  private saveToStorage(): void {
    localStorage.setItem('events', JSON.stringify(this.eventsSubject.value));
    localStorage.setItem('cart', JSON.stringify(this.cartSubject.value));
    if (this.currentEventSubject.value) {
      localStorage.setItem('currentEventId', this.currentEventSubject.value);
    }
  }

  createEvent(event: Omit<Event, 'id' | 'createdAt' | 'dishes'>): string {
    const newEvent: Event = {
      id: Date.now().toString(),
      ...event,
      dishes: [],
      createdAt: new Date()
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

  addDishToCart(dishId: string, dishName: string, quantity: number = 1): void {
    const currentEventId = this.currentEventSubject.value;
    if (!currentEventId) {
      throw new Error('No current event selected');
    }

    const cart = [...this.cartSubject.value];
    const existingItem = cart.find(item => 
      item.dishId === dishId && item.eventId === currentEventId
    );

    if (existingItem) {
      existingItem.quantity += quantity;
    } else {
      cart.push({
        dishId,
        dishName,
        quantity,
        eventId: currentEventId
      });
    }

    this.cartSubject.next(cart);
    this.saveToStorage();
  }

  removeDishFromCart(dishId: string): void {
    const currentEventId = this.currentEventSubject.value;
    if (!currentEventId) return;

    const cart = this.cartSubject.value.filter(item => 
      !(item.dishId === dishId && item.eventId === currentEventId)
    );

    this.cartSubject.next(cart);
    this.saveToStorage();
  }

  updateCartItemQuantity(dishId: string, quantity: number): void {
    const currentEventId = this.currentEventSubject.value;
    if (!currentEventId) return;

    const cart = [...this.cartSubject.value];
    const item = cart.find(item => 
      item.dishId === dishId && item.eventId === currentEventId
    );

    if (item) {
      if (quantity <= 0) {
        this.removeDishFromCart(dishId);
      } else {
        item.quantity = quantity;
        this.cartSubject.next(cart);
        this.saveToStorage();
      }
    }
  }

  getCartForCurrentEvent(): CartItem[] {
    const currentEventId = this.currentEventSubject.value;
    if (!currentEventId) return [];

    return this.cartSubject.value.filter(item => item.eventId === currentEventId);
  }

  clearCart(): void {
    const currentEventId = this.currentEventSubject.value;
    if (!currentEventId) return;

    const cart = this.cartSubject.value.filter(item => item.eventId !== currentEventId);
    this.cartSubject.next(cart);
    this.saveToStorage();
  }

  getAllEvents(): Event[] {
    return this.eventsSubject.value;
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