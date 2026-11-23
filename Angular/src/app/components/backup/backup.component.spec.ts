// ============================================================
// 📦 IMPORTS — ייבוא הכלים הדרושים לכתיבת הבדיקות
// ============================================================

// ComponentFixture: "עטיפה" סביב הקומפוננטה שמאפשרת לנו לגשת אליה בזמן בדיקה.
// TestBed: סביבת הבדיקה של Angular — כמו "מודול מיוחד" רק לצורך הרצת בדיקות.
import { ComponentFixture, TestBed } from '@angular/core/testing';

// NoopAnimationsModule: מחליף את מודול האנימציות האמיתי בגרסה "ריקה" שעושה כלום.
// סיבה: אנימציות גורמות לבדיקות להיכשל כי הן א-סינכרוניות. בבדיקות אנחנו רוצים הכל סינכרוני.
import { NoopAnimationsModule } from '@angular/platform-browser/animations';

// of: פונקציית RxJS שיוצרת Observable שמיד פולט ערך ומסתיים.
//     דוגמה: of(42) → Observable שמיד נותן את המספר 42.
//     שימוש כאן: נשתמש בו כדי להחזיר נתוני בדיקה במקום לפנות לשרת אמיתי.
// throwError: פונקציית RxJS שיוצרת Observable שמיד פולט שגיאה.
//             שימוש כאן: לסימולציה של כישלון בקריאה לשרת.
import { of, throwError, Subject } from 'rxjs';

// ייבוא הקומפוננטה שאנחנו בודקים (הנבדקת — "SUT": System Under Test)
import { BackupComponent } from './backup.component';

// ייבוא השירות והממשק שהקומפוננטה משתמשת בו.
// BackupInfo הוא ה-interface (טיפוס) של אובייקט המידע שחוזר מהסרת.
import { BackupService, BackupInfo } from '../../services/backup.service';

// ייבוא שירות ההודעות של PrimeNG — הקומפוננטה שלנו משתמשת בו להצגת הודעות הצלחה/כישלון.
import { MessageService } from 'primeng/api';


