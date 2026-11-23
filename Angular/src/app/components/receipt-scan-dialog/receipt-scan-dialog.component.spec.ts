import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { of, throwError, Subject } from 'rxjs';

import { ReceiptScanDialogComponent } from './receipt-scan-dialog.component';
import { ReceiptScanService } from '../../services/receipt-scan.service';
import { ReceiptScanDialogData, ScannedItem } from './receipt-scan-dialog.types';

const mockDialogData: ReceiptScanDialogData = {
  existingProducts: [
    { id: 1, name: 'מלח', stock: 3 }
  ]
};

const makeScannedItem = (overrides: Partial<ScannedItem> = {}): ScannedItem => ({
  name: 'מוצר בדיקה',
  edited_name: '',
  quantity: 2,
  unit_price: 15,
  matched_product_id: null,
  is_new: true,
  current_stock: 0,
  nameMatchLoading: false,
  ...overrides
});

describe('ReceiptScanDialogComponent', () => {
  let component: ReceiptScanDialogComponent;
  let fixture: ComponentFixture<ReceiptScanDialogComponent>;
  let mockDialogRef: jasmine.SpyObj<MatDialogRef<ReceiptScanDialogComponent>>;
  let mockReceiptScanService: jasmine.SpyObj<ReceiptScanService>;

  beforeEach(async () => {
    mockDialogRef = jasmine.createSpyObj('MatDialogRef', ['close']);
    mockReceiptScanService = jasmine.createSpyObj('ReceiptScanService', ['scan']);
    mockReceiptScanService.scan.and.returnValue(of([]));

    await TestBed.configureTestingModule({
      imports: [
        ReceiptScanDialogComponent,
        NoopAnimationsModule
      ],
      providers: [
        { provide: MatDialogRef, useValue: mockDialogRef },
        { provide: MAT_DIALOG_DATA, useValue: mockDialogData },
        { provide: ReceiptScanService, useValue: mockReceiptScanService }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ReceiptScanDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should start with no scanned items', () => {
    expect(component.scannedItems).toEqual([]);
  });

  it('should start with isLoading = false', () => {
    expect(component.isLoading).toBeFalse();
  });

  it('should start with hasScanned = false', () => {
    expect(component.hasScanned).toBeFalse();
  });

  it('should start with no error message', () => {
    expect(component.errorMessage).toBeNull();
  });

  it('should receive existing products from dialog data', () => {
    expect(component.data.existingProducts.length).toBe(1);
    expect(component.data.existingProducts[0].name).toBe('מלח');
  });

  it('should ignore file selection when no file is provided', () => {
    const mockEvent = { target: { files: null } } as unknown as Event;
    component.onFileSelected(mockEvent);
    expect(component.isLoading).toBeFalse();
  });

  it('should ignore non-PDF file selection', () => {
    const mockFile = new File(['content'], 'file.txt', { type: 'text/plain' });
    const mockEvent = {
      target: { files: [mockFile] }
    } as unknown as Event;
    component.onFileSelected(mockEvent);
    expect(component.isLoading).toBeFalse();
  });

  it('should handle name change for existing item', () => {
    component.scannedItems = [makeScannedItem({ name: 'מלח' })];
    // Create a subject for the item at index 0
    (component as any).nameChangeSubjects.set(0, new Subject<string>());

    component.onNameChange(0, 'מלח שולחן');
    expect(component.scannedItems[0].nameMatchLoading).toBeTrue();
  });

  it('should display columns including name, quantity, unitPrice and stock', () => {
    expect(component.displayedColumns).toContain('name');
    expect(component.displayedColumns).toContain('quantity');
    expect(component.displayedColumns).toContain('unitPrice');
    expect(component.displayedColumns).toContain('stock');
  });

  it('should clean up subscriptions on destroy', () => {
    const destroySpy = spyOn((component as any).destroy$, 'next').and.callThrough();
    component.ngOnDestroy();
    expect(destroySpy).toHaveBeenCalled();
  });
});
