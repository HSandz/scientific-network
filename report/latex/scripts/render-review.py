"""Render every PDF page at 100 dpi and create numbered contact sheets."""
from pathlib import Path
import argparse, subprocess
from PIL import Image, ImageOps, ImageDraw
p=argparse.ArgumentParser(); p.add_argument('pdf'); p.add_argument('output'); a=p.parse_args()
out=Path(a.output).resolve()
if not out.is_relative_to(Path(__file__).resolve().parents[1]):
    raise SystemExit('Review renders must stay inside report/latex/')
out.mkdir(parents=True,exist_ok=True)
for old in [*out.glob('page-*.png'), *out.glob('contact-*.jpg')]:
    old.unlink()
subprocess.run(['pdftoppm','-r','100','-png',a.pdf,str(out/'page')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
pages=sorted(out.glob('page-*.png'))
for start in range(0,len(pages),9):
    sheet=Image.new('RGB',(1500,2190),'#cdd3db'); d=ImageDraw.Draw(sheet)
    for j,path in enumerate(pages[start:start+9]):
        im=Image.open(path).convert('RGB'); im.thumbnail((480,690))
        x=(j%3)*500+(500-im.width)//2; y=(j//3)*730+30
        sheet.paste(im,(x,y)); d.text(((j%3)*500+15,(j//3)*730+8),f'PDF page {start+j+1}',fill='black')
    sheet.save(out/f'contact-{start//9+1:02}.jpg',quality=92)
print(f'Rendered {len(pages)} pages; {(len(pages)+8)//9} contact sheets in {out}')
