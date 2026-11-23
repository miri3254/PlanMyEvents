import { ApiToolService } from '../../services/api-tool.service';
import { ApiTool } from '../../core/models/api.models';
import { TableSettingItem } from '../../models/menu.model';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil, take } from 'rxjs';

import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { InputNumberModule } from 'primeng/inputnumber';
import { SelectModule } from 'primeng/select';
import { AutoCompleteModule } from 'primeng/autocomplete';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { TagModule } from 'primeng/tag';
import { CheckboxModule } from 'primeng/checkbox';
import { PanelModule } from 'primeng/panel';
import { TooltipModule } from 'primeng/tooltip';
import { BadgeModule } from 'primeng/badge';
import { DividerModule } from 'primeng/divider';
import { MessageService, ConfirmationService } from 'primeng/api';

import { ApiMenuService } from '../../services/api-menu.service';
import { ApiDishService } from '../../services/api-dish.service';
import {
  MenuTemplate,
  MenuTemplateCreate,
  MenuTemplateUpdate,
  MenuCategory,
  DishMenuMappingCreate
} from '../../models/menu.model';

interface MenuFormModel {
  tableSettingItems?: TableSettingItem[];
  id?: number;
  name: string;
  description: string;
  minGuests: number;
  basePricePerGuest: number | null;
  realDishesExtraPerGuest: number | null;  // תוספת כלים אמיתיים לסועד
  isTrayMenu: boolean;
  kosherType: string;  // בשרי/חלבי/פרווה
}

@Component({
  selector: 'app-menus',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    ButtonModule,
    DialogModule,
    InputTextModule,
    InputNumberModule,
    SelectModule,
    AutoCompleteModule,
    ToastModule,
    ConfirmDialogModule,
    TagModule,
    CheckboxModule,
    PanelModule,
    TooltipModule,
    BadgeModule,
    DividerModule
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './menus.component.html',
  styleUrls: ['./menus.component.scss']
})
export class MenusComponent implements OnInit, OnDestroy {
  menus: MenuTemplate[] = [];
  tableSettingTools: ApiTool[] = [];
  filteredMenus: MenuTemplate[] = [];
  loading = false;

  // Dialog state
  menuFormVisible = false;
  menuFormMode: 'create' | 'edit' = 'create';
  menuForm!: MenuFormModel;
  menuFormSubmitting = false;

  // Detail dialog
  selectedMenu: MenuTemplate | null = null;
  detailVisible = false;

  // Filter
  searchTerm = '';
  selectedFilter: string = 'all';

  // Dish picker state
  dishPickerVisible = false;
  dishPickerCategory: any = null;
  dishPickerSearch = '';
  allDishes: any[] = [];
  filteredPickerDishes: any[] = [];
  selectedPickerDishes: any[] = [];  // Multi-select - dishes selected in picker
  dishPickerSubmitting = false;      // Loading state for adding multiple dishes
  dishEditMap: Record<number, { is_upgrade: boolean; extra_charge: number | null; default_serving_mode: "personal" | "central" | null }> = {};

  // Kosher type options for menu form
  kosherTypeOptions = [
    { label: 'בשרי', value: 'בשרי' },
    { label: 'חלבי', value: 'חלבי' },
    { label: 'פרווה', value: 'פרווה' }
  ];

  // Sub-meal form state
  subMealFormVisible = false;
  subMealFormSubmitting = false;
  subMealForm = {
    name: '',
    displayOrder: 0,
    isSplittable: false,
    splitExtraCharge: null as number | null
  };

  // Category form state
  categoryFormVisible = false;
  categoryFormSubmitting = false;
  categoryForm = {
    name: '',
    nameHebrew: '',
    subMealId: null as number | null,
    quota: null as number | null,
    displayOrder: 0
  };
  subMealsForSelect: { label: string; value: number }[] = [];

  private readonly destroy$ = new Subject<void>();

  constructor(
    private readonly toolService: ApiToolService,
    private readonly menuService: ApiMenuService,
    private readonly dishService: ApiDishService,
    private readonly messageService: MessageService,
    private readonly confirmationService: ConfirmationService
  ) {
    this.menuForm = this.getEmptyForm();
  }

