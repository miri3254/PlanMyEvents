export interface TableSettingItem { name: string; quantity: number; quantity_basis?: "place_setting" | "serving_group"; disposable_tool_id?: number | null; real_tool_id?: number | null; }
import { KosherType } from '../core/models/enums';

// ============================================
// Menu Models - תואם FastAPI app/schemas/menu.py
// ============================================

export type TableclothProfile = 'regular' | 'sweet' | 'shabbat' | 'shabbat_split';

export interface MenuTemplate {
  table_setting_items?: TableSettingItem[];
  tablecloth_profile?: TableclothProfile;
  id?: number;
  name: string;
  description?: string;
  min_guests: number;
  base_price_per_guest?: number;   // null עבור תפריטי מגשים
  real_dishes_extra_per_guest?: number;  // תוספת כלים אמיתיים לסועד
  is_tray_menu: boolean;
  kosher_type?: KosherType;        // בשרי/חלבי/פרווה
  sub_meals?: MenuSubMeal[];
  categories?: MenuCategory[];
  created_at?: string;
  updated_at?: string;
}

export interface MenuSubMeal {
  id?: number;
  template_id?: number;
  name: string;                    // "ליל שבת", "סעודת שבת בוקר"
  display_order: number;
  is_splittable: boolean;          // האם תומך בפיצול בוקר
  split_extra_charge?: number;     // תוספת מחיר אם יש פיצול
  categories?: MenuCategory[];
}

export interface MenuCategory {
  id?: number;
  template_id?: number;
  sub_meal_id?: number;
  name: string;                    // מפתח פנימי: salads, fish, etc.
  name_hebrew: string;             // שם תצוגה: "סלטים", "דגים"
  description?: string;            // מידע על מכסה: "2 לבחירה - חצי סלמון חצי מושט"
  display_order: number;
  quota?: number;                  // מגבלת בחירה (null = ללא הגבלה)
  quota_description?: string;      // "2 לבחירה", "1 בחירה"
  guest_count_rules?: Record<string, { quota: number }>; // כללים דינמיים: {"above_80": {"quota": 3}}
  is_required: boolean;
  tray_quantity?: number;          // כמות ליחידת מגש
  tray_price?: number;             // מחיר למגש
  dish_mappings?: DishMenuMapping[];
}

export interface DishMenuMapping {
  default_serving_mode?: "personal" | "central" | null;
  id?: number;
  dish_id: number;
  category_id: number;
  is_upgrade: boolean;             // האם מנה פרימיום
  extra_charge?: number;           // תוספת מחיר לשדרוג
  display_order: number;
  // Joined fields from response
  dish_name?: string;
  dish_kosher_type?: KosherType;
  dish_client_price?: number;
  dish_serving_size?: number;
  dish_description?: string;
}

export interface MenuTemplateCreate {
  table_setting_items?: TableSettingItem[];
  name: string;
  description?: string;
  min_guests?: number;
  base_price_per_guest?: number;
  real_dishes_extra_per_guest?: number;  // תוספת כלים אמיתיים
  is_tray_menu?: boolean;
  kosher_type?: string;  // בשרי/חלבי/פרווה
}

export interface MenuTemplateUpdate extends Partial<MenuTemplateCreate> {}

export interface MenuCategoryCreate {
  template_id?: number;
  sub_meal_id?: number;
  name: string;
  name_hebrew: string;
  description?: string;
  display_order?: number;
  quota?: number;
  quota_description?: string;
  is_required?: boolean;
  tray_quantity?: number;
  tray_price?: number;
}

export interface MenuCategoryUpdate extends Partial<MenuCategoryCreate> {}

export interface DishMenuMappingCreate {
  default_serving_mode?: "personal" | "central" | null;
  dish_id: number;
  category_id: number;
  is_upgrade?: boolean;
  extra_charge?: number;
  display_order?: number;
}

// Category dishes response - תואם CategoryDishesResponse בבקאנד
export interface CategoryDishesResponse {
  category_id: number;
  category_name: string;
  category_name_hebrew: string;
  quota?: number;
  quota_description?: string;
  standard_dishes: DishMenuMapping[];   // is_upgrade = false
  upgrade_dishes: DishMenuMapping[];    // is_upgrade = true
}
