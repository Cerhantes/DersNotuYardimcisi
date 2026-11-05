"""Kaynak PDF için kalıcı, skill'ler arasında ortak envanter. Her skill işe bununla başlar.

Kullanım:
  python -W ignore envanter.py <kaynak.pdf>                  içindekiler ve önceki betikler (metin çıkarmaz)
  python -W ignore envanter.py <kaynak.pdf> 368-449 478-529 --work <work>
                                                              aralıkları envantere ekle, yalnız bu işin metnini <work>/metin.txt'ye yaz
  python -W ignore envanter.py <kaynak.pdf> --serit <work> [--no 6.1,6.2] [--aralik 6.1 6.40]
                                                              kitaptaki numaralı denklemlerin kırpıntıları
  python -W ignore envanter.py <kaynak.pdf> --sekil-kaydet <work>   <work>/fig + figs.json envantere
  python -W ignore envanter.py <kaynak.pdf> --sekil-al <work>       envanterdeki şekiller <work>'e
  python -W ignore envanter.py <kaynak.pdf> --sekil-eksik 5.1,5.2   bu numaralardan kesilmemiş olanlar
  python -W ignore envanter.py <kaynak.pdf> --bul 8.30,8.21         bu denklem, tablo ve şekillerin PDF sayfaları
  (--sekil-kaydet ve --sekil-al figs.json'u numara bazında birleştirir; --sekil-kaydet <work> --yalniz 5.2 yalnız bu numarayı kaydeder)

Konum: <kaynağın klasörü>/.kaynak/envanter/<kaynak adı>/
  envanter.json  imza, sayfa aralıkları, bölümler, numaralı denklem/tablo/şekil dizini (sayfa numarasıyla)
  metin.txt      sayfa işaretli metin (===== PDF sayfa N); önceki işlerin aralıklarını da içerir
  fig/, figs.json  kesilmiş şekiller

Sayfalar PDF görüntüleyici numarasıdır (1 tabanlı). Yeni aralıklar eskilerle birleştirilir.
Kaynak dosya değiştiyse envanter yeniden kurulur.
"""
import hashlib, json, os, re, shutil, sys
import pymupdf as fitz

DENK = re.compile(r'\((\d{1,2}[.\-–]\d{1,3}[a-z]?)\)\s*$')
ATIF = re.compile(r'(?i)\b(eqs?\.?|equations?|denklem\w*|see)\s*$')
TABLO = re.compile(r'^(?:Table|TABLE|Tablo|TABLO|Çizelge)\s+(\d{1,2}[.\-]\d{1,3}[a-z]?)\b\s*[.:–-]?\s*(.*)')
SEKIL = re.compile(r'^(?:Fig\.?|Figure|FIGURE|Şekil|ŞEKİL)\s+(\d{1,2}[.\-]\d{1,3}[a-z]?)\b\s*[.:–-]?\s*(.*)')
ICERIK_ADI = re.compile(r'^(?!semalar|ornek|aks_|sekil)[^/\\]+\.py$')


def imza(yol):
    h = hashlib.sha256()
    with open(yol, 'rb') as f:
        for parca in iter(lambda: f.read(1 << 20), b''):
            h.update(parca)
    return h.hexdigest()


def klasor(kaynak):
    kok = os.path.splitext(os.path.basename(kaynak))[0]
    return os.path.join(os.path.dirname(os.path.abspath(kaynak)), '.kaynak', 'envanter', kok)


def birlestir(araliklar):
    out = []
    for a, b in sorted(araliklar):
        if out and a <= out[-1][1] + 1:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def sayfalar(araliklar):
    return [i for a, b in araliklar for i in range(a, b + 1)]


def tara(d, nolar):
    denk, tablo, sekil = {}, {}, {}
    for no in nolar:
        p = d[no - 1]
        sag = p.rect.width * 0.72
        for b in p.get_text('dict')['blocks']:
            for l in b.get('lines', []):
                t = ''.join(s['text'] for s in l['spans']).strip()
                if not t:
                    continue
                m = DENK.search(t)
                if m and l['bbox'][2] > sag and not ATIF.search(t[:m.start()]) and len(t) - len(m.group(0)) < 60:
                    denk.setdefault(m.group(1), {'sayfa': no, 'kutu': [round(v, 1) for v in l['bbox']]})
                m = TABLO.match(t)
                if m:
                    tablo.setdefault(m.group(1), {'sayfa': no, 'baslik': m.group(2)[:70]})
                m = SEKIL.match(t)
                if m:
                    sekil.setdefault(m.group(1), {'sayfa': no, 'baslik': m.group(2)[:70]})
    return denk, tablo, sekil


