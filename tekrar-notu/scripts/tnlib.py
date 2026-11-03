"""Tekrar notu altyapısı. İçerik betiği:

    from tnlib import *
    d = start(out, work, 'KONU', 'Konu – Tekrar Notu', 'Kaynak: ... (düz metin; & yazılabilir)')
    d.cover([...kapsam satırları...], [...nasıl kullanılır...])
    d.h1('1. Başlık'); B([...]); E('Q = k A ΔT / L', '(3.1)'); F2('2.1', '2.2', 'cap a', 'cap b')
    d.make()

Tüm metin yardımcıları (B P E X BX T F F2) S() süzgecinden geçer:
  x_o -> alt simge, x_{ort} -> alt simge, x^2 / x^{-1/n} -> üst simge,
  oklar (↑↓) önceki kelimeye, '=' '≈' '<' '>' iki yanına, paragrafın son kelimesi öncekine bağlanır
  (satır sonunda yalnız "↑." ya da tek kelime kalmaz).
"""
import os, re
import notlib
from notlib import *          # Doc, ss, FW, Paragraph, Table, TableStyle, Image, KeepTogether, Spacer, colors ...

__all__ = [n for n in dir(notlib) if not n.startswith('_')] + ['start', 'S', 'B', 'P', 'E', 'X', 'BX', 'T', 'F', 'F2']

d = None
_work = None
sub2 = None


def start(out, work, title, header, source, subtitle='Tekrar Notu — konu konu bilmen gerekenler'):
    """title: kapak (BÜYÜK HARF); header: sayfa üstü sol, ör. 'Isı İletimi – Tekrar Notu'; source: sayfa üstü sağ.
    work: kaynak.py çıktısı (figs.json, fig/*.png)."""
    global d, _work, sub2
    ss['body'].fontSize, ss['body'].leading = 10.3, 13.6
    ss['bullet'].fontSize, ss['bullet'].leading, ss['bullet'].spaceAfter = 10.3, 13.6, 1.8
    ss['boxb'].fontSize, ss['boxb'].leading = 10, 13.2
    ss['toc1'].fontSize, ss['toc1'].leading = 9.8, 11.4
    ss['toc2'].fontSize, ss['toc2'].leading = 8.6, 9.6
    sub2 = ParagraphStyle('sub2', parent=ss['bullet'], leftIndent=30, bulletIndent=19)
    _work = work
    # header canvas'a düz metin olarak yazılır: &amp; değil & kullan
    d = Doc(out, title, subtitle, header, work, source.replace('&amp;', '&'))
    globals()['d'] = d
    return d


def S(t):
    if not t: return t
    t = re.sub(r'(?<=[A-Za-zα-ωΑ-Ω0-9\)|])_\{([^}]+)\}', r'<sub>\1</sub>', t)      # |_{r=R} de
    t = re.sub(r'(?<=[A-Za-zα-ωΑ-Ω\)|])_([A-Za-z0-9α-ω∞]+)', r'<sub>\1</sub>', t)   # p_∞ de
    t = re.sub(r'\^\{([^}]+)\}', r'<super>\1</super>', t)
    t = re.sub(r'\^([A-Za-z0-9\-−α-ω]+)', r'<super>\1</super>', t)   # '/' ',' '.' dahil değil: x^{1/n} yaz
    t = re.sub(r' (?=\(?[↑↓])', '&nbsp;', t)
    t = t.replace(' → ', '&nbsp;→ ')
    t = re.sub(r' ([=≈<>]|&lt;|&gt;) ', r'&nbsp;\1&nbsp;', t)
    t = re.sub(r' (?=(?:[^ <>&]|&\w+;|</?\w+>)*$)', '&nbsp;', t)
    return t


def B(items, num=False):
    """madde listesi; ('>', metin) = alt madde"""
    k = 0
    for it in items:
        if isinstance(it, tuple):
            d.story.append(Paragraph(S(it[1]), sub2, bulletText='–'))
        else:
            k += 1
            d.story.append(Paragraph(S(it), ss['bullet'], bulletText=('%d.' % k) if num else '•'))
    d.story.append(Spacer(1, 3))


def P(*ts): d.p(*[S(t) for t in ts])


def E(t, n=''):
    """numaralı denklem; iki denklemi aynı satıra yazmak için aralarına 2+ boşluk koy"""
    d.eq(re.sub(r' {2,}', '&nbsp;' * 5, S(t)), n)


def X(kind, body, title=None):
    """kutu: kind = tanim | onemli | ornek | ozet | ipucu | terim"""
    d.box(kind, [S(b) if isinstance(b, str) else b for b in (body if isinstance(body, list) else [body])], title)


def BX(kind, items, title=None):
    """madde listeli kutu"""
    st = ParagraphStyle('bb', parent=ss['boxb'], leftIndent=12, bulletIndent=2, spaceAfter=1.5)
    d.box(kind, [Paragraph(S(t), st, bulletText='•') for t in items], title)


def T(rows, widths=None, title=None, fs=None):
    """tablo; ilk satır başlık. fs: dar/çok sütunlu tabloda yazı boyu (ör. 8.4) — hücrede sayı bölünmesin"""
    f = (lambda c: '<font size="%s">%s</font>' % (fs, c)) if fs else (lambda c: c)
    d.table([[f(S(str(c))) for c in r] for r in rows], widths, S(title) if title else None)


def F(num, cap, maxh=200, scale=0.8, terms=None):
    """tek şekil (tam genişlik). İçinde küçük yazı/çok satır olan şekilde maxh büyüt (ör. 330, scale=1.0)."""
    d.fig(num, S(cap), scale=scale, maxh=maxh, terms=S(terms) if terms else None)


def F2(a, b, capa, capb, h=150):
    """iki şekil yan yana, ortak yükseklik h (pt)"""
    cells, caps = [], []
    for num, cap in ((a, capa), (b, capb)):
        pg, rc = d.figs[num]
        wpt, hpt = rc[2] - rc[0], rc[3] - rc[1]
        w = min(h * wpt / hpt, FW / 2 - 14)
        cells.append(Image(os.path.join(_work, 'fig', num + '.png'), width=w, height=w * hpt / wpt))
        caps.append(Paragraph('<b><font color="#1F3A5F">Şekil %s</font></b> – %s' % (num, S(cap)), ss['cap']))
    t = Table([cells, caps], colWidths=[FW / 2, FW / 2])
    t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, 0), 'CENTER'), ('VALIGN', (0, 0), (-1, 0), 'BOTTOM'),
                           ('VALIGN', (0, 1), (-1, 1), 'TOP'),
                           ('LINEBELOW', (0, 1), (-1, 1), 0.5, colors.HexColor('#BBBBBB')),
                           ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6)]))
    d.keep([Spacer(1, 4), t, Spacer(1, 8)])
