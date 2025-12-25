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
import { Subject } from 'rxjs';
import { take, takeUntil } from 'rxjs/operators';
import { EventService } from '../../core/services/event.service';
import { CalendarDay, Event, EventStatus, HebrewDateParts } from '../../core/models';
import { EVENT_STATUS_DISPLAY, EVENT_STATUS_OPTIONS } from '../../core/constants/app.constants';
import { LookupService } from '../../core/services/lookup.service';
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
    private readonly eventService: EventService,
    private readonly lookupService: LookupService,
    private readonly messageService: MessageService,
    private readonly confirmationService: ConfirmationService
  ) {
    this.eventForm = this.buildDefaultFormModel();
  }

  ngOnInit(): void {
    this.lookupService.lookup$
      .pipe(takeUntil(this.destroy$))
      .subscribe(snapshot => {
        this.eventTypeOptions = snapshot.eventTypes;
        this.kosherOptions = snapshot.kosherTypes;
        this.refreshHebrewSelectors(this.eventForm?.hebrewParts.year || this.currentHebrewMonth.year);
      });

    this.eventService.events$
      .pipe(takeUntil(this.destroy$))
      .subscribe(events => {
        this.events = events;
        this.loadingList = false;
        this.applyFilter();
        this.syncCalendarWithSnapshot();
      });

    this.updateCalendarRange();
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
    this.statusLocked = !this.eventService.canModifyStatus(event);
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
        this.eventService.deleteEvent(event.id);
        if (origin === 'details') {
          this.closeDialog();
        }
        this.messageService.add({
          severity: 'success',
          summary: 'אירוע נמחק',
          detail: `${event.name} הוסר מהמערכת`
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

    const payload = {
      name: this.eventForm.name,
      participants: this.eventForm.participants,
      eventType: this.eventForm.eventType,
      foodType: this.eventForm.foodType,
      status: this.eventForm.status,
      notes: this.eventForm.notes,
      eventDate: this.eventForm.eventDate,
      hebrewDate: this.eventForm.hebrewLabel,
      hebrewParts: this.eventForm.hebrewParts
    };

    this.eventFormSubmitting = true;
    if (this.eventFormMode === 'create') {
      const eventId = this.eventService.createEvent(payload);
      this.eventService.setCurrentEvent(eventId);
      this.messageService.add({
        severity: 'success',
        summary: 'אירוע נוצר',
        detail: `${this.eventForm.name} נוסף ללוח`
      });
      this.eventFormSubmitting = false;
      this.closeEventForm();
    } else if (this.eventForm.id) {
      this.eventService
        .updateEventDetails(this.eventForm.id, payload)
        .pipe(take(1))
        .subscribe({
          next: updated => {
            this.messageService.add({
              severity: 'success',
              summary: 'אירוע עודכן',
              detail: `${updated.name} נשמר בהצלחה`
            });
            this.eventFormSubmitting = false;
            this.closeEventForm();
          },
          error: error => {
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
    const severity = this.statusDisplay[status]?.severity;
    if (!severity) {
      return null;
    }

    return severity === 'warning' ? 'warn' : severity;
  }

  getStatusIcon(status: EventStatus): string {
    return this.statusDisplay[status]?.icon || 'pi pi-info-circle';
  }

  getStatusClass(status: EventStatus): string {
    return `status-${this.statusDisplay[status]?.severity || 'info'}`;
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

    this.statusUpdating = true;
    this.eventService
      .updateEventStatus(this.selectedEvent.id, this.selectedStatus)
      .pipe(take(1))
      .subscribe({
        next: updated => {
          this.selectedEvent = updated;
          this.selectedStatus = updated.status;
          this.statusLocked = !this.eventService.canModifyStatus(updated);
          this.messageService.add({
            severity: 'success',
            summary: 'סטטוס עודכן',
            detail: `${updated.name} עודכן בהצלחה`
          });
          this.statusUpdating = false;
        },
        error: error => {
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
    this.eventService
      .fetchEventsByRange(this.calendarRange.start, this.calendarRange.end)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: events => {
          this.calendarEvents = events;
          this.buildCalendarGrid();
        },
        error: () => {
          this.calendarEvents = [];
          this.buildCalendarGrid();
          this.loadingCalendar = false;
        },
        complete: () => {
          this.loadingCalendar = false;
        }
      });
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
    return !this.eventService.canModifyStatus(matchingEvent);
  }

  get eventTypeSelectItems(): { label: string; value: string }[] {
    return this.eventTypeOptions.map(value => ({ label: value, value }));
  }

  get kosherSelectItems(): { label: string; value: string }[] {
    return this.kosherOptions.map(value => ({ label: value, value }));
  }
}
