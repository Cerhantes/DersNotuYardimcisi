"""Konu seçildikten sonraki hazırlık, tek komutta: metin, sayfa farkı, şekil bayrakları, şekil tespiti ve kesimi.

Kullanım:
    python -W ignore hazirla.py <kitap.pdf> <ilk-son> [<ilk-son> ...] --work <work>
                                [--cap R] [--cap-font R] [--label-font R] [--label-len N] [--pad N] [--cap-above]

Sırayla:
  1. envanter.py: aralıkların metni <work>/metin.txt'ye
  2. aralıktaki basılı sayfa numaralarından PDF ↔ kitap sayfa farkı
  3. detect_figs.py bayrakları aralığın kendi sayfalarından seçilir (verilen bayrak seçimin önüne geçer);
     her seçim gerekçesiyle yazılır
  4. Envanterde aralığın bütün şekilleri varsa (daha önce kesilip gözden geçirilmiş) onlar alınır; yoksa
     detect_figs.py (her aralık için) + crop_figs.py + sekil_kenar.py çalışır
Gözle kontrolde durur: temas sayfalarını ve KENAR satırlarını açmak hâlâ şarttır. Düzeltmeden sonra
crop_figs.py doğrudan yeniden çalıştırılır (bkz. SEKIL.md); bu betik yeniden çalıştırılırsa split.json ve
over.json korunur.
Çıkış kodu: 0 hazır, 1 kontrol edilecek UYARI var ya da şekil başlığı bulunamadı.
"""
import argparse, collections, json, os, re, subprocess, sys
import pymupdf as fitz

BURASI = os.path.dirname(os.path.abspath(__file__))
ORTAK = os.path.normpath(os.path.join(BURASI, '..', '..', '..', 'ortak'))
VARSAYILAN_CAP = r'^\s*(FIGURE|Figure|Fig\.|ŞEKİL|Şekil)\s*\d+[.\-]\d+'
GENIS_CAP = r'^\s*(FIGURE|Figure|FIG\.?|Fig\.?|ŞEKİL|Şekil|Şek\.)\s*\d+[.\-–]\d+'
VARSAYILAN_CAP_FONT = r'Bold|Black|Heavy|Demi|Semi|Bd'


