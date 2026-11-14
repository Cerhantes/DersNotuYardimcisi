"""Üslup denetimi: kurala aykırı yazımı yakalar, Türkçede doğru olan yazımı yakalamaz."""
import contextlib, io, json, os, shutil, sys, tempfile, unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, 'skills', 'ders-notu', 'scripts'))
import notlib
from uslup_denetim import denetle


def h1(t):
    return {'t': 'h1', 'metin': t}


def p(t):
    return {'t': 'p', 'metin': t}


def ozet():
    return {'t': 'box', 'tur': 'ozet', 'baslik': 'ÖZET', 'icerik': [{'t': 'metin', 'metin': '• özet'}]}


TEKRAR = [h1('Genel Tekrar ve Kendini Sına'), ozet(), {'t': 'h3', 'metin': 'Kendini Sına'},
          {'t': 'bl', 'maddeler': ['a?', 'b?', 'c?'], 'num': True}]


def not_(*ogeler, tekrar=True):
    """Tek bölümlük, kurallara uygun iskelet; ogeler bölümün ortasına girer."""
    return [h1('1. Konu'), p('Giriş paragrafı.')] + list(ogeler) + [ozet()] + (TEKRAR if tekrar else [])


def kurallar(kayit, etiketler=None):
    kesin, oneri = denetle(kayit, etiketler)
    return [k for k, _, _ in kesin], [k for k, _, _ in oneri]


class Temiz(unittest.TestCase):
    def test_uygun_not_temiz(self):
        self.assertEqual(kurallar(not_(p('Şekil 2.1\'de görüldüğü gibi akı 2,5 W/m² olur.'))), ([], []))


class YerAtfi(unittest.TestCase):
    def test_asagidaki_sekil_kesin(self):
        for t in ('Aşağıdaki şekle bakalım.', 'Yukarıdaki tabloda değerler var.', 'Önceki grafik bunu gösterir.',
                  'Yandaki şeklin sol tarafı.'):
            self.assertIn('yer-atfı', kurallar(not_(p(t)))[0], t)

    def test_numarasiz_sekilde_goruldugu_kesin(self):
        self.assertIn('yer-atfı', kurallar(not_(p('Şekilde görüldüğü gibi sıcaklık düşer.')))[0])

    def test_bu_sekilde_turkce_dogru(self):
        for t in ('Bu şekilde gösterilir ki akı sabittir.', 'Isı üç şekilde aktarılır.', 'Böyle bir şekilde görülür.'):
            self.assertEqual(kurallar(not_(p(t))), ([], []), t)

    def test_asagidaki_sekilde_yalniz_oneri(self):
        kesin, oneri = kurallar(not_(p('Akı aşağıdaki şekilde hesaplanır:')))
        self.assertEqual(kesin, [])
        self.assertIn('yer-atfı', oneri)


class Ondalik(unittest.TestCase):
    def test_birimli_noktali_sayi_kesin(self):
        self.assertIn('ondalık', kurallar(not_(p('Duvar 0.2 m kalınlığındadır.')))[0])

    def test_denklemde_noktali_sayi_kesin(self):
        self.assertIn('ondalık', kurallar(not_({'t': 'eq', 'metin': 'Q = 0.7 × 10', 'no': ''}))[0])

    def test_cozum_adiminda_noktali_sayi_kesin(self):
        cz = {'t': 'cozum', 'baslik': 'Ö', 'soru': 'S', 'sekil': None, 'verilen': ['v', 'i'], 'kabuller': [],
              'adimlar': [{'metin': 'adım', 'denklemler': ['q = 1.4 × 10']}], 'sonuc': ['q = 3'], 'yorum': None}
        self.assertIn('ondalık', kurallar(not_(cz))[0])

    def test_numaralar_ondalik_sayilmaz(self):
        for t in ('Şekil 2.3 ve Tablo 4.1 birlikte okunur.', 'Bölüm 6.2 bunu anlatır; (3.27) kullanılır.'):
            self.assertEqual(kurallar(not_(p(t)))[0], [], t)
        self.assertEqual(kurallar(not_({'t': 'eq', 'metin': 'Q = (2.1) ile (2.3–2.5) birlikte', 'no': '(2.6)'}))[0], [])

    def test_baslik_numarasi_ondalik_sayilmaz(self):
        self.assertEqual(kurallar(not_({'t': 'h2', 'metin': '2.1 Isı Akısı'}, p('x')))[0], [])

    def test_tablo_hucresi_yalniz_oneri(self):
        tb = {'t': 'table', 'baslik': None, 'satirlar': [['Malzeme', 'k'], ['Bakır', '0.4']]}
        kesin, oneri = kurallar(not_(tb))
        self.assertEqual(kesin, [])
        self.assertIn('ondalık', oneri)


