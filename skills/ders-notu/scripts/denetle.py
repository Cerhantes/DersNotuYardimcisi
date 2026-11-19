"""Her derlemeden sonra bütün denetimler, tek komutta. Her aracın çıktısı kendi başlığı altında olduğu gibi basılır,
sonda engellerin listesi verilir.

Kullanım:
    python -W ignore denetle.py <out.pdf> <work> --kaynak <kitap.pdf> --aralik <ilk-son> [<ilk-son> ...]
                                [--disarida <dosya>] [--haric <dosya>]
    python -W ignore denetle.py <out.pdf> <work>          (kaynaksız: üslup, belge içi denklem, şekil atfı, sayfa farkı)

Çalışanlar:
  0. <work>/derleme.json  notlib'in derleme uyarıları (sığmayan denklem, yazı tipinde olmayan simge, şeklin bıraktığı boşluk)
  1. uslup_denetim.py   KESİN listesi boşalmalı (--kaynak varsa şekil etiketleri de)
  2. denklem_kapsam.py  her aralık için kaynakla (YOK / YALNIZ ANILMIŞ boşalmalı) + belge içi kip
  3. sekil_atif.py      ANILAN AMA YOK boşalmalı
  4. sayfa_fark.py      AÇILACAK sayfalar, TAŞMA, BÖLÜNMÜŞ HÜCRE?
--disarida denklem_kapsam.py'ye, --haric sekil_atif.py'ye geçer (her satırda gerekçe).
Çıkış kodu: 0 otomatik denetimler temiz, 1 engel var, 2 kaynak gözle karşılaştırılmalı (numaralı denklem bulunamadı).
Otomatik denetimler temiz olsa bile AÇILACAK sayfalara gözle bakılmadan belge teslim edilmez.
"""
import argparse, json, os, re, subprocess, sys

BURASI = os.path.dirname(os.path.abspath(__file__))
ORTAK = os.path.normpath(os.path.join(BURASI, '..', '..', '..', 'ortak'))


