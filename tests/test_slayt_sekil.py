"""slayt_sekil.py: slayt zeminindeki resim parçaları tek tek kesilip beyaz zeminde birleşir; süs resimleri ve gri zemin girmez."""
import io, json, os, shutil, sys, tempfile, unittest
import pymupdf as fitz
from PIL import Image

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, 'skills', 'ders-notu', 'scripts'))
import slayt_sekil

GRI = (0.82, 0.82, 0.82)


def png(renk, en=120, boy=80):
    b = io.BytesIO()
    Image.new('RGB', (en, boy), renk).save(b, 'PNG')
    return b.getvalue()


def belge(yol, sayfa=4):
    """Her sayfada iki gri slayt; üst slaytta iki ayrı resim parçası (aralarında gri zemin), alt slaytta bir parça;
    her slaytta aynı süs resmi (tekrar eden logo)."""
    d = fitz.open()
    logo = png((200, 180, 40), 30, 30)
    for i in range(sayfa):   # içerik resimleri her sayfada farklı (gerçek slaytlardaki gibi), logo aynı
        p = d.new_page(width=540, height=720)
        for y0 in (68, 381):
            p.draw_rect(fitz.Rect(90, y0, 450, y0 + 270), color=None, fill=GRI)
            p.insert_image(fitz.Rect(410, y0 + 223, 440, y0 + 253), stream=logo)
        p.insert_image(fitz.Rect(110, 120, 230, 200), stream=png((30, 60, 200 - 10 * i)))
        p.insert_image(fitz.Rect(300, 130, 420, 210), stream=png((200 - 10 * i, 40, 40)))
        p.insert_text((240, 175), 'Slayt metni', fontsize=12)   # iki parçanın arasında
        p.insert_image(fitz.Rect(140, 430, 380, 590), stream=png((20, 150 - 10 * i, 60), 240, 160))
    d.save(yol)
    d.close()


class SlaytSekil(unittest.TestCase):
    def setUp(self):
        self.k = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.k)
        self.pdf = os.path.join(self.k, 's.pdf')
        belge(self.pdf)
        self.w = os.path.join(self.k, 'w')

    def calistir(self, *arg):
        out = io.StringIO()
        so, sys.stdout = sys.stdout, out
        try:
            slayt_sekil.main([self.pdf, self.w] + list(arg))
        finally:
            sys.stdout = so
        return json.load(open(os.path.join(self.w, 'parcalar.json'))), json.load(open(os.path.join(self.w, 'figs.json')))

    def test_parcalar_slayta_gore_ayrilir_sus_atilir(self):
        parcalar, figs = self.calistir('1-4')
        self.assertEqual(sorted(parcalar)[:2], ['1a', '1b'])
        self.assertEqual(len(parcalar['1a'][1]), 2)   # iki ayrı parça; logo süs sayıldı
        self.assertEqual(len(parcalar['1b'][1]), 1)
        self.assertEqual(sorted(figs), sorted(parcalar))

    def test_parcalar_arasinda_gri_zemin_yok(self):
        self.calistir('1-4')
        im = Image.open(os.path.join(self.w, 'fig', '1a.png')).convert('RGB')
        renkler = {c for _, c in im.getcolors(1 << 20)}
        gri = [c for c in renkler if all(abs(v - 209) <= 6 for v in c)]
        self.assertEqual(gri, [], 'parçaların arasına slayt zemini girmiş')
        self.assertIn((255, 255, 255), renkler)

    def test_duzenlenen_listeden_yeniden_birlestirir(self):
        parcalar, _ = self.calistir('1-4')
        parcalar = {'1a': [parcalar['1a'][0], parcalar['1a'][1][:1]]}   # yalnız ilk parça, tek slayt
        json.dump(parcalar, open(os.path.join(self.w, 'parcalar.json'), 'w'))
        _, figs = self.calistir('--parcalar')
        self.assertEqual(list(figs), ['1a'])
        self.assertEqual(sorted(os.listdir(os.path.join(self.w, 'fig'))), ['1a.png'])   # eski kesimler silindi
        en, boy = Image.open(os.path.join(self.w, 'fig', '1a.png')).size
        self.assertLess(en / boy, 2.2)   # yalnız 120×80'lik parça (+ kenar payı)

    def test_denetci_yalniz_parca_icindeki_yaziyi_okur(self):
        # 'Slayt metni' iki parçanın birleşik kutusunun içinde ama parçaların dışında: şekil etiketi sayılmaz
        parcalar, figs = self.calistir('1-4')
        from uslup_denetim import kaynak_etiketleri
        tum = kaynak_etiketleri(self.pdf, {'1a': figs['1a']})
        parcali = kaynak_etiketleri(self.pdf, {'1a': figs['1a']}, parcalar)
        self.assertIn('metni', tum['1a'])
        self.assertNotIn('metni', parcali['1a'])

    def test_denetci_her_sayfadaki_altligi_etiket_saymaz(self):
        # her sayfada aynı altlık yazısı resim parçasının üstüne biniyor: etiket sayılmaz
        d = fitz.open(self.pdf)
        for p in d:
            p.insert_text((150, 560), 'Makina Elemanlari', fontsize=9)
        yol = os.path.join(self.k, 'alt.pdf')
        d.save(yol)
        self.pdf = yol
        parcalar, figs = self.calistir('1-4')
        from uslup_denetim import kaynak_etiketleri
        et = kaynak_etiketleri(self.pdf, figs, parcalar)
        self.assertNotIn('Makina', et['1b'])

    def test_zeminsiz_sayfa_tek_slayt(self):
        d = fitz.open()
        p = d.new_page(width=540, height=720)
        p.insert_image(fitz.Rect(100, 100, 300, 250), stream=png((10, 10, 10), 200, 150))
        yol = os.path.join(self.k, 'z.pdf')
        d.save(yol)
        self.pdf = yol
        parcalar, _ = self.calistir('1-1')
        self.assertEqual(list(parcalar), ['1a'])



class Satir(unittest.TestCase):
    """Yeniden dizmenin birimi slayttaki satırdır; birbirine binen parçalar tek parçadır."""
    def test_ayni_satirdaki_parcalar_gruplanir(self):
        R = fitz.Rect
        # 20b gibi: üç satır, her satırda kötü|iyi çifti
        p = [R(140, 448, 196, 508), R(221, 448, 284, 508), R(136, 514, 196, 550), R(216, 514, 284, 553),
             R(112, 568, 195, 609), R(209, 568, 291, 608)]
        g = slayt_sekil.satirla(p)
        self.assertEqual([[r.x0 for r in s] for s in g], [[140, 221], [136, 216], [112, 209]])

    def test_ust_uste_satirlar_ayri_kalir(self):
        R = fitz.Rect
        # 17b gibi: satırlar yalnız kenarda 1 pt değiyor
        p = [R(121, 449, 290, 506), R(115, 505, 294, 567), R(129, 566, 315, 652)]
        self.assertEqual(len(slayt_sekil.satirla(p)), 3)

    def test_binen_parcalar_birlesir(self):
        R = fitz.Rect
        # 10a gibi: ikinci resim birincinin köşesine biniyor (kesişim küçüğün %20'si)
        p = slayt_sekil.kaynastir([R(95, 101, 450, 220), R(300, 189, 450, 339)])
        self.assertEqual(len(p), 1)
        self.assertEqual(tuple(p[0]), (95, 101, 450, 339))
        # yalnız kenarda değenler birleşmez
        self.assertEqual(len(slayt_sekil.kaynastir([R(121, 449, 290, 506), R(115, 505, 294, 567)])), 2)


if __name__ == '__main__':
    unittest.main()
