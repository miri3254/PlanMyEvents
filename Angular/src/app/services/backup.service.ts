import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface BackupInfo {
  exists: boolean;
  size_bytes: number;
  size_mb: number;
  last_modified: string | null;
  path: string;
}

@Injectable({
  providedIn: 'root'
})
export class BackupService {
  private apiUrl = `${environment.apiUrl}/backup`;

  constructor(private http: HttpClient) {}

  /**
   * קבלת מידע על קובץ מסד הנתונים
   */
  getBackupInfo(): Observable<BackupInfo> {
    return this.http.get<BackupInfo>(`${this.apiUrl}/info`);
  }

  /**
   * הורדת גיבוי של מסד הנתונים
   */
  downloadBackup(): void {
    // פתיחת חלון חדש להורדת הגיבוי
    const url = `${this.apiUrl}/download`;
    window.open(url, '_blank');
  }

  /**
   * הורדת גיבוי עם Blob (אלטרנטיבה)
   */
  downloadBackupAsBlob(): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/download`, {
      responseType: 'blob'
    });
  }
}
