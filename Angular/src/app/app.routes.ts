import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => 
      import('./components/dashboard/dashboard')
        .then(m => m.DashboardComponent),
    title: 'לוח בקרה - PlanMyEvents'
  },
  {
    path: 'dishes',
    loadComponent: () => 
      import('./components/dishes/dishes.component')
        .then(m => m.DishesComponent),
    title: 'מנות - PlanMyEvents'
  },
  {
    path: 'dishes/event/:eventId',
    loadComponent: () => 
      import('./components/dishes/dishes.component')
        .then(m => m.DishesComponent),
    title: 'בחירת מנות לאירוע - PlanMyEvents'
  },
  {
    path: 'events/:eventId/select-dishes',
    loadComponent: () =>
      import('./components/event-dish-wizard/event-dish-wizard.component')
        .then(m => m.EventDishWizardComponent),
    title: 'הוספת מנות או כלים - PlanMyEvents'
  },
  {
    path: 'products',
    loadComponent: () => 
      import('./components/products/products.component')
        .then(m => m.ProductsComponent),
    title: 'מוצרים - PlanMyEvents'
  },
  {
    path: 'tools',
    loadComponent: () => 
      import('./components/tools/tools.component')
        .then(m => m.ToolsComponent),
    title: 'כלים - PlanMyEvents'
  },
  {
    path: 'settings',
    loadComponent: () =>
      import('./components/settings/settings')
        .then(m => m.SettingsComponent),
    title: 'הגדרות - PlanMyEvents'
  },
  {
    path: 'events',
    loadComponent: () =>
      import('./components/events/events.component')
        .then(m => m.EventsComponent),
    title: 'אירועים - PlanMyEvents'
  },
  {
    path: 'menus',
    loadComponent: () =>
      import('./components/menus/menus.component')
        .then(m => m.MenusComponent),
    title: 'תפריטים - PlanMyEvents'
  },
  {
    path: 'backup',
    loadComponent: () =>
      import('./components/backup/backup.component')
        .then(m => m.BackupComponent),
    title: 'גיבוי נתונים - PlanMyEvents'
  },
  {
    path: '**',
    redirectTo: '',
    pathMatch: 'full'
  }
];
