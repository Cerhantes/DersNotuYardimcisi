"""Formül kağıdı altyapısı: matplotlib mathtext ile dizilmiş formüller + reportlab kart düzeni.

İçerik betiği:
    import sys; from fslib import *
    d = Sheet(sys.argv[1], sys.argv[2], 'KONU – FORMÜL KAĞIDI', 'alt başlık (ders · kapsam)',
              'Konu – Formül Kağıdı', 'Kaynak: Yazar, Kitap, Bölüm n')
    E = d.E
    d.card('1 · Kart başlığı (English term)', [
        E(r'q=-k\\frac{dT}{dx}', '(2.1)', terms(('q', 'ısı akısı'), ('k', '...')), label='Isı akısı', note='...'),
        'serbest kısa satır (kahverengi not)',
    ] + d.tbl([[...başlık], [...satır]], [3 * cm, 2 * cm], 'Tablo başlığı'),
        fig='sema_adi', cap='şekil açıklaması')
    d.make()

Çalıştırma: PYTHONPATH=<skill>/scripts py -W ignore icerik.py <cikti.pdf> <work>
Şemalar <work>/dg/<ad>.png içinde aranır (dglib.save bunları oraya yazar).
"""
import os, re, sys, hashlib, warnings, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image as PImage
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Spacer, Image, Table, TableStyle,
                                KeepTogether, PageBreak)
from reportlab.platypus import Paragraph as _P

plt.rcParams.update({'mathtext.fontset': 'cm'})

# ---------------------------------------------------------------- yazı tipleri
# Body = Calibri/Carlito/DejaVu Sans, Math = Cambria/Caladea/DejaVu Serif (Windows, Mac, Linux) — bkz. fontlar.py
import fontlar
FONTS = fontlar.kaydet()
_body, _math = pdfmetrics.getFont('Body'), pdfmetrics.getFont('Math')
_BODY_CM, _MATH_CM = _body.face.charToGlyph, _math.face.charToGlyph
_missing = set()


def _fix_glyphs(t):
    """Metin yazı tipinde olmayan karakterleri (∛ ≫ ∝ ≈ √ ...) matematik yazı tipine geçirir."""
    out = []
    for s in re.split(r'(<[^>]+>|&#?\w+;)', t):
        if not s or s[0] in '<&':
            out.append(s); continue
        for ch in s:
            o = ord(ch)
            if o in _BODY_CM or ch in '\n\t ':
                out.append(ch)
            elif o in _MATH_CM:
                out.append('<font name="Math">%s</font>' % ch)
            else:
                out.append(ch)
                if ch not in _missing:
                    _missing.add(ch)
                    print('UYARI: "%s" (U+%04X) iki yazı tipinde de yok, kutu görünecek' % (ch, o), file=sys.stderr)
    return ''.join(out)


def Paragraph(t, *a, **k):
    return _P(_fix_glyphs(t), *a, **k)


# ---------------------------------------------------------------- düzen ve stiller
NAVY = colors.HexColor('#1F3A5F'); ACC = colors.HexColor('#C0504D'); GREY = colors.HexColor('#555555')
PAGE_W, PAGE_H = A4
LM = RM = 1.4 * cm; TM, BM = 1.9 * cm, 1.5 * cm
FW = PAGE_W - LM - RM
FH = PAGE_H - TM - BM

st_title = ParagraphStyle('t', fontName='Body-B', fontSize=20, leading=24, textColor=colors.white)
st_sub = ParagraphStyle('s', fontName='Body', fontSize=10, leading=13, textColor=colors.white)
st_card = ParagraphStyle('c', fontName='Body-B', fontSize=11.5, leading=14, textColor=colors.white)
st_terms = ParagraphStyle('tm', fontName='Body', fontSize=8.3, leading=10.4, textColor=colors.HexColor('#444444'))
st_note = ParagraphStyle('n', fontName='Body', fontSize=8.6, leading=11, textColor=colors.HexColor('#7A3B00'))
st_lab = ParagraphStyle('l', fontName='Body-B', fontSize=8.6, leading=11, textColor=NAVY, spaceAfter=1.5)
st_num = ParagraphStyle('nm', fontName='Body', fontSize=8, leading=10, textColor=GREY, alignment=2)
st_cap = ParagraphStyle('cp', fontName='Body-I', fontSize=7.6, leading=9.2, textColor=GREY, alignment=TA_CENTER)
st_cell = ParagraphStyle('cl', fontName='Body', fontSize=8.2, leading=10)
st_cellh = ParagraphStyle('ch', fontName='Body-B', fontSize=8.2, leading=10, textColor=colors.white)


def P(html, style=None):
    """Sağ sütuna ya da kart içine serbest paragraf (ör. birim dönüşümleri kutusu)."""
    return Paragraph(html, style or st_terms)


