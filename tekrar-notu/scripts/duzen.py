"""Derlenmiş tekrar notunda satır kırılması hatalarını tarar + sayfa temas görüntüleri üretir.

py -W ignore duzen.py <out.pdf> <work>

Konsola, son satırı tek kelime / çok kısa olan metin blokları yazılır (sayfa | önceki satır sonu | son satır).
Gerçek hata türleri:  '↑.' gibi yalnız ok, kelime ortasından bölünmüş tablo hücresi ('83–86 HR' | 'A',
'4000–500' | '0'), ham alt çizgi ('F_c'). Yanlış alarm: denklem numarası '(8.1)', tablo hücrelerinin
yan yana birleşik okunması ('83–8682–84...'), iki kelimelik normal paragraf sonu.
Sonra <work>/rv_<k>.png (8 sayfa/görüntü) — HEPSİNİ aç.
"""
import sys, os, re
import pymupdf
from PIL import Image

src, work = sys.argv[1], sys.argv[2]
doc = pymupdf.open(src)
print('Sayfa sayısı:', doc.page_count)
eqno = re.compile(r'^\([\d\.,–\-a-z ]+\)$')   # (6.9a), (8.13–8.14), (7.7a–b)
n = 0
for i, p in enumerate(doc):
    txt = p.get_text()
    for bad in ('&amp;', '&lt;', '&gt;', '&nbsp;', '<sub>', '<super>', '<b>'):
        if bad in txt: print('%d  HAM İŞARETLEME: %s' % (i + 1, bad)); n += 1
    for m in re.finditer(r'\b[A-Za-zα-ω]_[A-Za-z0-9{]', txt):
        print('%d  HAM ALT ÇİZGİ: %r' % (i + 1, txt[max(0, m.start() - 15):m.end() + 10])); n += 1
    for b in p.get_text('dict')['blocks']:
        if b['type']: continue
        rows = []
        for l in b['lines']:
            t = ''.join(s['text'] for s in l['spans']).strip()
            y = round(l['bbox'][3])
            if rows and abs(rows[-1][0] - y) < 5: rows[-1][1] += t; continue
            rows.append([y, t])
        if len(rows) < 2: continue
        last = rows[-1][1]
        if eqno.match(last): continue
        if len(last.split()) >= 2 and len(last) > 6: continue                 # normal paragraf sonu
        if not re.search(r'[A-Za-zÇĞİÖŞÜçğıöşüα-ω]', last) and len(last) > 6: continue   # birleşik okunan tablo satırı
        if True:
            print('%d  %r | %r' % (i + 1, rows[-2][1][-40:], last)); n += 1
print('Şüpheli satır:', n)

# temas sayfaları
pw = 380
for k in range(0, doc.page_count, 8):
    pages = []
    for j in range(k, min(k + 8, doc.page_count)):
        pix = doc[j].get_pixmap(dpi=55)
        im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples); im.thumbnail((pw, 540)); pages.append(im)
    S = Image.new('RGB', (4 * pw, 2 * 540), (128, 128, 128))
    for j, im in enumerate(pages): S.paste(im, ((j % 4) * pw, (j // 4) * 540))
    out = os.path.join(work, 'rv_%d.png' % (k // 8)); S.save(out); print('KONTROL:', out)
