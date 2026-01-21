export interface DishIngredient {
    id?: number;            // מזהה המרכיב במסד הנתונים
    product_id?: number;    // מזהה מוצר (snake_case להתאמה לבקאנד)
    name?: string;          // שם המוצר - Backend מחזיר name
    quantity: number;       // כמות נדרשת
    unit: string;           // יחידת מידה (גרם, ליטר, יחידות וכו')
    // Legacy support
    productId?: string;     
    productName?: string;   
}

export interface DishEquipment {
    id?: number;           // מזהה
    tool_id?: number;      // מזהה כלי
    name: string;          // שם הכלי/ציוד
    quantity: number;      // כמות
    required?: boolean;    // האם נדרש (legacy)
}

export interface ServingDish {
    id?: number;           // מזהה
    tool_id?: number;      // מזהה כלי
    name: string;          // שם הכלי להגשה
    quantity: number;      // כמות
    category?: string;     // קטגוריה
}

export interface Dish {
    id?: number;           // מזהה ייחודי (number לא string)
    name: string;          // שם המנה
    description?: string;  // תיאור המנה
    category: string;      // קטגוריה (עיקרית, תוספת, קינוח וכו')
    kosher_type: string;   // סוג כשרות (חלבי, בשרי, פרווה) - snake_case
    serving_size: number;  // גודל מנה - snake_case
    price_per_unit?: number; // מחיר ליחידה
    estimated_price?: number; // מחיר מוערך
    image_url?: string;    // תמונת המנה - snake_case
    is_active: boolean;    // האם המנה פעילה - snake_case
    created_at?: string;   // תאריך יצירה
    updated_at?: string;   // תאריך עדכון
    ingredients: DishIngredient[]; // רשימת מוצרים וכמויות
    equipment: DishEquipment[];    // רשימת כלים וציוד נדרש
    serving_dishes?: ServingDish[];    // כלים להגשה - snake_case
    
    // Legacy camelCase support for backwards compatibility
    kosherType?: string;   
    servingSize?: number;  
    imageUrl?: string;     
    isActive?: boolean;    
    estimatedPrice?: number;
    createdDate?: Date;    
    lastModified?: Date;   
    servingDescription?: string;      
    servingIngredients?: DishIngredient[]; 
    servingDishes?: ServingDish[];    
    waiterNotes?: string;             
}

export interface EventDishSelection {
    dish: Dish;           // המנה שנבחרה
    quantity: number;     // כמות מנות לאירוע
    totalPrice: number;   // מחיר כולל למנה זו
}

export interface ShoppingListItem {
    product_id?: number;  // מזהה מוצר
    name: string;         // שם המוצר
    quantity: number;     // כמות כוללת נדרשת
    unit: string;         // יחידת מידה
    estimated_price: number; // מחיר משוער
    category?: string;    // קטגוריה
    // Legacy support
    productName?: string; 
    totalQuantity?: number;
    estimatedPrice?: number;
    dishes?: string[];     // רשימת מנות שדורשות מוצר זה
}