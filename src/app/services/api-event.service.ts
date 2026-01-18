import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { BaseApiService } from '../core/services/base-api.service';
import { 
  ApiEvent, 
  EventCreate, 
  EventUpdate, 
  EventStatusUpdate, 
  EventDish,
  EventsQueryParams,
  ApiResponse,
  ShoppingListItem,
  EquipmentListItem
} from '../core/models/api.models';

@Injectable({
  providedIn: 'root'
})
export class ApiEventService extends BaseApiService {

  // Events CRUD
  getEvents(params?: EventsQueryParams): Observable<ApiResponse<ApiEvent>> {
    return this.get<ApiResponse<ApiEvent>>('/events', params);
  }

  getEvent(eventId: string): Observable<ApiEvent> {
    return this.get<ApiEvent>(`/events/${eventId}`);
  }

  createEvent(event: EventCreate): Observable<ApiEvent> {
    return this.post<ApiEvent>('/events', event);
  }

  updateEvent(eventId: string, event: EventUpdate): Observable<ApiEvent> {
    return this.put<ApiEvent>(`/events/${eventId}`, event);
  }

  updateEventStatus(eventId: string, status: EventStatusUpdate): Observable<ApiEvent> {
    return this.patch<ApiEvent>(`/events/${eventId}/status`, status);
  }

  deleteEvent(eventId: string): Observable<void> {
    return this.delete<void>(`/events/${eventId}`);
  }

  // Event Dishes
  addDishToEvent(eventId: string, dishData: { dish_id: string; quantity: number }): Observable<EventDish> {
    return this.post<EventDish>(`/events/${eventId}/dishes`, dishData);
  }

  updateEventDish(eventId: string, dishId: string, quantity: { quantity: number }): Observable<EventDish> {
    return this.put<EventDish>(`/events/${eventId}/dishes/${dishId}`, quantity);
  }

  removeDishFromEvent(eventId: string, dishId: string): Observable<void> {
    return this.delete<void>(`/events/${eventId}/dishes/${dishId}`);
  }

  // Event Lists
  getShoppingList(eventId: string): Observable<ShoppingListItem[]> {
    return this.get<ShoppingListItem[]>(`/events/${eventId}/shopping-list`);
  }

  getEquipmentList(eventId: string): Observable<EquipmentListItem[]> {
    return this.get<EquipmentListItem[]>(`/events/${eventId}/equipment-list`);
  }
}