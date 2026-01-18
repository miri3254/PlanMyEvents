import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PanelModule } from 'primeng/panel';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { BadgeModule } from 'primeng/badge';
import { DialogModule } from 'primeng/dialog';
import { TableModule } from 'primeng/table';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { SelectButtonModule } from 'primeng/selectbutton';
import { SelectModule } from 'primeng/select';
import { SkeletonModule } from 'primeng/skeleton';
import { TooltipModule } from 'primeng/tooltip';
import { InputTextModule } from 'primeng/inputtext';
import { InputNumberModule } from 'primeng/inputnumber';
import { DatePickerModule } from 'primeng/datepicker';
import { MessageService, ConfirmationService } from 'primeng/api';
import { Subject, Observable, EMPTY } from 'rxjs';
import { take, takeUntil, catchError, map } from 'rxjs/operators';
import { ApiEventService } from '../../services/api-event.service';
import { ApiLookupService } from '../../services/api-lookup.service';
import { 
  ApiEvent, 
  EventCreate, 
  EventUpdate, 
  EventStatusUpdate, 
  EventsQueryParams,
  LookupValue
} from '../../core/models/api.models';
import { CalendarDay, HebrewDateParts, EventStatus, Event } from '../../core/models';
import {
  buildHebrewMonthOptions,
  formatHebrewMonthTitle,
  getHebrewMonthLength,
  getHebrewYearsRange,
  hebrewPartsToGregorian,
  renderHebrewLabelFromParts,
  sanitizeHebrewParts,
  shiftHebrewMonth,
  toHebrewParts
} from '../../core/utils/hebrew-date.util';

// Helper function to convert ApiEvent to local Event
function mapApiEventToEvent(apiEvent: ApiEvent): Event {
  return {
    id: apiEvent.id,
    name: apiEvent.name,
    participants: apiEvent.guest_count,
    eventType: apiEvent.event_type,
    foodType: 'כל הסוגים', // Default value, might need to be mapped from another field
    dishes: [], // Would need to map from apiEvent.dishes if available
    createdAt: new Date(apiEvent.created_at || new Date().toISOString()),
    eventDate: apiEvent.event_date,
    hebrewDate: undefined, // Would need Hebrew date calculation
    status: mapApiStatusToLocalStatus(apiEvent.status),
    notes: apiEvent.notes
  };
}

// Helper function to map API status to local EventStatus
function mapApiStatusToLocalStatus(apiStatus: string): EventStatus {
  const statusMap: { [key: string]: EventStatus } = {
    'pending': 'בהמתנה לאישור',
    'scheduled': 'אושר',
    'in-progress': 'עבר',
    'completed': 'הסתיים',
    'cancelled': 'התבטל'
  };
  
  return statusMap[apiStatus] || 'בהמתנה לאישור';
}

// Helper function to map local EventStatus to API status
function mapLocalStatusToApiStatus(localStatus: EventStatus): string {
  const statusMap: { [key in EventStatus]: string } = {
    'בהמתנה לאישור': 'pending',
    'אושר': 'scheduled',
    'עבר': 'in-progress',
    'הסתיים': 'completed',
    'התבטל': 'cancelled'
  };
  
  return statusMap[localStatus] || 'pending';
}

// Event status constants
export const EVENT_STATUS_OPTIONS: { label: string; value: EventStatus }[] = [
  { label: 'בהמתנה לאישור', value: 'בהמתנה לאישור' },
  { label: 'אושר', value: 'אושר' },
  { label: 'עבר', value: 'עבר' },
  { label: 'התבטל', value: 'התבטל' },
  { label: 'הסתיים', value: 'הסתיים' }
];

export const EVENT_STATUS_DISPLAY: { [key in EventStatus]: { label: string; severity: string; icon: string; class: string } } = {
  'בהמתנה לאישור': { label: 'בהמתנה לאישור', severity: 'warn', icon: 'clock', class: 'pending' },
  'אושר': { label: 'אושר', severity: 'info', icon: 'calendar', class: 'scheduled' },
  'עבר': { label: 'עבר', severity: 'secondary', icon: 'history', class: 'past' },
  'התבטל': { label: 'התבטל', severity: 'danger', icon: 'times', class: 'cancelled' },
  'הסתיים': { label: 'הסתיים', severity: 'success', icon: 'check', class: 'completed' }
};

type EventFilterKey = 'all' | 'past' | 'cancelled' | 'completed' | 'pending';
type CalendarViewMode = 'gregorian' | 'hebrew';
type DateInputMode = 'gregorian' | 'hebrew';

interface EventFilterButton {
  key: EventFilterKey;
  label: string;
}

