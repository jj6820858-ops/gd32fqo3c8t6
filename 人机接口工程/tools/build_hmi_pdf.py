"""Generate individual submission parts and merge in the course-required order."""
from pathlib import Path
import re, json, shutil, hashlib, zipfile
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from pypdf import PdfReader, PdfWriter
import fitz

root=Path(__file__).resolve().parents[1]
output=root/'output/pdf'; parts=output/'parts'; qa=root/'tmp/pdfs'
parts.mkdir(parents=True,exist_ok=True); qa.mkdir(parents=True,exist_ok=True)
pdfmetrics.registerFont(TTFont('CN',r'C:\Windows\Fonts\simhei.ttf'))
pdfmetrics.registerFont(TTFont('Mono',r'C:\Windows\Fonts\consola.ttf'))
body=ParagraphStyle('body',fontName='CN',fontSize=10.2,leading=16,
                    wordWrap='CJK',spaceAfter=6)
heading=ParagraphStyle('heading',parent=body,fontSize=13,leading=20,spaceBefore=12)
title=ParagraphStyle('title',parent=body,fontSize=17,leading=25,spaceAfter=15)
small=ParagraphStyle('small',parent=body,fontSize=8.4,leading=12)
def para(text,style=body):
    text=escape(text.strip())
    text=re.sub(r'`([^`]+)`',r'\1',text)
    return Paragraph(text,style)
def footer(c,doc):
    c.setFont('CN',8); c.setFillColor(colors.HexColor('#667085'))
    c.drawString(42,25,'基础模块02_人机接口 | V1.1 | 2026-10-09 | 待原理图整改')
    c.drawRightString(A4[0]-42,25,f'{doc.page}')
def markdown_pdf(source,target):
    lines=source.read_text(encoding='utf-8-sig').splitlines(); story=[]; i=0
    while i<len(lines):
        line=lines[i].strip()
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                cells=[s.strip() for s in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[-:]+',s) for s in cells): rows.append(cells)
                i+=1
            n=len(rows[0]); widths=([45,154,164,148] if n==4 else [66,103,64,100,178])
            table=Table([[para(s,small) for s in r] for r in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E8EEF6')),
                ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#CDD5DF')),
                ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),
                ('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),6),
                ('BOTTOMPADDING',(0,0),(-1,-1),6)]))
            story.extend([table,Spacer(1,8)]); continue
        if line.startswith('# '): story.append(para(line[2:],title))
        elif line.startswith('## '): story.append(para(line[3:],heading))
        elif line: story.append(para(line))
        i+=1
    SimpleDocTemplate(str(target),pagesize=A4,rightMargin=42,leftMargin=42,
                      topMargin=38,bottomMargin=44).build(story,onFirstPage=footer,onLaterPages=footer)

def pieces(text,size=8.5):
    """Exact character runs with font fallback; no content elision."""
    runs=[]
    for char in text:
        font='Mono' if ord(char)<128 else 'CN'
        if runs and runs[-1][0]==font: runs[-1][1]+=char
        else: runs.append([font,char])
    return runs
def width(text,size=8.5):
    return sum(pdfmetrics.stringWidth(t,f,size) for f,t in pieces(text,size))
def draw(c,x,y,text,size=8.5):
    for font,t in pieces(text,size):
        c.setFont(font,size); c.drawString(x,y,t); x+=pdfmetrics.stringWidth(t,font,size)
def code_pdf(source,target):
    c=canvas.Canvas(str(target),pagesize=A4)
    c.setTitle(source.name+' | 基础模块02_人机接口')
    page=0; y=0
    def newpage():
        nonlocal page,y
        if page: c.showPage()
        page+=1; y=A4[1]-70
        c.setFont('CN',13); c.setFillColor(colors.HexColor('#173354'))
        c.drawString(36,A4[1]-35,source.name+' | 基础模块02_人机接口')
        c.setFont('CN',8); c.setFillColor(colors.HexColor('#667085'))
        c.drawString(36,A4[1]-49,'源码完整导出 | V1.1 / 2026-10-09 | 各函数责任成员见注释')
        c.drawRightString(A4[0]-36,24,str(page)); c.setFillColor(colors.black)
    newpage()
    for no,line in enumerate(source.read_text(encoding='utf-8-sig').splitlines(),1):
        remaining=line.expandtabs(4); chunks=[]; chunk=''
        for ch in remaining:
            if width(chunk+ch)>A4[0]-100:
                chunks.append(chunk); chunk=''
            chunk+=ch
        chunks.append(chunk)
        for j,t in enumerate(chunks):
            if y<45: newpage()
            c.setFillColor(colors.HexColor('#8492A6'))
            c.setFont('Mono',7); c.drawRightString(56,y,str(no) if j==0 else '>')
            c.setFillColor(colors.black); draw(c,66,y,t); y-=12
    c.save()

