import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
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
export class SettingsComponent implements OnInit {
  
  settings: AppSettings = {
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
      defaultCategory: 'מנה עיקרית',
      defaultKosherType: 'פרווה',
      showIngredientsCount: true
    },
    events: {
      autoSelectCurrentEvent: true,
      showEventInfoInHeader: true,
      defaultEventType: 'שבת',
      defaultFoodType: 'פרווה',
      maxEventsHistory: 50
    },
    products: {
      defaultView: 'table',
      autoUpdatePrices: false,
      showSupplierInfo: true,
      lowStockThreshold: 5,
      defaultCategory: 'מוצרי מזון'
    },
    advanced: {
      enableLogging: false,
      autoBackup: true,
      backupInterval: 7,
      clearDataOnExit: false
    }
  };

  // Options for dropdowns
  currencyOptions = [
    { label: 'שקל חדש (₪)', value: 'ILS' },
    { label: 'דולר ($)', value: 'USD' },
    { label: 'יורו (€)', value: 'EUR' }
  ];

  languageOptions = [
    { label: 'עברית', value: 'he' },
    { label: 'English', value: 'en' }
  ];

  themeOptions = [
    { label: 'בהיר - כחול', value: 'lara-light-blue' },
    { label: 'בהיר - ירוק', value: 'lara-light-green' },
    { label: 'כהה - כחול', value: 'lara-dark-blue' },
    { label: 'כהה - ירוק', value: 'lara-dark-green' }
  ];

  dishCategories = [
    { label: 'מנה עיקרית', value: 'מנה עיקרית' },
    { label: 'מנה ראשונה', value: 'מנה ראשונה' },
    { label: 'תוספת', value: 'תוספת' },
    { label: 'קינוח', value: 'קינוח' },
    { label: 'משקה', value: 'משקה' },
    { label: 'חטיף', value: 'חטיף' }
  ];

  kosherTypes = [
    { label: 'חלבי', value: 'חלבי' },
    { label: 'בשרי', value: 'בשרי' },
    { label: 'פרווה', value: 'פרווה' }
  ];

  eventTypes = [
    { label: 'שבת', value: 'שבת' },
    { label: 'שבע ברכות', value: 'שבע ברכות' },
    { label: 'ברית', value: 'ברית' },
    { label: 'בוקר', value: 'בוקר' }
  ];

  foodTypes = [
    { label: 'בשרי', value: 'בשרי' },
    { label: 'חלבי', value: 'חלבי' },
    { label: 'פרווה', value: 'פרווה' }
  ];

  productCategories = [
    { label: 'מוצרי מזון', value: 'מוצרי מזון' },
    { label: 'משקאות', value: 'משקאות' },
    { label: 'חטיפים', value: 'חטיפים' },
    { label: 'מוצרי חלב', value: 'מוצרי חלב' }
  ];

  viewOptions = [
    { label: 'טבלה', value: 'table' },
    { label: 'כרטיסים', value: 'cards' }
  ];

  constructor(private messageService: MessageService) {}

  ngOnInit(): void {
    this.loadSettings();
  }

  loadSettings(): void {
    const savedSettings = localStorage.getItem('appSettings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        this.settings = { ...this.settings, ...parsed };
      } catch (error) {
        console.error('Error loading settings:', error);
        this.messageService.add({
          severity: 'warn',
          summary: 'שגיאה',
          detail: 'לא ניתן לטעון הגדרות קודמות, נטענות הגדרות ברירת מחדל'
        });
      }
    }
  }

  saveSettings(): void {
    try {
      localStorage.setItem('appSettings', JSON.stringify(this.settings));
      this.messageService.add({
        severity: 'success',
        summary: 'נשמר בהצלחה',
        detail: 'ההגדרות נשמרו בהצלחה'
      });
    } catch (error) {
      console.error('Error saving settings:', error);
      this.messageService.add({
        severity: 'error',
        summary: 'שגיאה',
        detail: 'לא ניתן לשמור הגדרות'
      });
    }
  }

  resetToDefaults(): void {
    this.settings = {
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
        defaultCategory: 'מנה עיקרית',
        defaultKosherType: 'פרווה',
        showIngredientsCount: true
      },
      events: {
        autoSelectCurrentEvent: true,
        showEventInfoInHeader: true,
        defaultEventType: 'שבת',
        defaultFoodType: 'פרווה',
        maxEventsHistory: 50
      },
      products: {
        defaultView: 'table',
        autoUpdatePrices: false,
        showSupplierInfo: true,
        lowStockThreshold: 5,
        defaultCategory: 'מוצרי מזון'
      },
      advanced: {
        enableLogging: false,
        autoBackup: true,
        backupInterval: 7,
        clearDataOnExit: false
      }
    };

    this.messageService.add({
      severity: 'info',
      summary: 'איפוס הגדרות',
      detail: 'ההגדרות אופסו לברירת המחדל'
    });
  }

  exportSettings(): void {
    const dataStr = JSON.stringify(this.settings, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = `planmyevents-settings-${new Date().toISOString().split('T')[0]}.json`;
    link.click();

    this.messageService.add({
      severity: 'success',
      summary: 'יוצא בהצלחה',
      detail: 'ההגדרות יוצאו לקובץ'
    });
  }

  importSettings(event: any): void {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const importedSettings = JSON.parse(e.target?.result as string);
        this.settings = { ...this.settings, ...importedSettings };
        this.messageService.add({
          severity: 'success',
          summary: 'יובא בהצלחה',
          detail: 'ההגדרות יובאו בהצלחה'
        });
      } catch (error) {
        this.messageService.add({
          severity: 'error',
          summary: 'שגיאה',
          detail: 'קובץ ההגדרות פגום או לא תקין'
        });
      }
    };
    reader.readAsText(file);
  }

  clearAllData(): void {
    // Clear all application data
    const keysToKeep = ['appSettings']; // Keep settings
    const allKeys = Object.keys(localStorage);
    
    allKeys.forEach(key => {
      if (!keysToKeep.includes(key)) {
        localStorage.removeItem(key);
      }
    });

    this.messageService.add({
      severity: 'warn',
      summary: 'נתונים נמחקו',
      detail: 'כל נתוני האפליקציה נמחקו (למעט הגדרות)'
    });
  }
}