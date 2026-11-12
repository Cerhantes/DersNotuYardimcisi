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


class Baglama(unittest.TestCase):
    B = ' '

    def test_numara_birim_ve_isaret_baglanir(self):
        self.assertEqual(notlib._baglar('Bölüm 7 ve Şekil 6.13'), 'Bölüm%s7 ve Şekil%s6.13' % (self.B, self.B))
        self.assertEqual(notlib._baglar('L = 4,1 m'), 'L%s=%s4,1%sm' % (self.B, self.B, self.B))
        self.assertEqual(notlib._baglar('1) Keskin'), '1)%sKeskin' % self.B)

    def test_isaretten_once_gelmeyen_tek_harf_baglanmaz(self):
        for t in ('a ve b', 'x ile y artar', 'o zaman'):
            self.assertEqual(notlib._baglar(t), t)

    def test_etiket_icine_dokunulmaz(self):
        self.assertEqual(notlib._baglar('<font name="Math">x</font>'), '<font name="Math">x</font>')


class SekilBoslugu(unittest.TestCase):
    """Şekil sayfaya sığmayınca sayfanın kalanı boş kalmasın."""

    def kur(self, dolgu, yukseklik, baslik=False, genislik=300, ek=''):
        self.k = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, self.k)
        os.makedirs(os.path.join(self.k, 'fig'))
        fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 40, 40), 0).save(os.path.join(self.k, 'fig', '1.1.png'))
        with open(os.path.join(self.k, 'figs.json'), 'w') as f:
            f.write('{"1.1": [1, [0, 0, %d, %d]]}' % (genislik, yukseklik))
        self.pdf = os.path.join(self.k, 'o.pdf')
        d = notlib.Doc(self.pdf, 'T', 'A', 'B', self.k, 'K')
        d.cover(['x'], ['y'])
        for i in range(dolgu):
            d.p('Dolgu satırı %d' % i)
        if baslik:
            d.h3('ARABASLIK')
        d.fig('1.1', 'SEKILALTI ' + ek, maxh=1000)
        for i in range(6):
            d.p('SONRAKI%d metni.' % i)
        d.make()
        doc = fitz.open(self.pdf)
        sayfa = lambda m: [i for i, p in enumerate(doc) if m in p.get_text()][0]
        self.s = {m: sayfa(m) for m in ('Dolgu satırı %d' % (dolgu - 1), 'SEKILALTI', 'SONRAKI0', 'SONRAKI5')}
        self.s['son'] = self.s.pop('Dolgu satırı %d' % (dolgu - 1))
        sp = doc[self.s['SEKILALTI']]
        self.resimler = [r['bbox'] for r in sp.get_image_info()]
        self.aciklama = next(b for b in sp.get_text('blocks') if 'SEKILALTI' in b[4])
        doc.close()

    def yanda_mi(self):
        r, a = self.resimler[0], self.aciklama
        return a[0] >= r[2] - 1 and a[1] < r[3]

    UZUN = 'kelime ' * 70   # dar yan sütunda şeklin boyunu aşar, altta ise daha çok yer tutar

    def test_dar_sekilde_aciklama_yanda(self):
        self.kur(dolgu=3, yukseklik=300)
        self.assertTrue(self.yanda_mi())

    def test_genis_sekilde_aciklama_altta(self):
        self.kur(dolgu=3, yukseklik=300, genislik=480)
        self.assertFalse(self.yanda_mi())

    def test_sekilden_uzun_aciklama_altta(self):
        self.kur(dolgu=3, yukseklik=150, ek=self.UZUN)
        self.assertFalse(self.yanda_mi())

    def test_sigmayan_sekilde_alttaki_aciklama_yana_alinir(self):
        yana = 0
        for dolgu in range(14, 40):
            self.kur(dolgu, yukseklik=150, ek=self.UZUN)
            if self.yanda_mi():
                yana += 1
                self.assertEqual(self.s['son'], self.s['SEKILALTI'], dolgu)   # yana alınca aynı sayfada kaldı
        self.assertGreater(yana, 0)

    def test_az_farkla_sigmayan_genis_sekil_kucultulur(self):
        tam = 310 * 0.92                                # fig(): h = (300 + 10) × 0,92; genişlik 451 pt, yanda yer yok
        kucultulen = 0
        for dolgu in range(14, 34):
            self.kur(dolgu, yukseklik=300, genislik=480)
            self.assertFalse(self.yanda_mi())
            if self.s['son'] != self.s['SEKILALTI']:
                continue
            h = self.resimler[0][3] - self.resimler[0][1]
            self.assertGreaterEqual(h, tam * notlib.Doc.SEKIL_MIN_OLCEK - 1, dolgu)
            kucultulen += h < tam - 1
        self.assertGreater(kucultulen, 0)               # sınırda en az bir kez küçültülüp aynı sayfada kaldı

    def test_cok_buyuk_sekilde_sonraki_metin_bosluga_akar(self):
        self.kur(dolgu=20, yukseklik=560)
        self.assertEqual(self.s['son'], self.s['SONRAKI0'])     # metin boşluğu doldurdu
        self.assertEqual(self.s['SEKILALTI'], self.s['son'] + 1)

    def test_basligi_olan_sekilde_metin_one_gecmez(self):
        self.kur(dolgu=20, yukseklik=560, baslik=True)
        self.assertGreater(self.s['SONRAKI0'], self.s['son'])
        self.assertGreaterEqual(self.s['SONRAKI0'], self.s['SEKILALTI'])


