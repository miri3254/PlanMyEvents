import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { StorageService } from '../core/services/storage.service';
import { Event, EventStatus } from '../core/models';

export type { Event } from '../core/models';

@Injectable({
  providedIn: 'root'
})
export class EventService {
  private eventsSubject = new BehaviorSubject<Event[]>([]);
  private currentEventSubject = new BehaviorSubject<string | null>(null);
  private dishesSubject = new BehaviorSubject<any[]>([]);
  private productsSubject = new BehaviorSubject<any[]>([]);
  private toolsSubject = new BehaviorSubject<any[]>([]);

  public events$ = this.eventsSubject.asObservable();
  public dishes$ = this.dishesSubject.asObservable();
  public products$ = this.productsSubject.asObservable();
  public tools$ = this.toolsSubject.asObservable();

  public currentEvent$: Observable<Event | null>;

  constructor(private storageService: StorageService) {
    this.currentEvent$ = this.currentEventSubject.pipe(
      map(eventId => eventId ? this.getEvent(eventId) || null : null)
    );
    this.loadFromStorage();
  }

  private loadFromStorage(): void {
    const events = this.storageService.get<Event[]>('events') || [];
    const currentEventId = this.storageService.get<string>('currentEventId');

    this.eventsSubject.next(events);
    this.currentEventSubject.next(currentEventId || null);
    
    this.saveToStorage();
  }

  private saveToStorage(): void {
    this.storageService.set('events', this.eventsSubject.value);
    this.storageService.set('currentEventId', this.currentEventSubject.value);
  }

  createEvent(event: Omit<Event, 'id' | 'createdAt' | 'dishes' | 'eventDate' | 'status'> & { eventDate?: Date | string }): string {
    const newEvent: Event = {
      id: Date.now().toString(),
      ...event,
      dishes: [],
      createdAt: new Date(),
      eventDate: event.eventDate || new Date(),
      status: 'בהמתנה לאישור'  // Default status
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

  getEvents(): Event[] {
    return [...this.eventsSubject.value].sort((a, b) => {
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
    
    this.eventsSubject.next(events);
    
    if (this.currentEventSubject.value === id) {
      this.currentEventSubject.next(null);
    }
    
    this.saveToStorage();
  }

  saveDish(dish: any): void {
    const dishes = [...this.dishesSubject.value];
    const existingIndex = dishes.findIndex(d => d.id === dish.id);
    
    if (existingIndex >= 0) {
      dishes[existingIndex] = dish;
    } else {
      dishes.push(dish);
    }
    
    this.dishesSubject.next(dishes);
  }

  deleteDish(dishId: string): void {
    const dishes = this.dishesSubject.value.filter(dish => dish.id !== dishId);
    this.dishesSubject.next(dishes);
  }

  // Product methods
  saveProduct(product: any): void {
    const products = [...this.productsSubject.value];
    const existingIndex = products.findIndex(p => p.id === product.id);
    
    if (existingIndex >= 0) {
      products[existingIndex] = product;
    } else {
      products.push(product);
    }
    
    this.productsSubject.next(products);
  }

  deleteProduct(productId: string): void {
    const products = this.productsSubject.value.filter(product => product.id !== productId);
    this.productsSubject.next(products);
  }

  // Tool methods
  saveTool(tool: any): void {
    const tools = [...this.toolsSubject.value];
    const existingIndex = tools.findIndex(t => t.id === tool.id);
    
    if (existingIndex >= 0) {
      tools[existingIndex] = tool;
    } else {
      tools.push(tool);
    }
    
    this.toolsSubject.next(tools);
  }

  deleteTool(toolId: string): void {
    const tools = this.toolsSubject.value.filter(tool => tool.id !== toolId);
    this.toolsSubject.next(tools);
  }

  // Event management methods
  canModifyStatus(event: Event): boolean {
    return event.status !== 'הסתיים';
  }

  updateEventDetails(eventId: string, updates: Partial<Event>): Observable<Event> {
    const events = [...this.eventsSubject.value];
    const eventIndex = events.findIndex(e => e.id === eventId);
    
    if (eventIndex >= 0) {
      events[eventIndex] = { ...events[eventIndex], ...updates };
      this.eventsSubject.next(events);
      this.saveToStorage();
      return new BehaviorSubject(events[eventIndex]).asObservable();
    }
    
    throw new Error('Event not found');
  }

  updateEventStatus(eventId: string, status: EventStatus): Observable<Event> {
    return this.updateEventDetails(eventId, { status });
  }

  fetchEventsByRange(start: Date, end: Date): Observable<Event[]> {
    const filteredEvents = this.eventsSubject.value.filter(event => {
      const eventDate = new Date(event.eventDate);
      return eventDate >= start && eventDate <= end;
    });
    return new BehaviorSubject(filteredEvents).asObservable();
  }
}