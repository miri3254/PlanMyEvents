from pathlib import Path
from datetime import datetime
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import text
from app.db.engine import engine
from app.db.session import SessionLocal
from app.models.dish import Dish
from app.models.menu import MenuTemplate, MenuCategory, DishMenuMapping
from app.core.enums import KosherType

N=lambda s: re.sub(r'[^\w]', '', (s or '').replace('תפוא','תפוחיאדמה').replace('סלומון','סלמון').lower())
SETS={
'בשרי':{'סלטים':['חומוס','חסה שרי פטריות ונבטים','מיקס כרובים','סירות חציל וטחינה','שרי עגבניות וזיתים'],'ראשונות':['פילו ירקות','טורטיה תפוחי אדמה ופטריות'],'תוספות':['אורז אגוזים וחמוציות','תפוחי אדמה פריזיאני פיקנטי','אנטיפסטי ירקות'],'עיקריות':['כרעיים ברביקיו','שניצל פריך','סטייק חזה'],'קינוחים':['מוס משובח','מקרונים','טארטלטים ממולאים']},
'ליל שבת':{'סלטים':['חומוס','חסה שרי פטריות ונבטים','מיקס כרובים','סירות חציל וטחינה','מטבוחה'],'ראשונות':['סלמון בסילאן ושקדים','מושט פיקנטי חריף'],'תוספות':['אורז אגוזים וחמוציות','תפוחי אדמה פריזיאני פיקנטי','אנטיפסטי ירקות'],'עיקריות':['כרעיים ברביקיו','חזה ממולא','סטייק חזה'],'קינוחים':['מיקס קינוחים']},
'שולחן מתוק':{'סלטים':['חומוס הבית','חסה שרי פטריות ונבטים','מיקס כרובים','סירות חציל וטחינה','שרי ועגבניות פיקנטי'],'ראשונות':['בלינצס תפוחי אדמה','טורטיה בציפוי פריך','פילו ירקות'],'תוספות':['אורז אגוזים וחמוציות','פשטידה אישית','נודלס ירקות מוקפץ','קוגל תפוחי אדמה','קוגל אטריות','צולנט פרווה','תפוחי אדמה אפוי פיקנטי']},
'שבת יום':{'סלטים':['חומוס','סחוג פיקנטי','עגבניות שרי וזיתים פיקנטי','סלט פטריות מוקפץ','חציל קוביות פיקנטי','רצועות בטטה בצילי ובוטנים'],'ראשונות':['ביצים וכבד בהגשה אישית'],'תוספות':['צולנט עם בשר','קישקע','קוגל אטריות'],'עיקריות':['שניצלים','פרוסות פסטרמה ביתית בסגנון שווארמה'],'קינוחים':['מיקס קינוחים']}}
MENUS=[('תפריט מנצח בשרי לשליחה לדוגמא ללקוח (1)','בשרי',60,'בשרי'),('תפריט מנצח בשרי לשליחה לדוגמא ללקוח (2)','בשרי',60,'בשרי'),('תפריט מנצח ליל שבת (1)','ליל שבת',70,'בשרי'),('תפריט מנצח ליל שבת (2)','ליל שבת',70,'בשרי'),('תפריט מנצח לשליחה שולחן מתוק (1)','שולחן מתוק',1,'פרווה'),('תפריט מנצח לשליחה שולחן מתוק (2)','שולחן מתוק',1,'פרווה'),('תפריט מנצח שבת יום (1)','שבת יום',70,'בשרי'),('תפריט מנצח שבת יום (2)','שבת יום',70,'בשרי')]
def run():
 db=SessionLocal(); ds={N(x.name):x for x in db.query(Dish).filter(Dish.is_deleted.is_(False))}
 def get(n,k):
  if N(n) not in ds: ds[N(n)]=Dish(name=n,description='מקור: תפריט לקוח.',notes='נוצר מתפריט מקור; מתכון מפורט חסר.',kosher_type=KosherType(k),is_active=True);db.add(ds[N(n)]);db.flush()
  return ds[N(n)]
 for title,kind,minn,k in MENUS:
  if db.query(MenuTemplate).filter_by(menu_type=title).first():continue
  m=MenuTemplate(menu_type=title,name=title,min_guests=minn,kosher_type=k);db.add(m);db.flush()
  for ci,(cat,names) in enumerate(SETS[kind].items()):
   c=MenuCategory(template_id=m.id,name=f'קטגוריה {ci+1}',name_hebrew=cat,display_order=ci,is_required=False);db.add(c);db.flush()
   for di,n in enumerate(names):db.add(DishMenuMapping(category_id=c.id,dish_id=get(n,k).id,display_order=di))
 db.commit();print('done')
if __name__=='__main__':run()