  ngOnInit(): void {
    this.loadMenus();
    this.toolService.getAllTools().pipe(takeUntil(this.destroy$)).subscribe({next: tools => this.tableSettingTools = tools, error: () => this.messageService.add({severity: 'error', summary: 'לא ניתן לטעון את קטלוג הכלים'})});
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadMenus(): void {
    this.loading = true;
    this.menuService.getMenuTemplates()
      .pipe(take(1))
      .subscribe({
        next: (menus) => {
          this.menus = menus;
          this.applyFilter();
          this.loading = false;
        },
        error: (err) => {
          this.messageService.add({
            severity: 'error',
            summary: 'שגיאה',
            detail: 'טעינת תפריטים נכשלה'
          });
          this.loading = false;
        }
      });
  }

  applyFilter(): void {
    let list = [...this.menus];
    if (this.searchTerm?.trim()) {
      const term = this.searchTerm.trim().toLowerCase();
      list = list.filter(m =>
        m.name.toLowerCase().includes(term) ||
        (m.description || '').toLowerCase().includes(term)
      );
    }
    this.filteredMenus = list;
  }

  setFilter(filter: string): void {
    this.selectedFilter = filter;
    this.applyFilter();
  }

  onSearch(): void {
    this.applyFilter();
  }

  // ===== CRUD =====

  openCreateForm(): void {
    this.menuForm = this.getEmptyForm();
    this.menuFormMode = 'create';
    this.menuFormVisible = true;
  }

  openEditForm(menu: MenuTemplate): void {
    this.menuFormMode = 'edit';
    this.menuForm = {
      id: menu.id,
      tableSettingItems: menu.table_setting_items?.map(item => ({ ...item })),
      name: menu.name,
      description: menu.description || '',
      minGuests: menu.min_guests,
      basePricePerGuest: menu.base_price_per_guest ?? null,
      realDishesExtraPerGuest: menu.real_dishes_extra_per_guest ?? null,
      isTrayMenu: menu.is_tray_menu,
      kosherType: menu.kosher_type || 'פרווה'
    };
    this.menuFormVisible = true;
  }

  closeForm(): void {
    this.menuFormVisible = false;
    this.menuForm = this.getEmptyForm();
  }

  submitForm(): void {
    if (!this.isFormValid()) return;

    this.menuFormSubmitting = true;

    if (this.menuFormMode === 'create') {
      const payload: MenuTemplateCreate = {
        table_setting_items: this.menuForm.tableSettingItems,
        name: this.menuForm.name,
        description: this.menuForm.description || undefined,
        min_guests: this.menuForm.minGuests,
        base_price_per_guest: this.menuForm.basePricePerGuest ?? undefined,
        real_dishes_extra_per_guest: this.menuForm.realDishesExtraPerGuest ?? undefined,
        is_tray_menu: this.menuForm.isTrayMenu,
        kosher_type: this.menuForm.kosherType
      };

      this.menuService.createMenuTemplate(payload)
        .pipe(take(1))
        .subscribe({
          next: (created) => {
            this.menus = [created, ...this.menus];
            this.applyFilter();
            this.messageService.add({
              severity: 'success',
              summary: 'תפריט נוצר',
              detail: `${created.name} נוסף בהצלחה`
            });
            this.menuFormSubmitting = false;
            this.closeForm();
          },
          error: (err) => {
            this.messageService.add({
              severity: 'error',
              summary: 'שגיאה',
              detail: err?.message || 'יצירת תפריט נכשלה'
            });
            this.menuFormSubmitting = false;
          }
        });
    } else if (this.menuForm.id) {
      const payload: MenuTemplateUpdate = {
        table_setting_items: this.menuForm.tableSettingItems,
        name: this.menuForm.name,
        description: this.menuForm.description || undefined,
        min_guests: this.menuForm.minGuests,
        base_price_per_guest: this.menuForm.basePricePerGuest ?? undefined,
        real_dishes_extra_per_guest: this.menuForm.realDishesExtraPerGuest ?? undefined,
        is_tray_menu: this.menuForm.isTrayMenu,
        kosher_type: this.menuForm.kosherType
      };

      this.menuService.updateMenuTemplate(this.menuForm.id, payload)
        .pipe(take(1))
        .subscribe({
          next: (updated) => {
            const idx = this.menus.findIndex(m => m.id === updated.id);
            if (idx !== -1) this.menus[idx] = updated;
            this.applyFilter();
            this.messageService.add({
              severity: 'success',
              summary: 'תפריט עודכן',
              detail: `${updated.name} נשמר בהצלחה`
            });
            this.menuFormSubmitting = false;
            this.closeForm();
          },
          error: (err) => {
            this.messageService.add({
              severity: 'error',
              summary: 'שגיאה',
              detail: err?.message || 'עדכון תפריט נכשל'
            });
            this.menuFormSubmitting = false;
          }
        });
    }
  }

  deleteMenu(menu: MenuTemplate): void {
    this.confirmationService.confirm({
      message: `האם למחוק את התפריט "${menu.name}"?`,
      header: 'אישור מחיקה',
      icon: 'pi pi-trash',
      acceptLabel: 'מחק',
      rejectLabel: 'ביטול',
      accept: () => {
        if (!menu.id) return;
        this.menuService.deleteMenuTemplate(menu.id)
          .pipe(take(1))
          .subscribe({
            next: () => {
              this.menus = this.menus.filter(m => m.id !== menu.id);
              this.applyFilter();
              this.messageService.add({
                severity: 'success',
                summary: 'תפריט נמחק',
                detail: `${menu.name} הוסר`
              });
            },
            error: () => {
              this.messageService.add({
                severity: 'error',
                summary: 'שגיאה',
                detail: 'מחיקת תפריט נכשלה'
              });
            }
          });
      }
    });
  }

  openDetails(menu: MenuTemplate): void {
    // Reload the template fresh to get latest dishes data
    if (menu.id) {
      this.menuService.getMenuTemplate(menu.id)
        .pipe(take(1))
        .subscribe({
          next: (freshMenu) => {
            this.selectedMenu = freshMenu;
            this.detailVisible = true;
          },
          error: () => {
            this.selectedMenu = menu;
            this.detailVisible = true;
          }
        });
    } else {
      this.selectedMenu = menu;
      this.detailVisible = true;
    }
  }

  closeDetails(): void {
    this.detailVisible = false;
    this.selectedMenu = null;
  }

  // ===== Helpers =====

  isFormValid(): boolean {
    return !!(this.menuForm.name?.trim());
  }

  getCategoriesCount(menu: MenuTemplate): number {
    return (menu.categories?.length || 0) +
      (menu.sub_meals?.reduce((sum, sm) => sum + (sm.categories?.length || 0), 0) || 0);
  }

  /** Translate menu type from English to Hebrew */
  getMenuTypeHebrew(type: string): string {
    return type;
  }

  getMenuTypeSeverity(type: string): 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast' {
    return 'info';
  }