def calistir(betik, *arg):
    """Betiği aynı Python'la çalıştırır, çıktısını olduğu gibi basar; (çıkış kodu, çıktı)."""
    r = subprocess.run([sys.executable, '-W', 'ignore', betik] + [str(a) for a in arg], capture_output=True,
                       text=True, encoding='utf-8', env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    cikti = (r.stdout or '') + (r.stderr or '')
    if cikti.strip():
        print(cikti.rstrip())
    return r.returncode, cikti


def sayfa_listesi(araliklar):
    return [i for a, b in araliklar for i in range(a, b + 1)]


def sayfa_farki(d, sayfalar):
    """Aralıktaki sayfaların üst/alt satırındaki tek başına sayılardan PDF − basılı farkı: Counter."""
    say = collections.Counter()
    for no in sayfalar:
        satir = [l.strip() for l in d[no - 1].get_text().splitlines() if l.strip()]
        for l in satir[:3] + satir[-3:]:
            if re.fullmatch(r'\d{1,4}', l) and 0 <= no - int(l) < 200:
                say[no - int(l)] += 1
                break
    return say


def aile(font):
    """'ABCDEF+Helvetica-Bold' -> 'Helvetica'"""
    return re.split(r'[-,]', font.split('+')[-1])[0]


def yazi_tipleri(d, sayfalar, cap):
    """(başlık satırlarının ilk yazı tipi Counter, etiket adaylarının yazı tipi Counter, gövde yazı tipi Counter)"""
    cap_re = re.compile(cap)
    capf, etiket, govde = collections.Counter(), collections.Counter(), collections.Counter()
    for no in sayfalar:
        p = d[no - 1]
        cizim = [fitz.Rect(x['rect']) for x in p.get_drawings()] + [fitz.Rect(x['bbox']) for x in p.get_image_info()]
        cizim = [r for r in cizim if not r.is_infinite and r.width * r.height < p.rect.width * p.rect.height * 0.8]
        for b in p.get_text('dict')['blocks']:
            for l in b.get('lines', []):
                t = ''.join(s['text'] for s in l['spans'])
                if cap_re.match(t):
                    capf[l['spans'][0]['font']] += 1
                for s in l['spans']:
                    govde[s['font']] += len(s['text'])
                    r = fitz.Rect(s['bbox'])
                    if 0 < len(s['text'].strip()) <= 25 and any(c.intersects(r) for c in cizim):
                        etiket[s['font']] += 1
    return capf, etiket, govde


def bayrak_sec(d, sayfalar, verilen):
    """detect_figs.py bayrakları ve gerekçeleri: ({bayrak: değer}, [gerekçe satırları], başlık bulundu mu)."""
    secim, neden = {}, []
    cap = verilen.cap or VARSAYILAN_CAP
    capf, etiket, govde = yazi_tipleri(d, sayfalar, cap)
    if not capf and not verilen.cap:
        capf2, _, _ = yazi_tipleri(d, sayfalar, GENIS_CAP)
        if capf2:
            cap, capf = GENIS_CAP, capf2
            secim['--cap'] = cap
            neden.append('--cap: varsayılan biçimle başlık yok, geniş biçim (FIG., Şek., en tire) %d satır buldu' % sum(capf.values()))
    elif verilen.cap:
        secim['--cap'] = verilen.cap
        neden.append('--cap: verildi')
    if not capf:
        neden.append('ŞEKİL BAŞLIĞI BULUNAMADI: aralıkta "Figure n.m" biçiminde satır yok. book_info.py ile kitabın başlık biçimine '
                     'bak, --cap ile ver (ör. "^Şekil \\d+-\\d+"); şekil yoksa bu normaldir')
        return secim, neden, False
    govde_ana = govde.most_common(1)[0][0] if govde else ''

    # başlık yazı tipi: başlıklar kalınsa varsayılan yeter; değilse gövdeden farklı olan yazı tipi başlıktır
    if verilen.cap_font:
        secim['--cap-font'] = verilen.cap_font
        neden.append('--cap-font: verildi')
    else:
        toplam = sum(capf.values())
        kalin = sum(c for f, c in capf.items() if re.search(VARSAYILAN_CAP_FONT, f))
        ozet = ', '.join('%s %d' % (f, c) for f, c in capf.most_common(4))
        if kalin >= 0.3 * toplam:
            neden.append('--cap-font: varsayılan (başlık satırlarının %d/%d\'i kalın yazı tipiyle başlıyor: %s)' % (kalin, toplam, ozet))
        else:
            aday = [(f, c) for f, c in capf.most_common() if aile(f) != aile(govde_ana)]
            if aday:
                secim['--cap-font'] = re.escape(aday[0][0].split('+')[-1])
                neden.append('--cap-font: %s (başlıklar kalın değil; gövde metninden (%s) farklı en sık başlık yazı tipi; adaylar: %s)'
                             % (aday[0][0], govde_ana, ozet))
            else:
                neden.append('UYARI --cap-font: başlıklar kalın değil ve gövdeyle aynı yazı tipinde (%s): metin içi "Fig. n" atıfları '
                             'başlık sanılabilir; temas sayfalarında numaraları dikkatle kontrol et' % ozet)

    # etiket yazı tipi: etiketler gövdeden farklı tek bir yazı tipindeyse onu ver (daha temiz), değilse auto
    if verilen.label_font:
        secim['--label-font'] = verilen.label_font
        neden.append('--label-font: verildi')
    elif etiket:
        top_f, top_c = etiket.most_common(1)[0]
        aile_say = collections.Counter()
        for f, c in etiket.items():
            aile_say[aile(f)] += c
        top_aile, aile_c = aile_say.most_common(1)[0]
        pay = aile_c / sum(etiket.values())
        if top_aile != aile(govde_ana) and pay >= 0.6:
            secim['--label-font'] = '^(?:[A-Z]{6}\\+)?' + re.escape(top_aile)
            neden.append('--label-font: %s ailesi (etiket adaylarının %%%d\'i; gövde %s)' % (top_aile, round(pay * 100), govde_ana))
        else:
            neden.append('--label-font: auto (etiketler gövdeyle aynı ya da karışık yazı tipinde: en sık %s %%%d)'
                         % (top_aile, round(pay * 100)))
    for ad in ('label_len', 'pad'):
        v = getattr(verilen, ad)
        if v is not None:
            secim['--' + ad.replace('_', '-')] = v
            neden.append('--%s: verildi' % ad.replace('_', '-'))
    return secim, neden, True


def envanter_sekilleri(kaynak, araliklar):
    """(aralıktaki şekil numaraları, envanterde hazır olanlar) — envanter.json'dan."""
    sys.path.insert(0, ORTAK)
    import envanter
    yer = envanter.klasor(kaynak)
    try:
        e = json.load(open(os.path.join(yer, 'envanter.json'), encoding='utf-8'))
    except OSError:
        return [], []
    sayfalar = set(sayfa_listesi(araliklar))
    nolar = sorted((n for n, x in e.get('sekiller', {}).items() if x['sayfa'] in sayfalar), key=envanter.sira)
    eksik = envanter.sekil_eksik(yer, nolar)
    return nolar, [n for n in nolar if n not in eksik]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('kaynak')
    ap.add_argument('araliklar', nargs='+', help='ilk-son (PDF sayfa numarası)')
    ap.add_argument('--work', required=True)
    ap.add_argument('--cap'); ap.add_argument('--cap-font', dest='cap_font'); ap.add_argument('--label-font', dest='label_font')
    ap.add_argument('--label-len', dest='label_len', type=int); ap.add_argument('--pad', type=float)
    ap.add_argument('--cap-above', dest='cap_above', action='store_true')
    a = ap.parse_args(argv)
    araliklar = []
    for x in a.araliklar:
        m = re.fullmatch(r'(\d+)-(\d+)', x)
        if not m:
            sys.exit('Aralık biçimi ilk-son olmalı: %s' % x)
        araliklar.append((int(m.group(1)), int(m.group(2))))
    os.makedirs(a.work, exist_ok=True)
    d = fitz.open(a.kaynak)
    sorun = False

    print('=== 1. METİN (envanter)')
    calistir(os.path.join(ORTAK, 'envanter.py'), a.kaynak, *a.araliklar, '--work', a.work)

    print('\n=== 2. SAYFA FARKI (PDF no − basılı no, bu aralıkta)')
    fark = sayfa_farki(d, sayfa_listesi(araliklar))
    if fark:
        print('  ' + ', '.join('+%d: %d sayfa' % fc for fc in fark.most_common(3)))
        if len(fark) > 1 and fark.most_common(2)[1][1] > 2:
            print('  UYARI: aralıkta birden çok fark var; sınır sayfalarını metin.txt\'de doğrula')
    else:
        print('  basılı sayfa numarası bulunamadı (raporda PDF numaralarını kullan)')

    print('\n=== 3. ŞEKİLLER')
    nolar, hazir = envanter_sekilleri(a.kaynak, araliklar)
    if nolar and len(hazir) == len(nolar):
        print('Aralığın %d şeklinin hepsi envanterde (daha önce kesilip gözden geçirilmiş): alınıyor, tespit ve kesim atlandı.' % len(nolar))
        calistir(os.path.join(ORTAK, 'envanter.py'), a.kaynak, '--sekil-al', a.work)
        print('\nSONRAKİ ADIM: içerik betiğini yaz (şekiller hazır).')
        return 0
    if hazir:
        print('Envanterde aralığın %d/%d şekli var; eksikler için bütün aralık yeniden kesilecek (hepsini gözden geçir).'
              % (len(hazir), len(nolar)))
    secim, neden, bulundu = bayrak_sec(d, sayfa_listesi(araliklar), a)
    print('SEÇİLEN BAYRAKLAR:')
    for n in neden:
        print('  ' + n)
        sorun |= n.startswith(('UYARI', 'ŞEKİL BAŞLIĞI'))
    if not bulundu:
        return 1
    bayrak = [str(x) for kv in secim.items() for x in kv]
    print('  detect_figs.py ' + (' '.join(('"%s"' % x if ' ' in x or '\\' in x else x) for x in bayrak) or '(varsayılan bayraklar)'))

    birlesik = {}
    for ilk, son in araliklar:
        calistir(os.path.join(BURASI, 'detect_figs.py'), a.kaynak, a.work, ilk, son, *bayrak)
        birlesik.update(json.load(open(os.path.join(a.work, 'det.json'), encoding='utf-8')))
    json.dump(birlesik, open(os.path.join(a.work, 'det.json'), 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
    with open(os.path.join(a.work, 'bayraklar.txt'), 'w', encoding='utf-8') as f:
        f.write(' '.join(bayrak) + (' --cap-above' if a.cap_above else '') + '\n')

    print('\n=== 4. KESİM (crop_figs)')
    kod, cikti = calistir(os.path.join(BURASI, 'crop_figs.py'), a.kaynak, a.work, *(['--cap-above'] if a.cap_above else []))
    uyari = [l for l in cikti.splitlines() if l.startswith('UYARI')]
    figs = json.load(open(os.path.join(a.work, 'figs.json'), encoding='utf-8')) if os.path.exists(os.path.join(a.work, 'figs.json')) else {}
    if nolar:
        kayip = [n for n in nolar if n not in figs]
        if kayip:
            print('UYARI envanterin şekil dizininde olup kesilmeyen numaralar: %s -> kitapta bak; şekilse split.json / over.json '
                  'ile ver (satır başına düşmüş metin içi atıf da olabilir)' % ', '.join(kayip))
            uyari.append('kayıp')

    print('\n=== 5. KIRPIK ŞEKİL (sekil_kenar)')
    _, kenar = calistir(os.path.join(ORTAK, 'sekil_kenar.py'), os.path.join(a.work, 'fig'))
    sheets = sorted(f for f in os.listdir(a.work) if re.fullmatch(r'sheet_\d+\.png', f))

    print('\n=== GÖZLE KONTROL (atlanamaz)')
    print('AÇILACAK TEMAS SAYFALARI: ' + ' '.join(os.path.join(a.work, s) for s in sheets))
    if uyari:
        print('Önce UYARI satırlarındaki sayfalara bak.')
    if 'KENAR:' in kenar:
        print('KENAR satırlarındaki şekilleri kaynağıyla karşılaştır (küçük temas sayfasında kesik kolay kaçar).')
    print('Kitapta başlık şeklin üstündeyse --cap-above ile yeniden çalıştır. Düzeltme yolları: SEKIL.md.')
    print('Temizse: envanter.py <kitap> --sekil-kaydet <work>')
    return 1 if (sorun or uyari) else 0


if __name__ == '__main__':
    sys.exit(main())
