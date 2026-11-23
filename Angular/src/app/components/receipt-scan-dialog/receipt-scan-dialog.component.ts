import { Component, Inject, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatTableModule } from '@angular/material/table';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatChipsModule } from '@angular/material/chips';
import { Subject } from 'rxjs';
import { takeUntil, debounceTime, distinctUntilChanged } from 'rxjs/operators';
import Fuse from 'fuse.js';
import * as pdfjsLib from 'pdfjs-dist';
import { ReceiptScanService } from '../../services/receipt-scan.service';
import {
  ExistingProduct,
  ReceiptScanDialogData,
  ReceiptScanDialogResult,
  ScannedItem
} from './receipt-scan-dialog.types';

// Initialize PDF.js worker - using unpkg CDN which has latest versions
pdfjsLib.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`;

@Component({
  selector: 'app-receipt-scan-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatDialogModule,
    MatTableModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatChipsModule
  ],
  templateUrl: './receipt-scan-dialog.component.html',
  styleUrls: ['./receipt-scan-dialog.component.scss']
})
export class ReceiptScanDialogComponent implements OnInit, OnDestroy {
  scannedItems: ScannedItem[] = [];
  isLoading = false;
  hasScanned = false;
  errorMessage: string | null = null;

  displayedColumns: string[] = ['name', 'quantity', 'unitPrice', 'stock'];

  private destroy$ = new Subject<void>();
  private nameChangeSubjects: Map<number, Subject<string>> = new Map();
  private fuse!: Fuse<ExistingProduct>;

  constructor(
    public dialogRef: MatDialogRef<ReceiptScanDialogComponent, ReceiptScanDialogResult>,
    @Inject(MAT_DIALOG_DATA) public data: ReceiptScanDialogData,
    private receiptScanService: ReceiptScanService
  ) {}

  ngOnInit(): void {
    // Initialize Fuse.js for fuzzy matching
    this.fuse = new Fuse(this.data.existingProducts, {
      keys: ['name'],
      threshold: 0.4,
      includeScore: true
    });

    // If file was passed via data, process it immediately
    if (this.data.file) {
      this.processPdf(this.data.file);
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.nameChangeSubjects.forEach(subject => subject.complete());
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) {
      return;
    }

    const file = input.files[0];
    if (file.type !== 'application/pdf') {
      return;
    }

    this.processPdf(file);
  }

  private async processPdf(file: File): Promise<void> {
    this.isLoading = true;
    this.hasScanned = false;
    this.scannedItems = [];
    this.errorMessage = null;

    try {
      const images = await this.convertPdfToBase64Images(file);
      
      this.receiptScanService
        .scan(images, this.data.existingProducts)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (items: ScannedItem[]) => {
            this.scannedItems = items;
            this.initializeNameChangeListeners();
            this.isLoading = false;
            this.hasScanned = true;
          },
          error: (error: any) => {
            console.error('Error scanning receipt:', error);
            // Extract error message from backend response
            this.errorMessage = error?.error?.detail || error?.message || 'שגיאה בסריקת הקבלה';
            this.isLoading = false;
          }
        });
    } catch (error) {
      console.error('Error processing PDF:', error);
      this.errorMessage = 'שגיאה בעיבוד קובץ ה-PDF';
      this.isLoading = false;
    }
  }

  private async convertPdfToBase64Images(file: File): Promise<string[]> {
    const arrayBuffer = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
    
    const pagesToConvert = Math.min(2, pdf.numPages);
    const images: string[] = [];

    for (let pageNum = 1; pageNum <= pagesToConvert; pageNum++) {
      const page = await pdf.getPage(pageNum);
      const viewport = page.getViewport({ scale: 2.0 });
      
      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d')!;
      canvas.width = viewport.width;
      canvas.height = viewport.height;

      await page.render({
        canvas,
        canvasContext: context,
        viewport: viewport
      }).promise;

      // Convert to base64 (remove data:image/png;base64, prefix)
      const base64 = canvas.toDataURL('image/png').split(',')[1];
      images.push(base64);
    }

    return images;
  }

  private initializeNameChangeListeners(): void {
    this.scannedItems.forEach((item, index) => {
      const subject = new Subject<string>();
      this.nameChangeSubjects.set(index, subject);

      subject
        .pipe(
          debounceTime(400),
          distinctUntilChanged(),
          takeUntil(this.destroy$)
        )
        .subscribe((editedName) => {
          this.performFuzzyMatch(index, editedName);
        });
    });
  }

  onNameChange(index: number, newName: string): void {
    const subject = this.nameChangeSubjects.get(index);
    if (subject) {
      this.scannedItems[index].nameMatchLoading = true;
      subject.next(newName);
    }
  }

  private performFuzzyMatch(index: number, editedName: string): void {
    const item = this.scannedItems[index];
    
    if (!editedName || editedName.trim() === '') {
      item.matched_product_id = null;
      item.is_new = true;
      item.current_stock = 0;
      item.nameMatchLoading = false;
      return;
    }

    const results = this.fuse.search(editedName);
    
    if (results.length > 0 && results[0].score !== undefined && results[0].score <= 0.4) {
      const matchedProduct = results[0].item;
      item.matched_product_id = matchedProduct.id;
      item.is_new = false;
      item.current_stock = matchedProduct.stock;
    } else {
      item.matched_product_id = null;
      item.is_new = true;
      item.current_stock = 0;
    }
    
    item.nameMatchLoading = false;
  }

  triggerFileInput(): void {
    const fileInput = document.getElementById('pdfFileInput') as HTMLInputElement;
    fileInput?.click();
  }

  onConfirm(): void {
    this.dialogRef.close({
      confirmed: true,
      items: this.scannedItems
    });
  }

  onCancel(): void {
    this.dialogRef.close();
  }

  get canConfirm(): boolean {
    return !this.isLoading && this.scannedItems.length > 0;
  }
}
