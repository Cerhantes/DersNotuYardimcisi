import pymupdf as fitz, sys
from PIL import Image
src, pre = sys.argv[1], sys.argv[2]
d = fitz.open(src); n = d.page_count
per = 8
for k in range(0, n, per):
    ims = []
    for i in range(k, min(n, k + per)):
        pm = d[i].get_pixmap(dpi=45); ims.append(Image.frombytes('RGB', (pm.width, pm.height), pm.samples))
    w, h = ims[0].size
    s = Image.new('RGB', (w * 4 + 30, h * 2 + 10), 'gray')
    for j, im in enumerate(ims): s.paste(im, ((j % 4) * (w + 10), (j // 4) * (h + 10)))
    s.save(f'{pre}_{k//per}.png')
print(n)
