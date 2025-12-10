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

export interface Event {
  id: string;
  name: string;
  participants: number;
  eventType: string; // שבת/שבע ברכות/ברית/בוקר/אחר
  foodType: string; // חלבי/בשרי/פרווה/כל הסוגים
  dishes: { dishId: string; quantity: number }[];
  createdAt: Date;
  eventDate: String | Date;
  notes?: string;
}

export interface CartItem {
  dishId: string;
  dishName: string;
  peopleCount: number;  // Number of people this dish serves
  eventId: string;
  estimatedPrice?: number;  // Optional - can be calculated from dish
}

export interface ShoppingListItem {
  productName: string;
  totalQuantity: number;
  unit: string;
  estimatedPrice: number;
  dishes: string[];
}
