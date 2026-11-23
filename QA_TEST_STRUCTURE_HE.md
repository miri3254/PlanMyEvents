# PlanMyEvents - מבנה בדיקות מקיף לפני מסירה ללקוח

מטרת המסמך: להגדיר תוכנית בדיקות ברמת מסירה ללקוח למערכת PlanMyEvents, כך שהמערכת תותקף מכל שכבה: UI, API, DB, חישובים עסקיים, PDF, RTL, נתונים, ביצועים, אבטחה, התאוששות, התקנה ושימוש אמיתי.

המערכת שנבדקת:
- Frontend: Angular, Angular Material, PrimeNG, Chart.js, xlsx.
- Backend: FastAPI, SQLAlchemy, SQLite.
- מודולים מרכזיים: Dashboard, Events, Dishes, Products, Tools, Menus, Settings, Backup, Unit Conversions, Receipts, Event Calculations, PDF outputs.
- קבצי בדיקות קיימים: `FastAPI/tests/test_comprehensive.py`, `FastAPI/tests/test_event_calculations.py`, `FastAPI/tests/test_delivery_sheet_pdf.py`, `Angular/tests/events.spec.ts`, `Angular/tests/example.spec.ts`.

## 1. עקרונות בדיקה

### 1.1 רמות חומרה

| רמה | משמעות | חסימה למסירה |
|---|---|---|
| P0 | אובדן נתונים, חישוב קריטי שגוי, קריסה, PDF לא שמיש, אי יכולת ליצור אירוע | כן |
| P1 | פעולה מרכזית עובדת חלקית, תצוגה מטעה, מלאי/מחיר/כמות לא עקביים | כן |
| P2 | בעיית UX, שגיאה לא ברורה, איטיות נקודתית, שדה לא נוח | לפי החלטה |
| P3 | קוסמטיקה, ניסוח, שיפור נוחות | לא, אלא אם הלקוח דרש |

### 1.2 שערי איכות למסירה

אין למסור ללקוח אם אחד מהתנאים הבאים מתקיים:
- אי אפשר ליצור אירוע מלא מהתחלה עד הפקת PDF.
- חישוב קניות, ציוד או מחירים לא יציב בין רענונים.
- אירוע מאושר משתנה בדיעבד בניגוד לכללי snapshot.
- מחיקה/עדכון משאירים נתונים יתומים שפוגעים במסכים אחרים.
- PDF בעברית יוצא הפוך, חתוך, ריק או לא קריא.
- גיבוי/שחזור לא נבדקו על עותק אמיתי.
- בדיקות backend או build frontend נכשלות.
- יש שגיאות console קריטיות במסכים ראשיים.

### 1.3 פירמידת בדיקות מומלצת

| שכבה | יעד כיסוי | סוג |
|---|---:|---|
| Unit backend | 85% בלוגיקה עסקית | pytest |
| API integration | 100% endpoints מרכזיים | FastAPI TestClient |
| DB integrity | 100% קשרים קריטיים | pytest + SQLite temp DB |
| Frontend unit | 70% קומפוננטות ושירותים | Angular/Karma |
| E2E | 100% מסעות משתמש קריטיים | Playwright |
| PDF visual regression | 100% מסמכי לקוח | render + image compare |
| Security smoke | 100% endpoints כתיבה/מחיקה | scripts |
| Performance smoke | מסכים ודוחות כבדים | k6/Locust/Playwright |

## 2. מפת מודולים וסיכונים

| מודול | סיכון עסקי | מה חייב להיבדק |
|---|---|---|
| Events | לב המערכת | יצירה, עריכה, סטטוס, מחיר, תאריך, כמות אורחים, הוספת מנות, אישור, snapshot |
| Dishes | משפיע על חישובים | רכיבים, כלי הגשה, ציוד, סטים, חוקי חישוב, פעיל/לא פעיל |
| Products | מלאי ועלויות | CRUD, מלאי נמוך, מחיר יחידה, יחידות, קטגוריות, bulk |
| Tools | ציוד לאירוע | CRUD, מלאי, חסרים, שימוש באירוע, bulk |
| Menus | בחירת תפריט | תבניות, סוגי תפריטים, קטגוריות, מיפוי מנות, שינוי שם תפריט |
| Calculations | הכי קריטי | משקאות, לחמניות, מפות, ציוד, עלויות, rounding, snapshot |
| Shopping list | ביצוע בפועל | איחוד מוצרים, קיזוז מלאי, כמות לקנייה, מחיר משוער |
| Equipment list | ביצוע בפועל | כלי הגשה, מפות, ציוד ידני, חסרים במלאי |
| PDF | מסירה ללקוח/צוות | תעודת משלוח, מלצרים, קייטרינג, רשימת קניות, עברית, עמודים |
| Receipts | עדכון מלאי | OCR/AI, התאמת מוצרים, bulk update, טעויות זיהוי |
| Dashboard | ניהול | סטטיסטיקות, אירועים קרובים, מלאי נמוך, רווחיות, גרפים |
| Backup | התאוששות | יצירה, הורדה, מידע, שחזור ידני, קבצים נעולים |
| Lookup/Settings | נתוני בסיס | ערכים דינמיים, סדר, הוספה/עדכון/מחיקה |
| Unit conversions | דיוק כמויות | המרות מערכת/משתמש, חישוב, מחיקת המרת מערכת |

