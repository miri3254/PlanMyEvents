# תצוגת תאריכים עברים - מדריך טכני

## סיכום השינויים

### 1. תצוגת ימים עברים (1-30)
בלוח החודש, במקום להציג את מספר היום (1, 2, 3...), מוצגות כעת האותיות העבריות:

#### התאמת מספרים לאותיות:
- 1-10: א, ב, ג, ד, ה, ו, ז, ח, ט, י
- 11-19: יא, יב, יג, יד, **טו**, טז, יז, יח, יט
- 20-30: כ, כא, כב, כג, כד, כה, כו, כז, כח, כט, ל

**הערה חשובה:** לפי המסורת, ה-15 וה-16 כתובים כ"טו" ו"טז" (לא "ט״ו" ו"ט״ז") כדי להימנע מכתיבת שם האלוקים.

**קובץ הטמפלייט:**
```html
<span class="day-number hebrew">
  {{ getHebrewDayDisplay(day.hebrewDay) }}
</span>
```

**פונקציית ההמרה:**
```typescript
export function hebrewDayToLetters(
  day: number,
  month?: number,
  year?: number
): string {
  const hd = month && year
    ? new HDate(day, month, year)
    : new HDate(day, 1, 5785); // fallback safe year

  return hd.renderGematriya().split(' ')[0];
}
```

### 2. תצוגת שנים עברות בגימטריה
בלוח החודש ובבחירות השנה, השנה העברית מוצגת בגימטריה (numeral gematriya):

#### דוגמאות:
- 5786 → תשפ"ו (תשעים וששה)
- 5785 → תשפ"ה (תשעים וחמישה)
- 5784 → תשפ"ד (תשעים וארבעה)

**קוד המרה:**
```typescript
export function hebrewYearToGematriya(year: number): string {
  const hd = new HDate(1, 1, year);
  const parts = hd.renderGematriya().split(' ');
  return parts[parts.length - 1];
}
```

**השימוש בכותרת:**
```typescript
export function formatHebrewMonthTitle(month: number, year: number): string {
  const label = getHebrewMonthLabel(month, year);
  const yearGematriya = hebrewYearToGematriya(year);
  return label ? `${label} ${yearGematriya}` : `${yearGematriya}`;
}
```

### 3. ספרייה hebCal
הקוד משתמש בספרייית `@hebcal/core` שכוללת:

- **HDate** - אובייקט להמרת תאריכים
- **renderGematriya()** - המרה לגימטריה
- **getDate()** - קבלת היום
- **getMonth()** - קבלת החודש
- **getFullYear()** - קבלת השנה
- **isLeapYear()** - בדיקה אם שנה מעוברת
- **monthsInYear()** - מספר חודשים בשנה
- **daysInMonth()** - מספר ימים בחודש

### 4. פונקציות בקובץ hebrew-date.util.ts

#### פונקציות זמינות:
1. **hebrewDayToLetters(day, month?, year?)** - המרה של יום לאותיות (backward compatible)
2. **hebrewYearToGematriya(year)** - המרה של שנה לגימטריה
3. **toHebrewParts(date)** - המרת תאריך לועזי לחלקי תאריך עברי
4. **hebrewPartsToGregorian(parts)** - המרת חלקי תאריך עברי לתאריך לועזי
5. **renderHebrewLabelFromDate(date)** / **renderHebrewLabelFromParts(parts)** - תוויות עבריות
6. **getHebrewMonthLabel(month, year)** - שם החודש העברי
7. **buildHebrewMonthOptions(year)** - רשימת אפשרויות חודשים לשנה
8. **formatHebrewMonthTitle(month, year)** - כותרת חודש עם שנה בגימטריה
9. **getHebrewMonthLength(month, year)** - מספר ימים בחודש
10. **shiftHebrewMonth(parts, offset)** - ניווט בחודשים
11. **sanitizeHebrewParts(parts, fallbackYear)** - ולידציה של חלקי תאריך
12. **getHebrewYearsRange(centerYear, past, future)** - טווח שנים עבריות

> ⚠️ **חשוב:** אין להשתמש יותר בטבלאות חודשים, חישוב גימטריה ידני, או הורדת 3760 מהשנה!

### 5. עדכונים בקומפוננט

#### events.component.ts:
```typescript
// הוספת פונקציה לתצוגה
getHebrewDayDisplay(day: number): string {
  return hebrewDayToLetters(day);
}

// עדכון בחירות השנים
private buildHebrewYearOptions(centerYear: number): { label: string; value: number }[] {
  return getHebrewYearsRange(centerYear, 2, 6).map((year: number) => ({
    label: hebrewYearToGematriya(year),
    value: year
  }));
}
```

#### events.component.html:
```html
<span class="day-number hebrew">
  {{ getHebrewDayDisplay(day.hebrewDay) }}
</span>
```

### 6. עיצוב (SCSS)
הוסף עיצוב מיוחד לאותיות עבריות:
```scss
.day-number.hebrew {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  letter-spacing: 0px;
}
```

## דוגמה של תצוגה בלוח

| יום לועזי | יום עברי | אירועים |
|---------|--------|--------|
| 14      | יד      | אירוע 1 |
| 15      | טו      | -       |
| 16      | טז      | אירוע 2 |
| 20      | כ       | -       |
| 21      | כא      | אירוע 3 |

## בדיקות

✅ **בדוק את התצוגה:**
1. כנס ללוח אירועים
2. בדוק שהימים מוצגים באותיות עבריות
3. בדוק שהשנה בחודש מוצגת בגימטריה
4. בדוק את בחירות השנים בטופס - גם הן בגימטריה

## הערות לעדכון עתידי

אם תרצה להוסיף עוד תאריכים עברים:
1. עדכן את `HEBREW_DAYS` בקובץ hebrew-date.util.ts
2. כל השאר יתעדכן אוטומטית!

## קישורים לתיעוד

- [@hebcal/core Documentation](https://github.com/yahuda-g/hebcal-js)
- Gematriya - מערכת המספור העברית
