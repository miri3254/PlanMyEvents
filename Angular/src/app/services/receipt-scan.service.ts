import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import type { ExistingProduct, ScannedItem } from '../components/receipt-scan-dialog/receipt-scan-dialog.types';

interface ScanRequestBody {
  images: string[];
  existing_products: any[];
}

interface ScanResponseItem {
  matched_product_id: number | null;
  name: string;
  quantity: number;
  unit_price: number;
  is_new: boolean;
  current_stock: number;
}

interface ScanResponse {
  items: ScanResponseItem[];
}

@Injectable({
  providedIn: 'root'
})
export class ReceiptScanService {
  private readonly apiUrl = `${environment.apiUrl}/receipts/scan`;

  constructor(private http: HttpClient) {}

  /**
   * Scans receipt images using AI and returns matched/new product items
   * @param images Base64 encoded images of receipt pages
   * @param existingProducts List of existing products for matching
   * @returns Observable of ScannedItem array
   */
  scan(images: string[], existingProducts: ExistingProduct[]): Observable<ScannedItem[]> {
    const body: ScanRequestBody = {
      images,
      existing_products: existingProducts
    };

    // TODO: POST to /api/receipts/scan - update endpoint as needed
    return this.http.post<ScanResponse>(this.apiUrl, body).pipe(
      map((response) => this.mapResponseToScannedItems(response.items))
    );
  }

  private mapResponseToScannedItems(items: ScanResponseItem[]): ScannedItem[] {
    return items.map((item) => ({
      matched_product_id: item.matched_product_id,
      name: item.name,
      edited_name: item.name, // Initialize edited_name with original name
      quantity: item.quantity,
      unit_price: item.unit_price,
      is_new: item.is_new,
      current_stock: item.current_stock,
      nameMatchLoading: false
    }));
  }
}