## 3. מסעות משתמש E2E שחייבים לעבור

### 3.1 מסע מלא: אירוע חדש עד הפקת מסמכים

1. פתיחת Dashboard.
2. מעבר לאירועים.
3. יצירת אירוע עם:
   - שם בעברית.
   - קטגוריה.
   - סוג תפריט.
   - תאריך עתידי.
   - כמות אורחים.
   - הערות.
4. שמירה ובדיקה שהאירוע מופיע ברשימה.
5. כניסה לאירוע.
6. מעבר לבחירת מנות.
7. הוספת מנות מכמה קטגוריות.
8. שינוי כמויות למנה בודדת.
9. הסרת מנה.
10. הוספת מנה מחדש.
11. שמירה/Finalize.
12. פתיחת סיכום חישובים.
13. שינוי הגדרות חישוב:
    - צורת שולחן: עגול/מלבן.
    - חלוקת לחמניות.
    - חיוב אשראי.
    - ציוד ידני.
14. Recalculate.
15. בדיקת רשימת קניות.
16. בדיקת רשימת ציוד.
17. שינוי מחיר אירוע.
18. אישור אירוע.
19. הפקת PDF:
    - תעודת משלוח.
    - דף מלצרים.
    - דף קייטרינג.
    - רשימת קניות.
20. רענון דפדפן.
21. וידוא שכל הנתונים נשמרו.
22. שינוי מלאי מוצר אחרי אישור.
23. וידוא ש-snapshot של אירוע מאושר לא משתנה אם זה הכלל העסקי.

קריטריון מעבר: אין שגיאות UI, אין שגיאות console, כל PDF נפתח, כל הכמויות עקביות בין המסך ל-PDF.

### 3.2 מסע מלאי

1. יצירת מוצר חדש.
2. הכנסת מלאי נוכחי, סף מינימום, יחידה ומחיר.
3. בדיקת הופעה במוצרים.
4. בדיקת חיפוש/סינון.
5. הורדת כמות מתחת למינימום.
6. בדיקת low stock במוצרים ובדשבורד.
7. שימוש במוצר במנה.
8. שימוש במנה באירוע.
9. בדיקת קיזוז מלאי ברשימת קניות.
10. מחיקת מוצר שנמצא בשימוש.
11. בדיקה שהמערכת חוסמת מחיקה או מטפלת בלי לשבור חישובים.

### 3.3 מסע כלי/ציוד

1. יצירת כלי חדש.
2. הגדרת מלאי וסף מינימום.
3. שיוך כלי למנה.
4. שיוך סט הגשה למנה.
5. יצירת אירוע עם המנה.
6. בדיקת רשימת ציוד.
7. בדיקת חסר במלאי.
8. שינוי כמות מלאי ובדיקה שהחישוב מתעדכן.
9. אישור אירוע ובדיקת snapshot.

### 3.4 מסע תפריטים

1. יצירת תבנית תפריט.
2. הוספת sub meal.
3. הוספת קטגוריות.
4. מיפוי מנות לקטגוריות.
5. בדיקת validate לקטגוריה.
6. יצירת אירוע לפי סוג תפריט.
7. שינוי שם תפריט.
8. בדיקה שאירועים ישנים עדיין נפתחים.
9. בדיקה שאירועים חדשים משתמשים בשם החדש.

### 3.5 מסע קבלה וסריקת מלאי

1. העלאת קבלה תקינה.
2. העלאת קובץ תמונה גדול.
3. העלאת PDF.
4. העלאת קובץ לא נתמך.
5. בדיקת תוצאות זיהוי.
6. התאמת מוצרים קיימים.
7. יצירת מוצר חדש מתוך שורה לא מזוהה.
8. Bulk update למלאי.
9. ביטול שורה.
10. בדיקה שלא עודכן מלאי כפול ברענון.

### 3.6 מסע גיבוי

1. יצירת גיבוי.
2. בדיקת רשימת גיבויים.
3. בדיקת מידע על גיבוי אחרון.
4. הורדת גיבוי.
5. פתיחת קובץ הגיבוי בסביבת בדיקה.
6. בדיקת תקינות טבלאות וספירת רשומות.
7. בדיקת מצב כשה-DB נעול.
8. בדיקת מצב שאין הרשאות כתיבה לתיקיית backup.

## 4. בדיקות API לפי endpoint

לכל endpoint לבצע לפחות את המטריצה הבאה:
- 200/201 לנתיב תקין.
- 400/422 לקלט שגוי.
- 404 ל-id לא קיים.
- בדיקת schema מלא של response.
- בדיקת type לכל שדה.
- בדיקת תווים בעברית.
- בדיקת ערכים ריקים/null.
- בדיקת מספרים שליליים.
- בדיקת מספרים גדולים במיוחד.
- בדיקת pagination/sort/filter אם קיים.
- בדיקת idempotency איפה שרלוונטי.
- בדיקת side effects ב-DB.

