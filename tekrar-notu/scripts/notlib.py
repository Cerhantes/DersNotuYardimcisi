import json, os, re, sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Image,
                                Table, TableStyle, KeepTogether, PageBreak, CondPageBreak, NextPageTemplate)
from reportlab.platypus.tableofcontents import TableOfContents

# Ders notu PDF altyapısı (reportlab). İçerik betiği: from notlib import *  ->  d = Doc(...); d.h1(...); d.p(...); d.fig(...); d.make()

# Body = Carlito (repoda), Math = DejaVu Serif (matplotlib) — bkz. fontlar.py
import fontlar
FONTS = fontlar.kaydet()

NAVY = colors.HexColor('#1F3A5F')
ACC = colors.HexColor('#C0504D')
GREY = colors.HexColor('#555555')
BOXES = {
    'tanim':  ('#E8F0FA', '#2E6DB4', 'TANIM'),
    'onemli': ('#FFF3E0', '#E08A00', 'ÖNEMLİ'),
    'ornek':  ('#EAF6EC', '#2E8B57', 'ÇÖZÜMLÜ ÖRNEK'),
    'ozet':   ('#F2ECF7', '#7A4FA0', 'ÖZET'),
    'ipucu':  ('#EEF6F8', '#2A8A9E', 'İPUCU / SEZGİ'),
    'terim':  ('#F5F5F5', '#777777', 'ŞEKİLDEKİ TERİMLER'),
}

PAGE_W, PAGE_H = A4
LM = RM = 2.0 * cm
TM, BM = 2.2 * cm, 2.0 * cm
FW = PAGE_W - LM - RM
FH = PAGE_H - TM - BM

ss = {}
ss['body'] = ParagraphStyle('body', fontName='Body', fontSize=10.8, leading=15, alignment=TA_JUSTIFY, spaceAfter=5)
ss['bullet'] = ParagraphStyle('bullet', parent=ss['body'], leftIndent=16, bulletIndent=5, spaceAfter=2.5)
ss['h1'] = ParagraphStyle('h1', fontName='Body-B', fontSize=17, leading=21, textColor=NAVY, spaceBefore=6, spaceAfter=8, keepWithNext=1)
ss['h2'] = ParagraphStyle('h2', fontName='Body-B', fontSize=13.5, leading=17, textColor=NAVY, spaceBefore=9, spaceAfter=4, keepWithNext=1)
ss['h3'] = ParagraphStyle('h3', fontName='Body-B', fontSize=11.5, leading=15, textColor=ACC, spaceBefore=6, spaceAfter=2, keepWithNext=1)
ss['cap'] = ParagraphStyle('cap', fontName='Body', fontSize=9.3, leading=12, textColor=GREY, alignment=TA_JUSTIFY)
ss['eq'] = ParagraphStyle('eq', fontName='Math', fontSize=12, leading=17, alignment=TA_CENTER)
ss['eqn'] = ParagraphStyle('eqn', fontName='Body', fontSize=10, leading=17, alignment=2, textColor=GREY)
ss['boxt'] = ParagraphStyle('boxt', fontName='Body-B', fontSize=9.5, leading=12, spaceAfter=3)
ss['boxb'] = ParagraphStyle('boxb', parent=ss['body'], fontSize=10.3, leading=14, spaceAfter=3)
ss['cell'] = ParagraphStyle('cell', fontName='Body', fontSize=9.3, leading=11.5)
ss['cellh'] = ParagraphStyle('cellh', fontName='Body-B', fontSize=9.3, leading=11.5, textColor=colors.white)
ss['toc1'] = ParagraphStyle('toc1', fontName='Body-B', fontSize=10.5, leading=12.8, leftIndent=0)
ss['toc2'] = ParagraphStyle('toc2', fontName='Body', fontSize=9.3, leading=10.6, leftIndent=18)


_P = Paragraph

# Sayfa sonunda paragraf bölünürken: alt sayfada en az MIN_TAIL satır, üstte en az MIN_HEAD satır kalsın.
# Olmuyorsa paragraf bütün olarak sonraki sayfaya geçer (sonraki sayfanın başında 1-2 satırlık "artık" kalmaz).
MIN_HEAD, MIN_TAIL = 2, 3

