"""Numarasız slayt belgelerinde şekiller: her slaytın resim parçalarını tek tek keser, beyaz zeminde yeniden birleştirir.

Slaytlarda bir "şekil" çoğu zaman gri slayt zemini üstüne ayrı ayrı yerleştirilmiş birkaç resimden oluşur. Hepsini kapsayan
tek bir dikdörtgen kesilirse parçaların arasındaki gri zemin ve slayt yazıları da kesime girer. Bu betik her parçayı yalnız
kendi sınırından (paysız) keser ve parçaları slayttaki konumlarında beyaz bir tuvale yapıştırır.

Kullanım:
    python -W ignore slayt_sekil.py <kaynak.pdf> <work> <ilk-son> [<ilk-son> ...]
        Aday kipi: her slayt için parça listesi <work>/parcalar.json'a yazılır, hepsi birleştirilir.
    python -W ignore slayt_sekil.py <kaynak.pdf> <work> --parcalar
        <work>/parcalar.json'daki (düzenlenmiş) listeden yeniden birleştirir.

parcalar.json: {"17b": [16, [[x0, y0, x1, y1], ...]], ...}
    anahtar = PDF sayfa no + slayt harfi (a: sayfanın ilk slaytı, b: ikinci ...), değer = [sayfa idx, parça kutuları (pt)].
    Gözden geçirirken: istenmeyen slaytı sil, slayttaki istenmeyen parçayı listeden çıkar, resim olmayan (vektör)
    bir çizim için kutusunu elle ekle; sonra --parcalar ile yeniden çalıştır.
Çıktı: <work>/fig/<no>.png (çok parçalıysa parçalar ayrıca <work>/fig/<no>/), <work>/figs.json (notlib'in beklediği biçim: {no: [sayfa idx, birleşik kutu]}),
       <work>/sheet_*.png temas sayfaları (her şeklin adı ve parça sayısıyla).
Slayt zemini: sayfanın en az %12'sini kaplayan, beyaz olmayan dolgulu dikdörtgen. Hiç yoksa sayfanın tamamı tek slayt sayılır.
Süs: aralıktaki sayfaların en az %30'unda tekrar eden resim (altıgen süsler, logo) ya da 500 pt²'den küçük resim.
"""
import argparse, collections, json, os, re, shutil, sys
import pymupdf as fitz
from PIL import Image, ImageChops, ImageDraw

DPI = 220
KENAR = 4          # birleşik şeklin çevresinde bırakılan beyaz pay (pt)
MIN_ALAN = 500     # bundan küçük resim parça sayılmaz (pt²); formül kutuları ~60×16 pt
SUS_ORAN = 0.3     # sayfaların bu oranında tekrar eden resim süstür


def sayfalar(araliklar):
    return [i for a, b in araliklar for i in range(a, b + 1)]


def slaytlar(p):
    """Sayfadaki slayt zeminleri, yukarıdan aşağı, soldan sağa."""
    alan = p.rect.width * p.rect.height
    out = []
    for dr in p.get_drawings():
        r, dolgu = fitz.Rect(dr['rect']), dr.get('fill')
        if dolgu and min(dolgu) < 0.97 and r.width * r.height >= 0.12 * alan and r.width * r.height < 0.95 * alan:
            if not any(abs(r.x0 - o.x0) < 2 and abs(r.y0 - o.y0) < 2 for o in out):
                out.append(r)
    return sorted(out, key=lambda r: (round(r.y0), r.x0)) or [fitz.Rect(p.rect)]


