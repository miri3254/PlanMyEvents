import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
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

  getTool(toolId: string): Observable<ApiTool> {
    return this.get<ApiTool>(`/tools/${toolId}`);
  }

  createTool(tool: ToolCreate): Observable<ApiTool> {
    return this.post<ApiTool>('/tools', tool);
  }

  updateTool(toolId: string, tool: ToolUpdate): Observable<ApiTool> {
    return this.put<ApiTool>(`/tools/${toolId}`, tool);
  }

  deleteTool(toolId: string): Observable<void> {
    return this.delete<void>(`/tools/${toolId}`);
  }

  // Bulk Operations
  createMultipleTools(tools: ToolCreate[]): Observable<ApiTool[]> {
    return this.post<ApiTool[]>('/tools/bulk', tools);
  }

  deleteMultipleTools(toolIds: string[]): Observable<void> {
    return this.delete<void>(`/tools/bulk?ids=${toolIds.join(',')}`);
  }
}