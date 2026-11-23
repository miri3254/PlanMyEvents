import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { BaseApiService } from '../core/services/base-api.service';
import { 
  ApiProduct, 
  ProductCreate, 
  ProductUpdate,
  ProductsQueryParams,
  ApiResponse
} from '../core/models/api.models';

@Injectable({
  providedIn: 'root'
})
export class ApiProductService extends BaseApiService {

  // Products CRUD
  getProducts(params?: ProductsQueryParams): Observable<ApiResponse<ApiProduct>> {
    return this.get<ApiResponse<ApiProduct>>('/products', params);
  }

  getProduct(productId: number): Observable<ApiProduct> {
    return this.get<ApiProduct>(`/products/${productId}`);
  }

  createProduct(product: ProductCreate): Observable<ApiProduct> {
    return this.post<ApiProduct>('/products', product);
  }

  updateProduct(productId: number, product: ProductUpdate): Observable<ApiProduct> {
    return this.put<ApiProduct>(`/products/${productId}`, product);
  }

  deleteProduct(productId: number): Observable<void> {
    return this.delete<void>(`/products/${productId}`);
  }

  // Bulk Operations
  createMultipleProducts(products: ProductCreate[]): Observable<{ message: string; success: boolean; count: number }> {
    return this.post<{ message: string; success: boolean; count: number }>('/products/bulk', products);
  }

  deleteMultipleProducts(productIds: number[]): Observable<{ message: string; deleted_count: number; success: boolean }> {
    return this.delete<{ message: string; deleted_count: number; success: boolean }>(`/products/bulk?ids=${productIds.join(',')}`);
  }
}