interface EventFormModel {
  id?: string;
  name: string;
  participants: number;
  eventType: string;
  foodType: string;
  status: EventStatus;
  notes?: string;
  eventDate: Date;
  hebrewParts: HebrewDateParts;
  hebrewLabel: string;
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
    ToastModule,
    ConfirmDialogModule,
    SelectButtonModule,
    SelectModule,
    SkeletonModule,
    TooltipModule,
    InputTextModule,
    InputNumberModule,
    DatePickerModule
  ],
  templateUrl: './events.component.html',
  styleUrls: ['./events.component.scss'],
  providers: [MessageService, ConfirmationService]
})
export class EventsComponent implements OnInit, OnDestroy {
  readonly statusOptions = EVENT_STATUS_OPTIONS;
  readonly statusDisplay = EVENT_STATUS_DISPLAY;
  readonly filterButtons: EventFilterButton[] = [
    { key: 'all', label: 'כל האירועים' },
    { key: 'past', label: 'אירועים שהיו' },
    { key: 'cancelled', label: 'אירועים שהתבטלו' },
    { key: 'completed', label: 'אירועים שהסתיימו' },
    { key: 'pending', label: 'ממתינים לאישור' }
  ];
  readonly viewModeOptions = [
    { label: 'לוח לועזי', value: 'gregorian' },
    { label: 'תאריכים עבריים', value: 'hebrew' }
  ];
  readonly dateModeOptions = [
    { label: 'תאריך לועזי', value: 'gregorian' },
    { label: 'תאריך עברי', value: 'hebrew' }
  ];
  readonly weekDays = ['א׳', 'ב׳', 'ג׳', 'ד׳', 'ה׳', 'ו׳', 'ש׳'];

  events: Event[] = [];
  filteredEvents: Event[] = [];
  calendarCells: (CalendarDay | null)[] = [];
  calendarEvents: Event[] = [];
  selectedFilter: EventFilterKey = 'all';
  viewMode: CalendarViewMode = 'gregorian';
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
  statusLocked = false;
  statusUpdating = false;

  // Event form state
  eventFormVisible = false;
  eventFormMode: 'create' | 'edit' = 'create';
  eventFormSubmitting = false;
  dateInputMode: DateInputMode = 'gregorian';
  hebrewMonthOptions = buildHebrewMonthOptions(this.currentHebrewMonth.year);
  hebrewYearOptions = this.buildHebrewYearOptions(this.currentHebrewMonth.year);

  // Lookup data
  eventTypeOptions: string[] = [];
  kosherOptions: string[] = [];
  eventForm!: EventFormModel;

  private readonly destroy$ = new Subject<void>();

  constructor(
    private readonly eventService: ApiEventService,
    private readonly lookupService: ApiLookupService,
    private readonly messageService: MessageService,
    private readonly confirmationService: ConfirmationService
  ) {
    this.eventForm = this.buildDefaultFormModel();
  }

