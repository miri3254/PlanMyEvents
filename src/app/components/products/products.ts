import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { EventService } from '../../core/services/event.service';
import { Product } from '../../core/models';
import { INVENTORY_STATUS, CATEGORIES } from '../../core/constants/app.constants';
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
export class ProductsComponent implements OnInit {
  // Data properties
  products: Product[] = [];
  filteredProducts: Product[] = [];
  selectedProducts: Product[] = [];
  
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
  product: Product = this.getEmptyProduct();
  
  // Statistics
  inventoryStats = {
    inStock: 0,
    lowStock: 0,
    outOfStock: 0
  };
  
  // Dropdown options
  inventoryStatuses = INVENTORY_STATUS.map(status => ({ 
    label: status, 
    value: status 
  }));
  
  categories = CATEGORIES.map(category => ({ 
    label: category, 
    value: category 
  }));

  statusOptions = [
    { label: 'כל הסטטוסים', value: '' },
    ...INVENTORY_STATUS.map(status => ({ label: status, value: status }))
  ];
  
  // For inline editing in table
  clonedProducts: { [s: string]: Product } = {};

  constructor(
    private eventService: EventService,
    private confirmationService: ConfirmationService,
    private messageService: MessageService
  ) {}

  ngOnInit(): void {
    this.loadProducts();
  }

  loadProducts(): void {
    this.eventService.products$.subscribe(products => {
      this.products = products;
      this.calculateStats();
      this.applyFilters();
    });
  }

  calculateStats(): void {
    this.inventoryStats = {
      inStock: this.products.filter(p => p.inventoryStatus === 'במלאי').length,
      lowStock: this.products.filter(p => p.inventoryStatus === 'מלאי-נמוך').length,
      outOfStock: this.products.filter(p => p.inventoryStatus === 'אזל').length
    };
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
    
    // Reload to show new product at top
    this.loadProducts();
    
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
    switch (status) {
      case 'במלאי': return 'success';
      case 'מלאי-נמוך': return 'warn';
      case 'אזל': return 'danger';
      default: return 'info';
    }
  }

  getStatusIcon(status: string): string {
    switch (status) {
      case 'במלאי': return 'pi pi-check-circle';
      case 'מלאי-נמוך': return 'pi pi-exclamation-circle';
      case 'אזל': return 'pi pi-times-circle';
      default: return 'pi pi-info-circle';
    }
  }

  trackByProduct(index: number, product: Product): string {
    return product.id;
  }

  private getEmptyProduct(): Product {
    return {
      id: Date.now().toString(),
      name: '',
      inventoryStatus: 'במלאי',
      brand: '',
      packageQuantity: 1,
      estimatedPrice: 0,
      category: '',
      supplier: ''
    };
  }
}