# ---------------------------------------------------------------- formül ve terim yardımcıları
_EQD = None


def eq_img(tex, fs=12.5):
    """mathtext formülünü PNG'ye çizer (önbellekli); (yol, genişlik_pt, yükseklik_pt) döndürür."""
    tex = tex.replace(r'\frac', r'\dfrac').replace(r'\ddfrac', r'\dfrac')
    key = hashlib.md5(('%s|%s' % (tex, fs)).encode()).hexdigest()[:16]
    p = os.path.join(_EQD, key + '.png')
    if not os.path.exists(p):
        fig = plt.figure(figsize=(0.01, 0.01))
        fig.text(0, 0, '$%s$' % tex, fontsize=fs)
        try:
            fig.savefig(p, dpi=500, bbox_inches='tight', pad_inches=0.02, transparent=True)
        except Exception as e:
            plt.close(fig)
            if os.path.exists(p):
                os.remove(p)
            raise ValueError('mathtext hatası: %r\n  -> %s' % (tex, str(e).splitlines()[0])) from None
        plt.close(fig)
    w, h = PImage.open(p).size
    return p, w / 500 * 72, h / 500 * 72


def sym(s):
    """'T_1' -> Cambria italik T<sub>1</sub>. Virgülle birden çok: 'T_1, T_2'. Biçim: taban[_alt][^üst]."""
    def one(tok):
        m = re.match(r'^([^_^]+)(?:_([^_^]+))?(?:\^([^_^]+))?$', tok)
        if not m:
            return tok
        b, sub, sup = m.groups()
        out = '<i>%s</i>' % b
        if sub: out += '<sub>%s</sub>' % sub
        if sup: out += '<super>%s</super>' % sup
        return out
    return '<font name="Math">%s</font>' % ', '.join(one(x) for x in s.split(', '))


def terms(*pairs):
    """terms(('q', 'ısı akısı'), ('L', 'kalınlık (m)')) -> 'q: ısı akısı · L: ...'"""
    return ' · '.join('<font color="#1F3A5F">%s</font>: %s' % (sym(a), b) for a, b in pairs)


