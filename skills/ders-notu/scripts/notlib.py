import json, os, re, sys, unicodedata
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
from reportlab.platypus import paraparser
from reportlab.platypus.flowables import _listWrapOn

# Varsayılan 0,5 ile alt simge alt satıra ve noktalamaya, üst simge üst satıra çarpıyor
paraparser.subFraction = 0.22
paraparser.supFraction = 0.42

# Ders notu PDF altyapısı (reportlab). İçerik betiği: from notlib import *  ->  d = Doc(...); d.h1(...); d.p(...); d.fig(...); d.make()

# Yazı tipi ve renk teması ortak/ klasöründe (bkz. ortak/fontlar.py, ortak/tema.py)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'ortak'))
import fontlar
from tema import Tema
FONTS = fontlar.kaydet()

GREY = colors.HexColor('#555555')
KOYU = colors.HexColor('#333333')
CIZGI = colors.HexColor('#BBBBBB')
BOXES = {
    'tanim':  ('#E8F0FA', '#2E6DB4', 'TANIM'),
    'onemli': ('#FFF3E0', '#E08A00', 'ÖNEMLİ'),
    'ornek':  ('#EAF6EC', '#2E8B57', 'ÇÖZÜMLÜ ÖRNEK'),
    'ozet':   (None, None, 'ÖZET'),   # o anki konunun rengi
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
ss['h1'] = ParagraphStyle('h1', fontName='Body-B', fontSize=17, leading=21, textColor=KOYU, spaceBefore=6, spaceAfter=8, keepWithNext=1)
ss['h2'] = ParagraphStyle('h2', fontName='Body-B', fontSize=13.5, leading=17, textColor=KOYU, spaceBefore=9, spaceAfter=4, keepWithNext=1)
ss['h3'] = ParagraphStyle('h3', fontName='Body-B', fontSize=11.5, leading=15, textColor=KOYU, spaceBefore=6, spaceAfter=2, keepWithNext=1)
ss['cap'] = ParagraphStyle('cap', fontName='Body', fontSize=9.3, leading=12, textColor=GREY, alignment=TA_JUSTIFY)
ss['eq'] = ParagraphStyle('eq', fontName='Math', fontSize=12, leading=17, alignment=TA_CENTER)
ss['eqn'] = ParagraphStyle('eqn', fontName='Body', fontSize=10, leading=17, alignment=2, textColor=GREY)
_CEQ = ParagraphStyle('ceq', parent=ss['eq'], fontSize=10.8, leading=15.5)   # cozum() adım denklemleri
_KFS = ParagraphStyle('kfs', parent=ss['cap'], alignment=TA_CENTER, fontSize=8.8, leading=10.5)
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
ZINCIR = 8   # sayfada birlikte tutulan en uzun denklem zinciri

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


def _buyuk_nokta(t, stil=None):
    """Birleşen nokta küçük harfe göre durur, DejaVu Serif büyük harfinde gövdenin içine düşer.
    Hazır karakteri olan (Ė) ona iner; olmayan (Q̇, V̇) noktanın oturduğu metin yazı tipine geçer,
    bulunduğu yerin kalın ve eğik hali korunur."""
    ad = getattr(stil, 'fontName', '')
    kalin, egik = int(ad in ('Body-B', 'Body-BI')), int(ad in ('Body-I', 'Body-BI'))
    out = []
    for s in re.split(r'(<[^>]+>)', t):
        if s[:1] == '<':
            etiket = s.lower()
            kalin += {'<b>': 1, '</b>': -1}.get(etiket, 0)
            egik += {'<i>': 1, '</i>': -1}.get(etiket, 0)
            out.append(s); continue
        ek = ('B' if kalin > 0 else '') + ('I' if egik > 0 else '')
        yazi = 'Body-' + ek if ek else 'Body'
        def degistir(m):
            hazir = unicodedata.normalize('NFC', m.group(0))
            return hazir if len(hazir) == 1 else '<font name="%s">%s</font>̇' % (yazi, m.group(1))
        out.append(re.sub('([A-Z])̇', degistir, s))
    return ''.join(out)


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


_BAG_KELIME = re.compile(r'(?<![\w])(Bölüm|Şekil|Tablo|Örnek|Soru|Problem|Denklem|Kitap|Sayfa|Ek|Madde|Adım|Fig\.|Eq\.|Table|Chapter|Sec\.)[ \t]+(?=[(\[]?[\dA-Z])')
_BAG_BIRIM = re.compile(r'(\d)[ \t]+(?=(?:mm|cm|km|m|kg|g|N|kN|Pa|kPa|MPa|bar|atm|W|kW|MW|hp|J|kJ|s|sn|dk|h|saat|K|°C|°F|°|L|lt|ft|in|lbf|slug|rad|d/d|mmHg|mSS)(?![\wçğıöşü]))')
_BAG_ISARET = re.compile(r'(?<=[=≈≅<>≤≥±×→∝~])[ \t]+(?=[\d−\-+(])')
# Tek harf yalnız ardından işaret geliyorsa bağlanır ('V = ...'): her tek harfi bağlamak satırda kırılacak yeri
# azaltıp paragrafı gereksiz küçültüyordu. Madde numarası '1)' sonraki sözcükle kalır.
_BAG_TEK = re.compile(r'(?<![\w])([a-zA-Zçğıöşü](?=[ \t]+[=≈≅<>≤≥±×→∝~])|\d+\))[ \t]+(?=\S)')


def _baglar(t):
    """Satır sonunda ayrılmaması gereken parçaları bölünmez boşlukla (U+00A0) bağlar:
    'Bölüm 7', 'Şekil 6.13', '4,1 m', '= 0,5', '1) Keskin', 'V ='."""
    out = []
    for s in re.split(r'(<[^>]+>|&#?\w+;)', t):
        if not s or s[0] in '<&':
            out.append(s); continue
        s = _BAG_KELIME.sub(lambda m: m.group(1) + ' ', s)
        s = _BAG_BIRIM.sub(lambda m: m.group(1) + ' ', s)
        s = _BAG_ISARET.sub(' ', s)
        s = _BAG_TEK.sub(lambda m: m.group(1) + ' ', s)
        out.append(s)
    return ''.join(out)


_KUCULEN = set()   # yazısı küçültülen paragraflar (make() sonunda sayılır)


class _SigP(_BP):
    """Sığmayan satır kalırsa (genişliği aşan satır) yalnız bu paragrafın yazısını 0,25 pt adımlarla küçültür (en çok 1,5 pt)."""

    def _tasan(self):
        for l in getattr(self, 'blPara', None).lines if getattr(self, 'blPara', None) else []:
            es = l[0] if isinstance(l, tuple) else getattr(l, 'extraSpace', 0)
            if es < -0.05:
                return True
        return False

    def wrap(self, aW, aH):
        r = _BP.wrap(self, aW, aH)
        adim = 0
        while adim < 6 and self._tasan():
            adim += 1
            st = self.style.clone('%s_k%d' % (self.style.name, adim))
            st.fontSize = self.style.fontSize - 0.25
            st.spaceShrinkage = 0
            self.__init__(self._sig_metin, st, *self._sig_ek, **self._sig_k)
            r = _BP.wrap(self, aW, aH)
        if adim:
            _KUCULEN.add(self._sig_metin)
        return r


def Paragraph(t, *a, **k):
    stil = a[0] if a else k.get('style')
    if stil is not None:
        stil.spaceShrinkage = 0      # bölünmez boşluklu satırlarda reportlab'in daraltma hesabı taşmaya yol açıyor
    metin = _fix_glyphs(_baglar(_buyuk_nokta(t, stil)))
    p = _SigP(metin, *a, **k)
    p._sig_metin, p._sig_ek, p._sig_k = metin, a[1:], {x: y for x, y in k.items() if x != 'style'}
    return p


class Doc(BaseDocTemplate):
    def __init__(self, out, title, subtitle, header, work, source, renk=None):
        """out: çıktı PDF; header: sayfa üstü sol yazı; work: crop_figs.py çalışma klasörü (figs.json + fig/);
        source: sayfa üstü sağ yazı, ör. 'Kaynak: <Yazar>, <Kitap adı>';
        renk: tema.PALET'ten bir ad = tek renkli belge; None = her h1 sıradaki rengi alır"""
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
        self.tema = Tema(title, renk)
        self._kapak = (colors.HexColor(self.tema.ana), colors.HexColor(self.tema.zemin))

    @property
    def ana(self):
        return self.tema.ana

    def _renkli(self, ad):
        """ss[ad] stilinin o anki konu rengindeki kopyası."""
        return ParagraphStyle('%s-%s' % (ad, self.ana), parent=ss[ad], textColor=colors.HexColor(self.ana))

    # ---------- page decorations ----------
    def _cover(self, c, d):
        c.saveState()
        ana, zemin = self._kapak
        c.setFillColor(zemin); c.rect(0, PAGE_H - 9 * cm, PAGE_W, 9 * cm, fill=1, stroke=0)
        c.setFillColor(ana); c.rect(0, PAGE_H - 9.15 * cm, PAGE_W, 0.15 * cm, fill=1, stroke=0)
        c.restoreState()

    def _page(self, c, d):
        c.saveState()
        c.setStrokeColor(CIZGI); c.setLineWidth(0.6)
        c.line(LM, PAGE_H - 1.5 * cm, PAGE_W - RM, PAGE_H - 1.5 * cm)
        c.setFont('Body', 8.5); c.setFillColor(GREY)
        c.drawString(LM, PAGE_H - 1.3 * cm, self.header)
        c.drawRightString(PAGE_W - RM, PAGE_H - 1.3 * cm, self.source)
        c.line(LM, 1.4 * cm, PAGE_W - RM, 1.4 * cm)
        c.drawCentredString(PAGE_W / 2, 0.9 * cm, str(d.page))
        c.restoreState()

    def beforeDocument(self):
        self._hn = 0
        self._ertelenen = set()

    def afterFlowable(self, fl):
        if isinstance(fl, _P) and getattr(fl, '_toc', None) is not None:
            lvl = fl._toc
            txt = fl.getPlainText()
            key = 'h%d' % self._hn; self._hn += 1
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(txt, key, level=lvl, closed=False)
            self.notify('TOCEntry', (lvl, txt, self.page, key))

    # ---------- content API ----------
    def cover(self, lines, contents, kutu='BU NOTU NASIL KULLANMALISIN?'):
        s = self.story
        s.append(Spacer(1, 1.2 * cm))
        s.append(Paragraph(self.title_, ParagraphStyle('ct', fontName='Body-B', fontSize=30, leading=36, textColor=self._kapak[0])))
        s.append(Spacer(1, 0.4 * cm))
        s.append(Paragraph(self.subtitle, ParagraphStyle('cs', fontName='Body', fontSize=15, leading=20, textColor=KOYU)))
        s.append(Spacer(1, 4.3 * cm))
        for l in lines:
            s.append(Paragraph(l, ParagraphStyle('cl', parent=ss['body'], fontSize=11.5, leading=16, alignment=TA_LEFT)))
        s.append(Spacer(1, 0.6 * cm))
        self.box('ipucu', contents, title=kutu)
        s.append(NextPageTemplate('main'))
        s.append(PageBreak())
        s.append(Paragraph('İçindekiler', self._renkli('h1')))
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

    def h1(self, t, newpage=False, need=9, renk=None):
        self.tema.sonraki(renk)
        if newpage: self.story.append(PageBreak())
        else: self.story.append(CondPageBreak(need * cm))
        self.story.append(self._hp(t, self._renkli('h1'), 0))

    def h2(self, t, need=6):
        self.story.append(CondPageBreak(need * cm))
        self.story.append(self._hp(t, self._renkli('h2'), 1))

    def h3(self, t):
        self.story.append(CondPageBreak(3.5 * cm))
        self.story.append(Paragraph(t, self._renkli('h3')))

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
        self._denklem_ekle(tb, t, n)

    @staticmethod
    def _giris_mi(f):
        """':' ile biten, başlık olmayan cümle: ardındaki denklemi tanıtır."""
        return isinstance(f, _P) and not getattr(f.style, 'keepWithNext', 0) and f.getPlainText().rstrip().endswith(':')

    def _giris_al(self):
        """Hikâyenin sonundaki giriş cümlesini (madde listesinin boşluğuyla birlikte) çıkarıp döndürür."""
        s = self.story
        if s and self._giris_mi(s[-1]):
            return [s.pop()]
        if len(s) > 1 and isinstance(s[-1], Spacer) and self._giris_mi(s[-2]):
            s.pop()
            return [s.pop()]
        return []

    def _denklem_ekle(self, tb, t, n=''):
        """Sayfa bölünmesi türetimi parçalamasın. Aynı sayfada kalanlar: '=', '+' ile başlayan devam satırı,
        numarasız ara adım ve sonraki denklem, aynı numaranın harfli denklemleri (2.18a, 2.18b),
        ':' ile biten giriş cümlesi ve üstündeki başlık denklemle.
        Zincir en çok ZINCIR satır olur, daha uzun türetim sayfaya bölünebilir (bütün sayfa boş kalmasın)."""
        duz = re.sub(r'<[^>]+>|&nbsp;', '', t).strip()
        m = re.match(r'\((\d+\.\d+)[a-z]\)', n or '')
        harf = m.group(1) if m else None
        parca = [tb]
        once = self.story[-1] if self.story else None
        if getattr(once, '_denklem', False):
            icerik = once._content if isinstance(once, KeepTogether) else [once]
            devam = duz and duz[0] in '=+−×'
            ayni = harf and getattr(once, '_harf', None) == harf
            if devam or ayni or (getattr(once, '_numarasiz', False) and len(icerik) < ZINCIR):
                self.story.pop()
                parca = list(icerik) + parca
        parca = self._giris_al() + parca
        parca = self._heads() + parca
        oge = tb if len(parca) == 1 else KeepTogether(parca)
        oge._denklem = True
        oge._numarasiz = not n
        oge._harf = harf
        self.story.append(oge)

    def grup_bas(self):
        """Aynı sayfada kalacak konu grubunu başlatır: g = d.grup_bas(); ...; d.grup_son(g).
        Grubu tanıtan giriş cümlesi gruba dahildir."""
        s = self.story
        if s and getattr(s[-1], '_denklem', False):
            s[-1]._denklem = False   # gruptan önceki denklem zinciri gruba girmesin, sınır kaymasın
        if s and self._giris_mi(s[-1]):
            return len(s) - 1
        if len(s) > 1 and isinstance(s[-1], Spacer) and self._giris_mi(s[-2]):
            return len(s) - 2
        return len(s)

    def grup_son(self, g):
        parca = []
        for f in self.story[g:]:   # iç içe KeepTogether sayfaya sığmaz sayılıp boşuna sayfa atlatır: düzleştir
            parca.extend(f._content if isinstance(f, KeepTogether) else [f])
        del self.story[g:]
        self.story.append(KeepTogether(self._heads() + parca))

    def _boxflow(self, kind, body, title=None):
        bg, fg, lab = BOXES[kind]
        if kind == 'ozet': bg, fg = self.tema.zemin, self.ana
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

    def ceq(self, t, n=''):
        """Çözüm adımı denklemi (cozum içinde): metne yakın boyutta (10,8 pt), ortalı."""
        p = Paragraph(t + ('&nbsp;&nbsp;&nbsp;<font name="Body" size="9" color="#555555">%s</font>' % n if n else ''), _CEQ)
        self._wrapcheck(p, FW - 32, n)
        return p

    def kf(self, num, cap, h=100, terms=None):
        """cozum() içinde çizim: ortalı görsel ve altında kısa açıklama (sekil= ile verilir)."""
        rc = self.figs[num][1]
        w = h * (rc[2] - rc[0]) / (rc[3] - rc[1])
        if w > FW - 40:
            w, h = FW - 40, (FW - 40) * (rc[3] - rc[1]) / (rc[2] - rc[0])
        capt = '<b>Şekil %s</b> – %s' % (num, cap)
        if terms: capt += '<br/><font color="#777777"><i>Şekildeki terimler:</i> %s</font>' % terms
        t = Table([[Image(os.path.join(self.work, 'fig', num + '.png'), width=w, height=h)], [Paragraph(capt, _KFS)]], colWidths=[FW - 32])
        t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('TOPPADDING', (0, 0), (-1, -1), 1), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]))
        return t

    def cozum(self, title, soru, sekil, verilen, kabuller, adimlar, sonuc, yorum=None):
        """Tam çözümlü örnek: SORU, çizim, Verilen/İstenen, KABULLER, numaralı ÇÖZÜM adımları, çerçeveli SONUÇ, Yorum.
        sekil: d.kf(...) ya da None. verilen: (verilenler, istenenler). adimlar: [(açıklama, [denklem | (denklem, no), ...]), ...].
        sonuc: [satırlar]. Kutu satırlara bölünür: uzun örnek yalnız adım sınırında sayfaya bölünür;
        başlık, soru ve çizim ilk satırda birlikte kalır."""
        bg, fg, lab = BOXES['ornek']
        P = lambda t, st=ss['boxb']: Paragraph(t, st)
        etk = ParagraphStyle('etk', parent=ss['boxb'], fontName='Body-B', textColor=colors.HexColor(fg), spaceBefore=5, spaceAfter=2, keepWithNext=1)
        kab = ParagraphStyle('kab', parent=ss['boxb'], leftIndent=12, bulletIndent=2, spaceAfter=1.5)
        adm = ParagraphStyle('adm', parent=ss['boxb'], spaceBefore=3, spaceAfter=1.5, keepWithNext=1)
        satir = [[Paragraph('<font color="%s">%s</font>' % (fg, title), ss['boxt']), P('SORU', etk), P(soru)] + ([sekil] if sekil else []) + [
                  Spacer(1, 4), P('<b>Verilen:</b> ' + verilen[0] + '<br/><b>İstenen:</b> ' + verilen[1])]]
        if kabuller:
            satir.append([P('KABULLER', etk)] + [Paragraph(k, kab, bulletText='•') for k in kabuller])
        for i, (txt, eqs) in enumerate(adimlar, 1):
            ic = [P('<b>%d)</b> %s' % (i, txt), adm)] + [self.ceq(*e) if isinstance(e, tuple) else self.ceq(e) for e in eqs]
            satir.append(([P('ÇÖZÜM', etk)] if i == 1 else []) + ic)
        st = Table([[[x if not isinstance(x, str) else P(x) for x in sonuc]]], colWidths=[FW - 32])
        st.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor(fg)), ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                                ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                                ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]))
        satir.append([P('SONUÇ', etk), st] + ([P('<i>Yorum:</i> ' + yorum)] if yorum else []))
        t = Table([[x] for x in satir], colWidths=[FW])
        t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(bg)), ('LINEBEFORE', (0, 0), (0, -1), 3.5, colors.HexColor(fg)),
                               ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                               ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                               ('TOPPADDING', (0, 0), (-1, 0), 6), ('BOTTOMPADDING', (0, -1), (-1, -1), 6)]))
        t._bolunur = True
        self.story += [Spacer(1, 3), t, Spacer(1, 7)]

    def fig(self, num, cap, scale=1.0, maxw=None, maxh=320, terms=None, keep=None):
        pg, rc = self.figs[num]
        wpt, hpt = rc[2] - rc[0] + 10, rc[3] - rc[1] + 10
        w = wpt * 0.92 * scale
        w = min(w, maxw or FW)
        h = w * hpt / wpt
        if h > maxh: h = maxh; w = h * wpt / hpt
        capt = '<b><font color="%s">Şekil %s</font></b> – %s' % (self.ana, num, cap)
        if terms: capt += '<br/><font color="#777777"><i>Şekildeki terimler:</i> %s</font>' % terms
        heads = self._heads()

        def yap(oran=1.0):
            img = Image(os.path.join(self.work, 'fig', num + '.png'), width=w * oran, height=h * oran)
            ct = Table([[img], [Paragraph(capt, ss['cap'])]], colWidths=[min(FW, max(w + 20, 12 * cm))])
            ct.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('LINEBELOW', (0, 1), (-1, 1), 0.5, colors.HexColor('#BBBBBB')),
                                    ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 1), (-1, 1), 6)]))
            flow = [Spacer(1, 4), ct, Spacer(1, 8)]
            if keep:  # keep figure together with some preceding/following paragraph text
                flow = keep(flow)
            kt = KeepTogether(heads + list(flow))
            kt._sekil = (yap, h, bool(heads))   # sayfa sonunda sığmazsa filterFlowables küçültür ya da metni öne alır
            return kt
        self.story.append(yap())

    # ---------- şekil sığmayınca sayfa yarı boş kalmasın ----------
    SEKIL_MIN_OLCEK = 0.8     # sığdırmak için şekil en çok bu orana küçülür
    SEKIL_BOSLUK = 3 * cm     # bundan küçük boşluk için uğraşılmaz

    @staticmethod
    def _baslik_mi(f):
        return isinstance(f, _P) and (getattr(f.style, 'keepWithNext', 0) or getattr(f, '_toc', None) is not None)

    def _akabilir(self, f):
        """Şeklin önüne alınabilecek öğe: paragraf, boşluk, denklem, kutu, tablo. Başlık (ya da başlık taşıyan
        grup), sayfa atlatıcı ve başka şekil sınırdır: şekil kendi konusunun dışına taşınmaz."""
        if getattr(f, '_sekil', None) or isinstance(f, (CondPageBreak, PageBreak)):
            return False
        if isinstance(f, KeepTogether):
            return not any(self._baslik_mi(x) for x in f._content)
        if isinstance(f, _P):
            return not self._baslik_mi(f)
        return isinstance(f, (Spacer, Table))

    def _yukseklik(self, f, W):
        return _listWrapOn(f._content if isinstance(f, KeepTogether) else [f], W, self.canv)[1]

    def filterFlowables(self, flowables):
        f = flowables[0] if flowables else None
        sk = getattr(f, '_sekil', None)
        if not sk or id(f) in self._ertelenen:
            return
        fr = self.frame
        bos = fr._y - fr._y1p
        if getattr(fr, '_atTop', 1) or bos < self.SEKIL_BOSLUK:
            return
        W = fr._aW
        H = self._yukseklik(f, W)
        if H <= bos + 0.5:
            return
        yap, h, basli = sk          # yap None: yalnız akıtılır (ör. yan yana iki şekil)
        # 1) küçültülerek sığıyorsa küçült
        oran = (h - (H - bos) - 1) / h if yap else 0
        while oran >= self.SEKIL_MIN_OLCEK:
            yeni = yap(oran)
            if self._yukseklik(yeni, W) <= bos + 0.5:
                flowables[0] = yeni
                return
            oran -= 0.02
        self._ertelenen.add(id(f))
        if basli:      # şeklin başlığı var: arkasındaki metin başlığın altına ait, öne alınmaz
            return
        # 2) sonraki metni boşluğa akıt, şekil sonraki sayfanın başına geçsin
        kalan, i = bos, 1
        while i < len(flowables) and kalan > 0 and self._akabilir(flowables[i]):
            g = flowables[i]
            hg = self._yukseklik(g, W)
            if hg > kalan and not isinstance(g, _P):
                # çözümlü örnek adım sınırında bölünebilir: ilk satırı (başlık, soru, çizim) sığıyorsa akar;
                # kutu, tablo, denklem bölünmez: sığmıyorsa şekilden sonra kalır
                if not (getattr(g, '_bolunur', False) and g._rowHeights[0] <= kalan):
                    break
            kalan -= hg
            i += 1
        if i > 1:
            flowables[:i] = flowables[1:i] + [f]

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

    def keep(self, flow, sekil=False):
        """flow'u tek parça tut; hemen önündeki başlıkları da içine al. (reportlab'in keepWithNext'i
        KeepTogether'a bağlanmaz: başlık + şekil/tablo varsa başlık sayfa sonunda yalnız kalabiliyordu.)
        sekil=True: sayfaya sığmazsa ardındaki metin boşluğa akar (bkz. filterFlowables)."""
        heads = self._heads()
        kt = KeepTogether(heads + list(flow))
        if sekil:
            kt._sekil = (None, 0, bool(heads))
        self.story.append(kt)

    def table(self, rows, widths=None, title=None, small=False):
        data = []
        for i, r in enumerate(rows):
            st = ss['cellh'] if i == 0 else ss['cell']
            data.append([Paragraph(str(c), st) for c in r])
        if widths: widths = [w * FW for w in widths]
        t = Table(data, colWidths=widths, repeatRows=1)
        sty = [('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.ana)), ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#AAAAAA')),
               ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]
        for i in range(1, len(rows)):
            if i % 2 == 0: sty.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor(self.tema.zemin)))
        t.setStyle(TableStyle(sty))
        fl = [Spacer(1, 3)]
        if title: fl.append(Paragraph('<b><font color="%s">%s</font></b>' % (self.ana, title), ss['cap']))
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
        if _KUCULEN:
            print('BİLGİ: %d paragraf, taşan satır yüzünden en çok 1,5 pt küçültüldü' % len(_KUCULEN))
