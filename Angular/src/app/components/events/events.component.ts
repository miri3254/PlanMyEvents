import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { PanelModule } from 'primeng/panel';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { BadgeModule } from 'primeng/badge';
import { DialogModule } from 'primeng/dialog';
import { TableModule } from 'primeng/table';
import { Tabs, TabPanel, TabList, TabPanels, Tab } from 'primeng/tabs';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { SelectButtonModule } from 'primeng/selectbutton';
import { SelectModule } from 'primeng/select';
import { SkeletonModule } from 'primeng/skeleton';
import { TooltipModule } from 'primeng/tooltip';
import { InputTextModule } from 'primeng/inputtext';
import { InputNumberModule } from 'primeng/inputnumber';
import { DatePickerModule } from 'primeng/datepicker';
import { LoadingOverlayComponent } from '../../shared/loading-overlay/loading-overlay.component';
import { MessageService, ConfirmationService } from 'primeng/api';
import { Subject, Observable, EMPTY, of } from 'rxjs';
import { take, takeUntil, catchError, map, switchMap, tap } from 'rxjs/operators';
import { ApiEventService } from '../../services/api-event.service';
import { ApiProductService } from '../../services/api-product.service';
import { ApiLookupService } from '../../services/api-lookup.service';
import { ApiMenuService } from '../../services/api-menu.service';
import { ApiToolService } from '../../services/api-tool.service';
import { MenuTemplate } from '../../models/menu.model';
import { 
  ApiEvent, 
  ApiProduct,
  ApiTool,
  EventCreate, 
  EventUpdate, 
  EventStatusUpdate, 
  EventsQueryParams,
  DeliveryNoteTemplate,
  LookupValue,
  EventCalculationSummary,
  RollSplit,
  EventToolSetItem,
  SeatingSide
} from '../../core/models/api.models';
import { CalendarDay, HebrewDateParts, EventStatus, Event, EventOwner, EVENT_STATUSES } from '../../core/models';
import {
  buildHebrewMonthOptions,
  formatHebrewMonthTitle,
  getHebrewMonthLength,
  getHebrewYearsRange,
  hebrewPartsToGregorian,
  renderHebrewLabelFromParts,
  sanitizeHebrewParts,
  shiftHebrewMonth,
  toHebrewParts,
  hebrewDayToLetters,
  hebrewYearToGematriya
} from '../../core/utils/hebrew-date.util';

type ManualCalculationToolRow = {
  tool_id?: number | null;
  name?: string;
  quantity: number;
  is_reusable: boolean;
  notes?: string;
};

// Helper function to convert ApiEvent to local Event
function mapApiEventToEvent(apiEvent: ApiEvent): Event {
  const owners = apiEvent.owners?.map(o => ({
    name: o.name,
    phone: o.phone,
    email: o.email,
    order: o.order
  })) || [];
  
  return {
    id: apiEvent.id,
    name: apiEvent.name,
    eventCategory: apiEvent.event_category,
    menuType: apiEvent.menu_type,
    guestCount: apiEvent.guest_count,
    date: apiEvent.date,
    eventTime: apiEvent.event_time,
    hebrewDate: apiEvent.hebrew_date,
    daySequenceNumber: apiEvent.day_sequence_number,
    daySequenceColor: apiEvent.day_sequence_color,
    status: apiEvent.status as EventStatus,
    notes: apiEvent.notes,
    address: apiEvent.address,
    city: apiEvent.city,
    isRealDishes: apiEvent.is_real_dishes,
    isMorningSplit: apiEvent.is_morning_split,
    splitExtraCharge: apiEvent.split_extra_charge,
    // Pricing fields
    basePricePerGuest: apiEvent.base_price_per_guest,
    realDishesExtraPerGuest: apiEvent.real_dishes_extra_per_guest ?? 0,
    calculatedPrice: apiEvent.calculated_price ?? 0,
    finalPrice: apiEvent.final_price ?? undefined,
    discountPercent: apiEvent.discount_percent ?? 0,
    discountAmount: apiEvent.discount_amount ?? 0,
    totalPrice: apiEvent.total_price,
    owners: owners,
    dishes: apiEvent.dishes?.map(d => ({
      dishId: d.dish_id,
      quantity: d.quantity,
      isGift: d.is_gift,
      isDraft: d.is_draft,
      snapshotBasePrice: d.snapshot_base_price,
      snapshotClientPrice: d.snapshot_client_price,
      currentBasePrice: d.current_base_price,
      dishName: d.dish_name,
      dishKosherType: d.dish_kosher_type,
      categoryNameHebrew: d.category_name_hebrew
    })) || [],
    createdAt: apiEvent.created_at ? new Date(apiEvent.created_at) : undefined,
    waiterCount: apiEvent.waiter_count,
    tableCount: apiEvent.table_count,
    venueName: apiEvent.venue_name,
    floor: apiEvent.floor,
    hasElevator: apiEvent.has_elevator,
    accessCode: apiEvent.access_code,
    onsiteContactName: apiEvent.onsite_contact_name,
    onsiteContactPhone: apiEvent.onsite_contact_phone,
    hallOwnerName: apiEvent.hall_owner_name,
    hallOwnerPhone: apiEvent.hall_owner_phone,
    seatingSides: apiEvent.seating_sides || [],
    hasNearbyParking: apiEvent.has_nearby_parking,
    hasBackEntrance: apiEvent.has_back_entrance,
    requiresCarts: apiEvent.requires_carts,
    accessNotes: apiEvent.access_notes,
    dishwareType: apiEvent.dishware_type,
    deliveryContentsNotes: apiEvent.delivery_contents_notes,
    lastMinuteItems: apiEvent.last_minute_items,
    equipmentDropoffLocation: apiEvent.equipment_dropoff_location,
    checkRefrigerator: apiEvent.check_refrigerator,
    checkFreezer: apiEvent.check_freezer,
    checkHotPlate: apiEvent.check_hot_plate,
    connectGas: apiEvent.connect_gas,
    putInRefrigerator: apiEvent.put_in_refrigerator,
    putInFreezer: apiEvent.put_in_freezer,
    putOnHotPlate: apiEvent.put_on_hot_plate,
    countBoxes: apiEvent.count_boxes,
    checkDrinks: apiEvent.check_drinks,
    checkRolls: apiEvent.check_rolls,
    deliverySpecialNotes: apiEvent.delivery_special_notes,
    selectedDeliveryNoteTemplateIds: apiEvent.selected_delivery_note_template_ids || [],
    deliveryNotes: apiEvent.delivery_notes?.map(note => ({
      id: note.id,
      templateId: note.template_id,
      note: note.note
    })) || [],
    boxes: apiEvent.boxes?.map(box => ({
      id: box.id,
      boxType: box.box_type,
      quantity: box.quantity,
      notes: box.notes
    })) || [],
    totalBoxes: apiEvent.total_boxes || 0,
  };
}

// Event status constants - תואם בקנד
const EVENT_STATUS_OPTIONS: { label: string; value: EventStatus }[] = [
  { label: 'טיוטה', value: 'טיוטה' },
  { label: 'אושר', value: 'מאושר' },
  { label: 'עבר', value: 'הסתיים' },
  { label: 'בוטל', value: 'בוטל' }
];

const EVENT_STATUS_DISPLAY: { [key in EventStatus]: { label: string; severity: string; icon: string; class: string } } = {
  'טיוטה': { label: 'טיוטה', severity: 'secondary', icon: 'pi pi-file-edit', class: 'draft' },
  'מאושר': { label: 'אושר', severity: 'info', icon: 'pi pi-check-circle', class: 'approved' },
  'הסתיים': { label: 'עבר', severity: 'success', icon: 'pi pi-history', class: 'past' },
  'בוטל': { label: 'בוטל', severity: 'danger', icon: 'pi pi-ban', class: 'cancelled' }
};

const EVENT_STATUS_TRANSITIONS: Record<EventStatus, EventStatus[]> = {
  [EVENT_STATUS_OPTIONS[0].value]: [EVENT_STATUS_OPTIONS[1].value, EVENT_STATUS_OPTIONS[3].value],
  [EVENT_STATUS_OPTIONS[1].value]: [EVENT_STATUS_OPTIONS[2].value, EVENT_STATUS_OPTIONS[3].value, EVENT_STATUS_OPTIONS[0].value],
  [EVENT_STATUS_OPTIONS[2].value]: [],
  [EVENT_STATUS_OPTIONS[3].value]: [EVENT_STATUS_OPTIONS[0].value],
} as Record<EventStatus, EventStatus[]>;

type EventFilterKey = 'all' | 'past' | 'cancelled' | 'completed';
type CalendarViewMode = 'gregorian' | 'hebrew';
type DateInputMode = 'gregorian' | 'hebrew';
type EventTimeFilter = 'all' | 'today' | 'thisWeek' | 'thisMonth' | 'upcoming' | 'past';
type EventDishFilter = 'all' | 'withDishes' | 'withoutDishes' | 'withGiftDishes';
type EventDetailTab = 'overview' | 'edit' | 'calculations';

interface EventFilterButton {
  key: EventFilterKey;
  label: string;
}

interface EventFormModel {
  id?: number;
  name: string;
  eventCategory: string;
  guestCount: number;
  menuType: string;
  status: EventStatus;
  notes?: string;
  eventDate: Date;
  eventTime?: string;
  hebrewParts: HebrewDateParts;
  hebrewLabel: string;
  
  // מיקום
  address?: string;
  city?: string;
  
  // כלים
  isRealDishes: boolean;  // כלים אמיתיים (לא חד"פ)
  
  // בעלי אירוע דינמיים
  owners: EventOwner[];
  venueName?: string;
  floor?: number;
  hasElevator: boolean;
  accessCode?: string;
  onsiteContactName?: string;
  onsiteContactPhone?: string;
  hallOwnerName?: string;
  hallOwnerPhone?: string;
  seatingSides: SeatingSide[];
  hasNearbyParking: boolean;
  hasBackEntrance: boolean;
  requiresCarts: boolean;
  accessNotes?: string;
  dishwareType: string;
  deliveryContentsNotes?: string;
  lastMinuteItems?: string;
  equipmentDropoffLocation?: string;
  checkRefrigerator: boolean;
  checkFreezer: boolean;
  checkHotPlate: boolean;
  connectGas: boolean;
  putInRefrigerator: boolean;
  putInFreezer: boolean;
  putOnHotPlate: boolean;
  countBoxes: boolean;
  checkDrinks: boolean;
  checkRolls: boolean;
  deliverySpecialNotes?: string;
  selectedDeliveryNoteTemplateIds: number[];
  boxes: { boxType: string; quantity: number; notes?: string }[];
}

// ממשק לבעל אירוע בטופס
interface FormEventOwner {
  name: string;
  phone: string;
  email: string;
}

interface CalendarRange {
  start: Date;
  end: Date;
}

