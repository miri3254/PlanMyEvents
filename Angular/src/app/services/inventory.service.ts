import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import type { ScannedItem } from '../components/receipt-scan-dialog/receipt-scan-dialog.types';

export interface InventoryProduct {
  id: number;
  name: string;
  stock: number;
}

@Injectable({
  providedIn: 'root'
})
export class InventoryService {
  private readonly apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  /**
   * Get all products with their current stock levels
   * @returns Observable of inventory products
   */
  getProducts(): Observable<InventoryProduct[]> {
    return this.http.get<InventoryProduct[]>(`${this.apiUrl}/receipts/products/inventory`);
  }

  /**
   * Bulk update inventory from scanned receipt items
   * @param items Scanned items to update
   * @returns Observable of update result
   */
  bulkUpdate(items: ScannedItem[]): Observable<void> {
    return this.http.post<void>(`${this.apiUrl}/receipts/inventory/bulk-update`, { items });
  }
}
