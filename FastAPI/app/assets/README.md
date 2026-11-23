# Assets - קבצי נכסים

## פונטים עבריים

### הורדת פונט Heebo
להורדה מ-Google Fonts:
https://fonts.google.com/specimen/Heebo

1. לחץ על "Download family"
2. חלץ את קבצי ה-TTF לתיקיית `fonts/`
3. שנה שם לקבצים (או עדכן את הנתיבים ב-`pdf_generator.py`):
   - `Heebo-Regular.ttf`
   - `Heebo-Bold.ttf`

### פונטים חלופיים
- **Assistant**: https://fonts.google.com/specimen/Assistant
- **Rubik**: https://fonts.google.com/specimen/Rubik
- **Open Sans Hebrew**: https://fonts.google.com/specimen/Open+Sans

## תמונת בלאנק (רקע לכל הדף)

מקם את תמונת הבלאנק שלך בתיקייה זו בשם:
`blank.png`

### דרישות התמונה:
- **גודל**: A4 (595 x 842 pixels @ 72 DPI, או 2480 x 3508 @ 300 DPI)
- **פורמט**: PNG (מומלץ) או JPEG
- **רקע**: התמונה תמתח לכל הדף!
- **אזורים ריקים לטקסט**: השאר מרווחים לטקסט:
  - למעלה: לפחות 3 ס"מ
  - למטה: לפחות 2.5 ס"מ
  - בצדדים: לפחות 2 ס"מ

### מבנה תיקיות:
```
assets/
├── README.md
├── blank.png           # תמונת בלאנק (רקע לכל הדף)
└── fonts/
    ├── Heebo-Regular.ttf
    └── Heebo-Bold.ttf
```

## עדכון נתיבים

אם הפונטים או הבלאנק נמצאים במיקום אחר, עדכן את הנתיבים בקובץ:
`app/utils/pdf_generator.py`

```python
# נתיב לתמונת בלאנק (רקע לכל הדף)
BLANK_BACKGROUND_PATH = "נתיב/לתמונה/blank.png"

# נתיב לפונט עברי
HEBREW_FONT_PATH = "נתיב/לפונט/Heebo-Regular.ttf"
HEBREW_FONT_BOLD_PATH = "נתיב/לפונט/Heebo-Bold.ttf"
```
