// ============================================
// API Response models - תואם FastAPI backend
// ללא תאימות לאחור - מבנה חדש בלבד
// ============================================

import {
  MenuType,
  EventStatus,
  KosherType,
  UnitType,
  ToolCategory,
  ToolSubCategory,
  ProductCategory
} from './enums';

// ============================================
// Common interfaces
// ============================================

export interface ApiResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export interface BaseEntity {
  id: number;
  created_at?: string;
  updated_at?: string;
}

// ============================================
// Event Owner
// ============================================

export interface EventOwnerCreate {
  name: string;
  phone?: string;
  email?: string;
  order?: number;
}

export interface ApiEventOwner extends BaseEntity {
  event_id: number;
  name: string;
  phone?: string;
  email?: string;
  order: number;
}

export interface DeliveryNoteTemplate extends BaseEntity {
  note: string;
  display_order: number;
}

export interface EventBoxCreate {
  box_type: string;
  quantity: number;
  notes?: string;
}

export interface ApiEventBox extends BaseEntity {
  event_id: number;
  box_type: string;
  quantity: number;
  notes?: string;
}

export interface ApiEventDeliveryNote extends BaseEntity {
  event_id: number;
  template_id: number;
  note: string;
}

// ============================================
// Event - מבנה חדש: menu_type, address+city, owners[]
// ============================================

export interface EventCreate {
  name: string;
  event_category?: string;
  menu_type: MenuType;
  date: string;                  // ISO format datetime
  event_time?: string;           // שעת האירוע
  hebrew_date?: string;
  guest_count: number;
  address?: string;
  city?: string;
  is_real_dishes?: boolean;      // כלים אמיתיים (לא חד"פ)
  is_morning_split?: boolean;    // פיצול בוקר (שבת)
  notes?: string;
  status?: EventStatus;
  owners?: EventOwnerCreate[];
  venue_name?: string;
  floor?: number;
  has_elevator?: boolean;
  access_code?: string;
  onsite_contact_name?: string;
  onsite_contact_phone?: string;
  hall_owner_name?: string;
  hall_owner_phone?: string;
  seating_sides?: SeatingSide[];        // מקומות וצורת סידור בכל צד באולם
  has_nearby_parking?: boolean;
  has_back_entrance?: boolean;
  requires_carts?: boolean;
  access_notes?: string;
  dishware_type?: string;
  delivery_contents_notes?: string;
  last_minute_items?: string;
  equipment_dropoff_location?: string;
  check_refrigerator?: boolean;
  check_freezer?: boolean;
  check_hot_plate?: boolean;
  connect_gas?: boolean;
  put_in_refrigerator?: boolean;
  put_in_freezer?: boolean;
  put_on_hot_plate?: boolean;
  count_boxes?: boolean;
  check_drinks?: boolean;
  check_rolls?: boolean;
  delivery_special_notes?: string;
  selected_delivery_note_template_ids?: number[];
  boxes?: EventBoxCreate[];
}

export interface EventUpdate extends Partial<EventCreate> {
  final_price?: number;  // מחיר סופי (ניתן לעריכה)
}

export interface EventPriceUpdate {
  final_price: number;  // מחיר סופי
}

export interface EventStatusUpdate {
  status: EventStatus;
}

