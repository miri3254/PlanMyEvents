import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of } from 'rxjs';

import { ProductsComponent } from './products.component';
import { ApiProductService } from '../../services/api-product.service';
import { ApiLookupService } from '../../services/api-lookup.service';
import { ConfirmationService, MessageService } from 'primeng/api';

describe('ProductsComponent', () => {
  let component: ProductsComponent;
  let fixture: ComponentFixture<ProductsComponent>;
  let mockProductService: jasmine.SpyObj<ApiProductService>;
  let mockLookupService: jasmine.SpyObj<ApiLookupService>;

  beforeEach(async () => {
    mockProductService = jasmine.createSpyObj('ApiProductService', [
      'getProducts',
      'createProduct',
      'updateProduct',
      'deleteProduct',
      'deleteMultipleProducts'
    ]);
    
    mockLookupService = jasmine.createSpyObj('ApiLookupService', [
      'getLookupCategory'
    ]);

    // Setup default return values
    mockProductService.getProducts.and.returnValue(of({ items: [], total: 0, skip: 0, limit: 100 }));
    mockLookupService.getLookupCategory.and.returnValue(of([]));

    await TestBed.configureTestingModule({
      imports: [
        ProductsComponent,
        HttpClientTestingModule,
        NoopAnimationsModule
      ],
      providers: [
        { provide: ApiProductService, useValue: mockProductService },
        { provide: ApiLookupService, useValue: mockLookupService },
        ConfirmationService,
        MessageService
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ProductsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('saves pooled juice classification and bottle units through the existing product API', () => {
    component.product = { name: '', category: '', unit: 'ליטר', drinkType: 'orange_flavored', quantityInStock: 12 };
    component.onDrinkTypeChange();
    expect(component.product.name).toBe('מיץ');
    expect(component.product.unit).toBe('יחידות');
    mockProductService.createProduct.and.returnValue(of({ id: 9, name: 'מיץ', category: 'נוזלים', unit: 'יחידות' } as any));
    component.saveProduct();
    expect(mockProductService.createProduct).toHaveBeenCalledWith(jasmine.objectContaining({
      drink_type: 'orange_flavored', unit: 'יחידות', quantity_in_stock: 12
    }));
  });

  it('loads drink classification and explicitly clears it when removed', () => {
    component.product = component.mapApiProductToProduct({ id: 9, name: 'מיץ', category: 'נוזלים', unit: 'יחידות', drink_type: 'orange_flavored' } as any);
    expect(component.product.drinkType).toBe('orange_flavored');
    component.product.drinkType = null;
    mockProductService.updateProduct.and.returnValue(of({ id: 9 } as any));
    component.saveProduct();
    expect(mockProductService.updateProduct).toHaveBeenCalledWith(9, jasmine.objectContaining({ drink_type: null }));
  });

  it('should load products on init', () => {
    expect(mockProductService.getProducts).toHaveBeenCalled();
    expect(mockLookupService.getLookupCategory).toHaveBeenCalledWith('inventory_statuses');
    expect(mockLookupService.getLookupCategory).toHaveBeenCalledWith('product_categories');
    expect(mockLookupService.getLookupCategory).toHaveBeenCalledWith('measurement_units');
  });

  it('should filter products by search value', () => {
    component.products = [
      { id: 1, name: 'חלב', inventoryStatus: 'במלאי', brand: 'תנובה', packageQuantity: 1, estimatedPrice: 10, category: 'מוצרי חלב', supplier: 'סופר', unit: 'ליטר' },
      { id: 2, name: 'לחם', inventoryStatus: 'במלאי', brand: 'אנג\'ל', packageQuantity: 1, estimatedPrice: 8, category: 'מאפים', supplier: 'סופר', unit: 'יחידה' }
    ];
    
    component.searchValue = 'חלב';
    component.applyFilters();
    
    expect(component.filteredProducts.length).toBe(1);
    expect(component.filteredProducts[0].name).toBe('חלב');
  });

  it('should filter products by inventory status', () => {
    component.products = [
      { id: 1, name: 'מוצר1', inventoryStatus: 'במלאי', brand: '', packageQuantity: 1, estimatedPrice: 10, category: 'קטגוריה', supplier: '', unit: 'יחידה' },
      { id: 2, name: 'מוצר2', inventoryStatus: 'אזל', brand: '', packageQuantity: 1, estimatedPrice: 8, category: 'קטגוריה', supplier: '', unit: 'יחידה' }
    ];
    
    component.filterByInventoryStatus('אזל');
    
    expect(component.filteredProducts.length).toBe(1);
    expect(component.filteredProducts[0].inventoryStatus).toBe('אזל');
  });

  it('should open new product dialog', () => {
    component.openNew();
    
    expect(component.productDialog).toBeTrue();
    expect(component.product.id).toBe(0);
    expect(component.submitted).toBeFalse();
  });

  it('should toggle view mode', () => {
    expect(component.viewMode).toBe('table');
    
    component.setViewMode('grid');
    expect(component.viewMode).toBe('grid');
    
    component.setViewMode('table');
    expect(component.viewMode).toBe('table');
  });

  it('should sort products correctly', () => {
    component.products = [
      { id: 1, name: 'בננה', inventoryStatus: 'במלאי', brand: '', packageQuantity: 1, estimatedPrice: 5, category: 'פירות', supplier: '', unit: 'יחידה' },
      { id: 2, name: 'אבטיח', inventoryStatus: 'במלאי', brand: '', packageQuantity: 1, estimatedPrice: 20, category: 'פירות', supplier: '', unit: 'יחידה' }
    ];
    component.filteredProducts = [...component.products];
    
    component.sortBy('name');
    component.applyFilters();
    
    expect(component.sortField).toBe('name');
    expect(component.sortOrder).toBe('asc');
    expect(component.filteredProducts[0].name).toBe('אבטיח');
  });

  it('should clear filters', () => {
    component.searchValue = 'test';
    component.filterInventoryStatus = 'במלאי';
    
    component.clearFilters();
    
    expect(component.searchValue).toBe('');
    expect(component.filterInventoryStatus).toBe('');
  });

  it('should return correct status severity', () => {
    expect(component.getStatusSeverity('במלאי')).toBe('success');
    expect(component.getStatusSeverity('מלאי נמוך')).toBe('warn');
    expect(component.getStatusSeverity('אזל')).toBe('danger');
  });

  it('should hide dialog and reset submitted', () => {
    component.productDialog = true;
    component.submitted = true;
    
    component.hideDialog();
    
    expect(component.productDialog).toBeFalse();
    expect(component.submitted).toBeFalse();
  });
});
