import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, EMPTY, forkJoin, of } from 'rxjs';
import { catchError, map, takeUntil } from 'rxjs/operators';
import { Tool } from '../../core/models';
import { ApiToolService } from '../../services/api-tool.service';
import { ApiLookupService } from '../../services/api-lookup.service';
import { ApiTool, ToolCreate, ToolUpdate, LookupValue } from '../../core/models/api.models';

const FALLBACK_INVENTORY_STATUSES = ['במלאי', 'מלאי נמוך', 'אזל'];
const FALLBACK_TOOL_CATEGORIES = ['מפות', 'כלי הגשה', 'צלחות', 'סכו"ם', 'כוסות', 'קערות', 'מגשים', 'אחר'];
const FALLBACK_TOOL_SUB_CATEGORIES = ['חד"פ', 'אמיתי'];
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
import { TextareaModule } from 'primeng/textarea';

@Component({
  selector: 'app-tools',
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
    TextareaModule
  ],
  templateUrl: './tools.html',
  styleUrls: ['./tools.scss'],
  providers: [ConfirmationService, MessageService]
})
export class ToolsComponent implements OnInit, OnDestroy {
  tools: Tool[] = [];
  filteredTools: Tool[] = [];
  selectedTools: Tool[] = [];

  private readonly destroy$ = new Subject<void>();
  
  viewMode: 'table' | 'grid' = 'table';
  searchValue: string = '';
  filterInventoryStatus: string = '';
  filterCategory: string = '';
  filterSubCategory: string = '';
  toolDialog: boolean = false;
  detailDialog: boolean = false;
  submitted: boolean = false;
  
  sortField: string = '';
  sortOrder: 'asc' | 'desc' | '' = '';
  
  tool!: Tool;
  selectedTool: Tool | null = null;
  
  inventorySummary: Array<{
    value: string;
    label: string;
    count: number;
    severity: 'success' | 'warn' | 'danger' | 'info' | 'secondary' | 'contrast' | undefined;
    icon: string;
    badgeClass: string;
  }> = [];
  
  inventoryStatuses: { label: string; value: string }[] = [];
  categories: { label: string; value: string }[] = [];
  subCategories: { label: string; value: string }[] = [];
  statusOptions = [{ label: 'כל הסטטוסים', value: '' }];
  categoryOptions = [{ label: 'כל הקטגוריות', value: '' }];
  subCategoryOptions = [{ label: 'כל התת-קטגוריות', value: '' }];
  
  clonedTools: { [s: string]: Tool } = {};

  private inventoryStatusValues: string[] = [...FALLBACK_INVENTORY_STATUSES];
  private categoryValues: string[] = [...FALLBACK_TOOL_CATEGORIES];
  private subCategoryValues: string[] = [...FALLBACK_TOOL_SUB_CATEGORIES];

  constructor(
    private toolService: ApiToolService,
    private confirmationService: ConfirmationService,
    private messageService: MessageService,
    private lookupService: ApiLookupService
  ) {
    this.tool = this.getEmptyTool();
  }

  ngOnInit(): void {
    this.loadTools();
    this.loadLookupData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadTools(): void {
    this.toolService.getTools()
      .pipe(
        takeUntil(this.destroy$),
        map(response => (response.items || []).map(tool => this.mapApiToolToTool(tool))),
        catchError(error => {
          console.error('Error loading tools:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'שגיאה',
            detail: 'טעינת הכלים נכשלה'
          });
          return EMPTY;
        })
      )
      .subscribe(tools => {
        this.tools = tools;
        this.applyFilters();
        this.updateInventorySummary();
      });
  }

