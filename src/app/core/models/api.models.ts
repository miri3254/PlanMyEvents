// API Response models for FastAPI backend

// Common interfaces
export interface ApiResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export interface BaseEntity {
  id: string;
  created_at?: string;
  updated_at?: string;
}

// Event models
export interface EventCreate {
  name: string;
  event_type: string;
  date: string; // ISO format datetime
  hebrew_date?: string;
  guest_count: number;
  notes?: string;
  location?: string;
  contact_name?: string;
  contact_phone?: string;
  total_price?: number;
  status?: string;
}

export interface EventUpdate extends Partial<EventCreate> {}

export interface EventStatusUpdate {
  status: 'טיוטה' | 'מתוכנן' | 'בהכנה' | 'הושלם' | 'בוטל';
}

export interface ApiEvent extends BaseEntity {
  name: string;
  event_type: string;
  date: string; // ISO datetime
  hebrew_date?: string;
  guest_count: number;
  status: string;
  location?: string;
  contact_name?: string;
  contact_phone?: string;
  notes?: string;
  total_price?: number;
  dishes?: EventDish[];
}

export interface EventDish {
  id: string;
  event_id: string;
  dish_id: string;
  quantity: number;
  dish?: ApiDish;
}

// Dish models
export interface DishCreate {
  name: string;
  description?: string;
  category: string;
  kosher_type: string;
  serving_size: number;
  price_per_unit: number;
  is_active?: boolean;
}

export interface DishUpdate extends Partial<DishCreate> {}

export interface ApiDish extends BaseEntity {
  name: string;
  description?: string;
  category: string;
  kosher_type: string;
  serving_size: number;
  // Server returns price_per_unit (not estimated_price)
  price_per_unit: number;
  estimated_price?: number; // Keep for backwards compatibility
  image_url?: string;
  is_active: boolean;
  ingredients?: DishIngredient[];
  equipment?: DishEquipment[];
  serving_dishes?: DishServingDish[];
}

export interface DishIngredient extends BaseEntity {
  dish_id: string;
  product_id: string;
  quantity: number;
  unit: string;
  // Frontend helpers (optional)
  productId?: string;
  productName?: string;
  // Server returns name directly (not nested in product)
  name?: string;
  notes?: string;
  product?: ApiProduct;
}

export interface DishEquipment extends BaseEntity {
  dish_id: string;
  tool_id: string;
  quantity: number;
  // Server returns name directly (not nested in tool)
  name?: string;
  notes?: string;
  tool?: ApiTool;
}

export interface DishServingDish extends BaseEntity {
  dish_id: string;
  tool_id: string;
  quantity: number;
  // Server returns name directly (not nested in tool)
  name?: string;
  notes?: string;
  tool?: ApiTool;
}

// Product models
export interface ProductCreate {
  name: string;
  category: string;
  package_quantity: number;
  estimated_price: number;
  inventory_status: string;
  supplier?: string;
  brand?: string;
  notes?: string;
}

export interface ProductUpdate extends Partial<ProductCreate> {}

export interface ApiProduct extends BaseEntity {
  name: string;
  category: string;
  package_quantity: number;
  estimated_price: number;
  inventory_status: string;
  supplier?: string;
  brand?: string;
  notes?: string;
}

// Tool models
export interface ToolCreate {
  name: string;
  category: string;
  sub_category?: string;
  quantity_in_stock?: number;
  min_stock_level?: number;
  price_per_unit?: number;
  description?: string;
  color?: string;
  size?: string;
  inventory_status?: string;
}

export interface ToolUpdate extends Partial<ToolCreate> {}

export interface ApiTool extends BaseEntity {
  name: string;
  category: string;
  inventory_status: string;
  price_per_unit?: number;
  quantity_in_stock?: number;
  min_stock_level?: number;
  sub_category?: string;
  color?: string;
  size?: string;
  description?: string;
}

// Lookup models - Server returns string arrays
export interface LookupData {
  dish_categories: string[];
  kosher_types: string[];
  measurement_units: string[];
  product_categories: string[];
  inventory_statuses: string[];
  event_types: string[];
  event_statuses: string[];
  tool_categories: string[];
  tool_sub_categories: string[];
}

// For backwards compatibility
export interface LookupValue {
  id?: string;
  name: string;
  display_name?: string;
  is_active?: boolean;
  sort_order?: number;
}

// Dashboard models
export interface DashboardStats {
  total_events: number;
  upcoming_events: number;
  active_dishes: number;
  low_stock_products: number;
  total_products: number;
  total_tools: number;
  low_stock_tools: number;
  events_this_month: number;
  events_by_status: { [key: string]: number };
}

export interface UpcomingEvent {
  id: number;
  name: string;
  date: string;
  event_type: string;
  guest_count: number;
  status: string;
  location?: string;
}

export interface LowStockAlert {
  id: string;
  name: string;
  category: string;
  inventory_status: string;
}

// Shopping and Equipment Lists
export interface ShoppingListItem {
  product_id?: number;
  name: string;
  quantity: number;
  unit: string;
  estimated_price: number;
  category?: string;
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
}

export interface EquipmentListResponse {
  event_id: number;
  event_name: string;
  items: EquipmentListItem[];
}

// Query parameters
export interface EventsQueryParams {
  status?: string;
  event_type?: string;
  from_date?: string;
  to_date?: string;
  skip?: number;
  limit?: number;
}

export interface DishesQueryParams {
  category?: string;
  kosher_type?: string;
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