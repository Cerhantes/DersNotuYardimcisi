"""hazirla.py: şekil bayraklarını aralığın sayfalarından doğru seçer; tek komutta metin + kesim üretir.
denetle.py: engelleri toplar, çıkış koduyla bildirir."""
import argparse, contextlib, io, json, os, shutil, subprocess, sys, tempfile, unittest
import pymupdf as fitz

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SK = os.path.join(KOK, 'skills', 'ders-notu', 'scripts')
sys.path.insert(0, SK)
import hazirla


def kitap(yol, sayfa=3, cap_font='hebo', govde_font='tiro', etiket_font='helv', cap='Figure 1.%d Bir şekil başlığı.'):
    """Her sayfada: gövde metni, çizim (dikdörtgen + kısa etiketler), altında şekil başlığı, altta basılı sayfa no."""
    d = fitz.open()
    for i in range(sayfa):
        p = d.new_page()
        for k in range(6):
            p.insert_text((50, 80 + 14 * k), 'Body text line number %d of the page that is long enough.' % k, fontname=govde_font, fontsize=10)
        p.draw_rect(fitz.Rect(150, 200, 400, 380), color=(0, 0, 0), width=1)
        p.draw_line((160, 300), (390, 300), color=(0, 0, 0))
        for k, t in enumerate(('Hot fluid', 'Cold fluid', 'Wall')):
            p.insert_text((170, 230 + 40 * k), t, fontname=etiket_font, fontsize=8)
        p.insert_text((150, 400), cap % (i + 1), fontname=cap_font, fontsize=9)
        p.insert_text((300, 800), str(i + 1), fontname=govde_font, fontsize=9)   # basılı sayfa no
    d.save(yol)
    d.close()


def secim(yol, **verilen):
    d = fitz.open(yol)
    a = argparse.Namespace(cap=None, cap_font=None, label_font=None, label_len=None, pad=None)
    vars(a).update(verilen)
    return hazirla.bayrak_sec(d, list(range(1, d.page_count + 1)), a)


class BayrakSecimi(unittest.TestCase):
    def setUp(self):
        self.k = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.k)
        self.pdf = os.path.join(self.k, 'k.pdf')

    def test_kalin_baslik_varsayilan(self):
        kitap(self.pdf)
        s, neden, bulundu = secim(self.pdf)
        self.assertTrue(bulundu)
        self.assertNotIn('--cap-font', s)
        self.assertTrue(any('varsayılan' in n for n in neden))

    def test_kalin_olmayan_baslik_govdeden_farkli_yazi_tipi(self):
        kitap(self.pdf, cap_font='cour')
        s, _, _ = secim(self.pdf)
        self.assertIn('Courier', s['--cap-font'])

    def test_baslik_govdeyle_ayni_ve_kalin_degil_uyari(self):
        kitap(self.pdf, cap_font='tiro')
        s, neden, _ = secim(self.pdf)
        self.assertNotIn('--cap-font', s)
        self.assertTrue(any(n.startswith('UYARI --cap-font') for n in neden))

    def test_etiket_ayri_yazi_tipinde(self):
        kitap(self.pdf)
        s, _, _ = secim(self.pdf)
        self.assertIn('Helvetica', s['--label-font'])

    def test_etiket_govdeyle_ayni_auto(self):
        kitap(self.pdf, etiket_font='tiro')
        s, _, _ = secim(self.pdf)
        self.assertNotIn('--label-font', s)

    def test_verilen_bayrak_secimin_onune_gecer(self):
        kitap(self.pdf, cap_font='cour')
        s, neden, _ = secim(self.pdf, cap_font='Ozel', label_font='auto2')
        self.assertEqual((s['--cap-font'], s['--label-font']), ('Ozel', 'auto2'))

    def test_baslik_yok(self):
        kitap(self.pdf, cap='Picture %d without number format')
        s, neden, bulundu = secim(self.pdf)
        self.assertFalse(bulundu)
        self.assertTrue(any('BULUNAMADI' in n for n in neden))

    def test_genis_bicim_fig_buyuk_harf(self):
        kitap(self.pdf, cap='FIG. 1.%d Başlık')
        s, _, bulundu = secim(self.pdf)
        self.assertTrue(bulundu)
        self.assertEqual(s['--cap'], hazirla.GENIS_CAP)


