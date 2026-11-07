"""ortak/sekil_kenar.py ve ortak/pptx_slayt.py."""
import io, os, shutil, subprocess, sys, tempfile, unittest, zipfile

from PIL import Image, ImageDraw

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORTAK = os.path.join(KOK, 'ortak')
sys.path.insert(0, ORTAK)
import sekil_kenar


def calistir(*arg):
    r = subprocess.run([sys.executable, '-W', 'ignore'] + list(arg), capture_output=True, text=True, encoding='utf-8')
    return r.returncode, r.stdout + r.stderr


class SekilKenarTest(unittest.TestCase):
    def setUp(self):
        self.k = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.k)

    def png(self, ad, ciz):
        im = Image.new('RGB', (200, 100), 'white')
        ciz(ImageDraw.Draw(im))
        yol = os.path.join(self.k, ad + '.png')
        im.save(yol)
        return yol

    def test_ortada_kalan_sekil_temiz(self):
        yol = self.png('temiz', lambda d: d.rectangle([20, 20, 180, 80], outline='black', width=3))
        self.assertEqual(sekil_kenar.kenarlar(yol), {})

    def test_kesik_yazi_kenarda_yakalanir(self):
        yol = self.png('kesik', lambda d: d.rectangle([150, 40, 199, 60], fill='black'))
        self.assertEqual(list(sekil_kenar.kenarlar(yol)), ['sag'])

    def test_tek_nokta_gurultu_sayilmaz(self):
        yol = self.png('nokta', lambda d: d.point((0, 50), fill='black'))
        self.assertEqual(sekil_kenar.kenarlar(yol), {})

    def test_klasor_ciktisi(self):
        self.png('a', lambda d: d.rectangle([20, 20, 180, 80], outline='black'))
        self.png('b', lambda d: d.rectangle([0, 0, 199, 5], fill='black'))
        kod, cikti = calistir(os.path.join(ORTAK, 'sekil_kenar.py'), self.k)
        self.assertEqual(kod, 0)
        self.assertIn('KENAR: b:', cikti)
        self.assertNotIn('KENAR: a', cikti)


def _png(renk):
    b = io.BytesIO()
    Image.new('RGB', (40, 20), renk).save(b, 'PNG')
    return b.getvalue()


def _pptx(yol):
    """İki slaytlı en küçük sunum; sunum sırası dosya numarasının tersidir."""
    P = 'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
    REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    with zipfile.ZipFile(yol, 'w') as z:
        z.writestr('ppt/presentation.xml', '<p:presentation %s><p:sldIdLst><p:sldId id="256" r:id="rId2"/><p:sldId id="257" r:id="rId1"/></p:sldIdLst>'
                   '<p:sldSz cx="9144000" cy="6858000"/></p:presentation>' % P)
        z.writestr('ppt/_rels/presentation.xml.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="%s/slide" Target="slides/slide1.xml"/><Relationship Id="rId2" Type="%s/slide" Target="slides/slide2.xml"/></Relationships>' % (REL, REL))
        z.writestr('ppt/slides/slide1.xml', '<p:sld %s><p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>BIRINCI DOSYA</a:t></a:r></a:p></p:txBody></p:sp>'
                   '<p:pic><p:blipFill><a:blip r:embed="rId1"/></p:blipFill><p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="4572000" cy="3429000"/></a:xfrm></p:spPr></p:pic>'
                   '</p:spTree></p:cSld></p:sld>' % P)
        z.writestr('ppt/slides/_rels/slide1.xml.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="%s/image" Target="../media/image1.png"/></Relationships>' % REL)
        z.writestr('ppt/slides/slide2.xml', '<p:sld %s><p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>ILK SLAYT</a:t></a:r></a:p></p:txBody></p:sp>'
                   '</p:spTree></p:cSld></p:sld>' % P)
        z.writestr('ppt/media/image1.png', _png('red'))


class PptxSlaytTest(unittest.TestCase):
    def setUp(self):
        self.k = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.k)
        self.pptx = os.path.join(self.k, 'sunum.pptx')
        _pptx(self.pptx)
        kod, self.cikti = calistir(os.path.join(ORTAK, 'pptx_slayt.py'), self.pptx, os.path.join(self.k, 'o'), '--genislik', '400')
        self.assertEqual(kod, 0, self.cikti)

    def test_sunum_sirasi_ve_metin(self):
        t = open(os.path.join(self.k, 'o', 'slaytlar.txt'), encoding='utf-8').read()
        self.assertLess(t.index('ILK SLAYT'), t.index('BIRINCI DOSYA'))
        self.assertIn('=== 01 ===\nILK SLAYT', t)

    def test_resim_konumuna_yerlesir(self):
        im = Image.open(os.path.join(self.k, 'o', 's_02.png')).convert('RGB')
        self.assertEqual(im.size, (400, 300))
        self.assertEqual(im.getpixel((100, 100)), (255, 0, 0))    # resim sol üst çeyrekte
        self.assertEqual(im.getpixel((300, 250)), (255, 255, 255))



import drive_klasor as dk

_SAYFA = {
    'KOK': '<div class="flip-entry" id="entry-ALT1" tabindex="0"><div><a href="https://drive.google.com/drive/folders/ALT1"><div class="flip-entry-title">Vize &amp; 1</div></a></div></div>'
           '<div class="flip-entry" id="entry-F1" tabindex="0"><div><a href="https://drive.google.com/file/d/F1/view"><div class="flip-entry-title">genel.pdf</div></a></div></div>',
    'ALT1': '<div class="flip-entry" id="entry-F2" tabindex="0"><div><a href="https://drive.google.com/file/d/F2/view"><div class="flip-entry-title">2014 sınav.pdf</div></a></div></div>',
}


class DriveKlasorTest(unittest.TestCase):
    def test_baglantidan_id(self):
        self.assertEqual(dk.klasor_id('https://drive.google.com/drive/u/0/folders/1abc-XY_z?usp=sharing'), '1abc-XY_z')
        self.assertEqual(dk.klasor_id('1abc'), '1abc')

    def test_alt_klasorler_gezilir(self):
        getir = lambda url: _SAYFA.get(url.rsplit('=', 1)[1], '')
        t = dk.tara('KOK', getir=getir)
        self.assertEqual([(x['yol'], x['ad']) for x in t], [('/Vize & 1', '2014 sınav.pdf'), ('', 'genel.pdf')])


if __name__ == '__main__':
    unittest.main()