### 4.1 Health

| בדיקה | Endpoint | ציפייה |
|---|---|---|
| root | `GET /` | הודעת מערכת |
| health | `GET /api/health` | `status=ok` |
| unknown | `GET /api/not-real` | 404 |

### 4.2 Events

Endpoints:
- `GET /api/events`
- `GET /api/events/range`
- `GET /api/events/delivery-note-templates`
- `GET /api/events/{event_id}`
- `POST /api/events`
- `PUT /api/events/{event_id}`
- `DELETE /api/events/{event_id}`
- `PATCH /api/events/{event_id}/status`
- `PATCH /api/events/{event_id}/price`
- `POST /api/events/{event_id}/dishes`
- `PUT /api/events/{event_id}/dishes/{dish_id}`
- `DELETE /api/events/{event_id}/dishes/{dish_id}`
- `POST /api/events/{event_id}/dishes/bulk`
- `POST /api/events/{event_id}/dishes/finalize`
- `POST /api/events/{event_id}/trays`
- `PUT /api/events/{event_id}/trays/{tray_id}`
- `DELETE /api/events/{event_id}/trays/{tray_id}`
- `PATCH /api/events/{event_id}/morning-split`
- `POST /api/events/{event_id}/restore-stock`
- `GET /api/events/{event_id}/calculations/summary`
- `PUT /api/events/{event_id}/calculations/settings`
- `PUT /api/events/{event_id}/calculations/dish-serving-selections`
- `PUT /api/events/{event_id}/calculations/manual-tools`
- `POST /api/events/{event_id}/calculations/recalculate`
- `GET /api/events/{event_id}/shopping-list`
- `GET /api/events/{event_id}/equipment-list`
- `GET /api/events/{event_id}/delivery-sheet/pdf`
- `GET /api/events/{event_id}/waiter-pdf`
- `GET /api/events/{event_id}/catering-pdf`
- `GET /api/events/{event_id}/shopping-pdf`

בדיקות חובה:
- יצירת אירוע מינימלי.
- יצירת אירוע מלא עם כל השדות.
- יצירת אירוע עם שם בעברית, גרשיים, סוגריים, מקף, מספרים.
- יצירת אירוע עם `guest_count=0`, `1`, `2`, `9`, `10`, `49`, `50`, `80`, `120`, `300`, `9999`.
- יצירת אירוע ללא `name`.
- יצירת אירוע ללא `menu_type`.
- יצירת אירוע ללא `date`.
- יצירת אירוע עם date לא תקין.
- יצירת אירוע עם date בעבר.
- יצירת אירוע עם date עתידי רחוק.
- עדכון חלקי של שדה אחד בלבד.
- עדכון כמה שדות יחד.
- עדכון `guest_count` אחרי שיש מנות.
- עדכון `menu_type` אחרי בחירת מנות.
- שינוי סטטוס: טיוטה -> מאושר.
- שינוי סטטוס: מאושר -> בוטל.
- שינוי סטטוס לא חוקי.
- שינוי מחיר ידני.
- מחיר שלילי.
- מחיר 0.
- מחיר עם אגורות.
- הוספת מנה לאירוע.
- הוספת אותה מנה פעמיים.
- שינוי כמות מנה.
- כמות מנה 0.
- כמות מנה שלילית.
- מחיקת מנה מאירוע.
- bulk add עם מערך ריק.
- bulk add עם id לא קיים.
- finalize ללא מנות.
- finalize עם מנות תקינות.
- trays CRUD.
- morning split תקין.
- morning split מעל 100%.
- morning split שלילי.
- restore stock לפני אישור.
- restore stock אחרי אישור.
- מחיקת אירוע עם מנות/מגשים/חישובים.
- וידוא שאין orphan rows אחרי מחיקה.

### 4.3 Dishes

Endpoints:
- `GET /api/dishes`
- `GET /api/dishes/{dish_id}`
- `POST /api/dishes`
- `PUT /api/dishes/{dish_id}`
- `DELETE /api/dishes/{dish_id}`
- `PATCH /api/dishes/{dish_id}/active`
- `POST/PUT/DELETE /api/dishes/{dish_id}/ingredients`
- `POST/PUT/DELETE /api/dishes/{dish_id}/serving-dishes`
- `POST/PUT/DELETE /api/dishes/{dish_id}/equipment`
- `GET/POST/PUT/DELETE /api/dishes/{dish_id}/serving-sets`
- `GET/POST/PUT/DELETE /api/dishes/{dish_id}/calculation-rules`

