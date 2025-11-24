import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Product } from '../../models/product.model';
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
import { TooltipModule } from 'primeng/tooltip';
import { SelectButtonModule } from 'primeng/selectbutton';
import { RippleModule } from 'primeng/ripple';
import { CheckboxModule } from 'primeng/checkbox';
import { DividerModule } from 'primeng/divider';
import { FloatLabelModule } from 'primeng/floatlabel';




@Component({
  selector: 'app-products',
  standalone: true,
  imports: [
    CommonModule,
    DividerModule,
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
    TooltipModule,
    SelectButtonModule,
    RippleModule,
    CheckboxModule,
    FloatLabelModule
  ],
  templateUrl: './products.html',
  styleUrls: ['./products.scss'],
  providers: [ConfirmationService, MessageService]
})
export class ProductsComponent implements OnInit {
  products: Product[] = [];
  filteredProducts: Product[] = [];
  productDialog: boolean = false;
  submitted: boolean = false;
  product: Product = this.createEmptyProduct();
  searchValue: string = '';

  inventoryStatuses = [
    { label: 'במלאי', value: 'במלאי' },
    { label: 'אזל', value: 'אזל' },
    { label: 'מלאי-נמוך', value: 'מלאי-נמוך' }
  ];

  categories = [
    { label: 'מוצרי מזון', value: 'מוצרי מזון' },
    { label: 'משקאות', value: 'משקאות' },
    { label: 'חטיפים', value: 'חטיפים' },
    { label: 'מוצרי חלב', value: 'מוצרי חלב' }
  ];

  constructor(
    private confirmationService: ConfirmationService,
    private messageService: MessageService
  ) {}

  ngOnInit(): void {
    this.loadProducts();
  }

  loadProducts(): void {
    // TODO: Replace with actual data service call
    this.products = [
      {
        name: 'לחם אחיד',
        inventoryStatus: 'במלאי',
        brand: 'אנגל',
        packageQuantity: 1,
        estimatedPrice: 12,
        category: 'מוצרי מזון',
        supplier: 'ספק לחמים בע"מ'
      },
      {
        name: 'חלב 3%',
        inventoryStatus: 'במלאי',
        brand: 'תנובה',
        packageQuantity: 1,
        estimatedPrice: 7,
        category: 'מוצרי חלב',
        supplier: 'תנובה בע"מ'
      },
      {
        name: 'ביסלי',
        inventoryStatus: 'מלאי-נמוך',
        brand: 'אוסם',
        packageQuantity: 6,
        estimatedPrice: 25,
        category: 'חטיפים',
        supplier: 'אוסם בע"מ'
      },
      {
        name: 'קוקה קולה',
        inventoryStatus: 'במלאי',
        brand: 'קוקה קולה',
        packageQuantity: 12,
        estimatedPrice: 45,
        category: 'משקאות',
        supplier: 'קוקה קולה ישראל'
      }
    ];
    this.filteredProducts = [...this.products];
  }

  createEmptyProduct(): Product {
    return {
      name: '',
      inventoryStatus: 'במלאי',
      brand: '',
      packageQuantity: 1,
      estimatedPrice: 0,
      category: 'מוצרי מזון',
      supplier: ''
    };
  }

  openNew(): void {
    this.product = this.createEmptyProduct();
    this.submitted = false;
    this.productDialog = true;
  }

  editProduct(product: Product): void {
    this.product = { ...product };
    this.productDialog = true;
  }