  private loadLookupData(): void {
    forkJoin({
      statuses: this.lookupService.getLookupCategory('inventory_statuses')
        .pipe(catchError(() => of<LookupValue[]>([]))),
      categories: this.lookupService.getLookupCategory('tool_categories')
        .pipe(catchError(() => of<LookupValue[]>([]))),
      subCategories: this.lookupService.getLookupCategory('tool_sub_categories')
        .pipe(catchError(() => of<LookupValue[]>([])))
    })
      .pipe(takeUntil(this.destroy$))
      .subscribe(({ statuses, categories, subCategories }) => {
        this.inventoryStatusValues = this.toDisplayList(statuses, FALLBACK_INVENTORY_STATUSES);
        this.categoryValues = this.toDisplayList(categories, FALLBACK_TOOL_CATEGORIES);
        this.subCategoryValues = this.toDisplayList(subCategories, FALLBACK_TOOL_SUB_CATEGORIES);

        this.inventoryStatuses = this.inventoryStatusValues.map(value => ({ label: value, value }));
        this.categories = this.categoryValues.map(value => ({ label: value, value }));
        this.subCategories = this.subCategoryValues.map(value => ({ label: value, value }));

        this.statusOptions = [{ label: 'כל הסטטוסים', value: '' }, ...this.inventoryStatuses];
        this.categoryOptions = [{ label: 'כל הקטגוריות', value: '' }, ...this.categories];
        this.subCategoryOptions = [{ label: 'כל התת-קטגוריות', value: '' }, ...this.subCategories];

        if (this.filterInventoryStatus && !this.inventoryStatusValues.includes(this.filterInventoryStatus)) {
          this.filterInventoryStatus = '';
        }

        if (this.filterCategory && !this.categoryValues.includes(this.filterCategory)) {
          this.filterCategory = '';
        }

        if (this.filterSubCategory && !this.subCategoryValues.includes(this.filterSubCategory)) {
          this.filterSubCategory = '';
        }

        if (this.toolDialog) {
          if (this.tool.category && !this.categoryValues.includes(this.tool.category)) {
            this.tool.category = this.categoryValues[0] || '';
          }
          if (this.tool.subCategory && !this.subCategoryValues.includes(this.tool.subCategory)) {
            this.tool.subCategory = this.subCategoryValues[0] || '';
          }
          if (this.tool.inventoryStatus && !this.inventoryStatusValues.includes(this.tool.inventoryStatus)) {
            this.tool.inventoryStatus = this.inventoryStatusValues[0] || FALLBACK_INVENTORY_STATUSES[0];
          }
        }

        this.applyFilters();
        this.updateInventorySummary();
      });
  }

  private toDisplayList(values: LookupValue[], fallback: string[]): string[] {
    const list = (values || []).map(v => v.display_name || v.name).filter(Boolean);
    return list.length ? list : [...fallback];
  }

  private mapApiToolToTool(apiTool: ApiTool): Tool {
    return {
      id: apiTool.id,
      name: apiTool.name,
      brand: apiTool.brand || '',
      category: apiTool.category,
      subCategory: apiTool.sub_category || '',
      inventoryStatus: apiTool.inventory_status,
      estimatedPrice: apiTool.estimated_price ?? 0,
      description: apiTool.description || '',
      notes: apiTool.notes || '',
      quantity: apiTool.quantity ?? 0
    };
  }

  private mapToolToCreatePayload(tool: Tool): ToolCreate {
    return {
      name: tool.name.trim(),
      category: tool.category,
      sub_category: tool.subCategory || undefined,
      inventory_status: tool.inventoryStatus,
      estimated_price: tool.estimatedPrice,
      quantity: tool.quantity,
      brand: tool.brand || undefined,
      description: tool.description || undefined,
      notes: tool.notes || undefined
    };
  }

  private mapToolToUpdatePayload(tool: Tool): ToolUpdate {
    return this.mapToolToCreatePayload(tool);
  }

  setViewMode(mode: 'table' | 'grid'): void {
    this.viewMode = mode;
  }