בדיקות חובה:
- מנה מינימלית.
- מנה מלאה.
- שם מנה כפול.
- שם ריק.
- kosher type חלבי/בשרי/פרווה.
- base price שלילי/0/גבוה.
- serving size שלילי/0/1/גדול.
- מנה לא פעילה לא מופיעה בבחירה לאירוע.
- מנה לא פעילה עדיין קיימת באירוע ישן אם כבר נבחרה.
- הוספת רכיב עם מוצר קיים.
- הוספת רכיב עם מוצר לא קיים.
- כמות רכיב 0/שלילית/שברית.
- יחידה לא תואמת למוצר.
- מחיקת רכיב שמשמש בחישוב.
- הוספת כלי הגשה.
- הוספת ציוד.
- הוספת serving set.
- בחירת serving set באירוע.
- חוק חישוב לפי אורחים.
- חוק חישוב לפי מנה.
- חוק חישוב עם rounding up.
- חוק חישוב עם rounding down.
- חוק חישוב עם min/max.

### 4.4 Products

Endpoints:
- `GET /api/products`
- `GET /api/products/low-stock`
- `GET /api/products/{product_id}`
- `POST /api/products`
- `PUT /api/products/{product_id}`
- `DELETE /api/products/{product_id}`
- `POST /api/products/bulk`
- `DELETE /api/products/bulk`

בדיקות חובה:
- CRUD מלא.
- חיפוש לפי שם בעברית.
- סינון לפי קטגוריה.
- סינון לפי kosher type.
- pagination.
- sort אם קיים.
- price per unit: ריק, 0, שבר, גבוה, שלילי.
- quantity in stock: 0, 1, min-1, min, min+1.
- inventory status: תקין/נמוך/אין במלאי.
- bulk create עם 0/1/100/1000 פריטים.
- bulk create עם חלק תקינים וחלק שגויים.
- bulk delete עם id כפול.
- bulk delete עם id לא קיים.
- מחיקה של מוצר שמשויך לרכיב במנה.
- עדכון יחידה של מוצר שמשמש בחישוב.
- עדכון מחיר שמשפיע על estimated price.

### 4.5 Tools

Endpoints:
- `GET /api/tools`
- `GET /api/tools/low-stock`
- `GET /api/tools/{tool_id}`
- `POST /api/tools`
- `PUT /api/tools/{tool_id}`
- `DELETE /api/tools/{tool_id}`
- `POST /api/tools/bulk`
- `DELETE /api/tools/bulk`

בדיקות חובה:
- CRUD מלא.
- category/sub_category.
- מלאי נמוך.
- כלי עם מלאי 0.
- כלי שנדרש באירוע יותר מהמלאי.
- bulk עם כפילויות.
- מחיקה של כלי שמשויך למנה.
- שינוי שם כלי אחרי שאירוע אושר.
- שינוי מלאי אחרי snapshot.

### 4.6 Menus

Endpoints:
- `GET /api/menus`
- `GET /api/menus/by-type/{menu_type}`
- `GET /api/menus/{template_id}`
- `POST /api/menus`
- `PUT /api/menus/{template_id}`
- `DELETE /api/menus/{template_id}`
- `GET/POST/PUT/DELETE /api/menus/sub-meals`
- `GET/POST/PUT/DELETE /api/menus/categories`
- `POST /api/menus/categories/{category_id}/validate`
- `POST/PUT/DELETE /api/menus/dish-mappings`

בדיקות חובה:
- יצירת תפריט עם type ייחודי.
- יצירת תפריט עם type כפול.
- שינוי שם תפריט.
- lookup לפי type ישן ושם חדש אם נתמך.
- מחיקת תפריט שמשמש אירוע.
- תפריט בלי קטגוריות.
- קטגוריה בלי מנות.
- קטגוריה עם מנה לא פעילה.
- validate עם mapping חסר.
- mapping כפול לאותה מנה.
- שינוי סדר קטגוריות.
- שינוי סדר sub meals.

### 4.7 Unit Conversions

בדיקות חובה:
- seed ראשוני.
- seed כפול לא יוצר כפילויות.
- המרת ק"ג לגרם.
- המרת גרם לק"ג.
- המרת יחידות לאריזה.
- המרה לא קיימת.
- המרה בין קטגוריות לא תואמות.
- factor 0.
- factor שלילי.
- factor שברי.
- מחיקת המרת system חסומה.
- מחיקת המרת user מותרת.
- עדכון המרת user.
- שימוש בהמרה בתוך חישוב אירוע.

### 4.8 Receipts

בדיקות חובה:
- scan קובץ תמונה תקין.
- scan PDF תקין.
- scan קובץ ריק.
- scan קובץ גדול.
- scan קובץ עם עברית מטושטשת.
- scan קובץ לא נתמך.
- AI/OCR לא זמין.
- תוצאה עם מוצר מזוהה.
- תוצאה עם מוצר לא מזוהה.
- bulk update מלאי.
- bulk update חלקי.
- bulk update כפול.
- בדיקה שלא מתבצע עדכון מלאי אם scan נכשל.

### 4.9 Dashboard

