import { Injectable } from '@angular/core';
import * as XLSX from 'xlsx';

export interface ExcelSheet {
  name: string;
  headers: string[];
  rows: (string | number)[][];
}

@Injectable({ providedIn: 'root' })
export class ExcelExportService {

  /**
   * יוצר קובץ Excel עם גליון אחד או יותר
   */
  exportSheets(sheets: ExcelSheet[], filename: string): void {
    const wb = XLSX.utils.book_new();

    for (const sheet of sheets) {
      const ws = XLSX.utils.aoa_to_sheet([sheet.headers, ...sheet.rows]);

      // עיצוב כותרות - רוחב עמודות אוטומטי
      const colWidths = sheet.headers.map((h, colIdx) => {
        const maxLen = Math.max(
          h.length,
          ...sheet.rows.map(r => String(r[colIdx] ?? '').length)
        );
        return { wch: Math.min(maxLen + 4, 50) };
      });
      ws['!cols'] = colWidths;

      XLSX.utils.book_append_sheet(wb, ws, sheet.name);
    }

    XLSX.writeFile(wb, filename);
  }

  /** מחזיר תאריך היום בפורמט DD-MM-YYYY */
  todayString(): string {
    const today = new Date();
    return `${today.getDate().toString().padStart(2, '0')}-${(today.getMonth() + 1).toString().padStart(2, '0')}-${today.getFullYear()}`;
  }
}