@Component({
  selector: 'app-events',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    PanelModule,
    ButtonModule,
    TagModule,
    BadgeModule,
    DialogModule,
    TableModule,
    Tabs,
    TabPanel,
    TabList,
    TabPanels,
    Tab,
    ToastModule,
    ConfirmDialogModule,
    SelectButtonModule,
    SelectModule,
    SkeletonModule,
    TooltipModule,
    InputTextModule,
    InputNumberModule,
    DatePickerModule,
    LoadingOverlayComponent
  ],
  templateUrl: './events.component.html',
  styleUrls: ['./events.component.scss'],
  providers: [MessageService, ConfirmationService]
})
export class EventsComponent implements OnInit, OnDestroy {
  getGiftDishes(event: Event) {
    return (event.dishes || []).filter(dish => dish.isGift);
  }

  readonly statusOptions = EVENT_STATUS_OPTIONS;
  readonly statusDisplay = EVENT_STATUS_DISPLAY;
  readonly filterButtons: EventFilterButton[] = [
    { key: 'all', label: 'כל האירועים' },
    { key: 'past', label: 'אירועים שהיו' },
    { key: 'cancelled', label: 'אירועים שהתבטלו' },
    { key: 'completed', label: 'אירועים שהסתיימו' },
  ];
  // מוסתר זמנית: תמיכה בתאריכים עבריים
  // readonly viewModeOptions = [
  //   { label: 'לוח לועזי', value: 'gregorian' },
  //   { label: 'תאריכים עבריים', value: 'hebrew' }
  // ];
  readonly dateModeOptions = [
    { label: 'תאריך לועזי', value: 'gregorian' },
    { label: 'תאריך עברי', value: 'hebrew' }
  ];
  readonly pageLayoutOptions = [
    { label: 'רשימת אירועים', value: 'list-first', icon: 'pi pi-list' },
    { label: 'לוח חודשי', value: 'calendar-first', icon: 'pi pi-calendar' }
  ];
  readonly timeFilterOptions: { label: string; value: EventTimeFilter }[] = [
    { label: 'כל התאריכים', value: 'all' },
    { label: 'היום', value: 'today' },
    { label: 'השבוע', value: 'thisWeek' },
    { label: 'החודש', value: 'thisMonth' },
    { label: 'עתידיים', value: 'upcoming' },
    { label: 'עברו', value: 'past' }
  ];
  readonly dishFilterOptions: { label: string; value: EventDishFilter }[] = [
    { label: 'כל האירועים', value: 'all' },
    { label: 'עם מנות', value: 'withDishes' },
    { label: 'בלי מנות', value: 'withoutDishes' },
    { label: 'עם מנות מתנה', value: 'withGiftDishes' }
  ];
  readonly weekDays = ['א׳', 'ב׳', 'ג׳', 'ד׳', 'ה׳', 'ו׳', 'ש׳'];

  readonly eventSequenceColors = ['orange', 'green', 'purple', 'sky', 'red'];
  readonly dishwareTypeOptions = [
    { label: 'כלים אמיתיים', value: 'כלים אמיתיים' },
    { label: 'חד פעמי', value: 'חד פעמי' },
    { label: 'משולב', value: 'משולב' }
  ];
  readonly deliveryChecklist = [
    { label: 'לבדוק מקרר', key: 'checkRefrigerator' },
    { label: 'לבדוק מקפיא', key: 'checkFreezer' },
    { label: 'לבדוק פלטה', key: 'checkHotPlate' },
    { label: 'לחבר גז', key: 'connectGas' },
    { label: 'להכניס למקרר', key: 'putInRefrigerator' },
    { label: 'להכניס למקפיא', key: 'putInFreezer' },
    { label: 'לשים על פלטה', key: 'putOnHotPlate' },
    { label: 'לספור ארגזים', key: 'countBoxes' },
    { label: 'לבדוק שתיה', key: 'checkDrinks' },
    { label: 'לבדוק לחמניות', key: 'checkRolls' }
  ];

  events: Event[] = [];
  filteredEvents: Event[] = [];
  calendarCells: (CalendarDay | null)[] = [];
  calendarEvents: Event[] = [];
  selectedFilter: EventFilterKey = 'all';
  eventSearchTerm = '';
  selectedStatusFilter: EventStatus | 'all' = 'all';
  selectedCategoryFilter = 'all';
  selectedMenuFilter = 'all';
  selectedTimeFilter: EventTimeFilter = 'all';
  selectedDishFilter: EventDishFilter = 'all';
  viewMode: CalendarViewMode = 'gregorian';
  pageLayout: 'list-first' | 'calendar-first' = 'list-first';
  currentMonth = new Date();
  currentHebrewMonth: HebrewDateParts = (() => {
    const now = toHebrewParts(new Date());
    return { day: 1, month: now.month, year: now.year };
  })();
  calendarRange: CalendarRange = this.buildGregorianRange(new Date());
  loadingCalendar = false;
  loadingList = true;

  detailVisible = false;
  selectedEvent: Event | null = null;
  selectedStatus: EventStatus | null = null;
  activeDetailTab: EventDetailTab = 'overview';
  statusLocked = false;
  statusUpdating = false;
  calculationSummary: EventCalculationSummary | null = null;
  calculationLoading = false;
  manualCalculationTools: ManualCalculationToolRow[] = [];
  availableTools: ApiTool[] = [];
  rollProducts: ApiProduct[] = [];

  // Event form state
  eventFormVisible = false;
  eventFormMode: 'create' | 'edit' = 'create';
  eventFormSubmitting = false;
  dateInputMode: DateInputMode = 'gregorian';
  hebrewMonthOptions = buildHebrewMonthOptions(this.currentHebrewMonth.year);
  hebrewYearOptions = this.buildHebrewYearOptions(this.currentHebrewMonth.year);
  hebrewDayOptions = this.buildHebrewDayOptions(1, this.currentHebrewMonth.year);

  // Go to Date dialog state
  goToDateDialogVisible = false;
  goToDateValue: string = '';

  // טעינת תבניות תפריט
  menuTemplates: MenuTemplate[] = [];
  loadingMenuTemplates = false;
  eventCategories: string[] = [];
  loadingEventCategories = false;
  deliveryNoteTemplates: DeliveryNoteTemplate[] = [];
  eventForm!: EventFormModel;

  private readonly destroy$ = new Subject<void>();

  constructor(
    private readonly router: Router,
    private readonly route: ActivatedRoute,
    private readonly eventService: ApiEventService,
    private readonly productService: ApiProductService,
    private readonly lookupService: ApiLookupService,
    private readonly menuService: ApiMenuService,
    private readonly toolService: ApiToolService,
    private readonly messageService: MessageService,
    private readonly confirmationService: ConfirmationService
  ) {
    this.eventForm = this.buildDefaultFormModel();
  }

  ngOnInit(): void {
    this.loadMenuTemplates();
    this.loadEventCategories();
    this.loadDeliveryNoteTemplates();
    this.loadToolsForManualRows();
    this.loadRollProducts();
    this.refreshHebrewSelectors(this.currentHebrewMonth.year);

    this.loadEvents();
    this.updateCalendarRange();
    
    // בדיקה אם יש query param לפתיחת פופאפ אירוע
    this.route.queryParams
      .pipe(takeUntil(this.destroy$))
      .subscribe(params => {
        if (params['openEvent']) {
          const eventId = +params['openEvent'];
          this.openEventById(eventId);
          // ניקוי הפרמטר מה-URL
          this.router.navigate([], {
            relativeTo: this.route,
            queryParams: {},
            replaceUrl: true
          });
        } else if (params['createEvent']) {
          this.openCreateForm();
          // ניקוי הפרמטר מה-URL
          this.router.navigate([], {
            relativeTo: this.route,
            queryParams: {},
            replaceUrl: true
          });
        }
      });
  }

