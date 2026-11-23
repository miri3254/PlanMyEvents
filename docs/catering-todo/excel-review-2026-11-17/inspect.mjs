import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile} from '@oai/artifact-tool';
const base=new URL('.',import.meta.url);
const source=JSON.parse(await fs.readFile(new URL('source.json',base),'utf8'));
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(source.source));
console.log((await wb.inspect({kind:'workbook,sheet,table',maxChars:3500,tableMaxRows:2,tableMaxCols:4})).ndjson);
const img=await wb.render({sheetName:source.sheets[0].name,range:'B4:J12',scale:1.5,format:'png'});
await fs.writeFile(new URL('drinks-preview.png',base),new Uint8Array(await img.arrayBuffer()));
