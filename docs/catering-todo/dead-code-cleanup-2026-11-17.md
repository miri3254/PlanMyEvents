# ניקוי קוד שאינו בשימוש — 2026-11-17

בוצע לפי בקשת המשתמשת. לא שונו כללי מלאי או חישובים עסקיים.

## הוסר

- `Angular/src/app/services/event.service.ts`: שירות אירועים ישן מקומי, ללא צרכני import. המסכים משתמשים ב-ApiEventService.
- `Angular/src/app/core/services/profit-calculator.service.ts`: מחשבון ללא צרכנים.
- `Angular/src/app/models/dish.model.ts` ו-`product.model.ts`: מודלים ישנים ללא צרכנים.
- עטיפת `restoreStock` ב-`api-event.service.ts`: ללא קריאות; הוסרה גם ההערה השגויה על הפעלה אוטומטית בביטול. נתיב השרת נשאר.
- `EventService._get_equipment_list_legacy`: ללא קריאות.
- `EventCalculationService._sweet_hot_by_name`: ללא קריאות; החישוב הפעיל בקבוצות נשאר.
- `_add_category_dishes` ו-`_generate_shopping_pdf_legacy` ב-pdf_generator: ללא קריאות; מחוללי ה-PDF הפעילים נשארו.

## ראיות וגבולות

נבדקו גרף imports מנקודת הכניסה main.ts, נתיבים, הפניות בקוד, בבדיקות ובסקריפטים. אי-הגעה מהמסך לבדה לא שימשה הצדקה למחיקה. נשמרו מסך dashboard ישן שנבדק בטסט, קוד סריקת קבלות עם בדיקות, מודולים ישנים שמשמשים סקריפטים, נתיבי API, מיגרציות ותצורת production.

זו רשימת מחיקות שהוכחו בבדיקת המקורות, ולא הבטחה שאין עוד קוד מיותר. לא בוצעה בדיקה מול נתוני העסק או שינוי במסד העסקי.

## בדיקות

- TypeScript: `tsc -p tsconfig.app.json --noEmit` עבר.
- בניית Angular בתצורת development עברה, כולל תבניות וסגנונות.
- שרת: 17 בדיקות עברו ב-test_event_calculations.py, test_delivery_sheet_pdf.py ו-test_deep_crud_flows.py. DATABASE_URL הוגדר למסד זמני לפני טעינת האפליקציה.
- השוואת AST מול הגיבוי אישרה שבשלושת קובצי Python השתנו רק ארבע הפונקציות שהוסרו.
- בניית production נחסמה בשל שגיאת תעודה בהורדת גופן Heebo מ-Google; אין בכך אישור שבניית production תקינה.

גיבוי של ארבעת הקבצים שנמחקו ושל שלושת קובצי השרת לפני העריכה נמצא ב-`tmp/dead-code-cleanup-2026-11-17/`, מחוץ לקוד האפליקציה. שינויים קודמים של המשתמשת נשמרו.