class Kesme(unittest.TestCase):
    def test_kesmesiz_ek_kesin(self):
        for t in ('Şekil 2.3te görülür.', '(3.27)den çıkar.', '1313 °Cde başlar.', 'Tablo 4.1deki değer.'):
            self.assertIn('kesme', kurallar(not_(p(t)))[0], t)

    def test_kesmeli_ve_alt_sekil_dogru(self):
        for t in ("Şekil 2.3'te görülür.", "(3.27)'den çıkar.", "1313 °C'de başlar.", 'Şekil 3.13a ve 3-14b birlikte.',
                  "Şekil 3.13a'da görülür."):
            self.assertEqual(kurallar(not_(p(t)))[0], [], t)


class Yapi(unittest.TestCase):
    def test_ozetsiz_bolum_kesin(self):
        kayit = [h1('1. A'), p('giriş')] + TEKRAR
        self.assertIn('bölüm-özeti', kurallar(kayit)[0])

    def test_ozet_sonda_degil_kesin(self):
        kayit = [h1('1. A'), p('giriş'), ozet(), p('sonra')] + TEKRAR
        self.assertIn('bölüm-özeti', kurallar(kayit)[0])

    def test_girissiz_bolum_kesin(self):
        kayit = [h1('1. A'), {'t': 'h2', 'metin': '1.1 B'}, p('x'), ozet()] + TEKRAR
        self.assertIn('bölüm-girişi', kurallar(kayit)[0])

    def test_genel_tekrar_yok_kesin(self):
        self.assertIn('not-sonu', kurallar(not_(tekrar=False))[0])

    def test_kendini_sina_sorulari_yok_kesin(self):
        kayit = not_(tekrar=False) + [h1('Genel Tekrar ve Kendini Sına'), ozet()]
        self.assertIn('not-sonu', kurallar(kayit)[0])

    def test_kapak_bolum_sayilmaz(self):
        kayit = [{'t': 'kapak', 'satirlar': []}, {'t': 'box', 'tur': 'ipucu', 'baslik': None, 'icerik': []}] + not_()
        self.assertEqual(kurallar(kayit)[0], [])


class Terim(unittest.TestCase):
    def test_kalin_olmayan_terim_oneri(self):
        kesin, oneri = kurallar(not_(p('Buna ısı akısı (heat flux) denir.')))
        self.assertEqual(kesin, [])
        self.assertIn('terim', oneri)

    def test_kalin_terim_temiz(self):
        self.assertEqual(kurallar(not_(p('Buna <b>ısı akısı</b> (heat flux) denir.'))), ([], []))

    def test_ikinci_tanitim_oneri_ama_tanim_kutusu_degil(self):
        tanim = {'t': 'box', 'tur': 'tanim', 'baslik': None, 'icerik': [{'t': 'metin', 'metin': '<b>Isı akısı</b> (heat flux): …'}]}
        self.assertEqual(kurallar(not_(p('<b>ısı akısı</b> (heat flux)'), tanim))[1], [])
        self.assertIn('terim', kurallar(not_(p('<b>ısı akısı</b> (heat flux)'), p('yine <b>akı</b> (heat flux)')))[1])

    def test_turkce_parantez_terim_sayilmaz(self):
        self.assertEqual(kurallar(not_(p('Duvar (tek boyutlu) kabul edilir; iletim (sabit k ile) hesaplanır.'))), ([], []))


