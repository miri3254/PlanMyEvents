import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { BaseApiService } from './base-api.service';
import { UnitConversion, ConversionResult } from '../models';

export interface UnitConversionCreate {
  fromUnit: string;
  toUnit: string;
  factor: number;
  description?: string;
}

export interface UnitConversionUpdate {
  factor?: number;
  description?: string;
}

export interface UnitConversionsResponse {
  items: UnitConversion[];
  total: number;
}

@Injectable({
  providedIn: 'root'
})
export class UnitConversionService extends BaseApiService {
  private readonly endpoint = '/unit-conversions';

  /**
   * Get all unit conversions (system and user-defined)
   */
  getAll(): Observable<UnitConversionsResponse> {
    return this.get<UnitConversionsResponse>(this.endpoint);
  }

  /**
   * Get a specific unit conversion by ID
   */
  getById(id: number): Observable<UnitConversion> {
    return this.get<UnitConversion>(`${this.endpoint}/${id}`);
  }

  /**
   * Create a new user-defined unit conversion
   */
  create(data: UnitConversionCreate): Observable<UnitConversion> {
    const payload = {
      from_unit: data.fromUnit,
      to_unit: data.toUnit,
      factor: data.factor,
      description: data.description
    };
    return this.post<UnitConversion>(this.endpoint, payload);
  }

  /**
   * Update a user-defined unit conversion
   * Note: System conversions cannot be updated
   */
  update(id: number, data: UnitConversionUpdate): Observable<UnitConversion> {
    return this.put<UnitConversion>(`${this.endpoint}/${id}`, data);
  }

  /**
   * Delete a user-defined unit conversion
   * Note: System conversions cannot be deleted
   */
  remove(id: number): Observable<{ message: string }> {
    return this.delete<{ message: string }>(`${this.endpoint}/${id}`);
  }

  /**
   * Calculate a unit conversion
   */
  calculate(value: number, fromUnit: string, toUnit: string): Observable<ConversionResult> {
    return this.post<ConversionResult>(`${this.endpoint}/calculate`, {
      value,
      from_unit: fromUnit,
      to_unit: toUnit,
    });
  }

  /**
   * Seed system conversions (admin use only)
   */
  seedConversions(): Observable<{ message: string; count: number }> {
    return this.post<{ message: string; count: number }>(`${this.endpoint}/seed`, {});
  }
}
