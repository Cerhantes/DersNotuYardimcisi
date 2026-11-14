"""Sığmayan şekil: ardında boşluğu dolduracak metin yoksa önündeki denklemlerle yan yana alınır; olmuyorsa boşluk
kaydedilir ve denetle.py büyük boşluğu ENGEL sayar."""
import contextlib, io, json, os, shutil, subprocess, sys, tempfile, unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SK = os.path.join(KOK, 'skills', 'ders-notu', 'scripts')
sys.path.insert(0, SK)
import notlib
from reportlab.platypus import Spacer


def sekil(work, no='9.1', en=600, boy=400):
    from PIL import Image
    os.makedirs(os.path.join(work, 'fig'), exist_ok=True)
    Image.new('RGB', (en, boy), (200, 210, 225)).save(os.path.join(work, 'fig', no + '.png'))
    json.dump({no: [0, [0, 0, en, boy]]}, open(os.path.join(work, 'figs.json'), 'w'))


def derle(work, dolgu, onunde='denklem', ardinda='baslik'):
    """Sayfanın dolgu pt'lik kısmı dolu; ardından (denklem zinciri | başlık) + büyük şekil + (başlık | paragraf)."""
    d = notlib.Doc(os.path.join(work, 'o.pdf'), 'T', 'S', 'H', work, 'K')
    d.cover(['k'], ['n'])
    d.h1('1. A')
    d.raw(Spacer(1, dolgu))
    if onunde == 'denklem':
        d.p('Lehimdeki kayma gerilmesi:')
        d.eq('τ = F / A', '(1.1)')
    else:
        d.h2('1.1 Alt başlık')
    d.fig('9.1', 'Büyük şekil.', maxh=320)
    if ardinda == 'baslik':
        d.h2('1.2 Sonraki konu')
        d.p('Sonraki konunun metni.')
    else:
        d.p('Şekilden sonraki uzun metin. ' * 30)
    with contextlib.redirect_stdout(io.StringIO()):
        d.make()
    return d, json.load(open(os.path.join(work, 'derleme.json'), encoding='utf-8'))


class YanYana(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.work)
        sekil(self.work)

    def test_boslugu_yan_yerlesim_kapatir(self):
        # sayfa doluluğunu tara: yan yerleşim olan her durumda boşluk kalmaz; en az birinde yan yerleşim olur
        olan = 0
        for dolgu in range(int(notlib.FH) - 520, int(notlib.FH) - 200, 15):
            d, dr = derle(self.work, dolgu)
            if d._yan_yana:
                olan += 1
                self.assertEqual(dr['bosluk'], [], 'dolgu %d' % dolgu)
        self.assertGreater(olan, 0)

    def test_hic_buyuk_bosluk_kalmaz_ya_da_kaydedilir(self):
        # yan yerleşim sığmayan durumda da boşluk sessiz kalmaz: kaydedilir
        for dolgu in range(int(notlib.FH) - 520, int(notlib.FH) - 200, 15):
            d, dr = derle(self.work, dolgu)
            for no, sayfa, cm in dr['bosluk']:
                self.assertEqual(no, '9.1')
                self.assertGreaterEqual(cm, notlib.Doc.SEKIL_BOSLUK / notlib.cm - 0.05)

    def test_ardinda_metin_varsa_yan_yerlesim_yok(self):
        for dolgu in range(int(notlib.FH) - 520, int(notlib.FH) - 200, 30):
            d, dr = derle(self.work, dolgu, ardinda='metin')
            self.assertFalse(d._yan_yana, 'dolgu %d' % dolgu)

    def test_onunde_baslik_varsa_yan_yerlesim_yok_bosluk_kaydedilir(self):
        bulundu = False
        for dolgu in range(int(notlib.FH) - 520, int(notlib.FH) - 200, 15):
            d, dr = derle(self.work, dolgu, onunde='baslik')
            self.assertFalse(d._yan_yana)
            bulundu |= bool(dr['bosluk'])
        self.assertTrue(bulundu)


class DenetleBosluk(unittest.TestCase):
    def test_buyuk_bosluk_engel_kucugu_bilgi(self):
        work = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, work)
        ornek = os.path.join(KOK, 'skills', 'ders-notu', 'examples', 'ornek_ders_notu.py')
        env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONPATH=SK)
        subprocess.run([sys.executable, '-W', 'ignore', ornek, os.path.join(work, 'out.pdf'), work], capture_output=True, env=env, check=True)
        yol = os.path.join(work, 'derleme.json')
        dr = json.load(open(yol, encoding='utf-8'))

        def denetle(bosluk):
            dr['bosluk'] = bosluk
            json.dump(dr, open(yol, 'w', encoding='utf-8'))
            r = subprocess.run([sys.executable, '-W', 'ignore', os.path.join(SK, 'denetle.py'), os.path.join(work, 'out.pdf'), work],
                               capture_output=True, text=True, encoding='utf-8', env=env)
            return r.returncode, r.stdout

        kod, c = denetle([['15a', 12, 9.1]])
        self.assertEqual(kod, 1, c)
        self.assertIn('ENGEL: sayfa altında büyük boşluk: s.12 9.1 cm (Şekil 15a)', c)
        kod, c = denetle([['3.1', 4, 3.4]])
        self.assertNotIn('büyük boşluk', c)
        self.assertIn('küçük, bilgi', c)


if __name__ == '__main__':
    unittest.main()
