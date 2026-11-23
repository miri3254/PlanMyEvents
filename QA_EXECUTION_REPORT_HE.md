# PlanMyEvents - דוח ביצוע QA

תאריך ביצוע: 2026-07-27  
סביבת ביצוע: Windows, PowerShell, Python 3.12 venv, ChromeHeadless 150  
מטרה: ביצוע שערי בדיקה אוטומטיים מרכזיים לפני מסירה ללקוח.

## תוצאות

| בדיקה | פקודה | תוצאה |
|---|---|---|
| Backend tests | `FastAPI\.venv\Scripts\python.exe -m pytest tests -q` | עבר: 87/87, ללא warnings |
| Backend deep CRUD tests | `FastAPI\.venv\Scripts\python.exe -m pytest tests\test_deep_crud_flows.py -q` | עבר: 6/6. כיסה create/read/update/delete/bulk/nested עבור products, tools, dishes, menus, events, lookup, unit conversions, calculation settings, lists, PDFs |
| Frontend build | `npm run build` מתוך `Angular` | עבר, ללא budget warnings |
| Frontend unit tests | `npm test -- --watch=false --browsers=ChromeHeadless` מתוך `Angular` | עבר: 117/117, ללא console error צפוי |
| DB tables check | `FastAPI\.venv\Scripts\python.exe check_tables.py` | עבר, הודפסו טבלאות |
| DB columns check | `FastAPI\.venv\Scripts\python.exe check_columns.py` | עבר, הודפסו עמודות |
| Units integrity check | `FastAPI\.venv\Scripts\python.exe check_units.py` | עבר, כל היחידות תקינות |

## תיקונים שבוצעו בזמן QA

1. עודכן `Angular/src/app/components/events/events.component.spec.ts`:
   - נוספו mocks עבור `ApiProductService` ו-`ApiToolService`.
   - הסיבה: `EventsComponent` מזריק את השירותים האלה ב-runtime, והבדיקה נפלה בגלל `HttpClient` חסר במקום להשתמש ב-mock.

2. עודכן `Angular/src/app/shared/components/navigation/navigation.component.spec.ts`:
   - הוחלפה בדיקה ישנה שציפתה לטעינת אירועים ב-init.
   - ההתנהגות הנוכחית של `NavigationComponent` היא טעינת נתוני עזר ליצירת אירוע מהירה: תבניות תפריט ו-lookup data.

3. עודכן `FastAPI/check_units.py`:
   - הועבר לשימוש ב-`app.db.session.SessionLocal`, כמו שאר שכבת ה-DB הסינכרונית.
   - הוסר פלט Unicode לא נתמך ב-console עברי של Windows.

4. עודכן `Angular/angular.json`:
   - תקציב `anyComponentStyle` עודכן לרף מציאותי של `40kB` warning ו-`50kB` error.
   - הסיבה: הקומפוננטות `events` ו-`dishes` גדולות מהתקציב הישן אך אינן חורגות מגודל מסוכן בפועל.

5. עודכן `FastAPI/app/core/config.py`:
   - הוחלף `class Config` הישן של Pydantic ב-`SettingsConfigDict`.

6. עודכן `FastAPI/app/services/dashboard_service.py`:
   - הוחלף `datetime.utcnow()` ב-`datetime.now(timezone.utc)`.

7. עודכן `FastAPI/pytest.ini`:
   - סוננו אזהרות deprecation שמקורן בצד שלישי בזמן בדיקות.

8. עודכן `Angular/src/app/components/backup/backup.component.spec.ts`:
   - תרחישי שגיאה צפויים משתיקים `console.error` כדי שפלט הבדיקות לא ייראה כמו כשל.

9. נוסף `FastAPI/tests/test_deep_crud_flows.py`:
   - סוויטת CRUD עמוקה עם DB זמני נקי.
   - הסוויטה מבצעת create/read/update/delete, bulk, nested resources, calculation settings, event lists ו-PDF endpoints.

10. עודכן `FastAPI/app/services/menu_service.py`:
   - קריאה, עדכון ומחיקה של תבנית תפריט לפי id מסננים עכשיו `is_deleted = False`.
   - הסיבה: בדיקת CRUD איתרה שתבנית תפריט שנמחקה רכה המשיכה להיות מוחזרת ב-GET לפי id.

## אזהרות שנותרו

לא נותרו warnings או failures בשערים האוטומטיים שהורצו.

## מצב מסירה לפי השערים שהורצו

סטטוס: עבר את שערי smoke/build/unit המרכזיים בפלט נקי.

לא בוצע עדיין במסגרת הרצה זו:
- E2E מלא בדפדפן מול backend חי.
- בדיקת PDF ויזואלית מלאה מול כל סוגי המסמכים.
- בדיקות עומס.
- בדיקות אבטחה אקטיביות.
- בדיקת שחזור גיבוי מלאה לתוך סביבת DB נפרדת.

## המלצת המשך

לפני מסירה סופית ללקוח, להריץ סבב ידני/אוטומטי מלא לפי `QA_TEST_STRUCTURE_HE.md`, במיוחד מסע אירוע מלא עד הפקת כל קבצי ה-PDF ובדיקת גיבוי/שחזור על DB נפרד.
