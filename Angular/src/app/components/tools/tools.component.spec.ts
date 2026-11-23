import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of } from 'rxjs';

import { ToolsComponent } from './tools.component';
import { ApiToolService } from '../../services/api-tool.service';
import { ApiLookupService } from '../../services/api-lookup.service';
import { ExcelExportService } from '../../services/excel-export.service';
import { ConfirmationService, MessageService } from 'primeng/api';
import { Tool } from '../../core/models';

const makeTool = (overrides: Partial<Tool> = {}): Tool => ({
  id: 1,
  name: 'כלי בדיקה',
  brand: '',
  category: 'צלחות',
  subCategory: 'אמיתי',
  inventoryStatus: 'במלאי',
  pricePerUnit: 10,
  description: '',
  quantityInStock: 5,
  ...overrides
});

describe('ToolsComponent', () => {
  let component: ToolsComponent;
  let fixture: ComponentFixture<ToolsComponent>;
  let mockToolService: jasmine.SpyObj<ApiToolService>;
  let mockLookupService: jasmine.SpyObj<ApiLookupService>;
  let mockExcelService: jasmine.SpyObj<ExcelExportService>;

  beforeEach(async () => {
    mockToolService = jasmine.createSpyObj('ApiToolService', [
      'getTools',
      'createTool',
      'updateTool',
      'deleteTool',
      'deleteMultipleTools'
    ]);
    mockLookupService = jasmine.createSpyObj('ApiLookupService', ['getLookupCategory']);
    mockExcelService = jasmine.createSpyObj('ExcelExportService', ['exportToExcel']);

    mockToolService.getTools.and.returnValue(of({ items: [], total: 0 } as any));
    mockLookupService.getLookupCategory.and.returnValue(of([]));

    await TestBed.configureTestingModule({
      imports: [
        ToolsComponent,
        NoopAnimationsModule
      ],
      providers: [
        { provide: ApiToolService, useValue: mockToolService },
        { provide: ApiLookupService, useValue: mockLookupService },
        { provide: ExcelExportService, useValue: mockExcelService },
        ConfirmationService,
        MessageService
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ToolsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load tools on init', () => {
    expect(mockToolService.getTools).toHaveBeenCalled();
  });

  it('should load lookup data on init', () => {
    expect(mockLookupService.getLookupCategory).toHaveBeenCalledWith('inventory_statuses');
    expect(mockLookupService.getLookupCategory).toHaveBeenCalledWith('tool_categories');
    expect(mockLookupService.getLookupCategory).toHaveBeenCalledWith('tool_sub_categories');
  });

  it('should filter tools by search value', () => {
    component.tools = [
      makeTool({ id: 1, name: 'צלחת עגולה' }),
      makeTool({ id: 2, name: 'כוס שתייה' })
    ];

    component.searchValue = 'צלחת';
    component.applyFilters();

    expect(component.filteredTools.length).toBe(1);
    expect(component.filteredTools[0].name).toBe('צלחת עגולה');
  });

  it('should filter tools by inventory status', () => {
    component.tools = [
      makeTool({ id: 1, name: 'כלי1', inventoryStatus: 'במלאי' }),
      makeTool({ id: 2, name: 'כלי2', inventoryStatus: 'אין במלאי' })
    ];

    component.filterByInventoryStatus('אין במלאי');

    expect(component.filteredTools.length).toBe(1);
    expect(component.filteredTools[0].inventoryStatus).toBe('אין במלאי');
  });

  it('should filter tools by category', () => {
    component.tools = [
      makeTool({ id: 1, name: 'צלחת', category: 'צלחות' }),
      makeTool({ id: 2, name: 'כוס', category: 'כוסות' })
    ];

    component.filterByCategoryValue('צלחות');

    expect(component.filteredTools.length).toBe(1);
    expect(component.filteredTools[0].category).toBe('צלחות');
  });

  it('should clear all filters', () => {
    component.searchValue = 'test';
    component.filterInventoryStatus = 'במלאי';
    component.filterCategory = 'צלחות';
    component.filterSubCategory = 'אמיתי';

    component.clearFilters();

    expect(component.searchValue).toBe('');
    expect(component.filterInventoryStatus).toBe('');
    expect(component.filterCategory).toBe('');
    expect(component.filterSubCategory).toBe('');
  });

  it('should open new tool dialog with empty tool', () => {
    component.openNew();
    expect(component.toolDialog).toBeTrue();
    expect(component.submitted).toBeFalse();
    expect(component.tool.name).toBe('');
  });

  it('should set view mode to grid', () => {
    component.setViewMode('grid');
    expect(component.viewMode).toBe('grid');
  });

  it('should set view mode back to table', () => {
    component.viewMode = 'grid';
    component.setViewMode('table');
    expect(component.viewMode).toBe('table');
  });

  it('should toggle view from table to grid', () => {
    component.viewMode = 'table';
    component.toggleView();
    expect(component.viewMode).toBe('grid');
  });

  it('should toggle view from grid to table', () => {
    component.viewMode = 'grid';
    component.toggleView();
    expect(component.viewMode).toBe('table');
  });

  it('should populate tool when editTool is called', () => {
    const tool = makeTool({ id: 5, name: 'מגש הגשה' });
    component.editTool(tool);
    expect(component.toolDialog).toBeTrue();
    expect(component.tool.name).toBe('מגש הגשה');
  });

  it('should clear search value when clearSearch is called', () => {
    component.searchValue = 'חיפוש';
    component.clearSearch();
    expect(component.searchValue).toBe('');
  });
});
