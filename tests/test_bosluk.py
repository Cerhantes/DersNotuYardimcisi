"""Sayfa altında gereksiz boşluk kalmaz: başlık uzun paragrafıyla birlikte sayfa atlamaz, şekilli grup küçültülerek
sığdırılır, sığdırılan şekil yine de kayarsa boşluk kaydedilir."""
import contextlib, io, json, os, shutil, sys, tempfile, unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, 'skills', 'ders-notu', 'scripts'))
import notlib
import pymupdf as fitz
from reportlab.platypus import Spacer
from test_yan_yana import sekil


def sayfa_bul(pdf, metin):
    d = fitz.open(pdf)
    return [i for i, p in enumerate(d) if i >= 2 and metin in p.get_text()]   # kapak ve içindekiler hariç


def yap(work, govde):
    d = notlib.Doc(os.path.join(work, 'o.pdf'), 'T', 'S', 'H', work, 'K')
    d.cover(['k'], ['n'])
    d.h1('1. A')
    govde(d)
    with contextlib.redirect_stdout(io.StringIO()):
        d.make()
    return d, os.path.join(work, 'o.pdf')


class Bosluk(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.work)
        sekil(self.work)

    def test_baslik_uzun_paragrafla_sayfa_atlamaz(self):
        # sayfanın altında ≈ 5 cm kalır; başlık ve paragrafın ilk satırları orada kalmalı, paragraf bölünmeli
        def g(d):
            d.raw(Spacer(1, notlib.FH - 5.5 * notlib.cm - 60))
            d.p('DOLGU SONU.')
            d.h2('1.1 BASLIKX')
            d.p('Uzun paragraf cümlesi. ' * 120)
        _, pdf = yap(self.work, g)
        self.assertEqual(sayfa_bul(pdf, 'DOLGU SONU'), sayfa_bul(pdf, 'BASLIKX'))

    def test_baslik_tek_satira_yer_yoksa_atlar(self):
        # 1,5 cm'de başlık + iki satır sığmaz: başlık yalnız kalmamak için sonraki sayfaya geçer
        def g(d):
            d.raw(Spacer(1, notlib.FH - 1.5 * notlib.cm - 60))
            d.p('DOLGU SONU.')
            d.h2('1.1 BASLIKX', need=0)
            d.p('Uzun paragraf cümlesi. ' * 120)
        _, pdf = yap(self.work, g)
        self.assertEqual(sayfa_bul(pdf, 'BASLIKX')[0], sayfa_bul(pdf, 'DOLGU SONU')[0] + 1)

    def test_sekilli_grup_kucultulerek_sigar(self):
        sekil(self.work)
        for bos_cm in (8.6, 8.2):   # tam boyda sığmaz, küçültülünce sığar
            def g(d):
                d.raw(Spacer(1, notlib.FH - bos_cm * notlib.cm - 40))
                d.p('DOLGU SONU.')
                d.p('Şekil 9.1 ve şu bağıntı:')
                gr = d.grup_bas()
                d.eq('τ = F / A', '(1.1)')
                d.fig('9.1', 'GRUPSEKLI.', maxh=230)
                d.grup_son(gr)
                d.h2('1.2 Sonraki')
                d.p('Metin.')
            doc, pdf = yap(self.work, g)
            self.assertEqual(sayfa_bul(pdf, 'DOLGU SONU'), sayfa_bul(pdf, 'GRUPSEKLI'), bos_cm)
            self.assertTrue(doc._sekil_sonuc, bos_cm)

    def test_sigma_payi(self):
        # reportlab'ın verdiği yer, frame._y − _y1p'den biraz azdır; pay sıfırdan büyük olmalı
        self.assertGreater(notlib.Doc.SIGMA_PAYI, 0.5)


if __name__ == '__main__':
    unittest.main()
