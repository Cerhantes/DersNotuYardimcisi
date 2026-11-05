import json, os, shutil, sys, tempfile, unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, 'ortak'))
import envanter


def kur(yer, sekiller):
    os.makedirs(os.path.join(yer, 'fig'), exist_ok=True)
    for no in sekiller:
        open(os.path.join(yer, 'fig', no + '.png'), 'wb').write(b'x')
    json.dump(sekiller, open(os.path.join(yer, 'figs.json'), 'w'))


class SekilTest(unittest.TestCase):
    def setUp(self):
        self.kok = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.kok)
        self.is_, self.env = os.path.join(self.kok, 'is'), os.path.join(self.kok, 'env')

    def test_kaydet_figs_birlesir(self):
        kur(self.env, {'1.1': [0, [0, 0, 1, 1]]})
        kur(self.is_, {'2.1': [5, [0, 0, 2, 2]]})
        envanter.sekil_kopya(self.is_, self.env)
        self.assertEqual(set(json.load(open(os.path.join(self.env, 'figs.json')))), {'1.1', '2.1'})
        self.assertEqual(sorted(os.listdir(os.path.join(self.env, 'fig'))), ['1.1.png', '2.1.png'])

    def test_kaydet_cakismada_kaynak_kazanir(self):
        kur(self.env, {'1.1': [0, [0, 0, 1, 1]]})
        kur(self.is_, {'1.1': [9, [0, 0, 9, 9]]})
        envanter.sekil_kopya(self.is_, self.env)
        self.assertEqual(json.load(open(os.path.join(self.env, 'figs.json')))['1.1'][0], 9)

    def test_yalniz_istenen_numara_kaydedilir(self):
        kur(self.env, {'1.1': [0, [0, 0, 1, 1]]})
        kur(self.is_, {'1.1': [9, [0, 0, 9, 9]], '2.1': [5, [0, 0, 2, 2]]})
        envanter.sekil_kopya(self.is_, self.env, yalniz=['2.1'])
        figs = json.load(open(os.path.join(self.env, 'figs.json')))
        self.assertEqual(figs['1.1'][0], 0)
        self.assertEqual(figs['2.1'][0], 5)

    def test_numara_bul(self):
        import pymupdf as fitz
        d = fitz.open()
        for yazi in ('Bkz. Eq. (8.30) ve Table 8.4 atif', 'Giris\nT = V a,\n(8.30)\nFIGURE 8.21 Egri', 'TABLE 8.4\nDegerler', 'FIGURE 8.210 Baska\n(8.301)'):
            d.new_page().insert_text((50, 50), yazi)
        bulunan = envanter.numara_bul(d, ['8.30', '8.4', '8.21', '9.9'])
        self.assertEqual(bulunan['8.21'], [2])
        self.assertEqual(bulunan['8.4'], [3])
        self.assertIn(2, bulunan['8.30'])
        self.assertNotIn(4, bulunan['8.30'])
        self.assertEqual(bulunan['9.9'], [])

    def test_eksik(self):
        kur(self.env, {'1.1': [0, [0, 0, 1, 1]]})
        self.assertEqual(envanter.sekil_eksik(self.env, ['1.1', '9.9']), ['9.9'])

    def test_figs_yokken_eksik(self):
        os.makedirs(self.env)
        self.assertEqual(envanter.sekil_eksik(self.env, ['1.1']), ['1.1'])


if __name__ == '__main__':
    unittest.main()
