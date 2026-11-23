import { Injectable } from '@angular/core';
import { Observable, EMPTY, expand, reduce } from 'rxjs';
import { BaseApiService } from '../core/services/base-api.service';
import { 
  ApiTool, 
  ToolCreate, 
  ToolUpdate,
  ToolsQueryParams,
  ApiResponse
} from '../core/models/api.models';

@Injectable({
  providedIn: 'root'
})
export class ApiToolService extends BaseApiService {

  // Tools CRUD
  getTools(params?: ToolsQueryParams): Observable<ApiResponse<ApiTool>> {
    return this.get<ApiResponse<ApiTool>>('/tools', params);
  }

  getAllTools(): Observable<ApiTool[]> {
    return this.getTools({limit: 200}).pipe(
      expand(page => page.skip + page.items.length < page.total && page.items.length > 0
        ? this.getTools({limit: 200, skip: page.skip + page.items.length}) : EMPTY),
      reduce((items: ApiTool[], page) => [...items, ...page.items], [])
    );
  }

  getTool(toolId: number): Observable<ApiTool> {
    return this.get<ApiTool>(`/tools/${toolId}`);
  }

  createTool(tool: ToolCreate): Observable<ApiTool> {
    return this.post<ApiTool>('/tools', tool);
  }

  updateTool(toolId: number, tool: ToolUpdate): Observable<ApiTool> {
    return this.put<ApiTool>(`/tools/${toolId}`, tool);
  }

  deleteTool(toolId: number): Observable<void> {
    return this.delete<void>(`/tools/${toolId}`);
  }

  // Bulk Operations
  createMultipleTools(tools: ToolCreate[]): Observable<{ message: string; success: boolean; count: number }> {
    return this.post<{ message: string; success: boolean; count: number }>('/tools/bulk', tools);
  }

  deleteMultipleTools(toolIds: number[]): Observable<{ message: string; deleted_count: number; success: boolean }> {
    return this.delete<{ message: string; deleted_count: number; success: boolean }>(`/tools/bulk?ids=${toolIds.join(',')}`);
  }
}
