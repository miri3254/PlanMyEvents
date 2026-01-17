import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { Observable, Subject, takeUntil, map } from 'rxjs';
import { MenubarModule } from 'primeng/menubar';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { InputNumberModule } from 'primeng/inputnumber';
import { SelectModule } from 'primeng/select';
import { DatePickerModule } from 'primeng/datepicker';
import { EventService } from '../../../services/event.service';
import { Event } from '../../../core/models';
import { LookupService } from '../../../core/services/lookup.service';

type EventFormState = {
  name: string;
  participants: number;
  eventType: string;
  foodType: string;
  eventDate: Date | null;
  hebrewDate: string;
};

@Component({
  selector: 'app-navigation',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MenubarModule,
    ButtonModule,
    DialogModule,
    InputTextModule,
    InputNumberModule,
    SelectModule,
    DatePickerModule,
    FormsModule
  ],
  template: `
    <div class="nav-wrapper" dir="rtl">
      <!-- Gradient Header Bar -->
      <div class="gradient-header"></div>

      <!-- Main Navigation -->
      <div class="nav-container">
        <!-- Logo -->
        <div class="logo-section" routerLink="/">
          <div class="logo-icon">
            <i class="pi pi-calendar"></i>
          </div>
          <div class="logo-text">
            <h2>PlanMyEvents</h2>
            <span class="logo-subtitle">תכנון אירועים חכם</span>
          </div>
        </div>

        <!-- Menu Items -->
        <div class="menu-items">
          <a routerLink="/" 
             routerLinkActive="active"
             [routerLinkActiveOptions]="{exact: true}"
             class="menu-item">
            <i class="pi pi-chart-bar"></i>
            <span>לוח בקרה</span>
          </a>
          <a routerLink="/dishes" 
             routerLinkActive="active"
             class="menu-item">
            <i class="pi pi-star"></i>
            <span>מנות</span>
          </a>
          <a routerLink="/products" 
             routerLinkActive="active"
             class="menu-item">
            <i class="pi pi-shopping-cart"></i>
            <span>מוצרים</span>
          </a>
          <a routerLink="/tools" 
             routerLinkActive="active"
             class="menu-item">
            <i class="pi pi-box"></i>
            <span>כלים</span>
          </a>
          <a routerLink="/cart" 
             routerLinkActive="active"
             class="menu-item">
            <i class="pi pi-shopping-bag"></i>
            <span>עגלה</span>
          </a>
          <a routerLink="/events" 
             routerLinkActive="active"
             class="menu-item">
            <i class="pi pi-calendar-plus"></i>
            <span>אירועים</span>
          </a>
          <a routerLink="/settings" 
             routerLinkActive="active"
             class="menu-item">
            <i class="pi pi-cog"></i>
            <span>הגדרות</span>
          </a>
        </div>

        <!-- Actions -->
        <div class="nav-actions">
          <!-- Current Event Display -->
          <div *ngIf="currentEvent$ | async as event" class="current-event-badge">
            <i class="pi pi-users"></i>
            <span>{{ event.name }} ({{ event.participants }} אורחים)</span>
          </div>

          <!-- Event Selector -->
          <p-select
            [options]="eventOptions"
            [(ngModel)]="selectedEventId"
            (onChange)="onEventChange($event)"
            placeholder="בחר אירוע"
            optionLabel="label"
            optionValue="value"
            [style]="{'min-width': '200px'}"
            class="event-selector">
          </p-select>

          <!-- New Event Button -->
          <p-button
            label="אירוע חדש"
            icon="pi pi-plus"
            (onClick)="showEventDialog = true"
            [raised]="true"
            severity="primary"
            class="new-event-btn">
          </p-button>
        </div>
      </div>
    </div>

    <!-- Create Event Dialog -->
    <p-dialog
      [(visible)]="showEventDialog"
      [modal]="true"
      [rtl]="true"
      [style]="{width: '600px', minHeight: '500px'}"
      [contentStyle]="{overflow: 'visible'}"
      header="צור אירוע חדש"
      [draggable]="false">
      
      <div class="event-form">
        <!-- Event Name -->
        <div class="form-field">
          <label for="eventName">שם האירוע *</label>
          <input
            id="eventName"
            type="text"
            pInputText
            [(ngModel)]="newEvent.name"
            placeholder="לדוגמה: שבת חתן"
            class="w-full" />
        </div>

        <!-- Number of Participants -->
        <div class="form-field">
          <label for="participants">מספר משתתפים *</label>
          <p-inputnumber
            id="participants"
            [(ngModel)]="newEvent.participants"
            [min]="1"
            [max]="1000"
            [step]="5"
            class="w-full">
          </p-inputnumber>
        </div>

        <!-- Event Date -->
        <div class="form-field">
          <label for="eventDate">תאריך האירוע *</label>
          <p-datepicker
            id="eventDate"
            [(ngModel)]="newEvent.eventDate"
            (onSelect)="onDateChange($event)"
            [showIcon]="true"
            [touchUI]="true"
            dateFormat="dd/mm/yy"
            appendTo="body"
            class="w-full">
          </p-datepicker>
          <small class="text-600">התאריך העברי יעודכן אוטומטית וניתן לעריכה.</small>
        </div>

        <!-- Event Type -->
        <div class="form-field">
          <label for="eventType">סוג אירוע *</label>
          <p-select
            id="eventType"
            [options]="eventTypeOptions"
            [(ngModel)]="newEvent.eventType"
            placeholder="בחר סוג אירוע"
            optionLabel="label"
            optionValue="value"
            class="w-full">
          </p-select>
        </div>

        <!-- Hebrew Date -->
        <div class="form-field">
          <label for="hebrewDate">תאריך עברי</label>
          <input
            id="hebrewDate"
            type="text"
            pInputText
            [(ngModel)]="newEvent.hebrewDate"
            placeholder="לדוגמה: י״ד בטבת תשפ״ו"
            class="w-full" />
        </div>

        <!-- Food Type -->
        <div class="form-field">
          <label for="foodType">סוג אוכל *</label>
          <p-select
            id="foodType"
            [options]="foodTypeOptions"
            [(ngModel)]="newEvent.foodType"
            placeholder="בחר סוג אוכל"
            optionLabel="label"
            optionValue="value"
            class="w-full">
          </p-select>
        </div>
      </div>

      <ng-template pTemplate="footer">
        <div class="dialog-footer">
          <p-button
            label="ביטול"
            severity="secondary"
            (onClick)="closeEventDialog()"
            [text]="true">
          </p-button>
          <p-button
            label="צור אירוע"
            icon="pi pi-check"
            (onClick)="createEvent()"
            [disabled]="!isFormValid()"
            severity="primary">
          </p-button>
        </div>
      </ng-template>
    </p-dialog>
  `,
  styles: [`
    .nav-wrapper {
      position: sticky;
      top: 0;
      z-index: 1000;
      background: white;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
    }

    .gradient-header {
      height: 4px;
      width: 100%;
      background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    }

    .nav-container {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 24px;
      gap: 24px;
      max-width: 1400px;
      margin: 0 auto;
    }

    .logo-section {
      display: flex;
      align-items: center;
      gap: 12px;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .logo-section:hover {
      transform: translateY(-2px);
    }

    .logo-icon {
      width: 48px;
      height: 48px;
      background: linear-gradient(135deg, var(--primary), var(--primary-dark));
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 1.5rem;
      box-shadow: var(--shadow-glow);
    }

    .logo-text h2 {
      margin: 0;
      font-size: 1.25rem;
      background: linear-gradient(135deg, var(--primary), var(--primary-dark));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .logo-subtitle {
      font-size: 0.75rem;
      color: var(--muted-foreground);
      display: block;
      margin-top: -4px;
    }

    .menu-items {
      display: flex;
      gap: 8px;
      flex: 1;
    }

    .menu-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 16px;
      border-radius: 8px;
      text-decoration: none;
      color: var(--foreground);
      font-weight: 500;
      transition: all 0.3s ease;
      border: 2px solid transparent;
    }

    .menu-item:hover {
      background: var(--primary-light);
      color: var(--primary);
    }

    .menu-item.active {
      background: linear-gradient(135deg, var(--primary), var(--primary-dark));
      color: white;
      box-shadow: var(--shadow-glow);
    }

    .menu-item i {
      font-size: 1.1rem;
    }

    .nav-actions {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .current-event-badge {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      background: linear-gradient(135deg, 
        hsla(24, 95%, 53%, 0.1), 
        hsla(14, 90%, 48%, 0.1));
      border: 2px solid hsla(24, 95%, 53%, 0.2);
      border-radius: 8px;
      color: var(--primary);
      font-weight: 600;
      font-size: 0.875rem;
    }

    .event-selector {
      min-width: 200px;
    }

    .new-event-btn {
      background: linear-gradient(135deg, var(--primary), var(--primary-dark));
      border: none;
      box-shadow: var(--shadow-glow);
    }

    /* Event Form Styles */
    .event-form {
      display: flex;
      flex-direction: column;
      gap: 20px;
      padding: 10px 0;
    }

    .form-field {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .form-field label {
      font-weight: 600;
      color: var(--foreground);
      font-size: 0.9rem;
    }

    .w-full {
      width: 100%;
    }

    .dialog-footer {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
    }

    /* Responsive */
    @media (max-width: 968px) {
      .menu-items {
        display: none;
      }

      .current-event-badge {
        display: none;
      }
    }

    @media (max-width: 768px) {
      .nav-container {
        padding: 10px 16px;
      }

      .logo-text h2 {
        font-size: 1rem;
      }

      .logo-subtitle {
        display: none;
      }

      .event-selector {
        min-width: 150px;
      }
    }
  `]
})
export class NavigationComponent implements OnInit, OnDestroy {
  events$!: Observable<Event[]>;
  currentEvent$!: Observable<Event | null>;

