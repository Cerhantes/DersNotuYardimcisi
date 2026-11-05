"""Sayısal sonuçların kaydı. hesap.py her sonucu burada hesaplayıp yazar, içerik betiği R(no, ad) ile okur.
Böylece karttaki sayı hesapla aynıdır. reportlab gerektirmez."""
import json, os


class Hesap:
    def __init__(self, work):
        os.makedirs(work, exist_ok=True)
        self._yol = os.path.join(work, 'sonuc.json')
        self._veri = {}
        if os.path.exists(self._yol):
            with open(self._yol, encoding='utf-8') as f:
                self._veri = json.load(f)

    def kaydet(self, no, ad, deger, birim='', ondalik=2):
        """Değeri virgüllü biçimde sonuc.json'a yazar ve döndürür; ör. kaydet('1.1', 'q', 500.123, 'W', 1) -> '500,1 W'."""
        yazi = ('%.*f' % (ondalik, deger)).replace('.', ',')
        if birim:
            yazi += ' ' + birim
        self._veri.setdefault(no, {})[ad] = yazi
        with open(self._yol, 'w', encoding='utf-8') as f:
            json.dump(self._veri, f, ensure_ascii=False, indent=1)
        return yazi
