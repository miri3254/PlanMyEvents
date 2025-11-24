import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Observable, combineLatest } from 'rxjs';
import { map } from 'rxjs/operators';
import { EventService } from '../../core/services/event.service';
import { Product } from '../../core/models';
import { INVENTORY_STATUS } from '../../core/constants/app.constants';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { InputNumberModule } from 'primeng/inputnumber';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ToastModule } from 'primeng/toast';
import { ConfirmationService, MessageService } from 'primeng/api';
import { SelectModule } from 'primeng/select';
import { TableModule } from 'primeng/table';
import { SelectButtonModule } from 'primeng/selectbutton';

@Component({
  selector: 'app-products',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ButtonModule,
    DialogModule,
    InputTextModule,
    InputNumberModule,
    CardModule,
    TagModule,
    ConfirmDialogModule,
    ToastModule,
    SelectModule,
    TableModule,
    SelectButtonModule
  ],
  template: `
    <div class="p-6 space-y-6" dir="rtl">
      <!-- כותרת -->
      <div class="header-section">
        <div class="header-content">
          <div class="gradient-background"></div>
          <h1 class="gradient-title">ניהול מוצרים</h1>
          <p class="subtitle">מאגר מוצרים ומרכיבים למנות</p>
        </div>
        <p-button 
          label="מוצר חדש" 
          icon="pi pi-plus"
          (onClick)="handleCreateProduct()"
          styleClass="btn-gradient">
        </p-button>
      </div>

      <!-- חיפוש וסינון -->
      <p-card>
        <div class="search-filter-section">
          <div class="search-input-wrapper">
            <i class="pi pi-search search-icon"></i>
            <input 
              pInputText 
              type="text" 
              [(ngModel)]="searchQuery"
              placeholder="חיפוש מוצרים, מותגים או ספקים..."
              class="search-input" />
          </div>
          
          <p-select
            [options]="statusOptions"
            [(ngModel)]="filterStatus"
            placeholder="כל הסטטוסים"
            optionLabel="label"
            optionValue="value"
            styleClass="filter-select">
          </p-select>

          <p-selectButton 
            [options]="viewOptions" 
            [(ngModel)]="viewMode"
            optionLabel="icon"
            optionValue="value">
            <ng-template let-item>
              <i [class]="item.icon"></i>
            </ng-template>
          </p-selectButton>
        </div>
      </p-card>

      <!-- סטטיסטיקות מהירות -->
      <div class="stats-grid">
        <div class="stat-card stat-in-stock">
          <div class="stat-header">
            <div class="stat-icon-wrapper stat-icon-green">
              <i class="pi pi-check-circle"></i>
            </div>
            <span class="stat-title">במלאי</span>
          </div>
          <div class="stat-value stat-value-green">
            {{ (inventoryStats$ | async)?.inStock || 0 }}
          </div>
        </div>

        <div class="stat-card stat-low-stock">
          <div class="stat-header">
            <div class="stat-icon-wrapper stat-icon-yellow">
              <i class="pi pi-exclamation-circle"></i>
            </div>
            <span class="stat-title">מלאי נמוך</span>
          </div>
          <div class="stat-value stat-value-yellow">
            {{ (inventoryStats$ | async)?.lowStock || 0 }}
          </div>
        </div>

        <div class="stat-card stat-out-stock">
          <div class="stat-header">
            <div class="stat-icon-wrapper stat-icon-red">
              <i class="pi pi-times-circle"></i>
            </div>
            <span class="stat-title">אזל מהמלאי</span>
          </div>
          <div class="stat-value stat-value-red">
            {{ (inventoryStats$ | async)?.outOfStock || 0 }}
          </div>
        </div>
      </div>

      <!-- תצוגת טבלה -->
      <p-card *ngIf="viewMode === 'table'">
        <p-table 
          [value]="(filteredProducts$ | async) || []"
          [rows]="10"
          [paginator]="true"
          [rowsPerPageOptions]="[10, 25, 50]"
          styleClass="products-table">
          <ng-template pTemplate="header">
            <tr>
              <th>מוצר</th>
              <th>מותג</th>
              <th>ספק</th>
              <th>קטגוריה</th>
              <th>כמות באריזה</th>
              <th>מחיר משוער</th>
              <th>סטטוס</th>
              <th>פעולות</th>
            </tr>
          </ng-template>
          <ng-template pTemplate="body" let-product>
            <tr>
              <td>{{ product.name }}</td>
              <td>{{ product.brand }}</td>
              <td>{{ product.supplier }}</td>
              <td>
                <p-tag [value]="product.category" severity="secondary"></p-tag>
              </td>
              <td>{{ product.packageQuantity }}</td>
              <td>₪{{ product.estimatedPrice }}</td>
              <td>
                <span class="status-badge" [ngClass]="getStatusClass(product.inventoryStatus)">
                  <i [class]="getStatusIcon(product.inventoryStatus)"></i>
                  {{ product.inventoryStatus }}
                </span>
              </td>
              <td>
                <div class="action-buttons">
                  <p-button 
                    icon="pi pi-pencil"
                    (onClick)="handleEditProduct(product)"
                    [outlined]="true"
                    severity="secondary"
                    size="small">
                  </p-button>
                  <p-button 
                    icon="pi pi-trash"
                    (onClick)="confirmDelete(product.id)"
                    severity="danger"
                    size="small">
                  </p-button>
                </div>
              </td>
            </tr>
          </ng-template>
          <ng-template pTemplate="emptymessage">
            <tr>
              <td colspan="8" class="text-center">
                <p class="empty-message">לא נמצאו מוצרים</p>
              </td>
            </tr>
          </ng-template>
        </p-table>
      </p-card>

      <!-- תצוגת כרטיסים -->
      <div *ngIf="viewMode === 'grid'" class="grid-view">
        <div class="product-card" *ngFor="let product of filteredProducts$ | async">
          <div class="product-card-header">
            <div>
              <h3 class="product-name">{{ product.name }}</h3>
              <p class="product-brand">{{ product.brand }}</p>
            </div>
            <span class="status-badge" [ngClass]="getStatusClass(product.inventoryStatus)">
              <i [class]="getStatusIcon(product.inventoryStatus)"></i>
            </span>
          </div>
          
          <div class="product-card-body">
            <div class="product-detail">
              <span class="detail-label">ספק:</span>
              <span>{{ product.supplier }}</span>
            </div>
            <div class="product-detail">
              <span class="detail-label">קטגוריה:</span>
              <p-tag [value]="product.category" severity="secondary"></p-tag>
            </div>
            <div class="product-detail">
              <span class="detail-label">כמות באריזה:</span>
              <span>{{ product.packageQuantity }}</span>
            </div>
            <div class="product-detail">
              <span class="detail-label">מחיר:</span>
              <span>₪{{ product.estimatedPrice }}</span>
            </div>
          </div>

          <div class="product-card-footer">
            <p-button 
              label="ערוך"
              icon="pi pi-pencil"
              (onClick)="handleEditProduct(product)"
              [outlined]="true"
              styleClass="flex-1">
            </p-button>
            <p-button 
              icon="pi pi-trash"
              (onClick)="confirmDelete(product.id)"
              severity="danger">
            </p-button>
          </div>
        </div>

        <p-card *ngIf="(filteredProducts$ | async)?.length === 0" styleClass="col-span-full">
          <p class="empty-message">לא נמצאו מוצרים</p>
        </p-card>
      </div>

      <!-- דיאלוג עריכת מוצר -->
      <p-dialog 
        [(visible)]="isDialogOpen" 
        [modal]="true"
        [rtl]="true"
        [style]="{width: '600px'}"
        [header]="editingProduct?.name ? 'עריכת ' + editingProduct?.name : 'מוצר חדש'">
        
        <div class="dialog-content" *ngIf="editingProduct">
          <div class="form-grid">
            <div class="form-field">
              <label for="name">שם המוצר *</label>
              <input 
                id="name"
                pInputText 
                [(ngModel)]="editingProduct.name"
                placeholder="הזן שם מוצר"
                class="w-full" />
            </div>

            <div class="form-field">
              <label for="brand">מותג</label>
              <input 
                id="brand"
                pInputText 
                [(ngModel)]="editingProduct.brand"
                placeholder="שם המותג"
                class="w-full" />
            </div>

            <div class="form-field">
              <label for="supplier">ספק</label>
              <input 
                id="supplier"
                pInputText 
                [(ngModel)]="editingProduct.supplier"
                placeholder="שם הספק"
                class="w-full" />
            </div>

            <div class="form-field">
              <label for="category">קטגוריה</label>
              <input 
                id="category"
                pInputText 
                [(ngModel)]="editingProduct.category"
                placeholder="קטגוריה"
                class="w-full" />
            </div>

            <div class="form-field">
              <label for="packageQty">כמות באריזה</label>
              <p-inputnumber 
                id="packageQty"
                [(ngModel)]="editingProduct.packageQuantity"
                [min]="0.1"
                [step]="0.1"
                class="w-full">
              </p-inputnumber>
            </div>

            <div class="form-field">
              <label for="price">מחיר משוער (₪)</label>
              <p-inputnumber 
                id="price"
                [(ngModel)]="editingProduct.estimatedPrice"
                [min]="0"
                [step]="1"
                mode="currency"
                currency="ILS"
                locale="he-IL"
                class="w-full">
              </p-inputnumber>
            </div>

            <div class="form-field full-width">
              <label for="status">סטטוס מלאי</label>
              <p-select
                id="status"
                [options]="inventoryStatusOptions"
                [(ngModel)]="editingProduct.inventoryStatus"
                placeholder="בחר סטטוס"
                optionLabel="label"
                optionValue="value"
                class="w-full">
              </p-select>
            </div>
          </div>
        </div>

        <ng-template pTemplate="footer">
          <div class="dialog-footer">
            <p-button 
              label="ביטול"
              (onClick)="isDialogOpen = false"
              [outlined]="true"
              severity="secondary">
            </p-button>
            <p-button 
              label="שמור מוצר"
              icon="pi pi-check"
              (onClick)="handleSaveProduct()">
            </p-button>
          </div>
        </ng-template>
      </p-dialog>

      <!-- Toast Messages -->
      <p-toast position="top-center"></p-toast>

      <!-- Confirm Dialog -->
      <p-confirmDialog></p-confirmDialog>
    </div>
  `,
  styles: [`
    .p-6 { padding: 1.5rem; }
    .space-y-6 > * + * { margin-top: 1.5rem; }

    /* Header Section */
    .header-section {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      flex-wrap: wrap;
    }

    .header-content {
      position: relative;
    }

    .gradient-background {
      position: absolute;
      inset: 0;
      background: linear-gradient(to right, rgba(255, 115, 45, 0.1), rgba(255, 115, 45, 0.05), transparent);
      border-radius: 1rem;
      filter: blur(3rem);
      z-index: -1;
    }

    .gradient-title {
      margin: 0 0 0.5rem 0;
      background: linear-gradient(to right, var(--primary), var(--primary-dark));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      font-size: 2rem;
      font-weight: 700;
    }

    .subtitle {
      color: var(--muted-foreground);
      margin: 0;
    }

    .btn-gradient {
      background: linear-gradient(135deg, var(--primary), var(--primary-dark)) !important;
      border: none !important;
      box-shadow: var(--shadow-glow) !important;
    }

    /* Search & Filter */
    .search-filter-section {
      display: flex;
      gap: 1rem;
      flex-wrap: wrap;
    }

    .search-input-wrapper {
      flex: 1;
      position: relative;
      min-width: 200px;
    }

    .search-icon {
      position: absolute;
      right: 12px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--muted-foreground);
    }

    .search-input {
      width: 100%;
      padding-right: 40px !important;
    }

    .filter-select {
      min-width: 180px;
    }

    /* Stats Grid */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 1rem;
    }

    .stat-card {
      padding: 1.5rem;
      border-radius: 12px;
      border: 2px solid;
      transition: all 0.3s ease;
    }

    .stat-card:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-hover);
    }

    .stat-in-stock {
      background: linear-gradient(to bottom right, white, rgba(34, 197, 94, 0.05));
      border-color: rgba(34, 197, 94, 0.2);
    }

    .stat-low-stock {
      background: linear-gradient(to bottom right, white, rgba(234, 179, 8, 0.05));
      border-color: rgba(234, 179, 8, 0.2);
    }

    .stat-out-stock {
      background: linear-gradient(to bottom right, white, rgba(239, 68, 68, 0.05));
      border-color: rgba(239, 68, 68, 0.2);
    }

    .stat-header {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 0.75rem;
    }

    .stat-icon-wrapper {
      padding: 0.375rem;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .stat-icon-wrapper i {
      color: white;
      font-size: 1rem;
    }

    .stat-icon-green {
      background: linear-gradient(to bottom right, #22c55e, #16a34a);
    }

    .stat-icon-yellow {
      background: linear-gradient(to bottom right, #eab308, #ca8a04);
    }

    .stat-icon-red {
      background: linear-gradient(to bottom right, #ef4444, #dc2626);
    }

    .stat-title {
      font-size: 0.875rem;
      font-weight: 500;
    }

    .stat-value {
      font-size: 2rem;
      font-weight: 700;
      background: linear-gradient(to right, currentColor, currentColor);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .stat-value-green { color: #22c55e; }
    .stat-value-yellow { color: #eab308; }
    .stat-value-red { color: #ef4444; }

    /* Status Badges */
    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.375rem;
      padding: 0.25rem 0.75rem;
      border-radius: 6px;
      font-size: 0.875rem;
      font-weight: 500;
      border: 1px solid;
    }

    .status-in-stock {
      background: rgba(34, 197, 94, 0.1);
      color: #16a34a;
      border-color: rgba(34, 197, 94, 0.3);
    }

    .status-low-stock {
      background: rgba(234, 179, 8, 0.1);
      color: #ca8a04;
      border-color: rgba(234, 179, 8, 0.3);
    }

    .status-out-stock {
      background: rgba(239, 68, 68, 0.1);
      color: #dc2626;
      border-color: rgba(239, 68, 68, 0.3);
    }

    /* Table */
    .products-table {
      font-family: inherit;
    }

    .action-buttons {
      display: flex;
      gap: 0.5rem;
    }

    .empty-message {
      padding: 3rem;
      text-align: center;
      color: var(--muted-foreground);
    }

    /* Grid View */
    .grid-view {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 1rem;
    }

    .product-card {
      background: white;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.5rem;
      transition: all 0.3s ease;
    }

    .product-card:hover {
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    }

    .product-card-header {
      display: flex;
      justify-content: space-between;
      align-items: start;
      margin-bottom: 1rem;
    }

    .product-name {
      font-size: 1rem;
      font-weight: 600;
      margin: 0 0 0.25rem 0;
    }

    .product-brand {
      color: var(--muted-foreground);
      font-size: 0.875rem;
      margin: 0;
    }

    .product-card-body {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      margin-bottom: 1rem;
    }

    .product-detail {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.875rem;
    }

    .detail-label {
      color: var(--muted-foreground);
    }

    .product-card-footer {
      display: flex;
      gap: 0.5rem;
      padding-top: 0.75rem;
      border-top: 1px solid var(--border);
    }

    .flex-1 {
      flex: 1;
    }

    /* Dialog */
    .dialog-content {
      padding: 1rem 0;
    }

    .form-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 1rem;
    }

    .form-field {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .form-field label {
      font-weight: 600;
      font-size: 0.9rem;
    }

    .full-width {
      grid-column: 1 / -1;
    }

    .w-full {
      width: 100%;
    }

    .dialog-footer {
      display: flex;
      justify-content: flex-end;
      gap: 0.75rem;
    }

    .col-span-full {
      grid-column: 1 / -1;
    }

    .text-center {
      text-align: center;
    }

    @media (max-width: 768px) {
      .form-grid {
        grid-template-columns: 1fr;
      }

      .search-filter-section {
        flex-direction: column;
      }

      .search-input-wrapper {
        width: 100%;
      }
    }
  `],
  providers: [ConfirmationService, MessageService]
})
export class ProductsComponent implements OnInit {
  products$!: Observable<Product[]>;
  filteredProducts$!: Observable<Product[]>;
  inventoryStats$!: Observable<any>;