export interface ApiEvent extends BaseEntity {
  name: string;
  event_category?: string;
  menu_type: MenuType;
  date: string;
  event_time?: string;
  hebrew_date?: string;
  day_sequence_number?: number;
  day_sequence_color?: string;
  guest_count: number;
  status: EventStatus;
  address?: string;
  city?: string;
  is_real_dishes?: boolean;  // כלים אמיתיים
  is_morning_split?: boolean;
  split_extra_charge?: number;
  // Pricing fields
  base_price_per_guest?: number;
  real_dishes_extra_per_guest?: number;  // תוספת כלים אמיתיים
  calculated_price?: number;  // מחיר מחושב אוטומטית
  final_price?: number | null;  // מחיר סופי (ניתן לעריכה)
  discount_percent?: number;  // אחוז הנחה
  discount_amount?: number;  // סכום ההנחה
  total_price?: number;  // legacy
  notes?: string;
  venue_name?: string;
  floor?: number;
  has_elevator?: boolean;
  access_code?: string;
  onsite_contact_name?: string;
  onsite_contact_phone?: string;
  hall_owner_name?: string;
  hall_owner_phone?: string;
  seating_sides?: SeatingSide[];        // מקומות וצורת סידור בכל צד באולם
  has_nearby_parking?: boolean;
  has_back_entrance?: boolean;
  requires_carts?: boolean;
  access_notes?: string;
  dishware_type?: string;
  delivery_contents_notes?: string;
  last_minute_items?: string;
  equipment_dropoff_location?: string;
  check_refrigerator?: boolean;
  check_freezer?: boolean;
  check_hot_plate?: boolean;
  connect_gas?: boolean;
  put_in_refrigerator?: boolean;
  put_in_freezer?: boolean;
  put_on_hot_plate?: boolean;
  count_boxes?: boolean;
  check_drinks?: boolean;
  check_rolls?: boolean;
  delivery_special_notes?: string;
  selected_delivery_note_template_ids?: number[];
  boxes?: ApiEventBox[];
  delivery_notes?: ApiEventDeliveryNote[];
  total_boxes?: number;
  // חישובים אוטומטיים
  waiter_count?: number;  // 2 מלצרים לכל 50 סועדים
  table_count?: number;   // שולחן לכל 8 סועדים
  dishes?: ApiEventDish[];
  owners?: ApiEventOwner[];
  tray_selections?: ApiEventTraySelection[];
  calculation_settings?: EventCalculationSettings;
  has_calculation_snapshot?: boolean;
  warnings?: string[];                  // אזהרות עסקיות (לא חוסמות)
}

// ============================================
// Event Dish - כולל snapshot prices ו-draft status
// ============================================

export interface EventDishCreate {
  serving_mode?: "personal" | "central" | null;
  dish_id: number;
  sub_meal_id?: number;
  category_id?: number;
  quantity: number;
  is_upgrade?: boolean;
  is_gift?: boolean;
  extra_charge?: number;
  notes?: string;
}

export interface ApiEventDish extends BaseEntity {
  serving_mode?: "personal" | "central" | null;
  event_id: number;
  dish_id: number;
  sub_meal_id?: number;
  category_id?: number;
  quantity: number;
  is_upgrade: boolean;
  is_gift: boolean;
  extra_charge?: number;
  notes?: string;
  is_draft: boolean;                   // טיוטה = true, אושר = false
  snapshot_base_price?: number;        // מחיר עלות ברגע האישור - לא משתנה!
  snapshot_client_price?: number;      // מחיר ללקוח ברגע האישור - לא משתנה!
  current_base_price?: number;         // מחיר עלות נוכחי של המנה (fallback)
  // Joined fields
  dish_name?: string;
  dish_kosher_type?: KosherType;
  category_name_hebrew?: string;
}

// ============================================
// Event Tray Selection (למגשי אירוח)
// ============================================

export interface ApiEventTraySelection extends BaseEntity {
  event_id: number;
  dish_id: number;
  category_id?: number;
  tray_count: number;
  price_per_tray?: number;
  notes?: string;
}

// ============================================
// Dish
// ============================================

export interface DishCreate {
  name: string;
  description?: string;
  kosher_type?: KosherType;
  base_price?: number;
  client_price?: number;
  serving_size?: number;
  serving_description?: string;
  waiter_notes?: string;
  is_active?: boolean;
}

export interface DishUpdate extends Partial<DishCreate> {}

export interface ApiDishMenuMappingInfo {
  mapping_id: number;
  category_id: number;
  category_name_hebrew: string;
  menu_type: string;
  template_name: string;
  sub_meal_name?: string;
  is_upgrade: boolean;
  extra_charge?: number;
  display_order: number;
}

export interface ApiDish extends BaseEntity {
  name: string;
  description?: string;
  kosher_type: KosherType;
  base_price?: number;
  client_price?: number;
  serving_size: number;
  serving_description?: string;
  waiter_notes?: string;
  is_active: boolean;
  ingredients?: DishIngredient[];
  equipment?: DishEquipment[];
  serving_dishes?: DishServingDish[];
  menu_mappings?: ApiDishMenuMappingInfo[];
}

