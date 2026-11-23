"""Workbook E8:E9: menu place settings, with editable inventory links."""
def default_table_setting_items(profile):
    sweet = profile == 'sweet'
    roles = [('צלחת קטנה יפה', 1), ('צלחת גדולה יפה', 0 if sweet else 1),
             ('כוס יפה', 1), ('מפית', 1), ('סכין יפה', 1 if sweet else 2),
             ('מזלג יפה', 1 if sweet else 2)]
    return [dict(name=name, quantity=quantity, disposable_tool_id=None, real_tool_id=None)
            for name, quantity in roles if quantity]
