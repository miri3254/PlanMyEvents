import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { EventService, Event, CartItem } from '../../services/event.service';
import { Dish } from '../../models/dish.model';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { PanelModule } from 'primeng/panel';
import { BadgeModule } from 'primeng/badge';
import { DividerModule } from 'primeng/divider';
import { InputNumberModule } from 'primeng/inputnumber';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ConfirmationService, MessageService } from 'primeng/api';
import { TableModule } from 'primeng/table';
import { TooltipModule } from 'primeng/tooltip';
import { DialogModule } from 'primeng/dialog';

@Component({
  selector: 'app-cart',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    ButtonModule,
    CardModule,
    TagModule,
    PanelModule,
    BadgeModule,
    DividerModule,
    InputNumberModule,
    ToastModule,
    ConfirmDialogModule,
    TableModule,
    TooltipModule,
    DialogModule
  ],
  templateUrl: './cart.html',
  styleUrls: ['./cart.scss'],
  providers: [ConfirmationService, MessageService]
})
export class CartComponent implements OnInit {
  events: Event[] = [];
  cartItems: CartItem[] = [];
  mockDishes: Dish[] = []; // Mock dishes for now
  
  // Dialog states
  showEventDetails: boolean = false;
  selectedEvent: Event | null = null;
  selectedEventCart: CartItem[] = [];

  constructor(
    private eventService: EventService,
    private confirmationService: ConfirmationService,
    private messageService: MessageService
  ) {}

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    // Load mock dishes
    this.loadMockDishes();
    
    // Load events and cart items
    this.eventService.events$.subscribe(events => {
      this.events = events;
    });

