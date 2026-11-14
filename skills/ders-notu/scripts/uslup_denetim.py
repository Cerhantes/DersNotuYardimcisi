"""Üslup denetimi: ders notunun USLUP.md kurallarına uyup uymadığını notun iskeletinden denetler.

Kullanım:
    python -W ignore uslup_denetim.py <work> [--kaynak <kitap.pdf>]

<work>/kayit.json notlib'in make() sırasında yazdığı iskelettir (başlık, paragraf, kutu, şekil, denklem).
--kaynak verilirse şekillerin kitaptaki yazılı etiketleri de okunur (figs.json'daki sayfa ve kesimden):
etiketi olan şeklin terim satırı denetlenir.

İki sınıf bulgu:
    KESİN  yanlış alarm riski düşük kural; liste boşalmadan belge teslim edilmez
    ÖNERİ  tahmine dayalı; bakılır, gerekiyorsa düzeltilir, teslimi engellemez
Her bulgu yerini söyler: bölüm › alt bölüm › öğe ve metinden kısa bir alıntı (içerik betiğinde aratılabilir).
Çıkış kodu: KESİN yoksa 0, varsa 1.
"""
import argparse, json, os, re, sys

# ---------------------------------------------------------------- metin yardımcıları
TR = 'a-zçğıöşüâîû'
TRB = 'A-ZÇĞİÖŞÜÂÎÛ'


def duz(t):
    """İşaretlemesiz düz metin."""
    t = re.sub(r'<br\s*/?>', ' ', t or '')
    t = re.sub(r'<[^>]+>', '', t)
    t = t.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace(' ', ' ')
    return re.sub(r'\s+', ' ', t).strip()


