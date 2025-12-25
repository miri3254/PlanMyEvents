import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { InputTextModule } from 'primeng/inputtext';
import { InputNumberModule } from 'primeng/inputnumber';
import { SelectModule } from 'primeng/select';
import { CheckboxModule } from 'primeng/checkbox';
import { DividerModule } from 'primeng/divider';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { FloatLabelModule } from 'primeng/floatlabel';
import { FieldsetModule } from 'primeng/fieldset';
import { ToggleButtonModule } from 'primeng/togglebutton';
import { MultiSelectModule } from 'primeng/multiselect';
import {
  DashboardWidgetConfig,
  DashboardWidgetGroup,
  LookupData,
  LookupListKey
} from '../../core/constants/app.constants';
import { LookupService } from '../../core/services/lookup.service';

interface AppSettings {
  general: {
    appName: string;
    defaultParticipants: number;
    currency: string;
    language: string;
    theme: string;
  };
  dishes: {
    defaultServingSize: number;
    showPricesInCards: boolean;
    autoSaveChanges: boolean;
    defaultCategory: string;
    defaultKosherType: string;
    showIngredientsCount: boolean;
  };
  events: {
    autoSelectCurrentEvent: boolean;
    showEventInfoInHeader: boolean;
    defaultEventType: string;
    defaultFoodType: string;
    maxEventsHistory: number;
  };
  products: {
    defaultView: 'table' | 'cards';
    autoUpdatePrices: boolean;
    showSupplierInfo: boolean;
    lowStockThreshold: number;
    defaultCategory: string;
  };
  advanced: {
    enableLogging: boolean;
    autoBackup: boolean;
    backupInterval: number; // in days
    clearDataOnExit: boolean;
  };
}

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ButtonModule,
    CardModule,
    InputTextModule,
    InputNumberModule,
    SelectModule,
    CheckboxModule,
    DividerModule,
    ToastModule,
    FloatLabelModule,
    FieldsetModule,
    ToggleButtonModule,
    MultiSelectModule
  ],
  templateUrl: './settings.html',
  styleUrls: ['./settings.scss'],
  providers: [MessageService]
})
export class SettingsComponent implements OnInit, OnDestroy {
  private readonly destroy$ = new Subject<void>();

  settings: AppSettings;
  lookupData: LookupData | null = null;

  readonly currencyOptions = [
    { label: 'שקל חדש (₪)', value: 'ILS' },
    { label: 'דולר ($)', value: 'USD' },
    { label: 'יורו (€)', value: 'EUR' }
  ];

  readonly languageOptions = [
    { label: 'עברית', value: 'he' },
    { label: 'English', value: 'en' }
  ];

  readonly themeOptions = [
    { label: 'בהיר - כחול', value: 'lara-light-blue' },
    { label: 'בהיר - ירוק', value: 'lara-light-green' },
    { label: 'כהה - כחול', value: 'lara-dark-blue' },
    { label: 'כהה - ירוק', value: 'lara-dark-green' }
  ];

  dishCategories: { label: string; value: string }[] = [];
  kosherTypes: { label: string; value: string }[] = [];
  eventTypes: { label: string; value: string }[] = [];
  foodTypes: { label: string; value: string }[] = [];
  productCategories: { label: string; value: string }[] = [];

  viewOptions = [
    { label: 'טבלה', value: 'table' },
    { label: 'כרטיסים', value: 'cards' }
  ];

  readonly listKeys: LookupListKey[] = [
    'dishCategories',
    'kosherTypes',
    'measurementUnits',
    'productCategories',
    'inventoryStatuses',
    'eventTypes'
  ];

  listDrafts: Record<LookupListKey, string> = {
    dishCategories: '',
    kosherTypes: '',
    measurementUnits: '',
    productCategories: '',
    inventoryStatuses: '',
    eventTypes: ''
  };

  editableLists: Record<LookupListKey, string[]> = {
    dishCategories: [],
    kosherTypes: [],
    measurementUnits: [],
    productCategories: [],
    inventoryStatuses: [],
    eventTypes: []
  };

