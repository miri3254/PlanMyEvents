# Plan My Events - Backend

מערכת לניהול אירועים - צד שרת

## התקנה

```bash
# התקנת dependencies
pip install -r requirements.txt

# הרצת השרת
uvicorn app.main:app --reload
```

## מבנה הפרויקט

```
├── app/
│   ├── main.py              # נקודת הכניסה הראשית
│   ├── core/                # הגדרות ליבה
│   │   ├── config.py        # הגדרות האפליקציה
│   │   ├── database.py      # חיבור לדאטאבייס
│   │   └── cors.py          # הגדרות CORS
│   ├── models/              # מודלים של SQLAlchemy
│   ├── schemas/             # סכמות Pydantic
│   ├── routers/             # נתיבי API
│   ├── services/            # לוגיקה עסקית
│   └── utils/               # פונקציות עזר
├── data/                    # תיקיית הדאטאבייס
├── alembic/                 # מיגרציות
├── requirements.txt
└── README.md
```

## API Endpoints

- `/api/events` - ניהול אירועים
- `/api/dishes` - ניהול מנות
- `/api/products` - ניהול מוצרים
- `/api/tools` - ניהול כלים
- `/api/lookup` - טבלאות בחירה
- `/api/dashboard` - סטטיסטיקות

## תיעוד API

לאחר הרצת השרת, ניתן לגשת לתיעוד ב:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
