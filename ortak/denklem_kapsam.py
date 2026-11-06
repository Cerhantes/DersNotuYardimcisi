"""Kaynaktaki her numaralı denklem belgede gösterilmiş mi? Ara adımlar dahil hiçbiri atlanamaz.

python -W ignore denklem_kapsam.py <kaynak.pdf> <belge.pdf> --from <ilk> --to <son> [--disarida <dosya>]

Belgedeki durumlar:
  gösterilmiş     denklem yazılı, numarası satır sonunda ya da kendi satırında
  YALNIZ ANILMIŞ  numara metin içinde geçiyor, denklemin kendisi gösterilmemiş ('(2.18a–c) yerleştirilir')
  YOK             numara hiç geçmiyor
--disarida: kapsam dışı bırakılanlar, her satırda gerekçesiyle: '3.9: kullanıcı bu alt bölümü çıkardı'
            ya da aralık: '3.109–3.133: nano ölçek, ders dışı'. Gerekçesiz satır geçersizdir.
Çıkış kodu: 0 tamam, 1 eksik var, 2 kaynakta numaralı denklem bulunamadı (slaytta denklemler görsel olabilir;
bu durumda araç güvence vermez, kaynak gözle karşılaştırılır).
"""
import argparse, re, sys
import pymupdf

NUMARA = r'\d+\.\d+[a-z]?(?:\s*[–-]\s*(?:\d+\.)?\d*[a-z]?)?'
AYRI = re.compile(r'^\(\s*(%s)\s*\)$' % NUMARA)
SATIR_SONU = re.compile(r'\(\s*(%s)\s*\)$' % NUMARA)
HERHANGI = re.compile(r'\(\s*(%s)\s*\)' % NUMARA)
MATEMATIK = re.compile(r'[=≈≡≤≥<>∂∫]')


def _ac(s):
    """'2.18a–c' -> 2.18a, 2.18b, 2.18c; '6.16–6.18' ve '1.1–2' -> tek tek."""
    m = re.fullmatch(r'(\d+)\.(\d+)([a-z]?)(?:\s*[–-]\s*(?:(\d+)\.)?(\d*)([a-z]?))?', s.strip())
    if not m:
        return []
    bol, n, h, bol2, n2, h2 = m.groups()
    if h and h2 and not n2:
        return ['%s.%s%s' % (bol, n, chr(c)) for c in range(ord(h), ord(h2) + 1)]
    if n2 and (bol2 in (None, bol)) and not h and not h2 and int(n2) >= int(n):
        return ['%s.%d' % (bol, x) for x in range(int(n), int(n2) + 1)]
    return ['%s.%s%s' % (bol, n, h)]


def _satirlar(yol, ilk=1, son=10 ** 6):
    d = pymupdf.open(yol)
    for i, p in enumerate(d):
        if ilk <= i + 1 <= son:
            for s in p.get_text().split('\n'):
                s = ' '.join(s.split())
                if s:
                    yield s
    d.close()


def _gosterilen(s):
    """Satırda gösterilmiş denklemin numarası; yoksa None."""
    m = AYRI.match(s)
    if m:
        return m.group(1)
    m = SATIR_SONU.search(s)
    return m.group(1) if m and MATEMATIK.search(s) else None


def kaynak_numaralari(yol, ilk=1, son=10 ** 6):
    out = set()
    for s in _satirlar(yol, ilk, son):
        g = _gosterilen(s)
        if g:
            out.update(_ac(g))
    return out


def not_numaralari(yol):
    gosterilen, anilan = set(), set()
    for s in _satirlar(yol):
        g = _gosterilen(s)
        if g:
            gosterilen.update(_ac(g))
        for m in HERHANGI.finditer(s):
            if m.group(1) != g:
                anilan.update(_ac(m.group(1)))
    return gosterilen, anilan - gosterilen


def _disarida(yol):
    gerekce, gecersiz = {}, []
    with open(yol, encoding='utf-8') as f:
        for satir in f:
            satir = satir.strip()
            if not satir:
                continue
            bas, _, neden = satir.partition(':')
            if not neden.strip():
                gecersiz.append(satir)
                continue
            for n in _ac(bas):
                gerekce[n] = neden.strip()
    return gerekce, gecersiz


def _sira(n):
    return [int(x) for x in re.findall(r'\d+', n)] + [n]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('kaynak'); ap.add_argument('belge')
    ap.add_argument('--from', dest='ilk', type=int, default=1)
    ap.add_argument('--to', dest='son', type=int, default=10 ** 6)
    ap.add_argument('--disarida')
    a = ap.parse_args(argv)
    kaynak = kaynak_numaralari(a.kaynak, a.ilk, a.son)
    if not kaynak:
        print('UYARI: kaynakta numaralı denklem bulunamadı. Denklemler görsel olabilir; kaynağı gözle karşılaştır.')
        return 2
    gosterilen, anilan = not_numaralari(a.belge)
    gerekce, gecersiz = _disarida(a.disarida) if a.disarida else ({}, [])
    kalan = kaynak - gosterilen
    disari = {n: gerekce[n] for n in kalan if n in gerekce}
    kalan -= set(disari)
    yalniz = sorted(kalan & anilan, key=_sira)
    yok = sorted(kalan - anilan, key=_sira)
    print('Kaynakta %d numaralı denklem; gösterilen %d, kapsam dışı %d' % (len(kaynak), len(kaynak & gosterilen), len(disari)))
    if yok:
        print('YOK: ' + ', '.join(yok))
    if yalniz:
        print('YALNIZ ANILMIŞ (denklemi de göster): ' + ', '.join(yalniz))
    for s in gecersiz:
        print('GEREKÇESİZ dışlama, geçersiz: ' + s)
    for n in sorted(disari, key=_sira):
        print('Kapsam dışı %s: %s' % (n, disari[n]))
    if yok or yalniz or gecersiz:
        return 1
    print('DENKLEM KAPSAMI TAMAM')
    return 0


if __name__ == '__main__':
    sys.exit(main())