export interface DishIngredient extends BaseEntity {
  dish_id?: number;
  product_id?: number;
  quantity: number;
  unit: string;
  name?: string;
  is_serving_component: boolean;
  product?: ApiProduct;
}

export interface DishEquipment extends BaseEntity {
  dish_id?: number;
  tool_id: number;
  quantity: number;
  name?: string;
  tool?: ApiTool;
}

export interface DishServingDish extends BaseEntity {
  dish_id?: number;
  tool_id?: number;
  quantity: number;
  name?: string;
  tool?: ApiTool;
}

// ============================================
// Product
// ============================================

export interface ProductCreate {
  drink_type?: 'pepsi' | 'pepsi_max' | 'orange_flavored' | 'water' | 'soda' | null;
  name: string;
  category: string;
  unit?: string;
  package_quantity?: number;
  price_per_unit?: number;
  estimated_price?: number;
  quantity_in_stock?: number;
  min_stock_level?: number;
  supplier?: string;
  brand?: string;
  barcode?: string;
  notes?: string;
  description?: string;
  kosher_type?: KosherType;
}

export interface ProductUpdate extends Partial<ProductCreate> {}

export interface ApiProduct extends BaseEntity {
  drink_type?: ProductCreate['drink_type'];
  name: string;
  category: string;
  unit: string;
  package_quantity?: number;
  price_per_unit?: number;
  estimated_price?: number;
  quantity_in_stock?: number;
  min_stock_level?: number;
  inventory_status?: string;     // מחושב בבקאנד: במלאי / מלאי נמוך / אין במלאי
  supplier?: string;
  brand?: string;
  barcode?: string;
  notes?: string;
  description?: string;
  kosher_type?: KosherType;
}

// ============================================
// Tool
// ============================================

export interface ToolCreate {
  name: string;
  brand?: string;
  category: string;
  sub_category?: string;
  quantity_in_stock?: number;
  min_stock_level?: number;
  price_per_unit?: number;
  description?: string;
  color?: string;
  size?: string;
}

export interface ToolUpdate extends Partial<ToolCreate> {}

export interface ApiTool extends BaseEntity {
  name: string;
  brand?: string;
  category: string;
  sub_category?: string;
  quantity_in_stock?: number;
  min_stock_level?: number;
  price_per_unit?: number;
  inventory_status?: string;     // מחושב בבקאנד: במלאי / מלאי נמוך / אין במלאי
  description?: string;
  color?: string;
  size?: string;
}

// ============================================
// Lookup - תואם FastAPI /lookup endpoint
// ============================================

export interface LookupData {
  menu_types: string[];
  event_categories: string[];
  kosher_types: string[];
  measurement_units: string[];
  product_categories: string[];
  inventory_statuses: string[];
  event_statuses: string[];
  tool_categories: string[];
  tool_sub_categories: string[];
}

// Generic lookup value used by components
export interface LookupValue {
  label: string;
  value: string;
}

// ============================================
// Dashboard - Basic Stats
// ============================================

export interface DashboardStats {
  total_events: number;
  upcoming_events: number;
  active_dishes: number;
  low_stock_products: number;
  total_products: number;
  total_tools: number;
  total_dishes: number;
  low_stock_tools: number;
  events_this_month: number;
  events_by_status: { [key: string]: number };
}

export interface UpcomingEvent {
  id: number;
  name: string;
  date: string;
  event_time?: string;
  hebrew_date?: string;
  menu_type: MenuType;
  guest_count: number;
  status: EventStatus;
  address?: string;
  city?: string;
}

export interface LowStockAlert {
  id: number;
  name: string;
  category: string;
  quantity_in_stock: number;
  min_stock_level: number;
  inventory_status: string;
}

export interface LowStockResponse {
  products: LowStockAlert[];
  tools: LowStockAlert[];
}

// ============================================
// Dashboard - Profitability Models
// ============================================

