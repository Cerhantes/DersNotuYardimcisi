import contextlib, io, json, os, shutil, sys, tempfile, unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, 'skills', 'soru-kitapcigi', 'scripts'))
import solib
from denetim import denetle, rapor
from hesaplib import Hesap


class DenetimTest(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.work)
        self.pdf = os.path.join(self.work, 'out.pdf')

    def derle(self, kartlar, sorular, cikarilan=(), notu=None):
        """kartlar: solib.soru argüman listeleri; sorular: sorular.json 'sorular' listesi"""
        solib.start(self.pdf, self.work, 'D', 'D', 'K')
        solib.kapak(['K'], False, notu)
        for a in kartlar:
            solib.soru(*a[0], **a[1])
        with contextlib.redirect_stderr(io.StringIO()):
            solib.make()
        json.dump({'sorular': sorular, 'cikarilan': list(cikarilan)},
                  open(os.path.join(self.work, 'sorular.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        return denetle(self.pdf, self.work)

    @staticmethod
    def kart(no, konular=('K',), metin='Metin', **k):
        return ((no, list(konular), metin, ['Adım']), k)

    def sekilli(self, no='5.1'):
        from PIL import Image
        os.makedirs(os.path.join(self.work, 'fig'), exist_ok=True)
        Image.new('RGB', (100, 50), (200, 0, 0)).save(os.path.join(self.work, 'fig', no + '.png'))
        json.dump({no: [0, [0, 0, 100, 50]]}, open(os.path.join(self.work, 'figs.json'), 'w'))

    def test_temiz(self):
        self.assertEqual(self.derle([self.kart('1.1')], [{'no': '1.1', 'konular': ['K']}]), [])

    def test_eksik_soru(self):
        s = self.derle([self.kart('1.1')], [{'no': '1.1', 'konular': ['K']}, {'no': '1.2', 'konular': ['K']}])
        self.assertEqual(len(s), 1)
        self.assertIn('1.2', s[0])

    def test_fazla_soru(self):
        s = self.derle([self.kart('1.1'), self.kart('1.9')], [{'no': '1.1', 'konular': ['K']}])
        self.assertTrue(any('1.9' in x for x in s))

    def test_5_1_ve_5_10_karismaz(self):
        s = self.derle([self.kart('5.10')], [{'no': '5.1', 'konular': ['K']}, {'no': '5.10', 'konular': ['K']}])
        self.assertEqual(len(s), 1)
        self.assertIn('5.1 ', s[0] + ' ')

    def test_birlesik_numara(self):
        no = '8.35 / 8.73'
        self.assertEqual(self.derle([self.kart(no)], [{'no': no, 'konular': ['K']}]), [])

    def test_numarasiz(self):
        self.assertEqual(self.derle([self.kart('S12')], [{'no': 'S12', 'konular': ['K']}]), [])

    def test_metin_soru_atfi_bant_sanilmaz(self):
        s = self.derle([self.kart('1.1', metin="Soru 1.7'deki duvar için bulunuz")], [{'no': '1.1', 'konular': ['K']}])
        self.assertEqual(s, [])

    def test_konu_eksik(self):
        s = self.derle([self.kart('1.1', ('Başka',))], [{'no': '1.1', 'konular': ['K']}])
        self.assertTrue(any('konu' in x.lower() for x in s))

    def test_karma_etiketi(self):
        s = self.derle([self.kart('1.1')], [{'no': '1.1', 'konular': ['K', 'L']}])
        self.assertTrue(any('KARMA' in x for x in s))

    def test_karma_temiz(self):
        k = ['Uzun bir konu başlığı olur burada', 'Yine uzun bir ikinci konu başlığı olur', 'Üçüncü konu başlığı da uzun olur burada']
        self.assertEqual(self.derle([self.kart('1.1', k)], [{'no': '1.1', 'konular': k}]), [])

    def test_sekil_eksik(self):
        s = self.derle([self.kart('1.1')], [{'no': '1.1', 'konular': ['K'], 'sekiller': ['5.1']}])
        self.assertTrue(any('5.1' in x for x in s))

    def test_sekil_var(self):
        self.sekilli()
        s = self.derle([self.kart('1.1', sekil=[('5.1', 'alt')])], [{'no': '1.1', 'konular': ['K'], 'sekiller': ['5.1']}])
        self.assertEqual(s, [])

    def test_tablo_eksik(self):
        s = self.derle([self.kart('1.1')], [{'no': '1.1', 'konular': ['K'], 'tablolar': ['8.3']}])
        self.assertTrue(any('8.3' in x for x in s))

    def test_sekilsiz_atif(self):
        for metin in ('Şekil 5.1 için bulunuz', 'Fig. 5.1 için bulunuz', 'Şekildeki parçayı inceleyiniz'):
            s = self.derle([self.kart('1.1', metin=metin)], [{'no': '1.1', 'konular': ['K']}])
            self.assertTrue(any('atıf' in x.lower() for x in s), metin)

    def test_sayisal_sonuc_yok(self):
        s = self.derle([self.kart('1.1')], [{'no': '1.1', 'konular': ['K'], 'sayisal': True}])
        self.assertTrue(any('hesap' in x.lower() for x in s))

    def test_sayisal_kart_hesapla_uyusmaz(self):
        Hesap(self.work).kaydet('1.1', 'q', 500, 'W', 0)
        s = self.derle([self.kart('1.1', sonuc='q = 400 W')], [{'no': '1.1', 'konular': ['K'], 'sayisal': True}])
        self.assertTrue(any('500 W' in x for x in s))

    def test_sayisal_temiz(self):
        Hesap(self.work).kaydet('1.1', 'q', 500, 'W', 0)
        s = self.derle([self.kart('1.1', sonuc='q = 500 W')], [{'no': '1.1', 'konular': ['K'], 'sayisal': True}])
        self.assertEqual(s, [])

    def test_ardisik_kartta_son_satir_okunur(self):
        h = Hesap(self.work)
        h.kaydet('1.1', 'q', 500, 'W', 0)
        h.kaydet('1.2', 'q', 600, 'W', 0)
        y = [{'no': n, 'konular': ['K'], 'sayisal': True} for n in ('1.1', '1.2')]
        self.assertEqual(self.derle([self.kart('1.1', notu='Son satır 500 W'), self.kart('1.2', notu='Son satır 600 W')], y), [])

    def test_bagli_komsu(self):
        y = [{'no': '1.1', 'konular': ['K']}, {'no': '1.2', 'konular': ['K']}, {'no': '1.3', 'konular': ['K'], 'bagli': '1.1'}]
        s = self.derle([self.kart('1.1'), self.kart('1.2'), self.kart('1.3')], y)
        self.assertTrue(any('komşu' in x for x in s))

    def test_cikarilan_notta(self):
        y = [{'no': '1.1', 'konular': ['K']}]
        c = [{'no': '9.9', 'neden': 'veri yok'}]
        self.assertTrue(any('9.9' in x for x in self.derle([self.kart('1.1')], y, c)))
        self.assertEqual(self.derle([self.kart('1.1')], y, c, notu='9.9 çıkarıldı: veri yok'), [])

    def test_bilgi_satirlari(self):
        adim = ['Adım %d ' % i + 'kelime ' * 40 for i in range(40)]
        self.derle([(('1.1', ['K'], 'M', adim), {})], [{'no': '1.1', 'konular': ['K'], 'cevap': '≈ 3 kN'}])
        _, bilgi = rapor(self.pdf, self.work)
        self.assertIn('UZUN KART: 1.1', bilgi)
        self.assertIn('CEVAP KARŞILAŞTIR: 1.1 ≈ 3 kN', bilgi)

    def test_hesap_virgul(self):
        self.assertEqual(Hesap(self.work).kaydet('1.1', 'q', 500.123, 'W', 1), '500,1 W')
        self.assertEqual(json.load(open(os.path.join(self.work, 'sonuc.json'), encoding='utf-8'))['1.1']['q'], '500,1 W')


if __name__ == '__main__':
    unittest.main()
