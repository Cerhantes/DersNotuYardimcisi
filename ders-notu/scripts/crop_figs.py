# det.json'daki kümelerden şekilleri 220 dpi PNG olarak keser, figs.json yazar ve kontrol için
# temas sayfaları (contact sheet) üretir.
# Kullanım: python -W ignore crop_figs.py <kitap.pdf> <work> [--cap-above]
#   --cap-above: kitapta şekil başlığı şeklin ÜSTÜNDE (varsayılan: altında ya da yanında)
# Kümeler otomatik seçilir (pick()): her küme en yakın başlığa atanır; başlıktan şekle doğru olmayan
# taraftaki kümeler cezalandırılır. Seçim en yakın kümeden başlar, ona bitişik (≤25 pt) ya da aynı
# satırda/sütunda duran alt şekiller (a), (b), ... eklenir; uzaktakiler (denklem, kutu) atılır.
# Elle düzeltme dosyaları (isteğe bağlı, <work> içinde):
#   split.json : otomatik seçim yanlışsa hangi küme hangi şekle ait
#                {"224": {"5.6": [0], "5.7": [1, 2]}}       (anahtar = sayfa idx, değer = küme sıraları)
#   over.json  : kesimi tamamen elle ver (en son uygulanır)
#                {"8.1": [471, [30, 50, 325, 278]]}           (sayfa idx, [x0, y0, x1, y1] pt)
#   skip.json  : yok sayılacak sayfa idx listesi, ör. [471]  (o sayfadaki şekiller over.json ile verilir)
import pymupdf as fitz, json, sys, os, re, argparse
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('work'); ap.add_argument('--cap-above', action='store_true')
A = ap.parse_args()
src, W = A.src, A.work
d = fitz.open(src)
det = json.load(open(os.path.join(W, 'det.json'), encoding='utf-8'))
ld = lambda n, df: json.load(open(os.path.join(W, n), encoding='utf-8')) if os.path.exists(os.path.join(W, n)) else df
split, over, skip = ld('split.json', {}), ld('over.json', {}), set(map(str, ld('skip.json', [])))


def union(rs):
    a = fitz.Rect(rs[0])
    for x in rs[1:]: a |= fitz.Rect(x)
    return a


def gap(a, b):
    a, b = fitz.Rect(a), fitz.Rect(b)
    return max(0, a.x0 - b.x1, b.x0 - a.x1) + max(0, a.y0 - b.y1, b.y0 - a.y1)


def near(a, b, join=25, row=60):
    """Aynı şeklin parçası mı: bitişik ya da aynı satırda/sütunda kısa aralıkla duruyor."""
    a, b = fitz.Rect(a), fitz.Rect(b)
    if gap(a, b) <= join:
        return True
    vo = min(a.y1, b.y1) - max(a.y0, b.y0)
    ho = min(a.x1, b.x1) - max(a.x0, b.x0)
    if vo >= 0.5 * min(a.height, b.height) and max(a.x0 - b.x1, b.x0 - a.x1) <= row:
        return True
    return ho >= 0.5 * min(a.width, b.width) and max(a.y0 - b.y1, b.y0 - a.y1) <= join * 1.6


def pick(caps, cl):
    """Her kümeyi en yakın başlığa ata; her başlık için en yakın kümeden başlayıp near() olanları
    ekle (alt şekiller a, b, ...). Uzaktaki kümeler (denklem, kutu, tablo) atılır."""
    def dist(c, j):
        cr, r = fitz.Rect(caps[c][1]), fitz.Rect(cl[j])
        wrong = r.y1 < cr.y0 if A.cap_above else r.y0 > cr.y1   # şekil başlığın yanlış tarafında
        return gap(cr, r) + (200 if wrong else 0)
    own = {j: min(range(len(caps)), key=lambda c: dist(c, j)) for j in range(len(cl))}
    out = []
    for c in range(len(caps)):
        mine = [j for j in own if own[j] == c]
        if not mine:
            out.append([]); continue
        sel = [min(mine, key=lambda j: dist(c, j))]
        grow = True
        while grow:
            grow = False
            for j in mine:
                if j not in sel and any(near(cl[x], cl[j]) for x in sel):
                    sel.append(j); grow = True
        out.append(sorted(sel))
    return out


def fignum(cap):
    m = re.search(r'(\d+[.\-]\d+[a-z]?)', cap)   # 6.18a / 6.18b ayrı şekiller
    return m.group(1).replace('-', '.') if m else cap


figs, warn = {}, []
for k, v in det.items():
    cl = v['clusters']
    if k in skip or not cl:
        continue
    if k in split:
        for f, idx in split[k].items():
            figs[f] = (int(k), union([cl[i] for i in idx]))
    else:
        sel = pick(v['caps'], cl)
        for cap, idx in zip(v['caps'], sel):
            if idx:
                figs[fignum(cap[0])] = (int(k), union([cl[i] for i in idx]))
            else:
                warn.append(f'idx {k}: {fignum(cap[0])} için küme yok -> over.json ile ver')
        if len(v['caps']) > 1 or sum(map(len, sel)) < len(cl):
            warn.append(f'idx {k}: {len(v["caps"])} başlık, {len(cl)} küme, seçilen {sel} -> temas sayfasında kontrol et')
for f, (pg, rc) in over.items():
    figs[f] = (pg, fitz.Rect(rc))

os.makedirs(os.path.join(W, 'fig'), exist_ok=True)
json.dump({f: [pg, list(rc)] for f, (pg, rc) in figs.items()}, open(os.path.join(W, 'figs.json'), 'w'))
for f, (pg, rc) in figs.items():
    rc = fitz.Rect(rc.x0 - 5, rc.y0 - 5, rc.x1 + 5, rc.y1 + 5) & d[pg].rect
    d[pg].get_pixmap(dpi=220, clip=rc).save(os.path.join(W, 'fig', f + '.png'))

# temas sayfaları: her şeklin kesimini numarasıyla göster (gözle kontrol için)
def key(s):
    return [(int(x), '') if x.isdigit() else (0, x) for x in re.findall(r'\d+|[a-z]+', s)]
names = sorted(figs, key=key)
for part in range(0, len(names), 12):
    sheet = Image.new('RGB', (1500, 2000), 'white'); dr = ImageDraw.Draw(sheet)
    for j, n in enumerate(names[part:part + 12]):
        im = Image.open(os.path.join(W, 'fig', n + '.png')); im.thumbnail((480, 470))
        x, y = (j % 3) * 500, (j // 3) * 500
        sheet.paste(im, (x + 5, y + 25)); dr.text((x + 5, y + 5), f'{n}  (idx {figs[n][0]})', fill='red')
        dr.rectangle([x + 4, y + 24, x + 6 + im.width, y + 26 + im.height], outline='blue')
    sheet.save(os.path.join(W, f'sheet_{part // 12}.png'))
print(len(figs), 'şekil;', (len(names) + 11) // 12, 'temas sayfası ->', W)
for w in warn: print('UYARI', w)