export interface EventProfitability {
  event_id: number;
  event_name: string;
  event_date?: string;
  guest_count: number;
  menu_type?: string;
  status?: string;
  
  // Revenue (what client paid)
  revenue: number;
  
  // Costs breakdown
  food_cost: number;
  labor_cost: number;
  equipment_cost: number;
  
  // Profitability
  total_cost: number;
  gross_profit: number;
  profit_margin_percent: number;
  profit_per_guest: number;
}

export interface MonthlyProfitSummary {
  year: number;
  month: number;
  month_name: string;
  
  // Event counts
  total_events: number;
  completed_events: number;
  total_guests: number;
  
  // Financials
  total_revenue: number;
  total_cost: number;
  gross_profit: number;
  profit_margin_percent: number;
  
  // Averages
  avg_revenue_per_event: number;
  avg_profit_per_event: number;
  avg_revenue_per_guest: number;
}

export interface ExpenseBreakdown {
  category: string;
  amount: number;
  percentage: number;
  item_count: number;
  color?: string;
}

export interface ProfitabilityDashboard {
  // Period info
  period_start: string;
  period_end: string;
  period_label: string;
  
  // Overview KPIs
  total_revenue: number;
  total_cost: number;
  total_profit: number;
  profit_margin_percent: number;
  
  // Comparisons
  revenue_vs_last_period: number;
  profit_vs_last_period: number;
  events_vs_last_period: number;
  
  // Event stats
  total_events: number;
  completed_events: number;
  total_guests: number;
  avg_revenue_per_event: number;
  avg_profit_per_event: number;
  avg_profit_per_guest: number;
  
  // Top performers
  most_profitable_event?: EventProfitability;
  highest_margin_event?: EventProfitability;
  
  // Detailed data
  expense_by_category: ExpenseBreakdown[];
  monthly_trends: MonthlyProfitSummary[];
  events_profitability: EventProfitability[];
}

export interface InventorySummary {
  total_products: number;
  total_value: number;
  
  low_stock_count: number;
  out_of_stock_count: number;
  healthy_stock_count: number;
  
  value_by_category: ExpenseBreakdown[];
  low_stock_items: LowStockAlert[];
  out_of_stock_items: LowStockAlert[];
}

export interface RevenueChartData {
  labels: string[];
  revenue_data: number[];
  cost_data: number[];
  profit_data: number[];
  event_count_data: number[];
}

export interface ExpenseChartData {
  labels: string[];
  values: number[];
  colors: string[];
}

// ============================================
// Shopping & Equipment Lists
// ============================================

export interface ShoppingListItem {
  product_id?: number;
  name: string;
  quantity: number;
  unit: string;
  estimated_price: number;
  category?: string;
  formula_label?: string;
  source_type?: string;
  raw_quantity?: number;
  quantity_in_stock?: number;
  need_to_buy_quantity?: number;
  packages_to_buy?: number;
}

export interface ShoppingListResponse {
  event_id: number;
  event_name: string;
  items: ShoppingListItem[];
  total_estimated_price: number;
}

export interface EquipmentListItem {
  tool_id?: number;
  name: string;
  quantity: number;
  category?: string;
  available_in_stock?: number;
  need_to_buy?: number;
  formula_label?: string;
  source_type?: string;
  raw_quantity?: number;
  is_reusable?: boolean;
  reserved_quantity?: number;
  available_after_reservations?: number;
  shortage?: number;
}

export interface EquipmentListResponse {
  event_id: number;
  event_name: string;
  items: EquipmentListItem[];
}

/** צד באולם: שם הצד, מספר מקומות וצורת סידור (מזרח / מרובע / ארוכים...) */
export interface SeatingSide {
  side: string;
  places: number | null;
  arrangement: string;
}

/** שתייה אחרת: כמות ידנית והערות (בקשת בעל הקייטרינג) */
export interface OtherDrink {
  name: string;
  quantity: number | null;
  notes?: string;
  unit?: string;
}