  eventOptions: any[] = [];
  selectedEventId: string | null = null;

  private readonly destroy$ = new Subject<void>();

  showEventDialog = false;
  newEvent: EventFormState;

  eventTypeOptions: { label: string; value: string }[] = [];
  foodTypeOptions: { label: string; value: string }[] = [];

  constructor(
    private eventService: EventService,
    private lookupService: LookupService
  ) {
    this.newEvent = this.getDefaultEventForm();
  }

  ngOnInit(): void {
    this.events$ = this.eventService.events$;
    this.currentEvent$ = this.eventService.currentEvent$;

    // Subscribe to events to build options
    this.events$
      .pipe(takeUntil(this.destroy$))
      .subscribe(events => {
      this.eventOptions = [
        { label: 'ללא אירוע', value: null },
        ...events.map(event => ({
          label: `${event.name} (${event.participants} אורחים)`,
          value: event.id
        }))
      ];
    });

    // Subscribe to current event
    this.currentEvent$
      .pipe(takeUntil(this.destroy$))
      .subscribe(event => {
        this.selectedEventId = event?.id || null;
      });

    this.lookupService.lookup$
      .pipe(takeUntil(this.destroy$))
      .subscribe(data => {
        this.eventTypeOptions = data.eventTypes.map(type => ({
          label: type,
          value: type
        }));

        this.foodTypeOptions = [
          ...data.kosherTypes.map(type => ({ label: type, value: type })),
          { label: 'כל הסוגים', value: 'כל הסוגים' }
        ];

        if (
          this.newEvent.eventType &&
          !data.eventTypes.includes(this.newEvent.eventType)
        ) {
          this.newEvent.eventType = data.eventTypes[0] || '';
        }

        if (
          this.newEvent.foodType &&
          ![...data.kosherTypes, 'כל הסוגים'].includes(this.newEvent.foodType)
        ) {
          this.newEvent.foodType = data.kosherTypes[0] || 'כל הסוגים';
        }
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onEventChange(event: any): void {
    if (this.selectedEventId) {
      this.eventService.setCurrentEvent(this.selectedEventId);
    }
  }

  closeEventDialog(): void {
    this.showEventDialog = false;
    this.resetForm();
  }

  createEvent(): void {
    if (this.isFormValid()) {
      const eventId = this.eventService.createEvent({
        ...this.newEvent,
        eventDate: this.newEvent.eventDate || undefined
      });
      this.eventService.setCurrentEvent(eventId);
      this.closeEventDialog();
    }
  }

  resetForm(): void {
    this.newEvent = this.getDefaultEventForm();
  }

  isFormValid(): boolean {
    return !!(
      this.newEvent.name &&
      this.newEvent.participants > 0 &&
      this.newEvent.eventType &&
      this.newEvent.foodType &&
      this.newEvent.eventDate
    );
  }

  onDateChange(date: Date): void {
    if (date) {
      this.newEvent.hebrewDate = this.formatHebrewDate(date);
    }
  }

  private getDefaultEventForm(): EventFormState {
    const defaultEventType = this.lookupService.getList('eventTypes')[0] || '';
    const defaultKosher =
      this.lookupService.getList('kosherTypes')[0] || 'כל הסוגים';
    const now = new Date();

    return {
      name: '',
      participants: 10,
      eventType: defaultEventType,
      foodType: defaultKosher,
      eventDate: now,
      hebrewDate: this.formatHebrewDate(now)
    };
  }

  private formatHebrewDate(date?: Date | null): string {
    if (!date) {
      return '';
    }

    try {
      return new Intl.DateTimeFormat('he-IL-u-ca-hebrew', {
        day: 'numeric',
        month: 'long'
      }).format(date);
    } catch {
      return '';
    }
  }
}
