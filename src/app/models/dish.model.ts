export interface DishIngredient {
    productName: string;    // שם המוצר
    quantity: number;       // כמות נדרשת
    unit: string;          // יחידת מידה (גרם, ליטר, יחידות וכו')
}

export interface DishEquipment {
    name: string;          // שם הכלי/ציוד
    required: boolean;     // האם נדרש
}

export interface Dish {
    id?: string;           // מזהה ייחודי
    name: string;          // שם המנה
    description?: string;  // תיאור המנה
    estimatedPrice: number; // מחיר משוער למנה
    category: string;      // קטגוריה (עיקרית, תוספת, קינוח וכו')
    kosherType: string;    // סוג כשרות (חלבי, בשרי, פרווה)
    servingSize: number;   // כמות מנות בהכנה (למכמה אנשים)
    ingredients: DishIngredient[]; // רשימת מוצרים וכמויות
    equipment: DishEquipment[];    // רשימת כלים וציוד נדרש
    imageUrl?: string;     // תמונת המנה
    isActive: boolean;     // האם המנה פעילה
    createdDate?: Date;    // תאריך יצירה
    lastModified?: Date;   // תאריך עדכון אחרון
}

export interface EventDishSelection {
    dish: Dish;           // המנה שנבחרה
    quantity: number;     // כמות מנות לאירוע
    totalPrice: number;   // מחיר כולל למנה זו
}

export interface ShoppingListItem {
    productName: string;  // שם המוצר
    totalQuantity: number; // כמות כוללת נדרשת
    unit: string;         // יחידת מידה
    estimatedPrice: number; // מחיר משוער
    dishes: string[];     // רשימת מנות שדורשות מוצר זה
}