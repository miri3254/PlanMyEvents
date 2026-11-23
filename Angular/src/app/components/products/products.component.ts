import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ExcelExportService } from '../../services/excel-export.service';
import { Subject, EMPTY, forkJoin, of, Observable } from 'rxjs';
import { takeUntil, map, catchError, finalize } from 'rxjs/operators';
import { LoadingOverlayComponent } from '../../shared/loading-overlay/loading-overlay.component';
import { ApiProductService } from '../../services/api-product.service';
import { ApiLookupService } from '../../services/api-lookup.service';
import { Product } from '../../core/models';
import { ApiProduct, ProductCreate, ProductUpdate, LookupValue } from '../../core/models/api.models';
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
import { CheckboxModule } from 'primeng/checkbox';
import { DividerModule } from 'primeng/divider';
import { TooltipModule } from 'primeng/tooltip';
import { TabsModule } from 'primeng/tabs';

const FALLBACK_INVENTORY_STATUSES = ['במלאי', 'מלאי נמוך', 'אין במלאי'];
const FALLBACK_PRODUCT_CATEGORIES = ['מוצרי חלב', 'מוצרי בשר', 'קטניות', 'שתיה', 'נוזלים', 'מוצרים יבשים', 'קפואים'];

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
    SelectButtonModule,
    CheckboxModule,
    DividerModule,
    TooltipModule,
    TabsModule,
    LoadingOverlayComponent
  ],
  templateUrl: './products.html',
  styleUrls: ['./products.scss'],
  providers: [ConfirmationService, MessageService]
})
export class ProductsComponent implements OnInit, OnDestroy {
  readonly drinkTypes = [
    { label: 'אינו מוצר שתייה לחישוב אירוע', value: null },
    { label: 'פפסי', value: 'pepsi' },
    { label: 'פפסי מקס', value: 'pepsi_max' },
    { label: 'מיץ — כל הטעמים במלאי משותף', value: 'orange_flavored' },
    { label: 'מים', value: 'water' },
    { label: 'סודה', value: 'soda' },
  ];

  onDrinkTypeChange(): void {
    if (this.product.drinkType) {
      this.product.unit = 'יחידות';
      this.product.category = 'שתיה';
      if (!this.product.name?.trim()) {
        this.product.name = this.product.drinkType === 'orange_flavored' ? 'מיץ'
          : this.drinkTypes.find(t => t.value === this.product.drinkType)?.label || '';
      }
    }
  }
  // Data properties
  products: Product[] = [];
  filteredProducts: Product[] = [];
  selectedProducts: Product[] = [];

  private readonly destroy$ = new Subject<void>();
  
  // UI state
  viewMode: 'table' | 'grid' = 'table';
  searchValue: string = '';
  filterInventoryStatus: string = '';
  productDialog: boolean = false;
  submitted: boolean = false;
  isLoading = true;
  
  // Sorting state
  sortField: string = '';
  sortOrder: 'asc' | 'desc' | '' = '';
  
  // Current product being edited/created
  product!: Product;
  
  inventorySummary: Array<{
    value: string;
    label: string;
    count: number;
    severity: 'success' | 'warn' | 'danger' | 'info' | 'secondary' | 'contrast' | undefined;
    icon: string;
    badgeClass: string;
  }> = [];
  
  // Dropdown options
  inventoryStatuses: { label: string; value: string }[] = [];

  categories: { label: string; value: string }[] = [];

  measurementUnits: { label: string; value: string }[] = [];

  statusOptions = [{ label: 'כל הסטטוסים', value: '' }];
  
  // For inline editing in table
  clonedProducts: { [s: string]: Product } = {};

  constructor(
    private productService: ApiProductService,
    private lookupService: ApiLookupService,
    private confirmationService: ConfirmationService,
    private messageService: MessageService,
    private excelExportService: ExcelExportService
  ) {
    this.product = this.getEmptyProduct();
  }

  ngOnInit(): void {
    this.loadProducts();
    this.loadLookupData();
  }