  viewMode: 'table' | 'grid' = 'table';
  searchQuery: string = '';
  filterStatus: string = 'הכל';
  editingProduct: Product | null = null;
  isDialogOpen: boolean = false;

  viewOptions = [
    { icon: 'pi pi-list', value: 'table' },
    { icon: 'pi pi-th-large', value: 'grid' }
  ];

  statusOptions = [
    { label: 'כל הסטטוסים', value: 'הכל' },
    ...INVENTORY_STATUS.map(status => ({ label: status, value: status }))
  ];

  inventoryStatusOptions = INVENTORY_STATUS.map(status => ({ 
    label: status, 
    value: status 
  }));

  constructor(
    private eventService: EventService,
    private confirmationService: ConfirmationService,
    private messageService: MessageService
  ) {}

  ngOnInit(): void {
    this.products$ = this.eventService.products$;
    
    // Filter products based on search and status
    this.filteredProducts$ = combineLatest([
      this.products$,
      // Create observables for search and filter that emit when they change
    ]).pipe(
      map(([products]) => {
        return products.filter(product => {
          const matchSearch = 
            product.name.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
            product.brand.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
            product.supplier.toLowerCase().includes(this.searchQuery.toLowerCase());
          
          const matchStatus = 
            this.filterStatus === 'הכל' || 
            product.inventoryStatus === this.filterStatus;
          
          return matchSearch && matchStatus;
        });
      })
    );

    // Calculate inventory statistics
    this.inventoryStats$ = this.products$.pipe(
      map(products => ({
        inStock: products.filter(p => p.inventoryStatus === 'במלאי').length,
        lowStock: products.filter(p => p.inventoryStatus === 'מלאי-נמוך').length,
        outOfStock: products.filter(p => p.inventoryStatus === 'אזל').length,
        total: products.length
      }))
    );

    // Trigger filtering when search or filter changes
    this.setupReactiveFiltering();
  }

