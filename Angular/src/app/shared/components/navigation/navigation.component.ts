import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { Observable, Subject, take } from 'rxjs';
import { MenubarModule } from 'primeng/menubar';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { InputNumberModule } from 'primeng/inputnumber';
import { SelectModule } from 'primeng/select';
import { DatePickerModule } from 'primeng/datepicker';
import { TooltipModule } from 'primeng/tooltip';
import { ApiEventService } from '../../../services/api-event.service';
import { ApiMenuService } from '../../../services/api-menu.service';
import { ApiLookupService } from '../../../services/api-lookup.service';
import { MenuTemplate } from '../../../models/menu.model';
import { Event, EventCreate } from '../../../core/models';
import { ConnectionStatusService, ConnectionStatus } from '../../../core/services/connection-status.service';

type EventFormState = {
  name: string;
  eventCategory: string;
  guestCount: number;
  menuType: string;
  eventDate: Date | null;
  hebrewDate: string;
  address: string;
  city: string;
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
    FormsModule,
    TooltipModule
  ],
  template: `
    <!-- Connection Error Banner -->
    <div 
      *ngIf="(connectionStatus$ | async) as status"
      class="connection-banner"
      [class.connected]="status.isConnected"
      [class.disconnected]="!status.isConnected"
      [class.show-banner]="!status.isConnected && showConnectionBanner">
      <div class="banner-content" *ngIf="!status.isConnected && showConnectionBanner">
        <i class="pi pi-exclamation-triangle"></i>
        <span class="banner-message">
          <strong>אין חיבור לשרת!</strong> 
          המערכת לא מצליחה להתחבר לשרת. חלק מהפונקציות לא יעבדו כראוי.
          <br>
          <small>אנא בדוק את החיבור לאינטרנט או פנה לתמיכה טכנית.</small>
        </span>
        <button class="banner-close" (click)="dismissBanner()" pTooltip="הסתר הודעה">
          <i class="pi pi-times"></i>
        </button>
      </div>
    </div>

    <div class="nav-wrapper" dir="rtl">
      <!-- Gradient Header Bar -->
      <div class="gradient-header"></div>

      <!-- Main Navigation -->
      <div class="nav-container">
        <!-- Logo -->
        <div class="logo-section" routerLink="/">
          <img class="logo-image" src="assets/logo.png" alt="PlanMyEvents" />
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
          <a routerLink="/events" 
             routerLinkActive="active"
             class="menu-item">
            <i class="pi pi-calendar-plus"></i>
            <span>אירועים</span>
          </a>
          <a routerLink="/menus" 
             routerLinkActive="active"
             class="menu-item">
            <i class="pi pi-book"></i>
            <span>תפריטים</span>
          </a>
          <a routerLink="/backup" 
             routerLinkActive="active"
             class="menu-item"
             pTooltip="גיבוי וייצוא נתונים">
            <i class="pi pi-download"></i>
            <span>גיבוי</span>
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
          <!-- Connection Status Indicator -->
          <div 
            *ngIf="(connectionStatus$ | async) as status"
            class="connection-status-indicator"
            [class.connected]="status.isConnected"
            [class.disconnected]="!status.isConnected"
            [pTooltip]="status.message"
            tooltipPosition="bottom"
            (click)="retryConnection()">
            <i class="pi" [class.pi-wifi]="status.isConnected" [class.pi-wifi-off]="!status.isConnected"></i>
            <span class="status-text">{{ status.isConnected ? 'מחובר' : 'מנותק' }}</span>
          </div>

          <!-- New Event Button -->
          <p-button
            label="אירוע חדש"
            icon="pi pi-calendar-plus"
            (onClick)="navigateToNewEvent()"
            [raised]="true"
            severity="primary"
            styleClass="new-event-action">
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

        <!-- Number of Guests -->
        <div class="form-field">
          <label for="guestCount">מספר אורחים *</label>
          <p-inputnumber
            id="guestCount"
            [(ngModel)]="newEvent.guestCount"
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
          <small class="text-600">התאריך העברי יעודכן אוטומטית.</small>
        </div>

        <!-- Menu Type -->
        <div class="form-field">
          <label for="eventCategory">קטגוריית אירוע *</label>
          <p-select
            id="eventCategory"
            [options]="eventCategories"
            [(ngModel)]="newEvent.eventCategory"
            placeholder="בחר קטגוריית אירוע"
            class="w-full">
          </p-select>
        </div>

        <!-- Menu Type -->
        <div class="form-field">
          <label for="menuType">שם תפריט *</label>
          <p-select
            id="menuType"
            [options]="menuTemplateSelectItems"
            [(ngModel)]="newEvent.menuType"
            placeholder="בחר תפריט"
            optionLabel="label"
            optionValue="value"
            class="w-full">
            <ng-template pTemplate="item" let-item>
              <div>
                <div>{{ item.label }}</div>
                <small style="color: var(--text-color-secondary)">
                  {{ item.template.kosher_type }}
                  <span *ngIf="item.template.min_guests > 1"> &middot; מינ. {{ item.template.min_guests }}</span>
                  <span *ngIf="item.template.base_price_per_guest"> &middot; &#x20AA;{{ item.template.base_price_per_guest }}/אורח</span>
                </small>
              </div>
            </ng-template>
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

        <!-- Address -->
        <div class="form-field">
          <label for="address">כתובת</label>
          <input
            id="address"
            type="text"
            pInputText
            [(ngModel)]="newEvent.address"
            placeholder="רחוב ומספר"
            class="w-full" />
        </div>

        <!-- City -->
        <div class="form-field">
          <label for="city">עיר</label>
          <input
            id="city"
            type="text"
            pInputText
            [(ngModel)]="newEvent.city"
            placeholder="שם העיר"
            class="w-full" />
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
    /* Connection Banner Styles */
    .connection-banner {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      z-index: 2000;
      transform: translateY(-100%);
      transition: transform 0.3s ease;
    }

    .connection-banner.show-banner.disconnected {
      transform: translateY(0);
    }

    .connection-banner.disconnected .banner-content {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 16px;
      padding: 16px 24px;
      background: linear-gradient(135deg, #dc2626, #b91c1c);
      color: white;
      font-size: 1rem;
      text-align: center;
      box-shadow: 0 4px 20px rgba(220, 38, 38, 0.4);
    }

    .connection-banner .banner-content i.pi-exclamation-triangle {
      font-size: 1.5rem;
      animation: pulse 1.5s infinite;
    }

    .connection-banner .banner-message {
      flex: 1;
      text-align: right;
    }

    .connection-banner .banner-message small {
      opacity: 0.9;
    }

    .connection-banner .banner-close {
      background: rgba(255, 255, 255, 0.2);
      border: none;
      border-radius: 50%;
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      color: white;
      transition: background 0.2s;
    }

    .connection-banner .banner-close:hover {
      background: rgba(255, 255, 255, 0.3);
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }

    /* Connection Status Indicator */
    .connection-status-indicator {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 8px 14px;
      border-radius: 20px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .connection-status-indicator.connected {
      background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(22, 163, 74, 0.15));
      color: #16a34a;
      border: 1px solid rgba(34, 197, 94, 0.3);
    }

    .connection-status-indicator.connected:hover {
      background: linear-gradient(135deg, rgba(34, 197, 94, 0.25), rgba(22, 163, 74, 0.25));
    }

    .connection-status-indicator.disconnected {
      background: linear-gradient(135deg, rgba(220, 38, 38, 0.15), rgba(185, 28, 28, 0.15));
      color: #dc2626;
      border: 1px solid rgba(220, 38, 38, 0.3);
      animation: attention 2s infinite;
    }

    .connection-status-indicator.disconnected:hover {
      background: linear-gradient(135deg, rgba(220, 38, 38, 0.25), rgba(185, 28, 28, 0.25));
    }

    @keyframes attention {
      0%, 100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.4); }
      50% { box-shadow: 0 0 0 6px rgba(220, 38, 38, 0); }
    }

  .connection-status-indicator .pi {
      font-size: 1rem;
    }

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
      cursor: pointer;
      transition: all 0.3s ease;
      flex-shrink: 0;
    }

    .logo-section:hover {
      transform: translateY(-2px);
    }

    .logo-image {
      display: block;
      height: 56px;
      width: auto;
      max-width: min(240px, 32vw);
      object-fit: contain;
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

    :host ::ng-deep .new-event-action {
      box-sizing: border-box;
      min-height: 44px !important;
      height: 44px !important;
      padding: 0 18px 0 20px !important;
      border: 0 !important;
      outline: 0 !important;
      border-radius: 999px !important;
      background: linear-gradient(135deg, #f97316 0%, #ea580c 52%, #c2410c 100%) !important;
      color: #ffffff !important;
      font-weight: 800;
      letter-spacing: 0;
      box-shadow: 0 12px 24px rgba(234, 88, 12, 0.24) !important;
      transition: none !important;
      transform: none !important;
      filter: none !important;
      white-space: nowrap;
    }

    :host ::ng-deep .new-event-action .p-button-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 26px;
      height: 26px;
      margin-inline-end: 8px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.22);
      font-size: 0.95rem;
    }

    :host ::ng-deep .new-event-action .p-button-label {
      line-height: 1;
    }

    :host ::ng-deep .new-event-action:hover,
    :host ::ng-deep .new-event-action:enabled:hover,
    :host ::ng-deep .new-event-action:not(:disabled):hover,
    :host ::ng-deep .new-event-action:active,
    :host ::ng-deep .new-event-action:focus,
    :host ::ng-deep .new-event-action:focus-visible {
      min-height: 44px !important;
      height: 44px !important;
      padding: 0 18px 0 20px !important;
      border: 0 !important;
      outline: 0 !important;
      background: linear-gradient(135deg, #f97316 0%, #ea580c 52%, #c2410c 100%) !important;
      color: #ffffff !important;
      box-shadow: 0 12px 24px rgba(234, 88, 12, 0.24) !important;
      filter: none !important;
      transform: none !important;
      transition: none !important;
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

      .logo-image {
        height: 44px;
        max-width: 180px;
      }

      .event-selector {
        min-width: 150px;
      }
    }
  `]
})
export class NavigationComponent implements OnInit, OnDestroy {
  connectionStatus$!: Observable<ConnectionStatus>;

