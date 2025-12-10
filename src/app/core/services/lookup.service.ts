import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import {
  DEFAULT_LOOKUP_DATA,
  DEFAULT_DASHBOARD_SECTIONS,
  DEFAULT_DASHBOARD_METRICS,
  LookupData,
  LookupListKey,
  DashboardWidgetConfig,
  DashboardWidgetGroup
} from '../constants/app.constants';
import { StorageService } from './storage.service';

@Injectable({ providedIn: 'root' })
export class LookupService {
  private readonly storageKey = 'lookupData';
  private readonly dataSubject = new BehaviorSubject<LookupData>(
    this.loadInitialData()
  );

  readonly lookup$ = this.dataSubject.asObservable();

  constructor(private storage: StorageService) {}

  getSnapshot(): LookupData {
    return this.cloneData(this.dataSubject.value);
  }

  getList(key: LookupListKey): string[] {
    return [...this.dataSubject.value[key]];
  }

  addListItem(key: LookupListKey, rawValue: string): void {
    const value = this.sanitizeValue(rawValue);
    if (!value) {
      return;
    }

    const current = this.getList(key);
    if (current.includes(value)) {
      return;
    }

    const updated = [...current, value];
    this.applyListUpdate(key, updated);
  }

  updateListItem(key: LookupListKey, index: number, rawValue: string): void {
    const value = this.sanitizeValue(rawValue);
    if (!value) {
      this.removeListItem(key, index);
      return;
    }

    const current = this.getList(key);
    if (current[index] === value) {
      return;
    }

    const duplicate = current.some((item, idx) => item === value && idx !== index);
    if (duplicate) {
      return;
    }

    const updated = [...current];
    updated[index] = value;
    this.applyListUpdate(key, updated);
  }

  removeListItem(key: LookupListKey, index: number): void {
    const current = this.getList(key);
    if (index < 0 || index >= current.length) {
      return;
    }

    const updated = current.filter((_, idx) => idx !== index);
    this.applyListUpdate(key, updated);
  }

  resetList(key: LookupListKey): void {
    const defaults = DEFAULT_LOOKUP_DATA[key] as string[];
    this.applyListUpdate(key, [...defaults]);
  }

  resetAll(): void {
    const cloned = this.cloneData(DEFAULT_LOOKUP_DATA);
    this.persist(cloned);
  }

  toggleWidget(
    group: DashboardWidgetGroup,
    widgetId: string,
    enabled: boolean
  ): void {
    const widgets = this.getWidgetCollection(group);
    const idx = widgets.findIndex(widget => widget.id === widgetId);
    if (idx === -1) {
      return;
    }

    const updatedWidgets = widgets.map(widget =>
      widget.id === widgetId ? { ...widget, enabled } : widget
    );

    this.applyWidgetUpdate(group, updatedWidgets);
  }

  upsertWidget(
    group: DashboardWidgetGroup,
    widget: DashboardWidgetConfig
  ): void {
    const sanitized = this.sanitizeWidget(widget);
    if (!sanitized.id) {
      return;
    }

    const widgets = this.getWidgetCollection(group);
    const existingIndex = widgets.findIndex(item => item.id === sanitized.id);

    let updatedWidgets: DashboardWidgetConfig[];
    if (existingIndex === -1) {
      updatedWidgets = [...widgets, sanitized];
    } else {
      updatedWidgets = widgets.map((item, idx) =>
        idx === existingIndex ? { ...item, ...sanitized } : item
      );
    }

    this.applyWidgetUpdate(group, updatedWidgets);
  }

  removeWidget(group: DashboardWidgetGroup, widgetId: string): void {
    const widgets = this.getWidgetCollection(group).filter(
      widget => widget.id !== widgetId
    );
    this.applyWidgetUpdate(group, widgets);
  }

  resetWidgetGroup(group: DashboardWidgetGroup): void {
    const defaults =
      group === 'dashboardSections'
        ? DEFAULT_DASHBOARD_SECTIONS
        : DEFAULT_DASHBOARD_METRICS;
    this.applyWidgetUpdate(
      group,
      defaults.map(item => ({ ...item }))
    );
  }

  private loadInitialData(): LookupData {
    const stored = this.storage.get<LookupData>(this.storageKey);
    return this.mergeLookupData(stored ?? undefined);
  }