  setupReactiveFiltering(): void {
    // Re-trigger the filtered products whenever search or filter changes
    const originalNgDoCheck = this.ngDoCheck?.bind(this);
    this.ngDoCheck = () => {
      if (originalNgDoCheck) originalNgDoCheck();
      // Force recalculation of filtered products
      this.filteredProducts$ = combineLatest([this.products$]).pipe(
        map(([products]) => {
          return products.filter(product => {
            const matchSearch = 
              product.name.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
              product.brand.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
              product.supplier.toLowerCase().includes(this.searchQuery.toLowerCase());
            
            const matchStatus = 
              this.filterStatus === 'הכל' || 
              product.inventoryStatus === this.filterStatus;
            
            return matchSearch && matchStatus;
          });
        })
      );
    };
  }

  ngDoCheck(): void {
    // This will be overridden in setupReactiveFiltering
  }

  handleCreateProduct(): void {
    this.editingProduct = {
      id: Date.now().toString(),
      name: '',
      inventoryStatus: 'במלאי',
      brand: '',
      packageQuantity: 1,
      estimatedPrice: 0,
      category: '',
      supplier: ''
    };
    this.isDialogOpen = true;
  }

  handleEditProduct(product: Product): void {
    this.editingProduct = { ...product };
    this.isDialogOpen = true;
  }