report=parts/'01_阶段任务分工说明.pdf'
markdown_pdf(root/'document/基础模块02_人机接口_任务分工与交付说明.md',report)
sequence=[report]
code_names=['key.h','key.c','oled.h','oled.c','hmi_port.h','hmi_port.c','hmi_demo.c']
for no,name in enumerate(code_names,2):
    target=parts/f'{no:02d}_{name}.pdf'; code_pdf(root/'HARDWARE/HMI'/name,target)
    sequence.append(target)
schematic=parts/'09_立创EDA原始导出原理图.pdf'
shutil.copyfile(r'C:\Users\lenovo\Downloads\SCH_Schematic1_1_2026-10-09.pdf',schematic)
sequence.append(schematic)
merged=output/'项目班1-1直接测周法频率计基础模块02_人机接口何玉V1.1.pdf'
writer=PdfWriter(); manifest=[]; first=1
for path in sequence:
    reader=PdfReader(path); writer.append(reader,outline_item=path.stem)
    manifest.append({'file':path.name,'first_page':first,'pages':len(reader.pages),
                     'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    first+=len(reader.pages)
writer.add_metadata({'/Title':merged.stem,'/Author':'何玉；蒋观海；吕朋聪；张桂河；蓬晶晶',
                     '/Subject':'基础模块02_人机接口；驱动验证材料；原理图待整改'})
with merged.open('wb') as f: writer.write(f)
(output/'合并顺序与校验.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
# Render every page for visual review and make overview sheets.
from PIL import Image,ImageDraw
d=fitz.open(merged)
thumbs=[]
for index,p in enumerate(d):
    pix=p.get_pixmap(matrix=fitz.Matrix(1,1))
    png=qa/f'page_{index+1:02d}.png'; pix.save(png)
    im=Image.open(png).convert('RGB'); im.thumbnail((298,421))
    tile=Image.new('RGB',(318,451),'#dde3ea'); tile.paste(im,((318-im.width)//2,5))
    ImageDraw.Draw(tile).text((12,430),f'Page {index+1}',fill='black'); thumbs.append(tile)
for start in range(0,len(thumbs),12):
    sheet=Image.new('RGB',(318*4,451*3),'white')
    for j,im in enumerate(thumbs[start:start+12]): sheet.paste(im,((j%4)*318,(j//4)*451))
    sheet.save(qa/f'overview_{start//12+1}.png')
text=''.join(p.get_text() for p in d)
assert '何玉' in text and '吕朋聪' in text and '蒋观海' in text
assert len(d)==sum(p['pages'] for p in manifest)
assert len(PdfReader(schematic).pages)==3
assert schematic.read_bytes()==Path(r'C:\Users\lenovo\Downloads\SCH_Schematic1_1_2026-10-09.pdf').read_bytes()
for name in code_names:
    source=(root/'HARDWARE/HMI'/name).read_text(encoding='utf-8-sig')
    funcs=re.findall(r'^(?:static )?(?:void|int|uint8_t|uint32_t|key_value_t|oled_status_t)\s+(\w+)\([^;]*\)\s*\{',source,re.M)
    for fn in funcs: assert f'首次实现 {fn}' in source,(name,fn)
(output/'PDF检查记录.txt').write_text(f'合并共{len(d)}页；顺序与分文件页数一致；姓名文本可提取；原始3页图纸字节一致；全部页面已渲染。\n',encoding='utf-8')
archive=output/'基础模块02_人机接口_V1.1_源码与分文件PDF.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for f in (root/'HARDWARE/HMI').glob('*'): z.write(f,'HARDWARE/HMI/'+f.name)
    for f in sequence: z.write(f,'分文件PDF/'+f.name)
    for f in [root/'HMI.uvprojx',root/'HMI_build.log',root/'tests/test_hmi.c',
              root/'tests/test_i2c_port.c',root/'tests/mock/gd32f10x.h',
              root/'document/基础模块02_人机接口_任务分工与交付说明.md',
              output/'合并顺序与校验.json']:
        z.write(f,str(f.relative_to(root)))
print(json.dumps({'merged':str(merged),'pages':len(d),'parts':manifest,'archive':str(archive)},ensure_ascii=False))
