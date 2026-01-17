import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { EventService } from '../../services/event.service';
import { LookupService } from '../../core/services/lookup.service';
import { Product } from '../../core/models';
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
    private eventService: EventService,
    private confirmationService: ConfirmationService,
    private messageService: MessageService,
    private lookupService: LookupService
  ) {
    this.product = this.getEmptyProduct();
  }

  ngOnInit(): void {
    this.subscribeToProducts();
    this.lookupService.lookup$
      .pipe(takeUntil(this.destroy$))
      .subscribe(data => {
        this.inventoryStatuses = data.inventoryStatuses.map(status => ({
          label: status,
          value: status
        }));

        this.categories = data.productCategories.map(category => ({
          label: category,
          value: category
        }));

        this.statusOptions = [
          { label: 'כל הסטטוסים', value: '' },
          ...data.inventoryStatuses.map(status => ({ label: status, value: status }))
        ];

        if (
          this.filterInventoryStatus &&
          !data.inventoryStatuses.includes(this.filterInventoryStatus)
        ) {
          this.filterInventoryStatus = '';
          this.applyFilters();
        }

        if (
          this.productDialog &&
          this.product.category &&
          data.productCategories.length &&
          !data.productCategories.includes(this.product.category)
        ) {
          this.product.category = data.productCategories[0];
        }

        this.updateInventorySummary();
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private subscribeToProducts(): void {
    this.eventService.products$
      .pipe(takeUntil(this.destroy$))
      .subscribe(products => {
        this.products = products;
        this.applyFilters();
        this.updateInventorySummary();
      });
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
        this.eventService.deleteProduct(product.id);
        this.messageService.add({
          severity: 'success',
          summary: 'הצלחה',
          detail: 'המוצר נמחק בהצלחה',
          life: 3000
        });
      }
    });
  }

  deleteSelectedProducts(): void {
    this.confirmationService.confirm({
      message: `האם אתה בטוח שברצונך למחוק ${this.selectedProducts.length} מוצרים?`,
      header: 'אישור מחיקה',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'כן',
      rejectLabel: 'לא',
      accept: () => {
        this.selectedProducts.forEach(product => {
          this.eventService.deleteProduct(product.id);
        });
        this.selectedProducts = [];
        this.messageService.add({
          severity: 'success',
          summary: 'הצלחה',
          detail: 'המוצרים נמחקו בהצלחה',
          life: 3000
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

    // If it's a new product (no id), generate id and add timestamp
    if (!this.product.id) {
      this.product.id = Date.now().toString();
    }

    this.eventService.saveProduct(this.product);
    this.messageService.add({
      severity: 'success',
      summary: 'הצלחה',
      detail: 'המוצר נשמר בהצלחה',
      life: 3000
    });

    this.productDialog = false;
    this.product = this.getEmptyProduct();
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
    delete this.clonedProducts[product.id];
    this.eventService.saveProduct(product);
    this.messageService.add({
      severity: 'success',
      summary: 'הצלחה',
      detail: 'המוצר עודכן בהצלחה',
      life: 3000
    });
  }

  onRowEditCancel(product: Product, index: number): void {
    this.filteredProducts[index] = this.clonedProducts[product.id];
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

  private getEmptyProduct(): Product {
    const defaultStatus = this.lookupService.getList('inventoryStatuses')[0] || 'במלאי';
    const defaultCategory = this.lookupService.getList('productCategories')[0] || '';

    return {
      id: Date.now().toString(),
      name: '',
      inventoryStatus: defaultStatus,
      brand: '',
      packageQuantity: 1,
      estimatedPrice: 0,
      category: defaultCategory,
      supplier: ''
    };
  }

  private updateInventorySummary(): void {
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