  ngOnInit(): void {
    this.lookupService.lookup$
      .pipe(takeUntil(this.destroy$))
      .subscribe((snapshot: any) => {
        this.eventTypeOptions = snapshot.eventTypes;
        this.kosherOptions = snapshot.kosherTypes;
        this.refreshHebrewSelectors(this.eventForm?.hebrewParts.year || this.currentHebrewMonth.year);
      });

    this.loadEvents();
    this.updateCalendarRange();
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
          this.events = events;
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

  openEventDetails(event: Event): void {
    this.selectedEvent = event;
    this.selectedStatus = event.status;
    this.statusLocked = false; // For now, allow all status modifications
    this.detailVisible = true;
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

  openEditForm(event: Event): void {
    if (this.detailVisible) {
      this.closeDialog();
    }
    const eventDate = this.toDate(event.eventDate);
    const hebrewParts = toHebrewParts(eventDate);
    this.eventFormMode = 'edit';
    this.dateInputMode = 'gregorian';
    this.eventForm = {
      id: event.id,
      name: event.name,
      participants: event.participants,
      eventType: event.eventType,
      foodType: event.foodType,
      status: event.status,
      notes: event.notes,
      eventDate: this.startOfDay(eventDate),
      hebrewParts,
      hebrewLabel: renderHebrewLabelFromParts(hebrewParts)
    };
    this.refreshHebrewSelectors(hebrewParts.year);
    this.eventFormVisible = true;
  }

  closeEventForm(): void {
    if (this.eventFormSubmitting) {
      return;
    }
    this.eventFormVisible = false;
    this.eventForm = this.buildDefaultFormModel();
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

  submitEventForm(): void {
    if (!this.isFormValid()) {
      this.messageService.add({
        severity: 'warn',
        summary: 'חסר מידע',
        detail: 'אנא מלאי את כל השדות החיוניים לפני שמירה'
      });
      return;
    }

    this.eventFormSubmitting = true;
    
    if (this.eventFormMode === 'create') {
      const createPayload: EventCreate = {
        name: this.eventForm.name,
        event_type: this.eventForm.eventType,
        event_date: this.eventForm.eventDate.toISOString().split('T')[0], 
        event_time: '00:00', // Default time
        guest_count: this.eventForm.participants,
        notes: this.eventForm.notes
      };

      this.eventService.createEvent(createPayload)
        .pipe(
          take(1),
          map(mapApiEventToEvent)
        )
        .subscribe({
          next: (created: Event) => {
            this.events = [created, ...this.events];
            this.applyFilter();
            this.syncCalendarWithSnapshot();
            
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
        event_type: this.eventForm.eventType,
        event_date: this.eventForm.eventDate.toISOString().split('T')[0],
        guest_count: this.eventForm.participants,
        notes: this.eventForm.notes
      };

      this.eventService
        .updateEvent(this.eventForm.id, updatePayload)
        .pipe(
          take(1),
          map(mapApiEventToEvent)
        )
        .subscribe({
          next: (updated: Event) => {
            const index = this.events.findIndex(e => e.id === updated.id);
            if (index !== -1) {
              this.events[index] = updated;
              this.applyFilter();
              this.syncCalendarWithSnapshot();
            }
            
            this.messageService.add({
              severity: 'success',
              summary: 'אירוע עודכן',
              detail: `${updated.name} נשמר בהצלחה`
            });
            this.eventFormSubmitting = false;
            this.closeEventForm();
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
    return EVENT_STATUS_DISPLAY[status]?.icon || 'info-circle';
  }

  getStatusClass(status: EventStatus): string {
    return `status-${EVENT_STATUS_DISPLAY[status]?.class || 'info'}`;
  }

  trackCell(index: number, cell: CalendarDay | null): string | number {
    if (!cell) {
      return `empty-${index}`;
    }
    return `${cell.date.getTime()}-${cell.events.length}`;
  }

  private persistStatusChange(): void {
    if (!this.selectedEvent || !this.selectedStatus) {
      return;
    }

    const statusUpdate: EventStatusUpdate = {
      status: mapLocalStatusToApiStatus(this.selectedStatus) as any
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
      this.isWithinRange(event.eventDate, this.calendarRange)
    );
    this.buildCalendarGrid();
    this.loadingCalendar = false;
  }

  private applyFilter(): void {
    const today = this.startOfToday();
    this.filteredEvents = this.events
      .filter(event => {
        const eventDate = this.toDate(event.eventDate);
        switch (this.selectedFilter) {
          case 'past':
            return eventDate < today;
          case 'cancelled':
            return event.status === 'התבטל';
          case 'completed':
            return event.status === 'הסתיים';
          case 'pending':
            return event.status === 'בהמתנה לאישור';
          default:
            return true;
        }
      })
      .sort((a, b) => this.toDate(b.eventDate).getTime() - this.toDate(a.eventDate).getTime());
  }

  private syncCalendarWithSnapshot(): void {
    this.calendarEvents = this.events.filter(event => this.isWithinRange(event.eventDate, this.calendarRange));
    this.buildCalendarGrid();
  }

  private buildCalendarGrid(): void {
    this.calendarCells = this.viewMode === 'gregorian'
      ? this.buildGregorianCalendarGrid()
      : this.buildHebrewCalendarGrid();
  }

  private buildGregorianCalendarGrid(): (CalendarDay | null)[] {
    const start = new Date(this.currentMonth.getFullYear(), this.currentMonth.getMonth(), 1);
    const end = new Date(this.currentMonth.getFullYear(), this.currentMonth.getMonth() + 1, 0);
    const daysInMonth = end.getDate();
    const cells: (CalendarDay | null)[] = [];

    for (let i = 0; i < start.getDay(); i++) {
      cells.push(null);
    }

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

    for (let i = 0; i < firstDate.getDay(); i++) {
      cells.push(null);
    }

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
      events: this.calendarEvents.filter(event => this.isSameDay(event.eventDate, date))
    };
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
      participants: 50,
      eventType: this.eventTypeOptions[0] || 'אירוע',
      foodType: this.kosherOptions[0] || 'חלבי',
      status: 'בהמתנה לאישור',
      notes: '',
      eventDate: baseDate,
      hebrewParts,
      hebrewLabel: renderHebrewLabelFromParts(hebrewParts)
    };
  }

  private buildHebrewYearOptions(centerYear: number): { label: string; value: number }[] {
    return getHebrewYearsRange(centerYear, 2, 6).map(year => ({
      label: year.toString(),
      value: year
    }));
  }

  private refreshHebrewSelectors(centerYear: number): void {
    this.hebrewMonthOptions = buildHebrewMonthOptions(centerYear);
    this.hebrewYearOptions = this.buildHebrewYearOptions(centerYear);
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
      form.participants > 0 &&
      form.eventType &&
      form.foodType &&
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

  get eventTypeSelectItems(): { label: string; value: string }[] {
    return this.eventTypeOptions.map(value => ({ label: value, value }));
  }

  get kosherSelectItems(): { label: string; value: string }[] {
    return this.kosherOptions.map(value => ({ label: value, value }));
  }
}