  getKosherClass(type: string): string {
    switch (type) {
      case 'חלבי': return 'kosher-badge-dairy';
      case 'בשרי': return 'kosher-badge-meat';
      case 'פרווה': return 'kosher-badge-parve';
      default: return '';
    }
  }

  // ===== Dish Picker & Assignment =====

  openDishPicker(category: any): void {
    this.dishPickerCategory = category;
    this.dishPickerSearch = '';
    this.selectedPickerDishes = [];  // Reset selection
    // Load all dishes if not loaded
    if (this.allDishes.length === 0) {
      this.dishService.getDishes({ is_active: true, limit: 200 })
        .pipe(take(1))
        .subscribe(response => {
          this.allDishes = response.items;
          this.filterPickerDishes();
          this.dishPickerVisible = true;
        });
    } else {
      this.filterPickerDishes();
      this.dishPickerVisible = true;
    }
  }

  toggleDishSelection(dish: any): void {
    const idx = this.selectedPickerDishes.findIndex(d => d.id === dish.id);
    if (idx >= 0) {
      this.selectedPickerDishes.splice(idx, 1);
    } else {
      this.selectedPickerDishes.push(dish);
    }
  }

  isDishSelected(dish: any): boolean {
    return this.selectedPickerDishes.some(d => d.id === dish.id);
  }

