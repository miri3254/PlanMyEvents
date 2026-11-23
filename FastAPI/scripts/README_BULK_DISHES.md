# Bulk Dishes Import Script

## Overview

This script allows you to bulk import dishes from a JSON file into the database with proper upsert logic, ingredient handling, and menu mappings management.

## Features

✅ **Upsert Logic**: Automatically detects existing dishes by name and updates them instead of creating duplicates  
✅ **Ingredient Sync**: Clears old ingredients and replaces them with new ones from JSON  
✅ **Menu Mappings**: Creates or updates many-to-many relationships between dishes and menu types  
✅ **Enum Validation**: Validates `MenuType` enum values from JSON  
✅ **Transaction Safety**: Wraps everything in a database transaction - rolls back on any error  
✅ **Session Flush**: Uses `db.flush()` to get dish IDs before creating foreign key relationships  

## Usage

### From a JSON file:

```bash
python scripts/seed_dishes_bulk.py --file data/dishes_salads.json
```

### From a JSON string:

```bash
python scripts/seed_dishes_bulk.py --json '{"items": [...]}'
```

### From stdin:

```bash
cat data/dishes_salads.json | python scripts/seed_dishes_bulk.py
```

## JSON Format

The JSON file should follow this structure:

```json
{
  "items": [
    {
      "name": "רצועות גזר בתיבול פיקנטי ומנצ'ס",
      "category": "סלטים",
      "kosher_type": "פרווה",
      "description": "גזר פריך בתיבול פיקנטי. מתאים לכ-10 סועדים.",
      "serving_size": 10.0,
      "serving_description": "להגיש בקערה שקופה בינונית.",
      "waiter_notes": "לפזר מנצ'ס מעל רק ברגע ההגשה לשמירה על הפריכות.",
      "is_active": 1,
      "ingredients": [
        {"name": "גזר", "quantity": 1.5, "unit": "קילו"},
        {"name": "מנצ'ס", "quantity": 200, "unit": "גרם"}
      ],
      "menu_mappings": [
        {"menu_type": "SHABBAT", "category_name": "סלטים", "display_order": 1},
        {"menu_type": "SWEET_TABLE", "category_name": "סלטים", "display_order": 1}
      ]
    }
  ]
}
```

### Required Fields:
- `name` - Unique dish name (used for upsert detection)

### Optional Fields:
- `category` - Dish category (e.g., "סלטים", "עיקריות")
- `kosher_type` - Kosher classification ("פרווה", "חלבי", "בשרי")
- `description` - Dish description
- `serving_size` - Number of servings (default: 1.0)
- `serving_description` - How to serve the dish (for waiters)
- `waiter_notes` - Special notes for waiters
- `is_active` - Active status (1 or 0, default: 1)
- `price_per_unit` - Price per unit
- `estimated_price` - Estimated cost
- `client_price` - Price charged to client
- `image_url` - URL to dish image

### Ingredients Array:
Each ingredient can have:
- `name` - Ingredient name (required if no product_id)
- `product_id` - Foreign key to products table (optional)
- `quantity` - Amount needed (default: 1.0)
- `unit` - Unit of measurement (default: "יחידות")

### Menu Mappings Array:
Each mapping represents which menu types include this dish:
- `menu_type` - **REQUIRED** - Must be one of: `SHABBAT`, `MEAT_MENU`, `DAIRY_MENU`, `MEAT_TRAYS`, `DAIRY_TRAYS`, `SWEET_TABLE`
- `category_name` - **REQUIRED** - Category within the menu (e.g., "סלטים")
- `display_order` - Display order within category (default: 0)
- `client_price` - Override price for this menu type
- `estimated_price` - Estimated cost for this menu type
- `is_upgrade` - Is this a premium/upgrade item? (default: false)
- `extra_charge` - Additional charge if upgrade (default: 0.0)

## How It Works

### Flow:

1. **Parse JSON** - Load dishes from file/string/stdin
2. **For each dish:**
   - Check if dish with same `name` exists
   - If exists: **Update** fields
   - If not: **Create** new dish
3. **Flush session** - Get the dish ID for foreign keys
4. **Sync ingredients:**
   - Delete all existing ingredients
   - Add new ingredients from JSON
5. **Sync menu mappings:**
   - For each mapping in JSON:
     - Check if combo of `dish_id + menu_type + category_name` exists
     - If exists: **Update** fields
     - If not: **Create** new mapping
   - Note: Does NOT delete existing mappings not in JSON
6. **Commit transaction** - Save all changes

### Transaction Safety:

If ANY dish fails to process, the entire transaction is rolled back to keep the database clean.

## Examples

### Example 1: Import salads

```bash
python scripts/seed_dishes_bulk.py --file data/dishes_salads.json
```

Output:
```
🚀 Starting bulk import of 39 dishes...

[1/39] Processing: רצועות גזר בתיבול פיקנטי ומנצ'ס
  ✨ Creating new dish: רצועות גזר בתיבול פיקנטי ומנצ'ס
    🥗 Synced 2 ingredients
    📋 Synced 3 menu mappings
    ✅ Success!

...

🎉 Bulk import completed successfully!
   ✅ 39 dishes processed
```

### Example 2: Update existing dishes

Running the same file again will update existing dishes:

```bash
python scripts/seed_dishes_bulk.py --file data/dishes_salads.json
```

Output:
```
[1/39] Processing: רצועות גזר בתיבול פיקנטי ומנצ'ס
  ♻️  Updating existing dish: רצועות גזר בתיבול פיקנטי ומנצ'ס
    🥗 Synced 2 ingredients
    📋 Synced 3 menu mappings
    ✅ Success!
```

## Error Handling

### Invalid MenuType:

```json
{"menu_type": "INVALID_MENU"}
```

Will raise:
```
❌ Validation Error: Invalid menu_type: INVALID_MENU. Valid values: ['SHABBAT', 'MEAT_MENU', 'DAIRY_MENU', 'MEAT_TRAYS', 'DAIRY_TRAYS', 'SWEET_TABLE']
```

### Transaction Rollback:

If any error occurs, all changes are rolled back:
```
❌ Transaction rolled back due to error!
   Error: ...
   ✅ 15 dishes processed before error
   ❌ 1 dishes failed
```

## Technical Details

### Database Configuration:
- Uses `SessionLocal()` with `autoflush=False` to prevent premature foreign key errors
- Calls `db.flush()` after dish creation to get the dish ID
- Wraps entire operation in a transaction

### Enum Mapping:
- Converts string `menu_type` from JSON to `MenuType` enum using `MenuType[mapping['menu_type']]`

### Ingredient Handling:
- Clears existing ingredients before adding new ones to avoid duplicates
- Supports both `product_id` (FK to products) and plain text `name`

### Menu Mapping Logic:
- Checks for existing mappings by `(dish_id, menu_type, category_name)` tuple
- Updates if exists, creates if not
- Does NOT delete mappings not in the current JSON (preserves other menu associations)

## Files

- **Script**: `scripts/seed_dishes_bulk.py`
- **Sample JSON**: `data/dishes_salads.json`
- **Models**: `app/models/dish.py`, `app/models/menu_template.py`

## Notes

⚠️ **Important**: The script identifies dishes by `name`. If you change the name of a dish, it will create a new dish instead of updating the existing one.

💡 **Tip**: Keep your JSON files organized by category (salads, mains, desserts, etc.) for easier management.
