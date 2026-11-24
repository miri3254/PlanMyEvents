// ============================================
// Core data models for PlanMyEvents
// Re-exports from all model files
// ============================================

// Enums - מקור האמת לכל הערכים
export * from './enums';

// API models
export * from './api.models';

// ============================================
// Frontend-specific models (camelCase wrappers)
// ============================================

import { EventStatus, MenuType, KosherType } from './enums';
import type { SeatingSide } from './api.models';

export interface DishIngredient {
  id?: number;
  productId?: number;
  productName?: string;
  quantity: number | null;
  unit: string | null;
  isServingComponent: boolean;
  note?: string | null;
}

export interface ServingDish {
  id?: number;
  toolId?: number;
  name: string;
  quantity: number;
}

export interface DishMenuMappingInfo {
  mappingId: number;
  categoryId: number;
  categoryNameHebrew: string;
  menuType: string;
  templateName: string;
  subMealName?: string;
  isUpgrade: boolean;
  extraCharge?: number;
  displayOrder: number;
}

export interface Dish {
  id: number;
  name: string;
  description?: string;
  kosherType: KosherType;
  basePrice?: number;
  clientPrice?: number;
  servingSize: number | null;
  yieldQuantity?: number | null;
  yieldUnit?: string | null;
  notes?: string | null;
  servingDescription?: string;
  waiterNotes?: string;
  isActive: boolean;
  createdDate?: Date;
  lastModified?: Date;
  ingredients: DishIngredient[];
  servingDishes?: ServingDish[];
  // Warning indicator - אין מוצרים משויכים
  hasNoProducts?: boolean;
  // Menu mappings - לאילו תפריטים/קטגוריות שייכת המנה
  menuMappings?: DishMenuMappingInfo[];
}

export interface Product {
  drinkType?: 'pepsi' | 'pepsi_max' | 'orange_flavored' | 'water' | 'soda' | null;
  id?: number;
  name: string;
  category: string;
  unit: string;
  inventoryStatus?: string;
  brand?: string;
  packageQuantity?: number;
  estimatedPrice?: number;
  supplier?: string;
  kosherType?: KosherType;
  quantityInStock?: number;
  minStockLevel?: number;
  pricePerUnit?: number;
  barcode?: string;
  notes?: string;
  description?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Tool {
  id: number;
  name: string;
  brand?: string;
  category: string;
  subCategory?: string;
  inventoryStatus?: string;
  quantityInStock?: number;
  minStockLevel?: number;
  pricePerUnit?: number;
  description?: string;
  color?: string;
  size?: string;
}

export interface EventOwner {
  id?: number;
  name: string;
  phone?: string;
  email?: string;
  order?: number;
}

export interface EventDishSelection {
  dishId: number;
  quantity: number;
  subMealId?: number;
  categoryId?: number;
  isUpgrade?: boolean;
  isGift?: boolean;
  extraCharge?: number;
  notes?: string;
  isDraft: boolean;
  snapshotBasePrice?: number;
  snapshotClientPrice?: number;
  currentBasePrice?: number;  // fallback לפני snapshot
  // Joined
  dishName?: string;
  dishKosherType?: KosherType;
  categoryNameHebrew?: string;
}

export interface EventBoxSelection {
  id?: number;
  boxType: string;
  quantity: number;
  notes?: string;
}

export interface EventDeliveryNoteSelection {
  id?: number;
  templateId: number;
  note: string;
}

export interface Event {
  id: number;
  name: string;
  eventCategory?: string;
  menuType: MenuType;
  date: Date | string;
  eventTime?: string;
  hebrewDate?: string;
  daySequenceNumber?: number;
  daySequenceColor?: string;
  guestCount: number;
  status: EventStatus;
  address?: string;
  city?: string;
  isRealDishes?: boolean;  // כלים אמיתיים (לא חד"פ)
  isMorningSplit?: boolean;
  splitExtraCharge?: number;
  // Pricing fields
  basePricePerGuest?: number;
  realDishesExtraPerGuest?: number;  // תוספת כלים אמיתיים
  calculatedPrice?: number;  // מחיר מחושב אוטומטית
  finalPrice?: number;  // מחיר סופי (ניתן לעריכה)
  discountPercent?: number;  // אחוז הנחה
  discountAmount?: number;  // סכום ההנחה
  totalPrice?: number;  // legacy
  notes?: string;
  owners?: EventOwner[];
  dishes?: EventDishSelection[];
  createdAt?: Date;
  // Computed fields
  estimatedProfit?: number;
  isStockReduced?: boolean;
  waiterCount?: number;  // 2 מלצרים לכל 50 סועדים
  tableCount?: number;   // שולחן לכל 8 סועדים
  floor?: number;
  venueName?: string;
  hasElevator?: boolean;
  accessCode?: string;
  onsiteContactName?: string;
  onsiteContactPhone?: string;
  hallOwnerName?: string;
  hallOwnerPhone?: string;
  seatingSides?: SeatingSide[];
  hasNearbyParking?: boolean;
  hasBackEntrance?: boolean;
  requiresCarts?: boolean;
  accessNotes?: string;
  dishwareType?: string;
  deliveryContentsNotes?: string;
  lastMinuteItems?: string;
  equipmentDropoffLocation?: string;
  checkRefrigerator?: boolean;
  checkFreezer?: boolean;
  checkHotPlate?: boolean;
  connectGas?: boolean;
  putInRefrigerator?: boolean;
  putInFreezer?: boolean;
  putOnHotPlate?: boolean;
  countBoxes?: boolean;
  checkDrinks?: boolean;
  checkRolls?: boolean;
  deliverySpecialNotes?: string;
  selectedDeliveryNoteTemplateIds?: number[];
  deliveryNotes?: EventDeliveryNoteSelection[];
  boxes?: EventBoxSelection[];
  totalBoxes?: number;
}

export interface HebrewDateParts {
  day: number;
  month: number;
  year: number;
}

export interface CalendarDay {
  date: Date;
  hebrewDateLabel: string;
  hebrewDay: number;
  hebrewMonth: number;
  hebrewYear: number;
  isToday: boolean;
  isPast: boolean;
  events: Event[];
}

// Unit Conversion for settings
export interface UnitConversion {
  id: number;
  fromUnit: string;
  toUnit: string;
  factor: number;
  isSystem: boolean;
  description?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface ConversionResult {
  originalValue: number;
  originalUnit: string;
  convertedValue: number;
  targetUnit: string;
  conversionPath: string[];
}