  addSelectedDishes(): void {
    if (!this.dishPickerCategory?.id || this.selectedPickerDishes.length === 0) return;

    this.dishPickerSubmitting = true;
    const categoryId = this.dishPickerCategory.id;
    let currentOrder = this.dishPickerCategory.dish_mappings?.length || 0;
    let completed = 0;
    let errors = 0;

    for (const dish of this.selectedPickerDishes) {
      const mapping: DishMenuMappingCreate = {
        dish_id: dish.id,
        category_id: categoryId,
        is_upgrade: false,
        display_order: currentOrder++
      };

      this.menuService.addDishToCategory(mapping)
        .pipe(take(1))
        .subscribe({
          next: (result) => {
            // Add to local array
            if (!this.dishPickerCategory.dish_mappings) this.dishPickerCategory.dish_mappings = [];
            this.dishPickerCategory.dish_mappings.push({
              id: result.id,
              mapping_id: result.id,
              dish_id: dish.id,
              dish_name: dish.name,
              dish_kosher_type: dish.kosher_type,
              dish_client_price: dish.client_price,
              is_upgrade: false,
              extra_charge: null,
              display_order: currentOrder - 1
            });
            completed++;
            this.checkSelectionComplete(completed, errors);
          },
          error: () => {
            errors++;
            completed++;
            this.checkSelectionComplete(completed, errors);
          }
        });
    }
  }

  private checkSelectionComplete(completed: number, errors: number): void {
    if (completed === this.selectedPickerDishes.length) {
      this.dishPickerSubmitting = false;
      this.filterPickerDishes();
      const successCount = completed - errors;
      if (successCount > 0) {
        this.messageService.add({
          severity: 'success',
          summary: 'מנות שויכו',
          detail: `${successCount} מנות נוספו ל${this.dishPickerCategory.name_hebrew}`
        });
      }
      if (errors > 0) {
        this.messageService.add({
          severity: 'warn',
          summary: 'שגיאה חלקית',
          detail: `${errors} מנות לא הצליחו להתווסף`
        });
      }
      this.selectedPickerDishes = [];
      this.dishPickerVisible = false;
    }
  }

  filterPickerDishes(): void {
    const existingDishIds = new Set(
      (this.dishPickerCategory?.dish_mappings || []).map((d: any) => d.dish_id)
    );
    let dishes = this.allDishes.filter(d => !existingDishIds.has(d.id));

    // Filter by menu's kosher type - exact match only
    // Default to 'פרווה' if not set
    const menuKosherType = this.selectedMenu?.kosher_type || 'פרווה';
    console.log('Menu kosher type:', menuKosherType, 'Selected menu:', this.selectedMenu);
    
    // Always filter by kosher type
    // Filter dishes based on menu's kosher type:
    // - Meat menu: show meat and parve dishes
    // - Dairy menu: show dairy and parve dishes
    // - Parve menu: show only parve dishes
    dishes = dishes.filter(d => {
      const dishKosher = d.kosher_type || 'פרווה';
      
      if (menuKosherType === 'בשרי') {
        return dishKosher === 'בשרי' || dishKosher === 'פרווה';
      } else if (menuKosherType === 'חלבי') {
        return dishKosher === 'חלבי' || dishKosher === 'פרווה';
      } else {
        // תפריט פרווה - רק מנות פרווה
        return dishKosher === 'פרווה';
      }
    });

    if (this.dishPickerSearch?.trim()) {
      const term = this.dishPickerSearch.trim().toLowerCase();
      dishes = dishes.filter(d =>
        d.name.toLowerCase().includes(term) ||
        (d.description || '').toLowerCase().includes(term)
      );
    }

    this.filteredPickerDishes = dishes;
  }

  addDishToCategory(dish: any): void {
    if (!this.dishPickerCategory?.id) return;

    const mapping: DishMenuMappingCreate = {
      dish_id: dish.id,
      category_id: this.dishPickerCategory.id,
      is_upgrade: false,
      display_order: (this.dishPickerCategory.dish_mappings?.length || 0)
    };

    this.menuService.addDishToCategory(mapping)
      .pipe(take(1))
      .subscribe({
        next: (result) => {
          // Add to local array
          if (!this.dishPickerCategory.dish_mappings) this.dishPickerCategory.dish_mappings = [];
          this.dishPickerCategory.dish_mappings.push({
            id: result.id,
            mapping_id: result.id,
            dish_id: dish.id,
            dish_name: dish.name,
            dish_kosher_type: dish.kosher_type,
            dish_client_price: dish.client_price,
            is_upgrade: false,
            extra_charge: null,
            display_order: (this.dishPickerCategory.dish_mappings?.length || 0)
          });
          this.filterPickerDishes(); // re-filter to remove added dish
          this.messageService.add({
            severity: 'success',
            summary: 'מנה שויכה',
            detail: `${dish.name} נוספה ל${this.dishPickerCategory.name_hebrew}`
          });
        },
        error: () => {
          this.messageService.add({
            severity: 'error',
            summary: 'שגיאה',
            detail: 'שיוך מנה נכשל'
          });
        }
      });
  }