def calistir(baslik, betik, *arg):
    print('\n=== %s' % baslik)
    r = subprocess.run([sys.executable, '-W', 'ignore', betik] + [str(a) for a in arg], capture_output=True,
                       text=True, encoding='utf-8', env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    cikti = ((r.stdout or '') + (r.stderr or '')).rstrip()
    print(cikti or '(çıktı yok)')
    return r.returncode, cikti


KONUM = re.compile(r'\b(?:(?:üst|alt|orta|ilk|ikinci|üçüncü|son)\w*\s+(?:satır|kısm|kısım)\w*|satır(?:ı|ları|larında)\b'
                   r'|üstte\b|altta\b|ortada\b|en alttaki|en üstteki)', re.I)


OLCULEN_ESIK = 4.5   # cm: bu ve üstü sayfa altı boşluk (yeni h1 bölümünden önce değilse) gözle bakılır


def olculen_bosluklar(pdf, esik=OLCULEN_ESIK):
    """PDF'te her sayfanın altında kalan boş yüksekliği ölçer (cm). derleme.json yalnız şekil kaynaklı boşlukları
    kaydeder; başlık, kutu, formül grubu ya da bölünemeyen paragraf yüzünden kalan boşluk burada yakalanır.
    Sonraki sayfa yeni bir h1 bölümüyle başlıyorsa boşluk tasarım gereğidir, sayılmaz. Döner: [(sayfa, cm)]."""
    import pymupdf as fitz
    cm = 72 / 2.54
    d = fitz.open(pdf)
    out = []
    for i in range(2, len(d) - 1):           # kapak, içindekiler ve son sayfa hariç
        p, q = d[i], d[i + 1]
        H = p.rect.height
        ys = [b[3] for b in p.get_text('blocks') if 70 < b[1] < H - 60]
        ys += [im['bbox'][3] for im in p.get_image_info() if im['bbox'][1] < H - 60]
        ys += [dr['rect'].y1 for dr in p.get_drawings() if 70 < dr['rect'].y1 < H - 60 and dr['rect'].height < 0.9 * H]
        if not ys:
            continue
        bos = (H - 2.0 * cm - max(ys)) / cm
        if bos < esik:
            continue
        spans = [s for b in q.get_text('dict')['blocks'] if b['type'] == 0 for l in b['lines'] for s in l['spans']
                 if 55 < s['bbox'][1] < H - 60 and s['text'].strip()]
        if spans and min(spans, key=lambda s: s['bbox'][1])['size'] > 15:
            continue                             # sonraki sayfa yeni bölüm (h1)
        out.append((i + 1, round(bos, 1)))
    return out


def konum_sozleri(work, dizilen):
    """Yeniden dizilen şeklin parçaları artık slayttaki yerinde değil: açıklamasında ya da onu anlatan paragraflarda
    (şekli numarasıyla anan ya da hemen ardından gelen üç paragraf) "üst satır", "altta" gibi konum sözü kalmamalı."""
    yol = os.path.join(work, 'kayit.json')
    if not dizilen or not os.path.exists(yol):
        return []
    with open(yol, encoding='utf-8') as f:
        kayit = json.load(f)
    out, son, kalan = [], None, 0
    for e in kayit:
        if e.get('t') == 'fig':
            son, kalan = (e['no'], 3) if e['no'] in dizilen else (None, 0)
            if son:
                out += [(son, m.group(0)) for m in KONUM.finditer(e.get('cap') or '')]
            continue
        if e.get('t', '').startswith('h'):
            son, kalan = None, 0
        if e.get('t') != 'p':
            continue
        metin = e.get('metin', '')
        anilan = [n for n in dizilen if re.search(r'Şekil %s(?![0-9a-z])' % re.escape(n), metin)]
        if son and kalan > 0:
            anilan.append(son)
            kalan -= 1
        for n in dict.fromkeys(anilan):
            out += [(n, m.group(0)) for m in KONUM.finditer(metin)]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf'); ap.add_argument('work')
    ap.add_argument('--kaynak')
    ap.add_argument('--aralik', nargs='+', default=[], help='kaynak sayfa aralıkları: ilk-son')
    ap.add_argument('--disarida'); ap.add_argument('--haric')
    a = ap.parse_args(argv)
    if a.kaynak and not a.aralik:
        sys.exit('--kaynak ile --aralik da verilmeli (denklem kapsamı kaynak sayfa aralığında ölçülür)')
    engel, gozle = [], []

    print('=== 0. DERLEME UYARILARI')
    yol = os.path.join(a.work, 'derleme.json')
    if not os.path.exists(yol) or os.path.getmtime(yol) < os.path.getmtime(a.pdf) - 5:
        print('derleme.json yok ya da PDF\'ten eski: not güncel notlib ile derlenmemiş, derleme uyarıları denetlenemedi')
        gozle.append('derleme uyarıları: derleme çıktısındaki UYARI satırlarına kendin bak')
    else:
        with open(yol, encoding='utf-8') as f:
            dr = json.load(f)
        for t in dr.get('elle_denklem', []):
            print('ELLE DÜZENLENECEK DENKLEM: ' + t)
        for g in dr.get('eksik_glif', []):
            print('EKSİK GLİF (kutu görünür): %s (U+%04X)' % (g, ord(g)))
        if dr.get('elle_denklem'):
            engel.append('%d denklem sığmıyor (DUZEN.md: uzun parçaya ad ver ya da elle böl)' % len(dr['elle_denklem']))
        if dr.get('eksik_glif'):
            engel.append('yazı tipinde olmayan simge: %s (simgeyi değiştir)' % ' '.join(dr['eksik_glif']))
        esik = dr.get('bosluk_engel_cm', 6.0)
        buyuk = []
        for no, sayfa, b in dr.get('bosluk', []):
            print('BOŞLUK: s.%d altında %.1f cm (Şekil %s sığmadı, sonraki sayfaya geçti)%s'
                  % (sayfa, b, no, '' if b >= esik else ' — küçük, bilgi'))
            if b >= esik:
                buyuk.append('s.%d %.1f cm (Şekil %s)' % (sayfa, b, no))
        if buyuk:
            engel.append('sayfa altında büyük boşluk: %s (DUZEN.md › Büyük boşluk)' % ', '.join(buyuk))
        if not dr.get('elle_denklem') and not dr.get('eksik_glif') and not dr.get('bosluk'):
            print('temiz')

        konum = konum_sozleri(a.work, dr.get('dizilen', []))
        for no, metin in konum:
            print('KONUM SÖZÜ: Şekil %s yeniden dizildi, metin parçaları yerleriyle anıyor: "%s"' % (no, metin))
        if konum:
            gozle.append('yeniden dizilen şekil konumla anılmış (%s): "üst satır", "altta" yerine "ilk örnek", harf ya da içerik '
                         'kullan (USLUP.md › Şekiller)' % ', '.join(sorted({n for n, _ in konum})))

    arg = [a.work] + (['--kaynak', a.kaynak] if a.kaynak else [])
    kod, c = calistir('1. ÜSLUP', os.path.join(BURASI, 'uslup_denetim.py'), *arg)
    if kod:
        m = re.search(r'(\d+) KESİN', c)
        engel.append('üslup: %s KESİN' % (m.group(1) if m else '?'))

    for x in a.aralik:
        m = re.fullmatch(r'(\d+)-(\d+)', x)
        if not m:
            sys.exit('Aralık biçimi ilk-son olmalı: %s' % x)
        ek = ['--disarida', a.disarida] if a.disarida else []
        kod, c = calistir('2. DENKLEM KAPSAMI (kaynak %s)' % x, os.path.join(ORTAK, 'denklem_kapsam.py'),
                          a.kaynak, a.pdf, '--from', m.group(1), '--to', m.group(2), *ek)
        if kod == 2:
            gozle.append('kaynak %s: numaralı denklem bulunamadı → kaynağın her sayfasını görüntü olarak aç, her denklemi '
                         'betikle tek tek karşılaştır' % x)
        elif kod:
            satir = [l.split(':')[0] for l in c.splitlines() if l.startswith(('YOK', 'YALNIZ', 'GEREKÇESİZ'))]
            engel.append('denklem kapsamı %s: %s' % (x, ', '.join(satir)))
    kod, c = calistir('2. DENKLEM (belge içi)', os.path.join(ORTAK, 'denklem_kapsam.py'), '-', a.pdf)
    if kod:
        engel.append('belgede yalnız anılmış denklem')

    kod, c = calistir('3. ŞEKİL ATFI', os.path.join(ORTAK, 'sekil_atif.py'), a.pdf, *(['--haric', a.haric] if a.haric else []))
    if kod:
        engel.append('anılan ama belgede olmayan şekil')

    kod, c = calistir('4. SAYFA FARKI', os.path.join(ORTAK, 'sayfa_fark.py'), a.pdf, a.work)
    if 'TAŞMA' in c:
        engel.append('sağ kenar taşması')
    if 'BÖLÜNMÜŞ HÜCRE?' in c:
        gozle.append('BÖLÜNMÜŞ HÜCRE? satırındaki tablolara bak')
    m = re.search(r'AÇILACAK: (.*)', c)
    acilacak = m.group(1) if m and not m.group(1).startswith('yok') else ''

    print('\n=== 5. ÖLÇÜLEN BOŞLUK (sayfa altı, ≥ %.1f cm, yeni bölümden önce değil)' % OLCULEN_ESIK)
    olc = olculen_bosluklar(a.pdf)
    for sayfa, b in olc:
        print('BOŞLUK (ölçülen): s.%d altında %.1f cm' % (sayfa, b))
    if not olc:
        print('temiz')
    else:
        gozle.append('ölçülen sayfa altı boşluğu: %s → sayfaya bak; nedeni başlık, kutu, formül grubu ya da şekilse '
                     'DUZEN.md › Büyük boşluk' % ', '.join('s.%d' % s for s, _ in olc))
        acilacak = (acilacak + ' ' if acilacak else '') + ' '.join('rv%d.png' % s for s, _ in olc)

    print('\n=== SONUÇ')
    if not a.kaynak:
        print('NOT: kaynak verilmedi; denklem kapsamı kaynakla ve şekil etiketleri denetlenmedi.')
    for e in engel:
        print('ENGEL: ' + e)
    for g in gozle:
        print('GÖZLE: ' + g)
    if acilacak:
        print('AÇ (görülmemiş sayfalar): ' + acilacak)
    if engel:
        print('TESLİM EDİLEMEZ: engelleri gider, yeniden derle, bu betiği yeniden çalıştır.')
        return 1
    if gozle:
        print('OTOMATİK DENETİMLER TEMİZ, GÖZLE KARŞILAŞTIRMA BEKLİYOR: GÖZLE satırlarını tamamla.')
        return 2
    print('OTOMATİK DENETİMLER TEMİZ.' + (' Kalan: AÇ satırındaki sayfalara gözle bak.' if acilacak else
                                         ' Görülmemiş sayfa yok; düzen değiştiyse rv_ov.png ile sayfa dengesine bak.'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
