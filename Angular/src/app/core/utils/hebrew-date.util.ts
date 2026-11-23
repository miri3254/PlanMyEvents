import { HDate } from '@hebcal/hdate';
import { HebrewDateParts } from '../models';

export interface HebrewMonthOption {
  value: number;
  label: string;
}

/* =========================
   Conversions & Rendering
========================= */

/**
 * הופך אובייקט Date לחלקי תאריך עברי
 */
export function toHebrewParts(date: Date): HebrewDateParts {
  const hd = new HDate(date);
  return {
    day: hd.getDate(),
    month: hd.getMonth(),
    year: hd.getFullYear(),
  };
}

/**
 * הופך חלקי תאריך עברי לאובייקט Date של JS
 */
export function hebrewPartsToGregorian(parts: HebrewDateParts): Date {
  return new HDate(parts.day, parts.month, parts.year).greg();
}

/**
 * מחזיר תאריך מלא בגימטריה (למשל: י"ח בתשרי תשפ"ו)
 */
export function renderHebrewLabelFromParts(parts: HebrewDateParts): string {
  return new HDate(parts.day, parts.month, parts.year).renderGematriya();
}

export function renderHebrewLabelFromDate(date: Date): string {
  return new HDate(date).renderGematriya();
}

/**
 * החזרת היום בלבד בגימטריה (א, ב... טו, טז...)
 */
export function hebrewDayToLetters(
  day: number,
  month?: number,
  year?: number
): string {
  // יוצרים אובייקט תאריך זמני כדי להשתמש במנגנון הרינדור של הספרייה
  const hd = (month && year) 
    ? new HDate(day, month, year) 
    : new HDate(day, 1, 5785);
    
  return hd.renderGematriya().split(' ')[0];
}

/**
 * החזרת השנה בגימטריה (למשל: תשפ״ו)
 */
export function hebrewYearToGematriya(year: number): string {
  const hd = new HDate(1, 1, year);
  const parts = hd.renderGematriya().split(' ');
  return parts[parts.length - 1];
}

/* =========================
   Months Logic (Corrected for Leap Years)
========================= */

/**
 * מחזיר את שם החודש בעברית לפי מספר החודש ב-hdate
 */
export function getHebrewMonthLabel(month: number, year: number): string {
  // month הוא 1-based לפי HDate
  if (!month || month < 1 || month > HDate.monthsInYear(year)) return '';
  const isLeap = HDate.isLeapYear(year);
  // טיפול מיוחד באדרים
  if (isLeap) {
    if (month === 6) return "אדר א'";
    if (month === 7) return "אדר ב'";
  } else {
    if (month === 6) return "אדר";
  }
  // שאר החודשים - שלוף מהספריה
  const hd = new HDate(1, month, year);
  const parts = hd.renderGematriya().split(' ');
  return parts.length > 1 ? parts[1] : '';
}

/**
 * בונה רשימת אפשרויות לבחירת חודש בסדר כרונולוגי
 */
export function buildHebrewMonthOptions(year: number): HebrewMonthOption[] {
  const isLeap = HDate.isLeapYear(year);
  const count = isLeap ? 13 : 12;
  const options: HebrewMonthOption[] = [];

  for (let m = 1; m <= count; m++) {
    options.push({
      value: m,
      label: getHebrewMonthLabel(m, year),
    });
  }

  return options;
}

export function formatHebrewMonthTitle(month: number, year: number): string {
  return `${getHebrewMonthLabel(month, year)} ${hebrewYearToGematriya(year)}`;
}

export function getHebrewMonthLength(month: number, year: number): number {
  return HDate.daysInMonth(month, year);
}

/* =========================
   Navigation & Validation
========================= */

export function shiftHebrewMonth(parts: HebrewDateParts, offset: number): HebrewDateParts {
  const hd = new HDate(1, parts.month, parts.year).add(offset, 'month');
  return {
    day: 1,
    month: hd.getMonth(),
    year: hd.getFullYear(),
  };
}

export function sanitizeHebrewParts(parts: Partial<HebrewDateParts>, fallbackYear: number): HebrewDateParts {
  const year = parts.year && parts.year > 0 ? parts.year : fallbackYear;
  const monthsInYear = HDate.monthsInYear(year);
  const month = parts.month && parts.month >= 1 && parts.month <= monthsInYear ? parts.month : 1;
  const maxDay = HDate.daysInMonth(month, year);
  const day = parts.day && parts.day >= 1 && parts.day <= maxDay ? parts.day : 1;
  return { day, month, year };
}

export function getHebrewYearsRange(centerYear: number, past = 1, future = 5): number[] {
  const years: number[] = [];
  for (let y = centerYear - past; y <= centerYear + future; y++) {
    years.push(y);
  }
  return years;
}