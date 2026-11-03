"""Kaynak PDF'ten metin + şekil çıkarır.

py -W ignore kaynak.py <kaynak.pdf> <work> [--cap REGEX]

Çıktılar:
  <work>/metin.txt        her sayfa '===== SAYFA n =====' ile; Read ile parça parça okunur
  <work>/fig/<no>.png     gömülü görseller, altındaki (yoksa üstündeki) 'Şekil X.Y' başlığına göre adlandırılır;
                          aynı başlığa ait birden çok görsel birleştirilir
  <work>/figs.json        {no: [sayfa, [x0,y0,x1,y1]]}  (notlib/tnlib bunu okur)
  <work>/figsheet<k>.png  temas sayfaları — HEPSİNİ aç ve kontrol et
Konsola: künye, sayfa sayısı, içindekiler (yer imleri), şekil listesi, başlıksız görseller.
"""
import sys, re, json, os, argparse
import pymupdf
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('work')
ap.add_argument('--cap', default=r'^\s*(?:Şekil|Sekil|Fig\.?|Figure)\s+(\d+[\.\-]\d+[a-z]?)')
ap.add_argument('--dpi', type=int, default=220)
a = ap.parse_args()
os.makedirs(os.path.join(a.work, 'fig'), exist_ok=True)
cap_re = re.compile(a.cap)

doc = pymupdf.open(a.src)
print('Dosya   :', a.src)
print('Sayfa   :', doc.page_count)
print('Başlık  :', doc.metadata.get('title'))
print('Yazar   :', doc.metadata.get('author'))
print('\nİÇİNDEKİLER (seviye, başlık, sayfa):')
for l in doc.get_toc():
    print('  ' * (l[0] - 1) + '- %s  [s.%d]' % (l[1], l[2]))

with open(os.path.join(a.work, 'metin.txt'), 'w', encoding='utf-8') as f:
    for i, p in enumerate(doc):
        f.write('\n===== SAYFA %d =====\n' % (i + 1) + p.get_text())

figs, orphan = {}, []
for i, p in enumerate(doc):
    caps = []
    for b in p.get_text('blocks'):
        m = cap_re.match(b[4])
        if m: caps.append((m.group(1).replace('-', '.'), pymupdf.Rect(b[:4])))
    groups = {}
    for im in p.get_image_info():
        r = pymupdf.Rect(im['bbox'])
        if r.width < 20 or r.height < 20: continue
        below = [(c[1].y0 - r.y1, c) for c in caps if c[1].y0 >= r.y1 - 5]
        above = [(r.y0 - c[1].y1, c) for c in caps if c[1].y1 <= r.y0 + 5]
        cand = sorted(below)[:1] or sorted(above)[:1]
        if not cand or cand[0][0] > 150:
            orphan.append((i + 1, tuple(round(x) for x in r))); continue
        num = cand[0][1][0]
        groups[num] = groups[num] | r if num in groups else r
    for num, r in groups.items():
        if num in figs: num = num + '_s%d' % (i + 1)
        figs[num] = [i + 1, [r.x0, r.y0, r.x1, r.y1]]
        p.get_pixmap(clip=r, dpi=a.dpi).save(os.path.join(a.work, 'fig', num + '.png'))

json.dump(figs, open(os.path.join(a.work, 'figs.json'), 'w'), indent=0)


def key(s):
    # '6.10a', '5.3_s12' gibi harfli/ekli numaralar: (sayı, ek) çiftleri → karışık tip karşılaştırması olmaz
    return [(int(m.group(1)) if m.group(1) else -1, m.group(2)) for m in re.finditer(r'(\d*)([^\d\._]*)', s) if m.group(0)]


names = sorted(figs, key=key)
print('\nŞEKİLLER (%d):' % len(names), ' '.join(names))
if orphan: print('Başlığı bulunamayan görseller (sayfa, kutu):', orphan[:20])
for k in range(0, len(names), 20):
    S = Image.new('RGB', (1500, 1040), 'white'); dr = ImageDraw.Draw(S)
    for j, n in enumerate(names[k:k + 20]):
        im = Image.open(os.path.join(a.work, 'fig', n + '.png')); im.thumbnail((290, 235))
        x, y = (j % 5) * 300, (j // 5) * 260
        S.paste(im, (x + 5, y + 20)); dr.text((x + 5, y + 3), n, fill='red')
    out = os.path.join(a.work, 'figsheet%d.png' % (k // 20)); S.save(out); print('KONTROL:', out)
