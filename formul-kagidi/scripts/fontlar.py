"""Yazı tiplerini reportlab'e kaydeder. Kullanıcının yazı tipi kurması gerekmez; çıktı her makinede aynıdır.

  Metin (Body):      Carlito       repoda: ortak/fonts/ (Calibri ile aynı ölçüler, OFL lisanslı)
  Matematik (Math):  DejaVu Serif  matplotlib ile gelir
  Yedek (Sym):       DejaVu Sans   matplotlib ile gelir; ilk ikisinde olmayan simgeler için (≪ ≫ ∅ ≅ ...)
"""
import os


def kaydet(body='Body', math='Math'):
    """Body/Body-B/Body-I/Body-BI, Math/Math-I/Math-B ve Sym adlarıyla kaydeder; aile adlarını döndürür."""
    import matplotlib
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.fonts import addMapping

    fonts = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'ortak', 'fonts')
    mpl = os.path.join(matplotlib.get_data_path(), 'fonts', 'ttf')
    for ad, klasor, dosya in (
        (body, fonts, 'Carlito-Regular.ttf'), (body + '-B', fonts, 'Carlito-Bold.ttf'),
        (body + '-I', fonts, 'Carlito-Italic.ttf'), (body + '-BI', fonts, 'Carlito-BoldItalic.ttf'),
        (math, mpl, 'DejaVuSerif.ttf'), (math + '-I', mpl, 'DejaVuSerif-Italic.ttf'),
        (math + '-B', mpl, 'DejaVuSerif-Bold.ttf'), ('Sym', mpl, 'DejaVuSans.ttf'),
    ):
        pdfmetrics.registerFont(TTFont(ad, os.path.join(klasor, dosya)))
    addMapping(body, 0, 0, body); addMapping(body, 1, 0, body + '-B')
    addMapping(body, 0, 1, body + '-I'); addMapping(body, 1, 1, body + '-BI')
    addMapping(math, 0, 0, math); addMapping(math, 0, 1, math + '-I')
    addMapping(math, 1, 0, math + '-B'); addMapping(math, 1, 1, math + '-B')
    return 'Carlito', 'DejaVu Serif'
