import { Injectable } from '@angular/core';
import { Observable, BehaviorSubject } from 'rxjs';
import { map, tap } from 'rxjs/operators';
import { BaseApiService } from '../core/services/base-api.service';
import { 
  LookupData,
  LookupValue,
  ApiResponse
} from '../core/models/api.models';

interface LookupSnapshot {
  eventTypes: string[];
  kosherTypes: string[];
}

@Injectable({
  providedIn: 'root'
})
export class ApiLookupService extends BaseApiService {
  private _lookupSubject = new BehaviorSubject<LookupSnapshot>({
    eventTypes: ['אירוע', 'שבת', 'חתונה'],
    kosherTypes: ['חלבי', 'בשרי', 'פרווה']
  });

  // Observable for components to subscribe to
  lookup$ = this._lookupSubject.asObservable();

  // Get all lookup data
  getAllLookupData(): Observable<LookupData> {
    return this.get<LookupData>('/lookup').pipe(
      tap((data: any) => {
        // Update the behavior subject with actual data when available
        const snapshot: LookupSnapshot = {
          eventTypes: data.eventTypes || ['אירוע', 'שבת', 'חתונה'],
          kosherTypes: data.kosherTypes || ['חלבי', 'בשרי', 'פרווה']
        };
        this._lookupSubject.next(snapshot);
      })
    );
  }

  // Initialize lookup data (call this in app initialization)
  initializeLookupData(): void {
    this.getAllLookupData().subscribe({
      error: (error) => {
        console.warn('Failed to load lookup data, using defaults:', error);
      }
    });
  }

  // Get specific category
  getLookupCategory(category: string): Observable<LookupValue[]> {
    return this.get<LookupValue[] | ApiResponse<LookupValue>>(`/lookup/${category}`).pipe(
      map((response: LookupValue[] | ApiResponse<LookupValue>) => {
        if (Array.isArray(response)) {
          return response;
        }

        if (response && Array.isArray((response as ApiResponse<LookupValue>).items)) {
          return (response as ApiResponse<LookupValue>).items;
        }

        // Fallback to an empty array when the payload is unexpected
        return [];
      })
    );
  }

  // Add new lookup value
  addLookupValue(category: string, value: { name: string; display_name: string; is_active?: boolean; sort_order?: number }): Observable<LookupValue> {
    return this.post<LookupValue>(`/lookup/${category}`, value);
  }

  // Update lookup value
  updateLookupValue(category: string, valueId: string, value: { display_name?: string; is_active?: boolean; sort_order?: number }): Observable<LookupValue> {
    return this.put<LookupValue>(`/lookup/${category}/${valueId}`, value);
  }

  // Delete lookup value
  deleteLookupValue(category: string, valueId: string): Observable<void> {
    return this.delete<void>(`/lookup/${category}/${valueId}`);
  }

  // Convenience methods for common lookups
  getEventTypes(): Observable<LookupValue[]> {
    return this.getLookupCategory('event_types');
  }

  getEventStatuses(): Observable<LookupValue[]> {
    return this.getLookupCategory('event_statuses');
  }

  getDishCategories(): Observable<LookupValue[]> {
    return this.getLookupCategory('dish_categories');
  }

  getKosherTypes(): Observable<LookupValue[]> {
    return this.getLookupCategory('kosher_types');
  }

  getProductCategories(): Observable<LookupValue[]> {
    return this.getLookupCategory('product_categories');
  }

  getToolCategories(): Observable<LookupValue[]> {
    return this.getLookupCategory('tool_categories');
  }

  getUnits(): Observable<LookupValue[]> {
    return this.getLookupCategory('units');
  }
}