export interface EventCalculationSettings {
  drinks_enabled: boolean;
  drink_types?: Record<string, boolean>;
  orange_flavored_mode: 'orange' | 'flavored' | 'both';
  rolls_enabled: boolean;
  roll_splits?: RollSplit[];
  table_shape: 'square' | 'round' | 'rectangle';
  tablecloth_tool_id?: number;
  use_rectangular_for_square: boolean;
  table_overrides?: Array<Record<string, unknown>>;
  event_tool_set_items?: EventToolSetItem[];
  tablecloth_split?: { rectangle?: number; square?: number; extra?: { name: string; quantity: number | null }[] } | null; // חלוקת המפות + מפות נוספות
  desserts_enabled?: boolean;           // קינוחים 1.5 לסועד בין 4 סוגים
  other_drinks?: OtherDrink[] | null;   // שתייה אחרת
  credit_card_enabled: boolean;
  credit_card_amount?: number | null;
  credit_card_installments?: number;
  credit_card_rate?: number | null;
  credit_card_vat_multiplier?: number;
  notes?: string;
}

export interface RollSplit {
  name: string;
  percent: number;
  quantity?: number | null;
  product_id?: number | null;
  source?: 'product' | 'manual';
  price_per_unit?: number | null;
}

export interface EventToolSetItem {
  tool_id: number | null;
  quantity_per_guest: number;
  is_reusable?: boolean;
}

export interface CalculationRequirement {
  source_type: string;
  item_type: 'product' | 'tool';
  name: string;
  quantity: number;
  unit: string;
  formula_label?: string;
  details?: Record<string, unknown>;     // פירוט החישוב מהשרת (בסיס, ספייר, מקור)
  raw_quantity?: number;
  product_id?: number;
  tool_id?: number;
  category?: string;
  is_reusable: boolean;
  available_in_stock: number;
  reserved_quantity: number;
  available_after_reservations: number;
  shortage: number;
  need_to_buy_quantity: number;
}

export interface EventCalculationSummary {
  event_id: number;
  event_name: string;
  settings?: EventCalculationSettings;
  has_approved_snapshot: boolean;
  waiter_count: number;
  table_count: number;
  production_cost?: number | null;
  estimated_profit?: number | null;
  revenue?: number | null;
  table_formula_label?: string | null;
  waiter_formula_label?: string | null;
  product_requirements: CalculationRequirement[];
  tool_requirements: CalculationRequirement[];
  charge_requirements: Array<{ source_type: string; name: string; amount: number; formula_label?: string }>;
  warnings: string[];
  formula_trace: Array<Record<string, unknown>>;
}

export interface DishServingSet {
  id?: number;
  dish_id?: number;
  name: string;
  set_type: 'serving' | 'packaging';
  is_default: boolean;
  dishware_type?: string;
  serving_mode?: 'personal' | 'central';
  notes?: string;
  items: Array<{ id?: number; tool_id?: number; name?: string; quantity: number; quantity_basis: 'event' | 'table' | 'guest' | 'dish_unit' | 'tray' | 'place_setting' | 'serving_group'; is_reusable?: boolean }>;
}

export interface DishCalculationRule {
  id?: number;
  dish_id?: number;
  rule_type: string;
  product_id?: number;
  name?: string;
  params?: Record<string, unknown>;
  replaces_ingredient_product_id?: number;
  is_active: boolean;
}

// ============================================
// Query Parameters
// ============================================

export interface EventsQueryParams {
  status?: EventStatus;
  menu_type?: MenuType;
  from_date?: string;
  to_date?: string;
  search?: string;
  skip?: number;
  limit?: number;
}

export interface DishesQueryParams {
  kosher_type?: KosherType;
  is_active?: boolean;
  search?: string;
  skip?: number;
  limit?: number;
}

export interface ProductsQueryParams {
  inventory_status?: string;
  category?: string;
  search?: string;
  skip?: number;
  limit?: number;
}

export interface ToolsQueryParams {
  inventory_status?: string;
  category?: string;
  sub_category?: string;
  search?: string;
  skip?: number;
  limit?: number;
}

export interface WorkbookPreset {
  key: string; name: string; factor: number; divisor: number; unit: string | null;
  sheet: string; cell: string; group: string; audience_fraction: number;
}
