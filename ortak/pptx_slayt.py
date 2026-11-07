"""PowerPoint (.pptx) slaytlarını python-pptx ve PowerPoint olmadan okur.

python -W ignore pptx_slayt.py <sunum.pptx> <çıktı klasörü> [--genislik 2200] [--onek s]

Çıktı:
  <onek>_<nn>.png   her slayt, sunum sırasıyla: slayttaki resimler pptx'teki konum, boyut ve kırpımlarıyla yerleştirilir
  slaytlar.txt      her slaydın metin kutuları: '=== <nn> ===' ve altında metin
Metin kutuları ve vektör şekiller PNG'ye çizilmez: yalnız metin içeren slayt boş görünür, metni slaytlar.txt'tedir.
El yazısı ve taranmış sorular çoğunlukla resim olduğundan PNG'de görünür; metni yoktur, görerek okunur.
EMF/WMF resim okunamazsa 'OKUNAMADI' yazılır, o slayt eksik çizilir.
"""
import argparse, io, os, posixpath, re, sys, zipfile
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw

NS = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
RID = '{%s}id' % NS['r']
EMBED = '{%s}embed' % NS['r']


def _rels(z, parca):
    """parca'nın ilişki dosyası: {Id: zip içindeki tam yol}."""
    klasor, ad = posixpath.split(parca)
    yol = posixpath.join(klasor, '_rels', ad + '.rels')
    if yol not in z.namelist():
        return {}
    kok = ET.fromstring(z.read(yol))
    return {r.get('Id'): posixpath.normpath(posixpath.join(klasor, r.get('Target'))) for r in kok}


def slaytlar(z):
    """Sunum sırasıyla slayt parça yolları (dosya adındaki numara sırası değil)."""
    pr = ET.fromstring(z.read('ppt/presentation.xml'))
    rel = _rels(z, 'ppt/presentation.xml')
    return [rel[s.get(RID)] for s in pr.iter('{%s}sldId' % NS['p'])]


def metin(kok):
    satir = []
    for par in kok.iter('{%s}p' % NS['a']):
        t = ''.join(x.text or '' for x in par.iter('{%s}t' % NS['a'])).strip()
        if t:
            satir.append(t)
    return '\n'.join(satir)


def ciz(z, parca, W, H, genislik):
    s = genislik / W
    tuval = Image.new('RGB', (genislik, int(H * s)), 'white')
    rel = _rels(z, parca)
    hatalar = []
    for pic in ET.fromstring(z.read(parca)).iter('{%s}pic' % NS['p']):
        bl, off, ext = pic.find('.//a:blip', NS), pic.find('.//a:xfrm/a:off', NS), pic.find('.//a:xfrm/a:ext', NS)
        if bl is None or off is None or ext is None or bl.get(EMBED) not in rel:
            continue
        hedef = rel[bl.get(EMBED)]
        try:
            im = Image.open(io.BytesIO(z.read(hedef)))
            if hedef.lower().endswith(('.emf', '.wmf')):
                im.load(dpi=200)
            im = im.convert('RGBA')
        except Exception as e:
            hatalar.append('%s (%s)' % (posixpath.basename(hedef), e))
            continue
        sr = pic.find('.//a:srcRect', NS)
        if sr is not None:
            l, t, r, b = [int(sr.get(k, 0)) / 100000 for k in 'ltrb']
            im = im.crop((int(im.width * l), int(im.height * t), int(im.width * (1 - r)), int(im.height * (1 - b))))
        x, y, w, h = [int(v) * s for v in (off.get('x'), off.get('y'), ext.get('cx'), ext.get('cy'))]
        im = im.resize((max(int(w), 1), max(int(h), 1)))
        tuval.paste(im, (int(x), int(y)), im)
    return tuval, hatalar


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pptx'); ap.add_argument('out')
    ap.add_argument('--genislik', type=int, default=2200)
    ap.add_argument('--onek', default='s')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    z = zipfile.ZipFile(a.pptx)
    sz = ET.fromstring(z.read('ppt/presentation.xml')).find('p:sldSz', NS)
    W, H = int(sz.get('cx')), int(sz.get('cy'))
    yazi = []
    liste = slaytlar(z)
    for i, parca in enumerate(liste, 1):
        tuval, hatalar = ciz(z, parca, W, H, a.genislik)
        ImageDraw.Draw(tuval).text((4, 2), '%s-%d' % (a.onek, i), fill='red')
        tuval.save(os.path.join(a.out, '%s_%02d.png' % (a.onek, i)))
        for h in hatalar:
            print('OKUNAMADI: slayt %d: %s' % (i, h))
        yazi.append('=== %02d ===\n%s' % (i, metin(ET.fromstring(z.read(parca)))))
    open(os.path.join(a.out, 'slaytlar.txt'), 'w', encoding='utf-8').write('\n'.join(yazi) + '\n')
    print('%d slayt -> %s' % (len(liste), a.out))


if __name__ == '__main__':
    main()
