"""notlib dizgi kuralları: alt simge satıra çarpmaz, büyük harfin noktası harfin üstünde kalır."""
import filecmp, os, sys, tempfile, unittest
import pymupdf as fitz

KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(KOK, 'skills', 'ders-notu', 'scripts'))
import notlib
from reportlab.platypus import SimpleDocTemplate

NOKTA = '̇'


def spanlar(metin, stil='eq'):
    with tempfile.TemporaryDirectory() as k:
        yol = os.path.join(k, 't.pdf')
        SimpleDocTemplate(yol).build([notlib.Paragraph(metin, notlib.ss[stil])])
        d = fitz.open(yol)
        s = [x for b in d[0].get_text('dict')['blocks'] for l in b.get('lines', []) for x in l['spans']]
        d.close()
    return s


def harfin_yazi_tipi(s, harf):
    return next(x['font'] for x in s if harf in x['text'])


class AltSimge(unittest.TestCase):
    def test_alt_simge_yazi_boyutunun_uçte_birinden_az_iner(self):
        s = spanlar('c<sub>p</sub> x')
        taban, alt = s[0], s[1]
        self.assertLess(alt['origin'][1] - taban['origin'][1], taban['size'] / 3)

    def test_ust_simge_yarim_boydan_az_cikar(self):
        s = spanlar('T<super>4</super> x')
        taban, ust = s[0], s[1]
        self.assertLess(taban['origin'][1] - ust['origin'][1], taban['size'] / 2)


class BuyukHarfNoktasi(unittest.TestCase):
    def test_hazir_karsiligi_olmayan_buyuk_harf_metin_yazi_tipine_gecer(self):
        for harf in 'QV':
            s = spanlar(harf + NOKTA + ' = 5')
            self.assertIn('Carlito', harfin_yazi_tipi(s, harf), harf)

    def test_kalin_metinde_de_gecer(self):
        s = spanlar('<b>Q' + NOKTA + ' = 5</b>', 'body')
        self.assertIn('Carlito-Bold', harfin_yazi_tipi(s, 'Q'))

    def test_egik_metinde_de_gecer(self):
        s = spanlar('<i>V' + NOKTA + ' = 5</i>', 'body')
        self.assertIn('Carlito-Italic', harfin_yazi_tipi(s, 'V'))

    def test_kalin_stilde_de_gecer(self):
        s = spanlar('Q' + NOKTA + ' = 5', 'boxt')
        self.assertIn('Carlito-Bold', harfin_yazi_tipi(s, 'Q'))

    def test_hazir_karsiligi_olan_harf_tek_karaktere_iner(self):
        s = spanlar('E' + NOKTA + ' = 5')
        metin = ''.join(x['text'] for x in s)
        self.assertIn('Ė', metin)
        self.assertNotIn(NOKTA, metin)

    def test_kucuk_harf_ve_diger_metin_degismez(self):
        s = spanlar('q' + NOKTA + ' = 5')
        self.assertIn('DejaVu', harfin_yazi_tipi(s, 'q'))
        self.assertIn('DejaVu', harfin_yazi_tipi(spanlar('Q = 5'), 'Q'))


class Kopyalar(unittest.TestCase):
    def test_iki_notlib_kopyasi_ayni(self):
        a, b = (os.path.join(KOK, 'skills', k, 'scripts', 'notlib.py') for k in ('ders-notu', 'tekrar-notu'))
        self.assertTrue(filecmp.cmp(a, b, shallow=False))


if __name__ == '__main__':
    unittest.main()