def adaylar(d, nolar):
    """{şekil no: [sayfa idx, [parça kutuları]]}"""
    say = collections.Counter()
    for no in nolar:
        say.update({im['xref'] for im in d[no - 1].get_image_info(xrefs=True)})
    sus = {x for x, c in say.items() if len(nolar) >= 3 and c >= SUS_ORAN * len(nolar)}
    out = {}
    for no in nolar:
        p = d[no - 1]
        resimler = [(fitz.Rect(im['bbox']), im['xref']) for im in p.get_image_info(xrefs=True)]
        resimler = [(r & p.rect, x) for r, x in resimler if x not in sus and r.width * r.height >= MIN_ALAN and not r.is_infinite]
        for k, sl in enumerate(slaytlar(p)):
            parca = [r for r, _ in resimler if sl.contains(fitz.Point((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2))]
            parca = [r for r in parca if not (r.width >= 0.9 * sl.width and r.height >= 0.9 * sl.height)]   # resim olarak gömülü zemin
            if parca:
                parca.sort(key=lambda r: (round(r.y0), r.x0))
                out['%d%s' % (no, 'abcdefgh'[k])] = [no - 1, [[round(v, 1) for v in r] for r in parca]]
    return out


def kaynastir(parcalar, oran=0.10):
    """Birbirine binen parçaları tek parçada birleştirir (kesişim, küçük parçanın alanının oran'ından büyükse).
    Binen parçalar ayrı ayrı yeniden dizilirse kesişimdeki çizim iki kez görünür ve şeklin bütünlüğü bozulur."""
    out = [fitz.Rect(r) for r in parcalar]
    degisti = True
    while degisti:
        degisti = False
        for i in range(len(out)):
            for j in range(i + 1, len(out)):
                k = out[i] & out[j]
                kucuk = min(out[i].width * out[i].height, out[j].width * out[j].height)
                if not k.is_empty and k.width * k.height > oran * kucuk:
                    out[i] |= out.pop(j)
                    degisti = True
                    break
            if degisti:
                break
    return sorted(out, key=lambda r: (round(r.y0), r.x0))


def satirla(parcalar, oran=0.3):
    """Slaytta aynı satırdaki parçaları (dikeyde küçüğün boyunun oran'ından fazla örtüşenler) gruplar; okuma sırasıyla.
    Yeniden dizmenin birimi satırdır: bir satırdaki kötü/iyi çifti gibi yan yana örnekler birbirinden ayrılmaz."""
    gruplar = []
    for r in sorted(parcalar, key=lambda r: r.y0):
        g = gruplar[-1] if gruplar else None
        if g is not None:
            y0, y1 = min(x.y0 for x in g), max(x.y1 for x in g)
            if min(y1, r.y1) - max(y0, r.y0) > oran * min(r.height, y1 - y0):
                g.append(r)
                continue
        gruplar.append([r])
    return [sorted(g, key=lambda r: r.x0) for g in gruplar]


def tuvale(p, parcalar, s):
    """Parçaları beyaz tuvalde slayttaki yerlerine yapıştırır. Döner: (tuval, birleşik kutu)."""
    u = fitz.Rect(parcalar[0])
    for r in parcalar[1:]:
        u |= r
    tuval = Image.new('RGB', (max(1, round(u.width * s)), max(1, round(u.height * s))), 'white')
    for r in parcalar:
        pm = p.get_pixmap(dpi=DPI, clip=r, alpha=False)
        tuval.paste(Image.frombytes('RGB', (pm.width, pm.height), pm.samples), (round((r.x0 - u.x0) * s), round((r.y0 - u.y0) * s)))
    return tuval, u


def birlestir(d, pg, kutular, yol):
    """Parçaları beyaz tuvalde slayttaki yerlerine yapıştırır, boş kenarı kırpar. Döner: birleşik kutu (pt)."""
    p = d[pg]
    parcalar = [fitz.Rect(k) & p.rect for k in kutular]
    s = DPI / 72
    tuval, u = tuvale(p, parcalar, s)
    kut = ImageChops.difference(tuval, Image.new('RGB', tuval.size, 'white')).convert('L').point(lambda v: 255 if v > 12 else 0).getbbox()
    if kut:
        m = round(KENAR * s)
        dolu = Image.new('RGB', (kut[2] - kut[0] + 2 * m, kut[3] - kut[1] + 2 * m), 'white')
        dolu.paste(tuval.crop(kut), (m, m))
        tuval = dolu
        u = fitz.Rect(u.x0 + kut[0] / s - KENAR, u.y0 + kut[1] / s - KENAR, u.x0 + kut[2] / s + KENAR, u.y0 + kut[3] / s + KENAR)
    tuval.save(yol)
    # Satırları ayrı ayrı da kaydet: notlib şekli bunlarla yeniden dizebilir (bkz. notlib Doc.fig › paket)
    klasor = os.path.splitext(yol)[0]
    shutil.rmtree(klasor, ignore_errors=True)
    satirlar = satirla(kaynastir(parcalar))
    if len(satirlar) > 1:
        os.makedirs(klasor)
        olcu = []
        for k, g in enumerate(satirlar):
            st, gu = tuvale(p, g, s)
            st.save(os.path.join(klasor, '%d.png' % k))
            olcu.append([round(gu.width, 1), round(gu.height, 1)])
        json.dump(olcu, open(os.path.join(klasor, 'parcalar.json'), 'w'))
    return u


def sira(n):
    return [(int(x), '') if x.isdigit() else (0, x) for x in re.findall(r'\d+|[a-z]+', n)]


def temas(work, figs, parcalar):
    adlar = sorted(figs, key=sira)
    for k in range(0, len(adlar), 12):
        sh = Image.new('RGB', (1500, 2000), 'white')
        dr = ImageDraw.Draw(sh)
        for j, n in enumerate(adlar[k:k + 12]):
            im = Image.open(os.path.join(work, 'fig', n + '.png'))
            im.thumbnail((480, 470))
            x, y = (j % 3) * 500, (j // 3) * 500
            sh.paste(im, (x + 5, y + 25))
            dr.text((x + 5, y + 5), '%s  (sayfa %d, %d parça)' % (n, figs[n][0] + 1, len(parcalar[n][1])), fill='red')
            dr.rectangle([x + 4, y + 24, x + 6 + im.width, y + 26 + im.height], outline='blue')
        sh.save(os.path.join(work, 'sheet_%d.png' % (k // 12)))
    return (len(adlar) + 11) // 12


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('kaynak'); ap.add_argument('work')
    ap.add_argument('araliklar', nargs='*')
    ap.add_argument('--parcalar', action='store_true', help='<work>/parcalar.json\'dan yeniden birleştir')
    a = ap.parse_args(argv)
    d = fitz.open(a.kaynak)
    yol = os.path.join(a.work, 'parcalar.json')
    if a.parcalar:
        parcalar = json.load(open(yol, encoding='utf-8'))
    else:
        araliklar = []
        for x in a.araliklar:
            m = re.fullmatch(r'(\d+)-(\d+)', x)
            if not m:
                sys.exit('Aralık biçimi ilk-son olmalı: %s' % x)
            araliklar.append((int(m.group(1)), int(m.group(2))))
        if not araliklar:
            sys.exit('Aralık ya da --parcalar verilmeli')
        parcalar = adaylar(d, sayfalar(araliklar))
        os.makedirs(a.work, exist_ok=True)
        json.dump(parcalar, open(yol, 'w', encoding='utf-8'), indent=1)
    fig = os.path.join(a.work, 'fig')
    os.makedirs(fig, exist_ok=True)
    for f in os.listdir(fig):   # eski kesimler (silinen adaylar) temas sayfasına karışmasın
        if f.endswith('.png'):
            os.remove(os.path.join(fig, f))
        elif os.path.isdir(os.path.join(fig, f)):
            shutil.rmtree(os.path.join(fig, f))
    figs = {}
    for no, (pg, kutular) in parcalar.items():
        u = birlestir(d, pg, kutular, os.path.join(fig, no + '.png'))
        figs[no] = [pg, [round(v, 1) for v in u]]
    json.dump(figs, open(os.path.join(a.work, 'figs.json'), 'w'))
    for f in os.listdir(a.work):
        if re.fullmatch(r'sheet_\d+\.png', f):
            os.remove(os.path.join(a.work, f))
    n = temas(a.work, figs, parcalar) if figs else 0
    print('%d şekil (%d parça) birleştirildi; %d temas sayfası -> %s' % (len(figs), sum(len(v[1]) for v in parcalar.values()), n, a.work))
    print('Parça listesi: %s — istenmeyen slaytı/parçayı sil, vektör çizim için kutu ekle, sonra --parcalar ile yeniden çalıştır.' % yol)
    return 0


if __name__ == '__main__':
    sys.exit(main())