def sira(n):
    return [int(x) if x.isdigit() else x for x in re.findall(r'\d+|[a-z]', n)]


def bolumler(d):
    toc = d.get_toc()
    out = []
    for k, (lv, ad, pg) in enumerate(toc):
        if lv <= 2:
            nxt = next((t[2] for t in toc[k + 1:] if t[0] <= lv), d.page_count + 1)
            out.append({'duzey': lv, 'ad': ad.strip(), 'ilk': pg, 'son': max(pg, nxt - 1)})
    return out


def oku_kayit(yer, im):
    yol = os.path.join(yer, 'envanter.json')
    if not os.path.exists(yol):
        return None
    with open(yol, encoding='utf-8') as f:
        e = json.load(f)
    if e.get('imza') != im or 'araliklar' not in e:
        print('KAYNAK DEĞİŞTİ ya da eski kayıt: envanter yeniden kuruluyor, önceki betiklerdeki numaraları kontrol et.')
        return None
    return e


def kur(kaynak, istenen):
    """İstenen aralıkları envantere ekler; (yer, kayıt ya da None, yeni kuruldu mu) döndürür."""
    yer = klasor(kaynak)
    d = fitz.open(kaynak)
    im = imza(kaynak)
    e = oku_kayit(yer, im)
    if not istenen:
        return yer, e, False, d
    for a, b in istenen:
        if not 1 <= a <= b <= d.page_count:
            sys.exit('Geçersiz aralık %d-%d (kaynak %d sayfa)' % (a, b, d.page_count))
    eski = e['araliklar'] if e else []
    yeni = birlestir(eski + [list(x) for x in istenen])
    if yeni == eski:
        return yer, e, False, d
    os.makedirs(yer, exist_ok=True)
    nolar = sayfalar(yeni)
    denk, tablo, sekil = tara(d, nolar)
    e = {'kaynak': os.path.basename(kaynak), 'imza': im, 'sayfa_sayisi': d.page_count, 'araliklar': yeni,
         'bolumler': bolumler(d), 'denklemler': denk, 'tablolar': tablo, 'sekiller': sekil}
    with open(os.path.join(yer, 'envanter.json'), 'w', encoding='utf-8') as f:
        json.dump(e, f, ensure_ascii=False, indent=0)
    with open(os.path.join(yer, 'metin.txt'), 'w', encoding='utf-8') as f:
        for no in nolar:
            f.write('\n===== PDF sayfa %d\n' % no)
            f.write(d[no - 1].get_text())
    return yer, e, True, d


def is_metni(yer, istenen, work):
    """Envanter metninden yalnız bu işin sayfalarını <work>/metin.txt'ye yazar; yaklaşık bin token döndürür."""
    with open(os.path.join(yer, 'metin.txt'), encoding='utf-8') as f:
        parcalar = re.split(r'(?m)^(?====== PDF sayfa \d+$)', f.read())
    iste = set(sayfalar(istenen))
    secili = [p for p in parcalar if (m := re.match(r'===== PDF sayfa (\d+)', p)) and int(m.group(1)) in iste]
    os.makedirs(work, exist_ok=True)
    hedef = os.path.join(work, 'metin.txt')
    with open(hedef, 'w', encoding='utf-8') as f:
        f.write('\n'.join(secili))
    return hedef, os.path.getsize(hedef) / 4 / 1000


def onceki_betikler(kaynak):
    """Aynı klasörde daha önce üretilmiş belgelerin içerik betikleri."""
    kok = os.path.join(os.path.dirname(os.path.abspath(kaynak)), '.kaynak')
    out = []
    if not os.path.isdir(kok):
        return out
    for ad in sorted(os.listdir(kok)):
        yer = os.path.join(kok, ad)
        if ad == 'envanter' or not os.path.isdir(yer):
            continue
        for f in sorted(os.listdir(yer)):
            if ICERIK_ADI.match(f):
                yol = os.path.join(yer, f)
                out.append((ad, yol, os.path.getsize(yol)))
    return out