  loadEvents(): void {
    this.loadingList = true;
    this.eventService.getEvents()
      .pipe(
        takeUntil(this.destroy$),
        map((response: any) => response.items || []),
        map((apiEvents: ApiEvent[]) => apiEvents.map(mapApiEventToEvent))
      )
      .subscribe({
        next: (events: Event[]) => {
          this.events = this.normalizeEventSequences(events);
          this.loadingList = false;
          this.applyFilter();
          this.syncCalendarWithSnapshot();
        },
        error: (error: any) => {
          console.error('Error loading events:', error);
          this.loadingList = false;
        }
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  changeMonth(step: number): void {
    if (this.viewMode === 'gregorian') {
      const nextMonth = new Date(this.currentMonth);
      nextMonth.setMonth(this.currentMonth.getMonth() + step, 1);
      this.currentMonth = nextMonth;
    } else {
      this.currentHebrewMonth = shiftHebrewMonth(this.currentHebrewMonth, step);
    }
    this.updateCalendarRange();
    this.syncCalendarWithSnapshot();
  }

  goToToday(): void {
    const now = new Date();
    if (this.viewMode === 'gregorian') {
      this.currentMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    } else {
      const nowHebrew = toHebrewParts(now);
      this.currentHebrewMonth = { day: 1, month: nowHebrew.month, year: nowHebrew.year };
    }
    this.updateCalendarRange();
    this.syncCalendarWithSnapshot();
  }

  // Go to Date dialog methods
  openGoToDateDialog(): void {
    this.goToDateValue = '';
    this.goToDateDialogVisible = true;
  }

  closeGoToDateDialog(): void {
    this.goToDateDialogVisible = false;
    this.goToDateValue = '';
  }

  goToDate(): void {
    if (!this.goToDateValue) {
      return;
    }

    const parts = this.goToDateValue.split('/');
    if (parts.length !== 3) {
      this.messageService.add({ severity: 'error', summary: 'שגיאה', detail: 'פורמט תאריך שגוי. השתמש/י ב-DD/MM/YYYY' });
      return;
    }
    const day = parseInt(parts[0], 10);
    const month = parseInt(parts[1], 10) - 1;
    const year = parseInt(parts[2], 10);
    const targetDate = new Date(year, month, day);
    if (isNaN(targetDate.getTime()) || targetDate.getDate() !== day) {
      this.messageService.add({ severity: 'error', summary: 'שגיאה', detail: 'תאריך לא תקין' });
      return;
    }
    
    if (this.viewMode === 'gregorian') {
      this.currentMonth = new Date(targetDate.getFullYear(), targetDate.getMonth(), 1);
    } else {
      const hebrewParts = toHebrewParts(targetDate);
      this.currentHebrewMonth = { day: 1, month: hebrewParts.month, year: hebrewParts.year };
    }
    
    this.updateCalendarRange();
    this.syncCalendarWithSnapshot();
    this.closeGoToDateDialog();
    
    this.messageService.add({
      severity: 'info',
      summary: 'ניווט',
      detail: `עברת לחודש ${this.calendarTitle}`
    });
  }

  onViewModeChange(mode: CalendarViewMode): void {
    this.viewMode = mode;
    if (mode === 'gregorian') {
      this.currentMonth = new Date();
    } else {
      const nowHebrew = toHebrewParts(new Date());
      this.currentHebrewMonth = { day: 1, month: nowHebrew.month, year: nowHebrew.year };
    }
    this.updateCalendarRange();
    this.syncCalendarWithSnapshot();
  }

  setFilter(filter: EventFilterKey): void {
    this.selectedFilter = filter;
    this.applyFilter();
  }

  get statusFilterOptions(): { label: string; value: EventStatus | 'all' }[] {
    return [
      { label: 'כל הסטטוסים', value: 'all' },
      ...this.statusOptions
    ];
  }

  get selectedStatusOptions(): { label: string; value: EventStatus }[] {
    const current = this.selectedEvent?.status;
    if (!current) {
      return this.statusOptions;
    }
    const allowed = new Set<EventStatus>([current, ...(EVENT_STATUS_TRANSITIONS[current] || [])]);
    return this.statusOptions.filter(option => allowed.has(option.value));
  }

  get eventFormStatusOptions(): { label: string; value: EventStatus }[] {
    if (this.eventFormMode === 'create') {
      const draft = this.statusOptions[0]?.value;
      const allowed = new Set<EventStatus>([draft, ...(draft ? EVENT_STATUS_TRANSITIONS[draft] : [])].filter(Boolean) as EventStatus[]);
      return this.statusOptions.filter(option => allowed.has(option.value));
    }

    const current = this.events.find(event => event.id === this.eventForm?.id)?.status || this.eventForm?.status;
    if (!current) {
      return this.statusOptions;
    }
    const allowed = new Set<EventStatus>([current, ...(EVENT_STATUS_TRANSITIONS[current] || [])]);
    return this.statusOptions.filter(option => allowed.has(option.value));
  }

  get categoryFilterOptions(): { label: string; value: string }[] {
    return this.buildTextFilterOptions(
      'כל הקטגוריות',
      this.events.map(event => event.eventCategory).filter(Boolean) as string[]
    );
  }

  get menuFilterOptions(): { label: string; value: string }[] {
    return this.buildTextFilterOptions(
      'כל התפריטים',
      this.events.map(event => event.menuType).filter(Boolean) as string[]
    );
  }

  onEventFiltersChange(): void {
    this.applyFilter();
  }

  clearEventFilters(): void {
    this.eventSearchTerm = '';
    this.selectedStatusFilter = 'all';
    this.selectedCategoryFilter = 'all';
    this.selectedMenuFilter = 'all';
    this.selectedTimeFilter = 'all';
    this.selectedDishFilter = 'all';
    this.selectedFilter = 'all';
    this.applyFilter();
  }

  hasActiveEventFilters(): boolean {
    return !!(
      this.eventSearchTerm.trim() ||
      this.selectedStatusFilter !== 'all' ||
      this.selectedCategoryFilter !== 'all' ||
      this.selectedMenuFilter !== 'all' ||
      this.selectedTimeFilter !== 'all' ||
      this.selectedDishFilter !== 'all' ||
      this.selectedFilter !== 'all'
    );
  }

  openEventDetails(event: Event): void {
    this.selectedEvent = event;
    this.selectedStatus = event.status;
    this.activeDetailTab = 'overview';
    this.statusLocked = false; // For now, allow all status modifications
    this.openEditForm(event, false);
    this.activeDetailTab = 'overview';
    this.detailVisible = true;
    this.loadCalculationSummary(event.id);
  }

  loadCalculationSummary(eventId: number): void {
    this.calculationLoading = true;
    this.calculationSummary = null;
    this.eventService.getCalculationSummary(eventId)
      .pipe(take(1), takeUntil(this.destroy$))
      .subscribe({
        next: summary => {
          this.prepareCalculationSummary(summary);
          this.calculationLoading = false;
        },
        error: error => {
          console.error('Error loading event calculations:', error);
          this.calculationSummary = null;
          this.calculationLoading = false;
        }
      });
  }

  getTableclothRequirement() {
    return this.calculationSummary?.tool_requirements.find(row => row.source_type === 'tablecloths');
  }

  /** סה"כ מפות לפי החישוב (מנות ÷ 8 + ספייר) – מהשרת; החלוקה למלבן/מרובע מסומנת ידנית. */
  getTableclothRequiredTotal(): number {
    const row = this.getTableclothRequirement();
    const details = (row?.details || {}) as Record<string, number>;
    return Number(details['base_quantity'] || 0) + Number(details['spare_quantity'] || 0) || Number(row?.quantity || 0);
  }

  getTableclothSplit(): { rectangle: number; square: number } {
    const split = this.calculationSummary?.settings?.tablecloth_split || {};
    return { rectangle: Number(split.rectangle || 0), square: Number(split.square || 0) };
  }

  onTableclothSplitChange(shape: 'rectangle' | 'square', value: number | null): void {
    const settings = this.calculationSummary?.settings;
    if (!settings) return;
    const split = this.getTableclothSplit();
    split[shape] = Math.max(0, Number(value || 0));
    settings.tablecloth_split = split.rectangle || split.square ? split : null;
    this.saveCalculationSettings();
  }

  addSeatingSide(): void {
    this.eventForm.seatingSides.push({ side: '', places: null, arrangement: '' });
  }

  removeSeatingSide(index: number): void {
    this.eventForm.seatingSides.splice(index, 1);
  }

  /** דף למוביל החוזר: מה אמור לחזור לקייטרינג + הוראות החזרה */
  generateReturnSheetPdf(event: Event): void {
    if (!event?.id) return;
    this.eventService.printReturnSheetPdf(event.id);
    this.messageService.add({ severity: 'info', summary: 'PDF נוצר', detail: 'דף המוביל החוזר נפתח בחלון חדש' });
  }

  recalculateSelectedEvent(): void {
    if (!this.selectedEvent) return;
    this.calculationLoading = true;
    this.eventService.recalculateEvent(this.selectedEvent.id)
      .pipe(take(1), takeUntil(this.destroy$))
      .subscribe({
        next: summary => {
          this.prepareCalculationSummary(summary);
          this.calculationLoading = false;
        },
        error: () => {
          this.calculationLoading = false;
          this.messageService.add({ severity: 'error', summary: 'שגיאה', detail: 'חישוב האירוע נכשל' });
        }
      });
  }

  saveCalculationSettings(): void {
    const settings = this.calculationSummary?.settings;
    if (!this.selectedEvent || !settings) return;
    this.calculationLoading = true;
    this.eventService.updateCalculationSettings(this.selectedEvent.id, settings)
      .pipe(take(1), takeUntil(this.destroy$))
      .subscribe({
        next: summary => {
          this.prepareCalculationSummary(summary);
          this.calculationLoading = false;
          this.messageService.add({ severity: 'success', summary: 'נשמר', detail: 'הגדרות החישוב עודכנו' });
        },
        error: () => {
          this.calculationLoading = false;
          this.messageService.add({ severity: 'error', summary: 'שגיאה', detail: 'שמירת הגדרות החישוב נכשלה' });
        }
      });
  }

  onDrinkTypeChange(type: string, enabled: boolean): void {
    const settings = this.calculationSummary?.settings;
    if (!settings) return;

    settings.drink_types ??= {};
    settings.drink_types[type] = enabled;
    this.saveCalculationSettings();
  }

  private prepareCalculationSummary(summary: EventCalculationSummary): void {
    if (summary.settings) {
      summary.settings.drink_types ??= {
        pepsi: true, pepsi_max: true, orange_flavored: true, water: true, soda: true
      };
      summary.settings.roll_splits ||= [];
      summary.settings.event_tool_set_items ||= [];
      summary.settings.roll_splits.forEach(split => this.normalizeRollSplit(split));
      this.syncAllRollSplitQuantities(summary.settings.roll_splits);
    }
    this.calculationSummary = summary;
    this.manualCalculationTools = summary.tool_requirements
      .filter(row => row.source_type === 'manual_tool')
      .map(row => ({ tool_id: row.tool_id, name: row.name, quantity: row.quantity, is_reusable: row.is_reusable }));
  }

  private loadRollProducts(): void {
    this.productService.getProducts({ search: 'לחמ', limit: 200 })
      .pipe(take(1), takeUntil(this.destroy$))
      .subscribe({
        next: response => {
          this.rollProducts = (response.items || [])
            .filter(product => this.isRollProduct(product))
            .sort((a, b) => a.name.localeCompare(b.name, 'he'));
          this.calculationSummary?.settings?.roll_splits?.forEach(split => this.normalizeRollSplit(split));
        },
        error: error => {
          console.error('Error loading roll products:', error);
          this.rollProducts = [];
        }
      });
  }

  private isRollProduct(product: ApiProduct): boolean {
    const name = product.name || '';
    return name.includes('לחמניה') || name.includes('לחמנית') || name.includes('לחמניות');
  }

  private normalizeRollSplit(split: RollSplit): void {
    split.source = split.source || (split.product_id ? 'product' : 'manual');
    if (split.product_id) {
      const product = this.getRollProductById(split.product_id);
      if (product) {
        split.name = product.name;
        split.price_per_unit = product.price_per_unit ?? split.price_per_unit ?? 0;
      }
    }
    split.price_per_unit ??= 0;
  }

  private loadToolsForManualRows(): void {
    this.toolService.getTools({ limit: 200 })
      .pipe(take(1), takeUntil(this.destroy$))
      .subscribe({
        next: response => {
          this.availableTools = response.items || [];
        },
        error: error => {
          console.error('Error loading tools for manual rows:', error);
          this.availableTools = [];
        }
      });
  }

  addRollSplit(): void {
    const splits = this.calculationSummary?.settings?.roll_splits;
    if (!splits) return;

    const usedPercent = splits.reduce((sum, split) => sum + Number(split.percent || 0), 0);
    const percent = Math.max(0, this.roundRollPercent(100 - usedPercent));
    const quantity = Math.max(0, this.getRollTotal() - this.getRollSplitQuantityTotal());
    splits.push({ name: '', percent, quantity, source: 'product', product_id: null, price_per_unit: 0 });
  }

  removeRollSplit(index: number): void {
    this.calculationSummary?.settings?.roll_splits?.splice(index, 1);
  }

  getRollTotal(): number {
    const calculatedTotal = this.calculationSummary?.product_requirements
      ?.filter(row => row.source_type === 'rolls')
      .reduce((sum, row) => sum + Number(row.quantity || 0), 0) || 0;

    return calculatedTotal;
  }

  getRollFormula(): string {
    return this.calculationSummary?.product_requirements.find(row => row.source_type === 'rolls')?.formula_label || '';
  }

  getRollSplitQuantityTotal(): number {
    return this.calculationSummary?.settings?.roll_splits
      ?.reduce((sum, split) => sum + Number(split.quantity || 0), 0) || 0;
  }

  getRollSplitRemaining(): number {
    return this.getRollTotal() - this.getRollSplitQuantityTotal();
  }

  hasInvalidRollSplits(): boolean {
    const splits = this.calculationSummary?.settings?.roll_splits || [];
    return splits.some(split => {
      const source = split.source || (split.product_id ? 'product' : 'manual');
      if (source === 'product') {
        return !split.product_id;
      }
      return !String(split.name || '').trim() || Number(split.price_per_unit || 0) <= 0;
    });
  }

  onRollSplitPercentChange(split: RollSplit): void {
    const total = this.getRollTotal();
    const percent = Number(split.percent || 0);
    split.quantity = total > 0 ? Math.round(total * percent / 100) : 0;
  }

  onRollSplitQuantityChange(split: RollSplit): void {
    const total = this.getRollTotal();
    const quantity = Number(split.quantity || 0);
    split.percent = total > 0 ? this.roundRollPercent(quantity / total * 100) : 0;
  }

  onRollSplitSourceChange(split: RollSplit, source: 'product' | 'manual'): void {
    split.source = source;
    if (source === 'product') {
      split.name = '';
      split.product_id = null;
      split.price_per_unit = 0;
      return;
    }
    split.product_id = null;
    split.name = '';
    split.price_per_unit = split.price_per_unit ?? 0;
  }

  onRollProductChange(split: RollSplit, productId: number | null): void {
    split.product_id = productId;
    const product = productId ? this.getRollProductById(productId) : null;
    split.name = product?.name || '';
    split.price_per_unit = product?.price_per_unit ?? 0;
    split.source = 'product';
  }

  getRollProductById(productId: number | null | undefined): ApiProduct | null {
    if (!productId) return null;
    return this.rollProducts.find(product => product.id === productId) || null;
  }

  private syncAllRollSplitQuantities(splits: RollSplit[]): void {
    splits.forEach(split => this.onRollSplitPercentChange(split));
  }

  private roundRollPercent(value: number): number {
    return Math.round(value * 100) / 100;
  }

  addEventToolSetItem(): void {
    this.calculationSummary?.settings?.event_tool_set_items?.push({
      tool_id: null,
      quantity_per_guest: 1,
      is_reusable: false
    });
  }

  removeEventToolSetItem(index: number): void {
    this.calculationSummary?.settings?.event_tool_set_items?.splice(index, 1);
  }

  onEventToolSetToolChange(item: EventToolSetItem): void {
    const tool = this.availableTools.find(row => row.id === item.tool_id);
    if (!tool) {
      item.tool_id = null;
      return;
    }
  }

  getEventToolSetCalculatedQuantity(item: EventToolSetItem): number {
    const guests = this.selectedEvent?.guestCount || 1;
    return Math.ceil(guests * Number(item.quantity_per_guest || 0));
  }

  addManualTool(): void {
    this.manualCalculationTools.push({ tool_id: null, name: '', quantity: 1, is_reusable: false });
  }

  removeManualTool(index: number): void {
    this.manualCalculationTools.splice(index, 1);
  }

  onManualToolSelectionChange(row: ManualCalculationToolRow): void {
    const tool = this.availableTools.find(item => item.id === row.tool_id);
    if (!tool) {
      row.tool_id = null;
      return;
    }

    row.name = tool.name;
  }

  saveManualTools(): void {
    if (!this.selectedEvent) return;
    this.calculationLoading = true;
    this.eventService.updateManualTools(this.selectedEvent.id, this.manualCalculationTools)
      .pipe(take(1), takeUntil(this.destroy$))
      .subscribe({
        next: summary => { this.prepareCalculationSummary(summary); this.calculationLoading = false; },
        error: () => { this.calculationLoading = false; }
      });
  }

  /**
   * פתיחת פופאפ של אירוע לפי מזהה
   * משמש כאשר חוזרים מדף המנות
   */
  openEventById(eventId: number): void {
    // קודם מנסים למצוא באירועים שכבר נטענו
    const existingEvent = this.events.find(e => e.id === eventId);
    if (existingEvent) {
      this.openEventDetails(existingEvent);
      return;
    }
    
    // אם לא מצאנו, טוענים מהשרת
    this.eventService.getEvent(eventId)
      .pipe(
        take(1),
        map(mapApiEventToEvent),
        catchError(error => {
          console.error('Error loading event:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'שגיאה',
            detail: 'טעינת פרטי האירוע נכשלה'
          });
          return EMPTY;
        })
      )
      .subscribe((event: Event) => {
        this.openEventDetails(event);
      });
  }

  closeDialog(): void {
    this.detailVisible = false;
    this.selectedEvent = null;
    this.selectedStatus = null;
    this.statusLocked = false;
    this.statusUpdating = false;
  }

  openCreateForm(defaultDate?: Date): void {
    this.eventFormMode = 'create';
    this.dateInputMode = 'gregorian';
    this.eventForm = this.buildDefaultFormModel(defaultDate);
    this.refreshHebrewSelectors(this.eventForm.hebrewParts.year);
    this.eventFormVisible = true;
  }

  openEditForm(event: Event, showDialog = true): void {
    if (this.detailVisible && showDialog) {
      this.closeDialog();
    }
    const eventDate = this.toDate(event.date);
    const hebrewParts = toHebrewParts(eventDate);
    this.eventFormMode = 'edit';
    this.dateInputMode = 'gregorian';
    
    // המרת בעלי אירוע
    let owners: EventOwner[] = [];
    if (event.owners && event.owners.length > 0) {
      owners = event.owners.map(o => ({
        name: o.name || '',
        phone: o.phone || '',
        email: o.email || ''
      }));
    }
    if (owners.length === 0) {
      owners = [{ name: '', phone: '', email: '' }];
    }
    const dishwareType = event.dishwareType || (event.isRealDishes ? this.dishwareTypeOptions[0].value : this.dishwareTypeOptions[1].value);
    const isRealDishes = dishwareType === this.dishwareTypeOptions[0].value;
    
    this.eventForm = {
      id: event.id,
      name: event.name,
      eventCategory: event.eventCategory || '',
      guestCount: event.guestCount,
      menuType: event.menuType,
      status: event.status,
      notes: event.notes,
      eventDate: this.startOfDay(eventDate),
      eventTime: event.eventTime || '',
      hebrewParts,
      hebrewLabel: renderHebrewLabelFromParts(hebrewParts),
      
      // מיקום
      address: event.address || '',
      city: event.city || '',
      
      // כלים
      isRealDishes,
      
      // בעלי אירוע דינמיים
      owners: owners,
      venueName: event.venueName || '',
      floor: event.floor,
      hasElevator: !!event.hasElevator,
      accessCode: event.accessCode || '',
      onsiteContactName: event.onsiteContactName || '',
      onsiteContactPhone: event.onsiteContactPhone || '',
      hallOwnerName: event.hallOwnerName || '',
      hallOwnerPhone: event.hallOwnerPhone || '',
      seatingSides: (event.seatingSides || []).map(side => ({ ...side })),
      hasNearbyParking: !!event.hasNearbyParking,
      hasBackEntrance: !!event.hasBackEntrance,
      requiresCarts: !!event.requiresCarts,
      accessNotes: event.accessNotes || '',
      dishwareType,
      deliveryContentsNotes: event.deliveryContentsNotes || '',
      lastMinuteItems: event.lastMinuteItems || '',
      equipmentDropoffLocation: event.equipmentDropoffLocation || '',
      checkRefrigerator: !!event.checkRefrigerator,
      checkFreezer: !!event.checkFreezer,
      checkHotPlate: !!event.checkHotPlate,
      connectGas: !!event.connectGas,
      putInRefrigerator: !!event.putInRefrigerator,
      putInFreezer: !!event.putInFreezer,
      putOnHotPlate: !!event.putOnHotPlate,
      countBoxes: !!event.countBoxes,
      checkDrinks: !!event.checkDrinks,
      checkRolls: !!event.checkRolls,
      deliverySpecialNotes: event.deliverySpecialNotes || '',
      selectedDeliveryNoteTemplateIds: event.selectedDeliveryNoteTemplateIds || [],
      boxes: event.boxes?.length
        ? event.boxes.map(box => ({ boxType: box.boxType, quantity: box.quantity, notes: box.notes || '' }))
        : [{ boxType: '', quantity: 1, notes: '' }]
    };
    this.refreshHebrewSelectors(hebrewParts.year);
    if (showDialog) {
      this.eventFormVisible = true;
    }
  }

  closeEventForm(): void {
    if (this.eventFormSubmitting) {
      return;
    }
    this.eventFormVisible = false;
    this.eventForm = this.buildDefaultFormModel();
  }

  cancelEventForm(): void {
    if (this.detailVisible && this.eventFormMode === 'edit' && this.selectedEvent) {
      this.openEditForm(this.selectedEvent, false);
      this.activeDetailTab = 'overview';
      return;
    }
    this.closeEventForm();
  }

  startCreateEventForDate(date: Date, domEvent?: MouseEvent): void {
    domEvent?.stopPropagation();
    this.openCreateForm(date);
  }

  onGregorianDateChange(value: Date | null): void {
    if (!value) {
      return;
    }
    const normalized = this.startOfDay(value);
    const hebrewParts = toHebrewParts(normalized);
    this.eventForm.eventDate = normalized;
    this.eventForm.hebrewParts = hebrewParts;
    this.eventForm.hebrewLabel = renderHebrewLabelFromParts(hebrewParts);
    this.refreshHebrewSelectors(hebrewParts.year);
  }

  onRealDishesToggle(value: boolean): void {
    this.eventForm.isRealDishes = value;
    this.eventForm.dishwareType = value
      ? this.dishwareTypeOptions[0].value
      : this.dishwareTypeOptions[1].value;
  }

  onDishwareTypeChange(value: string): void {
    this.eventForm.dishwareType = value;
    this.eventForm.isRealDishes = value === this.dishwareTypeOptions[0].value;
  }

  onHebrewPartChange(): void {
    const sanitized = sanitizeHebrewParts(this.eventForm.hebrewParts, this.eventForm.hebrewParts.year);
    const gregorian = hebrewPartsToGregorian(sanitized);
    this.eventForm.hebrewParts = sanitized;
    this.eventForm.eventDate = this.startOfDay(gregorian);
    this.eventForm.hebrewLabel = renderHebrewLabelFromParts(sanitized);
    this.refreshHebrewSelectors(sanitized.year);
  }

  deleteEvent(event: Event, origin: 'list' | 'details'): void {
    this.confirmationService.confirm({
      header: 'מחיקת אירוע',
      message: `האם למחוק את האירוע "${event.name}"?`,
      icon: 'pi pi-trash',
      acceptLabel: 'מחק',
      rejectLabel: 'בטל',
      accept: () => {
        this.eventService.deleteEvent(event.id).subscribe({
          next: () => {
            // Remove from local array
            this.events = this.events.filter(e => e.id !== event.id);
            this.applyFilter();
            this.syncCalendarWithSnapshot();
            this.loadEvents();
            
            if (origin === 'details') {
              this.closeDialog();
            }
            this.messageService.add({
              severity: 'success',
              summary: 'אירוע נמחק',
              detail: `${event.name} הוסר מהמערכת`
            });
          },
          error: (error: any) => {
            this.messageService.add({
              severity: 'error',
              summary: 'שגיאה',
              detail: error?.message || 'מחיקת האירוע נכשלה'
            });
          }
        });
      }
    });
  }

  /** Business warnings from the server are shown, never blocking (user decisions 2026-11-23). */
  private showBusinessWarnings(warnings: string[] | undefined): void {
    for (const detail of warnings || []) {
      this.messageService.add({ severity: 'warn', summary: 'שימי לב', detail, life: 8000 });
    }
  }

  private sensitiveChangesConfirmed = false;

  /** Returns true when the save may continue now; otherwise asks first and re-runs `retry`. */
  private confirmSensitiveChanges(retry: () => void): boolean {
    if (this.sensitiveChangesConfirmed || this.eventFormMode === 'create' || !this.eventForm.id) {
      this.sensitiveChangesConfirmed = false;
      return true;
    }
    const original = this.events.find(e => e.id === this.eventForm.id);
    if (!original) return true;
    const messages: string[] = [];
    if (original.menuType !== this.eventForm.menuType && (original.dishes?.length || 0) > 0) {
      messages.push(`החלפת התפריט תמחק את ${original.dishes!.length} המנות שנבחרו מהתפריט הקודם.`);
    }
    const coreChanged = original.guestCount !== this.eventForm.guestCount
      || original.menuType !== this.eventForm.menuType
      || !!original.isRealDishes !== !!this.eventForm.isRealDishes;
    if (original.status === 'מאושר' && coreChanged) {
      messages.push('האירוע מאושר. הכמויות והשריונים יחושבו מחדש, והמחירים יישארו כפי שאושרו.');
    }
    if (!messages.length) return true;
    this.confirmationService.confirm({
      header: 'אישור שינוי',
      message: messages.join('<br>'),
      acceptLabel: 'המשך',
      rejectLabel: 'ביטול',
      accept: () => { this.sensitiveChangesConfirmed = true; retry(); },
    });
    return false;
  }

  submitEventForm(): void {
    if (!this.confirmSensitiveChanges(() => this.submitEventForm())) return;
    if (!this.isFormValid()) {
      this.messageService.add({
        severity: 'warn',
        summary: 'חסר מידע',
        detail: 'אנא מלאי את כל השדות החיוניים לפני שמירה'
      });
      return;
    }

    this.eventFormSubmitting = true;
    
    // סינון בעלים ריקים (שאין להם שם)
    const validOwners = this.eventForm.owners
      .filter(o => o.name && o.name.trim())
      .map((o, i) => ({
        name: o.name.trim(),
        phone: o.phone?.trim() || undefined,
        email: o.email?.trim() || undefined,
        order: i
      }));
    
    if (this.eventFormMode === 'create') {
      const createPayload: EventCreate = {
        name: this.eventForm.name,
        event_category: this.eventForm.eventCategory,
        menu_type: this.eventForm.menuType,
        date: this.formatDateForAPI(this.eventForm.eventDate),
        event_time: this.eventForm.eventTime || undefined,
        guest_count: this.eventForm.guestCount,
        notes: this.eventForm.notes,
        
        // מיקום
        address: this.eventForm.address || undefined,
        city: this.eventForm.city || undefined,
        
        // בעלי אירוע דינמיים
        owners: validOwners.length > 0 ? validOwners : undefined,
        ...this.buildDeliveryPayload()
      };

      this.eventService.createEvent(createPayload)
        .pipe(
          take(1),
          tap(apiEvent => this.showBusinessWarnings(apiEvent.warnings)),
          map(mapApiEventToEvent),
          switchMap((created: Event) => this.eventForm.status && this.eventForm.status !== created.status
            ? this.eventService.updateEventStatus(created.id, { status: this.eventForm.status as any }).pipe(map(mapApiEventToEvent))
            : of(created)
          )
        )
        .subscribe({
          next: (created: Event) => {
            this.events = this.normalizeEventSequences([created, ...this.events]);
            this.applyFilter();
            this.syncCalendarWithSnapshot();
            this.loadEvents();
            
            this.messageService.add({
              severity: 'success',
              summary: 'אירוע נוצר',
              detail: `${this.eventForm.name} נוסף ללוח`
            });
            this.eventFormSubmitting = false;
            this.closeEventForm();
          },
          error: (error: any) => {
            this.messageService.add({
              severity: 'error',
              summary: 'שגיאה',
              detail: error?.message || 'יצירת אירוע נכשלה'
            });
            this.eventFormSubmitting = false;
          }
        });
    } else if (this.eventForm.id) {
      const updatePayload: EventUpdate = {
        name: this.eventForm.name,
        event_category: this.eventForm.eventCategory,
        menu_type: this.eventForm.menuType,
        date: this.formatDateForAPI(this.eventForm.eventDate),
        event_time: this.eventForm.eventTime || undefined,
        guest_count: this.eventForm.guestCount,
        is_real_dishes: this.eventForm.isRealDishes,
        notes: this.eventForm.notes,
        
        // מיקום
        address: this.eventForm.address || undefined,
        city: this.eventForm.city || undefined,
        
        // בעלי אירוע דינמיים
        owners: validOwners,
        ...this.buildDeliveryPayload()
      };

      this.eventService
        .updateEvent(this.eventForm.id, updatePayload)
        .pipe(
          take(1),
          tap(apiEvent => this.showBusinessWarnings(apiEvent.warnings)),
          map(mapApiEventToEvent),
          switchMap((updated: Event) => this.eventForm.status && this.eventForm.status !== updated.status
            ? this.eventService.updateEventStatus(updated.id, { status: this.eventForm.status as any }).pipe(map(mapApiEventToEvent))
            : of(updated)
          )
        )
        .subscribe({
          next: (updated: Event) => {
            const index = this.events.findIndex(e => e.id === updated.id);
            if (index !== -1) {
              this.events[index] = updated;
              this.events = this.normalizeEventSequences(this.events);
              this.applyFilter();
              this.syncCalendarWithSnapshot();
              this.loadEvents();
            }
            
            this.messageService.add({
              severity: 'success',
              summary: 'אירוע עודכן',
              detail: `${updated.name} נשמר בהצלחה`
            });
            this.eventFormSubmitting = false;
            this.closeEventForm();
            // פתיחת popup צפייה בפרטי האירוע
            this.openEventDetails(updated);
          },
          error: (error: any) => {
            this.messageService.add({
              severity: 'error',
              summary: 'שגיאה',
              detail: error?.message || 'עדכון אירוע נכשל'
            });
            this.eventFormSubmitting = false;
          }
        });
    }
  }

  submitAndNavigateToDishes(): void {
    if (!this.confirmSensitiveChanges(() => this.submitAndNavigateToDishes())) return;
    if (!this.isFormValid()) {
      this.messageService.add({
        severity: 'warn',
        summary: 'חסר מידע',
        detail: 'אנא מלאי את כל השדות החיוניים לפני שמירה'
      });
      return;
    }

    this.eventFormSubmitting = true;
    
    // סינון בעלים ריקים (שאין להם שם)
    const validOwners = this.eventForm.owners
      .filter(o => o.name && o.name.trim())
      .map((o, i) => ({
        name: o.name.trim(),
        phone: o.phone?.trim() || undefined,
        email: o.email?.trim() || undefined,
        order: i
      }));
    
    if (this.eventFormMode === 'create') {
      const createPayload: EventCreate = {
        name: this.eventForm.name,
        event_category: this.eventForm.eventCategory,
        menu_type: this.eventForm.menuType,
        date: this.formatDateForAPI(this.eventForm.eventDate),
        event_time: this.eventForm.eventTime || undefined,
        guest_count: this.eventForm.guestCount,
        is_real_dishes: this.eventForm.isRealDishes,
        notes: this.eventForm.notes,
        
        // מיקום
        address: this.eventForm.address || undefined,
        city: this.eventForm.city || undefined,
        
        // בעלי אירוע דינמיים
        owners: validOwners.length > 0 ? validOwners : undefined,
        ...this.buildDeliveryPayload()
      };

      this.eventService.createEvent(createPayload)
        .pipe(
          take(1),
          tap(apiEvent => this.showBusinessWarnings(apiEvent.warnings)),
          map(mapApiEventToEvent),
          switchMap((created: Event) => this.eventForm.status && this.eventForm.status !== created.status
            ? this.eventService.updateEventStatus(created.id, { status: this.eventForm.status as any }).pipe(map(mapApiEventToEvent))
            : of(created)
          )
        )
        .subscribe({
          next: (created: Event) => {
            this.events = this.normalizeEventSequences([created, ...this.events]);
            this.applyFilter();
            this.syncCalendarWithSnapshot();
            
            this.messageService.add({
              severity: 'success',
              summary: 'אירוע נוצר',
              detail: `${this.eventForm.name} נוסף ללוח - עובר להוספת מנות או כלים`
            });
            this.eventFormSubmitting = false;
            this.closeEventForm();
            
            // מעבר לעמוד הוספת מנות
            this.navigateToAddDishes(created);
          },
          error: (error: any) => {
            const errorMsg = this.extractErrorMessage(error);
            this.messageService.add({
              severity: 'error',
              summary: 'שגיאה ביצירת אירוע',
              detail: errorMsg,
              life: 5000
            });
            this.eventFormSubmitting = false;
          }
        });
    } else if (this.eventForm.id) {
      const updatePayload: EventUpdate = {
        name: this.eventForm.name,
        event_category: this.eventForm.eventCategory,
        menu_type: this.eventForm.menuType,
        date: this.formatDateForAPI(this.eventForm.eventDate),
        event_time: this.eventForm.eventTime || undefined,
        guest_count: this.eventForm.guestCount,
        is_real_dishes: this.eventForm.isRealDishes,
        notes: this.eventForm.notes,
        
        // מיקום
        address: this.eventForm.address || undefined,
        city: this.eventForm.city || undefined,
        
        // בעלי אירוע דינמיים
        owners: validOwners,
        ...this.buildDeliveryPayload()
      };

      this.eventService
        .updateEvent(this.eventForm.id, updatePayload)
        .pipe(
          take(1),
          tap(apiEvent => this.showBusinessWarnings(apiEvent.warnings)),
          map(mapApiEventToEvent),
          switchMap((updated: Event) => this.eventForm.status && this.eventForm.status !== updated.status
            ? this.eventService.updateEventStatus(updated.id, { status: this.eventForm.status as any }).pipe(map(mapApiEventToEvent))
            : of(updated)
          )
        )
        .subscribe({
          next: (updated: Event) => {
            const index = this.events.findIndex(e => e.id === updated.id);
            if (index !== -1) {
              this.events[index] = updated;
              this.events = this.normalizeEventSequences(this.events);
              this.applyFilter();
              this.syncCalendarWithSnapshot();
            }
            
            this.messageService.add({
              severity: 'success',
              summary: 'אירוע עודכן',
              detail: `${updated.name} נשמר בהצלחה - עובר להוספת מנות או כלים`
            });
            this.eventFormSubmitting = false;
            this.closeEventForm();
            
            // מעבר לעמוד הוספת מנות
            this.navigateToAddDishes(updated);
          },
          error: (error: any) => {
            const errorMsg = this.extractErrorMessage(error);
            this.messageService.add({
              severity: 'error',
              summary: 'שגיאה בעדכון אירוע',
              detail: errorMsg,
              life: 5000
            });
            this.eventFormSubmitting = false;
          }
        });
    }
  }

  confirmStatusChange(): void {
    if (!this.selectedEvent || !this.selectedStatus || !this.isStatusChanged() || this.statusLocked) {
      return;
    }

    this.confirmationService.confirm({
      header: 'אישור עדכון',
      message: `האם לעדכן את סטטוס האירוע ל"${this.selectedStatus}"?`,
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'עדכן',
      rejectLabel: 'בטל',
      accept: () => this.persistStatusChange()
    });
  }

  onStatusQuickUpdate(): void {
    if (this.statusLocked) return;
    this.persistStatusChange();
  }

  isStatusChanged(): boolean {
    return !!(
      this.selectedEvent &&
      this.selectedStatus &&
      this.selectedEvent.status !== this.selectedStatus
    );
  }

  getStatusSeverity(status: EventStatus): 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast' | null {
    const severity = EVENT_STATUS_DISPLAY[status]?.severity;
    if (!severity) {
      return null;
    }

    return severity === 'warning' ? 'warn' : severity as any;
  }

  getStatusIcon(status: EventStatus): string {
    return EVENT_STATUS_DISPLAY[status]?.icon || 'pi pi-info-circle';
  }

  getStatusLabel(status: EventStatus): string {
    return EVENT_STATUS_DISPLAY[status]?.label || status;
  }

  getStatusClass(status: EventStatus): string {
    return `status-${EVENT_STATUS_DISPLAY[status]?.class || 'info'}`;
  }

  hasMultipleEventsOnDay(event: Event): boolean {
    return this.events.filter(other => this.isSameDay(other.date, this.toDate(event.date))).length > 1;
  }

  getEventSequenceLabel(event: Event): string {
    return `אירוע #${event.daySequenceNumber || 1}`;
  }

  getEventSequenceColorClass(event: Event): string {
    if (!this.hasMultipleEventsOnDay(event)) {
      return '';
    }
    return `event-sequence-${event.daySequenceColor || 'default'}`;
  }

  getHebrewDayDisplay(day: number): string {
    return hebrewDayToLetters(day);
  }

  trackCell(index: number, cell: CalendarDay | null): string | number {
    if (!cell) {
      return `empty-${index}`;
    }
    return `${cell.date.getTime()}-${cell.events.length}`;
  }

  /**
   * יצירת PDF הוראות הגשה למלצר ופתיחה בחלון חדש
   */
  generateWaiterPdf(event: Event): void {
    if (!event?.id) {
      this.messageService.add({
        severity: 'warn',
        summary: 'שגיאה',
        detail: 'לא ניתן ליצור PDF ללא מזהה אירוע'
      });
      return;
    }

    // בדיקה אם יש מנות לאירוע
    if (!event.dishes || event.dishes.length === 0) {
      this.messageService.add({
        severity: 'warn',
        summary: 'אין מנות',
        detail: 'לא נבחרו עדיין מנות לאירוע'
      });
      return;
    }

    this.eventService.printWaiterInstructions(event.id);
    this.messageService.add({
      severity: 'info',
      summary: 'PDF נוצר',
      detail: 'קובץ הוראות למלצר נפתח בחלון חדש'
    });
  }

  generateDeliverySheetPdf(event: Event): void {
    if (!event?.id) {
      this.messageService.add({
        severity: 'warn',
        summary: 'שגיאה',
        detail: 'לא ניתן ליצור דף משלוח ללא מזהה אירוע'
      });
      return;
    }

    const missing: string[] = [];
    if (!event.venueName) missing.push('שם האולם/המקום');
    if (!event.address || !event.city) missing.push('כתובת מלאה');
    if (!event.eventTime) missing.push('שעת האירוע');
    if (!event.onsiteContactPhone && !event.hallOwnerPhone && !event.owners?.some(owner => owner.phone)) {
      missing.push('טלפון איש קשר');
    }
    if (!event.equipmentDropoffLocation) missing.push('מיקום הפריקה');
    if (!event.dishwareType) missing.push('סוג הכלים');
    if (!event.boxes?.some(box => box.boxType && box.quantity > 0)) missing.push('סיכום ארגזים');

    const openPdf = () => {
      this.eventService.printDeliverySheetPdf(event.id);
      this.messageService.add({
        severity: 'info',
        summary: 'PDF נוצר',
        detail: 'דף המשלוח נפתח בחלון חדש'
      });
    };

    if (missing.length === 0) {
      openPdf();
      return;
    }

    this.confirmationService.confirm({
      header: 'פרטים חסרים בדף המשלוח',
      message: `חסרים: ${missing.join(', ')}. להפיק את הדף בכל זאת?`,
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'הפק בכל זאת',
      rejectLabel: 'חזור לעריכת האירוע',
      accept: openPdf,
      reject: () => this.openEditForm(event)
    });
  }

  /**
   * יצירת PDF סיכום לבעל הקייטרינג - ללא רקע צבעוני
   */
  generateCateringPdf(event: Event): void {
    if (!event?.id) {
      this.messageService.add({
        severity: 'warn',
        summary: 'שגיאה',
        detail: 'לא ניתן ליצור PDF ללא מזהה אירוע'
      });
      return;
    }

    // בדיקה אם יש מנות לאירוע
    if (!event.dishes || event.dishes.length === 0) {
      this.messageService.add({
        severity: 'warn',
        summary: 'אין מנות',
        detail: 'לא נבחרו עדיין מנות לאירוע'
      });
      return;
    }

    this.eventService.printCateringPdf(event.id);
    this.messageService.add({
      severity: 'info',
      summary: 'PDF נוצר',
      detail: 'רשימת האריזה נפתחה בחלון חדש'
    });
  }

  /**
   * יצירת PDF רשימת קניות מחולקת לפי קטגוריות + כלי הגשה
   */
  generateShoppingPdf(event: Event): void {
    if (!event?.id) {
      this.messageService.add({
        severity: 'warn',
        summary: 'שגיאה',
        detail: 'לא ניתן ליצור PDF ללא מזהה אירוע'
      });
      return;
    }

    if (!event.dishes || event.dishes.length === 0) {
      this.messageService.add({
        severity: 'warn',
        summary: 'אין מנות',
        detail: 'לא נבחרו עדיין מנות לאירוע'
      });
      return;
    }

    this.eventService.printShoppingPdf(event.id);
    this.messageService.add({
      severity: 'info',
      summary: 'PDF נוצר',
      detail: 'רשימת הקניות נפתחה בחלון חדש'
    });
  }

  /**
   * ניווט לדף הוספת מנות או כלים
   */
  navigateToAddDishes(event: Event): void {
    if (!event?.id) {
      this.messageService.add({
        severity: 'warn',
        summary: 'שגיאה',
        detail: 'לא ניתן להוסיף מנות ללא מזהה אירוע'
      });
      return;
    }
    
    // סגירת הדיאלוג אם פתוח
    if (this.detailVisible) {
      this.closeDialog();
    }
    
    this.router.navigate(['/events', event.id, 'select-dishes']);
  }

  private persistStatusChange(): void {
    if (!this.selectedEvent || !this.selectedStatus) {
      return;
    }

    const statusUpdate: EventStatusUpdate = {
      status: this.selectedStatus as any
    };

    this.statusUpdating = true;
    this.eventService
      .updateEventStatus(this.selectedEvent.id, statusUpdate)
      .pipe(
        take(1),
        map(mapApiEventToEvent)
      )
      .subscribe({
        next: (updated: Event) => {
          this.selectedEvent = updated;
          this.selectedStatus = updated.status;
          // Update the event in the main list
          const index = this.events.findIndex(e => e.id === updated.id);
          if (index !== -1) {
            this.events[index] = updated;
            this.events = this.normalizeEventSequences(this.events);
            this.applyFilter();
            this.syncCalendarWithSnapshot();
          }
          this.messageService.add({
            severity: 'success',
            summary: 'סטטוס עודכן',
            detail: `${updated.name} עודכן בהצלחה`
          });
          this.statusUpdating = false;
        },
        error: (error: any) => {
          this.messageService.add({
            severity: 'error',
            summary: 'שגיאה',
            detail: error?.message || 'עדכון סטטוס נכשל'
          });
          this.statusUpdating = false;
        }
      });
  }

  private updateCalendarRange(): void {
    this.calendarRange = this.viewMode === 'gregorian'
      ? this.buildGregorianRange(this.currentMonth)
      : this.buildHebrewRange(this.currentHebrewMonth);
    this.loadCalendarEvents();
  }

  private loadCalendarEvents(): void {
    this.loadingCalendar = true;
    // Use existing events and filter them for the calendar range
    this.calendarEvents = this.events.filter(event => 
      this.isWithinRange(event.date, this.calendarRange)
    );
    this.buildCalendarGrid();
    this.loadingCalendar = false;
  }

  private applyFilter(): void {
    const today = this.startOfToday();
    this.filteredEvents = this.events
      .filter(event => {
        const eventDate = this.toDate(event.date);
        if (!this.matchesQuickFilter(event, eventDate, today)) return false;
        if (!this.matchesSearchFilter(event)) return false;
        if (!this.matchesSelectFilters(event)) return false;
        if (!this.matchesTimeFilter(eventDate, today)) return false;
        if (!this.matchesDishFilter(event)) return false;
        return true;
      })
      .sort((a, b) => this.compareEventsForList(a, b));
  }

  private matchesQuickFilter(event: Event, eventDate: Date, today: Date): boolean {
    switch (this.selectedFilter) {
      case 'past':
        return eventDate < today;
      case 'cancelled':
        return event.status === 'בוטל';
      case 'completed':
        return event.status === 'הסתיים';
      default:
        return true;
    }
  }

  private matchesSearchFilter(event: Event): boolean {
    const query = this.normalizeSearchText(this.eventSearchTerm);
    if (!query) return true;

    const ownersText = (event.owners || [])
      .map(owner => `${owner.name || ''} ${owner.phone || ''} ${owner.email || ''}`)
      .join(' ');

    const searchableText = this.normalizeSearchText([
      event.name,
      event.eventCategory,
      event.menuType,
      event.status,
      event.city,
      event.address,
      event.hebrewDate,
      event.notes,
      ownersText
    ].filter(Boolean).join(' '));

    return searchableText.includes(query);
  }

  private matchesSelectFilters(event: Event): boolean {
    return (
      (this.selectedStatusFilter === 'all' || event.status === this.selectedStatusFilter) &&
      (this.selectedCategoryFilter === 'all' || event.eventCategory === this.selectedCategoryFilter) &&
      (this.selectedMenuFilter === 'all' || event.menuType === this.selectedMenuFilter)
    );
  }

  private matchesTimeFilter(eventDate: Date, today: Date): boolean {
    const day = this.startOfDay(eventDate);
    switch (this.selectedTimeFilter) {
      case 'today':
        return day.getTime() === today.getTime();
      case 'thisWeek':
        return day >= today && day <= this.addDays(today, 7);
      case 'thisMonth':
        return day.getFullYear() === today.getFullYear() && day.getMonth() === today.getMonth();
      case 'upcoming':
        return day >= today;
      case 'past':
        return day < today;
      default:
        return true;
    }
  }

  private matchesDishFilter(event: Event): boolean {
    const dishes = event.dishes || [];
    switch (this.selectedDishFilter) {
      case 'withDishes':
        return dishes.length > 0;
      case 'withoutDishes':
        return dishes.length === 0;
      case 'withGiftDishes':
        return dishes.some(dish => dish.isGift);
      default:
        return true;
    }
  }

  private buildTextFilterOptions(allLabel: string, values: string[]): { label: string; value: string }[] {
    const uniqueValues = Array.from(new Set(values.map(value => value.trim()).filter(Boolean)))
      .sort((a, b) => a.localeCompare(b, 'he'));
    return [
      { label: allLabel, value: 'all' },
      ...uniqueValues.map(value => ({ label: value, value }))
    ];
  }

  private normalizeSearchText(value: string): string {
    return value.toLowerCase().trim().replace(/\s+/g, ' ');
  }

  private addDays(date: Date, days: number): Date {
    const next = new Date(date);
    next.setDate(next.getDate() + days);
    return next;
  }

  private syncCalendarWithSnapshot(): void {
    this.calendarEvents = this.events.filter(event => this.isWithinRange(event.date, this.calendarRange));
    this.buildCalendarGrid();
  }

  private buildCalendarGrid(): void {
    this.calendarCells = this.viewMode === 'gregorian'
      ? this.buildGregorianCalendarGrid()
      : this.buildHebrewCalendarGrid();
  }

  private buildGregorianCalendarGrid(): (CalendarDay | null)[] {
    const start = new Date(this.currentMonth.getFullYear(), this.currentMonth.getMonth(), 1);
    const daysInMonth = new Date(this.currentMonth.getFullYear(), this.currentMonth.getMonth() + 1, 0).getDate();
    const cells: (CalendarDay | null)[] = [];

    // Add empty cells for days before the month starts
    for (let i = 0; i < start.getDay(); i++) {
      cells.push(null);
    }

    // Add calendar days
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(this.currentMonth.getFullYear(), this.currentMonth.getMonth(), day);
      cells.push(this.buildCalendarDay(date));
    }

    this.padCalendarCells(cells);
    return cells;
  }

