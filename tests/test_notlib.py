"""notlib dizgi kuralları: alt simge satıra çarpmaz, büyük harfin noktası harfin üstünde kalır."""
import filecmp, os, shutil, sys, tempfile, unittest
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


class Bolunme(unittest.TestCase):
    def setUp(self):
        self.k = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, self.k)
        os.makedirs(os.path.join(self.k, 'fig'))
        with open(os.path.join(self.k, 'figs.json'), 'w') as f:
            f.write('{}')
        self.pdf = os.path.join(self.k, 'o.pdf')
        self.d = notlib.Doc(self.pdf, 'T', 'A', 'B', self.k, 'K')
        self.d.cover(['x'], ['y'])

    def doldur(self, cumle=38):
        for i in range(cumle):
            self.d.p('Dolgu satırı %d' % i)

    def sayfalar(self, *metinler):
        self.d.make()
        d = fitz.open(self.pdf)
        sonuc = [[i for i, p in enumerate(d) if m in p.get_text()] for m in metinler]
        d.close()
        return sonuc

    def sona_getir(self, kur):
        """Son satır sayfaya sığmayana dek dolgu ekleyerek kuralı sayfa sınırında sına."""
        for n in range(20, 60):
            self.setUp()
            self.doldur(n)
            kur()
            self.d.make()
            d = fitz.open(self.pdf)
            sayfa = [i for i, p in enumerate(d) if 'ILK' in p.get_text()], [i for i, p in enumerate(d) if 'SON' in p.get_text()]
            d.close()
            yield sayfa

    def test_cok_satirli_denklem_bolunmez(self):
        for ilk, son in self.sona_getir(lambda: (self.d.eq('ILK = a + b', ''), self.d.eq('+ SON', '(1.1)'))):
            self.assertEqual(ilk, son)

    def test_denklemi_tanitan_cumle_denklemden_ayrilmaz(self):
        for ilk, son in self.sona_getir(lambda: (self.d.p('ILK şöyledir:'), self.d.eq('SON = 1', '(1.1)'))):
            self.assertEqual(ilk, son)

    def test_grup_tek_parca_kalir(self):
        def kur():
            g = self.d.grup_bas()
            self.d.eq('ILK = 1', '(1.1)'); self.d.eq('orta = 2', '(1.2)'); self.d.eq('SON = 3', '(1.3)')
            self.d.grup_son(g)
        for ilk, son in self.sona_getir(kur):
            self.assertEqual(ilk, son)

    def test_numarasiz_ara_adim_sonraki_denklemden_ayrilmaz(self):
        for ilk, son in self.sona_getir(lambda: (self.d.eq('ILK = 1', ''), self.d.eq('SON = 2', '(1.1)'))):
            self.assertEqual(ilk, son)

    def test_cok_uzun_zincir_bolunebilir(self):
        self.doldur(3)
        for i in range(notlib.ZINCIR + 3):
            self.d.eq('a%d = 1' % i, '')
        self.assertGreater(sum(isinstance(f, notlib.KeepTogether) for f in self.d.story), 1)

    def test_harfli_denklemler_birlikte_kalir(self):
        for ilk, son in self.sona_getir(lambda: (self.d.eq('ILK = 1', '(2.18a)'), self.d.eq('b = 2', '(2.18b)'), self.d.eq('SON = 3', '(2.18c)'))):
            self.assertEqual(ilk, son)

    def test_grup_giris_cumlesini_de_alir(self):
        def kur():
            self.d.p('ILK şöyledir:')
            g = self.d.grup_bas()
            self.d.eq('a = 1', '(1.1)'); self.d.eq('SON = 2', '(1.2)')
            self.d.grup_son(g)
        for ilk, son in self.sona_getir(kur):
            self.assertEqual(ilk, son)

    def test_grup_ara_adimdan_sonra_baslasa_da_tam_kalir(self):
        def kur():
            self.d.eq('once = 0', '')
            g = self.d.grup_bas()
            self.d.eq('ILK = 1', '(1.1)'); self.d.eq('orta = 2', '(1.2)'); self.d.eq('SON = 3', '(1.3)')
            self.d.grup_son(g)
        for ilk, son in self.sona_getir(kur):
            self.assertEqual(ilk, son)

    def test_grup_yeri_varken_sayfa_atlatmaz(self):
        self.doldur(3)
        g = self.d.grup_bas()
        self.d.eq('ILK = 1', ''); self.d.eq('+ 2', '(1.1)'); self.d.eq('SON = 3', '(1.2)')
        self.d.grup_son(g)
        self.d.make()
        d = fitz.open(self.pdf)
        ilk_dolgu = next(i for i, p in enumerate(d) if 'Dolgu' in p.get_text())
        son = next(i for i, p in enumerate(d) if 'SON' in p.get_text())
        d.close()
        self.assertEqual(ilk_dolgu, son)

    def test_ayri_denklemler_birbirine_baglanmaz(self):
        self.doldur(5)
        self.d.eq('a = 1', '(1.1)'); self.d.eq('b = 2', '(1.2)')
        self.assertFalse(isinstance(self.d.story[-1], notlib.KeepTogether))

    def cozum(self, adim=3):
        self.d.cozum('ÇÖZÜMLÜ ÖRNEK 1.1 – ORNEKBASLIK', 'SORUMETNI', None, ('VERILENLER', 'ISTENENLER'), ['KABULBIR'],
                     [('ADIM%d açıklaması:' % i, ['x = %d' % i, ('y = %d' % i, '(1.%d)' % i)]) for i in range(1, adim + 1)],
                     ['SONUCSATIRI'], yorum='YORUMCUMLESI')

    def test_cozum_bolumleri_sirayla(self):
        self.cozum()
        self.d.make()
        t = ' '.join(fitz.open(self.pdf)[-1].get_text().split())
        sira = ['ORNEKBASLIK', 'SORU', 'SORUMETNI', 'Verilen: VERILENLER', 'İstenen: ISTENENLER', 'KABULLER', 'KABULBIR',
                'ÇÖZÜM 1) ADIM1', '2) ADIM2', 'SONUÇ', 'SONUCSATIRI', 'Yorum: YORUMCUMLESI']
        yer = [t.index(s) for s in sira]
        self.assertEqual(yer, sorted(yer))

    def test_uzun_cozum_adim_sinirinda_bolunur(self):
        self.doldur(30)
        self.cozum(adim=30)
        self.d.make()
        d = fitz.open(self.pdf)
        sayfa = lambda m: [i for i, p in enumerate(d) if m in p.get_text()]
        self.assertGreater(len(set(sayfa('ADIM'))), 1)                     # kutu sayfaya bölündü
        self.assertEqual(sayfa('ORNEKBASLIK'), sayfa('SORUMETNI'))         # başlık ve soru birlikte
        for i in range(1, 31):                                             # adım ve denklemleri ayrılmaz
            self.assertEqual(sayfa('ADIM%d ' % i), sayfa('(1.%d)' % i), i)


class Kopyalar(unittest.TestCase):
    def test_iki_notlib_kopyasi_ayni(self):
        a, b = (os.path.join(KOK, 'skills', k, 'scripts', 'notlib.py') for k in ('ders-notu', 'tekrar-notu'))
        self.assertTrue(filecmp.cmp(a, b, shallow=False))


if __name__ == '__main__':
    unittest.main()
