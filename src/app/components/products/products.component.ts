import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, EMPTY, forkJoin, of } from 'rxjs';
import { takeUntil, map, catchError } from 'rxjs/operators';
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

const FALLBACK_INVENTORY_STATUSES = ['במלאי', 'מלאי נמוך', 'אזל'];
const FALLBACK_PRODUCT_CATEGORIES = ['מוצרי חלב', 'בשר ועוף', 'ירקות ופירות', 'תבלינים', 'יבשים', 'שמנים'];

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
    TooltipModule
  ],
  templateUrl: './products.html',
  styleUrls: ['./products.scss'],
  providers: [ConfirmationService, MessageService]
})
export class ProductsComponent implements OnInit, OnDestroy {
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

  statusOptions = [{ label: 'כל הסטטוסים', value: '' }];
  
  // For inline editing in table
  clonedProducts: { [s: string]: Product } = {};

  constructor(
    private productService: ApiProductService,
    private lookupService: ApiLookupService,
    private confirmationService: ConfirmationService,
    private messageService: MessageService
  ) {
    this.product = this.getEmptyProduct();
  }

  ngOnInit(): void {
    this.loadProducts();
    this.loadLookupData();
  }

  loadProducts(): void {
    this.productService.getProducts()
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
        })
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
        )
    })
      .pipe(takeUntil(this.destroy$))
      .subscribe(({ statuses, categories }) => {
        // Lookup service now returns string arrays directly
        const statusList = statuses.length > 0 ? statuses : FALLBACK_INVENTORY_STATUSES;
        const categoryList = categories.length > 0 ? categories : FALLBACK_PRODUCT_CATEGORIES;

        this.inventoryStatuses = statusList.map(status => ({ label: status, value: status }));
        this.categories = categoryList.map(category => ({ label: category, value: category }));
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

        this.buildInventorySummary();
      });
  }

  // Mapping function
  mapApiProductToProduct = (apiProduct: ApiProduct): Product => {
    return {
      id: apiProduct.id,
      name: apiProduct.name,
      inventoryStatus: apiProduct.inventory_status,
      brand: apiProduct.brand || '',
      packageQuantity: apiProduct.package_quantity || 0,
      estimatedPrice: apiProduct.estimated_price,
      category: apiProduct.category,
      supplier: apiProduct.supplier || ''
    };
  };

  private mapProductToCreatePayload(product: Product): ProductCreate {
    return {
      name: product.name.trim(),
      category: product.category,
      package_quantity: product.packageQuantity,
      estimated_price: product.estimatedPrice,
      inventory_status: product.inventoryStatus,
      supplier: product.supplier?.trim() || undefined,
      brand: product.brand?.trim() || undefined
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
        product.brand.toLowerCase().includes(this.searchValue.toLowerCase()) ||
        product.supplier.toLowerCase().includes(this.searchValue.toLowerCase());
      
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
        const aId = parseInt(a.id) || 0;
        const bId = parseInt(b.id) || 0;
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
        const ids = this.selectedProducts.map(product => product.id);
        const request$ = ids.length > 1
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

    const request$ = isUpdate
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
            detail: 'שמירת המוצר נכשלה',
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
    this.clonedProducts[product.id] = { ...product };
  }

  onRowEditSave(product: Product): void {
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
        delete this.clonedProducts[product.id];
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
    if (this.clonedProducts[product.id]) {
      this.filteredProducts[index] = this.clonedProducts[product.id];
    }
    delete this.clonedProducts[product.id];
  }

  getStatusSeverity(status: string): 'success' | 'warn' | 'danger' | 'info' | 'secondary' | 'contrast' | undefined {
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

  getStatusIcon(status: string): string {
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

  trackByProduct(index: number, product: Product): string {
    return product.id;
  }

  isDisposableProduct(product: Product): boolean {
    return product.category === 'חד"פ';
  }

  private getEmptyProduct(): Product {
    return {
      id: '',
      name: '',
      inventoryStatus: this.inventoryStatuses[0]?.value || FALLBACK_INVENTORY_STATUSES[0],
      brand: '',
      packageQuantity: 1,
      estimatedPrice: 0,
      category: this.categories[0]?.value || FALLBACK_PRODUCT_CATEGORIES[0] || '',
      supplier: ''
    };
  }

  private buildInventorySummary(): void {
    if (!this.inventoryStatuses.length) {
      this.inventorySummary = [];
      return;
    }

    this.inventorySummary = this.inventoryStatuses.map(option => {
      const count = this.products.filter(product => product.inventoryStatus === option.value).length;
      const severity = this.getStatusSeverity(option.value);
      return {
        value: option.value,
        label: option.label,
        count,
        severity,
        icon: this.getStatusIcon(option.value),
        badgeClass: this.getFilterBadgeClass(severity)
      };
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
}