  deleteProduct(product: Product): void {
    this.confirmationService.confirm({
      message: `האם אתה בטוח שברצונך למחוק את המוצר "${product.name}"?`,
      header: 'אישור מחיקה',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'כן',
      rejectLabel: 'לא',
      accept: () => {
        this.products = this.products.filter(p => p !== product);
        this.filteredProducts = this.filteredProducts.filter(p => p !== product);
        this.messageService.add({
          severity: 'success',
          summary: 'הצלחה',
          detail: 'המוצר נמחק בהצלחה'
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

    if (this.product.name?.trim()) {
      if (this.product.name) {
        // Edit existing product
        const index = this.products.findIndex(p => p.name === this.product.name);
        if (index !== -1) {
          this.products[index] = this.product;
        } else {
          // Add new product
          this.products.push(this.product);
        }
        this.filteredProducts = [...this.products];
        this.messageService.add({
          severity: 'success',
          summary: 'הצלחה',
          detail: this.product.name ? 'המוצר עודכן בהצלחה' : 'המוצר נוסף בהצלחה'
        });
      }

      this.productDialog = false;
      this.product = this.createEmptyProduct();
    }
  }

  onSearch(): void {
    if (this.searchValue.trim()) {
      this.filteredProducts = this.products.filter(product =>
        product.name.toLowerCase().includes(this.searchValue.toLowerCase()) ||
        product.brand.toLowerCase().includes(this.searchValue.toLowerCase()) ||
        product.category.toLowerCase().includes(this.searchValue.toLowerCase()) ||
        product.supplier.toLowerCase().includes(this.searchValue.toLowerCase())
      );
    } else {
      this.filteredProducts = [...this.products];
    }
  }

  clearSearch(): void {
    this.searchValue = '';
    this.filteredProducts = [...this.products];
  }

  trackByProduct(index: number, product: Product): string {
    return product.name + product.brand;
  }

  getStatusSeverity(status: string): "success" | "info" | "warn" | "danger" | "secondary" | "contrast" | null {
    switch (status) {
      case 'במלאי':
        return 'success';
      case 'אזל':
        return 'danger';
      case 'מלאי-נמוך':
        return 'warn';
      default:
        return 'info';
    }
  }

  viewMode: 'table' | 'cards' = 'table';
  selectedProducts: Product[] = [];
  
  toggleView() { 
    this.viewMode = this.viewMode === 'table' ? 'cards' : 'table'; 
  }

  clonedProducts: { [s: string]: Product } = {};

  onSelectAllChange(event: any) {
    if (event.checked) {
      this.selectedProducts = [...this.filteredProducts];
    } else {
      this.selectedProducts = [];
    }
  }

  deleteSelectedProducts() {
    this.confirmationService.confirm({
      message: `האם אתה בטוח שברצונך למחוק ${this.selectedProducts.length} מוצרים?`,
      header: 'אישור מחיקה',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'כן',
      rejectLabel: 'לא',
      accept: () => {
        this.products = this.products.filter(p => !this.selectedProducts.includes(p));
        this.filteredProducts = this.filteredProducts.filter(p => !this.selectedProducts.includes(p));
        this.messageService.add({
          severity: 'success',
          summary: 'הצלחה',
          detail: `${this.selectedProducts.length} מוצרים נמחקו בהצלחה`
        });
        this.selectedProducts = [];
      }
    });
  }

  onRowEditInit(product: Product) {
    this.clonedProducts[product.name] = { ...product };
  }

  onRowEditSave(product: Product) {
    if (product.name && product.name.trim()) {
      delete this.clonedProducts[product.name];
      const index = this.products.findIndex(p => p.name === product.name);
      if (index !== -1) {
        this.products[index] = product;
        this.filteredProducts = [...this.products];
      }
      this.messageService.add({
        severity: 'success',
        summary: 'הצלחה',
        detail: 'המוצר עודכן בהצלחה'
      });
    } else {
      this.messageService.add({
        severity: 'error',
        summary: 'שגיאה',
        detail: 'שם המוצר נדרש'
      });
    }
  }

  onRowEditCancel(product: Product, index: number) {
    this.filteredProducts[index] = this.clonedProducts[product.name];
    delete this.clonedProducts[product.name];
  }
  filterByInventoryStatus(status: string) {
    if(!status) {
      this.filteredProducts = [...this.products];
      return;
    }
    this.filteredProducts = this.products.filter(product => product.inventoryStatus === status);
  }
}