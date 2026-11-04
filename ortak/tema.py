"""PDF renk teması: ana renk konudan konuya değişir, açık zeminli ve ferah bir görünüm verir.

Mor ve lacivert palette bilerek yoktur. Renk yalnız bu adlarla seçilir (rastgele hex kabul edilmez);
böylece hiçbir içerik betiği tek bir koyu renge geri dönemez.
"""
import hashlib

# Sıcak ve soğuk tonlar sırayla gelir, ardışık konular birbirinden ayrılır.
PALET = {
    'petrol': '#0F6E84',
    'kiremit': '#B5492A',
    'yesil': '#2C7A4B',
    'hardal': '#8F6508',
    'mavi': '#2A6FB0',
    'kirmizi': '#B03A3A',
    'turkuaz': '#0B7A75',
    'zeytin': '#5F7319',
}


def acik(hex_renk, oran=0.90):
    """Ana rengin beyazla karışmış açık tonu (başlık zemini, tablo satırı, özet kutusu)."""
    r, g, b = (int(hex_renk[i:i + 2], 16) for i in (1, 3, 5))
    return '#%02X%02X%02X' % tuple(round(c + (255 - c) * oran) for c in (r, g, b))


def _ad(renk):
    if renk not in PALET:
        raise ValueError('Bilinmeyen renk %r. Seçenekler: %s' % (renk, ', '.join(PALET)))
    return renk


class Tema:
    """renk verilirse belge tek renktir; verilmezse her konu sıradaki rengi alır.
    Başlangıç rengi başlıktan türetilir: farklı konuların PDF'leri farklı renkle açılır."""

    def __init__(self, baslik, renk=None):
        self._sira = list(PALET)
        self._sabit = _ad(renk) if renk else None
        self._i = int(hashlib.md5(baslik.encode('utf-8')).hexdigest(), 16) % len(self._sira)
        self._ilk = True

    def sonraki(self, renk=None):
        """Yeni konuya geçer. renk verilirse o renk kullanılır ve sıra oradan sürer."""
        if renk:
            self._i = self._sira.index(_ad(renk))
        elif not self._ilk:
            self._i = (self._i + 1) % len(self._sira)
        self._ilk = False
        return self.ana

    @property
    def ana(self):
        return PALET[self._sabit or self._sira[self._i]]

    @property
    def zemin(self):
        return acik(self.ana)
