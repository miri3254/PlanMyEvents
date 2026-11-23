import os, sys, pathlib, json, ast, operator, math, zipfile, xml.etree.ElementTree as ET
base=pathlib.Path(__file__).parent
data=json.loads((base/'source.json').read_text(encoding='utf8'))
ops={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv}
verified=[]
for sheet in data['sheets']:
    cells={c['ref']:c for r in sheet['rows'] for c in r['cells']}
    def calc(ref):
        c=cells[ref]
        if c['formula'] is None: return float(c['value'])
        def walk(n):
            if isinstance(n,ast.Expression): return walk(n.body)
            if isinstance(n,ast.Constant): return n.value
            if isinstance(n,ast.Name): return calc(n.id)
            if isinstance(n,ast.BinOp): return ops[type(n.op)](walk(n.left),walk(n.right))
            raise ValueError(ast.dump(n))
        return walk(ast.parse(c['formula'],mode='eval'))
    for c in cells.values():
        if c['formula'] is not None:
            value=calc(c['ref']); cached=float(c['value'])
            assert math.isclose(value,cached,rel_tol=1e-12,abs_tol=1e-9),(sheet['name'],c)
            verified.append({'sheet':sheet['name'],'cell':c['ref'],'calculated':value,'cached':cached})
os.environ['DATABASE_URL']='sqlite://'
sys.path.insert(0,str(base.parents[2]/'FastAPI'))
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import app.models
from app.db.base import Base
from app.models.event import Event, EventDish
from app.models.dish import Dish
from app.models.calculation import DishCalculationRule
from app.services.event_calculation_service import EventCalculationService
from app.schemas.calculation import EventCalculationSettingsUpdate
from app.core.enums import EventStatus
from datetime import datetime
engine=create_engine('sqlite://')
Base.metadata.create_all(engine)
observed=[]
with Session(engine) as db:
    service=EventCalculationService(db)
    for label,category,split in [('regular','אירוע רגיל',False),('sweet','שולחן מתוק',False),('shabbat','שבת',False),('split','שבת',True)]:
        event=Event(name=label,event_category=category,menu_type=category,guest_count=70,is_morning_split=split,status=EventStatus.DRAFT,date=datetime(2026,11,17))
        db.add(event);db.flush()
        s=service.summarize(event)
        observed.append({'case':label,'products':[{ 'name':x.name,'qty':x.quantity} for x in s.product_requirements],'cloths':[x.quantity for x in s.tool_requirements if x.source_type=='tablecloths'],'tables':s.table_count})
    for cat in ['אירוע רגיל','שולחן מתוק']:
        event=Event(name='garnish',event_category=cat,menu_type=cat,guest_count=250,status=EventStatus.DRAFT,date=datetime(2026,11,17))
        dish=Dish(name='סלט חסה לבדיקה');db.add_all([event,dish]);db.flush()
        db.add(EventDish(event_id=event.id,dish_id=dish.id,quantity=1));db.add(DishCalculationRule(dish_id=dish.id,rule_type='salad_garnish',name='פקאן לבדיקה',params={'quantity_per_bowl':60,'unit':'גרם'},is_active=True));db.flush();db.refresh(event)
        s=service.summarize(event)
        observed.append({'case':'garnish '+cat,'rows':[x.model_dump() for x in s.product_requirements if x.source_type=='salad_garnish']})
(base/'verification.json').write_text(json.dumps({'formulas_checked':len(verified),'all_cached_match':True,'rows':sum(len(s['rows']) for s in data['sheets']),'cells':sum(len(r['cells']) for s in data['sheets'] for r in s['rows']),'observed':observed},ensure_ascii=False,indent=2),encoding='utf8')
print('Formula checks:',len(verified),'passed; isolated service scenarios:',len(observed))