    this.eventService.cart$.subscribe(cart => {
      this.cartItems = cart;
    });
  }

  loadMockDishes(): void {
    // Mock dishes data - in real app this would come from a dishes service
    this.mockDishes = [
      {
        id: '1',
        name: 'פנקייק קלאסי',
        description: 'פנקייק רך וטעים לארוחת בוקר',
        estimatedPrice: 25,
        category: 'מנה ראשונה',
        kosherType: 'חלבי',
        servingSize: 4,
        ingredients: [],
        equipment: [],
        isActive: true,
        createdDate: new Date(),
        lastModified: new Date()
      },
      {
        id: '2',
        name: 'טוסט פרנצ׳',
        description: 'טוסט מטוגן בביצה וחלב',
        estimatedPrice: 18,
        category: 'מנה ראשונה',
        kosherType: 'חלבי',
        servingSize: 2,
        ingredients: [],
        equipment: [],
        isActive: true,
        createdDate: new Date(),
        lastModified: new Date()
      },
      {
        id: '3',
        name: 'שניצל עוף',
        description: 'שניצל עוף פריך וטעים',
        estimatedPrice: 35,
        category: 'מנה עיקרית',
        kosherType: 'בשרי',
        servingSize: 4,
        ingredients: [],
        equipment: [],
        isActive: true,
        createdDate: new Date(),
        lastModified: new Date()
      },
      {
        id: '4',
        name: 'סלט ירקות',
        description: 'סלט ירקות טריים וצבעוניים',
        estimatedPrice: 12,
        category: 'תוספת',
        kosherType: 'פרווה',
        servingSize: 6,
        ingredients: [],
        equipment: [],
        isActive: true,
        createdDate: new Date(),
        lastModified: new Date()
      },
      {
        id: '5',
        name: 'עוגת שוקולד',
        description: 'עוגת שוקולד עשירה וטעימה',
        estimatedPrice: 40,
        category: 'קינוח',
        kosherType: 'חלבי',
        servingSize: 8,
        ingredients: [],
        equipment: [],
        isActive: true,
        createdDate: new Date(),
        lastModified: new Date()
      }
    ];
  }

  getCartItemsForEvent(eventId: string): CartItem[] {
    return this.cartItems.filter(item => item.eventId === eventId);
  }

  getDishById(dishId: string): Dish | null {
    return this.mockDishes.find(dish => dish.id === dishId) || null;
  }

  getEventTotal(eventId: string): number {
    const eventCartItems = this.getCartItemsForEvent(eventId);
    return eventCartItems.reduce((total, item) => {
      const dish = this.getDishById(item.dishId);
      return total + (dish?.estimatedPrice || 0) * item.quantity;
    }, 0);
  }

  getTotalCartItems(eventId: string): number {
    const eventCartItems = this.getCartItemsForEvent(eventId);
    return eventCartItems.reduce((total, item) => total + item.quantity, 0);
  }

  getGrandTotal(): number {
    return this.events.reduce((total, event) => total + this.getEventTotal(event.id), 0);
  }

  getTotalEvents(): number {
    return this.events.length;
  }

  getTotalDishes(): number {
    return this.cartItems.reduce((total, item) => total + item.quantity, 0);
  }

  updateCartItemQuantity(item: CartItem, newQuantity: number): void {
    if (newQuantity <= 0) {
      this.removeCartItem(item);
    } else {
      this.eventService.updateCartItemQuantity(item.dishId, newQuantity);
      this.messageService.add({
        severity: 'success',
        summary: 'עודכן',
        detail: 'הכמות עודכנה בהצלחה'
      });
    }
  }

  removeCartItem(item: CartItem): void {
    this.confirmationService.confirm({
      message: `האם אתה בטוח שברצונך להסיר את ${item.dishName} מהתפריט?`,
      header: 'אישור הסרה',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'כן',
      rejectLabel: 'לא',
      accept: () => {
        this.eventService.removeDishFromCart(item.dishId);
        this.messageService.add({
          severity: 'success',
          summary: 'הוסר',
          detail: 'המנה הוסרה מהתפריט'
        });
      }
    });
  }

  clearEventCart(eventId: string): void {
    const event = this.events.find(e => e.id === eventId);
    if (!event) return;

    this.confirmationService.confirm({
      message: `האם אתה בטוח שברצונך לנקות את כל התפריט של "${event.name}"?`,
      header: 'אישור ניקוי תפריט',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'כן',
      rejectLabel: 'לא',
      accept: () => {
        const currentEventId = this.eventService.getCurrentEvent()?.id;
        this.eventService.setCurrentEvent(eventId);
        this.eventService.clearCart();
        if (currentEventId) {
          this.eventService.setCurrentEvent(currentEventId);
        }
        this.messageService.add({
          severity: 'success',
          summary: 'נוקה',
          detail: 'התפריט נוקה בהצלחה'
        });
      }
    });
  }

  deleteEvent(event: Event): void {
    this.confirmationService.confirm({
      message: `האם אתה בטוח שברצונך למחוק את האירוע "${event.name}" וכל התפריט שלו?`,
      header: 'אישור מחיקת אירוע',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'כן',
      rejectLabel: 'לא',
      accept: () => {
        this.eventService.deleteEvent(event.id);
        this.messageService.add({
          severity: 'success',
          summary: 'נמחק',
          detail: 'האירוע נמחק בהצלחה'
        });
      }
    });
  }

  viewEventDetails(event: Event): void {
    this.selectedEvent = event;
    this.selectedEventCart = this.getCartItemsForEvent(event.id);
    this.showEventDetails = true;
  }

  closeEventDetails(): void {
    this.showEventDetails = false;
    this.selectedEvent = null;
    this.selectedEventCart = [];
  }

  setCurrentEvent(eventId: string): void {
    this.eventService.setCurrentEvent(eventId);
    this.messageService.add({
      severity: 'info',
      summary: 'אירוע פעיל',
      detail: 'האירוע נבחר כאירוע פעיל'
    });
  }

  getCurrentEvent(): Event | null {
    return this.eventService.getCurrentEvent();
  }

  isCurrentEvent(eventId: string): boolean {
    const currentEvent = this.getCurrentEvent();
    return currentEvent?.id === eventId;
  }

  getEventTypeIcon(eventType: string): string {
    switch (eventType) {
      case 'שבת': return 'pi pi-sun';
      case 'שבע ברכות': return 'pi pi-heart';
      case 'ברית': return 'pi pi-star';
      case 'בוקר': return 'pi pi-clock';
      default: return 'pi pi-calendar';
    }
  }

  getFoodTypeColor(foodType: string): "success" | "info" | "warn" | "danger" | "secondary" | "contrast" | null {
    switch (foodType) {
      case 'בשרי': return 'danger';
      case 'חלבי': return 'info';
      case 'פרווה': return 'success';
      default: return 'secondary';
    }
  }

  getCategorySeverity(category: string): "success" | "info" | "warn" | "danger" | "secondary" | "contrast" | null {
    switch (category) {
      case 'מנה עיקרית': return 'contrast';
      case 'מנה ראשונה': return 'info';
      case 'תוספת': return 'secondary';
      case 'קינוח': return 'warn';
      default: return 'info';
    }
  }

  getKosherTypeSeverity(kosherType: string): "success" | "info" | "warn" | "danger" | "secondary" | "contrast" | null {
    switch (kosherType) {
      case 'חלבי': return 'info';
      case 'בשרי': return 'danger';
      case 'פרווה': return 'success';
      default: return 'secondary';
    }
  }
}