  private buildHebrewCalendarGrid(): (CalendarDay | null)[] {
    const { month, year } = this.currentHebrewMonth;
    const totalDays = getHebrewMonthLength(month, year);
    const firstDate = hebrewPartsToGregorian({ day: 1, month, year });
    const cells: (CalendarDay | null)[] = [];

    // Add empty cells for days before the month starts
    for (let i = 0; i < firstDate.getDay(); i++) {
      cells.push(null);
    }

    // Add calendar days
    for (let day = 1; day <= totalDays; day++) {
      const date = hebrewPartsToGregorian({ day, month, year });
      const parts = { day, month, year };
      cells.push(this.buildCalendarDay(date, parts));
    }

    this.padCalendarCells(cells);
    return cells;
  }

  private buildCalendarDay(date: Date, hebrewOverride?: HebrewDateParts): CalendarDay {
    const hebrewParts = hebrewOverride ?? toHebrewParts(date);
    return {
      date,
      hebrewDateLabel: renderHebrewLabelFromParts(hebrewParts),
      hebrewDay: hebrewParts.day,
      hebrewMonth: hebrewParts.month,
      hebrewYear: hebrewParts.year,
      isToday: this.isSameDay(date, new Date()),
      isPast: this.isPastDate(date),
      events: this.calendarEvents
        .filter(event => this.isSameDay(event.date, date))
        .sort((a, b) => this.compareEventsByDaySequence(a, b))
    };
  }

