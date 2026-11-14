"""Parçalı şekil sığmazsa parçaları okuma sırasıyla yeniden dizilir; hiçbir parça kaynak boyutunun PAKET_MIN'inin altına inmez."""
import contextlib, io, json, os, shutil, sys, tempfile, unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, 'skills', 'ders-notu', 'scripts'))
import notlib
from reportlab.platypus import Spacer
from PIL import Image

OLCU = [[169, 57], [179, 62], [186, 86]]   # Kaynak notundaki Şekil 17b'nin parçaları (pt)


def parcali_sekil(work, no='9.1', olcu=OLCU):
    """Üç satırlık (üst üste) bir slayt şekli: birleşik görüntü + fig/<no>/ parça görüntüleri."""
    os.makedirs(os.path.join(work, 'fig', no), exist_ok=True)
    w, h = max(o[0] for o in olcu), sum(o[1] for o in olcu)
    Image.new('RGB', (w * 3, h * 3), (210, 220, 235)).save(os.path.join(work, 'fig', no + '.png'))
    for k, (pw, ph) in enumerate(olcu):
        Image.new('RGB', (pw * 3, ph * 3), (40 + 60 * k, 80, 160)).save(os.path.join(work, 'fig', no, '%d.png' % k))
    json.dump(olcu, open(os.path.join(work, 'fig', no, 'parcalar.json'), 'w'))
    json.dump({no: [0, [0, 0, w, h]]}, open(os.path.join(work, 'figs.json'), 'w'))


def derle(work, dolgu, maxh=270, parcali=True):
    d = notlib.Doc(os.path.join(work, 'o.pdf'), 'T', 'S', 'H', work, 'K')
    d.cover(['k'], ['n'])
    d.h1('1. A')
    d.raw(Spacer(1, dolgu))
    d.p('Şekil 9.1 kuralları gösterir.')
    if not parcali:
        shutil.rmtree(os.path.join(work, 'fig', '9.1'), ignore_errors=True)
    d.fig('9.1', 'Parçalı şekil.', maxh=maxh)
    d.h2('1.1 Sonraki konu')
    d.p('Metin.')
    with contextlib.redirect_stdout(io.StringIO()):
        d.make()
    return d, json.load(open(os.path.join(work, 'derleme.json'), encoding='utf-8'))


class Paket(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.work)
        parcali_sekil(self.work)

    def tara(self, **k):
        return [derle(self.work, dolgu, **k) for dolgu in range(int(notlib.FH) - 330, int(notlib.FH) - 120, 12)]

    def test_yeniden_dizme_boslugu_kapatir(self):
        sonuc = self.tara()
        dizilen = [dr for d, dr in sonuc if d._dizilen]
        self.assertTrue(dizilen, 'hiçbir konumda yeniden dizilmedi')
        for dr in dizilen:
            self.assertEqual(dr['bosluk'], [])

    def test_parcasiz_sekil_yeniden_dizilmez(self):
        for d, dr in self.tara(parcali=False):
            self.assertFalse(d._dizilen)

    def test_olcek_sinirin_altina_inmez(self):
        # sınır 1'e çekilince (kaynaktan küçük olamaz) bu şekil hiçbir boşluğa yeniden dizilerek sığamaz
        eski = notlib.Doc.PAKET_MIN
        notlib.Doc.PAKET_MIN = 1.3
        try:
            for d, dr in self.tara():
                self.assertFalse(d._dizilen)
        finally:
            notlib.Doc.PAKET_MIN = eski

    def test_okuma_sirasi_korunur(self):
        # yeniden dizilen blokta parçalar 0, 1, 2 sırasıyla (soldan sağa, yukarıdan aşağı) yer alır
        for dolgu in range(int(notlib.FH) - 330, int(notlib.FH) - 120, 12):
            d, dr = derle(self.work, dolgu)
            if d._dizilen:
                break
        else:
            self.fail('yeniden dizilen konum yok')
        import pymupdf as fitz
        sayfa = fitz.open(os.path.join(self.work, 'o.pdf'))
        resimler = []
        for p in sayfa:
            for im in p.get_image_info(xrefs=True):
                r = fitz.Rect(im['bbox'])
                pix = fitz.Pixmap(sayfa, im['xref'])
                renk = pix.pixel(pix.width // 2, pix.height // 2)[0]
                resimler.append((p.number, round((r.y0 + r.y1) / 2 / 10), r.x0, renk))   # satır: dikey orta nokta
        parca = [x for x in resimler if x[3] in (40, 100, 160)]
        self.assertEqual([x[3] for x in sorted(parca)], [40, 100, 160])


if __name__ == '__main__':
    unittest.main()
