# Sayfalardaki şekil bölgelerini (vektör çizim + gömülü resim + şekil etiketleri) kümeler ve
# şekil başlıklarını ("FIGURE 5.3 ..." gibi) bulur. Çıktı: <work>/det.json
# Kullanım: python -W ignore detect_figs.py <kitap.pdf> <work> <ilk> <son> [--cap REGEX] [--label-font REGEX]
#   <ilk>/<son>: PDF sayfa numaraları (1'den başlar).
#   --cap: başlık satırını tanıyan regex (varsayılan FIGURE/Figure/Fig./Şekil + numara)
#   --cap-font: başlığın ilk parçasının yazı tipi (metin içi 'Fig. 5.7' atıflarını elemek için kalın olmalı)
#   --label-font: şekil içi etiketlerin yazı tipi regex'i. Varsayılan 'auto': yazı tipine bakmadan, çizime/resme
#                 yakın kısa satırlar (≤ --label-len karakter) etiket sayılır. Etiketler kitapta ayrı bir yazı
#                 tipindeyse (ör. Helvetica) regex vermek daha temiz sonuç verir; book_info.py öneri basar.
# İçinde uzun gövde metni olan büyük çizimler (renkli örnek/denklem kutusu zemini) şekil sayılmaz.
import pymupdf as fitz, sys, json, re, argparse, os

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('work'); ap.add_argument('a', type=int); ap.add_argument('b', type=int)
ap.add_argument('--cap', default=r'^\s*(FIGURE|Figure|Fig\.|ŞEKİL|Şekil)\s*\d+[.\-]\d+')
ap.add_argument('--cap-font', default=r'Bold|Black|Heavy|Demi|Semi|Bd')
ap.add_argument('--label-font', default='auto')
ap.add_argument('--label-len', type=int, default=40, help="auto modunda etiket sayılacak en uzun satır")
ap.add_argument('--pad', type=float, default=12, help='kümeleme mesafesi (pt)')
A = ap.parse_args()
os.makedirs(A.work, exist_ok=True)
cap_re, capf_re = re.compile(A.cap), re.compile(A.cap_font)
lab_re = None if A.label_font == 'auto' else re.compile(A.label_font)

d = fitz.open(A.src)
res = {}
for i in range(A.a - 1, A.b):
    p = d[i]
    pr = p.rect
    top, bot = pr.height * 0.06, pr.height - pr.height * 0.035   # üst bilgi / sayfa no şeridini dışla
    lines = []   # (metin, kutu, parçalar, blok no)
    for b, blk in enumerate(p.get_text('dict')['blocks']):
        for ln in blk.get('lines', []):
            lines.append((''.join(s['text'] for s in ln['spans']).strip(), fitz.Rect(ln['bbox']), ln['spans'], b))
    longs = [(t, r) for t, r, _, _ in lines if len(t) > 45]
    # başlığın tam alanı (crop_figs bunu kesimden siler): başlık satırı + aynı satırdaki metni + altındaki devam
    # satırları. Kitap şekil etiketlerini (eksen rakamı, (a), (b)) başlıkla aynı bloğa koyabilir; onlar konuma göre ayrılır.
    capboxes = []
    for t, r, sp, b in lines:
        if cap_re.match(t) and capf_re.search(sp[0]['font']):
            box = fitz.Rect(r)
            for _, r2, _, b2 in sorted((x for x in lines if x[3] == b), key=lambda x: (x[1].y0, x[1].x0)):
                ayni_satir = abs(r2.y0 - box.y0) < 3 and r2.x0 >= box.x0 and r2.x0 - box.x1 < 15
                ortak = min(r2.x1, box.x1) - max(r2.x0, box.x0)
                alt_satir = r2.y0 > box.y0 and r2.y0 - box.y1 < 6 and ortak >= 0.5 * r2.width
                if ayni_satir or alt_satir:
                    box |= r2
            capboxes.append(box)
    els = []
    for dr in p.get_drawings():
        r = fitz.Rect(dr['rect'])
        if not (r.x0 >= 0 and r.y0 >= top and r.x1 <= pr.width and r.y1 <= bot):
            continue
        if r.width * r.height > 20000 and sum(len(t) for t, lr in longs if r.contains(lr)) > 200:
            continue   # gövde metni taşıyan zemin kutusu
        if dr.get('color') is None and dr.get('fill') and min(dr['fill']) > 0.99:
            continue   # görünmez beyaz zemin (kitaplar başlığın altına koyar; şekli başlığa bağlıyordu)
        if any(c.contains(r) for c in capboxes):
            continue   # başlığın kendi süsü (ince çizgi vb.)
        els.append(r)
    for im in p.get_image_info():
        els.append(fitz.Rect(im['bbox']))
    caps, shorts = [], []
    for t, r, spans, b in lines:
        if cap_re.match(t) and capf_re.search(spans[0]['font']):
            caps.append((t, list(r)))
        elif any(c.contains(r) for c in capboxes):
            continue   # başlığın devam satırları etiket değildir
        elif lab_re:
            els += [fitz.Rect(s['bbox']) for s in spans if lab_re.search(s['font'])]
        elif t and len(t) <= A.label_len:
            shorts.append(r)
    # auto: çizime değen ya da çok yakın kısa satırları, yeni eklenenlerden de yayılarak etikete kat
    pending, near = shorts, 6
    while pending and els:
        hit = [r for r in pending if any(fitz.Rect(e.x0 - near, e.y0 - near, e.x1 + near, e.y1 + near).intersects(r) for e in els)]
        if not hit: break
        els += hit; pending = [r for r in pending if r not in hit]
    if not caps:
        continue
    els = [e for e in els if not e.is_infinite]
    # birbirine A.pad'den yakın öğeleri birleştir
    clusters = []
    for e in els:
        grown = fitz.Rect(e.x0 - A.pad, e.y0 - A.pad, e.x1 + A.pad, e.y1 + A.pad)
        nr = fitz.Rect(e)
        for c in [c for c in clusters if c.intersects(grown)]:
            nr |= c; clusters.remove(c)
        clusters.append(nr)
    changed = True
    while changed:
        changed = False
        for x in clusters:
            gx = fitz.Rect(x.x0 - A.pad, x.y0 - A.pad, x.x1 + A.pad, x.y1 + A.pad)
            for y in clusters:
                if x is not y and gx.intersects(y):
                    clusters.remove(x); clusters.remove(y); clusters.append(x | y); changed = True; break
            if changed: break
    clusters = [c for c in clusters if c.width * c.height > 3000]
    # çizimden uzak ama şekil alanına değen kısa etiketler ((a), (b), eksen harfi) yarım kesilmesin
    for n, c in enumerate(clusters):
        for r in [r for r in pending if fitz.Rect(c.x0 - 3, c.y0 - 3, c.x1 + 3, c.y1 + 3).intersects(r)]:
            clusters[n] = clusters[n] | r
            pending.remove(r)
    clusters.sort(key=lambda c: (round(c.y0), c.x0))
    res[i] = {'caps': caps, 'clusters': [list(c) for c in clusters], 'capboxes': [list(c) for c in capboxes]}

json.dump(res, open(os.path.join(A.work, 'det.json'), 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
for k, v in res.items():
    print(f'idx {k}', [c[0][:14] for c in v['caps']], [[round(x) for x in c] for c in v['clusters']])
