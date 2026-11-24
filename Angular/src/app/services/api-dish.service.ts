import { WorkbookPreset } from '../core/models/api.models';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { BaseApiService } from '../core/services/base-api.service';
import {
  ApiDish,
  DishCreate,
  DishUpdate,
  DishIngredient,
  DishEquipment,
  DishServingDish,
  DishesQueryParams,
  ApiResponse,
  DishServingSet,
  DishCalculationRule
} from '../core/models/api.models';

@Injectable({
  providedIn: 'root'
})
export class ApiDishService extends BaseApiService {

  // ========================================
  // Dishes CRUD
  // ========================================

  getDishes(params?: DishesQueryParams): Observable<ApiResponse<ApiDish>> {
    return this.get<ApiResponse<ApiDish>>('/dishes', params);
  }

  getDish(dishId: number): Observable<ApiDish> {
    return this.get<ApiDish>(`/dishes/${dishId}`);
  }

  createDish(dish: DishCreate): Observable<ApiDish> {
    return this.post<ApiDish>('/dishes', dish);
  }

  updateDish(dishId: number, dish: DishUpdate): Observable<ApiDish> {
    return this.put<ApiDish>(`/dishes/${dishId}`, dish);
  }

  toggleDishActive(dishId: number, isActive: { is_active: boolean }): Observable<ApiDish> {
    return this.patch<ApiDish>(`/dishes/${dishId}/active`, isActive);
  }

  deleteDish(dishId: number): Observable<void> {
    return this.delete<void>(`/dishes/${dishId}`);
  }

  // ========================================
  // Dish Ingredients - עם is_serving_component
  // ========================================

  addIngredient(dishId: number, ingredient: {
    product_id?: number;
    quantity: number | null;
    unit: string | null;
    name?: string;
    is_serving_component?: boolean;
    note?: string | null;
  }): Observable<DishIngredient> {
    return this.post<DishIngredient>(`/dishes/${dishId}/ingredients`, ingredient);
  }

  updateIngredient(
    dishId: number,
    ingredientId: number,
    ingredient: {
      quantity?: number | null;
      unit?: string | null;
      product_id?: number;
      name?: string;
      is_serving_component?: boolean;
      note?: string | null;
    }
  ): Observable<DishIngredient> {
    return this.put<DishIngredient>(`/dishes/${dishId}/ingredients/${ingredientId}`, ingredient);
  }

  removeIngredient(dishId: number, ingredientId: number): Observable<void> {
    return this.delete<void>(`/dishes/${dishId}/ingredients/${ingredientId}`);
  }

  // ========================================
  // Dish Equipment
  // ========================================

  addEquipment(dishId: number, equipment: { tool_id: number; quantity: number; name?: string }): Observable<DishEquipment> {
    return this.post<DishEquipment>(`/dishes/${dishId}/equipment`, equipment);
  }

  updateEquipment(dishId: number, equipmentId: number, equipment: { quantity?: number; name?: string; tool_id?: number }): Observable<DishEquipment> {
    return this.put<DishEquipment>(`/dishes/${dishId}/equipment/${equipmentId}`, equipment);
  }

  removeEquipment(dishId: number, equipmentId: number): Observable<void> {
    return this.delete<void>(`/dishes/${dishId}/equipment/${equipmentId}`);
  }

  // ========================================
  // Serving Dishes
  // ========================================

  addServingDish(dishId: number, servingDish: { tool_id?: number; name?: string; quantity: number }): Observable<DishServingDish> {
    return this.post<DishServingDish>(`/dishes/${dishId}/serving-dishes`, servingDish);
  }

  updateServingDish(dishId: number, servingDishId: number, servingDish: { name?: string; quantity?: number; tool_id?: number }): Observable<DishServingDish> {
    return this.put<DishServingDish>(`/dishes/${dishId}/serving-dishes/${servingDishId}`, servingDish);
  }

  removeServingDish(dishId: number, servingDishId: number): Observable<void> {
    return this.delete<void>(`/dishes/${dishId}/serving-dishes/${servingDishId}`);
  }

  getWorkbookPresets(): Observable<WorkbookPreset[]> {
    return this.get<WorkbookPreset[]>('/dishes/calculation-presets');
  }

  getServingSets(dishId: number): Observable<DishServingSet[]> {
    return this.get<DishServingSet[]>(`/dishes/${dishId}/serving-sets`);
  }

  saveServingSet(dishId: number, set: DishServingSet): Observable<DishServingSet> {
    return set.id
      ? this.put<DishServingSet>(`/dishes/${dishId}/serving-sets/${set.id}`, set)
      : this.post<DishServingSet>(`/dishes/${dishId}/serving-sets`, set);
  }

  deleteServingSet(dishId: number, setId: number): Observable<void> {
    return this.delete<void>(`/dishes/${dishId}/serving-sets/${setId}`);
  }

  getCalculationRules(dishId: number): Observable<DishCalculationRule[]> {
    return this.get<DishCalculationRule[]>(`/dishes/${dishId}/calculation-rules`);
  }

  saveCalculationRule(dishId: number, rule: DishCalculationRule): Observable<DishCalculationRule> {
    return rule.id
      ? this.put<DishCalculationRule>(`/dishes/${dishId}/calculation-rules/${rule.id}`, rule)
      : this.post<DishCalculationRule>(`/dishes/${dishId}/calculation-rules`, rule);
  }

  deleteCalculationRule(dishId: number, ruleId: number): Observable<void> {
    return this.delete<void>(`/dishes/${dishId}/calculation-rules/${ruleId}`);
  }
}
