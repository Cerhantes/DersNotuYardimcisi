"""Çözümlü soru kitapçığı PDF'ini <work>/sorular.json ve <work>/sonuc.json ile karşılaştırır.
Kullanım: python -W ignore denetim.py <pdf> <work>
Sorun yoksa "DENETİM TAMAM: <n> soru", çıkış 0. Varsa her satır "SORUN: ...", çıkış 1.
Bilgi satırları (hata değil): UZUN KART (bölünmüş kart: bakılmalı), CEVAP KARŞILAŞTIR (kaynaktaki cevap, çözümle karşılaştırılmalı).

sonuc.json'daki her değer kartta görünmelidir: hesap.py'de yalnız kartta yazılacak sonuçlar kaydedilir.
"""
import json, os, re, sys
import pymupdf as fitz

BOY_NO, BOY_KONU, BOY_UST = 11.5, 8.8, 8.5
_ATIF = re.compile(r'(?:Şekil|Şek\.|Fig\.?|Figure)\s*\d+[.\-]\d+|\b[Şş]ekil(?:de|den|deki|e|i)\b')
_BANT = re.compile(r'^Soru (.+?)( \(devam\))?$')


def _duz(t):
    return re.sub(r'\s+', ' ', t.replace('\xa0', ' ')).strip()


def _satirlar(p):
    cik = []
    for b in p.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            yazi = ''.join(s['text'] for s in l['spans'])
            if yazi.strip():
                s = max(l['spans'], key=lambda x: len(x['text']))
                cik.append({'t': _duz(yazi), 'y': l['bbox'][1], 'boy': s['size'], 'kalin': 'bold' in s['font'].lower()})
    return sorted(cik, key=lambda x: x['y'])


def kartlar(pdf):
    """Belge sırasıyla {no: {'konu', 'metin', 'gorsel', 'devam'}}."""
    d = fitz.open(pdf)
    sonuc = {}
    for p in d:
        sat = _satirlar(p)
        bant = []
        for l in sat:
            m = _BANT.match(l['t'])
            if m and l['kalin'] and abs(l['boy'] - BOY_NO) < 0.2:
                bant.append((l['y'], m.group(1), bool(m.group(2))))
        konu_sat = [l for l in sat if abs(l['boy'] - BOY_KONU) < 0.15]
        for i, (y, no, devam) in enumerate(bant):
            alt = bant[i + 1][0] if i + 1 < len(bant) else p.rect.height + 1
            konu = [l['t'] for l in konu_sat if abs(l['y'] - y) < 30]
            metin = [l['t'] for l in sat if y < l['y'] < alt
                     and abs(l['boy'] - BOY_KONU) >= 0.15 and abs(l['boy'] - BOY_UST) >= 0.15]
            gorsel = sum(1 for g in p.get_image_info() if y < g['bbox'][1] < alt)
            k = sonuc.setdefault(no, {'konu': '', 'metin': '', 'gorsel': 0, 'devam': False})
            if not devam:
                k['konu'] = _duz(' '.join(konu))
            k['metin'] = _duz(k['metin'] + ' ' + ' '.join(metin))
            k['gorsel'] += gorsel
            k['devam'] = k['devam'] or devam
    return sonuc, ' '.join(_duz(p.get_text()) for p in d)


def rapor(pdf, work):
    """(sorunlar, bilgi) listeleri."""
    with open(os.path.join(work, 'sorular.json'), encoding='utf-8') as f:
        js = json.load(f)
    yol = os.path.join(work, 'sonuc.json')
    hesap = {}
    if os.path.exists(yol):
        with open(yol, encoding='utf-8') as f:
            hesap = json.load(f)
    pdf_kart, tum = kartlar(pdf)
    sira = list(pdf_kart)
    sorun, bilgi = [], []
    istenen = {s['no'] for s in js['sorular']}
    for no in sira:
        if no not in istenen:
            sorun.append("Soru %s PDF'te var, sorular.json'da yok" % no)
    for s in js['sorular']:
        no = s['no']
        if no not in pdf_kart:
            sorun.append("Soru %s PDF'te yok" % no)
            continue
        k = pdf_kart[no]
        konular = [_duz(x) for x in s['konular']]
        if len(konular) > 1:
            if not k['konu'].startswith('KARMA ·'):
                sorun.append('Soru %s: birden çok konu var, bant KARMA değil: %s' % (no, k['konu']))
            elif k['konu'] != 'KARMA · ' + ' + '.join(konular):
                sorun.append('Soru %s: bantta konu uyuşmuyor: %s' % (no, k['konu']))
        elif k['konu'] != konular[0]:
            sorun.append('Soru %s: bantta konu uyuşmuyor: %s' % (no, k['konu']))
        gerekli = s.get('sekiller', [])
        for num in gerekli:
            if 'Şekil %s' % num not in k['metin']:
                sorun.append('Soru %s: Şekil %s kartta yok' % (no, num))
        if k['gorsel'] < len(gerekli):
            sorun.append('Soru %s: %d şekil gerekli, kartta %d görsel var' % (no, len(gerekli), k['gorsel']))
        for num in s.get('tablolar', []):
            if 'Tablo %s' % num not in k['metin']:
                sorun.append('Soru %s: Tablo %s kartta yok' % (no, num))
        if k['gorsel'] == 0:
            m = _ATIF.search(k['metin'])
            if m:
                sorun.append('Soru %s: şekilsiz atıf: "%s"' % (no, m.group(0)))
        if s.get('sayisal'):
            degerler = hesap.get(no, {})
            if not degerler:
                sorun.append('Soru %s: sayısal ama hesap.py kaydı yok' % no)
            for ad, deger in degerler.items():
                if _duz(deger) not in k['metin']:
                    sorun.append('Soru %s: hesap sonucu kartta yok: %s = %s' % (no, ad, deger))
        bagli = s.get('bagli')
        if bagli and bagli in pdf_kart and abs(sira.index(no) - sira.index(bagli)) != 1:
            sorun.append('Soru %s: bağlı olduğu Soru %s ile komşu değil' % (no, bagli))
        if k['devam']:
            bilgi.append('UZUN KART: %s' % no)
        if s.get('cevap'):
            bilgi.append('CEVAP KARŞILAŞTIR: %s %s' % (no, s['cevap']))
    for c in js.get('cikarilan', []):
        if not re.search(r'(?<![\d.])%s(?![\d])' % re.escape(c['no']), tum):
            sorun.append('Çıkarılan soru %s kapsam notunda anılmıyor' % c['no'])
    return sorun, bilgi


def denetle(pdf, work):
    return rapor(pdf, work)[0]


def main():
    pdf, work = sys.argv[1:3]
    sorun, bilgi = rapor(pdf, work)
    for b in bilgi:
        print(b)
    for s in sorun:
        print('SORUN: ' + s)
    if sorun:
        sys.exit(1)
    with open(os.path.join(work, 'sorular.json'), encoding='utf-8') as f:
        print('DENETİM TAMAM: %d soru' % len(json.load(f)['sorular']))


if __name__ == '__main__':
    main()