  private compareEventsForList(a: Event, b: Event): number {
    const dateDiff = this.startOfDay(this.toDate(b.date)).getTime() - this.startOfDay(this.toDate(a.date)).getTime();
    if (dateDiff !== 0) {
      return dateDiff;
    }

    return this.compareEventsByDaySequence(a, b);
  }

  private compareEventsByDaySequence(a: Event, b: Event): number {
    const sequenceDiff = (a.daySequenceNumber || 999) - (b.daySequenceNumber || 999);
    if (sequenceDiff !== 0) {
      return sequenceDiff;
    }

    return this.getEventSortMinutes(a) - this.getEventSortMinutes(b);
  }

  private getEventSortMinutes(event: Event): number {
    const rawTime = (event.eventTime || '').trim();
    if (rawTime) {
      const [hourText, minuteText = '0'] = rawTime.split(':');
      const hour = Number(hourText);
      const minute = Number(minuteText);
      if (Number.isInteger(hour) && Number.isInteger(minute) && hour >= 0 && hour <= 23 && minute >= 0 && minute <= 59) {
        return hour * 60 + minute;
      }
    }

    const date = this.toDate(event.date);
    return date.getHours() * 60 + date.getMinutes() || 24 * 60;
  }

  private normalizeEventSequences(events: Event[]): Event[] {
    const groups = new Map<string, Event[]>();

    for (const event of events) {
      const key = this.getEventDayKey(event);
      const dayEvents = groups.get(key) || [];
      dayEvents.push(event);
      groups.set(key, dayEvents);
    }

    for (const dayEvents of groups.values()) {
      const hasServerSequences = dayEvents.every(event => event.daySequenceNumber && event.daySequenceColor);
      if (hasServerSequences) {
        continue;
      }

      dayEvents
        .sort((a, b) => this.getEventSortMinutes(a) - this.getEventSortMinutes(b))
        .forEach((event, index) => {
          event.daySequenceNumber = index + 1;
          event.daySequenceColor = this.eventSequenceColors[index] || event.daySequenceColor;
        });
    }

    return events;
  }

