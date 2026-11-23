// ============================================
// Centralized Enums - תואם בדיוק לבקאנד FastAPI
// ============================================

// סוגי תפריט - שם חופשי, טעון דינמית מ-menu_templates
// MenuType is a plain string alias - the value is the template's name (e.g. "תפריט שבת")
export type MenuType = string;

// סטטוס אירוע (EventStatus) - תואם app/core/enums.py
export const EVENT_STATUSES = ['טיוטה', 'מאושר', 'הסתיים', 'בוטל'] as const;
export type EventStatus = typeof EVENT_STATUSES[number];

// סוגי כשרות (KosherType) - תואם app/core/enums.py
export const KOSHER_TYPES = ['פרווה', 'בשרי', 'חלבי'] as const;
export type KosherType = typeof KOSHER_TYPES[number];

// קטגוריות מוצרים (ProductCategory) - תואם app/core/enums.py
export const PRODUCT_CATEGORIES = ['מוצרי חלב', 'מוצרי בשר', 'קטניות', 'שתיה', 'נוזלים', 'מוצרים יבשים', 'קפואים'] as const;
export type ProductCategory = typeof PRODUCT_CATEGORIES[number];

// יחידות מידה (UnitType) - תואם app/core/enums.py
export const UNIT_TYPES = ['ק"ג', 'גרם', 'מ"ג', 'ליטר', 'מ"ל', 'יחידות', 'אריזה', 'מגש', 'כוס', 'כף', 'כפית', 'קורט', 'חבילה'] as const;
export type UnitType = typeof UNIT_TYPES[number];

// קטגוריות כלים (ToolCategory) - תואם app/core/enums.py
export const TOOL_CATEGORIES = ['צלחות', 'כוסות', 'סכו"ם', 'מפות', 'כלי הגשה'] as const;
export type ToolCategory = typeof TOOL_CATEGORIES[number];

// תת-קטגוריות כלים (ToolSubCategory) - תואם app/core/enums.py
export const TOOL_SUB_CATEGORIES = ['אמיתי', 'חד פעמי'] as const;
export type ToolSubCategory = typeof TOOL_SUB_CATEGORIES[number];

// סטטוס מלאי - מחושב בבקאנד
export const INVENTORY_STATUSES = ['במלאי', 'מלאי נמוך', 'אין במלאי'] as const;
export type InventoryStatus = typeof INVENTORY_STATUSES[number];

// ============================================
// Display helpers
// ============================================

export interface StatusDisplay {
  value: string;
  label: string;
  severity: 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast';
  icon: string;
}

export const EVENT_STATUS_DISPLAY: Record<EventStatus, StatusDisplay> = {
  'טיוטה': { value: 'טיוטה', label: 'טיוטה', severity: 'secondary', icon: 'pi pi-pencil' },
  'מאושר': { value: 'מאושר', label: 'מאושר', severity: 'success', icon: 'pi pi-check-circle' },
  'הסתיים': { value: 'הסתיים', label: 'הסתיים', severity: 'info', icon: 'pi pi-flag' },
  'בוטל': { value: 'בוטל', label: 'בוטל', severity: 'danger', icon: 'pi pi-times-circle' }
};

export const INVENTORY_STATUS_DISPLAY: Record<string, StatusDisplay> = {
  'במלאי': { value: 'במלאי', label: 'במלאי', severity: 'success', icon: 'pi pi-check' },
  'מלאי נמוך': { value: 'מלאי נמוך', label: 'מלאי נמוך', severity: 'warn', icon: 'pi pi-exclamation-triangle' },
  'אין במלאי': { value: 'אין במלאי', label: 'אין במלאי', severity: 'danger', icon: 'pi pi-times' }
};