// ============================================================
// 📝 describe — "חבילת בדיקות" (Test Suite)
// ============================================================
// describe מקבל שם תיאורי ופונקציה שמכילה את כל הבדיקות הקשורות לנושא אחד.
// כאן: כל הבדיקות שנוגעות ל-BackupComponent מקובצות יחד.
// אפשר לקנן describe בתוך describe ליצירת היררכיה (למשל: describe > describe > it)
describe('BackupComponent', () => {

  // ============================================================
  // 🔧 הגדרת משתנים משותפים לכל הבדיקות (scope של describe)
  // ============================================================

  // component: ייחזיק את המופע (instance) של BackupComponent עצמו אחרי יצירתו.
  // נשתמש בו כדי לגשת לשדות ומתודות של הקומפוננטה ישירות: component.isLoading וכו'.
  let component: BackupComponent;

  // fixture: "הכלוב" שמכיל את הקומפוננטה + ה-DOM שלה.
  // ComponentFixture<BackupComponent> = fixture שעוטף ספציפית את BackupComponent.
  // דרך ה-fixture נוכל לגשת גם לקומפוננטה וגם לאלמנטי ה-HTML שלה.
  let fixture: ComponentFixture<BackupComponent>;

  // mockBackupService: "מזויף" (Mock) של BackupService האמיתי.
  // ====================================================================
  // 🧩 מושג: Mock / Spy
  // ====================================================================
  // בבדיקות יחידה (Unit Tests) אנחנו רוצים לבדוק קומפוננטה אחת בבידוד — בלי תלות חיצונית.
  // BackupService בדרך כלל שולח HTTP לשרת. בבדיקה אנחנו לא רוצים שרת אמיתי!
  // לכן יוצרים "Mock" — אובייקט שנראה ומתנהג כמו השירות האמיתי, אבל
  // אנחנו שולטים מה הוא מחזיר. כך הבדיקה מהירה, מנותקת מרשת, ודטרמיניסטית.
  //
  // jasmine.SpyObj<BackupService>: טיפוס TypeScript שמתאר Mock של BackupService
  // כולל כל המתודות שלו כ-"Spies" (ראיות מרגלות).
  // Spy = פונקציה שמחליפה פונקציה אמיתית ומתעדת: האם נקראה? כמה פעמים? עם אילו ארגומנטים?
  let mockBackupService: jasmine.SpyObj<BackupService>;

  // mockMessageService: "מזויף" של MessageService.
  // הקומפוננטה קוראת ל-messageService.add() כדי להציג הודעות.
  // בבדיקה נרצה לוודא שהיא *ניסתה* להציג הודעה — בלי שהודעה תופיע ממש על המסך.
  let mockMessageService: jasmine.SpyObj<MessageService>;

  // ============================================================
  // 📋 נתוני בדיקה (Test Data / Test Fixtures)
  // ============================================================
  // mockBackupInfo: אובייקט נתונים מזויף שמייצג תגובה מהשרת.
  // const = קבוע, לא ישתנה בין הבדיקות.
  // BackupInfo: הטיפוס המוגדר ב-backup.service.ts — ה-interface שמתאר את מבנה הנתונים.
  const mockBackupInfo: BackupInfo = {
    exists: true,                        // קובץ הגיבוי קיים
    size_bytes: 5452595,                 // גודל בבייטים (~5.2MB)
    size_mb: 5.2,                        // גודל 5.2 מגה
    last_modified: '2025-01-15 10:30:00', // תאריך שינוי אחרון
    path: '/backups/test.sql'            // נתיב הקובץ
  };


  // ============================================================
  // ⚙️ beforeEach — הכנה לפני כל בדיקה
  // ============================================================
  // beforeEach מתבצע לפני כל it() בלוק.
  // מטרתו: לאפס את הסביבה כדי שכל בדיקה מתחילה עם slate נקי.
  // async: הפונקציה כוללת קוד א-סינכרוני (await) — יש לחכות לסיומה.
  beforeEach(async () => {

    // ============================================================
    // 🕵️ יצירת Spy Objects (Mock Services)
    // ============================================================
    // jasmine.createSpyObj(שם_לתצוגה, [רשימת_מתודות]):
    // יוצר אובייקט מזויף עם הפונקציות המפורטות ברשימה.
    // כל פונקציה כזו היא "Spy" — היא לא עושה כלום כברירת מחדל
    // אבל מתעדת כל קריאה אליה.
    mockBackupService = jasmine.createSpyObj('BackupService', [
      'getBackupInfo',         // מתודה לקבלת מידע על הגיבוי
      'downloadBackupAsBlob'   // מתודה להורדת הגיבוי
    ]);
    mockMessageService = jasmine.createSpyObj('MessageService', ['add', 'clear'], {
      // p-toast של PrimeNG מנסה לעשות subscribe על שני ה-Observables האלו בזמן אתחול.
      // בלי השדות האלה, הבדיקה קורסת עם "Cannot read properties of undefined".
      messageObserver: new Subject().asObservable(),
      clearObserver: new Subject().asObservable()
    }); // מתודות להצגת הודעות

    // ============================================================
    // 🎭 הגדרת התנהגות ברירת מחדל ל-Spy
    // ============================================================
    // .and.returnValue(ערך): אומר ל-Spy "כשיקראו לך, החזר את הערך הזה".
    // of(mockBackupInfo): יוצר Observable שמיד מחזיר את mockBackupInfo.
    // כלומר: בכל מקום שהקומפוננטה תקרא ל-getBackupInfo(),
    // היא תקבל מיד את mockBackupInfo — בלי HTTP אמיתי.
    mockBackupService.getBackupInfo.and.returnValue(of(mockBackupInfo));

    // ============================================================
    // 🏗️ TestBed.configureTestingModule — בניית מודול הבדיקה
    // ============================================================
    // זהו המקבילה של @NgModule בקוד הרגיל — אבל לסביבת הבדיקה.
    // כאן מגדירים אילו קומפוננטות, מודולים ושירותים יהיו זמינים בבדיקה.
    await TestBed.configureTestingModule({

      // imports: מודולים ש-Angular צריך להכיר כדי לרנדר את הקומפוננטה.
      imports: [
        BackupComponent,       // הקומפוננטה שאנחנו בודקים (standalone component — מייבאת את עצמה)
        NoopAnimationsModule   // מחליף אנימציות אמיתיות ב"כלום" כדי שהבדיקות לא יתקעו
      ],

      // providers: שירותים שיוזרקו (Dependency Injection) לקומפוננטה.
      // במקום לרשום את השירות האמיתי, אנחנו מחליפים אותו ב-Mock שלנו.
      // { provide: X, useValue: Y } = "כשמישהו מבקש X, תן לו Y".
      providers: [
        { provide: BackupService, useValue: mockBackupService },   // המוק במקום השירות האמיתי
        { provide: MessageService, useValue: mockMessageService }  // המוק במקום השירות האמיתי
      ]
    })
    // ============================================================
    // 🔑 overrideComponent — דריסת providers ברמת הקומפוננטה
    // ============================================================
    // הקומפוננטה מגדירה providers: [MessageService] בתוך ה-@Component decorator שלה.
    // זה גורם ל-Angular ליצור מופע חדש ונפרד של MessageService עבורה —
    // ומתעלם מה-Mock שרשמנו למעלה!
    // overrideComponent מאפשר לנו לדרוס את ה-providers הפנימיים של הקומפוננטה,
    // כך שגם המופע שהיא יוצרת עצמה יהיה ה-Mock שלנו.
    .overrideComponent(BackupComponent, {
      set: {
        providers: [
          { provide: MessageService, useValue: mockMessageService }
        ]
      }
    })
    .compileComponents(); // compileComponents: מקמפל את ה-HTML וה-CSS של הקומפוננטה

    // ============================================================
    // 🔨 יצירת הקומפוננטה בפועל
    // ============================================================
    // TestBed.createComponent: יוצר מופע של הקומפוננטה ומחזיר fixture.
    fixture = TestBed.createComponent(BackupComponent);

    // fixture.componentInstance: הגישה לאובייקט הקומפוננטה עצמו (ה-TypeScript class).
    // זה מה שנשתמש בו כדי לקרוא ל-component.loadBackupInfo() למשל.
    component = fixture.componentInstance;

    // fixture.detectChanges(): מפעיל את "מחזור השינויים" של Angular.
    // זה מה שמפעיל את ngOnInit() וגורם לקומפוננטה לרנדר את ה-HTML לראשונה.
    // חשוב: בלי זה, ngOnInit לא יקרא ו-component.backupInfo יישאר null.
    fixture.detectChanges();
  });


  // ============================================================
  // ✅ it — בדיקה בודדת (Test Case)
  // ============================================================
  // it(תיאור, פונקציה) = בדיקה יחידה.
  // ה-string הראשון הוא שם הבדיקה — מה אמורה לקרות.
  // מוסכמה: שמות מתחילים ב-"should" (אמור/צריך).
  // כשהבדיקה נכשלת, השם מוצג בדוח — חשוב שיהיה ברור!

  // בדיקה 1: הקומפוננטה נוצרת בכלל?
  it('should create', () => {
    // expect(ערך).toBeTruthy(): בדיקה שהערך הוא "אמיתי" (לא null/undefined/false/0/'').
    // component קיים ולא null = הקומפוננטה נוצרה בהצלחה.
    expect(component).toBeTruthy();
  });


  // בדיקה 2: האם הקומפוננטה טענה מידע גיבוי בעת האתחול (ngOnInit)?
  it('should load backup info on init', () => {

    // expect(spy).toHaveBeenCalled(): בדיקה שהפונקציה נקראה לפחות פעם אחת.
    // כלומר: אנחנו בודקים שהקומפוננטה *ניסתה* לקרוא לשרת.
    expect(mockBackupService.getBackupInfo).toHaveBeenCalled();

    // expect(ערך).toEqual(ערך_צפוי): בדיקת שוויון עמוק (deep equality).
    // שונה מ-toBe() שבודק שוויון לפי הפניה (===).
    // toEqual בודק שכל שדות האובייקט זהים — גם אם מדובר באובייקטים שונים בזיכרון.
    // כאן: backupInfo של הקומפוננטה אמור להיות שווה לנתוני הבדיקה שהכנו.
    expect(component.backupInfo).toEqual(mockBackupInfo);
  });


  // בדיקה 3: האם isLoading חוזר ל-false אחרי טעינה?
  it('should set isLoading to false after loading', () => {

    // toBeFalse(): בדיקה שהערך הוא בדיוק false (לא סתם falsy).
    // הקומפוננטה מציגה spinner בזמן טעינה — חשוב לוודא שהוא מוסתר אחרי הסיום.
    expect(component.isLoading).toBeFalse();
  });


  // בדיקה 4: האם refreshInfo() קורא שוב לטעינת הנתונים?
  it('should reload backup info when refreshInfo is called', () => {

    // .calls.reset(): מאפס את מונה הקריאות של ה-Spy.
    // למה? כי getBackupInfo כבר נקרא ב-ngOnInit (ב-beforeEach).
    // אנחנו רוצים לספור רק את הקריאה שתגיע מ-refreshInfo().
    mockBackupService.getBackupInfo.calls.reset();

    // קריאה ידנית למתודה שאנחנו בודקים
    component.refreshInfo();

    // toHaveBeenCalledTimes(1): בדיקה שהפונקציה נקראה בדיוק פעם אחת.
    // (לא אפס פעמים ולא שתית פעמים — בדיוק אחת)
    expect(mockBackupService.getBackupInfo).toHaveBeenCalledTimes(1);
  });


  // בדיקה 5: מה קורה כשהשרת מגיב עם שגיאה?
  it('should show error message when getBackupInfo fails', () => {
    spyOn(console, 'error');

    // עכשיו אנחנו משנים את ה-Spy כך שיחזיר Observable של שגיאה (במקום הצלחה).
    // throwError(() => new Error('שגיאת שרת')):
    //   יוצר Observable שמיד "זורק" שגיאה (מפעיל את ה-error handler של subscribe).
    //   הפרמטר הוא factory function (פונקציה שיוצרת את השגיאה) — דרישה של RxJS 7+.
    mockBackupService.getBackupInfo.and.returnValue(throwError(() => new Error('שגיאת שרת')));

    // קריאה מחדש ל-loadBackupInfo — הפעם השירות "ייכשל"
    component.loadBackupInfo();

    // jasmine.objectContaining({ severity: 'error' }):
    //   "Partial Matcher" — לא בודק שוויון מלא, אלא רק שהאובייקט **מכיל** את השדה הזה.
    //   כלומר: לא אכפת לנו מה הכותרת הספציפית של ההודעה (summary/detail) —
    //   רק שה-severity הוא 'error'. גמיש יותר ועמיד לשינויים עתידיים.
    expect(mockMessageService.add).toHaveBeenCalledWith(
      jasmine.objectContaining({ severity: 'error' })
    );

    // מוודאים שגם אחרי שגיאה, ה-loading נעצר (לא נשאר spinner לנצח)
    expect(component.isLoading).toBeFalse();
  });


  // בדיקה 6: האם הורדת הגיבוי עובדת כהלכה?
  it('should download backup as blob', () => {

    // Blob: אובייקט בינארי בדפדפן — כך נראים קבצים להורדה.
    // 'application/octet-stream': סוג MIME של קובץ בינארי כללי.
    const mockBlob = new Blob(['data'], { type: 'application/octet-stream' });

    // משנים את ה-Spy שיחזיר Observable עם ה-Blob המזויף
    mockBackupService.downloadBackupAsBlob.and.returnValue(of(mockBlob));

    // ============================================================
    // 🧩 מושג: spyOn — ריגול על מתודות קיימות
    // ============================================================
    // spyOn(אובייקט, 'שם_מתודה'): מחליף מתודה קיימת ב-Spy.
    // שונה מ-createSpyObj שיוצר אובייקט חדש לגמרי —
    // כאן אנחנו "חוטפים" מתודה של אובייקט שכבר קיים.
    //
    // למה צריך את אלה?
    // הקומפוננטה קוראת ל-document.body.appendChild, URL.createObjectURL וכו'
    // כדי ליצור ולהוריד את הקובץ. בסביבת בדיקה (JSDOM) תהיות בפונקציות אלה —
    // אז אנחנו "עוצרים" אותן ולא מאפשרים להן לרוץ.
    spyOn(document.body, 'appendChild');   // מניעת הוספת אלמנט DOM
    spyOn(document.body, 'removeChild');   // מניעת הסרת אלמנט DOM
    spyOn(window.URL, 'createObjectURL').and.returnValue('blob:mock'); // מחזיר URL מזויף
    spyOn(window.URL, 'revokeObjectURL');  // מניעת ניקוי URL

    // הפעלת המתודה שאנחנו בודקים
    component.downloadBackup();

    // בדיקה שהשירות נקרא
    expect(mockBackupService.downloadBackupAsBlob).toHaveBeenCalled();

    // בדיקה שהוצגה הודעת הצלחה
    expect(mockMessageService.add).toHaveBeenCalledWith(
      jasmine.objectContaining({ severity: 'success' })
    );

    // בדיקה שה-loading נעצר
    expect(component.isDownloading).toBeFalse();
  });


  // בדיקה 7: מה קורה כשהורדה נכשלת?
  it('should show error when download fails', () => {
    spyOn(console, 'error');

    // השרת "מגיב" עם שגיאה
    mockBackupService.downloadBackupAsBlob.and.returnValue(throwError(() => new Error('שגיאה')));

    component.downloadBackup();

    // מצפים להודעת שגיאה
    expect(mockMessageService.add).toHaveBeenCalledWith(
      jasmine.objectContaining({ severity: 'error' })
    );

    // ה-loading נעצר גם בכישלון
    expect(component.isDownloading).toBeFalse();
  });


  // בדיקה 8: בדיקה שאחרי הורדה מוצלחת isDownloading חוזר ל-false
  it('should set isDownloading to true when starting download', () => {
    const mockBlob = new Blob(['data'], { type: 'application/octet-stream' });
    mockBackupService.downloadBackupAsBlob.and.returnValue(of(mockBlob));
    spyOn(document.body, 'appendChild');
    spyOn(document.body, 'removeChild');
    spyOn(window.URL, 'createObjectURL').and.returnValue('blob:mock');
    spyOn(window.URL, 'revokeObjectURL');

    // הערה: כי of() מפעיל את ה-observable באופן סינכרוני, isDownloading כבר
    // חזר ל-false עד שאנחנו בודקים. קוד a-synchrony אמיתי היה דורש fakeAsync/tick.
    component.downloadBackup();
    expect(component.isDownloading).toBeFalse();
  });

}); // סגירת ה-describe הראשי