class DenklemBoyutu(unittest.TestCase):
    """Sığmayan denklem önce küçültülür (en çok EQ_MIN_ORAN), ancak yine sığmazsa uyarılır."""

    def setUp(self):
        self.k = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, self.k)
        os.makedirs(os.path.join(self.k, 'fig'))
        with open(os.path.join(self.k, 'figs.json'), 'w') as f:
            f.write('{}')
        self.d = notlib.Doc(os.path.join(self.k, 'o.pdf'), 'T', 'A', 'B', self.k, 'K')
        self.w = notlib.FW - 2 * 2.2 * notlib.cm - 12

    def test_sigan_denklem_kuculmez(self):
        satirlar, oran = self.d._denklem('x = a + b', notlib.ss['eq'], self.w, '')
        self.assertEqual((satirlar, oran), (['x = a + b'], 1.0))
        self.assertEqual(self.d._eq_kucuk, [])

    def test_biraz_uzun_denklem_kuculup_tek_satirda_kalir(self):
        t = 'Δ(s) = (m<sub>1</sub>s² + bs + k<sub>1</sub> + k<sub>2</sub>)(m<sub>2</sub>s² + bs + k<sub>2</sub> + k<sub>3</sub>) − (bs + k<sub>2</sub>)²'
        self.assertGreater(self.d._satir(notlib.Paragraph(t, notlib.ss['eq']), self.w), 1)
        satirlar, oran = self.d._denklem(t, notlib.ss['eq'], self.w, '')
        self.assertEqual(len(satirlar), 1)
        self.assertTrue(notlib.EQ_MIN_ORAN <= oran < 1)

    def test_bilesik_denklem_virgulden_bolunur(self):
        t = ('E<sub>i</sub> = Z<sub>1</sub>I + Z<sub>2</sub>I<sub>1</sub> = [Z<sub>1</sub> + Z<sub>2</sub>(Z<sub>3</sub> + Z<sub>4</sub>)/'
             '(Z<sub>2</sub> + Z<sub>3</sub> + Z<sub>4</sub>)] I,&nbsp;&nbsp; E<sub>o</sub> = Z<sub>4</sub>I<sub>2</sub> = '
             'Z<sub>2</sub>Z<sub>4</sub>I/(Z<sub>2</sub> + Z<sub>3</sub> + Z<sub>4</sub>)')
        satirlar, oran = self.d._denklem(t, notlib.ss['eq'], self.w, '')
        self.assertEqual(len(satirlar), 2)
        self.assertTrue(satirlar[0].endswith('I,'))
        self.assertTrue(notlib._duz(satirlar[1]).startswith('Eo'))
        self.assertGreaterEqual(oran, notlib.EQ_BOLUNMUS_ORAN)

    def test_esitlikten_bolunur_tek_terim_dusmez(self):
        t = 'X(s) = [m x(0)s + m ẋ(0) + b x(0)]/(ms² + bs + k) = (0,1s + 0,35)/(s² + 3s + 2)'
        satirlar, _ = self.d._denklem(t, notlib.ss['eq'], self.w, '')
        self.assertEqual(len(satirlar), 2)
        self.assertTrue(satirlar[1].startswith('= '))
        uz = [len(notlib._duz(x)) for x in satirlar]
        self.assertGreaterEqual(min(uz), 0.25 * sum(uz))

    def test_parantez_icinden_bolunmez_uyarir(self):
        import io, contextlib
        t = 'f(x) = [' + ' + '.join('a<sub>%d</sub>x' % i for i in range(40)) + ']'
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            satirlar, oran = self.d._denklem(t, notlib.ss['eq'], self.w, '(9.9)')
        self.assertEqual(len(satirlar), 1)
        self.assertIn('UYARI denklem', out.getvalue())
        self.assertEqual(len(self.d._eq_elle), 1)

    def test_eq_bolunen_denklemi_numarasi_son_satirda_olacak_bicimde_ekler(self):
        self.d.eq('X(s) = [m x(0)s + m ẋ(0) + b x(0)]/(ms² + bs + k) = (0,1s + 0,35)/(s² + 3s + 2)', '(5-1)')
        son = self.d.story[-1]
        icerik = son._content if hasattr(son, '_content') else [son]
        tablolar = [x for x in icerik if isinstance(x, notlib.Table)]
        self.assertEqual(len(tablolar), 2)
        self.assertEqual(tablolar[0]._cellvalues[0][2].getPlainText(), '')
        self.assertEqual(tablolar[1]._cellvalues[0][2].getPlainText(), '(5-1)')


class Kopyalar(unittest.TestCase):
    def test_iki_notlib_kopyasi_ayni(self):
        a, b = (os.path.join(KOK, 'skills', k, 'scripts', 'notlib.py') for k in ('ders-notu', 'tekrar-notu'))
        self.assertTrue(filecmp.cmp(a, b, shallow=False))


if __name__ == '__main__':
    unittest.main()
