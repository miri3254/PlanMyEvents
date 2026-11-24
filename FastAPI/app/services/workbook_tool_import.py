"""Repeatable, additive mappings reviewed against BOTH original tool sheets.

Only exact reviewed dish names are matched. Existing owner variants/layouts win.
No stock quantities, prices, event selections or snapshots are rewritten.
"""
from app.models.tool import Tool
from app.models.dish import Dish
from app.models.menu import MenuTemplate
from app.models.product import Product
from app.models.calculation import DishServingSet, DishServingSetItem
from app.core.enums import ToolCategory, ToolSubCategory, UnitType
from app.services.table_setting_rules import default_table_setting_items

# aliases, disposable vessel/row, real vessel/row, utensil
CENTRAL = [
    (['סלט מיקס כרובים'], 'קערה גלאס', 17, 'קערה לכרוב', 15, 'כף יפה'),
    (['סלט חסה מתוק', 'סלט חסה שרי ופטריות'], 'קערה שקופה עגולה גדולה', 18, 'קערה לחסה', 16, 'כף יפה'),
    (['סלט גזר מעודן', 'סלט גזר פיקנטי', 'סלט שרי'], 'מרקית מהסט של העריכה', 21, 'מרקית לסלט', 19, 'כפית יפה'),
    (['טורטיות ירקות ופירה'], 'אובל נמוך', 31, 'אובל נמוך', 29, 'כף יפה'),
    (["בלינצ'ס שמנת"], 'אובל נמוך', 32, 'אובל נמוך', 30, 'כף יפה'),
    (['פלפל ממולא'], 'אובל עמוק', 33, 'אובל עמוק', 31, 'כף יפה'),
    (['שניצל פריך'], 'אובל נמוך', 41, 'אובל נמוך', 39, 'כף יפה'),
    (['עוף ברביקיו'], 'אובל עמוק', 42, 'אובל עמוק', 40, 'כף יפה'),
    (['סלמון בעשבי תיבול'], 'אובל עמוק', 43, 'אובל עמוק', 41, 'כף יפה'),
    (['אורז עם ירקות'], 'קערה כלנית', 47, 'קערה לאורז', 45, 'כף יפה'),
    (['תפוחי אדמה פריזיאניים', 'תפוחי אדמה מוקרמים'], 'קערה כלנית', 48, 'קערה לתפו"א', 46, 'כף יפה'),
    (['שעועית ירוקה ושומשום'], 'מרקית מהסט של העריכה', 49, 'מרקית או קערה דומה לשעועית', 47, 'כף יפה'),
    (['פסטה מוקרמת'], 'קערה כלנית', 50, 'קערה לפסטה', 48, 'כף יפה'),
    (['קוגל תפוחי אדמה'], 'אובל עמוק', 51, 'אובל עמוק', 49, 'כף יפה'),
    (['פשטידת פטריות וגבינות', 'פשטידת קישואים'], 'אובל נמוך', 54, 'אובל נמוך', 52, 'כף יפה'),
]
PERSONAL = [(['טורטיות ירקות ופירה'], 27, 25), (["בלינצ'ס שמנת"], 28, 26), (['פלפל ממולא'], 29, 27)]
SOURCE = 'workbook:32d788fd:tools:v1'

def prepare_workbook_tools(db):
    stats = dict(tools_created=0, variants_created=0, menus_linked=0, products_created=0)
    def tool(name, kind):
        material = ToolSubCategory.REAL if kind == 'real' else ToolSubCategory.DISPOSABLE
        label = name + (' — אמיתי' if kind == 'real' else ' — חד פעמי')
        candidates = db.query(Tool).filter(Tool.name.in_([name, label]), Tool.sub_category == material, Tool.is_deleted == False).all()
        if len(candidates) > 1:
            raise ValueError('Ambiguous inventory link: ' + label)
        if candidates:
            return candidates[0]
        result = Tool(name=label, sub_category=material, category=ToolCategory.SERVING,
                      description=SOURCE, quantity_in_stock=0, price_per_unit=0)
        db.add(result); db.flush(); stats['tools_created'] += 1
        return result

    # User clarified 2026-11-23: a product name, NOT a quantity multiplier.
    tool('קערה שקופה כפולה', 'disposable')

    dishes = db.query(Dish).filter(Dish.is_deleted == False, Dish.is_active == True).all()
    def add(names, kind, mode, row, items):
        for dish in [d for d in dishes if d.name in names]:
            existing = db.query(DishServingSet).filter_by(dish_id=dish.id, set_type='serving', dishware_type=kind, is_deleted=False).all()
            if any(s.serving_mode == mode for s in existing):
                continue
            sheet = 'חישוב כלים אמיתיים' if kind == 'real' else 'חישוב כלים'
            variant = DishServingSet(dish_id=dish.id, name='הגשה ' + ('מרכזית' if mode == 'central' else 'אישית'),
                dishware_type=kind, serving_mode=mode, set_type='serving', is_default=not existing,
                notes=f'{SOURCE}; {sheet}, B{row}:D{row}. ניתן לשנות את הקישור והכמויות.')
            db.add(variant); db.flush()
            for name, basis in items:
                linked = tool(name, kind)
                db.add(DishServingSetItem(set_id=variant.id, tool_id=linked.id, name=linked.name,
                    quantity=1, quantity_basis=basis))
            stats['variants_created'] += 1

    for names, disposable, drow, real, rrow, utensil in CENTRAL:
        for kind, vessel, row in [('disposable', disposable, drow), ('real', real, rrow)]:
            add(names, kind, 'central', row, [(vessel, 'serving_group'), (utensil, 'serving_group')])
    for names, drow, rrow in PERSONAL:
        for kind, row in [('disposable', drow), ('real', rrow)]:
            add(names, kind, 'personal', row, [('צלחת שקופה פשוטה' if kind == 'disposable' else 'צלחת פשוטה', 'place_setting'), ('מזלג פשוט', 'place_setting')])
    for kind, row in [('disposable', 26), ('real', 24)]:
        add(['מרק כתום'], kind, 'personal', row, [('מרקית אישית', 'place_setting'), ('כף יפה', 'place_setting'),
            ('קסרול לקרוטונים', 'serving_group'), ('כפית יפה', 'serving_group')])

    for menu in db.query(MenuTemplate).filter_by(is_deleted=False, is_tray_menu=False):
        # Null means untouched defaults; an explicit list (including []) is owner's data.
        if menu.table_setting_items is not None:
            continue
        items = default_table_setting_items(menu.tablecloth_profile)
        items.append(dict(name='קערה ללחמניות', quantity=1, quantity_basis='serving_group'))
        if menu.tablecloth_profile == 'sweet':
            items.append(dict(name='קסרול שקוף למציות', quantity=1, quantity_basis='serving_group'))
        for item in items:
            name = {'קערה ללחמניות': 'קערה', 'קסרול שקוף למציות': 'קסרול שקוף'}.get(item['name'], item['name'])
            for kind in ('disposable', 'real'):
                # Napkins stay disposable, including a real-dishware event.
                item[kind+'_tool_id'] = tool(name, 'disposable' if name == 'מפית' else kind).id
        menu.table_setting_items = items
        stats['menus_linked'] += 1
    if not db.query(Product).filter_by(name='מציות', is_deleted=False).first():
        db.add(Product(name='מציות', unit=UnitType.BUNDLE, quantity_in_stock=0,
            description='חישוב מציות, C4:C5; חבילות שלמות בעיגול למעלה. '+SOURCE))
        stats['products_created'] += 1
    db.flush()
    return stats
