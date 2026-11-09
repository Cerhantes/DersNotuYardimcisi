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

Çalıştırma: PYTHONPATH=<skill>/scripts python -W ignore icerik.py <cikti.pdf> <work>
Şemalar <work>/dg/<ad>.png içinde aranır (dglib.save bunları oraya yazar).
"""
import json, os, re, sys, hashlib, warnings, matplotlib
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
# Yazı tipi ve renk teması ortak/ klasöründe (bkz. ortak/fontlar.py, ortak/tema.py)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'ortak'))
import fontlar
from tema import Tema, acik
FONTS = fontlar.kaydet()
_body, _math = pdfmetrics.getFont('Body'), pdfmetrics.getFont('Math')
_BODY_CM, _MATH_CM = _body.face.charToGlyph, _math.face.charToGlyph
_SYM_CM = pdfmetrics.getFont('Sym').face.charToGlyph
_missing = set()
_ANA = '#333333'   # o anki kartın rengi
_ADLI = set()      # terms(...) ile adlandırılmış semboller


def _fix_glyphs(t):
    """Metin yazı tipinde olmayan karakterleri (∛ ≫ ∝ ≈ √ ...) matematik ya da yedek yazı tipine geçirir."""
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
# Tek harf yalnız ardından işaret geliyorsa bağlanır ('V = ...'); madde numarası '1)' sonraki sözcükle kalır.
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


def Paragraph(t, *a, **k):
    # Küçük yazıda alt simge alttaki satıra binmesin
    t = t.replace('<sub>', '<sub rise="1.6" size="6.2">').replace('@ANA@', _ANA)
    return _P(_fix_glyphs(_baglar(t)), *a, **k)


# ---------------------------------------------------------------- düzen ve stiller
GREY = colors.HexColor('#555555'); KOYU = colors.HexColor('#333333'); CIZGI = colors.HexColor('#BBBBBB')
PAGE_W, PAGE_H = A4
LM = RM = 1.4 * cm; TM, BM = 1.9 * cm, 1.5 * cm
FW = PAGE_W - LM - RM
FH = PAGE_H - TM - BM

st_title = ParagraphStyle('t', fontName='Body-B', fontSize=20, leading=24)
st_sub = ParagraphStyle('s', fontName='Body', fontSize=10, leading=13, textColor=KOYU)
st_card = ParagraphStyle('c', fontName='Body-B', fontSize=11.5, leading=14)
st_terms = ParagraphStyle('tm', fontName='Body', fontSize=8.3, leading=11, textColor=colors.HexColor('#444444'))
st_note = ParagraphStyle('n', fontName='Body', fontSize=8.6, leading=11, textColor=colors.HexColor('#7A3B00'))
st_lab = ParagraphStyle('l', fontName='Body-B', fontSize=8.6, leading=11, spaceAfter=1.5)
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
    """'T_1' -> matematik yazı tipinde italik T<sub>1</sub>. Virgülle birden çok: 'T_1, T_2'. Biçim: taban[_alt][^üst]."""
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
    for a, _ in pairs:
        for s in a.split(', '):
            if not (s.isascii() and s.isalpha() and len(s) > 1):   # 'MRR' gibi adlar harflerine bölünmez
                _ADLI.update(_semboller(re.sub(r'_(\w+)', r'_{\1}', s)))   # 'D_ort' -> D_{ort}
    return ' · '.join('<font color="@ANA@">%s</font>: %s' % (sym(a), b) for a, b in pairs)


YUNAN = {'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'delta': 'δ', 'epsilon': 'ε', 'varepsilon': 'ε', 'zeta': 'ζ', 'eta': 'η',
         'theta': 'θ', 'kappa': 'κ', 'lambda': 'λ', 'mu': 'μ', 'nu': 'ν', 'xi': 'ξ', 'pi': 'π', 'rho': 'ρ', 'sigma': 'σ',
         'tau': 'τ', 'phi': 'φ', 'varphi': 'φ', 'chi': 'χ', 'psi': 'ψ', 'omega': 'ω', 'Gamma': 'Γ', 'Delta': 'Δ',
         'Theta': 'Θ', 'Lambda': 'Λ', 'Pi': 'Π', 'Sigma': 'Σ', 'Phi': 'Φ', 'Psi': 'Ψ', 'Omega': 'Ω'}
SABIT = {'π', 'Δ', 'Σ'}   # sabit ya da işlem, büyüklük değil: adlandırılması ya da şemada görünmesi beklenmez
_TOK = re.compile(r'\\([A-Za-z]+)|([A-Za-zΑ-Ωα-ω])')


def _semboller(tex):
    """Formül metnindeki semboller: 'F_c', 'β', 'D_ort'. LaTeX ve Unicode yazımı aynı sonucu verir."""
    t = tex.replace('\u0307', '').replace('ϕ', 'φ')
    t = re.sub(r'_\{?\\mathrm\{(\w+)\}\}?', r'_{\1}', t)     # D_{\mathrm{ort}} -> D_{ort}
    t = re.sub(r'\\mathrm\{[^{}]*\}', ' ', t)                # MRR gibi adlar ve birimler
    t = re.sub(r'frac\{d([^{}]*)\}\{d([^{}]*)\}', r'frac{\1}{\2}', t)   # dT/dx: türev işareti sembol değil
    bul, i = set(), 0
    while True:
        m = _TOK.search(t, i)
        if not m:
            return bul - SABIT
        i = m.end()
        if m.group(1) and m.group(1) not in YUNAN:
            continue
        taban = YUNAN[m.group(1)] if m.group(1) else m.group(2)
        alt = re.match(r'\s*_(\{[^{}]*\}|\\[A-Za-z]+|.)', t[i:])
        if alt:
            i += alt.end()
            a = alt.group(1).strip('{}').lstrip('\\')
            taban += '_' + YUNAN.get(a, a)
        bul.add(taban)


def _sema_sembolleri(yazilar):
    """Şema yazıları -> (matematik yazılı semboller, düz yazıda tek başına duran harfler ('V', 'm/s'deki m, s))."""
    mat, duz = set(), set()
    for y in yazilar:
        for i, parca in enumerate(y.split('$')):
            if i % 2:
                mat |= _semboller(parca)
            else:
                duz |= set(re.findall(r'(?<![\wΑ-Ωα-ω])[A-Za-zΑ-Ωα-ω](?![\wΑ-Ωα-ω])', parca))
    return mat - SABIT, duz - SABIT


def _numaralar(n):
    """'(8.4–8.5)' -> {'8.4', '8.5'}; aralıkların ara numaraları da."""
    b = re.findall(r'(\d+)\.(\d+)', n or '')
    if len(b) == 2 and b[0][0] == b[1][0]:
        return {'%s.%d' % (b[0][0], k) for k in range(int(b[0][1]), int(b[1][1]) + 1)}
    return {'%s.%s' % x for x in b}


# ---------------------------------------------------------------- belge
class Sheet(BaseDocTemplate):
    def __init__(self, out, work, title, subtitle, header, source, renk=None):
        """renk: tema.PALET'ten bir ad = tek renkli kağıt; None = her kart sıradaki rengi alır."""
        global _EQD
        _EQD = os.path.join(work, 'eq'); os.makedirs(_EQD, exist_ok=True)
        self.dg = os.path.join(work, 'dg')
        super().__init__(out, pagesize=A4, leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
                         title=title, author=source)
        self.header, self.source, self.title_, self.subtitle = header, source, title, subtitle
        fr = Frame(LM, BM, FW, FH, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate('p', [fr], onPage=self._page)])
        self.story = []
        self.work, self._nums, self._tablolar, self._kartlar = work, set(), set(), []
        self.tema = Tema(title, renk)
        self._title()

    def _page(self, c, d):
        c.saveState(); c.setStrokeColor(CIZGI); c.setLineWidth(0.6)
        c.line(LM, PAGE_H - 1.25 * cm, PAGE_W - RM, PAGE_H - 1.25 * cm)
        c.setFont('Body-B', 8.5); c.setFillColor(KOYU); c.drawString(LM, PAGE_H - 1.07 * cm, self.header)
        c.setFont('Body', 8); c.setFillColor(GREY); c.drawRightString(PAGE_W - RM, PAGE_H - 1.07 * cm, self.source)
        c.line(LM, 1.05 * cm, PAGE_W - RM, 1.05 * cm)
        c.drawCentredString(PAGE_W / 2, 0.6 * cm, 'Sayfa %d' % d.page)
        c.restoreState()

    def _title(self):
        ana = colors.HexColor(self.tema.ana)
        t = Table([[Paragraph(self.title_, ParagraphStyle('t2', parent=st_title, textColor=ana))],
                   [Paragraph(self.subtitle, st_sub)]], colWidths=[FW])
        t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(self.tema.zemin)),
                               ('LINEBELOW', (0, -1), (-1, -1), 2, ana),
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

    def card(self, title, items, fig=None, cap=None, figw=0.40, figmaxh=5.6 * cm, renk=None):
        """Bir kavramın kartı. items: E(...) blokları, str (not satırı) ya da flowable (ör. d.tbl(...) elemanları).
        fig: şema adı (<work>/dg/ad.png) | png yolu | flowable listesi (tablo, P(...)) | None (tam genişlik).
        renk: bu kartın rengi (tema.PALET); None = sıradaki. Başlığında '(devam)' olan kart öncekinin rengini korur."""
        global _ANA
        if '(devam)' not in title or renk:
            self.tema.sonraki(renk)
        _ANA = self.tema.ana
        col = colors.HexColor(_ANA)
        for f in list(items) + (fig if isinstance(fig, list) else []):
            self._boya(f, col)
        self._sema_denetimi(title, items, fig)
        lab_st = ParagraphStyle('l-%s' % _ANA, parent=st_lab, textColor=col)
        lw = FW * (1 - figw) if fig is not None else FW
        left = []
        for it in items:
            if isinstance(it, tuple) and it and it[0] == 'eq':
                _, p, w, h, n, tm, lab, note, tex = it
                self._nums |= _numaralar(n)
                avail = lw - 12 - 1.6 * cm
                sc = min(1.0, avail / w)
                if sc < 0.8:
                    print('UYARI: formül %%%d küçültüldü, iki satıra böl ya da fs düşür: %s' % (sc * 100, tex[:70]),
                          file=sys.stderr)
                if lab: left.append(Paragraph(lab, lab_st))
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
        hdr = Paragraph(title, ParagraphStyle('c-%s' % _ANA, parent=st_card, textColor=col))
        cw = [lw, FW - lw] if fig is not None else [FW]
        data = [[hdr] + ([''] if fig is not None else []), body]
        t = Table(data, colWidths=cw)
        sty = [('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.tema.zemin)), ('SPAN', (0, 0), (-1, 0)),
               ('LINEBELOW', (0, 0), (-1, 0), 1.2, col),
               ('BOX', (0, 0), (-1, -1), 0.6, col), ('VALIGN', (0, 1), (-1, -1), 'TOP'),
               ('TOPPADDING', (0, 0), (-1, 0), 3), ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
               ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
               ('TOPPADDING', (0, 1), (-1, -1), 5)]
        if fig is not None:
            sty += [('VALIGN', (1, 1), (1, 1), 'MIDDLE'), ('LINEBEFORE', (1, 1), (1, 1), 0.4, CIZGI)]
        t.setStyle(TableStyle(sty))
        _, th = t.wrap(FW, FH)
        if th > FH:
            raise ValueError('Kart bir sayfaya sığmıyor (%.0f > %.0f pt): "%s" -> iki karta böl ("... (devam)")'
                             % (th, FH, re.sub('<[^>]+>', '', title)))
        self.story += [KeepTogether([t]), Spacer(1, 9)]

    @staticmethod
    def _boya(f, col):
        """d.tbl çıktısı kart çağrısından önce kurulur; rengini kart belirler."""
        if isinstance(f, Table) and getattr(f, '_tablo_rengi', None):
            sty = [('BACKGROUND', (0, 0), (-1, 0), col)]
            sty += [('BACKGROUND', (0, i), (-1, i), colors.HexColor(acik(_ANA, 0.92))) for i in range(2, f._nrows, 2)]
            f.setStyle(TableStyle(sty))
        elif isinstance(f, _P) and getattr(f, '_tablo_rengi', None):
            for parca in f.frags:
                parca.textColor = col

    def _sema_denetimi(self, title, items, fig):
        """Kartın sembollerini kaydeder; şemayla formül arasındaki farkları raporlar (dglib şema yazılarını kaydeder)."""
        tex = ' '.join(it[8] for it in items if isinstance(it, tuple) and it and it[0] == 'eq')
        form = _semboller(tex)
        ad = re.sub('<[^>]+>', '', title)
        self._kartlar.append((ad, form))
        if not isinstance(fig, str):
            return
        kayit = os.path.splitext(self._fig_path(fig))[0] + '.yazi.json'
        if not os.path.exists(kayit):
            return
        with open(kayit, encoding='utf-8') as f:
            mat, duz = _sema_sembolleri(json.load(f))
        yok, fazla = sorted(form - mat - duz), sorted(mat - form)
        if yok:
            print('ŞEMA "%s" (%s): formülde var, şemada yok: %s' % (ad, fig, ' '.join(yok)))
        if fazla:
            print('ŞEMA "%s" (%s): şemada var, formülde yok: %s' % (ad, fig, ' '.join(fazla)))

    def _kapsam_denetimi(self):
        """Adlandırılmamış sembolleri ve <work>/metin.txt içinde geçip kağıda girmeyen denklem/tabloları raporlar."""
        for ad, form in self._kartlar:
            yok = sorted(form - _ADLI)
            if yok:
                print('UYARI: "%s" kartında adlandırılmamış sembol: %s' % (ad, ' '.join(yok)), file=sys.stderr)
        yol = os.path.join(self.work, 'metin.txt')
        if not os.path.exists(yol):
            return
        with open(yol, encoding='utf-8') as f:
            metin = f.read()
        kaynak = set(re.findall(r'\((\d+\.\d+)\)', metin))
        bolumler = {n.split('.')[0] for n in self._nums}   # (0.15) gibi parantez içi sayılar elenir
        kaynak = {n for n in kaynak if n.split('.')[0] in bolumler}
        eksik = sorted(kaynak - self._nums, key=lambda s: [int(x) for x in s.split('.')])
        print('KAPSAM: kaynakta geçip kağıtta olmayan denklemler: %s' % (', '.join(eksik) or 'yok'))
        tablo = set(re.findall(r'\b(?:TABLE|Table|Tablo)\s+(\d+\.\d+)', metin))
        tablo = {n for n in tablo if n.split('.')[0] in bolumler} - self._tablolar
        print('KAPSAM: kaynakta geçip kağıtta olmayan tablolar: %s'
              % (', '.join(sorted(tablo, key=lambda s: [int(x) for x in s.split('.')])) or 'yok'))

    def tbl(self, rows, widths, title=None):
        """Sabitler / tipik değerler tablosu; ilk satır başlık. Liste döndürür: items'a `+ d.tbl(...)` ile ekle
        ya da fig=d.tbl(...) ile sağ sütuna koy."""
        data = [[Paragraph(str(c), st_cellh if i == 0 else st_cell) for c in r] for i, r in enumerate(rows)]
        t = Table(data, colWidths=widths)
        sty = [('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#AAAAAA')),
               ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 1.5),
               ('BOTTOMPADDING', (0, 0), (-1, -1), 2), ('LEFTPADDING', (0, 0), (-1, -1), 3)]
        t.setStyle(TableStyle(sty))
        t._tablo_rengi = True
        out = []
        if title:
            self._tablolar |= set(re.findall(r'Tablo\s+(\d+\.\d+)', title))
            b = Paragraph('<b>%s</b>' % title, ParagraphStyle('tt', parent=st_terms))
            b._tablo_rengi = True
            out.append(b)
        out.append(t)
        return out

    def pagebreak(self):
        self.story.append(PageBreak())

    def make(self):
        self.build(self.story)
        self._kapsam_denetimi()
        print('ok', self.filename, 'sayfa:', self.page)
