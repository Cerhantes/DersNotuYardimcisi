"""Şekil atıf denetimi: belgede adı geçen her şeklin belgede gerçekten bulunduğunu denetler.

Kullanım:
    python sekil_atif.py <belge.pdf> [--haric <dosya>]

Şekil açıklaması (notlib biçimi) 'Şekil <no> – ...' diye başlar; bunlar belgedeki şekillerdir.
Metnin geri kalanındaki 'Şekil <no>' geçişleri atıftır ('Şekil 3-14(a)', 'Şekil 2.3'te', 'Şek. 4').

Çıktı:
    ANILAN AMA YOK: <no> (sayfa ...)   metinde anılıyor, belgede şekli yok  → şekli ekle ya da atfı kaldır
    VAR AMA ANILMAMIŞ: <no>            şekil var, metinde hiç anılmıyor     → bilgi; atıf eklenmesi önerilir
--haric dosyası: her satır '<no>  gerekçe' — bilerek konmayan şekiller (ör. kaynağın kapsam dışı şekli).
Çıkış kodu: ANILAN AMA YOK listesi boşsa 0, değilse 1.
"""
import argparse, re, sys
import pymupdf as fitz

NO = r'(?:[A-ZÇĞİÖŞÜ]-)?\d+(?:[.\-]\d+)?[a-z]?'
ACIKLAMA = re.compile(r'Şekil\s+(' + NO + r')\s+[–—-]\s')
ATIF = re.compile(r'(?:Şekil(?:ler|de|den|e|in)?|Şek\.)\s+(' + NO + r')')
ARDISIK = re.compile(r'^\s*(?:,|ve|ile|–|-)\s*(' + NO + r')')   # 'Şekil 3-55(a) ve 3-56' gibi listeler


def tara(pdf):
    """(şekiller {no: ilk sayfa}, atıflar {no: [sayfalar]})"""
    d = fitz.open(pdf)
    sekil, atif = {}, {}
    for i, p in enumerate(d, 1):
        t = re.sub(r'\s+', ' ', p.get_text())
        acik = set()
        for m in ACIKLAMA.finditer(t):
            sekil.setdefault(m.group(1), i)
            acik.add(m.start())
        for m in ATIF.finditer(t):
            if m.start() in acik:
                continue
            nos = [m.group(1)]
            kalan = t[m.end():]
            kalan = re.sub(r'^\([a-z]\)', '', kalan)
            while True:
                k = ARDISIK.match(kalan)
                if not k:
                    break
                nos.append(k.group(1))
                kalan = re.sub(r'^\([a-z]\)', '', kalan[k.end():])
            for n in nos:
                atif.setdefault(n, []).append(i)
    d.close()
    return sekil, atif


def denetle(pdf, haric=None):
    """(şekiller, anılan ama olmayanlar {no: [sayfalar]}, var ama anılmamışlar [no])"""
    sekil, atif = tara(pdf)
    var = lambda n: n in sekil or (n[-1].isalpha() and n[:-1] in sekil)   # 'Şekil 3-13a' → 3-13'ün (a) parçası
    yok = {n: s for n, s in atif.items() if not var(n) and n not in (haric or {}) and n[:-1] not in (haric or {})}
    anilan = set(atif) | {n[:-1] for n in atif if n[-1].isalpha()}
    anilmamis = sorted(n for n in sekil if n not in anilan)
    return sekil, yok, anilmamis


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf')
    ap.add_argument('--haric', help="her satır: '<no>  gerekçe'")
    a = ap.parse_args()
    haric = {}
    if a.haric:
        for satir in open(a.haric, encoding='utf-8'):
            if satir.strip() and not satir.startswith('#'):
                no, _, neden = satir.strip().partition(' ')
                haric[no] = neden.strip()
    sekil, yok, anilmamis = denetle(a.pdf, haric)
    print('Belgedeki şekil: %d · atıf yapılan farklı şekil: %d' % (len(sekil), len(tara(a.pdf)[1])))
    if yok:
        print('ANILAN AMA YOK: ' + '; '.join('%s (sayfa %s)' % (n, ', '.join(map(str, sorted(set(s))))) for n, s in sorted(yok.items())))
    else:
        print('ANILAN AMA YOK: — (anılan her şekil belgede var)')
    if anilmamis:
        print('VAR AMA ANILMAMIŞ (bilgi; metinde numarayla anılması önerilir): ' + ' '.join(anilmamis))
    for n, neden in sorted(haric.items()):
        print('HARİÇ: %s – %s' % (n, neden))
    return 1 if yok else 0


if __name__ == '__main__':
    sys.exit(main())
