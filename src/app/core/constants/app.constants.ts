// Application constants for PlanMyEvents

export const CATEGORIES = [
  'עיקרית',
  'ראשונה',
  'תוספת',
  'קינוח',
  'משקה',
  'חטיף'
] as const;

export const KOSHER_TYPES = [
  'חלבי',
  'בשרי',
  'פרווה'
] as const;

export const EVENT_TYPES = [
  'שבת',
  'שבע ברכות',
  'ברית',
  'בוקר',
  'אחר'
] as const;

export const UNITS = [
  'גרם',
  'ליטר',
  'יחידות',
  'כפות',
  'כוסות',
  'מ"ל',
  'ק"ג'
] as const;

export const INVENTORY_STATUS = [
  'במלאי',
  'אזל',
  'מלאי-נמוך'
] as const;

export type Category = typeof CATEGORIES[number];
export type KosherType = typeof KOSHER_TYPES[number];
export type EventType = typeof EVENT_TYPES[number];
export type Unit = typeof UNITS[number];
export type InventoryStatus = typeof INVENTORY_STATUS[number];
