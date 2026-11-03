"""Derlenen formül kağıdını (ya da kaynaktaki bir sayfayı) gözden geçirmek için PNG üretir.

Kullanım: py -W ignore review.py <pdf> <work> [dpi] [--pages 3,5]
  <work>/rv<n>.png   her sayfa (varsayılan 100 dpi; Read ile tek tek aç)
  <work>/rv_ov.png   tüm sayfaların küçük önizlemesi (sayfa dengesi / boşluk kontrolü)
--pages: yalnızca bu sayfalar (1 tabanlı); kaynak PDF'te karmaşık bir denklemi görmek için de kullanılır.
"""
import os, sys
import pymupdf as fitz
from PIL import Image

args = sys.argv[1:]
pages = None
if '--pages' in args:
    k = args.index('--pages'); pages = [int(x) for x in args[k + 1].split(',')]; del args[k:k + 2]
src, work = args[0], args[1]
dpi = int(args[2]) if len(args) > 2 else 100
d = fitz.open(src)
idx = [p - 1 for p in pages] if pages else range(d.page_count)
for i in idx:
    out = os.path.join(work, 'rv%d.png' % (i + 1))
    d[i].get_pixmap(dpi=dpi).save(out); print(out)
if not pages:
    ims = []
    for i in range(d.page_count):
        pm = d[i].get_pixmap(dpi=40); ims.append(Image.frombytes('RGB', (pm.width, pm.height), pm.samples))
    w, h = ims[0].size; cols = min(4, len(ims)); rows = (len(ims) + cols - 1) // cols
    s = Image.new('RGB', (cols * (w + 8), rows * (h + 8)), 'gray')
    for j, im in enumerate(ims): s.paste(im, ((j % cols) * (w + 8), (j // cols) * (h + 8)))
    s.save(os.path.join(work, 'rv_ov.png')); print(os.path.join(work, 'rv_ov.png'), 'sayfa:', d.page_count)