class _BP(_P):
    def split(self, aW, aH):
        if not hasattr(self, 'blPara'): self.wrap(aW, aH)
        bp = getattr(self, 'blPara', None)
        lead = self.style.leading
        if bp is None or getattr(bp, 'kind', 0) == 1 and getattr(self.style, 'autoLeading', '') not in ('', 'off') or lead <= 0:
            return _P.split(self, aW, aH)
        n, s = len(bp.lines), int(aH / float(lead))
        if s >= n: return _P.split(self, aW, aH)
        if n - s < MIN_TAIL: s = n - MIN_TAIL
        if s < MIN_HEAD:
            del self.blPara
            return []
        return _P.split(self, aW, s * lead + 0.01)

_BODY_CM = pdfmetrics.getFont('Body').face.charToGlyph
_MATH_CM = pdfmetrics.getFont('Math').face.charToGlyph
_SYM_CM = pdfmetrics.getFont('Sym').face.charToGlyph
_missing = set()


def _fix_glyphs(t):
    """Metin yazı tipinde olmayan karakterleri (∛ ∝ ′ ≪ ...) matematik ya da yedek yazı tipine geçirir."""
    out = []
    for s in re.split(r'(<[^>]+>|&#?\w+;)', t):
        if not s or s[0] in '<&':
            out.append(s); continue
        for ch in s:
            o = ord(ch)
            if o in _BODY_CM or ch.isspace():
                out.append(ch)
            elif o in _MATH_CM:
                out.append('<font name="Math">%s</font>' % ch)
            elif o in _SYM_CM:
                out.append('<font name="Sym">%s</font>' % ch)
            else:
                out.append(ch)
                if ch not in _missing:
                    _missing.add(ch)
                    print('UYARI: "%s" (U+%04X) hiçbir yazı tipinde yok, kutu görünecek' % (ch, o), file=sys.stderr)
    return ''.join(out)


def Paragraph(t, *a, **k):
    return _BP(_fix_glyphs(t), *a, **k)


