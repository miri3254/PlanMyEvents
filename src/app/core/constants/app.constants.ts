// Application constants and default lookup configuration for PlanMyEvents
import { EventStatus } from '../models';

export interface DashboardWidgetConfig {
  id: string;
  label: string;
  enabled: boolean;
  description?: string;
  accentColor?: string;
}

export type DashboardWidgetGroup = 'dashboardSections' | 'dashboardMetrics';

export interface LookupData {
  dishCategories: string[];
  kosherTypes: string[];
  measurementUnits: string[];
  productCategories: string[];
  inventoryStatuses: string[];
  eventTypes: string[];
  toolCategories: string[];
  toolSubCategories: string[];
  dashboardSections: DashboardWidgetConfig[];
  dashboardMetrics: DashboardWidgetConfig[];
}

export type LookupListKey = keyof Pick<LookupData,
  'dishCategories' |
  'kosherTypes' |
  'measurementUnits' |
  'productCategories' |
  'inventoryStatuses' |
  'eventTypes' |
  'toolCategories' |
  'toolSubCategories'
>;

export const DEFAULT_DISH_CATEGORIES = [
  'עיקרית',
  'ראשונה',
  'תוספת',
  'קינוח',
  'משקה',
  'חטיף'
] as const;

export const DEFAULT_KOSHER_TYPES = [
  'חלבי',
  'בשרי',
  'פרווה'
] as const;

export const DEFAULT_EVENT_TYPES = [
  'שבת',
  'שבע ברכות',
  'ברית',
  'בוקר',
  'אחר'
] as const;

export const DEFAULT_MEASUREMENT_UNITS = [
  'גרם',
  'ליטר',
  'יחידות',
  'כפות',
  'כוסות',
  'מ"ל',
  'ק"ג'
] as const;

export const DEFAULT_INVENTORY_STATUSES = [
  'במלאי',
  'אזל',
  'מלאי-נמוך'
] as const;

export const DEFAULT_PRODUCT_CATEGORIES = [
  'מוצרי מזון',
  'משקאות',
  'חטיפים',
  'מוצרי חלב'
] as const;

export const DEFAULT_TOOL_CATEGORIES = [
  'מפות',
  'כלי הגשה',
  'צלחות',
  'סכו"ם',
  'כוסות',
  'קערות',
  'מגשים',
  'אחר'
] as const;

export const DEFAULT_TOOL_SUB_CATEGORIES = [
  'חד"פ',
  'אמיתי'
] as const;

export const DEFAULT_DASHBOARD_SECTIONS: DashboardWidgetConfig[] = [
  {
    id: 'eventsOverview',
    label: 'אירועים פעילים',
    enabled: true,
    description: 'תצוגת מצב האירועים והאירוע הנבחר',
    accentColor: 'hsl(210, 100%, 56%)'
  },
  {
    id: 'dishesSummary',
    label: 'מנות פעילות',
    enabled: true,
    description: 'כרטיסי תובנות על המנות והעגלה',
    accentColor: 'hsl(24, 95%, 53%)'
  },
  {
    id: 'inventoryHealth',
    label: 'בריאות מלאי',
    enabled: true,
    description: 'סטטוסים של מלאי וזמינות מוצרים',
    accentColor: 'hsl(142, 76%, 48%)'
  },
  {
    id: 'quickLinks',
    label: 'קישורים מהירים',
    enabled: true,
    description: 'קיצורי הדרך לפעולות ניהול עיקריות',
    accentColor: 'hsl(280, 61%, 56%)'
  }
];

