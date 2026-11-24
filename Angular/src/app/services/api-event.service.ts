import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { BaseApiService } from '../core/services/base-api.service';
import {
  ApiEvent,
  EventCreate,
  EventUpdate,
  EventStatusUpdate,
  EventPriceUpdate,
  DeliveryNoteTemplate,
  ApiEventDish,
  EventDishCreate,
  EventsQueryParams,
  ApiResponse,
  ShoppingListResponse,
  EquipmentListResponse,
  EventCalculationSettings,
  EventCalculationSummary
} from '../core/models/api.models';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiEventService extends BaseApiService {

  // ========================================
  // Events CRUD
  // ========================================

  getEvents(params?: EventsQueryParams): Observable<ApiResponse<ApiEvent>> {
    return this.get<ApiResponse<ApiEvent>>('/events', params);
  }

  getEvent(eventId: number): Observable<ApiEvent> {
    return this.get<ApiEvent>(`/events/${eventId}`);
  }

  getEventsByRange(start: string, end: string): Observable<ApiEvent[]> {
    return this.get<ApiEvent[]>('/events/range', { start, end });
  }

  getDeliveryNoteTemplates(): Observable<DeliveryNoteTemplate[]> {
    return this.get<DeliveryNoteTemplate[]>('/events/delivery-note-templates');
  }

  createEvent(event: EventCreate): Observable<ApiEvent> {
    return this.post<ApiEvent>('/events', event);
  }

  updateEvent(eventId: number, event: EventUpdate): Observable<ApiEvent> {
    return this.put<ApiEvent>(`/events/${eventId}`, event);
  }

  updateEventStatus(eventId: number, status: EventStatusUpdate): Observable<ApiEvent> {
    return this.patch<ApiEvent>(`/events/${eventId}/status`, status);
  }

  /** Update final price and recalculate discount */
  updateEventPrice(eventId: number, finalPrice: number): Observable<ApiEvent> {
    const data: EventPriceUpdate = { final_price: finalPrice };
    return this.patch<ApiEvent>(`/events/${eventId}/price`, data);
  }

  deleteEvent(eventId: number): Observable<void> {
    return this.delete<void>(`/events/${eventId}`);
  }

  // ========================================
  // Event Dishes - כולל draft ו-snapshot
  // ========================================

  /** הוספת מנה לאירוע - נשמרת מיד (ללא מצב ביניים של טיוטה) */
  addDishToEvent(eventId: number, dishData: EventDishCreate): Observable<ApiEvent> {
    return this.post<ApiEvent>(`/events/${eventId}/dishes`, dishData);
  }

  /** שמירה מרובה של מנות */
  bulkSaveDishes(eventId: number, dishes: EventDishCreate[], replace: boolean = false): Observable<{ message: string; success: boolean; count: number }> {
    return this.post<{ message: string; success: boolean; count: number }>(`/events/${eventId}/dishes/bulk`, { dishes, replace });
  }

  /** אישור סופי של מנות - לוכד snapshot prices */
  finalizeDishes(eventId: number): Observable<{ message: string }> {
    return this.post<{ message: string }>(`/events/${eventId}/dishes/finalize`, {});
  }

  updateEventDish(eventId: number, dishId: number, data: {
    serving_mode?: "personal" | "central" | null;
    quantity?: number;
    notes?: string;
    is_upgrade?: boolean;
    is_gift?: boolean;
    extra_charge?: number;
  }, eventDishId?: number): Observable<ApiEvent> {
    const query = eventDishId == null ? '' : `?event_dish_id=${eventDishId}`;
    return this.put<ApiEvent>(`/events/${eventId}/dishes/${dishId}${query}`, data);
  }

  removeDishFromEvent(eventId: number, dishId: number): Observable<void> {
    return this.delete<void>(`/events/${eventId}/dishes/${dishId}`);
  }

  // ========================================
  // Morning Split (שבת)
  // ========================================

  toggleMorningSplit(eventId: number, isSplit: boolean): Observable<ApiEvent> {
    return this.patch<ApiEvent>(`/events/${eventId}/morning-split`, { is_morning_split: isSplit });
  }

  // ========================================
  // Event Lists
  // ========================================

  getShoppingList(eventId: number): Observable<ShoppingListResponse> {
    return this.get<ShoppingListResponse>(`/events/${eventId}/shopping-list`);
  }

  getEquipmentList(eventId: number): Observable<EquipmentListResponse> {
    return this.get<EquipmentListResponse>(`/events/${eventId}/equipment-list`);
  }

  // ========================================
  // PDF למלצרים
  // ========================================

  printWaiterInstructions(eventId: number): void {
    const url = `${environment.apiUrl}/events/${eventId}/waiter-pdf`;
    window.open(url, '_blank');
  }

  getWaiterPdfUrl(eventId: number): string {
    return `${environment.apiUrl}/events/${eventId}/waiter-pdf`;
  }

  // ========================================
  // PDF לבעלי קייטרינג
  // ========================================

  printCateringPdf(eventId: number): void {
    const url = `${environment.apiUrl}/events/${eventId}/catering-pdf`;
    window.open(url, '_blank');
  }

  getCateringPdfUrl(eventId: number): string {
    return `${environment.apiUrl}/events/${eventId}/catering-pdf`;
  }

  // ========================================
  // PDF רשימת קניות
  // ========================================

  printShoppingPdf(eventId: number): void {
    const url = `${environment.apiUrl}/events/${eventId}/shopping-pdf`;
    window.open(url, '_blank');
  }

  getShoppingPdfUrl(eventId: number): string {
    return `${environment.apiUrl}/events/${eventId}/shopping-pdf`;
  }

  getCalculationSummary(eventId: number): Observable<EventCalculationSummary> {
    return this.get<EventCalculationSummary>(`/events/${eventId}/calculations/summary`);
  }

  updateCalculationSettings(eventId: number, settings: EventCalculationSettings): Observable<EventCalculationSummary> {
    return this.put<EventCalculationSummary>(`/events/${eventId}/calculations/settings`, settings);
  }

  recalculateEvent(eventId: number): Observable<EventCalculationSummary> {
    return this.post<EventCalculationSummary>(`/events/${eventId}/calculations/recalculate`, {});
  }

  getDishServingSelections(eventId: number): Observable<Array<{dish_id: number; set_type: string; set_id: number}>> {
    return this.get<Array<{dish_id: number; set_type: string; set_id: number}>>(`/events/${eventId}/calculations/dish-serving-selections`);
  }

  updateDishServingSelections(eventId: number, selections: unknown[]): Observable<EventCalculationSummary> {
    return this.put<EventCalculationSummary>(`/events/${eventId}/calculations/dish-serving-selections`, { selections });
  }

  getManualTools(eventId: number): Observable<Array<{tool_id?: number | null; name?: string; quantity: number; is_reusable: boolean; notes?: string}>> {
    return this.get(`/events/${eventId}/calculations/manual-tools`);
  }

  updateManualTools(eventId: number, rows: unknown[]): Observable<EventCalculationSummary> {
    return this.put<EventCalculationSummary>(`/events/${eventId}/calculations/manual-tools`, { rows });
  }

  printReturnSheetPdf(eventId: number): void {
    window.open(`${environment.apiUrl}/events/${eventId}/return-sheet/pdf`, '_blank');
  }

  printDeliverySheetPdf(eventId: number): void {
    const url = `${environment.apiUrl}/events/${eventId}/delivery-sheet/pdf`;
    window.open(url, '_blank');
  }
}