  openDishEdit(dish: any): void {
    this.dishEditMap[dish.id] = {
      default_serving_mode: dish.default_serving_mode ?? null,
      is_upgrade: dish.is_upgrade ?? false,
      extra_charge: dish.extra_charge ?? null
    };
  }

  cancelDishEdit(dish: any): void {
    delete this.dishEditMap[dish.id];
  }

  saveDishEdit(dish: any): void {
    const edit = this.dishEditMap[dish.id];
    if (!edit) return;
    this.menuService.updateDishMapping(dish.id, {
      default_serving_mode: edit.default_serving_mode,
      is_upgrade: edit.is_upgrade,
      extra_charge: edit.is_upgrade ? (edit.extra_charge ?? undefined) : undefined
    }).pipe(take(1)).subscribe({
      next: () => {
        dish.default_serving_mode = edit.default_serving_mode;
        dish.is_upgrade = edit.is_upgrade;
        dish.extra_charge = edit.is_upgrade ? edit.extra_charge : null;
        delete this.dishEditMap[dish.id];
        this.messageService.add({ severity: 'success', summary: 'עודכן', detail: 'הגדרות מנה עודכנו' });
      },
      error: () => {
        this.messageService.add({ severity: 'error', summary: 'שגיאה', detail: 'עדכון מנה נכשל' });
      }
    });
  }

  removeDishFromCat(mappingId: number, category: any): void {
    this.confirmationService.confirm({
      message: 'האם להסיר את המנה מהקטגוריה?',
      header: 'אישור הסרה',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'הסר',
      rejectLabel: 'ביטול',
      accept: () => {
        this.menuService.removeDishFromCategory(mappingId)
          .pipe(take(1))
          .subscribe({
            next: () => {
              if (category.dish_mappings) {
                category.dish_mappings = category.dish_mappings.filter((d: any) => d.mapping_id !== mappingId);
              }
              this.messageService.add({
                severity: 'success',
                summary: 'מנה הוסרה',
                detail: 'המנה הוסרה מהקטגוריה'
              });
            },
            error: () => {
              this.messageService.add({
                severity: 'error',
                summary: 'שגיאה',
                detail: 'הסרת מנה נכשלה'
              });
            }
          });
      }
    });
  }

  deleteCategory(category: MenuCategory, subMeal?: any): void {
    const dishCount = category.dish_mappings?.length || 0;
    const warningMessage = dishCount > 0
      ? `האם למחוק את הקטגוריה "${category.name_hebrew}"? יש בה ${dishCount} מנות משויכות שיוסרו גם כן.`
      : `האם למחוק את הקטגוריה "${category.name_hebrew}"?`;

    this.confirmationService.confirm({
      message: warningMessage,
      header: 'אישור מחיקת קטגוריה',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'מחק',
      rejectLabel: 'ביטול',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => {
        if (!category.id) return;

        this.menuService.deleteCategory(category.id)
          .pipe(take(1))
          .subscribe({
            next: () => {
              // Remove from sub-meal categories
              if (subMeal && subMeal.categories) {
                subMeal.categories = subMeal.categories.filter((c: MenuCategory) => c.id !== category.id);
              }
              // Remove from direct categories
              if (this.selectedMenu?.categories) {
                this.selectedMenu.categories = this.selectedMenu.categories.filter(c => c.id !== category.id);
              }
              this.messageService.add({
                severity: 'success',
                summary: 'קטגוריה נמחקה',
                detail: `הקטגוריה "${category.name_hebrew}" נמחקה בהצלחה`
              });
            },
            error: () => {
              this.messageService.add({
                severity: 'error',
                summary: 'שגיאה',
                detail: 'מחיקת קטגוריה נכשלה'
              });
            }
          });
      }
    });
  }

