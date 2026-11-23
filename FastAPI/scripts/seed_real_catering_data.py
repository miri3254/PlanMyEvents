"""Reset the demo database and seed the real catering recipes from /מתכונים.

This file is intentionally deterministic: rerunning it produces the same catalogue.
Quantities are kept in the units written in the source Word documents.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "data" / "planmyevents.db"
NOW = datetime.now().isoformat(sep=" ", timespec="seconds")

# Ingredient: product name, quantity, database unit (enum member name).
def I(name, qty, unit="UNIT"):
    return (name, float(qty), unit)


DISHES = [
    ("סלט מיקס כרובים", "PARVE", "קערה 2.5 ליטר", [I("כרוב לבן",.5,"KG"),I("כרוב סגול",.5,"KG"),I("בצל ירוק",1),I("שמן",2,"CUP"),I("סוכר",1,"CUP"),I("מלח",3,"TEASPOON"),I("חומץ",.25,"CUP"),I("פלפל שחור",.25,"TEASPOON"),I("תערובת פיצוחים",1,"CUP")]),
    ("בורגול וירקות", "PARVE", "2 קערות של 2.5 ליטר", [I("בורגול",1,"KG"),I("פטרוזיליה",1,"BUNDLE"),I("סלרי",1,"BUNDLE"),I("סילאן",.75,"CUP"),I("מיץ לימון",.25,"CUP"),I("מלח",1,"TEASPOON"),I("כורכום",.25,"TEASPOON"),I("פלפל שחור",.25,"TEASPOON"),I("אגוזי מלך",100,"GRAM"),I("חמוציות",100,"GRAM")]),
    ("סלט חסה מתוק", "PARVE", "קערה 2.5 ליטר", [I("חסה אייסברג",1,"KG"),I("אפרסק משומר",1,"PACKAGE"),I("חמוציות",100,"GRAM"),I("פקאן",100,"GRAM"),I("שמן",2,"CUP"),I("מיץ תפוזים",2,"CUP"),I("שום",8),I("חרדל",2,"TEASPOON"),I("סוכר",.75,"CUP"),I("מלח",2,"TEASPOON")]),
    ("סלט חסה שרי ופטריות", "PARVE", "קערת מגש אירוח", [I("חסה אייסברג",.5,"KG"),I("פטריות טריות",1,"PACKAGE"),I("נבטים",.5,"PACKAGE"),I("עגבניות שרי",15),I("מיונז",2,"TABLESPOON"),I("שמן",.25,"CUP"),I("סוכר",.25,"CUP"),I("חומץ",1,"TABLESPOON"),I("שום",3),I("שקדים וחמוציות",.5,"CUP")]),
    ("סלט אישי", "PARVE", "24 כוסות", [I("כרוב לבן",1,"KG"),I("כרוב סגול",1,"KG"),I("חסה אייסברג",1),I("פטריות טריות",1,"PACKAGE"),I("נבטים",1,"PACKAGE"),I("עגבניות שרי",24),I("שמן",3,"CUP"),I("מיץ תפוזים",3,"CUP"),I("סוכר",1.25,"CUP"),I("שום",10),I("חרדל",2,"TEASPOON"),I("מלח",3,"TEASPOON")]),
    ("סלט יווני", "DAIRY", "קערת מגש אירוח", [I("חסה אייסברג",1,"KG"),I("זיתים שחורים",.5,"CUP"),I("מלפפון",1),I("עגבניות שרי",10),I("בצל סגול",.5),I("גבינה בולגרית",.5,"PACKAGE"),I("שמן זית",.5,"CUP"),I("שמן",1,"CUP"),I("מיץ לימון",.25,"CUP")]),
    ("ירקות חתוכים", "PARVE", "2 מגשים", [I("חסה",1),I("גזר",2),I("מלפפון",2),I("נבטים",.5,"PACKAGE"),I("צנונית",10),I("פטריות טריות",.5,"PACKAGE"),I("פלפל אדום",1),I("פלפל צהוב",1),I("עגבניות שרי",10)]),
    ("סלט גזר מעודן", "PARVE", "קערת מגש אירוח", [I("גזר ג'וליאני",1,"KG"),I("בצל ירוק",1),I("פקאן",150,"GRAM"),I("חמוציות",50,"GRAM"),I("שמן",1,"CUP"),I("סוכר",.5,"CUP"),I("מלח",1,"TEASPOON"),I("אבקת שום",1,"TEASPOON")]),
    ("סלט גזר פיקנטי", "PARVE", "כ-4 ליטר", [I("גזר ג'וליאני",2,"KG"),I("מלח",2,"TEASPOON"),I("סוכר",.5,"CUP"),I("מיץ לימון",3,"TABLESPOON"),I("חרדל",3,"TEASPOON"),I("צ'ילי גרוס",2,"TEASPOON"),I("מיונז",8,"TABLESPOON"),I("שום",6)]),
    ("סלט אסייתי", "PARVE", "2 קערות", [I("כרוב סגול",1,"KG"),I("גזר ג'וליאני",1,"CUP"),I("נבטים",1,"PACKAGE"),I("בצל ירוק",1),I("מיץ תפוזים",.5,"CUP"),I("רוטב סויה",.5,"CUP"),I("שמן",.5,"CUP"),I("סילאן",.5,"CUP"),I("שום",4),I("אטריות דקות",1,"PACKAGE")]),
    ("סלט שרי", "DAIRY", "קערת מגש אירוח", [I("עגבניות שרי",1,"PACKAGE"),I("בצל ירוק",.5,"BUNDLE"),I("זיתים שחורים",1,"CUP"),I("בצל סגול",1),I("גרעיני חמנייה",.5,"CUP"),I("גבינה בולגרית",.5,"PACKAGE")]),
    ("סלט פסטה קר", "DAIRY", "קערת מגש אירוח", [I("פסטה",1,"PACKAGE"),I("מלפפון",1),I("פלפל אדום",1),I("בצל סגול",1),I("פטרוזיליה",.25,"BUNDLE"),I("זיתים שחורים",.5,"CUP"),I("גבינה צפתית",.5,"PACKAGE"),I("סילאן",2,"TABLESPOON"),I("שמן",.25,"CUP"),I("שמן זית",2,"TABLESPOON")]),
    ("קינואה וירקות", "PARVE", "קערת מגש אירוח", [I("קינואה",1,"KG"),I("מלפפון",1),I("פלפל אדום",1),I("בצל סגול",.5),I("עגבניות שרי",10),I("מיץ לימון",.25,"CUP"),I("סילאן",2,"TABLESPOON"),I("שמן",3,"TABLESPOON"),I("אגוזי מלך",10)]),
    ("סלט אבוקדו", "PARVE", "1 ליטר", [I("אבוקדו",1,"KG"),I("ביצים",4),I("בצל מטוגן",.5,"CUP"),I("פלפל שחור",.5,"TEASPOON"),I("מיץ לימון",2,"TABLESPOON"),I("מלח",1,"TEASPOON")]),
    ("סלט ביצים", "PARVE", "1 ליטר", [I("ביצים",12),I("בצל מטוגן",.75,"CUP"),I("מלח",1,"TEASPOON"),I("פלפל שחור",.25,"TEASPOON"),I("מיונז",2,"TABLESPOON"),I("שמן",.25,"CUP")]),
    ("סלט טונה", "PARVE", "2 ליטר", [I("ביצים",8),I("טונה במים",4,"PACKAGE"),I("גזר",2),I("מלפפון חמוץ",4),I("מיונז",2,"TABLESPOON"),I("פלפל שחור",.5,"TEASPOON"),I("צ'ילי גרוס",.5,"TEASPOON")]),
    ("עגבניות חי", "PARVE", "1 ליטר", [I("עגבנייה",1,"KG"),I("שום",8),I("פטרוזיליה",1,"BUNDLE"),I("שמן זית",3,"TABLESPOON"),I("מיץ לימון",.25,"CUP"),I("מלח",1,"TEASPOON"),I("פלפל שחור",.25,"TEASPOON"),I("סוכר",.25,"CUP")]),
    ("טפנד זיתים", "PARVE", "1 ליטר", [I("זיתים",2.5,"PACKAGE"),I("שום",6),I("מיונז",2,"TABLESPOON"),I("שמן זית",.25,"CUP"),I("מלח",.5,"TEASPOON")]),
    ("גבינת שמנת בטעמים", "DAIRY", "1 ליטר", [I("שמנת חמוצה",5,"PACKAGE"),I("שום",3),I("שמן זית",2,"TABLESPOON"),I("מלח",2,"TEASPOON"),I("מיונז",1,"TABLESPOON")]),
    ("טורטייה גבינות קריספית", "DAIRY", "70 חצאים / 35 טורטיות", [I("טורטייה",35),I("גבינה צהובה",500,"GRAM"),I("קוטג'",4,"PACKAGE"),I("שמנת חמוצה",4,"PACKAGE"),I("גבינת שמנת",250,"GRAM"),I("בטטה",500,"ML"),I("ביצים",6),I("חרדל",2,"TEASPOON"),I("פירורי לחם",1,"PACKAGE"),I("שמן",1,"CUP")]),
    ("טורטייה טונה וירקות", "PARVE", "מגש אירוח", [I("טורטייה",20),I("ביצים",8),I("טונה במים",4,"PACKAGE"),I("גזר",2),I("מלפפון חמוץ",4),I("מיונז",2,"TABLESPOON"),I("פלפל אדום",1),I("מלפפון",1),I("חסה",1)]),
    ("טורטייה סלמון מעושן", "DAIRY", "2 חבילות טורטיות", [I("טורטייה",2,"PACKAGE"),I("גבינת שמנת",1,"PACKAGE"),I("חסה",1),I("פלפל אדום",1),I("סלמון מעושן",2,"PACKAGE")]),
    ("טורטייה פלפל קלוי וגבינת שמנת", "DAIRY", "20 טורטיות", [I("טורטייה",20),I("גבינת שמנת חלפיניו",1,"PACKAGE"),I("פלפל קלוי",1,"PACKAGE"),I("חסה",1)]),
    ("בלינצ'ס שמנת", "DAIRY", "30 יחידות", [I("חלב",3,"CUP"),I("קמח",2,"CUP"),I("ביצים",4),I("סוכר",3,"TABLESPOON"),I("מלח",.5,"TEASPOON"),I("שמנת מתוקה",2,"PACKAGE"),I("ריבת חלב",2,"TABLESPOON"),I("פודינג וניל",.5,"CUP"),I("שמנת חמוצה",1,"PACKAGE")]),
    ("לזניה אישית", "DAIRY", "55 יחידות", [I("פסטה",4,"PACKAGE"),I("קוטג'",3,"PACKAGE"),I("רסק עגבניות",4,"PACKAGE"),I("פטריות טריות",3,"PACKAGE"),I("בצל מטוגן",2,"CUP"),I("אבקת מרק",1.25,"CUP"),I("שמנת מתוקה",2,"PACKAGE"),I("גבינה צהובה",1,"PACKAGE")]),
    ("מוסקת חצילים בגבינת שמנת", "DAIRY", "מגש שחור זהב", [I("חציל",4),I("שמן",1,"CUP"),I("פפריקה מתוקה",.5,"TEASPOON"),I("מלח",.5,"TEASPOON"),I("גבינת שמנת",1,"PACKAGE"),I("צ'ילי גרוס",.25,"TEASPOON")]),
    ("מיני קישים", "DAIRY", "72 יחידות", [I("בסיס מיני קיש",72),I("שמנת מתוקה",8,"PACKAGE"),I("חלב",2,"CUP"),I("קמח",2,"CUP"),I("אבקת מרק",.5,"CUP"),I("אגוז מוסקט",1,"TEASPOON")]),
    ("קישים גדולים", "DAIRY", "95 יחידות", [I("בסיס קיש",95),I("ביצים",20),I("שמנת מתוקה",1,"PACKAGE"),I("גבינה לבנה",850,"GRAM"),I("קוטג'",4,"PACKAGE"),I("בצל מטוגן",3,"CUP"),I("קמח",1,"CUP"),I("אבקת מרק",1,"CUP"),I("גבינת פיצה",1,"PACKAGE")]),
    ("פשטידת פטריות וגבינות", "DAIRY", "60 יחידות", [I("פטריות שימורים",6,"PACKAGE"),I("קוטג'",3,"PACKAGE"),I("בצל מטוגן",5,"CUP"),I("מיונז",3,"TABLESPOON"),I("שמן",3,"CUP"),I("ביצים",18),I("קמח",5,"CUP"),I("סילאן",3,"TABLESPOON"),I("אבקת מרק",1.5,"CUP"),I("אבקת אפייה",1,"PACKAGE")]),
    ("פשטידת קישואים", "DAIRY", "60 יחידות", [I("קישוא",10,"CUP"),I("בצל מטוגן",2,"CUP"),I("קוטג'",3,"PACKAGE"),I("קמח",2.5,"CUP"),I("ביצים",30),I("אבקת מרק",1,"CUP"),I("מיונז",4,"TABLESPOON"),I("פירורי לחם",1,"PACKAGE")]),
    ("פסטה מוקרמת", "DAIRY", "2 מגשים קטנים", [I("פסטה",1,"PACKAGE"),I("שמנת מתוקה",500,"ML"),I("פטריות",2,"CUP"),I("חמאה",.5,"PACKAGE"),I("אבקת מרק",.25,"CUP"),I("אגוז מוסקט",.25,"TEASPOON"),I("חלב",1,"LITER"),I("מלח",.5,"TEASPOON"),I("פלפל שחור",.5,"TEASPOON")]),
    ("תפוחי אדמה מוקרמים", "DAIRY", "מגש לכ-10 אנשים", [I("תפוחי אדמה",9),I("אבקת מרק",2,"TABLESPOON"),I("פטריות שימורים",1,"PACKAGE"),I("שמנת מתוקה",2,"PACKAGE"),I("חלב",.75,"CUP"),I("קמח",1,"TABLESPOON")]),
    ("הום פרייז", "DAIRY", "מגש שחור זהב גדול", [I("תפוחי אדמה",2.6,"KG"),I("אבקת מרק",.5,"CUP"),I("צ'ילי מתוק",1,"CUP"),I("חמאה",100,"GRAM")]),
    ("קוביות בטטה בצ'ילי", "PARVE", "מגש אירוח", [I("בטטה",10),I("שמן",.25,"CUP"),I("מלח",.5,"TEASPOON"),I("סילאן",2,"TABLESPOON"),I("דבש",2,"TABLESPOON"),I("צ'ילי מתוק",.5,"CUP"),I("שומשום",.25,"CUP")]),
    ("פוקאצ'ות", "PARVE", "64 יחידות", [I("קמח",2,"KG"),I("מים",9,"CUP"),I("מלח",2,"TABLESPOON"),I("סוכר",1,"CUP"),I("שמן",1,"CUP"),I("שמרים",6,"TABLESPOON")]),
    ("פיציות", "DAIRY", "כ-30 יחידות", [I("בצק עלים",1,"PACKAGE"),I("רסק עגבניות",1.5,"KG"),I("זיתים ירוקים",2,"PACKAGE"),I("תבלין פיצה",3,"TABLESPOON"),I("שמן זית",.25,"CUP"),I("סוכר",1.5,"CUP"),I("מלח",4,"TEASPOON"),I("גבינה צהובה",2,"CUP")]),
    ("לחמניות בטעמים", "PARVE", "30 יחידות", [I("מים",550,"ML"),I("קמח",1,"KG"),I("סוכר",.75,"CUP"),I("שמן",.75,"CUP"),I("מלח",1,"TABLESPOON"),I("שמרים",2,"TABLESPOON")]),
    ("לחמניות ביס", "PARVE", "42 יחידות", [I("מים",550,"ML"),I("שמרים",2,"TABLESPOON"),I("קמח",1,"KG"),I("סוכר",.5,"CUP"),I("מלח",1,"TABLESPOON")]),
    ("שקשוקה", "PARVE", "15 מנות ביצה", [I("פלפל אדום",3),I("עגבנייה",3),I("בצל",3),I("פלפל חריף",1),I("שום",6),I("סוכר",2,"TABLESPOON"),I("רסק עגבניות",2,"TABLESPOON"),I("צ'ילי גרוס",1,"TEASPOON"),I("ביצים",15)]),
    ("מרק כתום", "PARVE", "20 ליטר", [I("בטטה",10,"KG"),I("בצל מטוגן",1,"LITER"),I("אבקת מרק",3,"CUP"),I("פלפל שחור",2,"TEASPOON")]),
    ("מרק אפונה וירקות", "PARVE", "16 ליטר", [I("אפונה",2,"KG"),I("לקט ירקות",1,"PACKAGE"),I("אבקת מרק",2,"CUP"),I("מלח",2,"TABLESPOON")]),
    ("מרק עדשים", "PARVE", "24 ליטר", [I("עדשים אדומות",2,"KG"),I("לקט ירקות",1,"PACKAGE"),I("כרובית",1,"PACKAGE"),I("ברוקולי",1,"PACKAGE"),I("אבקת מרק",3,"CUP"),I("מלח",2,"TABLESPOON"),I("פלפל שחור",1,"TEASPOON")]),
    ("אורז עם ירקות", "PARVE", "תבנית גסטרונום", [I("אורז",2,"KG"),I("שמן",3,"CUP"),I("גזר ג'וליאני",1,"KG"),I("פטריות שימורים",1,"PACKAGE"),I("פלפל אדום",1),I("בטטה",2),I("אבקת מרק",2,"CUP")]),
    ("קוגל תפוחי אדמה", "PARVE", "2 תבניות גדולות / 70 יחידות", [I("תפוחי אדמה",5,"KG"),I("ביצים",20),I("שמן",2,"CUP"),I("מלח",2,"TABLESPOON"),I("פלפל שחור",2,"TEASPOON")]),
    ("תפוחי אדמה פריזיאניים", "PARVE", "5 ק\"ג / גסטרונום", [I("תפוחי אדמה בייבי",5,"KG"),I("שמן",1,"CUP"),I("אבקת מרק",1.5,"CUP"),I("צ'ילי מתוק",.5,"CUP"),I("אבקת שום",2,"TABLESPOON"),I("צ'ילי גרוס",1,"TEASPOON"),I("גריל עוף",2,"TABLESPOON"),I("פפריקה מתוקה",2,"TABLESPOON")]),
    ("שעועית ירוקה ושומשום", "PARVE", "50 איש", [I("שעועית ירוקה",3,"KG"),I("אבקת מרק בצל",2,"CUP"),I("בצל מטוגן",2,"CUP"),I("מלח",1,"TABLESPOON"),I("שומשום",1,"CUP"),I("שמן",2,"CUP")]),
    ("פלפל ממולא", "PARVE", "80 יחידות", [I("פלפל אדום",80),I("אורז",2,"KG"),I("שמן",1.5,"CUP"),I("מלח",2,"TABLESPOON"),I("רסק עגבניות",2.5,"KG"),I("בזיליקום יבש",.5,"CUP"),I("אבקת מרק",2.5,"CUP"),I("סוכר",2.5,"CUP"),I("צ'ילי גרוס",1,"TEASPOON")]),
    ("טורטיות ירקות ופירה", "PARVE", "75 יחידות", [I("טורטייה",75),I("פירה אינסטנט",1,"KG"),I("ירקות מאודים",6,"CUP"),I("אבקת מרק",1,"CUP"),I("ביצים",4),I("פירורי לחם",1,"PACKAGE"),I("שמן",1,"CUP")]),
    ("סלמון בעשבי תיבול", "PARVE", "35 יחידות", [I("סלמון",35),I("שמן זית",1,"CUP"),I("שום",10),I("פטרוזיליה",1,"BUNDLE"),I("מלח",2,"TEASPOON"),I("פלפל שחור",1,"TEASPOON")]),
    ("פרגיות במרינדת הדרים", "MEAT", "35 יחידות", [I("פרגיות",35),I("מיץ תפוזים",2,"CUP"),I("סילאן",1,"CUP"),I("שמן",1,"CUP"),I("שום",8),I("פפריקה מתוקה",2,"TABLESPOON")]),
    ("עוף ברביקיו", "MEAT", "30 כרעיים", [I("כרעי עוף",30),I("רוטב ברביקיו",3,"CUP"),I("סילאן",1,"CUP"),I("פפריקה מתוקה",2,"TABLESPOON"),I("גריל עוף",2,"TABLESPOON"),I("שומשום",1,"CUP")]),
    ("שניצל פריך", "MEAT", "30 יחידות", [I("שניצל עוף",30),I("ביצים",4),I("חרדל",1,"TABLESPOON"),I("אבקת שום",1,"TABLESPOON"),I("גריל עוף",1,"TABLESPOON"),I("פירורי לחם",500,"GRAM"),I("שומשום שחור",50,"GRAM"),I("פטרוזיליה יבשה",50,"GRAM")]),
    ("אקלרים בשמנת ושוקולד", "PARVE", "מנה אחת לפי המתכון", [I("מים",.5,"LITER"),I("שמן",1,"CUP"),I("מלח",1,"TEASPOON"),I("סוכר",1.5,"TEASPOON"),I("קמח",300,"GRAM"),I("ביצים",8),I("קצפת צמחית",1,"PACKAGE"),I("שוקולד מריר",200,"GRAM")]),
    ("בראוניז", "PARVE", "60 קוביות", [I("שוקולד מריר",600,"GRAM"),I("סוכר",6,"CUP"),I("קמח",4,"CUP"),I("אגוזי מלך",200,"GRAM"),I("ביצים",12),I("מרגרינה",2,"PACKAGE")]),
    ("כוסות קרם אוכמניות", "DAIRY", "20 כוסות", [I("ביסקוויטים",300,"GRAM"),I("חמאה",1,"PACKAGE"),I("שמנת חמוצה",10,"PACKAGE"),I("פודינג וניל",1,"CUP"),I("סוכר",.5,"CUP"),I("מיץ לימון",.25,"CUP"),I("אוכמניות",300,"GRAM")]),
    ("מוזלי", "DAIRY", "מנה לפי המתכון", [I("קיווי",2),I("תפוח ירוק",2),I("תפוח אדום",2),I("מנגו",1),I("קוקטייל פירות",1,"PACKAGE"),I("אפרסק משומר",1,"PACKAGE"),I("שמנת חמוצה",10,"PACKAGE"),I("יוגורט",4,"PACKAGE"),I("סוכר",1.5,"CUP"),I("פודינג וניל",1.5,"CUP"),I("קוואקר",2,"CUP"),I("פצפוצי אורז",1,"CUP")]),
    ("מוס שמנת", "DAIRY", "32 כוסות שוט", [I("שמנת מתוקה",1,"LITER"),I("פודינג וניל",8,"TABLESPOON"),I("רוטב תותים",1,"PACKAGE")]),
    ("סופלה שוקולד", "PARVE", "44 יחידות", [I("שוקולד מריר",800,"GRAM"),I("ביצים",20),I("קורנפלור",20,"TABLESPOON"),I("סוכר",5,"CUP"),I("שמן",2.5,"CUP")]),
    ("עוגת גבינה אישית בריבת חלב", "DAIRY", "15 יחידות", [I("קמח",2.5,"CUP"),I("סוכר",2.5,"CUP"),I("שמן",.5,"CUP"),I("אבקת אפייה",.5,"PACKAGE"),I("ביצים",9),I("גבינה לבנה",1,"KG"),I("שמנת חמוצה",1,"PACKAGE"),I("מיץ לימון",.25,"CUP"),I("ריבת חלב",1,"PACKAGE")]),
    ("עוגת גבינה שלוש שכבות", "DAIRY", "תבנית גדולה", [I("ביסקוויטים",1,"PACKAGE"),I("חמאה",100,"GRAM"),I("גבינה לבנה",850,"GRAM"),I("שמנת מתוקה",1,"PACKAGE"),I("סוכר",1.25,"CUP"),I("ביצים",5),I("קורנפלור",2,"TABLESPOON"),I("שמנת חמוצה",2,"PACKAGE"),I("ריבת חלב",300,"GRAM")]),
    ("עוגת קפה ושוקולד", "PARVE", "תבנית גדולה", [I("קמח",5,"CUP"),I("סוכר",2.75,"CUP"),I("ביצים",6),I("שמן",2.25,"CUP"),I("קפה נמס",36,"TABLESPOON"),I("שוקולד צ'יפס",300,"GRAM"),I("שוקולד מריר",200,"GRAM"),I("קצפת צמחית",1,"CUP")]),
    ("סיגרי פילו וחלבה", "PARVE", "120 יחידות", [I("בצק פילו",3,"PACKAGE"),I("חלבה",1,"KG"),I("שמן",1,"CUP")]),
    ("שייק פירות", "PARVE", "9 ליטר", [I("קיווי",4),I("רסק תפוחים",2,"PACKAGE"),I("אננס משומר",3,"PACKAGE"),I("אפרסק משומר",3,"PACKAGE"),I("קוקטייל פירות",3,"PACKAGE"),I("ג'לי",.5,"KG"),I("מיץ תפוזים",1.5,"LITER")]),
    ("ירקות אנטיפסטי", "PARVE", "המסמך המצורף מכיל כותרת בלבד", []),
]

DAIRY = {"חלב","חמאה","שמנת חמוצה","שמנת מתוקה","קוטג'","גבינה לבנה","גבינה צהובה","גבינה בולגרית","גבינה צפתית","גבינת שמנת","גבינת שמנת חלפיניו","גבינת פיצה","יוגורט","ריבת חלב"}
MEAT = {"כרעי עוף","שניצל עוף","פרגיות"}
FROZEN = {"אפונה","לקט ירקות","שעועית ירוקה","ירקות מאודים"}
LIQUID = {"מים","שמן","שמן זית","חומץ","מיץ לימון","מיץ תפוזים","סילאן","דבש","רוטב סויה","צ'ילי מתוק","מיונז","חרדל","רוטב ברביקיו","רוטב תותים"}

# Unique tools visible in the supplied catering spreadsheet screenshot.
# Guest counts in the sheet are calculation inputs, not inventory counts.
TOOLS = [
    ("קערה", "SERVING", "מרכזי"),
    ("קערה מלבנית", "SERVING", "מרכזי"),
    ("קערה שקופה", "SERVING", "מרכזי"),
    ("מזנון שקוף", "SERVING", "מרכזי"),
    ("מזנון לקרוטונים", "SERVING", "מרכזי"),
    ("צלחת גדולה", "PLATES", "אישי"),
    ("צלחת קטנה", "PLATES", "אישי"),
    ("מרקית", "PLATES", "אישי"),
    ("קערית", "PLATES", "אישי"),
    ("כלי הגשה אישי", "SERVING", "אישי"),
    ("אובל נמוך", "SERVING", "אישי"),
    ("אובל גדול", "SERVING", "מרכזי"),
    ("מגש", "SERVING", "מרכזי"),
    ("כף", "CUTLERY", "אישי"),
    ("כפית", "CUTLERY", "אישי"),
    ("סכין", "CUTLERY", "אישי"),
    ("מזלג", "CUTLERY", "אישי"),
]

def product_defaults(name, seen_units):
    kosher = "MEAT" if name in MEAT else "DAIRY" if name in DAIRY else "PARVE"
    category = "MEAT" if name in MEAT else "DAIRY" if name in DAIRY else "FROZEN" if name in FROZEN else "LIQUIDS" if name in LIQUID else "DRY"
    unit = next((u for u in ("KG","LITER","PACKAGE","BUNDLE","UNIT","GRAM") if u in seen_units), "UNIT")
    return category, unit, kosher

def insert_base(cur, table, fields, values):
    cols = list(fields) + ["created_at","updated_at","is_deleted"]
    vals = list(values) + [NOW,NOW,0]
    quoted_cols = ",".join(f'"{column}"' for column in cols)
    cur.execute(f'INSERT INTO "{table}" ({quoted_cols}) VALUES ({",".join("?" for _ in cols)})', vals)
    return cur.lastrowid

def main():
    conn=sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys=OFF")
    cur=conn.cursor()
    tables=[r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name!='alembic_version'")]
    try:
        cur.execute("BEGIN")
        for table in tables: cur.execute(f'DELETE FROM "{table}"')
        if cur.execute("SELECT 1 FROM sqlite_master WHERE name='sqlite_sequence'").fetchone():
            cur.execute("DELETE FROM sqlite_sequence")

        conversions = [
            ("KG","GRAM",1000,1),("GRAM","KG",.001,1),
            ("MG","GRAM",.001,1),("GRAM","MG",1000,1),
            ("KG","MG",1000000,1),("MG","KG",.000001,1),
            ("LITER","ML",1000,1),("ML","LITER",.001,1),
            ("CUP","ML",240,1),("ML","CUP",1/240,1),
            ("TABLESPOON","GRAM",15,0),("TEASPOON","GRAM",5,0),("PINCH","GRAM",.5,0),
        ]
        for from_unit,to_unit,factor,is_system in conversions:
            insert_base(cur,"unit_conversions",["from_unit","to_unit","factor","is_system","description"],[from_unit,to_unit,factor,is_system,f"{from_unit} -> {to_unit}"])

        units={}
        for _,_,_,ings in DISHES:
            for name,_,unit in ings: units.setdefault(name,set()).add(unit)
        product_ids={}
        for name in sorted(units):
            category,unit,kosher=product_defaults(name,units[name])
            product_ids[name]=insert_base(cur,"products",["name","category","unit","quantity_in_stock","min_stock_level","kosher_type","notes"],[name,category,unit,0,0,kosher,"נוצר ממתכוני הקייטרינג האמיתיים"])

        for name,category,usage in TOOLS:
            insert_base(cur,"tools",["name","brand","category","sub_category","quantity_in_stock","min_stock_level","price_per_unit","description","color","size"],[name,None,category,"REAL",0,0,0,f"מהאקסל המצורף; שימוש {usage}",None,None])

        dish_ids={}; dish_groups={}
        for name,kosher,serving,ings in DISHES:
            desc="מקור: מסמכי Word בתיקיית מתכונים. הכמויות נשמרו לפי המתכון."
            did=insert_base(cur,"dishes",["name","description","kosher_type","serving_size","serving_description","is_active"],[name,desc,kosher,1,serving,1])
            dish_ids[name]=did
            group="קינוחים" if any(x in name for x in ("עוג","מוס","סופלה","בראונ","אקלר","שייק","פילו")) else "מנות עיקריות" if kosher=="MEAT" or any(x in name for x in ("מרק","אורז","קוגל","שעועית","פלפל ממולא","פריזיאניים","סלמון")) else "מגשי אירוח" if any(x in name for x in ("טורט","בלינצ","לזניה","קיש","פשטיד","פסטה","פוקא","פיצ","לחמ","מוקר","הום")) else "סלטים ומטבלים"
            dish_groups[name]=group
            for prod,qty,unit in ings:
                insert_base(cur,"dish_ingredients",["dish_id","product_id","name","quantity","unit","is_serving_component"],[did,product_ids[prod],prod,qty,unit,0])

        templates={}
        for menu_type,name,kosher,tray in [("REAL_CATERING","קייטרינג מלא","PARVE",0),("HOSTING_TRAYS","מגשי אירוח","DAIRY",1)]:
            templates[name]=insert_base(cur,"menu_templates",["menu_type","name","description","min_guests","base_price_per_guest","is_tray_menu","kosher_type","real_dishes_extra_per_guest"],[menu_type,name,"תפריט שנוצר מהמתכונים האמיתיים",10,None,tray,kosher,0])
        categories={}
        for order,group in enumerate(("סלטים ומטבלים","מגשי אירוח","מנות עיקריות","קינוחים"),1):
            template=templates["מגשי אירוח"] if group=="מגשי אירוח" else templates["קייטרינג מלא"]
            categories[group]=insert_base(cur,"menu_categories",["template_id","sub_meal_id","name","name_hebrew","display_order","quota","is_required","tray_quantity"],[template,None,f"real_{order}",group,order,None,1,1 if group=="מגשי אירוח" else None])
        orders={g:0 for g in categories}
        for name,did in dish_ids.items():
            g=dish_groups[name]; orders[g]+=1
            insert_base(cur,"dish_menu_mappings",["dish_id","category_id","is_upgrade","extra_charge","display_order"],[did,categories[g],0,0,orders[g]])

        sample_events=[
            ("אירוע דמה – קייטרינג בשרי","REAL_CATERING",80,["סלט מיקס כרובים","סלט גזר פיקנטי","מרק כתום","עוף ברביקיו","אורז עם ירקות","שעועית ירוקה ושומשום","שייק פירות"]),
            ("אירוע דמה – מגשי אירוח חלבי","HOSTING_TRAYS",40,["סלט חסה מתוק","טורטייה גבינות קריספית","לזניה אישית","מיני קישים","פסטה מוקרמת","כוסות קרם אוכמניות"]),
            ("אירוע דמה – שבת","REAL_CATERING",50,["סלט אבוקדו","סלט ביצים","סלמון בעשבי תיבול","קוגל תפוחי אדמה","שניצל פריך","עוגת גבינה שלוש שכבות"]),
        ]
        for idx,(name,menu_type,guests,selected) in enumerate(sample_events):
            eid=insert_base(cur,"events",["name","event_category","menu_type","status","date","event_time","city","guest_count","is_morning_split","total_price","is_real_dishes","calculated_price","day_sequence_number","has_elevator","has_nearby_parking","has_back_entrance","requires_carts","check_refrigerator","check_freezer","check_hot_plate","connect_gas","put_in_refrigerator","put_in_freezer","put_on_hot_plate","count_boxes","check_drinks","check_rolls"],[name,"אירוע דמה",menu_type,"DRAFT",(datetime.now()+timedelta(days=14+idx*7)).isoformat(sep=" "),"18:00","ירושלים",guests,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
            insert_base(cur,"event_owners",["event_id","name","phone","order"],[eid,"לקוח דמה","050-0000000",0])
            for dname in selected:
                did=dish_ids[dname]; cid=categories[dish_groups[dname]]
                insert_base(cur,"event_dishes",["event_id","dish_id","sub_meal_id","category_id","quantity","is_upgrade","is_gift","extra_charge","notes","is_draft"],[eid,did,None,cid,1,0,0,0,"נתוני בדיקה חדשים",0])
        conn.commit()
        print(f"Seeded {len(product_ids)} products, {len(dish_ids)} dishes, {len(TOOLS)} tools and {len(sample_events)} sample events")
    except Exception:
        conn.rollback(); raise
    finally:
        conn.execute("PRAGMA foreign_keys=ON"); conn.close()

if __name__ == "__main__": main()
