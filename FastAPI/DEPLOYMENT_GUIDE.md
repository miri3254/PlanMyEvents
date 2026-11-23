# Menu System Deployment Guide

## Complete Backend Setup - Step by Step

### Prerequisites
- FastAPI server stopped
- Database backup recommended (optional, but safe)

---

## Step 1: Run Database Migration

```powershell
cd FastAPI
alembic upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Running upgrade b15919c3c20e -> 20260204_131451, add_menu_system
```

**What this does:**
- Creates `menu_templates` table
- Creates `menu_categories` table  
- Creates `dish_menu_mappings` table
- Adds `menu_type` column to `events` table
- Adds `is_draft` column to `event_dishes` table
- Migrates existing event_type data to menu_type

---

## Step 2: Reset Old Data (DESTRUCTIVE)

⚠️ **WARNING:** This deletes all existing dishes and event_dishes!

```powershell
python scripts/reset_data.py
```

**Expected Output:**
```
🗑️  Resetting data...
   ✅ Deleted X dishes
   ✅ Deleted X event_dishes
   ✅ Reset lookup_data: event_types → menu_types
✨ Data reset complete!
```

**What this does:**
- Deletes all dishes
- Deletes all event_dishes relationships
- Updates lookup_data to replace "event_types" with "menu_types"

---

## Step 3: Seed Menu Templates

```powershell
python scripts/seed_menu_templates.py
```

**Expected Output:**
```
🌱 Starting menu template seeding...
✅ Created template: שבת מלא (SHABBAT)
   📁 Added category: סלטים (quota: 5)
   📁 Added category: דגים (מנה ראשונה) (quota: 2)
   📁 Added category: עיקריות (quota: 2)
   📁 Added category: תוספות (quota: 3)
   📁 Added category: קינוחים (quota: 1)
✅ Created template: תפריט בשרי (MEAT_MENU)
   ... (and so on for all 6 templates)

✨ Seeding complete!
   Templates created: 6
   Categories created: 23
```

**What this does:**
- Creates 6 menu templates: SHABBAT, MEAT_MENU, DAIRY_MENU, MEAT_TRAYS, DAIRY_TRAYS, SWEET_TABLE
- Creates all categories with exact quotas from your menu specifications
- Sets display order and required flags

---

## Step 4: Seed Full Dish Data

```powershell
python scripts/seed_dishes_from_menus.py
```

**Expected Output:**
```
🌱 Starting dish and mapping seeding...

📁 Creating Salads...
   ✅ Created 39 salad dishes

📁 Creating Dairy-Specific Salads...
   ✅ Created 5 dairy salad dishes

📁 Creating Fish Dishes...
   ✅ Created 9 fish dishes

📁 Creating Shabbat Main Courses...
   ✅ Created 15 main course dishes

📁 Creating Side Dishes...
   ✅ Created 18 side dishes

📁 Creating Pastry Dishes...
   ✅ Created 9 pastry dishes

📁 Creating Soup Dishes...
   ✅ Created 5 soup dishes

📁 Creating Dairy Main Dishes...
   ✅ Created 12 dairy main dishes

📁 Creating Dessert Dishes...
   ✅ Created 5 dessert dishes

📁 Creating Meat Tray Items...
   ✅ Created 7 meat tray items

✨ Seeding complete!
   Dishes created: ~120+
   Menu mappings created: ~250+

📋 Database is ready with full menu data!
```

**What this does:**
- Creates all dishes from your menu specifications
- Creates dish_menu_mappings linking each dish to appropriate menu_type(s) and categories
- Marks premium items (Salmon Menu, Beef #5, etc.) as `is_upgrade=True` with `extra_charge`
- Sets correct display_order for each dish within its category

---

## Step 5: Verify Installation

### Test API Endpoints

```powershell
# Start server
uvicorn app.main:app --reload

# In another terminal or browser, test:
```

**Test 1: Get all menu templates**
```
GET http://localhost:8000/api/menus/templates
```

**Test 2: Get SHABBAT template with categories**
```
GET http://localhost:8000/api/menus/SHABBAT/template
```
Expected: JSON with 5 categories (salads, fish, main_course, sides, desserts)

**Test 3: Get salads for SHABBAT**
```
GET http://localhost:8000/api/menus/SHABBAT/categories/salads/dishes
```
Expected: 39 standard salad dishes + quota info

**Test 4: Get main courses for SHABBAT with quota adjustment**
```
GET http://localhost:8000/api/menus/SHABBAT/categories/main_course/dishes/with-quota?guest_count=90
```
Expected: Quota should be 3 (not 2) because guest_count > 80

---

## Verification Checklist

✅ **Database Tables Created:**
- [ ] `menu_templates` (6 rows)
- [ ] `menu_categories` (23 rows)
- [ ] `dish_menu_mappings` (250+ rows)
- [ ] `events.menu_type` column exists
- [ ] `event_dishes.is_draft` column exists

✅ **Menu Templates:**
- [ ] SHABBAT: 5 categories (salads:5, fish:2, main:2, sides:3, desserts:1)
- [ ] MEAT_MENU: 5 categories
- [ ] DAIRY_MENU: 5 categories
- [ ] MEAT_TRAYS: 3 categories
- [ ] DAIRY_TRAYS: 3 categories
- [ ] SWEET_TABLE: 3 categories

✅ **Dishes Seeded:**
- [ ] 39 salads (mapped to SHABBAT, SWEET_TABLE)
- [ ] 5 dairy salads (mapped to DAIRY_MENU)
- [ ] 9 fish dishes (mapped to SHABBAT, DAIRY_MENU)
- [ ] 15 main courses (mapped to SHABBAT, MEAT_MENU)
- [ ] 18 sides
- [ ] 9 pastries
- [ ] 5 soups
- [ ] 12 dairy mains
- [ ] 5 desserts
- [ ] 7 meat trays

✅ **Upgrades Marked:**
- [ ] "תפריט סלמון מלא" (All Salmon Menu) - SHABBAT fish upgrade
- [ ] "פרוסות בקר #5" (Beef #5) - SHABBAT/MEAT_MENU main upgrade
- [ ] "דג בציפוי אגוזים" (Nut-crust Fish) - DAIRY_MENU upgrade
- [ ] "פלפלים סילאן" (Silan Peppers) - DAIRY_MENU upgrade
- [ ] "תוספת גבינה" (Extra Cheese) - DAIRY_MENU upgrade

✅ **Business Logic:**
- [ ] MenuService.apply_guest_count_rules works
- [ ] SHABBAT/MEAT_MENU: guest_count > 80 → main_course quota = 3
- [ ] Validation returns soft quotas (not hard blocks)

---

## Common Issues & Fixes

### Issue: "Table already exists" during migration
**Fix:**
```powershell
alembic downgrade -1
alembic upgrade head
```

### Issue: Seed script fails with "Dish not found"
**Fix:** Run scripts in order:
1. Migration first
2. Reset data second
3. Templates third
4. Dishes last

### Issue: API returns empty dishes array
**Fix:** Check dish_menu_mappings were created:
```sql
SELECT COUNT(*) FROM dish_menu_mappings WHERE menu_type = 'SHABBAT';
```
Should return 100+

---

## Next Steps: Frontend Integration

Once backend is verified, proceed to:
1. Update Angular Event model to use `menuType` instead of `eventType`
2. Create MenuService in Angular
3. Transform DishesComponent into guided wizard
4. Update EventsComponent form with menu type selector

**Backend is now fully ready for menu-driven catering! 🎉**
