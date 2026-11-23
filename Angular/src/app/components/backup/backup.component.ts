import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BackupService, BackupInfo } from '../../services/backup.service';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';

@Component({
  selector: 'app-backup',
  standalone: true,
  imports: [
    CommonModule,
    ButtonModule,
    CardModule,
    ToastModule
  ],
  providers: [MessageService],
  template: `
    <div class="backup-container" dir="rtl">
      <p-card>
        <ng-template pTemplate="header">
          <div class="card-header">
            <i class="pi pi-download"></i>
            <h2>גיבוי נתונים</h2>
          </div>
        </ng-template>
        
        <div class="backup-info" *ngIf="backupInfo && backupInfo.exists">
          <div class="info-row">
            <i class="pi pi-database"></i>
            <span><strong>גודל מסד הנתונים:</strong> {{ backupInfo.size_mb }} MB</span>
          </div>
          <div class="info-row" *ngIf="backupInfo.last_modified">
            <i class="pi pi-clock"></i>
            <span><strong>עודכן לאחרונה:</strong> {{ backupInfo.last_modified }}</span>
          </div>
        </div>

        <div class="backup-actions">
          <p-button 
            label="הורד גיבוי"
            icon="pi pi-cloud-download"
            (onClick)="downloadBackup()"
            [loading]="isDownloading"
            [raised]="true"
            severity="success">
          </p-button>

          <p-button 
            label="רענן מידע"
            icon="pi pi-refresh"
            (onClick)="refreshInfo()"
            [loading]="isLoading"
            severity="secondary"
            [outlined]="true">
          </p-button>
        </div>

        <ng-template pTemplate="footer">
          <div class="backup-note">
            <i class="pi pi-info-circle"></i>
            <p>
              הגיבוי כולל את כל הנתונים במערכת: אירועים, מנות, מוצרים וכלים.
              מומלץ לבצע גיבוי קבוע של הנתונים.
            </p>
          </div>
        </ng-template>
      </p-card>

      <p-toast position="top-center" />
    </div>
  `,
  styles: [`
    .backup-container {
      padding: 2rem;
      max-width: 700px;
      margin: 0 auto;
    }

    .card-header {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 1.5rem;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border-radius: 8px 8px 0 0;
      margin: -1rem -1rem 0 -1rem;

      i {
        font-size: 2rem;
      }

      h2 {
        margin: 0;
        font-size: 1.75rem;
        font-weight: 600;
      }
    }

    .backup-info {
      margin: 1.5rem 0;
      padding: 1.25rem;
      background-color: #f8f9fa;
      border-radius: 8px;
      border-right: 4px solid #667eea;

      .info-row {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin: 0.75rem 0;
        font-size: 0.95rem;

        i {
          color: #667eea;
          font-size: 1.1rem;
        }

        &:first-child {
          margin-top: 0;
        }

        &:last-child {
          margin-bottom: 0;
        }
      }
    }

    .backup-actions {
      display: flex;
      gap: 1rem;
      margin: 1.5rem 0;
      flex-wrap: wrap;

      ::ng-deep p-button {
        flex: 1;
        min-width: 160px;

        button {
          width: 100%;
        }
      }
    }

    .backup-note {
      display: flex;
      gap: 1rem;
      padding: 1.25rem;
      background-color: #e3f2fd;
      border-radius: 8px;
      align-items: flex-start;

      i {
        color: #1976d2;
        flex-shrink: 0;
        font-size: 1.3rem;
        margin-top: 0.15rem;
      }

      p {
        margin: 0;
        font-size: 0.9rem;
        color: #424242;
        line-height: 1.6;
      }
    }

    @media (max-width: 600px) {
      .backup-container {
        padding: 1rem;
      }

      .backup-actions {
        flex-direction: column;

        ::ng-deep p-button {
          width: 100%;
        }
      }
    }
  `]
})
export class BackupComponent implements OnInit {
  backupInfo: BackupInfo | null = null;
  isLoading = false;
  isDownloading = false;

  constructor(
    private backupService: BackupService,
    private messageService: MessageService
  ) {}

  ngOnInit(): void {
    this.loadBackupInfo();
  }

  loadBackupInfo(): void {
    this.isLoading = true;
    this.backupService.getBackupInfo().subscribe({
      next: (info) => {
        this.backupInfo = info;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('שגיאה בטעינת מידע גיבוי:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'שגיאה',
          detail: 'לא ניתן לטעון מידע על הגיבוי'
        });
        this.isLoading = false;
      }
    });
  }

  refreshInfo(): void {
    this.loadBackupInfo();
  }

  downloadBackup(): void {
    this.isDownloading = true;
    
    // שימוש ב-Blob download לקובץ בינארי
    this.backupService.downloadBackupAsBlob().subscribe({
      next: (blob) => {
        // יצירת URL זמני לקובץ
        const url = window.URL.createObjectURL(blob);
        
        // יצירת קישור זמני והורדה
        const link = document.createElement('a');
        link.href = url;
        
        // שם הקובץ עם חותמת זמן
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
        link.download = `planmyevents_backup_${timestamp}.db`;
        
        // לחיצה על הקישור (הורדה)
        document.body.appendChild(link);
        link.click();
        
        // ניקוי
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
        this.messageService.add({
          severity: 'success',
          summary: 'הצלחה!',
          detail: 'הגיבוי הורד בהצלחה'
        });
        
        this.isDownloading = false;
      },
      error: (error) => {
        console.error('שגיאה בהורדת גיבוי:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'שגיאה',
          detail: 'לא ניתן להוריד את הגיבוי'
        });
        this.isDownloading = false;
      }
    });
  }
}
