import contextlib, io, json, os, shutil, sys, tempfile, unittest

import pymupdf as fitz

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, 'skills', 'soru-kitapcigi', 'scripts'))
import solib
from solib import H, M, TB


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