  private mergeLookupData(stored?: LookupData): LookupData {
    const defaults = this.cloneData(DEFAULT_LOOKUP_DATA);
    if (!stored) {
      return defaults;
    }

    return {
      dishCategories: this.normalizeList(
        stored.dishCategories,
        defaults.dishCategories
      ),
      kosherTypes: this.normalizeList(stored.kosherTypes, defaults.kosherTypes),
      measurementUnits: this.normalizeList(
        stored.measurementUnits,
        defaults.measurementUnits
      ),
      productCategories: this.normalizeList(
        stored.productCategories,
        defaults.productCategories
      ),
      inventoryStatuses: this.normalizeList(
        stored.inventoryStatuses,
        defaults.inventoryStatuses
      ),
      eventTypes: this.normalizeList(stored.eventTypes, defaults.eventTypes),
      dashboardSections: this.mergeWidgetCollection(
        stored.dashboardSections,
        DEFAULT_DASHBOARD_SECTIONS
      ),
      dashboardMetrics: this.mergeWidgetCollection(
        stored.dashboardMetrics,
        DEFAULT_DASHBOARD_METRICS
      )
    };
  }

  private mergeWidgetCollection(
    stored: DashboardWidgetConfig[] | undefined,
    defaults: DashboardWidgetConfig[]
  ): DashboardWidgetConfig[] {
    const merged = new Map<string, DashboardWidgetConfig>();
    defaults.forEach(widget => {
      merged.set(widget.id, { ...widget });
    });

    (stored ?? []).forEach(widget => {
      if (!widget) {
        return;
      }
      const sanitized = this.sanitizeWidget(widget);
      if (!sanitized.id) {
        return;
      }
      const current = merged.get(sanitized.id) ?? {
        id: sanitized.id,
        label: sanitized.label || sanitized.id,
        enabled: true
      };
      merged.set(sanitized.id, { ...current, ...sanitized });
    });

    return Array.from(merged.values());
  }

  private getWidgetCollection(group: DashboardWidgetGroup): DashboardWidgetConfig[] {
    const current = this.dataSubject.value[group];
    return current.map(widget => ({ ...widget }));
  }

  private applyListUpdate(key: LookupListKey, values: string[]): void {
    const trimmed = this.normalizeList(values);
    const current = this.cloneData(this.dataSubject.value);
    current[key] = trimmed;
    this.persist(current);
  }

  private applyWidgetUpdate(
    group: DashboardWidgetGroup,
    widgets: DashboardWidgetConfig[]
  ): void {
    const current = this.cloneData(this.dataSubject.value);
    current[group] = widgets.map(widget => ({ ...widget }));
    this.persist(current);
  }

  private persist(data: LookupData): void {
    const cloned = this.cloneData(data);
    this.storage.set(this.storageKey, cloned);
    this.dataSubject.next(cloned);
  }

  private cloneData(data: LookupData): LookupData {
    return {
      dishCategories: [...data.dishCategories],
      kosherTypes: [...data.kosherTypes],
      measurementUnits: [...data.measurementUnits],
      productCategories: [...data.productCategories],
      inventoryStatuses: [...data.inventoryStatuses],
      eventTypes: [...data.eventTypes],
      dashboardSections: data.dashboardSections.map(widget => ({ ...widget })),
      dashboardMetrics: data.dashboardMetrics.map(widget => ({ ...widget }))
    };
  }

  private normalizeList(
    values: string[] | undefined,
    fallback: string[] = []
  ): string[] {
    const normalized = (values ?? fallback)
      .map(value => this.sanitizeValue(value))
      .filter((value): value is string => !!value);

    const unique: string[] = [];
    normalized.forEach(value => {
      if (!unique.includes(value)) {
        unique.push(value);
      }
    });

    return unique;
  }

  private sanitizeValue(raw: string): string {
    return (raw ?? '').toString().trim();
  }

  private sanitizeWidget(widget: DashboardWidgetConfig): DashboardWidgetConfig {
    const id = this.sanitizeValue(widget.id);
    const label = this.sanitizeValue(widget.label || id);
    const description = this.sanitizeValue(widget.description || '');
    const accentColor = this.sanitizeValue(widget.accentColor || '');

    return {
      id,
      label: label || id,
      enabled: widget.enabled !== false,
      description: description || undefined,
      accentColor: accentColor || undefined
    };
  }
}