def alinti(t, m=None, gen=70):
    """Eşleşmenin çevresinden (yoksa baştan) kısa alıntı."""
    if m is None:
        return t[:gen] + ('…' if len(t) > gen else '')
    a = max(0, m.start() - gen // 3)
    b = min(len(t), a + gen)
    return ('…' if a else '') + t[a:b] + ('…' if b < len(t) else '')


BIRIM = (r'(?:mm|cm|km|m|kg|g|N|kN|MN|Pa|kPa|MPa|GPa|bar|atm|W|kW|MW|hp|J|kJ|MJ|s|sn|dk|h|saat|K|°C|°F|°|L|lt|'
         r'ft|in|lbf|rad|mol|kmol|Hz|V|A|Ω|m/s|m²|m³|W/m·K|W/m²·K|W/m²|J/kg·K|kJ/kg·K|kJ/kg|kg/m³|kg/s|%)')

# ---------------------------------------------------------------- kurallar (KESİN)
# Yer bildiren şekil atfı. 'aşağıdaki şekilde' Türkçede 'şöyle' anlamında da kullanılır: o yüzden yalnız
# 'şekilde' biçimi ÖNERİ'dir; şekil/tablo/grafik adının diğer çekimleri KESİN'dir.
YON_KESIN = re.compile(r'(?i)\b(aşağıdaki|yukarıdaki|yandaki|alttaki|üstteki|önceki|sonraki)\s+'
                       r'(şekl(?:i|e|in|inde)|şekil(?:\b|den|deki)|tablo\w*|grafi\w*|çizim\w*|resim\w*|resm\w*|görsel\w*|diyagram\w*)')
YON_SEKILDE = re.compile(r'(?i)\b(aşağıdaki|yukarıdaki|yandaki)\s+şekilde\b')
# numarası olmadan 'şekilde görüldüğü/gösterildiği' (numaralı atıf 'Şekil 2.1'de görüldüğü' bunu tetiklemez)
SEKILDE_GORUL = re.compile(r"(?i)(?<![\w'’)])\s(şekilde|şekilden|grafikte|tabloda)\s+(görül|gösteril|izlen|bakıl)")

ONDALIK_BIRIM = re.compile(r'(?<![\w.,])(?<!Şekil )(?<!Tablo )(?<!Bölüm )(?<!Denklem )(?<!Örnek )(?<!Problem )'
                           r'(\d+\.\d+)\s?' + BIRIM + r'(?![\w' + TR + r'])')
ONDALIK_DENKLEM = re.compile(r'(?<![\w.(])(\d+\.\d+)(?![\d.)]|\s*[–-]\s*\d)')
SAYI_HUCRE = re.compile(r'^[−\-+≈~]?\s*\d+\.\d+$')

# Kesmesiz ek: 'Şekil 2.3te', '(3.27)den', '1313 °Cde'. Alt şekil harfi (3.13a) ek sayılmaz.
EK = r'(?:deki|daki|teki|taki|den|dan|ten|tan|de|da|te|ta|ye|ya|nin|nın|nun|nün|in|ın|un|ün|le|la)'
KESME_ATIF = re.compile(r'\b(Şekil|Tablo|Bölüm|Denklem|Örnek|Ek)\s+(\d+(?:[.\-]\d+)*[a-z]?(?:\([a-z]\))?)' + EK + r'\b')
KESME_PARANTEZ = re.compile(r'(\(\d+[.\-]\d+[a-z]?\))(e|a|' + EK[3:-1] + r')\b')
KESME_BIRIM = re.compile(r'(\d\s?°C)(' + EK[3:-1] + r')\b')

TEKRAR_BASLIK = re.compile(r'(?i)genel tekrar|kendini sına')

# ---------------------------------------------------------------- kurallar (ÖNERİ)
INGILIZCE_EK = re.compile(r'(tion|sion|ity|ness|ment|ance|ence|ing|ism|ure|ics|ivity|ance|ency|ogy|ysis)$')
PARANTEZ = re.compile(r'\(([A-Za-z][A-Za-z \-]{2,48})\)')
KISALTMA = re.compile(r'(?i)\b(vb|vs|ör|bkz|şek|denk|yy|sn|dk|no|prof|dr)\.')
CUMLE = re.compile(r'(?<!\d)[.!?](?=\s+[' + TRB + r'0-9"“(]|\s*$)')
TURKCE_KELIME = re.compile(r'(?i)^(ve|ile|bir|iki|tek|sabit|veya|ya|da|de|en|çok|az|her|bu|şu|o)$|(lu|lar|ler|dir|tir|mak|mek|ken|sel)$')
ETIKET_KELIME = re.compile(r'^[A-Za-z][A-Za-z\-]{3,}$')
ETIKET_HARIC = {'figure', 'fig', 'table', 'note', 'from', 'with', 'that', 'this', 'into', 'over', 'than', 'then', 'when',
                'where', 'which', 'each', 'both', 'between', 'through', 'along', 'line', 'lines', 'curve', 'curves'}


def ingilizce_mi(s):
    """Parantez içi İngilizce terim mi? (Türkçe harf yok; iki+ kelime ya da İngilizce son ek)."""
    if re.search('[çğıöşüÇĞİÖŞÜ]', s):
        return False
    kel = s.split()
    if any(TURKCE_KELIME.search(k) for k in kel):
        return False
    if len(kel) >= 2:
        return all(re.fullmatch(r'[A-Za-z\-]+', k) for k in kel) and any(len(k) > 3 for k in kel)
    return bool(INGILIZCE_EK.search(s.lower())) and len(s) > 5


# ---------------------------------------------------------------- iskeleti dolaş
def metinler(o):
    """Bir kayıt öğesinin içindeki (tür, metin) parçaları: 'nesir' denetlenen düz yazı, 'denklem' denklem metni."""
    t = o['t']
    if t in ('p', 'h1', 'h2', 'h3'):
        yield 'nesir', o['metin']
    elif t == 'bl':
        for m in o['maddeler']:
            yield 'nesir', m
    elif t == 'eq':
        yield 'denklem', o['metin']
    elif t == 'fig':
        yield 'nesir', o.get('cap') or ''
    elif t == 'box':
        for b in o['icerik']:
            if b['t'] == 'metin':
                yield 'nesir', b['metin']
            elif b['t'] == 'eq':
                yield 'denklem', b['metin']
            elif b['t'] == 'fig':
                yield 'nesir', b.get('cap') or ''
    elif t == 'cozum':
        yield 'nesir', o['soru']
        for v in o['verilen'] + o['kabuller']:
            yield 'nesir', v
        for a in o['adimlar']:
            yield 'nesir', a['metin']
            for e in a['denklemler']:
                yield 'denklem', e
        for s in o['sonuc']:
            yield 'denklem', s
        if o.get('yorum'):
            yield 'nesir', o['yorum']
        if o.get('sekil') and o['sekil'].get('t') == 'fig':
            yield 'nesir', o['sekil'].get('cap') or ''
    elif t == 'table':
        for r in o['satirlar'][1:]:
            for c in r:
                yield 'hucre', c
        if o.get('baslik'):
            yield 'nesir', o['baslik']


def ogeler_yerli(kayit):
    """(öğe, yer) — yer: 'Bölüm › Alt bölüm › öğe türü'."""
    h1 = h2 = None
    ad = {'p': 'paragraf', 'bl': 'madde listesi', 'eq': 'denklem', 'fig': 'şekil', 'box': 'kutu', 'cozum': 'çözümlü örnek',
          'table': 'tablo', 'h1': 'başlık', 'h2': 'başlık', 'h3': 'başlık', 'kapak': 'kapak', 'raw': 'öğe'}
    for o in kayit:
        if o['t'] == 'h1':
            h1, h2 = duz(o['metin']), None
        elif o['t'] == 'h2':
            h2 = duz(o['metin'])
        tur = ad.get(o['t'], o['t'])
        if o['t'] == 'box':
            tur = '%s kutusu' % o['tur']
        elif o['t'] == 'fig':
            tur = 'Şekil %s açıklaması' % o['no']
        yer = ' › '.join(x for x in ('kapak' if h1 is None else '“%s”' % h1, h2 and '“%s”' % h2, tur) if x)
        yield o, yer


def bolumler(kayit):
    """[(h1 metni, [öğeler])] — ilk h1'den önceki kapak hariç."""
    out = []
    for o in kayit:
        if o['t'] == 'h1':
            out.append((duz(o['metin']), []))
        elif out:
            out[-1][1].append(o)
    return out


def figler(kayit):
    """Notun bütün şekilleri (d.fig ve çözümlü örnekteki d.kf, kutu içindekiler dahil)."""
    for o in kayit:
        if o['t'] == 'fig':
            yield o
        elif o['t'] == 'cozum' and o.get('sekil') and o['sekil'].get('t') == 'fig':
            yield o['sekil']
        elif o['t'] == 'box':
            for b in o['icerik']:
                if b.get('t') == 'fig':
                    yield b


# ---------------------------------------------------------------- kaynaktaki şekil etiketleri
def kaynak_etiketleri(kaynak, figs):
    """{şekil no: [etiket kelimeleri]} — kesim alanındaki yazılı etiketler (başlık bloğu hariç)."""
    import pymupdf as fitz
    d = fitz.open(kaynak)
    bas = re.compile(r'^\s*(FIGURE|Figure|Fig\.|FIG\.|ŞEKİL|Şekil)\s*\d')
    out = {}
    for no, (pg, rc) in figs.items():
        if not 0 <= pg < d.page_count:
            continue
        p = d[pg]
        r = fitz.Rect(rc)
        kel = []
        for b in p.get_text('dict', clip=r)['blocks']:
            satirlar = [''.join(s['text'] for s in l['spans']).strip() for l in b.get('lines', [])]
            if satirlar and bas.match(satirlar[0]):
                continue   # şekil başlığı (kesimden zaten silinir)
            for s in satirlar:
                kel += s.split()
        out[no] = kel
    d.close()
    return out


def etiket_kelimeleri(kel):
    out = []
    for k in kel:
        k = k.strip('.,;:()[]{}"\'')
        if ETIKET_KELIME.match(k) and k.lower() not in ETIKET_HARIC and k.lower() not in (x.lower() for x in out):
            out.append(k)
    return out


# ---------------------------------------------------------------- denetim
def denetle(kayit, etiketler=None):
    """(kesin, oneri): her biri [(kural, yer, açıklama)]"""
    kesin, oneri = [], []
    K = lambda kural, yer, ne: kesin.append((kural, yer, ne))
    O = lambda kural, yer, ne: oneri.append((kural, yer, ne))

    # 1) metin kuralları
    tanitilan = {}   # İngilizce terim -> ilk tanıtıldığı yer
    for o, yer in ogeler_yerli(kayit):
        for tur, ham in metinler(o):
            t = duz(ham)
            if not t:
                continue
            if tur == 'nesir':
                for m in YON_KESIN.finditer(t):
                    K('yer-atfı', yer, '"%s" → şekle/tabloya numarasıyla atıf yap (Şekil n\'de …)' % alinti(t, m))
                for m in SEKILDE_GORUL.finditer(' ' + t):
                    K('yer-atfı', yer, '"%s" → hangi şekil? Numarasıyla yaz' % alinti(t, m))
                for m in YON_SEKILDE.finditer(t):
                    O('yer-atfı', yer, '"%s" → bir şekle işaret ediyorsa numarasıyla yaz; "şöyle" anlamındaysa sorun yok' % alinti(t, m))
                for m in ONDALIK_BIRIM.finditer(t):
                    K('ondalık', yer, '"%s" → ondalık ayırıcı virgül: %s' % (alinti(t, m), m.group(1).replace('.', ',')))
            if tur == 'denklem':
                for m in ONDALIK_DENKLEM.finditer(t):
                    K('ondalık', yer, 'denklemde "%s" → %s' % (alinti(t, m), m.group(1).replace('.', ',')))
            if tur == 'hucre' and SAYI_HUCRE.match(t):
                O('ondalık', yer, 'tablo hücresi "%s" → sayıysa virgülle yaz (bölüm/denklem numarasıysa sorun yok)' % t)
            if tur in ('nesir', 'hucre'):
                for rx in (KESME_ATIF, KESME_PARANTEZ, KESME_BIRIM):
                    for m in rx.finditer(t):
                        K('kesme', yer, '"%s" → ek kesmeyle ayrılır (ör. Şekil 2.3\'te, (3.27)\'den, 1313 °C\'de)' % alinti(t, m))
            if tur == 'nesir' and o['t'] not in ('h1', 'h2', 'h3'):
                for m in PARANTEZ.finditer(ham):
                    ing = m.group(1).strip()
                    if not ingilizce_mi(ing):
                        continue
                    once = ham[:m.start()].rstrip()
                    anahtar = ing.lower()
                    tanimda = o['t'] == 'box' and o.get('tur') == 'tanim'   # tanım kutusu terimi İngilizcesiyle yineler (USLUP)
                    if anahtar in tanitilan:
                        if tanimda or tanitilan[anahtar][1]:
                            continue
                        O('terim', yer, '"%s" İngilizcesiyle ikinci kez veriliyor (ilk: %s) → sonraki geçişlerde yalnız Türkçesi'
                          % (ing, tanitilan[anahtar][0]))
                        continue
                    tanitilan[anahtar] = (yer, tanimda)
                    if not once.endswith('</b>'):
                        O('terim', yer, '"%s" terimi kalın yazılmadan tanıtılmış → <b>Türkçe terim</b> (%s)' % (alinti(duz(once[-40:])), ing))
        if o['t'] == 'p':
            t = duz(o['metin'])
            n = len(CUMLE.findall(KISALTMA.sub('KISALTMA', t)))
            if n >= 6:
                O('paragraf', yer, '%d cümle → 2–4 cümlelik paragraflara böl: "%s"' % (n, alinti(t)))

    # 2) yapı kuralları
    bol = bolumler(kayit)
    if not any(TEKRAR_BASLIK.search(b) for b, _ in bol):
        K('not-sonu', 'not sonu', '"Genel Tekrar ve Kendini Sına" bölümü yok (tüm notun özeti + Kendini Sına soruları)')
    for baslik, ic in bol:
        yer = '“%s”' % baslik
        icerik = [o for o in ic if o['t'] != 'raw']
        if TEKRAR_BASLIK.search(baslik):
            if not any(o['t'] == 'box' and o['tur'] == 'ozet' for o in icerik):
                K('not-sonu', yer, 'tüm notun özeti (ozet kutusu, title=\'TÜM NOTUN ÖZETİ\') yok')
            if not any(o['t'] == 'bl' and len(o['maddeler']) >= 3 for o in icerik):
                K('not-sonu', yer, 'Kendini Sına soruları (en az 3 maddelik numaralı liste) yok')
            continue
        if not icerik:
            K('bölüm-girişi', yer, 'bölüm boş')
            continue
        if icerik[0]['t'] != 'p':
            K('bölüm-girişi', yer, 'bölüm giriş paragrafıyla açılmıyor (ilk öğe: %s) → 1–2 cümle: bu konu neden gerekli, öncekiyle bağı ne'
              % {'h2': 'alt başlık', 'h3': 'alt başlık', 'box': 'kutu', 'fig': 'şekil', 'eq': 'denklem', 'table': 'tablo',
                 'bl': 'madde listesi', 'cozum': 'çözümlü örnek'}.get(icerik[0]['t'], icerik[0]['t']))
        son = icerik[-1]
        if not (son['t'] == 'box' and son['tur'] == 'ozet'):
            var = any(o['t'] == 'box' and o['tur'] == 'ozet' for o in icerik)
            K('bölüm-özeti', yer, 'bölüm özet kutusuyla bitmiyor' + (' (özet var ama sonda değil)' if var else '')
              + ' → d.box(\'ozet\', [...], title=\'BÖLÜM n ÖZETİ\') bölümün son öğesi olur')

    # 3) şekil terimleri (kaynaktaki yazılı etiketlerle)
    for f in figler(kayit):
        if etiketler is None or f['no'] not in etiketler:
            continue
        kel = etiket_kelimeleri(etiketler[f['no']])
        terms = duz(f.get('terms') or '')
        if kel and not terms:
            K('şekil-terimi', 'Şekil %s' % f['no'], 'kitaptaki şekilde yazılı etiket var (%s) ama terim satırı yok → terms=\'English = Türkçe; …\''
              % ', '.join(kel[:6]))
        elif kel:
            eksik = [k for k in kel if k.lower() not in terms.lower()]
            if eksik:
                O('şekil-terimi', 'Şekil %s' % f['no'], 'şekildeki şu etiketler terim satırında yok: %s' % ', '.join(eksik[:10]))
    return kesin, oneri


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('work')
    ap.add_argument('--kaynak', help='kitap PDF: şekillerin yazılı etiketleri buradan okunur')
    a = ap.parse_args(argv)
    yol = os.path.join(a.work, 'kayit.json')
    if not os.path.exists(yol):
        print('kayit.json yok: %s — notu güncel notlib ile derle (d.make() yazar)' % a.work)
        return 1
    with open(yol, encoding='utf-8') as f:
        kayit = json.load(f)
    etiketler = None
    figs_yol = os.path.join(a.work, 'figs.json')
    if a.kaynak and os.path.exists(figs_yol):
        with open(figs_yol, encoding='utf-8') as f:
            etiketler = kaynak_etiketleri(a.kaynak, json.load(f))
    kesin, oneri = denetle(kayit, etiketler)
    print('ÜSLUP DENETİMİ: %d KESİN, %d ÖNERİ%s' % (len(kesin), len(oneri),
          '' if etiketler is not None else ' (şekil etiketleri denetlenmedi: --kaynak verilmedi)'))
    for kural, yer, ne in kesin:
        print('KESİN [%s] %s: %s' % (kural, yer, ne))
    for kural, yer, ne in oneri:
        print('ÖNERİ [%s] %s: %s' % (kural, yer, ne))
    if not kesin:
        print('ÜSLUP TAMAM: kesin kural ihlali yok')
    return 1 if kesin else 0


if __name__ == '__main__':
    sys.exit(main())
