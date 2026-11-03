"""Yazı tiplerini işletim sisteminden bağımsız bulup reportlab'e kaydeder.

Sıra (ilk tam bulunan aile kullanılır):
  Metin (Body):       Calibri  -> Carlito (Calibri ile aynı ölçüler)  -> DejaVu Sans
  Matematik (Math):   Cambria  -> DejaVu Serif   (Caladea'da Yunan harfleri yok, kullanılmaz)
Calibri/Cambria: Windows'ta hazır; Mac'te Microsoft Office kuruluysa uygulama içinden bulunur.
Mac'te Office yoksa Calibri ile birebir aynı sayfa düzeni için:  brew install --cask font-carlito
DejaVu, matplotlib ile birlikte gelir (son çare; metin DejaVu olursa düzen biraz değişir).
"""
import os, sys, glob

DIRS = [
    'C:/Windows/Fonts',
    os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'Fonts'),
    os.path.expanduser('~/Library/Fonts'), '/Library/Fonts', '/System/Library/Fonts',
    '/System/Library/Fonts/Supplemental',
    *glob.glob('/Applications/Microsoft *.app/Contents/Resources/DFonts'),
    os.path.expanduser('~/.fonts'), os.path.expanduser('~/.local/share/fonts'),
    '/usr/share/fonts', '/usr/local/share/fonts',
]

BODY = [  # (ad, normal, kalın, italik, kalın-italik)
    ('Calibri', 'calibri.ttf', 'calibrib.ttf', 'calibrii.ttf', 'calibriz.ttf'),
    ('Carlito', 'Carlito-Regular.ttf', 'Carlito-Bold.ttf', 'Carlito-Italic.ttf', 'Carlito-BoldItalic.ttf'),
    ('DejaVu Sans', 'DejaVuSans.ttf', 'DejaVuSans-Bold.ttf', 'DejaVuSans-Oblique.ttf', 'DejaVuSans-BoldOblique.ttf'),
]
MATH = [  # (ad, normal, italik, kalın)
    ('Cambria', 'cambria.ttc|0', 'cambriai.ttf', 'cambriab.ttf'),
    ('DejaVu Serif', 'DejaVuSerif.ttf', 'DejaVuSerif-Italic.ttf', 'DejaVuSerif-Bold.ttf'),
]
# İlk aile (Calibri/Cambria) dışındaki ailelerde bu karakterler yoksa aile atlanır (kutucuk çıkmasın)
NEED_BODY = 'çğıöşüÇĞİÖŞÜ→↑↓≈≤≥±×·°'
NEED_MATH = 'αβγδθλμπστφωΔΣ√∞∂∫≈≤≥±×·'

_index = None


def _build_index():
    idx = {}
    dirs = list(DIRS)
    try:
        import matplotlib
        dirs.append(os.path.join(matplotlib.get_data_path(), 'fonts', 'ttf'))
    except Exception:
        pass
    for d in dirs:
        if not d or not os.path.isdir(d):
            continue
        for root, _, files in os.walk(d):
            for f in files:
                idx.setdefault(f.lower(), os.path.join(root, f))
    return idx


def _find(spec):
    name, _, sub = spec.partition('|')
    p = _index.get(name.lower())
    return (p, int(sub) if sub else None) if p else None


def _covers(ttf, chars):
    cmap = ttf.face.charToGlyph
    return all(ord(c) in cmap for c in chars)


def _family(cands, need):
    from reportlab.pdfbase.ttfonts import TTFont
    for i, (name, *files) in enumerate(cands):
        found = [_find(f) for f in files]
        if not all(found):
            continue
        fonts = []
        for p, sub in found:
            fonts.append(TTFont('_probe', p, subfontIndex=sub) if sub is not None else TTFont('_probe', p))
        if i > 0 and not _covers(fonts[0], need):
            continue
        return name, found
    return None, None


def kaydet(body='Body', math='Math'):
    """Body/Body-B/Body-I/Body-BI ve Math/Math-I/Math-B adlarıyla kaydeder; seçilen aile adlarını döndürür."""
    global _index
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.fonts import addMapping
    if _index is None:
        _index = _build_index()

    def reg(n, ps):
        p, sub = ps
        pdfmetrics.registerFont(TTFont(n, p, subfontIndex=sub) if sub is not None else TTFont(n, p))

    bname, b = _family(BODY, NEED_BODY)
    mname, m = _family(MATH, NEED_MATH)
    if not b or not m:
        raise FileNotFoundError('Yazı tipi bulunamadı. `pip install matplotlib` (DejaVu için) ya da '
                                'Mac: `brew install --cask font-carlito`')
    for n, ps in zip((body, body + '-B', body + '-I', body + '-BI'), b): reg(n, ps)
    for n, ps in zip((math, math + '-I', math + '-B'), m): reg(n, ps)
    addMapping(body, 0, 0, body); addMapping(body, 1, 0, body + '-B')
    addMapping(body, 0, 1, body + '-I'); addMapping(body, 1, 1, body + '-BI')
    addMapping(math, 0, 0, math); addMapping(math, 0, 1, math + '-I')
    addMapping(math, 1, 0, math + '-B'); addMapping(math, 1, 1, math + '-B')
    if bname != 'Calibri' or mname != 'Cambria':
        msg = 'Yazı tipi: metin=%s, matematik=%s' % (bname, mname)
        if bname.startswith('DejaVu'):
            msg += ' (Calibri/Carlito yok: sayfa düzeni biraz farklı olur. Mac: brew install --cask font-carlito)'
        print(msg, file=sys.stderr)
    return bname, mname