  showConnectionBanner = true;

  private readonly destroy$ = new Subject<void>();

  showEventDialog = false;
  newEvent: EventFormState;

  menuTemplates: MenuTemplate[] = [];
  eventCategories: string[] = [];

  get menuTemplateSelectItems(): { label: string; value: string; template: MenuTemplate }[] {
    return this.menuTemplates.map(t => ({ label: t.name, value: t.name, template: t }));
  }

  constructor(
    private router: Router,
    private eventService: ApiEventService,
    private menuService: ApiMenuService,
    private lookupService: ApiLookupService,
    private connectionStatusService: ConnectionStatusService
  ) {
    this.newEvent = this.getDefaultEventForm();
  }

  ngOnInit(): void {
    this.connectionStatus$ = this.connectionStatusService.status$;

    // Load menu templates for the quick-create dialog
    this.menuService.getMenuTemplates()
      .pipe(take(1))
      .subscribe(templates => {
        this.menuTemplates = templates;
        if (!this.newEvent.menuType && templates.length > 0) {
          this.newEvent.menuType = templates[0].name;
        }
      });

    this.lookupService.getAllLookupData()
      .pipe(take(1))
      .subscribe(data => {
        this.eventCategories = data.event_categories || [];
        if (!this.newEvent.eventCategory) {
          this.newEvent.eventCategory = this.eventCategories[0] || '';
        }
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  dismissBanner(): void {
    this.showConnectionBanner = false;
  }

  navigateToNewEvent(): void {
    this.router.navigate(['/events'], { queryParams: { createEvent: '1' } });
  }

  retryConnection(): void {
    this.showConnectionBanner = true;
    this.connectionStatusService.forceCheck().subscribe();
  }

  closeEventDialog(): void {
    this.showEventDialog = false;
    this.resetForm();
  }

  createEvent(): void {
    if (this.isFormValid()) {
      const payload: EventCreate = {
        name: this.newEvent.name,
        event_category: this.newEvent.eventCategory,
        menu_type: this.newEvent.menuType,
        date: this.newEvent.eventDate?.toISOString() || new Date().toISOString(),
        guest_count: this.newEvent.guestCount,
        address: this.newEvent.address || undefined,
        city: this.newEvent.city || undefined,
        status: 'טיוטה'
      };
      this.eventService.createEvent(payload)
        .pipe(take(1))
        .subscribe({
          next: (created: any) => {
            this.closeEventDialog();
            this.router.navigate(['/events'], { queryParams: { openEvent: created.id } });
          },
          error: () => {
            this.closeEventDialog();
          }
        });
    }
  }

  resetForm(): void {
    this.newEvent = this.getDefaultEventForm();
  }

  isFormValid(): boolean {
    return !!(
      this.newEvent.name &&
      this.newEvent.eventCategory &&
      this.newEvent.guestCount > 0 &&
      this.newEvent.menuType &&
      this.newEvent.eventDate
    );
  }

  onDateChange(date: Date): void {
    if (date) {
      this.newEvent.hebrewDate = this.formatHebrewDate(date);
    }
  }

  private getDefaultEventForm(): EventFormState {
    const now = new Date();

    return {
      name: '',
      eventCategory: this.eventCategories[0] || '',
      guestCount: 10,
      menuType: '',
      eventDate: now,
      hebrewDate: this.formatHebrewDate(now),
      address: '',
      city: ''
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