בדיקות חובה:
- stats בלי נתונים.
- stats עם אירועים, מוצרים, כלים.
- upcoming לפי תאריך.
- upcoming לא מציג אירועים שבוטלו אם זה הכלל.
- low stock מוצרים וכלים.
- revenue לפי טווח.
- profitability לפי טווח.
- charts עם טווח ריק.
- inventory אחרי עדכון מלאי.
- dashboard לא קורס אם endpoint אחד נכשל.

### 4.10 Backup

בדיקות חובה:
- יצירת גיבוי.
- רשימת גיבויים.
- מידע על גיבוי אחרון.
- הורדת קובץ.
- בדיקה שהקובץ לא ריק.
- בדיקה שניתן לפתוח SQLite.
- בדיקה שכל הטבלאות קיימות.
- בדיקה שהגיבוי לא כולל קבצים זמניים כמו wal/shm בלבד.
- DB נעול.
- תיקיית יעד לא קיימת.
- אין הרשאות כתיבה.

## 5. בדיקות חישובים עסקיים

### 5.1 עקרונות

כל חישוב חייב להיבדק בשלושה מקומות:
- שירות backend ישירות.
- API summary.
- UI/PDF שמציג את התוצאה.

כל נוסחה חייבת לכלול:
- שם נוסחה.
- קלטים.
- תוצאה צפויה.
- rounding צפוי.
- מקור מלאי אם יש.
- מחיר צפוי.

### 5.2 מטריצת כמויות אורחים

להריץ את כל חישובי האירוע על הכמויות:

`0, 1, 2, 3, 4, 5, 9, 10, 11, 19, 20, 24, 25, 49, 50, 51, 74, 75, 76, 79, 80, 81, 99, 100, 101, 119, 120, 121, 179, 180, 181, 249, 250, 251, 299, 300, 301, 500, 999, 1000, 5000`

לכל כמות לבדוק:
- drinks.
- rolls.
- tablecloths.
- manual tools.
- serving dishes.
- product requirements.
- equipment requirements.
- total estimated cost.
- need_to_buy_quantity.

### 5.3 משקאות

בדיקות חובה:
- אירוע רגיל.
- אירוע מתוק.
- אירוע קטן מאוד.
- אירוע גדול.
- rounding למעלה.
- rounding למטה אם קיים.
- מלאי חלקי.
- מלאי גבוה מהצורך.
- מוצר משקה לא קיים במלאי.
- מוצר משקה קיים עם מחיר.
- מוצר משקה קיים בלי מחיר.

### 5.4 לחמניות

בדיקות חובה:
- חלוקה 100% ידנית.
- חלוקה 60/40.
- חלוקה 33/33/34.
- חלוקה שסכומה 99%.
- חלוקה שסכומה 101%.
- חלוקה עם אחוז שלילי.
- חלוקה עם שם ריק.
- חלוקה לפי מוצר מלאי.
- חלוקה ידנית עם מחיר.
- חלוקה עם rounding שמבטיח שסך הפריטים שווה לסך הנדרש.

### 5.5 מפות ושולחנות

בדיקות חובה:
- שולחן מלבן.
- שולחן עגול.
- אירוע מתוק עם 60% אורחים אם זה הכלל.
- תוספת reserve.
- כלי מפה שנבחר ידנית.
- שם כלי מפה כולל צורת שולחן.
- מלאי מפות חסר.
- שינוי צורת שולחן אחרי אישור.

### 5.6 אשראי וחיובים

בדיקות חובה:
- אשראי כבוי.
- אשראי דלוק עם סכום 0.
- אשראי עם סכום חיובי.
- אשראי עם אגורות.
- סכום שלילי.
- שינוי סכום אחרי חישוב.
- התאמת fee לדיוק של שתי ספרות.

### 5.7 Snapshot לאירוע מאושר

בדיקות חובה:
- אישור אירוע יוצר snapshot.
- שינוי guest_count אחרי אישור לא משנה summary אם זה הכלל.
- שינוי מחיר מוצר אחרי אישור לא משנה summary.
- שינוי מלאי אחרי אישור לא משנה summary.
- שינוי מנות אחרי אישור חסום או יוצר התנהגות מוגדרת.
- ביטול אירוע מאושר לא מוחק snapshot.
- restore stock לא משנה snapshot.

## 6. בדיקות PDF ו-RTL

מסמכים:
- Delivery sheet PDF.
- Waiter PDF.
- Catering PDF.
- Shopping PDF.

### 6.1 בדיקות מבנה PDF

לכל PDF:
- status code 200.
- content-type PDF.
- גודל קובץ מעל סף מינימום.
- ניתן לפתיחה ב-pdf parser.
- מספר עמודים צפוי.
- אין עמוד ריק.
- אין טקסט חתוך.
- אין טקסט מחוץ לעמוד.
- כותרות קיימות.
- פרטי אירוע קיימים.
- נתוני לקוח קיימים אם יש.
- כמות אורחים קיימת.
- תאריך בפורמט נכון.
- טבלאות לא נחתכות.
- עברית בכיוון נכון.
- מספרים לא מתהפכים.
- שילוב עברית/אנגלית תקין.

