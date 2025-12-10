import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { EventService } from '../../core/services/event.service';
import { Event, CartItem, Dish } from '../../core/models';
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
  dishes: Dish[] = [];
  
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
    // Load events and cart items
    const refreshEvents = () => {
      this.events = this.eventService.getEventsSorted();
      console.log('Loaded and sorted events:', this.events);
    };

    this.eventService.events$.subscribe(() => refreshEvents());
    this.eventService.currentEvent$.subscribe(() => refreshEvents());

    this.eventService.cart$.subscribe(cart => {
      this.cartItems = cart;
      console.log('Loaded cart items:', cart);
    });
    
    this.eventService.dishes$.subscribe(dishes => {
      this.dishes = dishes;
      console.log('Loaded dishes:', dishes);
    });
  }

  getCartItemsForEvent(eventId: string): CartItem[] {
    return this.cartItems.filter(item => item.eventId === eventId);
  }

  getDishById(dishId: string): Dish | null {
    const fromCache = this.dishes.find(dish => dish.id === dishId);
    if (fromCache) {
      return fromCache;
    }
    return this.eventService.getDishById(dishId) || null;
  }

  getEventTotal(eventId: string): number {
    const eventCartItems = this.getCartItemsForEvent(eventId);
    const total = eventCartItems.reduce((total, item) => {
      const dish = this.getDishById(item.dishId);
      // Single-selection model: each dish added once with base price
      return total + (dish?.estimatedPrice || 0);
    }, 0);
    console.log(`Event ${eventId} total:`, total);
    return total;
  }

  getTotalCartItems(eventId: string): number {
    // Count number of unique dishes (single-selection model)
    const eventCartItems = this.getCartItemsForEvent(eventId);
    return eventCartItems.length;
  }

  getGrandTotal(): number {
    return this.events.reduce((total, event) => total + this.getEventTotal(event.id), 0);
  }

  getTotalEvents(): number {
    return this.events.length;
  }

  getTotalDishes(): number {
    // Count total unique dishes across all events
    return this.cartItems.length;
  }

  getTotalPeopleCount(): number {
    // Calculate total people covered by all dishes in cart
    return this.cartItems.reduce((total, item) => total + item.peopleCount, 0);
  }

  // Quantity updates removed - single-selection model with fixed peopleCount

  removeCartItem(item: CartItem): void {
    this.confirmationService.confirm({
      message: `האם אתה בטוח שברצונך להסיר את ${item.dishName} מהתפריט?`,
      header: 'אישור הסרה',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'כן',
      rejectLabel: 'לא',
      accept: () => {
        this.eventService.removeDishFromCart(item.dishId, item.eventId);
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
        this.eventService.clearCart(eventId);
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