  listGroups = [
    {
      title: 'ניהול מנות',
      description: 'בנה קטגוריות, סוגי כשרות ויחידות מידה מותאמות לתהליך ההכנה.',
      lists: [
        {
          key: 'dishCategories' as LookupListKey,
          label: 'קטגוריות מנות',
          placeholder: 'הוסף קטגוריה חדשה',
          icon: 'pi pi-th-large'
        },
        {
          key: 'kosherTypes' as LookupListKey,
          label: 'סוגי כשרות',
          placeholder: 'הוסף סוג כשרות',
          icon: 'pi pi-shield'
        },
        {
          key: 'measurementUnits' as LookupListKey,
          label: 'יחידות מידה',
          placeholder: 'הוסף יחידת מידה',
          icon: 'pi pi-compass'
        }
      ]
    },
    {
      title: 'ניהול מוצרים',
      description: 'התאם את קטגוריות המלאי וסוגי הסטטוסים לצוות הרכש שלך.',
      lists: [
        {
          key: 'productCategories' as LookupListKey,
          label: 'קטגוריות מוצרים',
          placeholder: 'הוסף קטגוריה חדשה',
          icon: 'pi pi-box'
        },
        {
          key: 'inventoryStatuses' as LookupListKey,
          label: 'סטטוס מלאי',
          placeholder: 'הוסף סטטוס מלאי',
          icon: 'pi pi-chart-line'
        }
      ]
    },
    {
      title: 'ניהול לוח בקרה',
      description: 'קבע אילו סוגי אירועים ותובנות מזינים את הוויזואליזציות בלוח הבקרה.',
      lists: [
        {
          key: 'eventTypes' as LookupListKey,
          label: 'סוגי אירועים',
          placeholder: 'הוסף סוג אירוע',
          icon: 'pi pi-calendar'
        }
      ]
    }
  ];

  dashboardCollections: Record<DashboardWidgetGroup, DashboardWidgetConfig[]> = {
    dashboardSections: [],
    dashboardMetrics: []
  };

  dashboardDrafts: Record<DashboardWidgetGroup, { label: string; description: string }> = {
    dashboardSections: { label: '', description: '' },
    dashboardMetrics: { label: '', description: '' }
  };

  dashboardGroups = [
    {
      key: 'dashboardSections' as DashboardWidgetGroup,
      title: 'כרטיסי על בלוח הבקרה',
      description: 'בחר אילו כרטיסי מידע מוצגים כשמשתמש נכנס ללוח הבקרה.',
      addPlaceholder: 'שם אזור חדש',
      addDescriptionPlaceholder: 'תיאור קצר לאזור'
    },
    {
      key: 'dashboardMetrics' as DashboardWidgetGroup,
      title: 'מדדי עומק וניתוחים',
      description: 'נהל מדדי ביצועים משלימים והתראות חכמות ללוח הבקרה.',
      addPlaceholder: 'שם מדד חדש',
      addDescriptionPlaceholder: 'מה מודד המדד הזה?'
    }
  ];

  constructor(
    private messageService: MessageService,
    private lookupService: LookupService
  ) {
    this.settings = this.buildDefaultSettings();
  }

  ngOnInit(): void {
    this.lookupService.lookup$
      .pipe(takeUntil(this.destroy$))
      .subscribe(data => {
        this.lookupData = data;
        this.updateSelectOptions(data);
        this.listKeys.forEach(key => {
          this.editableLists[key] = [...data[key]];
        });
        this.dashboardCollections.dashboardSections = data.dashboardSections.map(widget => ({ ...widget }));
        this.dashboardCollections.dashboardMetrics = data.dashboardMetrics.map(widget => ({ ...widget }));
        this.syncSettingsWithLookups(data);
      });

    this.loadSettings();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadSettings(): void {
    const savedSettings = localStorage.getItem('appSettings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        this.settings = { ...this.settings, ...parsed };
        if (this.lookupData) {
          this.syncSettingsWithLookups(this.lookupData);
        }
      } catch (error) {
        console.error('Error loading settings:', error);
        this.notify('warn', 'שגיאה', 'לא ניתן לטעון הגדרות קודמות, נטענות ברירות מחדל.');
      }
    }
  }

  saveSettings(): void {
    try {
      localStorage.setItem('appSettings', JSON.stringify(this.settings));
      this.notify('success', 'נשמר בהצלחה', 'ההגדרות נשמרו בהצלחה.');
    } catch (error) {
      console.error('Error saving settings:', error);
      this.notify('error', 'שגיאה', 'לא ניתן לשמור הגדרות כרגע.');
    }
  }

  resetToDefaults(): void {
    this.settings = this.buildDefaultSettings();
    if (this.lookupData) {
      this.syncSettingsWithLookups(this.lookupData);
    }
    this.notify('info', 'איפוס הגדרות', 'ההגדרות הכלליות אופסו לערכי ברירת המחדל.');
  }

  resetAllLookupData(): void {
    this.lookupService.resetAll();
    this.notify('info', 'איפוס מילונים', 'כל רשימות הניהול אופסו לערכי ברירת המחדל.');
  }