### 6.2 בדיקות תוכן PDF מול API

להשוות:
- שם אירוע.
- תאריך.
- כמות אורחים.
- מנות.
- כמויות.
- רשימת קניות.
- רשימת ציוד.
- מחיר/עלות אם מוצג.
- הערות.
- סטטוס.

### 6.3 בדיקות עומס PDF

לבדוק יצירת PDF עבור:
- אירוע בלי מנות.
- אירוע עם מנה אחת.
- אירוע עם 20 מנות.
- אירוע עם 100 מנות.
- שמות מנות ארוכים מאוד.
- הערות ארוכות מאוד.
- הרבה ציוד.
- הרבה מוצרי קניות.
- טקסט עם גרשיים, סוגריים, נקודותיים, slash, סימן אחוז.

## 7. בדיקות Frontend

### 7.1 בדיקות כלליות לכל מסך

לכל route:
- טעינה ראשונית.
- טעינה כשה-API איטי.
- טעינה כשה-API מחזיר 500.
- מצב empty state.
- מצב הרבה נתונים.
- חיפוש.
- סינון.
- מיון.
- pagination.
- פתיחה וסגירת dialog.
- שמירה מוצלחת.
- שמירה שנכשלת.
- מחיקה עם אישור.
- ביטול מחיקה.
- הודעות שגיאה ברורות.
- אין console errors.
- אין memory leak ברור במעבר מסכים חוזר.
- רענון דפדפן נשאר במסך תקין.
- back/forward בדפדפן.

### 7.2 מסכים

Dashboard:
- cards מציגים מספרים נכונים.
- charts לא נשברים בלי נתונים.
- אירועים קרובים מסודרים לפי תאריך.
- מלאי נמוך תואם API.

Events:
- טופס יצירה.
- טופס עריכה.
- בחירת תאריך.
- שדות חובה.
- שינוי סטטוס.
- מחיר.
- כפתורי PDF.
- בחירת מנות.
- חישובים.

Dishes:
- CRUD.
- רכיבים.
- ציוד.
- serving sets.
- calculation rules.
- מצב active.

Products:
- CRUD.
- receipt scan dialog.
- inventory status.
- bulk.

Tools:
- CRUD.
- low stock.
- bulk.

Menus:
- תפריטים.
- categories.
- dish mappings.
- validation.

Settings:
- lookup values.
- unit conversions.
- persistence.

Backup:
- create/download.
- errors.

### 7.3 RTL ועברית

לבדוק בכל מסך:
- יישור מימין לשמאל.
- שדות input בעברית.
- placeholder לא נחתך.
- טבלאות עם מספרים באנגלית בתוך עברית.
- תאריכים ושעות.
- שם ארוך בעברית.
- שם עם אותיות סופיות.
- טקסט מעורב: `ABC מוצר 123`.
- כפתורים לא גולשים.
- mobile width.
- zoom browser 125% ו-150%.

## 8. בדיקות DB ושלמות נתונים

### 8.1 Referential integrity

בדיקות חובה:
- מחיקת אירוע מוחקת/מטפלת בכל:
  - event dishes.
  - trays.
  - calculation settings.
  - snapshots.
  - manual tools.
- מחיקת מנה שמשויכת לאירוע.
- מחיקת מוצר שמשויך לרכיב.
- מחיקת כלי שמשויך למנה.
- מחיקת תפריט שמשויך לאירוע.
- מחיקת קטגוריית תפריט עם mappings.

### 8.2 Consistency checks

להריץ סקריפט שמוודא:
- אין quantities שליליים.
- אין prices שליליים.
- אין events בלי name/date/menu_type.
- אין dishes בלי name.
- אין products בלי name.
- אין tools בלי name.
- אין foreign keys שבורים.
- אין duplicate lookup values.
- אין duplicate menu_type.
- אין calculation snapshots עם JSON לא תקין.
- אין PDF output זמני שנשמר במקום לא נכון.

### 8.3 Migration/seed

בדיקות חובה:
- DB ריק -> seed מלא.
- DB קיים -> seed חוזר לא משכפל נתונים.
- DB עם נתונים ישנים -> app עולה.
- DB עם נתונים חלקיים -> app מציג שגיאה נשלטת.
- backup לפני seed.
- rollback ידני אחרי seed שנכשל.

## 9. בדיקות קלטים חריגים

להריץ על כל טופס/API:
- מחרוזת ריקה.
- whitespace בלבד.
- טקסט ארוך 1,000 תווים.
- טקסט ארוך 10,000 תווים.
- emoji אם המערכת אמורה לתמוך.
- HTML: `<script>alert(1)</script>`.
- SQL-like: `' OR 1=1 --`.
- JSON nested במקום string.
- null.
- undefined ב-frontend.
- מספר שלילי.
- מספר גדול מאוד.
- float במקום int.
- string במקום number.
- date לא תקין.
- date timezone.
- תאריך לפני 1970.
- תאריך אחרי 2100.
- מערך ריק.
- מערך ענק.
- id לא קיים.
- id שלילי.
- id אפס.
- id כמחרוזת.

