// Core data models for PlanMyEvents

export interface DishIngredient {
  productName: string;
  quantity: number;
  unit: string; // גרם/ליטר/יחידות/כפות/כוסות/מ"ל/ק"ג
}

export interface DishEquipment {
  name: string;
  required: boolean;
}

export interface ServingDish {
  name: string;          // שם הכלי להגשה
  quantity: number;      // כמות
  category: string;      // קטגוריה
}

export interface Dish {
  id: string;
  name: string;
  description?: string;
  estimatedPrice: number;
  category: string; // עיקרית/ראשונה/תוספת/קינוח/משקה/חטיף
  kosherType: string; // חלבי/בשרי/פרווה
  servingSize: number;
  ingredients: DishIngredient[];
  equipment: DishEquipment[];
  imageUrl?: string;
  isActive: boolean;
  createdDate: Date;
  lastModified: Date;
  servingSizeServings?: number; // Optional - number of people this dish serves
  // Serving fields
  servingDescription?: string;      // תיאור צורת הגשה
  servingIngredients?: DishIngredient[]; // רכיבים להגשה
  servingDishes?: ServingDish[];    // כלים להגשה
  waiterNotes?: string;             // הערות למלצר
}

export interface Product {
  id: string;
  name: string;
  inventoryStatus: string; // במלאי/אזל/מלאי-נמוך
  brand: string;
  packageQuantity: number;
  estimatedPrice: number;
  category: string;
  supplier: string;
}

export interface Tool {
  id: string;
  name: string;                    // שם הכלי
  brand: string;                   // מותג
  category: string;                // קטגוריה (מפות, כלי הגשה, וכולי)
  subCategory: string;             // תת קטגוריה (חד"פ / אמיתי)
  inventoryStatus: string;         // סטטוס (במלאי / כמות נמוכה / אזל)
  estimatedPrice: number;          // מחיר משוער
  description?: string;            // תיאור / הערות
  notes?: string;                  // הערות נוספות
  quantity?: number;               // כמות במלאי
}

export type EventStatus =
  | 'בהמתנה לאישור'
  | 'אושר'
  | 'עבר'
  | 'התבטל'
  | 'הסתיים';

export interface HebrewDateParts {
  day: number;
  month: number;
  year: number;
}

export interface Event {
  id: string;
  name: string;
  participants: number;
  eventType: string; // שבת/שבע ברכות/ברית/בוקר/אחר
  foodType: string; // חלבי/בשרי/פרווה/כל הסוגים
  dishes: { dishId: string; quantity: number }[];
  createdAt: Date;
  eventDate: Date | string;
  hebrewDate?: string;
  status: EventStatus;
  notes?: string;
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