class SekilTerimi(unittest.TestCase):
    FIG = {'t': 'fig', 'no': '2.1', 'cap': 'Levha.', 'terms': None}

    def test_etiketli_sekilde_terim_yok_kesin(self):
        self.assertIn('şekil-terimi', kurallar(not_(self.FIG), {'2.1': ['Hot', 'surface', 'x']})[0])

    def test_bos_terim_de_kesin(self):
        fig = dict(self.FIG, terms='')
        self.assertIn('şekil-terimi', kurallar(not_(fig), {'2.1': ['Thickness']})[0])

    def test_etiketsiz_sekil_temiz(self):
        self.assertEqual(kurallar(not_(self.FIG), {'2.1': ['x', '10', 'T1']}), ([], []))

    def test_eksik_etiket_oneri(self):
        fig = dict(self.FIG, terms='Hot surface = sıcak yüz')
        kesin, oneri = kurallar(not_(fig), {'2.1': ['Hot', 'surface', 'Thickness']})
        self.assertEqual(kesin, [])
        self.assertIn('şekil-terimi', oneri)

    def test_turkce_kaynakta_turkce_etiket_terim_istemez(self):
        # slayttaki 'Lehim alanları' notun Türkçe metninde de geçiyor: çevrilecek terim değil
        kayit = not_(p('Her hesapta önce <b>lehim alanları</b> (joint area) belirlenir.'), self.FIG)
        self.assertEqual(kurallar(kayit, {'2.1': ['Lehim', 'alanları']}), ([], []))

    def test_parantez_ici_ingilizce_turkce_sayilmaz(self):
        # 'clearance' yalnız parantez içinde geçiyor: şekildeki İngilizce etiket hâlâ terim ister
        kayit = not_(p('Buna <b>lehim aralığı</b> (joint clearance) denir.'), self.FIG)
        self.assertIn('şekil-terimi', kurallar(kayit, {'2.1': ['Joint', 'clearance']})[0])

    def test_cozumdeki_cizim_de_denetlenir(self):
        cz = {'t': 'cozum', 'baslik': 'Ö', 'soru': 'S', 'sekil': dict(self.FIG, no='H2.1'), 'verilen': ['v', 'i'],
              'kabuller': [], 'adimlar': [], 'sonuc': [], 'yorum': None}
        self.assertIn('şekil-terimi', kurallar(not_(cz), {'H2.1': ['Insulation']})[0])


class Paragraf(unittest.TestCase):
    def test_uzun_paragraf_oneri(self):
        t = ' '.join('Bu %d. cümledir.' % i for i in range(7))
        self.assertIn('paragraf', kurallar(not_(p(t)))[1])

    def test_kisaltma_ve_ondalik_cumle_sayilmaz(self):
        t = 'Değer 2,5 olur, vb. durumlar da var. Bkz. Şekil 2.1. Üçüncü cümle. Dördüncü.'
        self.assertNotIn('paragraf', kurallar(not_(p(t)))[1])


class NotlibKaydi(unittest.TestCase):
    """notlib make() iskeleti kayit.json'a yazar; denetçi onu okur."""

    def test_ornek_not_kaydi_ve_denetimi(self):
        work = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, work)
        from PIL import Image
        os.makedirs(os.path.join(work, 'fig'))
        Image.new('RGB', (100, 60), 'white').save(os.path.join(work, 'fig', '1.1.png'))
        json.dump({'1.1': [0, [0, 0, 100, 60]]}, open(os.path.join(work, 'figs.json'), 'w'))
        d = notlib.Doc(os.path.join(work, 'o.pdf'), 'T', 'S', 'H', work, 'K')
        d.cover(['k'], ['n'])
        d.h1('1. A'); d.p('Giriş.'); d.eq('q = 1', '(1.1)')
        d.box('ornek', ['x', d.beq('y = 0.5')])
        d.fig('1.1', 'şekil', terms='A = a')
        d.cozum('Ö', 'S', d.kf('1.1', 'ç', h=40), ('v', 'i'), [], [('adım', ['z = 2'])], ['z = 2'])
        d.box('ozet', ['• ö'])
        with contextlib.redirect_stdout(io.StringIO()):   # devnull Windows'ta cp1252 açılır, 'İ' yazılamaz
            d.make()
        kayit = json.load(open(os.path.join(work, 'kayit.json'), encoding='utf-8'))
        self.assertEqual([o['t'] for o in kayit], ['kapak', 'box', 'h1', 'p', 'eq', 'box', 'fig', 'cozum', 'box'])
        self.assertEqual(kayit[5]['icerik'][1], {'t': 'eq', 'metin': 'y = 0.5', 'no': ''})
        self.assertEqual(kayit[7]['sekil']['no'], '1.1')
        kesin = [k for k, _, _ in denetle(kayit)[0]]
        self.assertIn('ondalık', kesin)      # kutudaki beq yakalandı
        self.assertIn('not-sonu', kesin)


if __name__ == '__main__':
    unittest.main()