## 10. בדיקות אבטחה

גם אם אין authentication כרגע, חובה לבדוק:
- CORS לא פתוח מדי בסביבת production.
- אין stack trace ב-response.
- אין path traversal בהורדת backup/PDF.
- אין אפשרות להוריד קבצים מחוץ לתיקיית גיבויים.
- אין SQL injection דרך query/search/filter.
- אין stored XSS בשמות אירועים/מנות/מוצרים.
- אין reflected XSS בהודעות שגיאה.
- אין העלאת קובץ מסוכן דרך receipts.
- הגבלת גודל קובץ upload.
- rate limit בסיסי ל-scan/PDF אם רלוונטי.
- endpoints מחיקה לא נגישים בטעות מ-GET.
- Swagger/ReDoc בסביבת לקוח רק אם מאושר.
- אין secrets בקוד/לוגים.
- אין DB path רגיש שנחשף ללקוח.

## 11. בדיקות ביצועים

### 11.1 מדדי יעד

| פעולה | יעד |
|---|---:|
| טעינת Dashboard | עד 2 שניות |
| רשימת אירועים 1,000 רשומות | עד 2 שניות |
| חיפוש מוצרים 10,000 רשומות | עד 1 שנייה |
| סיכום חישוב אירוע 100 מנות | עד 2 שניות |
| PDF אירוע גדול | עד 5 שניות |
| גיבוי DB | עד 10 שניות |

### 11.2 תרחישי עומס

- 10 משתמשים במקביל קוראים dashboard.
- 10 משתמשים יוצרים אירועים במקביל.
- 5 משתמשים מפיקים PDF במקביל.
- 20 בקשות חישוב מחדש לאותו אירוע.
- bulk create של 1,000 מוצרים.
- bulk delete של 500 מוצרים.
- DB בגודל 100MB.
- DB בגודל 1GB אם רלוונטי.

### 11.3 בדיקות N+1

לבדוק endpoints:
- events list.
- event details.
- dishes list.
- menu details.
- calculation summary.
- shopping list.
- equipment list.

קריטריון: מספר queries לא גדל לינארית בצורה קיצונית לפי כמות מנות/רכיבים.

## 12. בדיקות תאימות

דפדפנים:
- Chrome latest.
- Edge latest.
- Firefox latest אם נדרש.

מסכים:
- 1920x1080.
- 1366x768.
- 1440x900.
- 1024x768.
- 768x1024.
- 390x844.

מערכת הפעלה:
- Windows 10/11.
- בדיקת paths בעברית.
- בדיקת fonts בעברית.

Zoom:
- 100%.
- 125%.
- 150%.

## 13. בדיקות התקנה ופריסה

Backend:
- `pip install -r requirements.txt`.
- `uvicorn app.main:app --reload`.
- app עולה עם DB קיים.
- app עולה בלי DB ויוצר/מדווח נכון.
- פורט תפוס.
- env vars חסרים.
- כתיבה ללוג.

Frontend:
- `npm install` או `pnpm install` לפי החלטת הפרויקט.
- `npm run build`.
- `npm start`.
- environment API URL נכון.
- build production לא כולל source maps אם לא רצוי.

Full stack:
- frontend קורא backend.
- CORS תקין.
- refresh route Angular עובד.
- assets נטענים.
- PDF download עובד מהדפדפן.

## 14. בדיקות רגרסיה לפני כל מסירה

חבילת smoke קצרה:
- build frontend.
- pytest backend.
- פתיחת dashboard.
- יצירת מוצר.
- יצירת כלי.
- יצירת מנה.
- יצירת אירוע.
- הוספת מנה לאירוע.
- calculation summary.
- shopping list.
- equipment list.
- הפקת PDF אחד לפחות.
- backup.

חבילת release מלאה:
- כל ה-smoke.
- כל API integration.
- כל E2E.
- כל PDF visual checks.
- DB integrity.
- performance smoke.
- security smoke.

## 15. מבנה מומלץ לתיקיות בדיקה

```text
FastAPI/tests/
  conftest.py
  factories/
    event_factory.py
    dish_factory.py
    product_factory.py
    tool_factory.py
    menu_factory.py
  unit/
    test_event_calculation_drinks.py
    test_event_calculation_rolls.py
    test_event_calculation_tablecloths.py
    test_event_snapshot.py
    test_unit_conversion_service.py
    test_backup_service.py
  api/
    test_events_api.py
    test_dishes_api.py
    test_products_api.py
    test_tools_api.py
    test_menus_api.py
    test_dashboard_api.py
    test_lookup_api.py
    test_receipts_api.py
    test_pdf_api.py
  db/
    test_integrity.py
    test_delete_cascade.py
    test_seed_idempotency.py
  security/
    test_input_injection.py
    test_file_download_safety.py
  performance/
    test_large_event_summary.py

Angular/tests/
  e2e/
    dashboard.spec.ts
    events-full-flow.spec.ts
    dishes.spec.ts
    products.spec.ts
    tools.spec.ts
    menus.spec.ts
    pdf-downloads.spec.ts
    backup.spec.ts
    rtl-layout.spec.ts
  fixtures/
    seed-data.ts
    api-mocks.ts
  visual/
    pdf-render.spec.ts
    responsive.spec.ts
```

