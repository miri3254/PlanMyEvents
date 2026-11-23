import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { BaseApiService } from '../core/services/base-api.service';
import {
  MenuTemplate,
  MenuTemplateCreate,
  MenuTemplateUpdate,
  MenuCategory,
  MenuCategoryCreate,
  MenuCategoryUpdate,
  DishMenuMapping,
  DishMenuMappingCreate,
  CategoryDishesResponse
} from '../models/menu.model';

@Injectable({
  providedIn: 'root'
})
export class ApiMenuService extends BaseApiService {

  // ========================================
  // Menu Templates CRUD
  // ========================================

  getMenuTemplates(): Observable<MenuTemplate[]> {
    return this.get<MenuTemplate[]>('/menus');
  }

  getMenuByType(menuType: string): Observable<MenuTemplate> {
    return this.get<MenuTemplate>(`/menus/by-type/${encodeURIComponent(menuType)}`);
  }

  getMenuTemplate(templateId: number): Observable<MenuTemplate> {
    return this.get<MenuTemplate>(`/menus/${templateId}`);
  }

  createMenuTemplate(template: MenuTemplateCreate): Observable<MenuTemplate> {
    return this.post<MenuTemplate>('/menus', template);
  }

  updateMenuTemplate(templateId: number, template: MenuTemplateUpdate): Observable<MenuTemplate> {
    return this.put<MenuTemplate>(`/menus/${templateId}`, template);
  }

  deleteMenuTemplate(templateId: number): Observable<void> {
    return this.delete<void>(`/menus/${templateId}`);
  }

  // ========================================
  // Menu Categories
  // ========================================

  /** כל הקטגוריות מקובצות לפי תפריט - לטאב שיוך מנות */
  getAllCategoriesGrouped(): Observable<any[]> {
    return this.get<any[]>('/menus/categories/all');
  }

  createCategory(category: MenuCategoryCreate): Observable<MenuCategory> {
    return this.post<MenuCategory>('/menus/categories', category);
  }

  updateCategory(categoryId: number, category: MenuCategoryUpdate): Observable<MenuCategory> {
    return this.put<MenuCategory>(`/menus/categories/${categoryId}`, category);
  }

  deleteCategory(categoryId: number): Observable<void> {
    return this.delete<void>(`/menus/categories/${categoryId}`);
  }

  /** קבלת מנות בקטגוריה - כולל הפרדה בין רגילות לשדרוגים */
  getCategoryDishes(categoryId: number): Observable<CategoryDishesResponse> {
    return this.get<CategoryDishesResponse>(`/menus/categories/${categoryId}/dishes`);
  }

  /** וולידציה של בחירה מול מכסה */
  validateSelection(categoryId: number, selectedDishIds: number[]): Observable<{ valid: boolean; message?: string }> {
    return this.post<{ valid: boolean; message?: string }>(`/menus/categories/${categoryId}/validate`, { dish_ids: selectedDishIds });
  }

  // ========================================
  // Sub-Meals CRUD
  // ========================================

  getSubMeal(subMealId: number): Observable<any> {
    return this.get<any>(`/menus/sub-meals/${subMealId}`);
  }

  createSubMeal(subMeal: {
    template_id: number;
    name: string;
    display_order?: number;
    is_splittable?: boolean;
    split_extra_charge?: number | null;
  }): Observable<any> {
    return this.post<any>('/menus/sub-meals', subMeal);
  }

  updateSubMeal(subMealId: number, subMeal: Partial<{
    name: string;
    display_order: number;
    is_splittable: boolean;
    split_extra_charge: number | null;
  }>): Observable<any> {
    return this.put<any>(`/menus/sub-meals/${subMealId}`, subMeal);
  }

  deleteSubMeal(subMealId: number): Observable<void> {
    return this.delete<void>(`/menus/sub-meals/${subMealId}`);
  }

  // ========================================
  // Dish-Menu Mappings
  // ========================================

  addDishToCategory(mapping: DishMenuMappingCreate): Observable<DishMenuMapping> {
    return this.post<DishMenuMapping>('/menus/dish-mappings', mapping);
  }

  updateDishMapping(mappingId: number, mapping: Partial<DishMenuMappingCreate>): Observable<DishMenuMapping> {
    return this.put<DishMenuMapping>(`/menus/dish-mappings/${mappingId}`, mapping);
  }

  removeDishFromCategory(mappingId: number): Observable<void> {
    return this.delete<void>(`/menus/dish-mappings/${mappingId}`);
  }
}
