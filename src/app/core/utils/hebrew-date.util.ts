import { HDate } from '@hebcal/core';
import { HebrewDateParts } from '../models';

export interface HebrewMonthOption {
  value: number;
  label: string;
}

const MONTH_LABELS: Record<number, string> = {
  1: 'ניסן',
  2: 'אייר',
  3: 'סיון',
  4: 'תמוז',
  5: 'אב',
  6: 'אלול',
  7: 'תשרי',
  8: 'חשוון',
  9: 'כסלו',
  10: 'טבת',
  11: 'שבט',
  12: 'אדר א׳',
  13: 'אדר ב׳'
};

export function toHebrewParts(date: Date): HebrewDateParts {
  const hd = new HDate(date);
  return {
    day: hd.getDate(),
    month: hd.getMonth(),
    year: hd.getFullYear()
  };
}

export function hebrewPartsToGregorian(parts: HebrewDateParts): Date {
  const hd = new HDate(parts.day, parts.month, parts.year);
  return hd.greg();
}

export function renderHebrewLabelFromDate(date: Date): string {
  const hd = new HDate(date);
  return hd.renderGematriya(false, false);
}

export function renderHebrewLabelFromParts(parts: HebrewDateParts): string {
  const hd = new HDate(parts.day, parts.month, parts.year);
  return hd.renderGematriya(false, false);
}

export function getHebrewMonthLabel(month: number, year: number): string {
  if (month === 12 && !HDate.isLeapYear(year)) {
    return 'אדר';
  }
  return MONTH_LABELS[month] || '';
}

export function buildHebrewMonthOptions(year: number): HebrewMonthOption[] {
  const monthsInYear = HDate.monthsInYear(year);
  const options: HebrewMonthOption[] = [];
  for (let month = 1; month <= monthsInYear; month++) {
    options.push({
      value: month,
      label: getHebrewMonthLabel(month, year)
    });
  }
  return options;
}

export function getHebrewYearsRange(centerYear: number, past = 1, future = 5): number[] {
  const years: number[] = [];
  for (let offset = -past; offset <= future; offset++) {
    years.push(centerYear + offset);
  }
  return years;
}

export function sanitizeHebrewParts(parts: Partial<HebrewDateParts>, fallbackYear: number): HebrewDateParts {
  const year = parts.year && parts.year > 0 ? parts.year : fallbackYear;
  const monthsInYear = HDate.monthsInYear(year);
  const month = parts.month && parts.month >= 1 && parts.month <= monthsInYear ? parts.month : 1;
  const maxDay = HDate.daysInMonth(month, year);
  const day = parts.day && parts.day >= 1 && parts.day <= maxDay ? parts.day : 1;
  return { day, month, year };
}

export function formatHebrewMonthTitle(month: number, year: number): string {
  const label = getHebrewMonthLabel(month, year);
  return label ? `${label} ${year}` : `${year}`;
}

export function getHebrewMonthLength(month: number, year: number): number {
  return HDate.daysInMonth(month, year);
}

export function shiftHebrewMonth(parts: HebrewDateParts, offset: number): HebrewDateParts {
  const base = new HDate(1, parts.month, parts.year).add(offset, 'month');
  return {
    day: 1,
    month: base.getMonth(),
    year: base.getFullYear()
  };
}