  private getEventDayKey(event: Event): string {
    const date = this.toDate(event.date);
    return `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
  }

  private padCalendarCells(cells: (CalendarDay | null)[]): void {
    while (cells.length % 7 !== 0) {
      cells.push(null);
    }
  }

  private isSameDay(a: Date | string, b: Date): boolean {
    const dateA = this.toDate(a);
    return (
      dateA.getFullYear() === b.getFullYear() &&
      dateA.getMonth() === b.getMonth() &&
      dateA.getDate() === b.getDate()
    );
  }

  private toDate(value: Date | string): Date {
    if (value instanceof Date) {
      return value;
    }
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? new Date() : parsed;
  }

  private startOfToday(): Date {
    return this.startOfDay(new Date());
  }

  private startOfDay(date: Date): Date {
    const normalized = new Date(date);
    normalized.setHours(0, 0, 0, 0);
    return normalized;
  }

  private isPastDate(date: Date): boolean {
    return this.startOfDay(date).getTime() < this.startOfToday().getTime();
  }

  private buildDefaultFormModel(defaultDate?: Date): EventFormModel {
    const baseDate = this.startOfDay(defaultDate ?? new Date());
    const hebrewParts = toHebrewParts(baseDate);
    return {
      name: '',
      eventCategory: this.eventCategories[0] || '',
      guestCount: 50,
      menuType: this.menuTemplates[0]?.name || '',
      status: 'טיוטה',
      notes: '',
      eventDate: baseDate,
      eventTime: '',
      hebrewParts,
      hebrewLabel: renderHebrewLabelFromParts(hebrewParts),
      
      // מיקום
      address: '',
      city: '',
      
      // כלים - ברירת מחדל חד"פ
      isRealDishes: false,
      
      // בעלי אירוע דינמיים - מתחילים עם אחד ריק
      owners: [{ name: '', phone: '', email: '' }],
      venueName: '',
      floor: undefined,
      hasElevator: false,
      accessCode: '',
      onsiteContactName: '',
      onsiteContactPhone: '',
      hallOwnerName: '',
      hallOwnerPhone: '',
      seatingSides: [],
      hasNearbyParking: false,
      hasBackEntrance: false,
      requiresCarts: false,
      accessNotes: '',
      dishwareType: 'חד פעמי',
      deliveryContentsNotes: '',
      lastMinuteItems: '',
      equipmentDropoffLocation: '',
      checkRefrigerator: false,
      checkFreezer: false,
      checkHotPlate: false,
      connectGas: false,
      putInRefrigerator: false,
      putInFreezer: false,
      putOnHotPlate: false,
      countBoxes: false,
      checkDrinks: false,
      checkRolls: false,
      deliverySpecialNotes: '',
      selectedDeliveryNoteTemplateIds: [],
      boxes: [{ boxType: '', quantity: 1, notes: '' }]
    };
  }
  
  // הוספת בעל אירוע חדש
  addOwner(): void {
    this.eventForm.owners.push({ name: '', phone: '', email: '' });
  }
  
  // הסרת בעל אירוע
  removeOwner(index: number): void {
    if (this.eventForm.owners.length > 1) {
      this.eventForm.owners.splice(index, 1);
    } else {
      // אם זה האחרון, פשוט לנקות אותו
      this.eventForm.owners[0] = { name: '', phone: '', email: '' };
    }
  }

  private buildHebrewYearOptions(centerYear: number): { label: string; value: number }[] {
    return getHebrewYearsRange(centerYear, 2, 6).map((year: number) => ({
      label: hebrewYearToGematriya(year),
      value: year
    }));
  }

  private buildHebrewDayOptions(month: number, year: number): { label: string; value: number }[] {
    const maxDay = getHebrewMonthLength(month, year);
    const options: { label: string; value: number }[] = [];
    for (let day = 1; day <= maxDay; day++) {
      options.push({
        label: hebrewDayToLetters(day, month, year),
        value: day
      });
    }
    return options;
  }

  private refreshHebrewSelectors(centerYear: number): void {
    this.hebrewMonthOptions = buildHebrewMonthOptions(centerYear);
    this.hebrewYearOptions = this.buildHebrewYearOptions(centerYear);
    // עדכון אפשרויות היום לפי החודש והשנה הנוכחיים
    const month = this.eventForm?.hebrewParts.month || 1;
    const year = this.eventForm?.hebrewParts.year || centerYear;
    this.hebrewDayOptions = this.buildHebrewDayOptions(month, year);
  }

  private buildGregorianRange(reference: Date): CalendarRange {
    const start = new Date(reference.getFullYear(), reference.getMonth(), 1);
    const end = new Date(reference.getFullYear(), reference.getMonth() + 1, 0);
    return { start, end };
  }

  private buildHebrewRange(parts: HebrewDateParts): CalendarRange {
    const normalized = sanitizeHebrewParts({ ...parts, day: 1 }, parts.year);
    const days = getHebrewMonthLength(normalized.month, normalized.year);
    const start = hebrewPartsToGregorian({ ...normalized });
    const end = hebrewPartsToGregorian({ day: days, month: normalized.month, year: normalized.year });
    return { start: this.startOfDay(start), end: this.endOfDay(end) };
  }

  private endOfDay(date: Date): Date {
    const normalized = new Date(date);
    normalized.setHours(23, 59, 59, 999);
    return normalized;
  }

  private isWithinRange(value: Date | string, range: CalendarRange): boolean {
    const date = this.startOfDay(this.toDate(value));
    return date >= this.startOfDay(range.start) && date <= this.endOfDay(range.end);
  }

  get calendarTitle(): string {
    return this.viewMode === 'gregorian'
      ? new Intl.DateTimeFormat('he-IL', { month: 'long', year: 'numeric' }).format(this.currentMonth)
      : formatHebrewMonthTitle(this.currentHebrewMonth.month, this.currentHebrewMonth.year);
  }

  isFormValid(): boolean {
    const form = this.eventForm;
    return Boolean(
      form.name?.trim() &&
      form.eventCategory?.trim() &&
      form.guestCount > 0 &&
      form.menuType &&
      form.eventDate &&
      form.hebrewParts?.day
    );
  }

  isStatusFieldDisabled(): boolean {
    if (this.eventFormMode === 'create') {
      return false;
    }
    const matchingEvent = this.events.find(event => event.id === this.eventForm.id);
    if (!matchingEvent) {
      return true;
    }
    // For now, all statuses can be modified - can add logic later
    return false;
  }

  get menuTemplateSelectItems(): { label: string; value: string; template: MenuTemplate }[] {
    return this.menuTemplates.map(t => ({
      label: t.name,
      value: t.name,
      template: t
    }));
  }

  loadMenuTemplates(): void {
    this.loadingMenuTemplates = true;
    this.menuService.getMenuTemplates()
      .pipe(take(1))
      .subscribe({
        next: (templates: MenuTemplate[]) => {
          this.menuTemplates = templates;
          this.loadingMenuTemplates = false;
          // עדכן ברירת מחדל אם הניתן חלק
          if (this.eventFormVisible && !this.eventForm.menuType && templates.length > 0) {
            this.eventForm.menuType = templates[0].name;
          }
        },
        error: () => {
          this.loadingMenuTemplates = false;
        }
      });
  }

  loadEventCategories(): void {
    this.loadingEventCategories = true;
    this.lookupService.getAllLookupData()
      .pipe(take(1))
      .subscribe({
        next: data => {
          this.eventCategories = data.event_categories || [];
          if (this.eventFormVisible && !this.eventForm.eventCategory) {
            this.eventForm.eventCategory = this.eventCategories[0] || '';
          }
          this.loadingEventCategories = false;
        },
        error: () => {
          this.eventCategories = [];
          this.loadingEventCategories = false;
        }
      });
  }

  loadDeliveryNoteTemplates(): void {
    this.eventService.getDeliveryNoteTemplates()
      .pipe(take(1))
      .subscribe({
        next: (templates: DeliveryNoteTemplate[]) => {
          this.deliveryNoteTemplates = templates;
        },
        error: () => {
          this.deliveryNoteTemplates = [];
        }
      });
  }

  hasOwners(event: Event | null): boolean {
    if (!event) return false;
    return !!(event.owners && event.owners.length > 0);
  }

  /**
   * חישוב עלות הייצור הכוללת של האירוע (עלות לקייטרינג)
   * מחזיר null אם אין מחירי snapshot (אירוע לא אושר עדיין)
   */
  getEventProductionCost(event: Event | null): number | null {
    if (!event?.dishes || event.dishes.length === 0) return null;
    const relevantDishes = event.dishes.filter(d => {
      const price = d.snapshotBasePrice ?? d.currentBasePrice;
      return price != null;
    });
    if (relevantDishes.length === 0) return null;
    const guestCount = event.guestCount || 1;
    return relevantDishes.reduce((sum, d) => {
      const basePrice = d.snapshotBasePrice ?? d.currentBasePrice ?? 0;
      const qty = d.quantity ?? 1;
      return sum + basePrice * qty * guestCount;
    }, 0);
  }

  /**
   * חישוב רווח מוערך (מחיר סופי / מחושב פחות עלות ייצור)
   */
  getEventEstimatedProfit(event: Event | null): number | null {
    const cost = this.getEventProductionCost(event);
    if (cost === null || !event) return null;
    const revenue = event.finalPrice ?? event.calculatedPrice ?? 0;
    if (!revenue) return null;
    return revenue - cost;
  }

  trackByIndex(index: number): number {
    return index;
  }

  addBoxRow(): void {
    this.eventForm.boxes.push({ boxType: '', quantity: 1, notes: '' });
  }

  removeBoxRow(index: number): void {
    if (this.eventForm.boxes.length > 1) {
      this.eventForm.boxes.splice(index, 1);
    } else {
      this.eventForm.boxes[0] = { boxType: '', quantity: 1, notes: '' };
    }
  }

  toggleDeliveryNote(templateId: number, checked: boolean): void {
    const ids = new Set(this.eventForm.selectedDeliveryNoteTemplateIds || []);
    if (checked) {
      ids.add(templateId);
    } else {
      ids.delete(templateId);
    }
    this.eventForm.selectedDeliveryNoteTemplateIds = Array.from(ids);
  }

  isDeliveryNoteSelected(templateId: number): boolean {
    return (this.eventForm.selectedDeliveryNoteTemplateIds || []).includes(templateId);
  }

  getChecklistValue(key: string): boolean {
    return !!(this.eventForm as any)[key];
  }

  setChecklistValue(key: string, checked: boolean): void {
    (this.eventForm as any)[key] = checked;
  }

  private buildDeliveryPayload(): Partial<EventCreate> {
    const boxes = (this.eventForm.boxes || [])
      .filter(box => box.boxType && box.boxType.trim())
      .map(box => ({
        box_type: box.boxType.trim(),
        quantity: box.quantity || 1,
        notes: box.notes?.trim() || undefined
      }));

    return {
      is_real_dishes: this.eventForm.dishwareType === this.dishwareTypeOptions[0].value,
      venue_name: this.eventForm.venueName?.trim() || undefined,
      floor: this.eventForm.floor,
      has_elevator: this.eventForm.hasElevator,
      access_code: this.eventForm.accessCode?.trim() || undefined,
      onsite_contact_name: this.eventForm.onsiteContactName?.trim() || undefined,
      onsite_contact_phone: this.eventForm.onsiteContactPhone?.trim() || undefined,
      hall_owner_name: this.eventForm.hallOwnerName?.trim() || undefined,
      hall_owner_phone: this.eventForm.hallOwnerPhone?.trim() || undefined,
      seating_sides: this.eventForm.seatingSides
        .filter(side => side.side?.trim() || side.places)
        .map(side => ({ side: side.side?.trim() || '', places: side.places ?? null, arrangement: side.arrangement?.trim() || '' })),
      has_nearby_parking: this.eventForm.hasNearbyParking,
      has_back_entrance: this.eventForm.hasBackEntrance,
      requires_carts: this.eventForm.requiresCarts,
      access_notes: this.eventForm.accessNotes?.trim() || undefined,
      dishware_type: this.eventForm.dishwareType,
      delivery_contents_notes: this.eventForm.deliveryContentsNotes?.trim() || undefined,
      last_minute_items: this.eventForm.lastMinuteItems?.trim() || undefined,
      equipment_dropoff_location: this.eventForm.equipmentDropoffLocation?.trim() || undefined,
      check_refrigerator: this.eventForm.checkRefrigerator,
      check_freezer: this.eventForm.checkFreezer,
      check_hot_plate: this.eventForm.checkHotPlate,
      connect_gas: this.eventForm.connectGas,
      put_in_refrigerator: this.eventForm.putInRefrigerator,
      put_in_freezer: this.eventForm.putInFreezer,
      put_on_hot_plate: this.eventForm.putOnHotPlate,
      count_boxes: this.eventForm.countBoxes,
      check_drinks: this.eventForm.checkDrinks,
      check_rolls: this.eventForm.checkRolls,
      delivery_special_notes: this.eventForm.deliverySpecialNotes?.trim() || undefined,
      selected_delivery_note_template_ids: this.eventForm.selectedDeliveryNoteTemplateIds || [],
      boxes
    };
  }

  /**
   * תיקון באג: המרת תאריך לפורמט ISO datetime עם שעת צהריים
   * שימוש ב-12:00 UTC מונע הסטת יום בכל timezone בעולם
   * (toISOString על חצות מקומי גורם להסטה אחורה באזורים מזרחיים)
   */
  private formatDateForAPI(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}T12:00:00.000Z`;
  }

  /**
   * חילוץ הודעת שגיאה ברורה מתוך תגובת API
   * מנסה למצוא הודעה מפורשת מה-server ואם לא, מחזירה הודעה כללית
   */
  private extractErrorMessage(error: any): string {
    // בדוק תגובת HTTP עם מפתח detail (מFormats טיפיים של FastAPI)
    if (error?.error?.detail) {
      return error.error.detail;
    }
    
    // בדוק גם message
    if (error?.error?.message) {
      return error.error.message;
    }
    
    // בדוק standard error message
    if (error?.message) {
      return error.message;
    }
    
    // בדוק status code להודעה טובה יותר
    if (error?.status === 400) {
      return 'בדוקו את הנתונים שהוזנו (ודאו שקיימים מינימום סועדים לסוג התפריט)';
    }
    
    if (error?.status === 404) {
      return 'האירוע לא נמצא בשרת';
    }
    
    if (error?.status === 500) {
      return 'שגיאה בשרת - אנא נסו שוב מאוחר יותר';
    }
    
    // הודעת default
    return 'אירעה שגיאה בעת השמירה. אנא בדקו את הנתונים ונסו שוב.';
  }
}