  private getEmptyForm(): MenuFormModel {
    return {
      name: '',
      description: '',
      minGuests: 0,
      basePricePerGuest: null,
      realDishesExtraPerGuest: null,
      isTrayMenu: false,
      kosherType: 'פרווה'
    };
  }

  // ── Sub-Meal Form Methods ──────────────────────────────────────────

  openSubMealForm(): void {
    this.subMealForm = {
      name: '',
      displayOrder: (this.selectedMenu?.sub_meals?.length || 0),
      isSplittable: false,
      splitExtraCharge: null
    };
    this.subMealFormVisible = true;
  }

  closeSubMealForm(): void {
    this.subMealFormVisible = false;
  }

  submitSubMealForm(): void {
    if (!this.selectedMenu?.id || !this.subMealForm.name) return;

    this.subMealFormSubmitting = true;
    const payload = {
      template_id: this.selectedMenu.id,
      name: this.subMealForm.name,
      display_order: this.subMealForm.displayOrder,
      is_splittable: this.subMealForm.isSplittable,
      split_extra_charge: this.subMealForm.splitExtraCharge
    };
    const menuId = this.selectedMenu.id;

    this.menuService.createSubMeal(payload)
      .pipe(take(1))
      .subscribe({
        next: (created) => {
          // Refresh the menu detail
          this.loadMenuDetail(menuId);
          this.messageService.add({
            severity: 'success',
            summary: 'סעודה נוספה',
            detail: `${created.name} נוספה בהצלחה`
          });
          this.subMealFormSubmitting = false;
          this.closeSubMealForm();
        },
        error: (err) => {
          this.messageService.add({
            severity: 'error',
            summary: 'שגיאה',
            detail: err?.message || 'הוספת סעודה נכשלה'
          });
          this.subMealFormSubmitting = false;
        }
      });
  }

  // ── Category Form Methods ──────────────────────────────────────────

  openCategoryForm(subMealId?: number): void {
    // Prepare sub-meals dropdown options
    this.subMealsForSelect = (this.selectedMenu?.sub_meals || [])
      .filter(sm => sm.id !== undefined)
      .map(sm => ({
        label: sm.name,
        value: sm.id as number
      }));

    this.categoryForm = {
      name: '',
      nameHebrew: '',
      subMealId: subMealId || null,
      quota: null,
      displayOrder: 0
    };
    this.categoryFormVisible = true;
  }

  closeCategoryForm(): void {
    this.categoryFormVisible = false;
  }

  submitCategoryForm(): void {
    if (!this.selectedMenu?.id || !this.categoryForm.nameHebrew) return;

    this.categoryFormSubmitting = true;
    const menuId = this.selectedMenu.id;
    const payload: any = {
      template_id: this.categoryForm.subMealId ? null : menuId,
      sub_meal_id: this.categoryForm.subMealId || null,
      name: this.categoryForm.name || this.categoryForm.nameHebrew.toLowerCase().replace(/\s+/g, '_'),
      name_hebrew: this.categoryForm.nameHebrew,
      display_order: this.categoryForm.displayOrder,
      quota: this.categoryForm.quota,
      is_required: true
    };

    this.menuService.createCategory(payload)
      .pipe(take(1))
      .subscribe({
        next: (created) => {
          // Refresh the menu detail
          this.loadMenuDetail(menuId);
          this.messageService.add({
            severity: 'success',
            summary: 'קטגוריה נוספה',
            detail: `${created.name_hebrew} נוספה בהצלחה`
          });
          this.categoryFormSubmitting = false;
          this.closeCategoryForm();
        },
        error: (err) => {
          this.messageService.add({
            severity: 'error',
            summary: 'שגיאה',
            detail: err?.message || 'הוספת קטגוריה נכשלה'
          });
          this.categoryFormSubmitting = false;
        }
      });
  }

  private loadMenuDetail(menuId: number): void {
    this.menuService.getMenuTemplate(menuId)
      .pipe(take(1))
      .subscribe({
        next: (menu) => {
          this.selectedMenu = menu;
          // Also update in the list
          const idx = this.menus.findIndex(m => m.id === menu.id);
          if (idx !== -1) this.menus[idx] = menu;
        }
      });
  }
}
