import { Injectable } from '@angular/core';
import { Observable, BehaviorSubject } from 'rxjs';
import { map, tap } from 'rxjs/operators';
import { BaseApiService } from '../core/services/base-api.service';
import { 
  LookupData,
  LookupValue,
  ApiResponse
} from '../core/models/api.models';

// Interface matching actual server response
export interface ServerLookupData {
  dish_categories: string[];
  kosher_types: string[];
  measurement_units: string[];
  product_categories: string[];
  inventory_statuses: string[];
  event_types: string[];
  event_statuses: string[];
  tool_categories: string[];
  tool_sub_categories: string[];
}

interface LookupSnapshot {
  eventTypes: string[];
  kosherTypes: string[];
  dishCategories: string[];
  units: string[];
  productCategories: string[];
  inventoryStatuses: string[];
  eventStatuses: string[];
  toolCategories: string[];
  toolSubCategories: string[];
}

@Injectable({
  providedIn: 'root'
})
export class ApiLookupService extends BaseApiService {
  private _lookupSubject = new BehaviorSubject<LookupSnapshot>({
    eventTypes: ['שבת', 'שבע ברכות', 'ברית', 'בוקר', 'אחר'],
    kosherTypes: ['חלבי', 'בשרי', 'פרווה'],
    dishCategories: ['עיקרית', 'ראשונה', 'תוספת', 'קינוח', 'משקה', 'חטיף'],
    units: ['גרם', 'ליטר', 'יחידות', 'כפות', 'כוסות', 'מ"ל', 'ק"ג'],
    productCategories: [],
    inventoryStatuses: ['במלאי', 'אזל', 'מלאי-נמוך'],
    eventStatuses: [],
    toolCategories: [],
    toolSubCategories: []
  });

  // Observable for components to subscribe to
  lookup$ = this._lookupSubject.asObservable();

  // Get all lookup data - returns the actual server format
  getAllLookupData(): Observable<ServerLookupData> {
    return this.get<ServerLookupData>('/lookup').pipe(
      tap((data: ServerLookupData) => {
        // Update the behavior subject with actual data when available
        const snapshot: LookupSnapshot = {
          eventTypes: data.event_types || this._lookupSubject.value.eventTypes,
          kosherTypes: data.kosher_types || this._lookupSubject.value.kosherTypes,
          dishCategories: data.dish_categories || this._lookupSubject.value.dishCategories,
          units: data.measurement_units || this._lookupSubject.value.units,
          productCategories: data.product_categories || this._lookupSubject.value.productCategories,
          inventoryStatuses: data.inventory_statuses || this._lookupSubject.value.inventoryStatuses,
          eventStatuses: data.event_statuses || this._lookupSubject.value.eventStatuses,
          toolCategories: data.tool_categories || this._lookupSubject.value.toolCategories,
          toolSubCategories: data.tool_sub_categories || this._lookupSubject.value.toolSubCategories
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

  // Get specific category - returns string array from cached data
  getLookupCategory(category: string): Observable<string[]> {
    // Map category names to snapshot keys
    const categoryMap: { [key: string]: keyof LookupSnapshot } = {
      'dish_categories': 'dishCategories',
      'kosher_types': 'kosherTypes',
      'measurement_units': 'units',
      'units': 'units',
      'product_categories': 'productCategories',
      'inventory_statuses': 'inventoryStatuses',
      'event_types': 'eventTypes',
      'event_statuses': 'eventStatuses',
      'tool_categories': 'toolCategories',
      'tool_sub_categories': 'toolSubCategories'
    };

    const snapshotKey = categoryMap[category];
    if (snapshotKey) {
      return this.lookup$.pipe(
        map(snapshot => snapshot[snapshotKey] as string[])
      );
    }

    // Fallback to empty array for unknown categories
    return new BehaviorSubject<string[]>([]).asObservable();
  }

  // Add new lookup value - Backend expects { value: string }
  addLookupValue(category: string, value: string): Observable<{ message: string; success: boolean }> {
    return this.post<{ message: string; success: boolean }>(`/lookup/${category}`, { value });
  }

  // Update lookup value - Backend uses index, not id
  updateLookupValue(category: string, index: number, value: string): Observable<{ message: string; success: boolean }> {
    return this.put<{ message: string; success: boolean }>(`/lookup/${category}/${index}`, { value });
  }

  // Delete lookup value - Backend uses index, not id
  deleteLookupValue(category: string, index: number): Observable<void> {
    return this.delete<void>(`/lookup/${category}/${index}`);
  }

  // Convenience methods for common lookups - return string arrays
  getEventTypes(): Observable<string[]> {
    return this.getLookupCategory('event_types');
  }

  getEventStatuses(): Observable<string[]> {
    return this.getLookupCategory('event_statuses');
  }

  getDishCategories(): Observable<string[]> {
    return this.getLookupCategory('dish_categories');
  }

  getKosherTypes(): Observable<string[]> {
    return this.getLookupCategory('kosher_types');
  }

  getProductCategories(): Observable<string[]> {
    return this.getLookupCategory('product_categories');
  }

  getToolCategories(): Observable<string[]> {
    return this.getLookupCategory('tool_categories');
  }

  getUnits(): Observable<string[]> {
    return this.getLookupCategory('measurement_units');
  }

  getInventoryStatuses(): Observable<string[]> {
    return this.getLookupCategory('inventory_statuses');
  }
}