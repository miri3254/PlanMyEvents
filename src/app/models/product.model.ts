export interface Product {
    id?: number;            // מזהה
    name: string;           // שם המוצר
    category: string;       // קטגוריה
    unit: string;           // יחידת מידה
    package_quantity?: number; // כמות באריזה
    price_per_unit?: number; // מחיר ליחידה
    estimated_price?: number; // מחיר מוערך
    quantity_in_stock?: number; // כמות במלאי
    min_stock_level?: number; // רמת מלאי מינימלית
    inventory_status: string; // סטטוס מלאי
    supplier?: string;       // ספק
    brand?: string;          // מותג
    barcode?: string;        // ברקוד
    notes?: string;          // הערות
    description?: string;    // תיאור
    kosher_type?: string;    // סוג כשרות
    created_at?: string;     // תאריך יצירה
    updated_at?: string;     // תאריך עדכון
    
    // Legacy camelCase support
    inventoryStatus?: string;
    packageQuantity?: number;
    estimatedPrice?: number;
}