  exportSettings(): void {
    const dataStr = JSON.stringify(this.settings, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });

    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = `planmyevents-settings-${new Date().toISOString().split('T')[0]}.json`;
    link.click();

    this.notify('success', 'יוצא בהצלחה', 'ההגדרות יוצאו לקובץ JSON.');
  }

  importSettings(event: any): void {
    const file = event.target.files[0];
    if (!file) {
      return;
    }

    const reader = new FileReader();
    reader.onload = e => {
      try {
        const importedSettings = JSON.parse(e.target?.result as string);
        this.settings = { ...this.settings, ...importedSettings };
        if (this.lookupData) {
          this.syncSettingsWithLookups(this.lookupData);
        }
        this.notify('success', 'יובא בהצלחה', 'קובץ ההגדרות נטען והוחל.');
      } catch (error) {
        this.notify('error', 'שגיאה ביבוא', 'קובץ ההגדרות פגום או לא תקין.');
      }
    };
    reader.readAsText(file);
  }

  clearAllData(): void {
    const keysToKeep = ['appSettings', 'planmyevents_lookupData'];
    const allKeys = Object.keys(localStorage);

    allKeys.forEach(key => {
      if (!keysToKeep.includes(key)) {
        localStorage.removeItem(key);
      }
    });

    this.notify('warn', 'נתוני מערכת נוקו', 'כל הנתונים נמחקו מלבד הגדרות והתאמות מילונים.');
  }

  addListItem(key: LookupListKey): void {
    const value = this.listDrafts[key].trim();
    if (!value) {
      this.notify('warn', 'ערך חסר', 'יש להזין ערך לפני שמירה.');
      return;
    }

    if (this.editableLists[key].includes(value)) {
      this.notify('warn', 'ערך קיים', 'הערך כבר נמצא ברשימה.');
      return;
    }

    this.lookupService.addListItem(key, value);
    this.listDrafts[key] = '';
    this.ensureSettingValues(key, this.lookupService.getList(key));
    this.notify('success', 'נוסף בהצלחה', 'נוסף ערך חדש לרשימה.');
  }

  commitListItem(key: LookupListKey, index: number): void {
    const value = (this.editableLists[key][index] || '').trim();
    const previousValue = this.lookupData?.[key]?.[index] ?? null;
    this.lookupService.updateListItem(key, index, value);
    if (previousValue && value) {
      this.replaceSettingValue(key, previousValue, value);
    }
    this.ensureSettingValues(key, this.lookupService.getList(key));
    this.notify('success', 'עודכן בהצלחה', 'הערך עודכן במילון.');
  }

  removeListItem(key: LookupListKey, index: number): void {
    const removedValue = this.lookupData?.[key]?.[index] ?? null;
    this.lookupService.removeListItem(key, index);
    this.ensureSettingValues(key, this.lookupService.getList(key));
    if (removedValue) {
      this.replaceSettingValue(key, removedValue, '');
    }
    this.notify('warn', 'הערך הוסר', 'הפריט הוסר מהרשימה.');
  }

  resetList(key: LookupListKey): void {
    this.lookupService.resetList(key);
    this.ensureSettingValues(key, this.lookupService.getList(key));
    this.notify('info', 'הרשימה אופסה', 'הרשימה חזרה לערכי ברירת המחדל.');
  }

  addDashboardWidget(group: DashboardWidgetGroup): void {
    const draft = this.dashboardDrafts[group];
    const label = draft.label.trim();
    const description = draft.description.trim();

    if (!label) {
      this.notify('warn', 'שם חסר', 'יש להזין שם לפני הוספת רכיב.');
      return;
    }

    const widget: DashboardWidgetConfig = {
      id: this.generateWidgetId(label),
      label,
      enabled: true,
      description: description || undefined
    };

    this.lookupService.upsertWidget(group, widget);
    this.dashboardDrafts[group] = { label: '', description: '' };
    this.notify('success', 'רכיב נוצר', 'נוסף רכיב חדש ללוח הבקרה.');
  }

  commitWidget(group: DashboardWidgetGroup, index: number): void {
    const widget = this.dashboardCollections[group][index];
    this.lookupService.upsertWidget(group, widget);
    this.notify('success', 'עודכן רכיב', 'הרכיב עודכן בהצלחה.');
  }

  removeWidget(group: DashboardWidgetGroup, index: number): void {
    const widget = this.dashboardCollections[group][index];
    this.lookupService.removeWidget(group, widget.id);
    this.notify('warn', 'רכיב הוסר', 'הרכיב הוסר מלוח הבקרה.');
  }

  resetWidgetGroup(group: DashboardWidgetGroup): void {
    this.lookupService.resetWidgetGroup(group);
    this.notify('info', 'איפוס קבוצה', 'הרכיבים חזרו לברירות המחדל.');
  }

  private buildDefaultSettings(): AppSettings {
    const lookup = this.lookupService.getSnapshot();
    const firstCategory = lookup.dishCategories[0] || '';
    const firstKosher = lookup.kosherTypes[0] || '';
    const firstEvent = lookup.eventTypes[0] || '';
    const firstProductCategory = lookup.productCategories[0] || '';

    return {
      general: {
        appName: 'PlanMyEvents',
        defaultParticipants: 10,
        currency: 'ILS',
        language: 'he',
        theme: 'lara-light-blue'
      },
      dishes: {
        defaultServingSize: 4,
        showPricesInCards: true,
        autoSaveChanges: true,
        defaultCategory: firstCategory,
        defaultKosherType: firstKosher,
        showIngredientsCount: true
      },
      events: {
        autoSelectCurrentEvent: true,
        showEventInfoInHeader: true,
        defaultEventType: firstEvent,
        defaultFoodType: firstKosher,
        maxEventsHistory: 50
      },
      products: {
        defaultView: 'table',
        autoUpdatePrices: false,
        showSupplierInfo: true,
        lowStockThreshold: 5,
        defaultCategory: firstProductCategory
      },
      advanced: {
        enableLogging: false,
        autoBackup: true,
        backupInterval: 7,
        clearDataOnExit: false
      }
    };
  }

  private updateSelectOptions(data: LookupData): void {
    this.dishCategories = data.dishCategories.map(value => ({ label: value, value }));
    this.kosherTypes = data.kosherTypes.map(value => ({ label: value, value }));
    this.eventTypes = data.eventTypes.map(value => ({ label: value, value }));
    this.foodTypes = data.kosherTypes.map(value => ({ label: value, value }));
    this.productCategories = data.productCategories.map(value => ({ label: value, value }));
  }

  private syncSettingsWithLookups(data: LookupData): void {
    this.ensureSettingValues('dishCategories', data.dishCategories);
    this.ensureSettingValues('kosherTypes', data.kosherTypes);
    this.ensureSettingValues('eventTypes', data.eventTypes);
    this.ensureSettingValues('productCategories', data.productCategories);
  }

  private ensureSettingValues(key: LookupListKey, values: string[]): void {
    const firstValue = values[0] || '';
    switch (key) {
      case 'dishCategories':
        if (!values.includes(this.settings.dishes.defaultCategory)) {
          this.settings.dishes.defaultCategory = firstValue;
        }
        break;
      case 'kosherTypes':
        if (!values.includes(this.settings.dishes.defaultKosherType)) {
          this.settings.dishes.defaultKosherType = firstValue;
        }
        if (!values.includes(this.settings.events.defaultFoodType)) {
          this.settings.events.defaultFoodType = firstValue;
        }
        break;
      case 'eventTypes':
        if (!values.includes(this.settings.events.defaultEventType)) {
          this.settings.events.defaultEventType = firstValue;
        }
        break;
      case 'productCategories':
        if (!values.includes(this.settings.products.defaultCategory)) {
          this.settings.products.defaultCategory = firstValue;
        }
        break;
      default:
        break;
    }
  }

  private replaceSettingValue(
    key: LookupListKey,
    previousValue: string,
    nextValue: string
  ): void {
    switch (key) {
      case 'dishCategories':
        if (this.settings.dishes.defaultCategory === previousValue) {
          this.settings.dishes.defaultCategory = nextValue;
        }
        break;
      case 'kosherTypes':
        if (this.settings.dishes.defaultKosherType === previousValue) {
          this.settings.dishes.defaultKosherType = nextValue;
        }
        if (this.settings.events.defaultFoodType === previousValue) {
          this.settings.events.defaultFoodType = nextValue;
        }
        break;
      case 'eventTypes':
        if (this.settings.events.defaultEventType === previousValue) {
          this.settings.events.defaultEventType = nextValue;
        }
        break;
      case 'productCategories':
        if (this.settings.products.defaultCategory === previousValue) {
          this.settings.products.defaultCategory = nextValue;
        }
        break;
      default:
        break;
    }
  }

  private generateWidgetId(label: string): string {
    const normalized = label
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');
    return normalized || `widget-${Date.now()}`;
  }

  private notify(
    severity: 'success' | 'info' | 'warn' | 'error',
    summary: string,
    detail: string
  ): void {
    this.messageService.add({ severity, summary, detail });
  }
}