class Doc(BaseDocTemplate):
    def __init__(self, out, title, subtitle, header, work, source):
        """out: çıktı PDF; header: sayfa üstü sol yazı; work: crop_figs.py çalışma klasörü (figs.json + fig/);
        source: sayfa üstü sağ yazı, ör. 'Kaynak: <Yazar>, <Kitap adı>'"""
        super().__init__(out, pagesize=A4, leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
                         title=title, author='Ders notu – ' + source)
        self.header, self.source, self.work = header, source, work
        self.figs = json.load(open(os.path.join(work, 'figs.json')))
        fr = Frame(LM, BM, FW, FH, id='f', leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate('cover', [fr], onPage=self._cover),
                               PageTemplate('main', [fr], onPage=self._page)])
        self.story = []
        self.title_, self.subtitle = title, subtitle
        self._hn = 0

    # ---------- page decorations ----------
    def _cover(self, c, d):
        c.saveState()
        c.setFillColor(NAVY); c.rect(0, PAGE_H - 9 * cm, PAGE_W, 9 * cm, fill=1, stroke=0)
        c.setFillColor(ACC); c.rect(0, PAGE_H - 9.25 * cm, PAGE_W, 0.25 * cm, fill=1, stroke=0)
        c.restoreState()

    def _page(self, c, d):
        c.saveState()
        c.setStrokeColor(NAVY); c.setLineWidth(0.6)
        c.line(LM, PAGE_H - 1.5 * cm, PAGE_W - RM, PAGE_H - 1.5 * cm)
        c.setFont('Body', 8.5); c.setFillColor(GREY)
        c.drawString(LM, PAGE_H - 1.3 * cm, self.header)
        c.drawRightString(PAGE_W - RM, PAGE_H - 1.3 * cm, self.source)
        c.line(LM, 1.4 * cm, PAGE_W - RM, 1.4 * cm)
        c.drawCentredString(PAGE_W / 2, 0.9 * cm, str(d.page))
        c.restoreState()

    def beforeDocument(self):
        self._hn = 0

    def afterFlowable(self, fl):
        if isinstance(fl, _P) and getattr(fl, '_toc', None) is not None:
            lvl = fl._toc
            txt = fl.getPlainText()
            key = 'h%d' % self._hn; self._hn += 1
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(txt, key, level=lvl, closed=False)
            self.notify('TOCEntry', (lvl, txt, self.page, key))

    # ---------- content API ----------
    def cover(self, lines, contents):
        s = self.story
        s.append(Spacer(1, 1.2 * cm))
        s.append(Paragraph(self.title_, ParagraphStyle('ct', fontName='Body-B', fontSize=30, leading=36, textColor=colors.white)))
        s.append(Spacer(1, 0.4 * cm))
        s.append(Paragraph(self.subtitle, ParagraphStyle('cs', fontName='Body', fontSize=15, leading=20, textColor=colors.white)))
        s.append(Spacer(1, 4.3 * cm))
        for l in lines:
            s.append(Paragraph(l, ParagraphStyle('cl', parent=ss['body'], fontSize=11.5, leading=16, alignment=TA_LEFT)))
        s.append(Spacer(1, 0.6 * cm))
        self.box('ipucu', contents, title='BU NOTU NASIL KULLANMALISIN?')
        s.append(NextPageTemplate('main'))
        s.append(PageBreak())
        s.append(Paragraph('İçindekiler', ss['h1']))
        toc = TableOfContents(); toc.levelStyles = [ss['toc1'], ss['toc2']]
        toc.dotsMinLevel = 0
        # reportlab varsayılanı her satıra 3+3 pt dolgu ekler; tek sayfaya sığması için daralt
        toc.tableStyle = TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 0),
                                     ('RIGHTPADDING', (0, 0), (-1, -1), 0), ('TOPPADDING', (0, 0), (-1, -1), 1),
                                     ('BOTTOMPADDING', (0, 0), (-1, -1), 1)])
        s.append(toc)
        s.append(PageBreak())

    def _hp(self, txt, st, lvl):
        p = Paragraph(txt, st); p._toc = lvl; return p

    def h1(self, t, newpage=False, need=9):
        if newpage: self.story.append(PageBreak())
        else: self.story.append(CondPageBreak(need * cm))
        self.story.append(self._hp(t, ss['h1'], 0))

    def h2(self, t, need=6):
        self.story.append(CondPageBreak(need * cm))
        self.story.append(self._hp(t, ss['h2'], 1))

    def h3(self, t):
        self.story.append(CondPageBreak(3.5 * cm))
        self.story.append(Paragraph(t, ss['h3']))

    def p(self, *ts):
        for t in ts: self.story.append(Paragraph(t, ss['body']))

    def bl(self, items, num=False):
        for i, t in enumerate(items):
            b = '%d.' % (i + 1) if num else '•'
            self.story.append(Paragraph(t, ss['bullet'], bulletText=b))
        self.story.append(Spacer(1, 3))

    @staticmethod
    def _wrapcheck(p, width, n):
        # denklem satıra sığmazsa derleme sırasında uyar (bölüp iki d.eq satırı yaz ya da sadeleştir)
        p.wrap(width, 10000)
        bp = getattr(p, 'blPara', None)
        if bp is not None and len(bp.lines) > 1:
            print('UYARI denklem tek satıra sığmadı %s: %s' % (n, p.getPlainText()[:70]))

    def eq(self, t, n=''):
        nw = 2.2 * cm   # '(6.16–6.18)' gibi aralık numaraları için
        pe = Paragraph(t, ss['eq'])
        self._wrapcheck(pe, FW - 2 * nw - 12, n)
        tb = Table([[Paragraph('', ss['eqn']), pe, Paragraph(n, ss['eqn'])]],
                   colWidths=[nw, FW - 2 * nw, nw])
        tb.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 2),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
        self.story.append(tb)

    def _boxflow(self, kind, body, title=None):
        bg, fg, lab = BOXES[kind]
        inner = [Paragraph('<font color="%s">%s</font>' % (fg, title or lab), ss['boxt'])]
        for b in (body if isinstance(body, list) else [body]):
            if isinstance(b, str): inner.append(Paragraph(b, ss['boxb']))
            else: inner.append(b)
        t = Table([[inner]], colWidths=[FW])
        t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(bg)),
                               ('LINEBEFORE', (0, 0), (0, -1), 3.5, colors.HexColor(fg)),
                               ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                               ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
        return t

    def box(self, kind, body, title=None):
        self.story.append(Spacer(1, 3))
        self.story.append(self._boxflow(kind, body, title))
        self.story.append(Spacer(1, 7))

    def beq(self, t, n=''):
        """equation flowable for use inside boxes"""
        p = Paragraph(t + ('&nbsp;&nbsp;&nbsp;<font name="Body" size="9" color="#555555">%s</font>' % n if n else ''), ss['eq'])
        self._wrapcheck(p, FW - 32, n)
        return p

    def fig(self, num, cap, scale=1.0, maxw=None, maxh=320, terms=None, keep=None):
        pg, rc = self.figs[num]
        wpt, hpt = rc[2] - rc[0] + 10, rc[3] - rc[1] + 10
        w = wpt * 0.92 * scale
        w = min(w, maxw or FW)
        h = w * hpt / wpt
        if h > maxh: h = maxh; w = h * wpt / hpt
        img = Image(os.path.join(self.work, 'fig', num + '.png'), width=w, height=h)
        capt = '<b><font color="#1F3A5F">Şekil %s</font></b> – %s' % (num, cap)
        if terms: capt += '<br/><font color="#777777"><i>Şekildeki terimler:</i> %s</font>' % terms
        ct = Table([[img], [Paragraph(capt, ss['cap'])]], colWidths=[min(FW, max(w + 20, 12 * cm))])
        ct.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('LINEBELOW', (0, 1), (-1, 1), 0.5, colors.HexColor('#BBBBBB')),
                                ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 1), (-1, 1), 6)]))
        flow = [Spacer(1, 4), ct, Spacer(1, 8)]
        if keep:  # keep figure together with some preceding/following paragraph text
            flow = keep(flow)
        self.keep(flow)

    def _heads(self):
        """story sonundaki başlıkları (keepWithNext'li paragraflar) çıkarıp döndürür."""
        h, cpb = [], None
        while self.story:
            f = self.story[-1]
            if isinstance(f, _P) and getattr(f.style, 'keepWithNext', 0): h.insert(0, self.story.pop())
            elif isinstance(f, CondPageBreak) and h: cpb = self.story.pop()   # h1 ile h2 arasındaki CondPageBreak
            else: break
        if cpb is not None: self.story.append(cpb)   # en üstteki "yer yoksa sayfa atla" geri konur
        return h

    def keep(self, flow):
        """flow'u tek parça tut; hemen önündeki başlıkları da içine al. (reportlab'in keepWithNext'i
        KeepTogether'a bağlanmaz: başlık + şekil/tablo varsa başlık sayfa sonunda yalnız kalabiliyordu.)"""
        self.story.append(KeepTogether(self._heads() + list(flow)))

    def table(self, rows, widths=None, title=None, small=False):
        data = []
        for i, r in enumerate(rows):
            st = ss['cellh'] if i == 0 else ss['cell']
            data.append([Paragraph(str(c), st) for c in r])
        if widths: widths = [w * FW for w in widths]
        t = Table(data, colWidths=widths, repeatRows=1)
        sty = [('BACKGROUND', (0, 0), (-1, 0), NAVY), ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#AAAAAA')),
               ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]
        for i in range(1, len(rows)):
            if i % 2 == 0: sty.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F0F4F9')))
        t.setStyle(TableStyle(sty))
        fl = [Spacer(1, 3)]
        if title: fl.append(Paragraph('<b><font color="#1F3A5F">%s</font></b>' % title, ss['cap']))
        fl += [Spacer(1, 2)]
        th = t.wrap(FW, FH)[1]
        if th <= FH / 3:      # kısa tablo: tek parça
            self.keep(fl + [t, Spacer(1, 9)])
            return
        # uzun tablo: bütün olarak taşınırsa sayfa altında büyük boşluk kalır -> satırlardan bölünsün
        # (başlık satırı yeni sayfada tekrar eder). Başlıklar + tablo adı + ilk 3 satır aynı sayfada kalsın.
        heads = self._heads()
        need = sum(f.wrap(FW, FH)[1] for f in heads + fl) + sum(t._rowHeights[:4]) + 12
        self.story.append(CondPageBreak(need))
        self.story.append(KeepTogether(heads + fl + [Spacer(1, 0.1)]) if heads else KeepTogether(fl))
        self.story += [t, Spacer(1, 9)]

    def raw(self, f): self.story.append(f)

    def begin_keep(self): self._kstart = len(self.story)

    def end_keep(self):
        k = self.story[self._kstart:]; del self.story[self._kstart:]
        # blok içindeki CondPageBreak'ler (h2/h3'ün "yer yoksa sayfa atla"sı) KeepTogether içinde
        # yanlış ölçülüp gereksiz sayfa atlatır; bloğu bir bütün olarak öne al, ayrıca başına ekle
        need = sum(f.height for f in k if isinstance(f, CondPageBreak))
        k = [f for f in k if not isinstance(f, CondPageBreak)]
        if need: self.story.append(CondPageBreak(need))
        self.keep(k)

    def make(self):
        self.multiBuild(self.story)