def calistir(*arg):
    r = subprocess.run([sys.executable, '-W', 'ignore'] + list(arg), capture_output=True, text=True, encoding='utf-8',
                       env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    return r.returncode, r.stdout + r.stderr


class UcanUca(unittest.TestCase):
    def setUp(self):
        self.k = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.k)
        self.pdf = os.path.join(self.k, 'k.pdf')
        kitap(self.pdf)
        self.work = os.path.join(self.k, 'w')

    def test_hazirla_metin_ve_sekil_uretir_envanterden_yeniden_alir(self):
        kod, c = calistir(os.path.join(SK, 'hazirla.py'), self.pdf, '1-3', '--work', self.work)
        self.assertIn('AÇILACAK TEMAS SAYFALARI', c, c)
        self.assertTrue(os.path.getsize(os.path.join(self.work, 'metin.txt')))
        figs = json.load(open(os.path.join(self.work, 'figs.json')))
        self.assertEqual(sorted(figs), ['1.1', '1.2', '1.3'])
        self.assertTrue(os.path.exists(os.path.join(self.work, 'sheet_0.png')))
        # gözden geçirilip envantere kaydedilince ikinci iş tespit/kesim yapmadan alır
        calistir(os.path.join(KOK, 'ortak', 'envanter.py'), self.pdf, '--sekil-kaydet', self.work)
        w2 = os.path.join(self.k, 'w2')
        kod, c = calistir(os.path.join(SK, 'hazirla.py'), self.pdf, '1-3', '--work', w2)
        self.assertEqual(kod, 0, c)
        self.assertIn('hepsi envanterde', c)
        self.assertEqual(sorted(json.load(open(os.path.join(w2, 'figs.json')))), ['1.1', '1.2', '1.3'])

    def test_iki_aralik_det_json_birlesir(self):
        kitap(self.pdf, sayfa=5)
        calistir(os.path.join(SK, 'hazirla.py'), self.pdf, '1-2', '4-5', '--work', self.work)
        det = json.load(open(os.path.join(self.work, 'det.json')))
        self.assertEqual(sorted(det), ['0', '1', '3', '4'])


class Denetle(unittest.TestCase):
    """Örnek notu derler; denetle.py temizse 0, kural ihlalinde 1 döner."""

    def derle(self, ek=''):
        work = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, work)
        betik = open(os.path.join(KOK, 'skills', 'ders-notu', 'examples', 'ornek_ders_notu.py'), encoding='utf-8').read()
        betik = betik.replace('d.make()', ek + '\nd.make()')
        yol = os.path.join(work, 'b.py')
        open(yol, 'w', encoding='utf-8').write(betik)
        env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONPATH=SK)
        subprocess.run([sys.executable, '-W', 'ignore', yol, os.path.join(work, 'out.pdf'), work], capture_output=True, env=env, check=True)
        return work

    def test_ornek_temiz(self):
        w = self.derle()
        kod, c = calistir(os.path.join(SK, 'denetle.py'), os.path.join(w, 'out.pdf'), w)
        self.assertEqual(kod, 0, c)
        self.assertIn('OTOMATİK DENETİMLER TEMİZ', c)

    def test_ihlal_engel(self):
        w = self.derle("d.p('Aşağıdaki şekilde görülen Şekil 9.9 ile değer 0.5 m olur.')")
        kod, c = calistir(os.path.join(SK, 'denetle.py'), os.path.join(w, 'out.pdf'), w)
        self.assertEqual(kod, 1, c)
        self.assertIn('ENGEL: üslup', c)
        self.assertIn('ENGEL: anılan ama belgede olmayan şekil', c)
        self.assertIn('TESLİM EDİLEMEZ', c)

    def test_sigmayan_denklem_engel(self):
        w = self.derle("d.eq('x = (' + 'a + ' * 90 + 'b)', '(9.9)')")
        kod, c = calistir(os.path.join(SK, 'denetle.py'), os.path.join(w, 'out.pdf'), w)
        self.assertEqual(kod, 1, c)
        self.assertIn('ELLE DÜZENLENECEK DENKLEM', c)
        self.assertIn('denklem sığmıyor', c)


if __name__ == '__main__':
    unittest.main()
