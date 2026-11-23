import zipfile, xml.etree.ElementTree as ET, json, pathlib, hashlib
src=pathlib.Path(r'C:\Users\User\Desktop\Downloads\© חישובים  קיטרינג גינסברגר  © (3).xlsx')
out=pathlib.Path(__file__).parent
ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(src) as z:
    strings=[]
    if 'xl/sharedStrings.xml' in z.namelist():
        strings=[''.join(e.itertext()) for e in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',ns)]
    rels={r.attrib['Id']:r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    wb=ET.fromstring(z.read('xl/workbook.xml'))
    result={'source':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'sheets':[], 'names':[e.attrib|{'text':e.text} for e in wb.findall('m:definedNames/m:definedName',ns)],'extras':[n for n in z.namelist() if any(t in n for t in ['comments','drawings','externalLinks','vba','pivot'])]}
    for s in wb.findall('m:sheets/m:sheet',ns):
        target=rels[s.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
        target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
        root=ET.fromstring(z.read(target)); rows=[]
        for r in root.findall('m:sheetData/m:row',ns):
            cells=[]
            for c in r.findall('m:c',ns):
                v=c.find('m:v',ns); f=c.find('m:f',ns); inline=c.find('m:is',ns)
                val=v.text if v is not None else None
                if c.get('t')=='s' and val is not None: val=strings[int(val)]
                if inline is not None: val=''.join(inline.itertext())
                if val is not None or f is not None:
                    cells.append({'ref':c.get('r'),'value':val,'formula':f.text if f is not None else None,'formula_attrs':f.attrib if f is not None else None,'type':c.get('t'),'style':c.get('s')})
            if cells: rows.append({'row':int(r.get('r')),'hidden':r.get('hidden'),'cells':cells})
        sheet={'name':s.get('name'),'state':s.get('state','visible'),'dimension':root.find('m:dimension',ns).get('ref'),'rows':rows,'merges':[e.get('ref') for e in root.findall('m:mergeCells/m:mergeCell',ns)],'validations':[ET.tostring(e,encoding='unicode') for e in root.findall('m:dataValidations',ns)],'columns':[e.attrib for e in root.findall('m:cols/m:col',ns)]}
        result['sheets'].append(sheet)
    (out/'source.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    lines=[]
    for i,s in enumerate(result['sheets'],1):
        lines.append(f"\n=== {i}. {s['name']} [{s['state']}] {s['dimension']} ===")
        for r in s['rows']:
            lines.append(str(r['row'])+': '+' | '.join(c['ref']+' '+str(c['value'])+((' FORMULA='+str(c['formula'])+' '+str(c['formula_attrs'])) if c['formula_attrs'] is not None else '') for c in r['cells']))
    (out/'rows.txt').write_text('\n'.join(lines),encoding='utf8')
    print(json.dumps({'sheets':[{'name':s['name'],'range':s['dimension'],'rows':len(s['rows']),'cells':sum(len(r['cells']) for r in s['rows']),'formulas':sum(c['formula_attrs'] is not None for r in s['rows'] for c in r['cells'])} for s in result['sheets']],'extras':result['extras'],'names':result['names']},ensure_ascii=False))