def icindekiler(d):
    bol = bolumler(d)
    if not bol:
        print('Yer imi yok: içindekiler sayfasını kaynağın kendisinden oku.')
        return
    print('İçindekiler:')
    for b in bol:
        print('  ' * b['duzey'] + '%s [%d–%d]' % (b['ad'], b['ilk'], b['son']))


def ozet(kaynak, d, yer, e, kuruldu, istenen, work):
    if not istenen:
        icindekiler(d)
    if e:
        print('Envanter %s: %s' % ('kuruldu' if kuruldu else 'hazır, yeniden kullanılıyor', yer))
        print('Kaynak: %s | %d sayfa | envanterdeki aralıklar: %s'
              % (e['kaynak'], e['sayfa_sayisi'], ', '.join('%d–%d' % tuple(x) for x in e['araliklar'])))
        print('Dizin: %d denklem, %d tablo, %d şekil' % (len(e['denklemler']), len(e['tablolar']), len(e['sekiller'])))
        if work:
            hedef, bin_token = is_metni(yer, istenen or [tuple(x) for x in e['araliklar']], work)
            print('Bu işin metni: %s ≈ %d bin token' % (hedef, bin_token))
        if os.path.exists(os.path.join(yer, 'figs.json')):
            with open(os.path.join(yer, 'figs.json'), encoding='utf-8') as f:
                n = len(json.load(f))
            print('Şekiller hazır (%d şekil): kartta gerekenleri --sekil-eksik ile denetle, eksikleri kes, gerisini --sekil-al ile al.' % n)
    else:
        print('Envanter henüz yok: %s' % kaynak)
    bet = onceki_betikler(kaynak)
    if bet:
        print('Önceki içerik betikleri:')
        for ad, yol, sz in bet:
            print('  %s  ≈ %d bin token  %s' % (ad, sz / 4 / 1000, yol))


def serit(d, e, work, secim, aralik):
    from PIL import Image, ImageDraw
    os.makedirs(work, exist_ok=True)
    nolar = sorted(e['denklemler'], key=sira)
    if secim:
        nolar = [n for n in nolar if n in secim]
    if aralik:
        a, b = sira(aralik[0]), sira(aralik[1])
        nolar = [n for n in nolar if a <= sira(n) <= b]
    parcalar = []
    for n in nolar:
        x = e['denklemler'][n]
        p = d[x['sayfa'] - 1]
        r = fitz.Rect(x['kutu'])
        c = fitz.Rect(p.rect.x0 + 25, r.y0 - 21, p.rect.x1 - 8, r.y1 + 19) & p.rect
        pm = p.get_pixmap(dpi=88, clip=c, alpha=False)
        im = Image.frombytes('RGB', (pm.width, pm.height), pm.samples)
        dr = ImageDraw.Draw(im)
        dr.rectangle((0, 0, 62, 11), fill='white')
        dr.text((1, 0), '%s s%d' % (n, x['sayfa']), fill='red')
        parcalar.append(im)
    yollar, grup, y = [], [], 0

    def yaz():
        t = Image.new('RGB', (max(g.width for g in grup), sum(g.height + 2 for g in grup)), 'white')
        yy = 0
        for g in grup:
            t.paste(g, (0, yy))
            yy += g.height + 2
        yol = os.path.join(work, 'serit%02d.png' % len(yollar))
        t.save(yol)
        yollar.append(yol)

    for im in parcalar:
        if y + im.height > 1500 and grup:
            yaz()
            grup, y = [], 0
        grup.append(im)
        y += im.height + 2
    if grup:
        yaz()
    print('%d denklem, %d görsel:' % (len(parcalar), len(yollar)))
    for yol in yollar:
        print(' ', yol)
    print('Kırpıntı denklemin bir kısmını kesebilir; grup denklemlerde sayfaya bak.')


