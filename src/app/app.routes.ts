import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => 
      import('./components/dashboard/dashboard.component')
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
    path: 'products',
    loadComponent: () => 
      import('./components/products/products.component')
        .then(m => m.ProductsComponent),
    title: 'מוצרים - PlanMyEvents'
  },
  {
    path: 'cart',
    loadComponent: () => 
      import('./components/cart/cart')
        .then(m => m.CartComponent),
    title: 'עגלה - PlanMyEvents'
  },
  {
    path: '**',
    redirectTo: '',
    pathMatch: 'full'
  }
];