## 16. נתוני בדיקה שחייבים להיות קיימים

### 16.1 מוצרים

- מוצר יבש עם מלאי גבוה.
- מוצר יבש עם מלאי נמוך.
- מוצר ללא מלאי.
- מוצר חלבי.
- מוצר בשרי.
- מוצר פרווה.
- מוצר עם מחיר 0.
- מוצר עם מחיר שברי.
- מוצר עם יחידה ק"ג.
- מוצר עם יחידה גרם.
- מוצר עם יחידה יחידות.
- מוצר עם שם ארוך.

### 16.2 כלים

- כלי עם מלאי גבוה.
- כלי עם מלאי נמוך.
- כלי ללא מלאי.
- כלי הגשה.
- כלי מטבח.
- מפה עגולה.
- מפה מלבנית.
- כלי עם שם דומה לכלי אחר.

### 16.3 מנות

- מנה ללא רכיבים.
- מנה עם רכיב אחד.
- מנה עם 20 רכיבים.
- מנה עם כלי הגשה.
- מנה עם ציוד.
- מנה עם serving sets.
- מנה עם calculation rules.
- מנה לא פעילה.
- מנה חלבית/בשרית/פרווה.
- מנה עם שם ארוך.

### 16.4 אירועים

- אירוע טיוטה.
- אירוע מאושר.
- אירוע מבוטל.
- אירוע שהסתיים.
- אירוע קטן.
- אירוע בינוני.
- אירוע ענק.
- אירוע מתוק.
- אירוע שבת.
- אירוע מגשי אירוח.
- אירוע עם הרבה מנות.
- אירוע בלי מנות.
- אירוע עם snapshot.

## 17. Automation checklist

כל בדיקה אוטומטית צריכה לכלול:
- סידור נתונים עצמאי.
- DB נקי או fixture ברור.
- assert על status code.
- assert על response body.
- assert על DB side effect.
- assert על הודעת שגיאה בקלט שגוי.
- cleanup אם עובדים מול DB אמיתי.
- שם בדיקה שמסביר התנהגות עסקית, לא רק endpoint.

דוגמת שם טוב:
- `test_approved_event_summary_uses_snapshot_after_inventory_price_changes`
- `test_roll_split_rounding_preserves_required_total`
- `test_deleting_product_used_by_dish_is_blocked_or_keeps_calculation_stable`

## 18. Manual QA checklist

לפני מסירה ידנית ללקוח:
- עברתי על כל המסכים עם נתונים אמיתיים.
- יצרתי אירוע מלא.
- הפקתי את כל קבצי ה-PDF.
- הדפסתי PDF אחד פיזית או בדקתי preview print.
- בדקתי חיפוש בעברית.
- בדקתי שמות ארוכים.
- בדקתי טעינה מחדש של הדפדפן.
- בדקתי חזרה אחורה/קדימה.
- בדקתי שגיאות network דרך DevTools.
- בדקתי גיבוי.
- בדקתי שאין שגיאות console.
- בדקתי שאין שגיאות backend log.
- בדקתי build נקי.
- בדקתי DB backup לפני המסירה.

## 19. דוח מסירה ללקוח

לפני שליחה ללקוח להכין דוח קצר:

```text
גרסה:
תאריך בדיקה:
בודק:
סביבת בדיקה:
DB שנבדק:

תוצאות:
- Backend tests:
- Frontend build:
- E2E:
- PDF checks:
- Security smoke:
- Performance smoke:
- Backup/restore:

חסמים פתוחים:
1.
2.

בעיות ידועות שאינן חוסמות:
1.
2.

אישור מסירה:
שם:
חתימה:
תאריך:
```

## 20. פקודות מומלצות להרצה

Backend:

```powershell
cd FastAPI
python -m pytest tests -v
```

Frontend:

```powershell
cd Angular
npm run build
npm test
```

E2E:

```powershell
cd Angular
npx playwright test
```

בדיקת קבצים ונתונים:

```powershell
cd FastAPI
python check_tables.py
python check_columns.py
python check_units.py
```

## 21. Definition of Done למסירה

המערכת מוכנה למסירה רק כאשר:
- כל P0/P1 סגורים.
- כל הבדיקות האוטומטיות הקריטיות ירוקות.
- build frontend עובר.
- backend עולה נקי.
- אין שגיאות console במסכים מרכזיים.
- אין שגיאות backend log בזמן smoke.
- כל מסמכי PDF תקינים וקריאים.
- גיבוי עובד ונפתח.
- נבדקו נתוני אמת ולא רק fixtures.
- יש דוח מסירה חתום.