export const DEFAULT_DASHBOARD_METRICS: DashboardWidgetConfig[] = [
  {
    id: 'budgetProjection',
    label: 'הערכת עלויות',
    enabled: true,
    description: 'חישוב אומדן עלויות לפי תפריט האירוע',
    accentColor: 'hsl(45, 100%, 51%)'
  },
  {
    id: 'guestExperience',
    label: 'מדד חווית אורחים',
    enabled: false,
    description: 'מעקב אחרי שביעות רצון ומגמות תפריט',
    accentColor: 'hsl(340, 80%, 60%)'
  },
  {
    id: 'prepTimeline',
    label: 'תזמון הכנות',
    enabled: true,
    description: 'תכנון לו"ז הכנות והגשות',
    accentColor: 'hsl(200, 90%, 45%)'
  }
];

export const DEFAULT_LOOKUP_DATA: LookupData = {
  dishCategories: [...DEFAULT_DISH_CATEGORIES],
  kosherTypes: [...DEFAULT_KOSHER_TYPES],
  measurementUnits: [...DEFAULT_MEASUREMENT_UNITS],
  productCategories: [...DEFAULT_PRODUCT_CATEGORIES],
  inventoryStatuses: [...DEFAULT_INVENTORY_STATUSES],
  eventTypes: [...DEFAULT_EVENT_TYPES],
  toolCategories: [...DEFAULT_TOOL_CATEGORIES],
  toolSubCategories: [...DEFAULT_TOOL_SUB_CATEGORIES],
  dashboardSections: DEFAULT_DASHBOARD_SECTIONS.map(section => ({ ...section })),
  dashboardMetrics: DEFAULT_DASHBOARD_METRICS.map(metric => ({ ...metric }))
};

// Legacy exports kept for backward compatibility in templates/components.
export const CATEGORIES = [...DEFAULT_LOOKUP_DATA.dishCategories];
export const KOSHER_TYPES = [...DEFAULT_LOOKUP_DATA.kosherTypes];
export const EVENT_TYPES = [...DEFAULT_LOOKUP_DATA.eventTypes];
export const UNITS = [...DEFAULT_LOOKUP_DATA.measurementUnits];
export const INVENTORY_STATUS = [...DEFAULT_LOOKUP_DATA.inventoryStatuses];

export type Category = (typeof DEFAULT_DISH_CATEGORIES)[number];
export type KosherType = (typeof DEFAULT_KOSHER_TYPES)[number];
export type EventType = (typeof DEFAULT_EVENT_TYPES)[number];
export type Unit = (typeof DEFAULT_MEASUREMENT_UNITS)[number];
export type InventoryStatus = (typeof DEFAULT_INVENTORY_STATUSES)[number];

export type StatusSeverity = 'success' | 'info' | 'warning' | 'danger' | 'secondary' | 'contrast';

export interface EventStatusDisplay {
  value: EventStatus;
  label: string;
  severity: StatusSeverity;
  icon: string;
}

export const EVENT_STATUS_ORDER: EventStatus[] = [
  'בהמתנה לאישור',
  'אושר',
  'עבר',
  'התבטל',
  'הסתיים'
];

export const EVENT_STATUS_DISPLAY: Record<EventStatus, EventStatusDisplay> = {
  'בהמתנה לאישור': {
    value: 'בהמתנה לאישור',
    label: 'בהמתנה לאישור',
    severity: 'warning',
    icon: 'pi pi-clock'
  },
  'אושר': {
    value: 'אושר',
    label: 'אושר',
    severity: 'success',
    icon: 'pi pi-check-circle'
  },
  'עבר': {
    value: 'עבר',
    label: 'עבר',
    severity: 'info',
    icon: 'pi pi-flag'
  },
  'התבטל': {
    value: 'התבטל',
    label: 'התבטל',
    severity: 'danger',
    icon: 'pi pi-times-circle'
  },
  'הסתיים': {
    value: 'הסתיים',
    label: 'הסתיים',
    severity: 'secondary',
    icon: 'pi pi-calendar-times'
  }
};

export const EVENT_STATUS_OPTIONS = EVENT_STATUS_ORDER.map(status => ({
  label: EVENT_STATUS_DISPLAY[status].label,
  value: status
}));