  applyFilters(): void {
    this.filteredTools = this.tools.filter(tool => {
      const matchesSearch = !this.searchValue || 
        tool.name.toLowerCase().includes(this.searchValue.toLowerCase()) ||
        tool.brand.toLowerCase().includes(this.searchValue.toLowerCase()) ||
        (tool.description?.toLowerCase().includes(this.searchValue.toLowerCase()));
      
      const matchesStatus = !this.filterInventoryStatus || 
        tool.inventoryStatus === this.filterInventoryStatus;
      
      const matchesCategory = !this.filterCategory || 
        tool.category === this.filterCategory;
      
      const matchesSubCategory = !this.filterSubCategory || 
        tool.subCategory === this.filterSubCategory;
      
      return matchesSearch && matchesStatus && matchesCategory && matchesSubCategory;
    });

    if (this.sortField && this.sortOrder) {
      this.filteredTools.sort((a, b) => {
        let aValue = (a as any)[this.sortField];
        let bValue = (b as any)[this.sortField];

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
      this.filteredTools.sort((a, b) => {
        const aId = parseInt(a.id) || 0;
        const bId = parseInt(b.id) || 0;
        return bId - aId;
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

  filterByCategoryValue(category: string): void {
    this.filterCategory = category;
    this.applyFilters();
  }

  filterBySubCategoryValue(subCategory: string): void {
    this.filterSubCategory = subCategory;
    this.applyFilters();
  }

  filterBySubCategory(subCategory: string): void {
    // Toggle - if already selected, clear it
    if (this.filterSubCategory === subCategory) {
      this.filterSubCategory = '';
    } else {
      this.filterSubCategory = subCategory;
    }
    this.applyFilters();
  }

  clearFilters(): void {
    this.searchValue = '';
    this.filterInventoryStatus = '';
    this.filterCategory = '';
    this.filterSubCategory = '';
    this.applyFilters();
  }

  toggleView(): void {
    this.viewMode = this.viewMode === 'table' ? 'grid' : 'table';
  }

  openNew(): void {
    this.tool = this.getEmptyTool();
    this.submitted = false;
    this.toolDialog = true;
  }

  editTool(tool: Tool): void {
    this.tool = { ...tool };
    this.toolDialog = true;
  }

  viewToolDetails(tool: Tool): void {
    this.selectedTool = { ...tool };
    this.detailDialog = true;
  }

  editFromDetails(): void {
    if (this.selectedTool) {
      this.tool = { ...this.selectedTool };
      this.detailDialog = false;
      this.toolDialog = true;
    }
  }

  deleteTool(tool: Tool): void {
    this.confirmationService.confirm({
      message: `האם אתה בטוח שברצונך למחוק את ${tool.name}?`,
      header: 'אישור מחיקה',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'כן',
      rejectLabel: 'לא',
      accept: () => {
        this.toolService.deleteTool(tool.id)
          .pipe(
            takeUntil(this.destroy$),
            catchError(error => {
              console.error('Error deleting tool:', error);
              this.messageService.add({
                severity: 'error',
                summary: 'שגיאה',
                detail: 'מחיקת הכלי נכשלה',
                life: 3000
              });
              return EMPTY;
            })
          )
          .subscribe(() => {
            this.messageService.add({
              severity: 'success',
              summary: 'הצלחה',
              detail: 'הכלי נמחק בהצלחה',
              life: 3000
            });
            this.loadTools();
          });
      }
    });
  }

  deleteSelectedTools(): void {
    if (!this.selectedTools.length) {
      return;
    }

    this.confirmationService.confirm({
      message: `האם אתה בטוח שברצונך למחוק ${this.selectedTools.length} כלים?`,
      header: 'אישור מחיקה',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'כן',
      rejectLabel: 'לא',
      accept: () => {
        const ids = this.selectedTools.map(tool => tool.id);
        const request$ = ids.length > 1
          ? this.toolService.deleteMultipleTools(ids)
          : this.toolService.deleteTool(ids[0]);

        request$
          .pipe(
            takeUntil(this.destroy$),
            catchError(error => {
              console.error('Error deleting tools:', error);
              this.messageService.add({
                severity: 'error',
                summary: 'שגיאה',
                detail: 'מחיקת הכלים נכשלה',
                life: 3000
              });
              return EMPTY;
            })
          )
          .subscribe(() => {
            this.selectedTools = [];
            this.messageService.add({
              severity: 'success',
              summary: 'הצלחה',
              detail: 'הכלים נמחקו בהצלחה',
              life: 3000
            });
            this.loadTools();
          });
      }
    });
  }

  hideDialog(): void {
    this.toolDialog = false;
    this.submitted = false;
  }

  hideDetailDialog(): void {
    this.detailDialog = false;
    this.selectedTool = null;
  }

  saveTool(): void {
    this.submitted = true;

    if (!this.tool.name?.trim()) {
      return;
    }

    const isUpdate = !!this.tool.id;
    const payload = isUpdate
      ? this.mapToolToUpdatePayload(this.tool)
      : this.mapToolToCreatePayload(this.tool);

    const request$ = isUpdate
      ? this.toolService.updateTool(this.tool.id, payload as ToolUpdate)
      : this.toolService.createTool(payload as ToolCreate);

    request$
      .pipe(
        takeUntil(this.destroy$),
        catchError(error => {
          console.error('Error saving tool:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'שגיאה',
            detail: 'שמירת הכלי נכשלה',
            life: 3000
          });
          return EMPTY;
        })
      )
      .subscribe(() => {
        this.messageService.add({
          severity: 'success',
          summary: 'הצלחה',
          detail: isUpdate ? 'הכלי עודכן בהצלחה' : 'הכלי נוצר בהצלחה',
          life: 3000
        });
        this.toolDialog = false;
        this.tool = this.getEmptyTool();
        this.loadTools();
      });
  }

  sortBy(field: string): void {
    if (this.sortField === field) {
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
      this.selectedTools = [...this.filteredTools];
    } else {
      this.selectedTools = [];
    }
  }

  onRowEditInit(tool: Tool): void {
    this.clonedTools[tool.id] = { ...tool };
  }

  onRowEditSave(tool: Tool): void {
    delete this.clonedTools[tool.id];
    this.toolService.updateTool(tool.id, this.mapToolToUpdatePayload(tool))
      .pipe(
        takeUntil(this.destroy$),
        catchError(error => {
          console.error('Error updating tool:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'שגיאה',
            detail: 'עדכון הכלי נכשל',
            life: 3000
          });
          return EMPTY;
        })
      )
      .subscribe(() => {
        this.messageService.add({
          severity: 'success',
          summary: 'הצלחה',
          detail: 'הכלי עודכן בהצלחה',
          life: 3000
        });
        this.loadTools();
      });
  }

  onRowEditCancel(tool: Tool, index: number): void {
    this.filteredTools[index] = this.clonedTools[tool.id];
    delete this.clonedTools[tool.id];
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

  getSubCategorySeverity(subCategory: string): 'success' | 'warn' | 'danger' | 'info' | 'secondary' | 'contrast' | undefined {
    if (subCategory === 'חד"פ') {
      return 'info';
    }
    if (subCategory === 'אמיתי') {
      return 'success';
    }
    return 'secondary';
  }

  trackByTool(index: number, tool: Tool): string {
    return tool.id;
  }

  private getEmptyTool(): Tool {
    const defaultStatus = this.inventoryStatusValues[0] || FALLBACK_INVENTORY_STATUSES[0];
    const defaultCategory = this.categoryValues[0] || '';
    const defaultSubCategory = this.subCategoryValues[0] || '';

    return {
      id: '',
      name: '',
      inventoryStatus: defaultStatus,
      brand: '',
      estimatedPrice: 0,
      category: defaultCategory,
      subCategory: defaultSubCategory,
      description: '',
      notes: '',
      quantity: 0
    };
  }

  private updateInventorySummary(): void {
    if (!this.inventoryStatuses.length) {
      this.inventorySummary = [];
      return;
    }

    this.inventorySummary = this.inventoryStatuses.map(option => {
      const count = this.tools.filter(tool => tool.inventoryStatus === option.value).length;
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
