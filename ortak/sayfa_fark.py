"""Yalnız daha önce görülmemiş sayfaların görselini üretir; taşma ve bölünmüş hücreleri yazıyla raporlar.

Kullanım: python -W ignore sayfa_fark.py <pdf> <work> [dpi] [--hepsi]
  <work>/rv<n>.png   yalnız yeni ya da değişmiş sayfalar (varsayılan 100 dpi)
  <work>/rv_ov.png   tüm sayfaların küçük önizlemesi (sayfa dengesi için)
--hepsi: geçmişi yok say, bütün sayfaları üret.

Sayfa numarası bandı karşılaştırmaya girmez: yalnız yeri değişen sayfa yeniden açılmaz.
Geçmiş <work>/.sayfa_fark.json içinde tutulur; bir sayfanın hash'i önceki derlemelerde
görüldüyse o sayfa "görülmüş" sayılır.
"""
import hashlib, json, os, re, statistics, sys
import pymupdf as fitz
from PIL import Image

ALT_BANT = 0.06   # sayfa numarasının bulunduğu alt şerit


def imza(p):
    r = p.rect
    pm = p.get_pixmap(dpi=72, clip=fitz.Rect(0, 0, r.width, r.height * (1 - ALT_BANT)), alpha=False)
    return hashlib.sha1(pm.samples).hexdigest()


def sag_kenar(p):
    # görünen son karakter esas alınır: satır sonundaki boşluk karakteri taşma sayılmaz
    x = [c['bbox'][2] for b in p.get_text('rawdict')['blocks'] for l in b.get('lines', [])
         for s in l['spans'] for c in s['chars'] if not c['c'].isspace()]
    x += [fitz.Rect(i['bbox']).x1 for i in p.get_image_info()]
    return max(x, default=0)


def bolunmus(p):
    """Tablo hücresinde kelime ya da sayı ortasından bölünme: '0,26' / '9', 'İsten' / 'en'."""
    out = []
    for b in p.get_text('dict')['blocks']:
        satir = []
        for l in b.get('lines', []):
            t = ''.join(s['text'] for s in l['spans']).strip()
            if t:
                satir.append((t, max(s['size'] for s in l['spans']), l['bbox']))
        for (a, sa, ra), (c, sc, rc) in zip(satir, satir[1:]):
            dar = ra[2] - ra[0] < 75 and abs(ra[0] - rc[0]) < 2 and sc >= sa - 0.2
            if dar and len(c) <= 3 and re.search(r'\w$', a) and re.fullmatch(r'[\wçğıöşüÇĞİÖŞÜ]+[.,;:)]?', c) and ' ' not in a:
                if a[-1].isdigit() == c[0].isdigit():   # '1' / 'x' gibi iki ayrı öğeyi eleme
                    out.append('%s|%s' % (a, c))
    return out


def main():
    args = sys.argv[1:]
    hepsi = '--hepsi' in args
    args = [a for a in args if a != '--hepsi']
    src, work = args[0], args[1]
    dpi = int(args[2]) if len(args) > 2 else 100
    os.makedirs(work, exist_ok=True)
    d = fitz.open(src)
    kayit = os.path.join(work, '.sayfa_fark.json')
    gecmis = {}
    if os.path.exists(kayit) and not hepsi:
        with open(kayit, encoding='utf-8') as f:
            gecmis = json.load(f)
    gorulen = set(gecmis.get('gorulen', []))
    eski_sayfa = gecmis.get('sayfa')

    yeni, imzalar = [], []
    for i, p in enumerate(d):
        h = imza(p)
        imzalar.append(h)
        hedef = os.path.join(work, 'rv%d.png' % (i + 1))
        if h in gorulen:
            if os.path.exists(hedef):   # eski derlemeden kalan görsel yanlışlıkla açılmasın
                os.remove(hedef)
        else:
            p.get_pixmap(dpi=dpi, alpha=False).save(hedef)
            yeni.append(i + 1)
    for n in range(len(d) + 1, (eski_sayfa or 0) + 1):
        hedef = os.path.join(work, 'rv%d.png' % n)
        if os.path.exists(hedef):
            os.remove(hedef)

    ims = []
    for p in d:
        pm = p.get_pixmap(dpi=40, alpha=False)
        ims.append(Image.frombytes('RGB', (pm.width, pm.height), pm.samples))
    w, h = ims[0].size
    cols = min(6, len(ims))
    rows = (len(ims) + cols - 1) // cols
    ov = Image.new('RGB', (cols * (w + 6), rows * (h + 6)), 'gray')
    for j, im in enumerate(ims):
        ov.paste(im, ((j % cols) * (w + 6), (j // cols) * (h + 6)))
    ov.save(os.path.join(work, 'rv_ov.png'))

    with open(kayit, 'w', encoding='utf-8') as f:
        json.dump({'gorulen': sorted(gorulen | set(imzalar)), 'sayfa': len(d)}, f)

    print('Sayfa: %d%s' % (len(d), '' if eski_sayfa in (None, len(d)) else ' (önceki derleme %d)' % eski_sayfa))
    print('AÇILACAK: %s' % (' '.join('rv%d.png' % n for n in yeni) or 'yok, görülmemiş sayfa kalmadı'))
    print('Görülmüş, açma: %d sayfa' % (len(d) - len(yeni)))

    kenar = [sag_kenar(p) for p in d]
    orta = statistics.median(kenar)
    tasan = ['s.%d (%.1f pt)' % (i + 1, x - orta) for i, x in enumerate(kenar) if x > orta + 1.5]
    if tasan:
        print('TAŞMA: sağ kenar diğer sayfaları aşıyor: ' + ', '.join(tasan))
    bol = ['s.%d %s' % (i + 1, x) for i, p in enumerate(d) for x in bolunmus(p)]
    if bol:
        print('BÖLÜNMÜŞ HÜCRE? ' + ', '.join(bol[:30]) + (' ... (%d)' % len(bol) if len(bol) > 30 else ''))
    print('Yakalanamayan: tablonun sütun çizgisini aşması, üst üste binen yazı. Bunlar için açılan sayfalara bak; '
          'düzen akışı değiştiyse rv_ov.png ile sayfa dengesine de bak.')


if __name__ == '__main__':
    main()