# ---------------------------------------------------------------- belge
class Sheet(BaseDocTemplate):
    def __init__(self, out, work, title, subtitle, header, source, color='#1F3A5F'):
        global _EQD
        _EQD = os.path.join(work, 'eq'); os.makedirs(_EQD, exist_ok=True)
        self.dg = os.path.join(work, 'dg')
        super().__init__(out, pagesize=A4, leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
                         title=title, author=source)
        self.header, self.source, self.title_, self.subtitle = header, source, title, subtitle
        fr = Frame(LM, BM, FW, FH, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate('p', [fr], onPage=self._page)])
        self.story = []
        self.col = colors.HexColor(color)
        self._title()

    def _page(self, c, d):
        c.saveState(); c.setStrokeColor(NAVY); c.setLineWidth(0.6)
        c.line(LM, PAGE_H - 1.25 * cm, PAGE_W - RM, PAGE_H - 1.25 * cm)
        c.setFont('Body-B', 8.5); c.setFillColor(NAVY); c.drawString(LM, PAGE_H - 1.07 * cm, self.header)
        c.setFont('Body', 8); c.setFillColor(GREY); c.drawRightString(PAGE_W - RM, PAGE_H - 1.07 * cm, self.source)
        c.line(LM, 1.05 * cm, PAGE_W - RM, 1.05 * cm)
        c.drawCentredString(PAGE_W / 2, 0.6 * cm, 'Sayfa %d' % d.page)
        c.restoreState()

    def _title(self):
        t = Table([[Paragraph(self.title_, st_title)], [Paragraph(self.subtitle, st_sub)]], colWidths=[FW])
        t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), NAVY), ('LINEBELOW', (0, -1), (-1, -1), 3, ACC),
                               ('LEFTPADDING', (0, 0), (-1, -1), 12), ('TOPPADDING', (0, 0), (-1, 0), 9),
                               ('BOTTOMPADDING', (0, -1), (-1, -1), 9)]))
        self.story += [t, Spacer(1, 8)]

    # ---- bileşenler ----
    def E(self, tex, num='', tm=None, label=None, fs=12.5, note=None):
        """Formül bloğu: [kalın etiket] / formül ........ (no) / terimler satırı / ► not"""
        p, w, h = eq_img(tex, fs)
        return ('eq', p, w, h, num, tm, label, note, tex)

    def _fig_path(self, fig):
        if os.path.isabs(fig) or fig.lower().endswith('.png'):
            return fig
        return os.path.join(self.dg, fig + '.png')

    def card(self, title, items, fig=None, cap=None, figw=0.40, figmaxh=5.6 * cm):
        """Bir kavramın kartı. items: E(...) blokları, str (not satırı) ya da flowable (ör. d.tbl(...) elemanları).
        fig: şema adı (<work>/dg/ad.png) | png yolu | flowable listesi (tablo, P(...)) | None (tam genişlik)."""
        lw = FW * (1 - figw) if fig is not None else FW
        left = []
        for it in items:
            if isinstance(it, tuple) and it and it[0] == 'eq':
                _, p, w, h, n, tm, lab, note, tex = it
                avail = lw - 12 - 1.6 * cm
                sc = min(1.0, avail / w)
                if sc < 0.8:
                    print('UYARI: formül %%%d küçültüldü, iki satıra böl ya da fs düşür: %s' % (sc * 100, tex[:70]),
                          file=sys.stderr)
                if lab: left.append(Paragraph(lab, st_lab))
                row = Table([[Image(p, width=w * sc, height=h * sc), Paragraph(n, st_num)]],
                            colWidths=[lw - 12 - 1.6 * cm, 1.6 * cm])
                row.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('LEFTPADDING', (0, 0), (-1, -1), 4),
                                         ('RIGHTPADDING', (0, 0), (-1, -1), 0), ('TOPPADDING', (0, 0), (-1, -1), 2),
                                         ('BOTTOMPADDING', (0, 0), (-1, -1), 1)]))
                left.append(row)
                if tm: left.append(Paragraph(tm, ParagraphStyle('x', parent=st_terms, leftIndent=4)))
                if note: left.append(Paragraph('► ' + note, ParagraphStyle('y', parent=st_note, leftIndent=4)))
                left.append(Spacer(1, 3))
            elif isinstance(it, str):
                left.append(Paragraph(it, st_note)); left.append(Spacer(1, 4))
            else:
                left.append(it); left.append(Spacer(1, 4))
        body = [left]
        if fig is not None and not isinstance(fig, str):
            body.append(fig if isinstance(fig, list) else [fig])
        elif fig:
            ip = self._fig_path(fig)
            if not os.path.exists(ip):
                raise FileNotFoundError('şema yok: %s (önce şema betiğini çalıştır)' % ip)
            iw, ih = PImage.open(ip).size
            w = FW * figw - 10; h = w * ih / iw
            if h > figmaxh: h = figmaxh; w = h * iw / ih
            right = [Image(ip, width=w, height=h)]
            if cap: right += [Spacer(1, 2), Paragraph(cap, st_cap)]
            body.append(right)
        hdr = Paragraph(title, st_card)
        cw = [lw, FW - lw] if fig is not None else [FW]
        data = [[hdr] + ([''] if fig is not None else []), body]
        t = Table(data, colWidths=cw)
        sty = [('BACKGROUND', (0, 0), (-1, 0), self.col), ('SPAN', (0, 0), (-1, 0)),
               ('BOX', (0, 0), (-1, -1), 0.8, self.col), ('VALIGN', (0, 1), (-1, -1), 'TOP'),
               ('TOPPADDING', (0, 0), (-1, 0), 3), ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
               ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
               ('TOPPADDING', (0, 1), (-1, -1), 5), ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FBFCFE'))]
        if fig is not None:
            sty += [('VALIGN', (1, 1), (1, 1), 'MIDDLE'), ('LINEBEFORE', (1, 1), (1, 1), 0.4, colors.HexColor('#C8D3E0'))]
        t.setStyle(TableStyle(sty))
        _, th = t.wrap(FW, FH)
        if th > FH:
            raise ValueError('Kart bir sayfaya sığmıyor (%.0f > %.0f pt): "%s" -> iki karta böl ("... (devam)")'
                             % (th, FH, re.sub('<[^>]+>', '', title)))
        self.story += [KeepTogether([t]), Spacer(1, 9)]

    def tbl(self, rows, widths, title=None):
        """Sabitler / tipik değerler tablosu; ilk satır başlık. Liste döndürür: items'a `+ d.tbl(...)` ile ekle
        ya da fig=d.tbl(...) ile sağ sütuna koy."""
        data = [[Paragraph(str(c), st_cellh if i == 0 else st_cell) for c in r] for i, r in enumerate(rows)]
        t = Table(data, colWidths=widths)
        sty = [('BACKGROUND', (0, 0), (-1, 0), NAVY), ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#AAAAAA')),
               ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 1.5),
               ('BOTTOMPADDING', (0, 0), (-1, -1), 2), ('LEFTPADDING', (0, 0), (-1, -1), 3)]
        for i in range(2, len(rows), 2): sty.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F0F4F9')))
        t.setStyle(TableStyle(sty))
        out = []
        if title: out.append(Paragraph('<b>%s</b>' % title, ParagraphStyle('tt', parent=st_terms, textColor=NAVY)))
        out.append(t)
        return out

    def pagebreak(self):
        self.story.append(PageBreak())

    def make(self):
        self.build(self.story)
        print('ok', self.filename, 'sayfa:', self.page)
