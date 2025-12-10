// Application constants and default lookup configuration for PlanMyEvents

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
  dashboardSections: DashboardWidgetConfig[];
  dashboardMetrics: DashboardWidgetConfig[];
}

export type LookupListKey = keyof Pick<LookupData,
  'dishCategories' |
  'kosherTypes' |
  'measurementUnits' |
  'productCategories' |
  'inventoryStatuses' |
  'eventTypes'
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
