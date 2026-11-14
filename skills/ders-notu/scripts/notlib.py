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
_YANCAP = ParagraphStyle('yancap', parent=ss['cap'], alignment=TA_LEFT)   # şeklin yanına alınan açıklama
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
EQ_MIN_ORAN = 0.75   # sığmayan denklem en çok bu orana küçülür; daha uzunu anlamlı yerinden bölünür
EQ_BOLUNMUS_ORAN = 0.9   # bölünen denklemin satırları en çok bu orana küçülür (bölündükten sonra küçültmeye gerek kalmasın)
_EQ_AYRAC = re.compile(r'(?:&nbsp;|\s)*(⇒|,|;)(?:&nbsp;|\s)+|\s+(=|\+|−)\s+')   # denklem bölme yerleri


def _duz(t):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', t).replace('&nbsp;', ' ')).strip()


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
        self._fig_say = [0, 0]   # [açıklaması altta, yanda]
        self._fig_meta = {}      # şekil no -> (açıklama, en, boy): yan yerleşim için
        self._eq_kucuk = []       # tek satıra sığsın diye küçültülen denklemlerin oranları
        self._eq_bolunen = []     # bölünen denklemlerin satır sayıları
        self._eq_elle = []        # küçültülüp bölünemeyen (elle düzenlenecek) denklemler
        self.kayit = []           # notun iskeleti (başlık, paragraf, kutu, şekil, denklem): make() <work>/kayit.json'a yazar
        self.tema = Tema(title, renk)
        self._kapak = (colors.HexColor(self.tema.ana), colors.HexColor(self.tema.zemin))

    @property
    def ana(self):
        return self.tema.ana

    def _renkli(self, ad):
        """ss[ad] stilinin o anki konu rengindeki kopyası."""
        return ParagraphStyle('%s-%s' % (ad, self.ana), parent=ss[ad], textColor=colors.HexColor(self.ana))

    # ---------- iskelet kaydı (üslup denetimi için; bkz. uslup_denetim.py) ----------
    def _kaydet(self, tip, **alan):
        alan['t'] = tip
        self.kayit.append(alan)

    @staticmethod
    def _oge_kaydi(b):
        """Kutu ya da çözüm içindeki öğenin kaydı: metin, beq/ceq denklemi ya da kf çizimi."""
        if isinstance(b, str):
            return {'t': 'metin', 'metin': b}
        k = getattr(b, '_kayit', None)
        return dict(k) if k else {'t': 'diger'}

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
        self._sekil_sonuc = {}
        self._bosluk = []        # (şekil no, sayfa, boşluk pt): sığmayıp sonraki sayfaya geçen şeklin bıraktığı boşluk
        self._yan_yana = set()   # önündeki denklemlerle yan yana alınan şekiller

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
        self._kaydet('kapak', satirlar=list(lines))
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
        self._kaydet('h1', metin=t)
        if newpage: self.story.append(PageBreak())
        else: self.story.append(CondPageBreak(need * cm))
        self.story.append(self._hp(t, self._renkli('h1'), 0))

    def h2(self, t, need=6):
        self._kaydet('h2', metin=t)
        self.story.append(CondPageBreak(need * cm))
        self.story.append(self._hp(t, self._renkli('h2'), 1))

    def h3(self, t):
        self._kaydet('h3', metin=t)
        self.story.append(CondPageBreak(3.5 * cm))
        self.story.append(Paragraph(t, self._renkli('h3')))

    def p(self, *ts):
        for t in ts:
            self._kaydet('p', metin=t)
            self.story.append(Paragraph(t, ss['body']))

    def bl(self, items, num=False):
        self._kaydet('bl', maddeler=list(items), num=num)
        for i, t in enumerate(items):
            b = '%d.' % (i + 1) if num else '•'
            self.story.append(Paragraph(t, ss['bullet'], bulletText=b))
        self.story.append(Spacer(1, 3))

    @staticmethod
    def _satir(p, width):
        p.wrap(width, 10000)
        bp = getattr(p, 'blPara', None)
        return len(bp.lines) if bp is not None else 1

    @staticmethod
    def _stil(st, oran):
        if oran >= 1:
            return st
        k = st.clone('%s_d%d' % (st.name, round(oran * 100)))
        k.fontSize, k.leading = st.fontSize * oran, st.leading * oran
        return k

    def _oran(self, t, st, width, alt=None):
        """t'nin tek satıra sığdığı en büyük yazı oranı (1, 0,97, … , alt = EQ_MIN_ORAN); hiçbirinde sığmazsa None."""
        alt = EQ_MIN_ORAN if alt is None else alt
        oran = 1.0
        while oran >= alt - 1e-9:
            if self._satir(Paragraph(t, self._stil(st, oran)), width) == 1:
                return oran
            oran = round(oran - 0.03, 2)
        return None

    @staticmethod
    def _ayraclar(t):
        """Parantez dışındaki (derinlik 0) bölme yerleri: [(başlangıç, bitiş, işaret)]. İşaret: ⇒ , ; = + −"""
        n = len(t)
        dz, etiket, derin, i = [0] * (n + 1), [False] * (n + 1), 0, 0
        while i < n:
            c = t[i]
            if c == '<':
                j = t.find('>', i)
                j = n - 1 if j < 0 else j
                for k in range(i, j + 1):
                    etiket[k], dz[k] = True, derin
                i = j + 1
                continue
            if c in '([{':
                derin += 1
            dz[i] = derin
            if c in ')]}':
                derin -= 1
            i += 1
        out = []
        for m in _EQ_AYRAC.finditer(t):
            g = 1 if m.group(1) else 2
            k = m.start(g)
            if dz[k] == 0 and not etiket[k]:
                out.append((m.start(), m.end(), m.group(g)))
        return out

    def _bol(self, t, st, width, isaretler, derin=0):
        """t'yi isaretler'deki parantez dışı ayraçlardan, her parça tek satıra (en çok EQ_MIN_ORAN'a küçülerek) sığana dek
        ikiye böler (bölünmüş satırlar en çok EQ_BOLUNMUS_ORAN'a küçülür). Dengeli bölme seçilir: kısa parça bütünün en az %25'i (tek terim alt satıra düşmez); '⇒', ',' ve '='
        öncelikli. Bölünemezse None."""
        if self._oran(t, st, width, EQ_BOLUNMUS_ORAN) is not None:
            return [t]
        if derin > 4:
            return None
        L = len(_duz(t))
        aday = []
        for a, b, op in self._ayraclar(t):
            if op not in isaretler:
                continue
            sol = t[:a] + (op if op in ',;' else '')
            sag = ('' if op in ',;' else op + ' ') + t[b:]
            kisa = min(len(_duz(sol)), len(_duz(sag)))
            if kisa < 0.25 * L:
                continue
            aday.append((kisa * (1.25 if op in '⇒,;=' else 1.0), sol, sag))
        for _, sol, sag in sorted(aday, key=lambda x: -x[0]):
            a = self._bol(sol, st, width, isaretler, derin + 1)
            b = a and self._bol(sag, st, width, isaretler, derin + 1)
            if a and b:
                return a + b
        return None

    def _birlestir(self, satirlar, st, width):
        """İkiye bölme gereğinden çok satır üretebilir: yan yana satırlar birlikte sığıyorsa birleştirilir."""
        out = [satirlar[0]]
        for x in satirlar[1:]:
            ek = out[-1] + (' ' if x[:1] in '=+−⇒' else '&nbsp;&nbsp; ') + x
            if self._oran(ek, st, width, EQ_BOLUNMUS_ORAN) is not None:
                out[-1] = ek
            else:
                out.append(x)
        return out

    def _denklem(self, t, st, width, n):
        """Denklem satırları ve ortak yazı oranı: ([metin, ...], oran).
        1) Tek satıra sığıyorsa olduğu gibi; 2) değilse yazı %3 adımlarla en çok EQ_MIN_ORAN'a küçülür;
        3) yine sığmazsa önce bileşik ayraçlardan (⇒, virgül ya da noktalı virgülle ayrılmış denklemler), olmazsa = + − işaretlerinden
        anlamlı yerde bölünür (tek terim alt satıra düşmez), satırlar aynı oranda yazılır;
        4) bölünemezse en küçük oranda bırakılır ve UYARI verilir (elle düzenlenir)."""
        oran = self._oran(t, st, width)
        if oran is not None:
            if oran < 1:
                self._eq_kucuk.append(oran)
            return [t], oran
        satirlar = self._bol(t, st, width, ('⇒', ',', ';')) or self._bol(t, st, width, ('⇒', ',', ';', '=', '+', '−'))
        if not satirlar:
            self._eq_elle.append(_duz(t)[:70])
            print('UYARI denklem %%%d\'e küçültüldüğü ve bölünmeye çalışıldığı hâlde sığmadı %s: %s — elle böl ya da uzun '
                  'parçaya ad ver' % (round(EQ_MIN_ORAN * 100), n, _duz(t)[:70]))
            return [t], EQ_MIN_ORAN
        satirlar = self._birlestir(satirlar, st, width)
        self._eq_bolunen.append(len(satirlar))
        return satirlar, min(self._oran(x, st, width, EQ_BOLUNMUS_ORAN) for x in satirlar)

    @staticmethod
    def _no_html(n):
        return '&nbsp;&nbsp;&nbsp;<font name="Body" size="9" color="#555555">%s</font>' % n if n else ''

    def eq(self, t, n=''):
        self._kaydet('eq', metin=t, no=n)
        nw = 2.2 * cm   # '(6.16–6.18)' gibi aralık numaraları için
        satirlar, oran = self._denklem(t, ss['eq'], FW - 2 * nw - 12, n)
        for i, x in enumerate(satirlar):
            son = i == len(satirlar) - 1
            tb = Table([[Paragraph('', ss['eqn']), Paragraph(x, self._stil(ss['eq'], oran)), Paragraph(n if son else '', ss['eqn'])]],
                       colWidths=[nw, FW - 2 * nw, nw])
            tb.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 2),
                                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
            tb._eqsrc = (x, n if son else '')   # yan yerleşimde dar sütuna yeniden dizmek için
            self._denklem_ekle(tb, x, n if son else '')

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
            devam = duz and duz[0] in '=+−×⇒'
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
        self._kaydet('box', tur=kind, baslik=title, icerik=[self._oge_kaydi(b) for b in (body if isinstance(body, list) else [body])])
        self.story.append(Spacer(1, 3))
        self.story.append(self._boxflow(kind, body, title))
        self.story.append(Spacer(1, 7))

    def beq(self, t, n=''):
        """equation flowable for use inside boxes"""
        satirlar, oran = self._denklem(t, ss['eq'], FW - 32 - (len(n) * 5 + 14 if n else 0), n)
        p = Paragraph('<br/>'.join(satirlar) + self._no_html(n), self._stil(ss['eq'], oran))
        p._kayit = {'t': 'eq', 'metin': t, 'no': n}
        return p

    def ceq(self, t, n=''):
        """Çözüm adımı denklemi (cozum içinde): metne yakın boyutta (10,8 pt), ortalı."""
        satirlar, oran = self._denklem(t, _CEQ, FW - 32 - (len(n) * 5 + 14 if n else 0), n)
        p = Paragraph('<br/>'.join(satirlar) + self._no_html(n), self._stil(_CEQ, oran))
        p._kayit = {'t': 'eq', 'metin': t, 'no': n}
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
        t._kayit = {'t': 'fig', 'no': num, 'cap': cap, 'terms': terms}
        return t

    def cozum(self, title, soru, sekil, verilen, kabuller, adimlar, sonuc, yorum=None):
        """Tam çözümlü örnek: SORU, çizim, Verilen/İstenen, KABULLER, numaralı ÇÖZÜM adımları, çerçeveli SONUÇ, Yorum.
        sekil: d.kf(...) ya da None. verilen: (verilenler, istenenler). adimlar: [(açıklama, [denklem | (denklem, no), ...]), ...].
        sonuc: [satırlar]. Kutu satırlara bölünür: uzun örnek yalnız adım sınırında sayfaya bölünür;
        başlık, soru ve çizim ilk satırda birlikte kalır."""
        self._kaydet('cozum', baslik=title, soru=soru, sekil=self._oge_kaydi(sekil) if sekil else None,
                     verilen=list(verilen), kabuller=list(kabuller or []),
                     adimlar=[{'metin': txt, 'denklemler': [e[0] if isinstance(e, tuple) else e for e in eqs]} for txt, eqs in adimlar],
                     sonuc=[x for x in sonuc if isinstance(x, str)], yorum=yorum)
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
        self._kaydet('fig', no=num, cap=cap, terms=terms)
        pg, rc = self.figs[num]
        wpt, hpt = rc[2] - rc[0] + 10, rc[3] - rc[1] + 10
        w = wpt * 0.92 * scale
        w = min(w, maxw or FW)
        h = w * hpt / wpt
        if h > maxh: h = maxh; w = h * wpt / hpt
        capt = '<b><font color="%s">Şekil %s</font></b> – %s' % (self.ana, num, cap)
        if terms: capt += '<br/><font color="#777777"><i>Şekildeki terimler:</i> %s</font>' % terms
        self._fig_meta[num] = (capt, wpt, hpt, h)
        heads = self._heads()

        def yap(oran=1.0, yan=False):
            """yan=True: açıklama şeklin sağına yazılır (yalnız sığmayan şekilde; yanda yer yoksa None)."""
            img = Image(os.path.join(self.work, 'fig', num + '.png'), width=w * oran, height=h * oran)
            if yan:
                sol = w * oran + 14
                if FW - sol < self.YAN_MIN:
                    return None
                ct = Table([[img, Paragraph(capt, _YANCAP)]], colWidths=[sol, FW - sol])
                ct.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                                        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor('#BBBBBB')),
                                        ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                                        ('LEFTPADDING', (1, 0), (1, 0), 4)]))
            else:
                ct = Table([[img], [Paragraph(capt, ss['cap'])]], colWidths=[min(FW, max(w + 20, 12 * cm))])
                ct.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('LINEBELOW', (0, 1), (-1, 1), 0.5, colors.HexColor('#BBBBBB')),
                                        ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 1), (-1, 1), 6)]))
            flow = [Spacer(1, 4), ct, Spacer(1, 8)]
            if keep:  # keep figure together with some preceding/following paragraph text
                flow = keep(flow)
            kt = KeepTogether(heads + list(flow))
            kt._sekil = (yap, h, bool(heads), yan0)
            kt._no = num   # sayfa sonunda sığmazsa filterFlowables küçültür ya da metni öne alır
            return kt

        # Açıklama yana sığıyorsa (yanda en az YAN_MIN sütun kalır ve açıklama şeklin boyunu aşmaz) yana yazılır
        sutun = FW - (w + 14) - 10
        yan0 = sutun + 10 >= self.YAN_MIN and Paragraph(capt, _YANCAP).wrap(sutun, 10000)[1] <= h
        self._fig_say[yan0] += 1
        self.story.append(yap(1.0, yan0))

    # ---------- şekil sığmayınca sayfa yarı boş kalmasın ----------
    SEKIL_MIN_OLCEK = 0.8     # sığdırmak için şekil en çok bu orana küçülür
    SEKIL_BOSLUK = 3 * cm     # bundan küçük boşluk için uğraşılmaz
    YAN_MIN = 5.5 * cm        # açıklamanın şeklin yanına alınması için gereken en dar sütun

    def _sonuc(self, ne):
        self._sekil_sonuc[ne] = self._sekil_sonuc.get(ne, 0) + 1

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
        if f is not None and len(flowables) > 1 and not getattr(f, '_sekil', None) and getattr(flowables[1], '_sekil', None):
            if self._yan_yana_akista(flowables):
                return
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
        yap, h, basli, yan0 = sk    # yap None: yalnız akıtılır (ör. yan yana iki şekil)
        # Açıklaması alttaysa: 1) yana al, 2) küçült, 3) küçült + yana al. Zaten yandaysa yalnız 3.
        # İlk sığan kullanılır.
        if yap:
            adaylar = []
            if not yan0:
                adaylar.append((1.0, True))
                oran = (h - (H - bos) - 1) / h
                while oran >= self.SEKIL_MIN_OLCEK:
                    adaylar.append((oran, False))
                    oran -= 0.02
            oran = 0.98
            while oran >= self.SEKIL_MIN_OLCEK:
                adaylar.append((oran, True))
                oran -= 0.02
            for oran, yan in adaylar:
                yeni = yap(oran, yan)
                if yeni is not None and self._yukseklik(yeni, W) <= bos + 0.5:
                    flowables[0] = yeni
                    self._sonuc('küçük' if yan0 or not yan else 'küçük + yan' if oran < 1 else 'yan')
                    return
        self._ertelenen.add(id(f))
        if basli:      # şeklin başlığı var: arkasındaki metin başlığın altına ait, öne alınmaz
            self._sonuc('sonraki sayfa')
            self._bosluk.append((getattr(f, '_no', None), self.page, bos))
            return
        # 2) sonraki metni boşluğa akıt, şekil sonraki sayfanın başına geçsin
        kalan, i = bos, 1
        while i < len(flowables) and kalan > 0 and self._akabilir(flowables[i]):
            g = flowables[i]
            hg = self._yukseklik(g, W)
            if hg > kalan:
                # paragraf ve çözümlü örnek (adım sınırında, ilk satırı sığıyorsa) bölünerek akar; kutu, tablo,
                # denklem bölünmez. Taşan kısım şekille birlikte sonraki sayfaya sığmıyorsa akmaz: yoksa şekil
                # bir sayfa daha kayar, yeni boşluk açılır
                bolunur = isinstance(g, _P) or (getattr(g, '_bolunur', False) and g._rowHeights[0] <= kalan)
                if not bolunur or hg - kalan + H > fr._aH:
                    break
            kalan -= hg
            i += 1
        if i > 1:
            flowables[:i] = flowables[1:i] + [f]
        self._sonuc('metin aktı' if i > 1 else 'sonraki sayfa')
        if i == 1:     # akacak metin yok (ardında başlık var): boşluk kalır
            self._bosluk.append((getattr(f, '_no', None), self.page, bos))

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
            kt._sekil = (None, 0, bool(heads), False)
        self.story.append(kt)

    def table(self, rows, widths=None, title=None, small=False):
        self._kaydet('table', baslik=title, satirlar=[[str(c) for c in r] for r in rows])
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

    def raw(self, f):
        self._kaydet('raw')
        self.story.append(f)

    def begin_keep(self): self._kstart = len(self.story)

    def end_keep(self):
        k = self.story[self._kstart:]; del self.story[self._kstart:]
        # blok içindeki CondPageBreak'ler (h2/h3'ün "yer yoksa sayfa atla"sı) KeepTogether içinde
        # yanlış ölçülüp gereksiz sayfa atlatır; bloğu bir bütün olarak öne al, ayrıca başına ekle
        need = sum(f.height for f in k if isinstance(f, CondPageBreak))
        k = [f for f in k if not isinstance(f, CondPageBreak)]
        if need: self.story.append(CondPageBreak(need))
        self.keep(k)

    # ---------- sığmayan şekil: önündeki denklemlerle yan yana ----------
    YAN_YANA_ORAN = 0.55      # yan yerleşimde şeklin genişliği (FW'nin oranı)
    YAN_YANA_SOL_MIN = 6 * cm  # sol sütun bundan dar olmaz
    BOSLUK_ENGEL = 6 * cm     # bundan büyük boşluk denetle.py'de ENGEL

    def _dar_ogeler(self, g, colw):
        """g'nin (denklem zinciri ya da paragraf) colw genişliğe yeniden dizilmiş öğeleri; olmuyorsa None."""
        out = []
        for e in (g._content if isinstance(g, KeepTogether) else [g]):
            if hasattr(e, '_eqsrc'):
                x, n = e._eqsrc
                nw = 1.6 * cm if n else 0
                w = colw - nw
                oran = self._oran(x, ss['eq'], w - 6)
                if oran is None:
                    return None
                hucre = [Paragraph(x, self._stil(ss['eq'], oran))] + ([Paragraph(n, ss['eqn'])] if n else [])
                t = Table([hucre], colWidths=[w] + ([nw] if n else []))
                t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('LEFTPADDING', (0, 0), (-1, -1), 0),
                                       ('RIGHTPADDING', (0, 0), (-1, -1), 0), ('TOPPADDING', (0, 0), (-1, -1), 2),
                                       ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
                out.append(t)
            elif isinstance(e, _P) and not self._baslik_mi(e):
                out.append(e)
            elif isinstance(e, Spacer):
                continue
            else:
                return None   # başlık, kutu, tablo: dar sütuna alınmaz
        return out

    def _yan_yana_blok(self, g, no, W):
        """g (denklem zinciri ya da paragraf) solda, Şekil no sağda (FW·YAN_YANA_ORAN genişlikte, açıklaması altında)
        tek blok; olmuyorsa None."""
        capt, wpt, hpt, h0 = self._fig_meta[no]
        figw = W * self.YAN_YANA_ORAN
        figh = min(figw * hpt / wpt, h0)
        figw = figh * wpt / hpt
        colw = W - figw - 14
        if colw < self.YAN_YANA_SOL_MIN:
            return None
        sol = self._dar_ogeler(g, colw)
        if not sol:
            return None
        img = Image(os.path.join(self.work, 'fig', no + '.png'), width=figw, height=figh)
        tb = Table([[sol, [img, Spacer(1, 3), Paragraph(capt, ss['cap'])]]], colWidths=[colw + 14, figw])
        tb.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                                ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (0, 0), 14),
                                ('RIGHTPADDING', (1, 0), (1, 0), 0), ('TOPPADDING', (0, 0), (-1, -1), 4),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                                ('LINEBELOW', (1, 0), (1, 0), 0.5, colors.HexColor('#BBBBBB'))]))
        return tb

    def _yan_yana_akista(self, flowables):
        """flowables[0] bir denklem zinciri ya da paragraf, flowables[1] bir şekil. Şekil bu sayfaya (en çok
        SEKIL_MIN_OLCEK'e küçülse de) sığmayacak ve ardında boşluğu dolduracak metin yoksa (başlık geliyorsa) ikisini
        yan yana tek bloğa çevirir: sayfa altında boşluk kalmaz, şekil anlattığı denklemlerin yanında durur."""
        f, fig = flowables[0], flowables[1]
        yap, h, basli, yan0 = fig._sekil
        no = getattr(fig, '_no', None)
        if basli or yap is None or no not in self._fig_meta:
            return False
        if not (getattr(f, '_denklem', False) or (isinstance(f, _P) and not self._baslik_mi(f))):
            return False
        if len(flowables) > 2 and self._akabilir(flowables[2]):
            return False   # ardından metin geliyor: mevcut yol onu boşluğa akıtır
        fr = self.frame
        if getattr(fr, '_atTop', 1):
            return False
        bos, W = fr._y - fr._y1p, fr._aW
        kalan = bos - self._yukseklik(f, W)
        if kalan < 0 or kalan < self.SEKIL_BOSLUK:
            return False   # blok zaten sonraki sayfaya geçiyor ya da kalan boşluk küçük
        adaylar = [yap(self.SEKIL_MIN_OLCEK, False)] + ([yap(self.SEKIL_MIN_OLCEK, True)] if not yan0 else [])
        if any(x is not None and self._yukseklik(x, W) <= kalan for x in adaylar):
            return False   # şekil küçültülerek sığar: mevcut yol halleder
        blok = self._yan_yana_blok(f, no, W)
        if blok is None or self._yukseklik(blok, W) > bos + 0.5:
            return False
        flowables[0:2] = [blok]
        self._yan_yana.add(no)
        return True

    def make(self):
        with open(os.path.join(self.work, 'kayit.json'), 'w', encoding='utf-8') as f:
            json.dump(self.kayit, f, ensure_ascii=False, indent=0)
        self.multiBuild(self.story)
        if self._yan_yana:
            print('BİLGİ: %d şekil sayfaya sığmadığı için önündeki denklemlerle yan yana alındı: %s'
                  % (len(self._yan_yana), ', '.join(sorted(self._yan_yana))))
        if sum(self._fig_say):
            print('BİLGİ: %d şeklin açıklaması yanda, %d şeklinki altta' % (self._fig_say[1], self._fig_say[0]))
        if self._sekil_sonuc:
            print('BİLGİ: sayfaya sığmayan şekiller: ' + ', '.join('%s %d' % kv for kv in sorted(self._sekil_sonuc.items())))
        if _KUCULEN:
            print('BİLGİ: %d paragraf, taşan satır yüzünden en çok 1,5 pt küçültüldü' % len(_KUCULEN))
        if self._eq_kucuk:
            print('BİLGİ: %d denklem tek satıra sığsın diye küçültüldü (en küçük %%%d)'
                  % (len(self._eq_kucuk), round(min(self._eq_kucuk) * 100)))
        if self._eq_bolunen:
            print('BİLGİ: %d denklem anlamlı yerinden %d satıra bölündü' % (len(self._eq_bolunen), sum(self._eq_bolunen)))
        if self._eq_elle:
            print('ELLE DÜZENLENECEK DENKLEMLER (%d): ' % len(self._eq_elle) + ' | '.join(self._eq_elle))
        # denetle.py derleme çıktısını görmez: düzeltilmesi gerekenler dosyaya da yazılır
        with open(os.path.join(self.work, 'derleme.json'), 'w', encoding='utf-8') as f:
            json.dump({'elle_denklem': self._eq_elle, 'eksik_glif': sorted(_missing),
                       'bosluk': [[no, sayfa, round(b / cm, 1)] for no, sayfa, b in self._bosluk],
                       'bosluk_engel_cm': round(self.BOSLUK_ENGEL / cm, 1)}, f, ensure_ascii=False)
        for no, sayfa, b in self._bosluk:
            print('%s: s.%d altında %.1f cm boşluk (Şekil %s sığmadı, sonraki sayfaya geçti)'
                  % ('UYARI' if b >= self.BOSLUK_ENGEL else 'BİLGİ', sayfa, b / cm, no))