def sekil_kopya(kaynak_yer, hedef_yer, yalniz=None):
    """yalniz: yalnız bu numaralar kopyalanır; aynı aralıktaki elle düzeltilmiş kesimler ezilmez."""
    kaynak_fig = os.path.join(kaynak_yer, 'fig')
    if not (os.path.isdir(kaynak_fig) and os.path.exists(os.path.join(kaynak_yer, 'figs.json'))):
        sys.exit('Şekil bulunamadı: %s içinde fig/ ve figs.json gerekir' % kaynak_yer)
    os.makedirs(hedef_yer, exist_ok=True)
    with open(os.path.join(kaynak_yer, 'figs.json'), encoding='utf-8') as f:
        gelen = json.load(f)
    if yalniz is not None:
        eksik = [n for n in yalniz if n not in gelen]
        if eksik:
            sys.exit('Kesilmemiş şekil: %s' % ', '.join(eksik))
        gelen = {n: gelen[n] for n in yalniz}
    os.makedirs(os.path.join(hedef_yer, 'fig'), exist_ok=True)
    for n in gelen:
        shutil.copy2(os.path.join(kaynak_fig, n + '.png'), os.path.join(hedef_yer, 'fig', n + '.png'))
    hedef_json = os.path.join(hedef_yer, 'figs.json')
    birlesik = json.load(open(hedef_json, encoding='utf-8')) if os.path.exists(hedef_json) else {}
    birlesik.update(gelen)
    json.dump(birlesik, open(hedef_json, 'w', encoding='utf-8'))
    print('Kopyalandı: %d şekil -> %s' % (len(gelen), hedef_yer))


def numara_bul(d, nolar):
    """Her denklem, tablo ve şekil numarasının tanımlandığı PDF sayfaları (1 tabanlı).
    Tablo ve şekilde başlık satırı, denklemde satır başındaki (n) aranır; metin içi atıflar sayılmaz."""
    bulunan = {n: [] for n in nolar}
    for i, p in enumerate(d):
        t = p.get_text()
        for n in nolar:
            e = re.escape(n)
            if re.search(r'^(?:TABLE|Table|Tablo|FIGURE|Figure|Fig\.|Şekil)\s+%s(?![\d.])|^\(%s\),?\s*$' % (e, e), t, re.M):
                bulunan[n].append(i + 1)
    return bulunan


def sekil_eksik(yer, nolar):
    """nolar içinden envanterde kesilmemiş olanlar."""
    yol = os.path.join(yer, 'figs.json')
    var = json.load(open(yol, encoding='utf-8')) if os.path.exists(yol) else {}
    return [n for n in nolar if n not in var]


def main():
    a = sys.argv[1:]

    def al(ad, n=1):
        if ad not in a:
            return None
        k = a.index(ad)
        v = a[k + 1:k + 1 + n]
        del a[k:k + 1 + n]
        return v

    ser = al('--serit')
    no = al('--no')
    ar = al('--aralik', 2)
    kay = al('--sekil-kaydet')
    gel = al('--sekil-al')
    eks = al('--sekil-eksik')
    yal = al('--yalniz')
    bul = al('--bul')
    wrk = al('--work')
    kaynak = a[0]
    istenen = []
    for x in a[1:]:
        m = re.fullmatch(r'(\d+)-(\d+)', x)
        if not m:
            sys.exit('Aralık biçimi ilk-son olmalı: %s' % x)
        istenen.append((int(m.group(1)), int(m.group(2))))
    yer, e, kuruldu, d = kur(kaynak, istenen)
    if ser:
        if not e:
            sys.exit('Önce sayfa aralıklarıyla envanteri kur.')
        serit(d, e, ser[0], set(no[0].split(',')) if no else None, ar)
    elif kay:
        sekil_kopya(kay[0], yer, yal[0].split(',') if yal else None)
    elif gel:
        sekil_kopya(yer, gel[0])
    elif bul:
        for n, s in numara_bul(d, bul[0].split(',')).items():
            print('%s: %s' % (n, ', '.join(map(str, s)) or 'bulunamadı'))
    elif eks:
        nolar = [n for n in eks[0].split(',') if n]
        eksik = sekil_eksik(yer, nolar)
        print('HAZIR: %s' % (', '.join(n for n in nolar if n not in eksik) or 'yok'))
        print('EKSİK ŞEKİL: %s' % (', '.join(eksik) or 'yok'))
    else:
        ozet(kaynak, d, yer, e, kuruldu, istenen, wrk[0] if wrk else None)


if __name__ == '__main__':
    main()
