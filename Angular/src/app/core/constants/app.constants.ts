import {
  EventStatus,
  MenuType,
  KosherType,
  ProductCategory,
  UnitType,
  ToolCategory,
  ToolSubCategory,
  // DEFAULT_MENU_TYPES,
  EVENT_STATUSES,
  KOSHER_TYPES,
  PRODUCT_CATEGORIES,
  UNIT_TYPES,
  TOOL_CATEGORIES,
  TOOL_SUB_CATEGORIES,
  INVENTORY_STATUSES,
  EVENT_STATUS_DISPLAY,
  INVENTORY_STATUS_DISPLAY,
  StatusDisplay
} from '../models/enums';

// ============================================
// Dashboard Widget Config
// ============================================

export interface DashboardWidgetConfig {
  id: string;
  label: string;
  enabled: boolean;
  description?: string;
  accentColor?: string;
}

export type DashboardWidgetGroup = 'dashboardSections' | 'dashboardMetrics';

// ============================================
// Lookup Data - עם ערכי ברירת מחדל תואמים לבקאנד
// ============================================

export interface LookupData {
  kosherTypes: string[];
  measurementUnits: string[];
  productCategories: string[];
  inventoryStatuses: string[];
  eventStatuses: string[];
  toolCategories: string[];
  toolSubCategories: string[];
  dashboardSections: DashboardWidgetConfig[];
  dashboardMetrics: DashboardWidgetConfig[];
}

export type LookupListKey = keyof Pick<LookupData,
  'kosherTypes' | 'measurementUnits' |
  'productCategories' | 'inventoryStatuses' | 'eventStatuses' |
  'toolCategories' | 'toolSubCategories'
>;

// ברירות מחדל - תואמות בדיוק לבקאנד (menuTypes עכשיו דינמי!)
// DEFAULT_MENU_TYPES imported from enums.ts
export const DEFAULT_KOSHER_TYPES = [...KOSHER_TYPES] as const;
export const DEFAULT_EVENT_STATUSES = [...EVENT_STATUSES] as const;
export const DEFAULT_MEASUREMENT_UNITS = [...UNIT_TYPES] as const;
export const DEFAULT_PRODUCT_CATEGORIES = [...PRODUCT_CATEGORIES] as const;
export const DEFAULT_INVENTORY_STATUSES = [...INVENTORY_STATUSES] as const;
export const DEFAULT_TOOL_CATEGORIES = [...TOOL_CATEGORIES] as const;
export const DEFAULT_TOOL_SUB_CATEGORIES = [...TOOL_SUB_CATEGORIES] as const;

export const DEFAULT_DASHBOARD_SECTIONS: DashboardWidgetConfig[] = [
  { id: 'eventsOverview', label: 'אירועים פעילים', enabled: true, description: 'סקירת אירועים קרובים', accentColor: 'hsl(210, 100%, 56%)' },
  { id: 'dishesSummary', label: 'מנות פעילות', enabled: true, description: 'סיכום מנות במערכת', accentColor: 'hsl(24, 95%, 53%)' },
  { id: 'inventoryHealth', label: 'בריאות מלאי', enabled: true, description: 'מצב המלאי הכולל', accentColor: 'hsl(142, 76%, 48%)' },
  { id: 'quickLinks', label: 'קישורים מהירים', enabled: true, description: 'גישה מהירה לפעולות', accentColor: 'hsl(280, 61%, 56%)' }
];

export const DEFAULT_DASHBOARD_METRICS: DashboardWidgetConfig[] = [
  { id: 'budgetProjection', label: 'הערכת עלויות', enabled: true, description: 'תחזית תקציב', accentColor: 'hsl(45, 100%, 51%)' },
  { id: 'guestExperience', label: 'מדד חווית אורחים', enabled: false, description: 'מעקב חווית אורחים', accentColor: 'hsl(340, 80%, 60%)' },
  { id: 'prepTimeline', label: 'תזמון הכנות', enabled: true, description: 'ציר זמן הכנות', accentColor: 'hsl(200, 90%, 45%)' }
];

export const DEFAULT_LOOKUP_DATA: LookupData = {
  kosherTypes: [...DEFAULT_KOSHER_TYPES],
  measurementUnits: [...DEFAULT_MEASUREMENT_UNITS],
  productCategories: [...DEFAULT_PRODUCT_CATEGORIES],
  inventoryStatuses: [...DEFAULT_INVENTORY_STATUSES],
  eventStatuses: [...DEFAULT_EVENT_STATUSES],
  toolCategories: [...DEFAULT_TOOL_CATEGORIES],
  toolSubCategories: [...DEFAULT_TOOL_SUB_CATEGORIES],
  dashboardSections: DEFAULT_DASHBOARD_SECTIONS.map(s => ({ ...s })),
  dashboardMetrics: DEFAULT_DASHBOARD_METRICS.map(m => ({ ...m }))
};

// ============================================
// Event Status Display - תואם enums.ts
// ============================================

export type StatusSeverity = 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast';

export const EVENT_STATUS_ORDER: EventStatus[] = [...EVENT_STATUSES];

export const EVENT_STATUS_OPTIONS = EVENT_STATUS_ORDER.map(status => ({
  label: EVENT_STATUS_DISPLAY[status].label,
  value: status
}));

// ============================================
// Dropdown options helpers
// Note: MENU_TYPE_OPTIONS now uses DEFAULT_MENU_TYPES - for truly dynamic menu types,
// components should get fresh values from ApiLookupService
// ============================================

// export const MENU_TYPE_OPTIONS = DEFAULT_MENU_TYPES.map(t => ({ label: t, value: t }));
export const KOSHER_TYPE_OPTIONS = KOSHER_TYPES.map(t => ({ label: t, value: t }));
export const PRODUCT_CATEGORY_OPTIONS = PRODUCT_CATEGORIES.map(c => ({ label: c, value: c }));
export const UNIT_TYPE_OPTIONS = UNIT_TYPES.map(u => ({ label: u, value: u }));
export const TOOL_CATEGORY_OPTIONS = TOOL_CATEGORIES.map(c => ({ label: c, value: c }));
export const TOOL_SUB_CATEGORY_OPTIONS = TOOL_SUB_CATEGORIES.map(c => ({ label: c, value: c }));
export const INVENTORY_STATUS_OPTIONS = INVENTORY_STATUSES.map(s => ({ label: s, value: s }));