  loadProducts(): void {
    this.isLoading = true;
    this.productService.getProducts({ limit: 200 })
      .pipe(
        takeUntil(this.destroy$),
        map(response => response.items.map(this.mapApiProductToProduct)),
        catchError(error => {
          console.error('Error loading products:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'שגיאה',
            detail: 'טעינת המוצרים נכשלה'
          });
          return EMPTY;
        }),
        finalize(() => this.isLoading = false)
      )
      .subscribe(products => {
        this.products = products;
        this.applyFilters();
        this.buildInventorySummary();
      });
  }

  loadLookupData(): void {
    forkJoin({
      statuses: this.lookupService
        .getLookupCategory('inventory_statuses')
        .pipe(
          catchError(error => {
            console.warn('Failed to load inventory statuses:', error);
            return of<string[]>([]);
          })
        ),
      categories: this.lookupService
        .getLookupCategory('product_categories')
        .pipe(
          catchError(error => {
            console.warn('Failed to load product categories:', error);
            return of<string[]>([]);
          })
        ),
      units: this.lookupService
        .getLookupCategory('measurement_units')
        .pipe(
          catchError(error => {
            console.warn('Failed to load measurement units:', error);
            return of<string[]>([]);
          })
        )
    })
      .pipe(takeUntil(this.destroy$))
      .subscribe(({ statuses, categories, units }) => {
        // Lookup service now returns string arrays directly
        const statusList = statuses.length > 0 ? statuses : FALLBACK_INVENTORY_STATUSES;
        const categoryList = categories.length > 0 ? categories : FALLBACK_PRODUCT_CATEGORIES;
        const unitList = units.length > 0 ? units : ['יחידות', 'ק״ג', 'ליטר', 'גרם', 'אגדים'];

        this.inventoryStatuses = statusList.map(status => ({ label: status, value: status }));
        this.categories = categoryList.map(category => ({ label: category, value: category }));
        this.measurementUnits = unitList.map(unit => ({ label: unit, value: unit }));
        this.statusOptions = [{ label: 'כל הסטטוסים', value: '' }, ...this.inventoryStatuses];

        if (this.filterInventoryStatus && !statusList.includes(this.filterInventoryStatus)) {
          this.filterInventoryStatus = '';
          this.applyFilters();
        }

        if (this.productDialog && this.product.category && !categoryList.includes(this.product.category)) {
          this.product.category = categoryList[0] || '';
        }

        if (!this.product.inventoryStatus && statusList.length) {
          this.product.inventoryStatus = statusList[0];
        }

        if (!this.product.category && categoryList.length) {
          this.product.category = categoryList[0];
        }

        if (!this.product.unit && unitList.length) {
          this.product.unit = unitList[0];
        }

        this.buildInventorySummary();
      });
  }

  // Mapping function
  mapApiProductToProduct = (apiProduct: ApiProduct): Product => {
    return {
      id: apiProduct.id,
      name: apiProduct.name,
      drinkType: apiProduct.drink_type,
      category: apiProduct.category,
      unit: apiProduct.unit || 'יחידות',
      packageQuantity: apiProduct.package_quantity,
      estimatedPrice: apiProduct.estimated_price,
      inventoryStatus: apiProduct.inventory_status || 'במלאי',
      supplier: apiProduct.supplier,
      brand: apiProduct.brand,
      kosherType: apiProduct.kosher_type,
      quantityInStock: apiProduct.quantity_in_stock,
      minStockLevel: apiProduct.min_stock_level,
      pricePerUnit: apiProduct.price_per_unit,
      barcode: apiProduct.barcode,
      notes: apiProduct.notes,
      description: apiProduct.description
    };
  };

  private mapProductToCreatePayload(product: Product): ProductCreate {
    return {
      name: product.name.trim(),
      drink_type: product.drinkType ?? null,
      category: product.category,
      unit: product.unit || 'יחידות',
      package_quantity: product.packageQuantity,
      estimated_price: product.estimatedPrice,
      supplier: product.supplier?.trim() || undefined,
      brand: product.brand?.trim() || undefined,
      kosher_type: product.kosherType,
      quantity_in_stock: product.quantityInStock,
      min_stock_level: product.minStockLevel,
      price_per_unit: product.pricePerUnit,
      barcode: product.barcode?.trim() || undefined,
      notes: product.notes?.trim() || undefined,
      description: product.description?.trim() || undefined
    };
  }

  private mapProductToUpdatePayload(product: Product): ProductUpdate {
    return this.mapProductToCreatePayload(product);
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  setViewMode(mode: 'table' | 'grid'): void {
    this.viewMode = mode;
  }

  applyFilters(): void {
    // First, filter the products
    this.filteredProducts = this.products.filter(product => {
      const matchesSearch = !this.searchValue || 
        product.name.toLowerCase().includes(this.searchValue.toLowerCase()) ||
        product.brand?.toLowerCase().includes(this.searchValue.toLowerCase()) ||
        product.supplier?.toLowerCase().includes(this.searchValue.toLowerCase());
      
      const matchesStatus = !this.filterInventoryStatus || 
        product.inventoryStatus === this.filterInventoryStatus;
      
      return matchesSearch && matchesStatus;
    });

    // Then apply sorting if a sort field is set
    if (this.sortField && this.sortOrder) {
      this.filteredProducts.sort((a, b) => {
        let aValue = (a as any)[this.sortField];
        let bValue = (b as any)[this.sortField];

        // Handle string comparisons
        if (typeof aValue === 'string') {
          aValue = aValue.toLowerCase();
          bValue = bValue.toLowerCase();
        }

        let result = 0;
        if (aValue < bValue) {
          result = -1;
        } else if (aValue > bValue) {
          result = 1;
        }

        return this.sortOrder === 'asc' ? result : -result;
      });
    } else {
      // If no sorting, show newest first (by id which is timestamp)
      this.filteredProducts.sort((a, b) => {
        const aId = a.id || 0;
        const bId = b.id || 0;
        return bId - aId; // Descending order (newest first)
      });
    }
  }

  onSearch(): void {
    this.applyFilters();
  }

  clearSearch(): void {
    this.searchValue = '';
    this.applyFilters();
  }

  filterByInventoryStatus(status: string): void {
    this.filterInventoryStatus = status;
    this.applyFilters();
  }

  clearFilters(): void {
    this.searchValue = '';
    this.filterInventoryStatus = '';
    this.applyFilters();
  }

  toggleView(): void {
    this.viewMode = this.viewMode === 'table' ? 'grid' : 'table';
  }

  openNew(): void {
    this.product = this.getEmptyProduct();
    this.submitted = false;
    this.productDialog = true;
  }

  editProduct(product: Product): void {
    this.product = { ...product };
    this.productDialog = true;
  }

  deleteProduct(product: Product): void {
    this.confirmationService.confirm({
      message: `האם אתה בטוח שברצונך למחוק את ${product.name}?`,
      header: 'אישור מחיקה',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'כן',
      rejectLabel: 'לא',
      accept: () => {
        if (!product.id) return;
        this.productService.deleteProduct(product.id)
          .pipe(
            takeUntil(this.destroy$),
            catchError(error => {
              console.error('Error deleting product:', error);
              this.messageService.add({
                severity: 'error',
                summary: 'שגיאה',
                detail: 'מחיקת המוצר נכשלה',
                life: 3000
              });
              return EMPTY;
            })
          )
          .subscribe(() => {
            this.messageService.add({
              severity: 'success',
              summary: 'הצלחה',
              detail: 'המוצר נמחק בהצלחה',
              life: 3000
            });
            this.loadProducts();
          });
      }
    });
  }

  deleteSelectedProducts(): void {
    if (!this.selectedProducts.length) {
      return;
    }

    this.confirmationService.confirm({
      message: `האם אתה בטוח שברצונך למחוק ${this.selectedProducts.length} מוצרים?`,
      header: 'אישור מחיקה',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'כן',
      rejectLabel: 'לא',
      accept: () => {
        const ids = this.selectedProducts.map(product => product.id).filter((id): id is number => id !== undefined);
        if (ids.length === 0) return;
        const request$: Observable<unknown> = ids.length > 1
          ? this.productService.deleteMultipleProducts(ids)
          : this.productService.deleteProduct(ids[0]);

        request$
          .pipe(
            takeUntil(this.destroy$),
            catchError(error => {
              console.error('Error deleting products:', error);
              this.messageService.add({
                severity: 'error',
                summary: 'שגיאה',
                detail: 'מחיקת המוצרים נכשלה',
                life: 3000
              });
              return EMPTY;
            })
          )
          .subscribe(() => {
            this.selectedProducts = [];
            this.messageService.add({
              severity: 'success',
              summary: 'הצלחה',
              detail: 'המוצרים נמחקו בהצלחה',
              life: 3000
            });
            this.loadProducts();
          });
      }
    });
  }

  hideDialog(): void {
    this.productDialog = false;
    this.submitted = false;
  }

  saveProduct(): void {
    this.submitted = true;

    if (!this.product.name?.trim()) {
      return;
    }

    this.product.inventoryStatus = this.product.inventoryStatus || this.inventoryStatuses[0]?.value || FALLBACK_INVENTORY_STATUSES[0];
    this.product.category = this.product.category || this.categories[0]?.value || FALLBACK_PRODUCT_CATEGORIES[0] || '';

   

    const isUpdate = !!this.product.id;
    const payload = isUpdate
      ? this.mapProductToUpdatePayload(this.product)
      : this.mapProductToCreatePayload(this.product);

    const request$ = isUpdate && this.product.id
      ? this.productService.updateProduct(this.product.id, payload as ProductUpdate)
      : this.productService.createProduct(payload as ProductCreate);

    request$
      .pipe(
        takeUntil(this.destroy$),
        catchError(error => {
          console.error('Error saving product:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'שגיאה',
            detail: typeof error?.error?.detail === 'string' ? error.error.detail : 'שמירת המוצר נכשלה',
            life: 3000
          });
          return EMPTY;
        })
      )
      .subscribe(() => {
        this.messageService.add({
          severity: 'success',
          summary: 'הצלחה',
          detail: isUpdate ? 'המוצר עודכן בהצלחה' : 'המוצר נוצר בהצלחה',
          life: 3000
        });
        this.productDialog = false;
        this.product = this.getEmptyProduct();
        this.loadProducts();
      });
  }

  sortBy(field: string): void {
    if (this.sortField === field) {
      // Toggle sort order
      if (this.sortOrder === 'asc') {
        this.sortOrder = 'desc';
      } else if (this.sortOrder === 'desc') {
        this.sortOrder = '';
        this.sortField = '';
      } else {
        this.sortOrder = 'asc';
      }
    } else {
      this.sortField = field;
      this.sortOrder = 'asc';
    }
    
    this.applyFilters();
  }

  getSortIcon(field: string): string {
    if (this.sortField !== field) {
      return 'pi pi-sort-alt';
    }
    return this.sortOrder === 'asc' ? 'pi pi-sort-amount-up' : 'pi pi-sort-amount-down';
  }

  onSelectAllChange(event: any): void {
    if (event.checked) {
      this.selectedProducts = [...this.filteredProducts];
    } else {
      this.selectedProducts = [];
    }
  }

  // Inline editing methods for table
  onRowEditInit(product: Product): void {
    if (product.id) {
      this.clonedProducts[product.id] = { ...product };
    }
  }

  onRowEditSave(product: Product): void {
    if (!product.id) return;
    const payload = this.mapProductToUpdatePayload(product);

    this.productService.updateProduct(product.id, payload)
      .pipe(
        takeUntil(this.destroy$),
        catchError(error => {
          console.error('Error updating product:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'שגיאה',
            detail: 'עדכון המוצר נכשל',
            life: 3000
          });
          const idx = this.filteredProducts.findIndex(item => item.id === product.id);
          if (idx > -1) {
            this.onRowEditCancel(product, idx);
          }
          return EMPTY;
        })
      )
      .subscribe(() => {
        if (product.id) {
          delete this.clonedProducts[product.id];
        }
        this.messageService.add({
          severity: 'success',
          summary: 'הצלחה',
          detail: 'המוצר עודכן בהצלחה',
          life: 3000
        });
        this.loadProducts();
      });
  }

  onRowEditCancel(product: Product, index: number): void {
    if (product.id && this.clonedProducts[product.id]) {
      this.filteredProducts[index] = this.clonedProducts[product.id];
    }
    if (product.id) {
      delete this.clonedProducts[product.id];
    }
  }

  getStatusSeverity(status: string | null | undefined): 'success' | 'warn' | 'danger' | 'info' | 'secondary' | 'contrast' | undefined {
    if (!status) {
      return 'info';
    }
    const normalized = status.toLowerCase();
    if (normalized.includes('אזל') || normalized.includes('חסר') || normalized.includes('empty') || normalized.includes('out')) {
      return 'danger';
    }
    if (normalized.includes('נמוך') || normalized.includes('קריטי') || normalized.includes('low')) {
      return 'warn';
    }
    if (normalized.includes('במלאי') || normalized.includes('available') || normalized.includes('stock')) {
      return 'success';
    }
    return 'info';
  }

  getStatusIcon(status: string | undefined): string {
    if (!status) return 'pi pi-info-circle';
    const normalized = status.toLowerCase();
    if (normalized.includes('אזל') || normalized.includes('חסר') || normalized.includes('empty') || normalized.includes('out')) {
      return 'pi pi-times-circle';
    }
    if (normalized.includes('נמוך') || normalized.includes('קריטי') || normalized.includes('low')) {
      return 'pi pi-exclamation-circle';
    }
    if (normalized.includes('במלאי') || normalized.includes('available') || normalized.includes('stock')) {
      return 'pi pi-check-circle';
    }
    return 'pi pi-info-circle';
  }

  trackByProduct(index: number, product: Product): number {
    return product.id ?? index;
  }

  isDisposableProduct(product: Product): boolean {
    return product.category === 'חד"פ';
  }

  getComputedInventoryStatus(product: Product): string {
    const qty = product.quantityInStock ?? 0;
    const minLevel = product.minStockLevel ?? 0;
    if (qty <= 0) {
      return 'אזל';
    }
    if (qty <= minLevel) {
      return 'מלאי נמוך';
    }
    return 'במלאי';
  }

  private getEmptyProduct(): Product {
    return {
      id: 0,
      name: '',
      inventoryStatus: 'במלאי',
      brand: '',
      packageQuantity: 1,
      estimatedPrice: 0,
      category: this.categories[0]?.value || FALLBACK_PRODUCT_CATEGORIES[0] || '',
      supplier: '',
      unit: 'יחידות',
      quantityInStock: 0,
      minStockLevel: 0,
      pricePerUnit: 0
    };
  }

  private buildInventorySummary(): void {
    // Build summary from actual product statuses, not from lookup values
    const statusCounts = new Map<string, number>();
    
    this.products.forEach(product => {
      const status = product.inventoryStatus || 'לא מוגדר';
      statusCounts.set(status, (statusCounts.get(status) || 0) + 1);
    });

    this.inventorySummary = Array.from(statusCounts.entries()).map(([status, count]) => {
      const severity = this.getStatusSeverity(status);
      return {
        value: status,
        label: status,
        count,
        severity,
        icon: this.getStatusIcon(status),
        badgeClass: this.getFilterBadgeClass(severity)
      };
    });
    
    // Sort by severity: danger first, then warn, then success
    const severityOrder = { danger: 0, warn: 1, success: 2, info: 3, secondary: 4, contrast: 5 };
    this.inventorySummary.sort((a, b) => {
      const orderA = severityOrder[a.severity || 'info'] ?? 6;
      const orderB = severityOrder[b.severity || 'info'] ?? 6;
      return orderA - orderB;
    });
  }

  private getFilterBadgeClass(
    severity: 'success' | 'warn' | 'danger' | 'info' | 'secondary' | 'contrast' | undefined
  ): string {
    switch (severity) {
      case 'success':
        return 'filter-stat-success';
      case 'warn':
        return 'filter-stat-warning';
      case 'danger':
        return 'filter-stat-danger';
      default:
        return 'filter-stat-neutral';
    }
  }

  exportShortages(): void {
    const isShortage = (p: Product) =>
      (p.minStockLevel ?? 0) > 0 && (p.quantityInStock ?? 0) < (p.minStockLevel ?? 0);

    const headers = ['שם מוצר', 'כמות במלאי', 'כמות מינימום'];

    const productShortages = this.products
      .filter(p => p.category !== 'חד"פ' && isShortage(p))
      .map(p => [p.name, p.quantityInStock ?? 0, p.minStockLevel ?? 0]);

    const equipmentShortages = this.products
      .filter(p => p.category === 'חד"פ' && isShortage(p))
      .map(p => [p.name, p.quantityInStock ?? 0, p.minStockLevel ?? 0]);

    this.excelExportService.exportSheets(
      [
        { name: 'חוסרי מוצרים', headers, rows: productShortages },
        { name: 'חוסרי כלים',   headers, rows: equipmentShortages }
      ],
      `חוסרי_מוצרים_${this.excelExportService.todayString()}.xlsx`
    );

    this.messageService.add({
      severity: 'success',
      summary: 'יצוא הצליח',
      detail: `הקובץ הורד בהצלחה (${productShortages.length} מוצרים, ${equipmentShortages.length} כלים)`,
      life: 4000
    });
  }
}
