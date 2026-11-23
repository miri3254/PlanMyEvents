import { Injectable } from '@angular/core';
import { Observable, BehaviorSubject, of } from 'rxjs';
import { map, tap, take, catchError } from 'rxjs/operators';
import { BaseApiService } from '../core/services/base-api.service';
import {
  // DEFAULT_MENU_TYPES,
  KOSHER_TYPES,
  UNIT_TYPES,
  PRODUCT_CATEGORIES,
  INVENTORY_STATUSES,
  EVENT_STATUSES,
  TOOL_CATEGORIES,
  TOOL_SUB_CATEGORIES
} from '../core/models/enums';

// Interface matching actual server response
export interface ServerLookupData {
  event_categories: string[];
  kosher_types: string[];
  measurement_units: string[];
  product_categories: string[];
  inventory_statuses: string[];
  event_statuses: string[];
  tool_categories: string[];
  tool_sub_categories: string[];
}

interface LookupSnapshot {
  eventCategories: string[];
  kosherTypes: string[];
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
  // ברירות מחדל - יתעדכנו מהשרת (תפריטים דינמיים!)
  private _lookupSubject = new BehaviorSubject<LookupSnapshot>({
    eventCategories: [],
    kosherTypes: [...KOSHER_TYPES],
    units: [...UNIT_TYPES],
    productCategories: [...PRODUCT_CATEGORIES],
    inventoryStatuses: [...INVENTORY_STATUSES],
    eventStatuses: [...EVENT_STATUSES],
    toolCategories: [...TOOL_CATEGORIES],
    toolSubCategories: [...TOOL_SUB_CATEGORIES]
  });

  lookup$ = this._lookupSubject.asObservable();

  // Get all lookup data from server
  getAllLookupData(): Observable<ServerLookupData> {
    return this.get<ServerLookupData>('/lookup').pipe(
      tap((data: ServerLookupData) => {
        const snapshot: LookupSnapshot = {
          eventCategories: data.event_categories || [],
          kosherTypes: data.kosher_types || this._lookupSubject.value.kosherTypes,
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

  initializeLookupData(): void {
    this.getAllLookupData().subscribe({
      error: (error) => {
        console.warn('Failed to load lookup data, using defaults:', error);
      }
    });
  }

  getLookupCategory(category: string): Observable<string[]> {
    const categoryMap: { [key: string]: keyof LookupSnapshot } = {
      'event_categories': 'eventCategories',
      // 'menu_types': 'menuTypes',
      'kosher_types': 'kosherTypes',
      'measurement_units': 'units',
      'units': 'units',
      'product_categories': 'productCategories',
      'inventory_statuses': 'inventoryStatuses',
      'event_statuses': 'eventStatuses',
      'tool_categories': 'toolCategories',
      'tool_sub_categories': 'toolSubCategories'
    };

    const snapshotKey = categoryMap[category];
    if (snapshotKey) {
      return this.lookup$.pipe(
        take(1),
        map(snapshot => snapshot[snapshotKey] as string[])
      );
    }

    return of([]);
  }

  // CRUD operations for lookup values
  addLookupValue(category: string, value: string): Observable<{ message: string; success: boolean }> {
    return this.post<{ message: string; success: boolean }>(`/lookup/${category}`, { value });
  }

  updateLookupValue(category: string, index: number, value: string): Observable<{ message: string; success: boolean }> {
    return this.put<{ message: string; success: boolean }>(`/lookup/${category}/${index}`, { value });
  }

  deleteLookupValue(category: string, index: number): Observable<void> {
    return this.delete<void>(`/lookup/${category}/${index}`);
  }

  // Convenience methods
  getMenuTypes(): Observable<string[]> { return this.getLookupCategory('menu_types'); }
  getEventCategories(): Observable<string[]> { return this.getLookupCategory('event_categories'); }
  getEventStatuses(): Observable<string[]> { return this.getLookupCategory('event_statuses'); }
  getKosherTypes(): Observable<string[]> { return this.getLookupCategory('kosher_types'); }
  getProductCategories(): Observable<string[]> { return this.getLookupCategory('product_categories'); }
  getToolCategories(): Observable<string[]> { return this.getLookupCategory('tool_categories'); }
  getUnits(): Observable<string[]> { return this.getLookupCategory('measurement_units'); }
  getInventoryStatuses(): Observable<string[]> { return this.getLookupCategory('inventory_statuses'); }
}
