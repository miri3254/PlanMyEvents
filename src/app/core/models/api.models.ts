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
  event_date: string; // ISO format
  event_time: string; // HH:MM format
  guest_count: number;
  notes?: string;
  location?: string;
}

export interface EventUpdate extends Partial<EventCreate> {}

export interface EventStatusUpdate {
  status: 'pending' | 'scheduled' | 'in-progress' | 'completed' | 'cancelled';
}

export interface ApiEvent extends BaseEntity {
  name: string;
  event_type: string;
  event_date: string;
  event_time: string;
  guest_count: number;
  status: string;
  location?: string;
  notes?: string;
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
  estimated_price: number;
  is_active?: boolean;
}

export interface DishUpdate extends Partial<DishCreate> {}

export interface ApiDish extends BaseEntity {
  name: string;
  description?: string;
  category: string;
  kosher_type: string;
  serving_size: number;
  estimated_price: number;
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
  product?: ApiProduct;
}

export interface DishEquipment extends BaseEntity {
  dish_id: string;
  tool_id: string;
  quantity: number;
  tool?: ApiTool;
}

export interface DishServingDish extends BaseEntity {
  dish_id: string;
  tool_id: string;
  quantity: number;
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
  inventory_status: string;
  estimated_price?: number;
  quantity?: number;
  sub_category?: string;
  supplier?: string;
  brand?: string;
  description?: string;
  notes?: string;
}

export interface ToolUpdate extends Partial<ToolCreate> {}

export interface ApiTool extends BaseEntity {
  name: string;
  category: string;
  inventory_status: string;
  estimated_price?: number;
  quantity?: number;
  sub_category?: string;
  supplier?: string;
  brand?: string;
  description?: string;
  notes?: string;
}

// Lookup models
export interface LookupValue extends BaseEntity {
  name: string;
  display_name: string;
  is_active: boolean;
  sort_order?: number;
}

export interface LookupData {
  event_types: LookupValue[];
  event_statuses: LookupValue[];
  dish_categories: LookupValue[];
  kosher_types: LookupValue[];
  product_categories: LookupValue[];
  tool_categories: LookupValue[];
  units: LookupValue[];
}

// Dashboard models
export interface DashboardStats {
  total_events: number;
  upcoming_events: number;
  active_dishes: number;
  low_stock_products: number;
  events_by_status: { [key: string]: number };
}

export interface UpcomingEvent {
  id: string;
  name: string;
  event_date: string;
  event_time: string;
  guest_count: number;
  status: string;
}

export interface LowStockAlert {
  id: string;
  name: string;
  category: string;
  inventory_status: string;
}

// Shopping and Equipment Lists
export interface ShoppingListItem {
  product_id: string;
  product_name: string;
  total_quantity: number;
  unit: string;
  estimated_cost: number;
  category: string;
  supplier?: string;
  brand?: string;
}

export interface EquipmentListItem {
  tool_id: string;
  tool_name: string;
  total_quantity: number;
  category: string;
  sub_category?: string;
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