import contextlib, io, json, os, shutil, sys, tempfile, unittest

import pymupdf as fitz

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, 'skills', 'soru-kitapcigi', 'scripts'))
import solib
from solib import H, M, TB


from reportlab.platypus import Spacer


def sayfalar(pdf):
    return [p.get_text() for p in fitz.open(pdf)]


class KartTest(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.work)
        self.out = os.path.join(self.work, 'out.pdf')

    def derle(self, icerik, cevap=False, notu=None):
        solib.start(self.out, self.work, 'DENEME', 'Deneme', 'Kaynak: deneme')
        solib.kapak(['Kapsam: deneme'], cevap, notu)
        solib.bolum('Bölüm 1')
        icerik()
        hata = io.StringIO()
        with contextlib.redirect_stderr(hata):
            solib.make()
        self.hata = hata.getvalue()
        return sayfalar(self.out)

    def test_tek_konu_bant(self):
        s = ''.join(self.derle(lambda: solib.soru('1.1', ['1.1 Giriş'], 'Metin', ['Adım'])))
        self.assertIn('Soru 1.1\n', s)
        self.assertIn('1.1 Giriş', s)
        self.assertNotIn('KARMA ·', s)

    def test_karma_bant(self):
        s = ''.join(self.derle(lambda: solib.soru('1.2', ['A', 'B'], 'Metin', ['Adım'])))
        self.assertIn('KARMA · A + B', s)

    def test_kisa_kart_bolunmez(self):
        def icerik():
            for i in range(12):
                solib.soru('7.%d' % i, ['K'], 'SORUMETNI%02d ' % i + 'kelime ' * 60, ['Adım ' * 80, H('a = b')], sonuc='SONUCU%02d' % i)
        s = self.derle(icerik)
        self.assertGreater(len(s), 3)
        for i in range(12):
            soru = [n for n, t in enumerate(s) if 'SORUMETNI%02d' % i in t]
            son = [n for n, t in enumerate(s) if 'SONUCU%02d' % i in t]
            self.assertEqual(soru, son, i)
        self.assertNotIn('(devam)', ''.join(s))

    def test_uzun_kart_devam(self):
        s = self.derle(lambda: solib.soru('9.9', ['K'], 'UZUNSORU', ['Adım %d ' % i + 'kelime ' * 40 for i in range(40)], sonuc='BITTI'))
        ilk = next(t for t in s if 'UZUNSORU' in t)
        self.assertIn('ÇÖZÜM', ilk)
        self.assertIn('Adım 0', ilk)
        self.assertIn('Soru 9.9 (devam)', ''.join(s))
        self.assertIn('BITTI', ''.join(s))

    def test_konu_ardindan_uzun_kart(self):
        def icerik():
            solib.konu('KONUADI')
            solib.soru('9.8', ['KONUADI'], 'SORU', ['Adım %d ' % i + 'kelime ' * 40 for i in range(40)])
        s = self.derle(icerik)
        self.assertIn('(devam)', ''.join(s))
        self.assertTrue(any('KONUADI' in x and 'SORU' in x for x in s))

    def test_dev_adim_valueerror(self):
        with self.assertRaisesRegex(ValueError, 'Soru 3.3'):
            self.derle(lambda: solib.soru('3.3', ['K'], 'M', [TB([['A'], *[['x']] * 120])]))

    def test_figs_yokken_derlenir(self):
        self.derle(lambda: solib.soru('1.1', ['K'], 'M', ['A']))
        self.assertEqual(json.load(open(os.path.join(self.work, 'figs.json'))), {})

    def test_olmayan_sekil_mesaji(self):
        with self.assertRaisesRegex(KeyError, '5.10'):
            self.derle(lambda: solib.soru('1.1', ['K'], 'M', ['A'], sekil=[('5.10', 'alt')]))

    def test_sekil_kartta(self):
        from PIL import Image
        os.makedirs(os.path.join(self.work, 'fig'))
        Image.new('RGB', (200, 100), (200, 0, 0)).save(os.path.join(self.work, 'fig', '5.1.png'))
        json.dump({'5.1': [0, [0, 0, 200, 100]]}, open(os.path.join(self.work, 'figs.json'), 'w'))
        s = self.derle(lambda: solib.soru('1.1', ['K'], 'KARTSORU', ['A'], sekil=[('5.1', 'altyazı')]))
        n = next(i for i, t in enumerate(s) if 'KARTSORU' in t)
        self.assertEqual(len(fitz.open(self.out)[n].get_image_info()), 1)
        self.assertIn('Şekil 5.1', s[n])

    def test_soru_dizini(self):
        def icerik():
            solib.soru('1.1', ['Konu A'], 'M', ['A'])
            solib.soru('1.2', ['Konu A', 'Konu B'], 'M', ['A'])
        s = self.derle(icerik, notu='NOTUM')
        dizin = next(t for t in s if 'Soru dizini' in t)
        self.assertIn('1.1, 1.2', dizin)
        self.assertIn('NOTUM', dizin)

    def test_kapak_cevap_cumlesi(self):
        s = self.derle(lambda: solib.soru('1.1', ['K'], 'M', ['A']))
        self.assertIn('cevap anahtarı yoktur', ' '.join(s[0].split()))
        s = self.derle(lambda: solib.soru('1.1', ['K'], 'M', ['A']), cevap=True)
        self.assertNotIn('cevap anahtarı yoktur', ' '.join(s[0].split()))

    def test_varsayim_raporu(self):
        s = self.derle(lambda: solib.soru('1.1', ['K'], 'M', ['A'], varsayim='k = 50 alındı'))
        self.assertIn('Varsayım:', ''.join(s))
        self.assertIn('VARSAYIM 1.1: k = 50 alındı', self.hata)

    def test_yardimcilar_kartta(self):
        s = ''.join(self.derle(lambda: solib.soru('1.1', ['K'], 'M', [H('HESAPSATIRI'), M(['MADDEBIR', 'MADDEIKI']), TB([['BASLIK'], ['HUCRE']])])))
        for k in ('HESAPSATIRI', 'MADDEBIR', 'MADDEIKI', 'BASLIK', 'HUCRE'):
            self.assertIn(k, s)

    def test_grafik_cozumde(self):
        from PIL import Image
        yol = os.path.join(self.work, 'g.png')
        Image.new('RGB', (300, 200), (0, 0, 200)).save(yol)
        s = self.derle(lambda: solib.soru('1.1', ['K'], 'GRAFIKSORU', ['A', solib.G(yol, 'GRAFIKYAZI')]))
        n = next(i for i, t in enumerate(s) if 'GRAFIKSORU' in t)
        self.assertEqual(len(fitz.open(self.out)[n].get_image_info()), 1)
        self.assertLess(s[n].index('ÇÖZÜM'), s[n].index('GRAFIKYAZI'))

    def test_iki_nokta_sonraki_adimdan_ayrilmaz(self):
        for dolgu in range(0, 24, 3):       # sayfa sınırı farklı adımlara denk gelsin
            adim = ['Kısa dolgu'] * dolgu
            for i in range(30):
                adim += ['GIRIS%02d kısa:' % i, 'SONRAKI%02d ' % i + 'kelime ' * 25]
            s = self.derle(lambda: solib.soru('9.7', ['K'], 'M', adim))
            for i in range(30):
                sayfa = [n for n, x in enumerate(s) if 'GIRIS%02d' % i in x]
                sonraki = [n for n, x in enumerate(s) if 'SONRAKI%02d' % i in x]
                self.assertEqual(sayfa, sonraki, (dolgu, i))

    def bandlar(self):
        return [[l for l in p.get_text().split('\n') if l.startswith('Soru ') and l[5:6].isalnum() and ' ' not in l[5:]]
                for p in fitz.open(self.out)]

    def test_iki_nokta_ardindan_uzun_tablo_derlenir(self):
        for satir in (20, 30, 40):
            s = self.derle(lambda: solib.soru('4.4', ['K'], 'Metin ' * 80, ['Sonuçlar aşağıdaki tablodadır:', TB([['A']] + [['x']] * satir), 'Son adım']))
            self.assertIn('Soru 4.4', ''.join(s))

    def test_yerlesim_bosluklari_doldurur(self):
        def icerik():
            for no, h in (('A1', 380), ('A2', 380), ('A3', 100), ('A4', 100)):
                solib.soru(no, ['K'], 'M', [Spacer(1, h)])
        self.derle(icerik)
        dolu = [[x for x in b if x != 'Soru dizini'] for b in self.bandlar()]
        dolu = [b for b in dolu if b]
        self.assertEqual(len(dolu), 2, dolu)
        self.assertEqual(sorted(len(b) for b in dolu), [2, 2])

    def test_yerlesim_konulari_karistirmaz(self):
        def icerik():
            solib.konu('KONUBIR')
            solib.soru('B1', ['KONUBIR'], 'M', [Spacer(1, 500)])
            solib.konu('KONUIKI')
            solib.soru('B2', ['KONUIKI'], 'M', [Spacer(1, 500)])
            solib.soru('B3', ['KONUIKI'], 'M', [Spacer(1, 60)])
        s = ' '.join(self.derle(icerik)[2:])
        self.assertLess(s.index('Soru B1'), s.index('KONUIKI'))
        self.assertLess(s.index('KONUIKI'), s.index('Soru B3'))

    def test_bagli_sorular_birlikte_kalir(self):
        def icerik():
            solib.soru('C1', ['K'], 'M', [Spacer(1, 100)])
            solib.soru('C2', ['K'], 'M', [Spacer(1, 500)])
            solib.soru('C3', ['K'], 'M', [Spacer(1, 90)], bagli='C1')
        self.derle(icerik)
        sira = [n for b in self.bandlar() for n in b]
        self.assertEqual(abs(sira.index('Soru C1') - sira.index('Soru C3')), 1, sira)

    def test_bolum_basligi_yalniz_kalmaz(self):
        for dolgu in (300, 450, 600):
            def icerik():
                solib.soru('D1', ['K'], 'M', [Spacer(1, dolgu)])
                solib.bolum('IKINCIBOLUM')
                solib.konu('IKINCIKONU')
                solib.soru('D2', ['IKINCIKONU'], 'M', [Spacer(1, 400)])
            s = self.derle(icerik)[2:]
            ayni = [t for t in s if 'IKINCIBOLUM' in t]
            self.assertEqual(len(ayni), 1)
            self.assertIn('IKINCIKONU', ayni[0], dolgu)
            self.assertIn('Soru D2', ayni[0], dolgu)

    def test_bolumsuz_konu_derlenir(self):
        solib.start(self.out, self.work, 'D', 'D', 'K')
        solib.kapak(['K'], True)
        solib.konu('TEKKONU')
        solib.soru('E1', ['TEKKONU'], 'M', ['A'])
        with contextlib.redirect_stderr(io.StringIO()):
            solib.make()
        self.assertIn('Soru E1', ''.join(sayfalar(self.out)))

    def test_son_kart_bos_sayfa_acmaz(self):
        for h in range(560, 640, 8):
            s = self.derle(lambda: solib.soru('F1', ['K'], 'M', [Spacer(1, h)]))
            self.assertIn('Soru F1', s[-1], h)

    def test_tablo_basligi(self):
        s = ''.join(self.derle(lambda: solib.soru('1.1', ['K'], 'M', [TB([['A'], ['b']], baslik='Tablo 8.5 – Pay')])))
        self.assertIn('Tablo 8.5 – Pay', ' '.join(s.split()))

    def test_ek_cozumden_once(self):
        s = ''.join(self.derle(lambda: solib.soru('1.1', ['K'], 'M', ['A'], ek=[TB([['VERITABLO'], ['x']])])))
        self.assertLess(s.index('VERITABLO'), s.index('ÇÖZÜM'))

    def test_R_virgul(self):
        json.dump({'1.1': {'q': '500 W'}}, open(os.path.join(self.work, 'sonuc.json'), 'w'))
        solib.start(self.out, self.work, 'D', 'D', 'K')
        self.assertEqual(solib.R('1.1', 'q'), '500 W')
        with self.assertRaisesRegex(KeyError, '1.1/z'):
            solib.R('1.1', 'z')

    def test_skill_komutlari_var(self):
        import re
        yer = os.path.join(KOK, 'skills', 'soru-kitapcigi')
        metin = open(os.path.join(yer, 'SKILL.md'), encoding='utf-8').read()
        self.assertIn('name: soru-kitapcigi', metin)
        for y in re.findall(r'\$SK/\.\./\.\./ortak/(\w+\.\w+)', metin):
            self.assertTrue(os.path.exists(os.path.join(KOK, 'ortak', y)), y)
        for y in re.findall(r'\$SK/((?:scripts|examples)/\w+\.\w+)', metin):
            self.assertTrue(os.path.exists(os.path.join(yer, y)), y)
        for y in re.findall(r'\$DN/scripts/(\w+\.py)', metin):
            self.assertTrue(os.path.exists(os.path.join(KOK, 'skills', 'ders-notu', 'scripts', y)), y)
        self.assertTrue(os.path.exists(os.path.join(KOK, 'skills', 'formul-kagidi', 'scripts', 'review.py')))

    def test_notlib_kopyalari_ayni(self):
        a = open(os.path.join(KOK, 'skills', 'ders-notu', 'scripts', 'notlib.py'), 'rb').read()
        b = open(os.path.join(KOK, 'skills', 'tekrar-notu', 'scripts', 'notlib.py'), 'rb').read()
        self.assertEqual(a, b)


if __name__ == '__main__':
    unittest.main()
