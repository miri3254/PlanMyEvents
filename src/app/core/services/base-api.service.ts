import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class BaseApiService {
  protected baseUrl = environment.apiUrl;

  constructor(protected http: HttpClient) {}

  protected buildParams(params: { [key: string]: any }): HttpParams {
    let httpParams = new HttpParams();
    
    Object.keys(params).forEach(key => {
      const value = params[key];
      if (value !== null && value !== undefined && value !== '') {
        if (Array.isArray(value)) {
          value.forEach(item => {
            httpParams = httpParams.append(key, item.toString());
          });
        } else {
          httpParams = httpParams.set(key, value.toString());
        }
      }
    });
    
    return httpParams;
  }

  protected get<T>(endpoint: string, params?: { [key: string]: any }): Observable<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const httpParams = params ? this.buildParams(params) : undefined;
    
    return this.http.get<T>(url, { params: httpParams });
  }

  protected post<T>(endpoint: string, body: any): Observable<T> {
    const url = `${this.baseUrl}${endpoint}`;
    return this.http.post<T>(url, body);
  }

  protected put<T>(endpoint: string, body: any): Observable<T> {
    const url = `${this.baseUrl}${endpoint}`;
    return this.http.put<T>(url, body);
  }

  protected patch<T>(endpoint: string, body: any): Observable<T> {
    const url = `${this.baseUrl}${endpoint}`;
    return this.http.patch<T>(url, body);
  }

  protected delete<T>(endpoint: string): Observable<T> {
    const url = `${this.baseUrl}${endpoint}`;
    return this.http.delete<T>(url);
  }
}