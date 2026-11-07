"""denklem_kapsam: kaynaktaki numaralı denklem notta gösterilmiş mi, yalnız anılmış mı, yok mu?"""
import contextlib, io, os, shutil, sys, tempfile, unittest
import pymupdf as fitz

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, 'ortak'))
import denklem_kapsam as dk

YAZI = os.path.join(KOK, 'ortak', 'fonts', 'Carlito-Regular.ttf')


def pdf(yol, *sayfalar):
    d = fitz.open()
    for satirlar in sayfalar:
        p = d.new_page()
        for i, s in enumerate(satirlar):
            p.insert_text((50, 60 + 16 * i), s, fontname='car', fontfile=YAZI)
    d.save(yol); d.close()


class Taban(unittest.TestCase):
    def setUp(self):
        self.k = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, self.k)
        self.src, self.out = os.path.join(self.k, 's.pdf'), os.path.join(self.k, 'o.pdf')
        self.dis = os.path.join(self.k, 'disarida.txt')

    def calistir(self, *ek):
        b = io.StringIO()
        with contextlib.redirect_stdout(b):
            kod = dk.main([self.src, self.out, *ek])
        return kod, b.getvalue()


class Kaynak(Taban):
    def test_ayri_satirdaki_numara_denklemdir(self):
        pdf(self.src, ['q = -k dT/dx', '(2.1)', 'see Equation 2.5 and (2.6) in the text', 'E = mc', '(2.7a)'])
        self.assertEqual(sorted(dk.kaynak_numaralari(self.src)), ['2.1', '2.7a'])

    def test_sayfa_araligi_uygulanir(self):
        pdf(self.src, ['(1.1)'], ['(2.1)'], ['(3.1)'])
        self.assertEqual(sorted(dk.kaynak_numaralari(self.src, 2, 2)), ['2.1'])

    def test_satir_sonunda_denklemle_birlikte_numara_da_denklemdir(self):
        pdf(self.src, ['q = -k dT/dx     (2.1)', 'Bu sonuç (2.2) içindir, bakınız'])
        self.assertEqual(sorted(dk.kaynak_numaralari(self.src)), ['2.1'])


class Not(Taban):
    def test_uc_durum_ayrilir(self):
        pdf(self.out, ['q = -k dT/dx', '(2.1)', 'q2 = 5     (2.2)', 'ifadeler (2.3) ile yerine konur'])
        g, a = dk.not_numaralari(self.out)
        self.assertEqual(sorted(g), ['2.1', '2.2'])
        self.assertEqual(sorted(a), ['2.3'])

    def test_aralik_atif_harf_harf_acilir_ama_gosterilmis_sayilmaz(self):
        pdf(self.out, ['ifadeleri (2.18a–c) yerleştirilir ve'])
        g, a = dk.not_numaralari(self.out)
        self.assertEqual(g, set())
        self.assertEqual(sorted(a), ['2.18a', '2.18b', '2.18c'])

    def test_satir_sonu_aralik_gosterilmis_sayilir(self):
        pdf(self.out, ['q = 1     (6.16–6.18)', 'r = 2     (1.1–2)'])
        g, _ = dk.not_numaralari(self.out)
        self.assertEqual(sorted(g), ['1.1', '1.2', '6.16', '6.17', '6.18'])


class Rapor(Taban):
    def test_yalniz_anilan_denklem_gecmez(self):
        pdf(self.src, ['(2.18a)', '(2.18b)'])
        pdf(self.out, ['ifadeleri (2.18a–b) yerleştirilir ve'])
        kod, c = self.calistir()
        self.assertEqual(kod, 1)
        self.assertIn('YALNIZ ANILMIŞ', c); self.assertIn('2.18a', c)

    def test_eksik_denklem_gecmez(self):
        pdf(self.src, ['(2.16)', '(2.17)'])
        pdf(self.out, ['x = 1', '(2.16)'])
        kod, c = self.calistir()
        self.assertEqual(kod, 1)
        self.assertIn('YOK: 2.17', c)

    def test_hepsi_gosterilmisse_gecer(self):
        pdf(self.src, ['(2.1)'])
        pdf(self.out, ['x = 1', '(2.1)'])
        kod, c = self.calistir()
        self.assertEqual(kod, 0)
        self.assertIn('DENKLEM KAPSAMI TAMAM', c)

    def test_gerekceli_dislama_gecer_ve_raporlanir(self):
        pdf(self.src, ['(2.1)', '(3.9)'])
        pdf(self.out, ['x = 1', '(2.1)'])
        with open(self.dis, 'w', encoding='utf-8') as f:
            f.write('3.9: kullanıcı bu alt bölümü kapsam dışı bıraktı\n')
        kod, c = self.calistir('--disarida', self.dis)
        self.assertEqual(kod, 0)
        self.assertIn('kapsam dışı bıraktı', c)

    def test_gerekcesiz_dislama_gecmez(self):
        pdf(self.src, ['(3.9)'])
        pdf(self.out, ['x = 1'])
        with open(self.dis, 'w', encoding='utf-8') as f:
            f.write('3.9\n')
        kod, c = self.calistir('--disarida', self.dis)
        self.assertEqual(kod, 1)
        self.assertIn('GEREKÇESİZ', c)

    def test_kaynakta_numara_bulunmazsa_guvence_vermez(self):
        pdf(self.src, ['Slayt metni'])
        pdf(self.out, ['x = 1'])
        kod, c = self.calistir()
        self.assertEqual(kod, 2)
        self.assertIn('numaralı denklem bulunamadı', c)
        self.assertNotIn('TAMAM', c)

    def test_kaynaksiz_kip_metinde_kalan_numarayi_bulur(self):
        pdf(self.out, ['A sabit ise q Δx/A = −k ΔT (3.27). Integral alınır.', 'q = −k dT/dx (3.26)', 'a = b (2.13a)', '(2.13) yerine konursa'])
        b = io.StringIO()
        with contextlib.redirect_stdout(b):
            kod = dk.main(['-', self.out])
        self.assertEqual(kod, 1)
        self.assertIn('BELGEDE YALNIZ ANILMIŞ (denklemi numarasıyla göster): 3.27', b.getvalue())
        self.assertNotIn('3.26', b.getvalue().split(':')[-1])
        self.assertNotIn('2.13', b.getvalue())

    def test_kaynaksiz_kip_temiz_belge(self):
        pdf(self.out, ['q = −k dT/dx (3.26)', '(3.26) ile bulunur'])
        b = io.StringIO()
        with contextlib.redirect_stdout(b):
            kod = dk.main(['-', self.out])
        self.assertEqual(kod, 0)
        self.assertIn('BELGE İÇİ TAMAM', b.getvalue())

    def test_kaynakta_numara_yoksa_belge_ici_de_yazilir(self):
        pdf(self.src, ['Slayt metni'])
        pdf(self.out, ['metinde (3.27) geçer'])
        kod, c = self.calistir()
        self.assertEqual(kod, 2)
        self.assertIn('BELGEDE YALNIZ ANILMIŞ', c)


if __name__ == '__main__':
    unittest.main()
