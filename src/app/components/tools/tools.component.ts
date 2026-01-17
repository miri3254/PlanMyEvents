import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { EventService } from '../../services/event.service';
import { LookupService } from '../../core/services/lookup.service';
import { Tool } from '../../core/models';
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
  
  tool: Tool = {
    id: '',
    name: '',
    inventoryStatus: 'במלאי',
    brand: '',
    estimatedPrice: 0,
    category: '',
    subCategory: '',
    description: '',
    notes: '',
    quantity: 0
  };
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

  constructor(
    private eventService: EventService,
    private confirmationService: ConfirmationService,
    private messageService: MessageService,
    private lookupService: LookupService
  ) {}

  ngOnInit(): void {
    this.subscribeToTools();
    this.lookupService.lookup$
      .pipe(takeUntil(this.destroy$))
      .subscribe(data => {
        this.inventoryStatuses = data.inventoryStatuses.map(status => ({
          label: status,
          value: status
        }));

        this.categories = data.toolCategories.map(category => ({
          label: category,
          value: category
        }));

        this.subCategories = data.toolSubCategories.map(subCategory => ({
          label: subCategory,
          value: subCategory
        }));

        this.statusOptions = [
          { label: 'כל הסטטוסים', value: '' },
          ...data.inventoryStatuses.map(status => ({ label: status, value: status }))
        ];

        this.categoryOptions = [
          { label: 'כל הקטגוריות', value: '' },
          ...data.toolCategories.map(category => ({ label: category, value: category }))
        ];

        this.subCategoryOptions = [
          { label: 'כל התת-קטגוריות', value: '' },
          ...data.toolSubCategories.map(subCategory => ({ label: subCategory, value: subCategory }))
        ];

        if (
          this.filterInventoryStatus &&
          !data.inventoryStatuses.includes(this.filterInventoryStatus)
        ) {
          this.filterInventoryStatus = '';
          this.applyFilters();
        }

        if (
          this.toolDialog &&
          this.tool.category &&
          data.toolCategories.length &&
          !data.toolCategories.includes(this.tool.category)
        ) {
          this.tool.category = data.toolCategories[0];
        }

        this.updateInventorySummary();
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private subscribeToTools(): void {
    this.eventService.tools$
      .pipe(takeUntil(this.destroy$))
      .subscribe(tools => {
        this.tools = tools;
        this.applyFilters();
        this.updateInventorySummary();
      });
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
        this.eventService.deleteTool(tool.id);
        this.messageService.add({
          severity: 'success',
          summary: 'הצלחה',
          detail: 'הכלי נמחק בהצלחה',
          life: 3000
        });
      }
    });
  }

  deleteSelectedTools(): void {
    this.confirmationService.confirm({
      message: `האם אתה בטוח שברצונך למחוק ${this.selectedTools.length} כלים?`,
      header: 'אישור מחיקה',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'כן',
      rejectLabel: 'לא',
      accept: () => {
        this.selectedTools.forEach(tool => {
          this.eventService.deleteTool(tool.id);
        });
        this.selectedTools = [];
        this.messageService.add({
          severity: 'success',
          summary: 'הצלחה',
          detail: 'הכלים נמחקו בהצלחה',
          life: 3000
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

    if (!this.tool.id) {
      this.tool.id = Date.now().toString();
    }

    this.eventService.saveTool(this.tool);
    this.messageService.add({
      severity: 'success',
      summary: 'הצלחה',
      detail: 'הכלי נשמר בהצלחה',
      life: 3000
    });
    
    this.toolDialog = false;
    this.tool = this.getEmptyTool();
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
    this.eventService.saveTool(tool);
    this.messageService.add({
      severity: 'success',
      summary: 'הצלחה',
      detail: 'הכלי עודכן בהצלחה',
      life: 3000
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
    const defaultStatus = this.lookupService.getList('inventoryStatuses')[0] || 'במלאי';
    const defaultCategory = this.lookupService.getList('toolCategories')[0] || '';
    const defaultSubCategory = this.lookupService.getList('toolSubCategories')[0] || '';

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
