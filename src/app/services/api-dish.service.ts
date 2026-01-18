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
  ApiResponse
} from '../core/models/api.models';

@Injectable({
  providedIn: 'root'
})
export class ApiDishService extends BaseApiService {

  // Dishes CRUD
  getDishes(params?: DishesQueryParams): Observable<ApiResponse<ApiDish>> {
    return this.get<ApiResponse<ApiDish>>('/dishes', params);
  }

  getDish(dishId: string): Observable<ApiDish> {
    return this.get<ApiDish>(`/dishes/${dishId}`);
  }

  createDish(dish: DishCreate): Observable<ApiDish> {
    return this.post<ApiDish>('/dishes', dish);
  }

  updateDish(dishId: string, dish: DishUpdate): Observable<ApiDish> {
    return this.put<ApiDish>(`/dishes/${dishId}`, dish);
  }

  toggleDishActive(dishId: string, isActive: { is_active: boolean }): Observable<ApiDish> {
    return this.patch<ApiDish>(`/dishes/${dishId}/active`, isActive);
  }

  deleteDish(dishId: string): Observable<void> {
    return this.delete<void>(`/dishes/${dishId}`);
  }

  // Dish Ingredients
  addIngredient(dishId: string, ingredient: { product_id: string; quantity: number; unit: string }): Observable<DishIngredient> {
    return this.post<DishIngredient>(`/dishes/${dishId}/ingredients`, ingredient);
  }

  updateIngredient(dishId: string, ingredientId: string, ingredient: { quantity: number; unit: string }): Observable<DishIngredient> {
    return this.put<DishIngredient>(`/dishes/${dishId}/ingredients/${ingredientId}`, ingredient);
  }

  removeIngredient(dishId: string, ingredientId: string): Observable<void> {
    return this.delete<void>(`/dishes/${dishId}/ingredients/${ingredientId}`);
  }

  // Dish Equipment
  addEquipment(dishId: string, equipment: { tool_id: string; quantity: number }): Observable<DishEquipment> {
    return this.post<DishEquipment>(`/dishes/${dishId}/equipment`, equipment);
  }

  updateEquipment(dishId: string, equipmentId: string, equipment: { quantity: number }): Observable<DishEquipment> {
    return this.put<DishEquipment>(`/dishes/${dishId}/equipment/${equipmentId}`, equipment);
  }

  removeEquipment(dishId: string, equipmentId: string): Observable<void> {
    return this.delete<void>(`/dishes/${dishId}/equipment/${equipmentId}`);
  }

  // Serving Dishes
  addServingDish(dishId: string, servingDish: { tool_id: string; quantity: number }): Observable<DishServingDish> {
    return this.post<DishServingDish>(`/dishes/${dishId}/serving-dishes`, servingDish);
  }

  updateServingDish(dishId: string, servingDishId: string, servingDish: { quantity: number }): Observable<DishServingDish> {
    return this.put<DishServingDish>(`/dishes/${dishId}/serving-dishes/${servingDishId}`, servingDish);
  }

  removeServingDish(dishId: string, servingDishId: string): Observable<void> {
    return this.delete<void>(`/dishes/${dishId}/serving-dishes/${servingDishId}`);
  }
}