  handleSaveProduct(): void {
    if (!this.editingProduct) return;
    
    if (!this.editingProduct.name.trim()) {
      this.messageService.add({
        severity: 'error',
        summary: 'שגיאה',
        detail: 'יש להזין שם מוצר'
      });
      return;
    }

    this.eventService.saveProduct(this.editingProduct);
    this.messageService.add({
      severity: 'success',
      summary: 'הצלחה',
      detail: 'המוצר נשמר בהצלחה'
    });
    this.isDialogOpen = false;
    this.editingProduct = null;
  }

  confirmDelete(id: string): void {
    this.confirmationService.confirm({
      message: 'האם למחוק מוצר זה? פעולה זו לא ניתנת לביטול.',
      header: 'אישור מחיקה',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'מחק',
      rejectLabel: 'ביטול',
      accept: () => {
        this.handleDeleteProduct(id);
      }
    });
  }

  handleDeleteProduct(id: string): void {
    this.eventService.deleteProduct(id);
    this.messageService.add({
      severity: 'success',
      summary: 'הצלחה',
      detail: 'המוצר נמחק'
    });
  }

  getStatusClass(status: string): string {
    switch (status) {
      case 'במלאי': return 'status-in-stock';
      case 'מלאי-נמוך': return 'status-low-stock';
      case 'אזל': return 'status-out-stock';
      default: return '';
    }
  }

  getStatusIcon(status: string): string {
    switch (status) {
      case 'במלאי': return 'pi pi-check-circle';
      case 'מלאי-נמוך': return 'pi pi-exclamation-circle';
      case 'אזל': return 'pi pi-times-circle';
      default: return '';
    }
  }
}
