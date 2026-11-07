"""Kırpık şekil denetimi: kesimin kenarına değen mürekkebi bulur.

python -W ignore sekil_kenar.py <fig klasörü | png ...> [--esik 140] [--en-az 3]

Bir kenarda en az --en-az piksel --esik değerinden koyuysa (0 siyah, 255 beyaz) o kenar raporlanır:
  KENAR: 3.42b: alt 12, ust 21      -> etiket, ok ya da çizgi kesimin dışında kalmış olabilir
  KENAR TEMİZ: 48 şekil             -> hiçbir şekil kenara değmiyor
Her KENAR satırının şeklini kaynağıyla karşılaştır: kesik yazı ya da çizgi varsa kesimi genişlet;
komşu yazıdan kalan iz varsa beyazlat. Çerçeveli şekil, tablo çizgisi, kenara kadar uzanan grafik
eksenleri doğal olarak değer; bunlar hata değildir. Küçük ölçekli temas sayfasında bu kesikler kolay kaçar.
"""
import argparse, glob, os, sys
from PIL import Image


def kenarlar(yol, esik=140, en_az=3):
    """{kenar: koyu piksel sayısı}; yalnız en_az ve üstü olanlar."""
    im = Image.open(yol).convert('L')
    w, h = im.size
    px = im.load()
    say = {'sol': sum(px[0, y] < esik for y in range(h)),
           'sag': sum(px[w - 1, y] < esik for y in range(h)),
           'ust': sum(px[x, 0] < esik for x in range(w)),
           'alt': sum(px[x, h - 1] < esik for x in range(w))}
    return {k: v for k, v in say.items() if v >= en_az}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('yollar', nargs='+')
    ap.add_argument('--esik', type=int, default=140)
    ap.add_argument('--en-az', dest='en_az', type=int, default=3)
    a = ap.parse_args()
    dosyalar = []
    for y in a.yollar:
        dosyalar += sorted(glob.glob(os.path.join(y, '*.png'))) if os.path.isdir(y) else [y]
    if not dosyalar:
        sys.exit('PNG bulunamadı: ' + ' '.join(a.yollar))
    bulunan = 0
    for f in dosyalar:
        k = kenarlar(f, a.esik, a.en_az)
        if k:
            bulunan += 1
            print('KENAR: %s: %s' % (os.path.splitext(os.path.basename(f))[0], ', '.join('%s %d' % kv for kv in k.items())))
    if not bulunan:
        print('KENAR TEMİZ: %d şekil' % len(dosyalar))


if __name__ == '__main__':
    main()
