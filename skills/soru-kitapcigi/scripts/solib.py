"""Çözümlü soru kitapçığı altyapısı. İçerik betiği:

    from solib import *
    d = start(out, work, 'KONU', 'Konu – Çözümlü Sorular', 'Kaynak: ...')
    kapak(['Kapsam: ...'], kaynakta_cevap=False, kapsam_notu='Çıkarılanlar ve nedenleri')
    bolum('Bölüm 5 – Döküm')
    konu('5.2 Metallerin Katılaşması')
    soru('5.82', ['5.2 Katılaşma', '5.8 Kum Döküm'], 'Soru metni', ['Adım', H('C = 3/12,5^2'), M(['madde']), TB(satirlar)],
         sonuc='≈ 0,5 dk', notu='kısa not', varsayim='k = 50 W/m·K alındı', sekil=[('5.10', 'Türkçe altyazı')])
    make()

Metinler tnlib'in S() süzgecinden geçer (x_o, x^2). Kart bir sayfaya sığıyorsa bölünmez; sığmıyorsa adım arasından
bölünür, bant "(devam)" ile tekrar eder. Tek adım bir sayfadan uzunsa ValueError: adımı böl.
Kartlar make()'te ölçülür ve aynı konu içinde sayfalara en az boşluk kalacak biçimde dağıtılır; numara sırası korunmaz.
bagli= ile işaretlenen sorular birlikte taşınır ve yan yana kalır.
"""
import json, os, sys

_KOK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_KOK, '..', '..', 'tekrar-notu', 'scripts'))
import tnlib
from tnlib import S, ss, FW, FH, Paragraph, Table, TableStyle, Image, ParagraphStyle, colors, cm
from reportlab.platypus import CondPageBreak, Flowable, Spacer
from tema import PALET, acik

__all__ = ['start', 'kapak', 'bolum', 'konu', 'soru', 'H', 'M', 'TB', 'G', 'make', 'R', 'S', 'cm']

d = None
_work = None
_IC = 10            # kart iç boşluğu (pt)
_ARA = 4            # kart parçaları arası (pt)
_IW = FW - 2 * _IC
_KART_ARA = 10       # kartlar arası (pt)
_KARMA = PALET['kirmizi']
_VARSAYIM = PALET['hardal']
_CIZGI = colors.HexColor('#BBBBBB')

_st_no = ParagraphStyle('so_no', fontName='Body-B', fontSize=11.5, leading=14)
_st_konu = ParagraphStyle('so_konu', fontName='Body', fontSize=8.8, leading=11, alignment=2)
_st_soru = ParagraphStyle('so_soru', parent=ss['body'], fontSize=10.5, leading=14, spaceAfter=0)
_st_adim = ParagraphStyle('so_adim', parent=ss['body'], fontSize=10, leading=13.4, spaceAfter=0)
_st_madde = ParagraphStyle('so_madde', parent=_st_adim, leftIndent=12, bulletIndent=2)
_st_not = ParagraphStyle('so_not', parent=_st_adim, fontName='Body-I', fontSize=9, leading=12, textColor=colors.HexColor('#666666'))


def start(out, work, title, header, source, subtitle='Çözümlü Sorular', renk=None):
    """work: figs.json + fig/ (yoksa boş figs.json yazılır), sonuc.json. renk: tek renkli kitapçık için palet adı."""
    global d, _work
    os.makedirs(work, exist_ok=True)
    yol = os.path.join(work, 'figs.json')
    if not os.path.exists(yol):
        with open(yol, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    _work = work
    d = tnlib.start(out, work, title, header, source, subtitle=subtitle, renk=renk)
    d._dizin, d._varsayimlar, d._dizin_yeri, d._kapsam_notu = {}, [], None, None
    d._bloklar, d._bolum_var = [], False
    return d


def kapak(kapsam, kaynakta_cevap, kapsam_notu=None):
    icerik = ['Her soru, sorusu ve çözümüyle birlikte tek kart hâlindedir. Kartın üstündeki bant sorunun konusunu söyler; '
              '<b>KARMA</b> etiketli sorularda birden çok konu birlikte kullanılır. Sorular sayfa düzenine göre dizildiği için numara sırasında olmayabilir.']
    if not kaynakta_cevap:
        icerik.append('Kaynakta cevap anahtarı yoktur; çözümler Claude tarafından yapılmıştır, sayısal sonuçlar Python ile hesaplanmıştır.')
    d.cover(kapsam, icerik, kutu='BU KİTAPÇIĞI NASIL KULLANMALISIN?')
    d._dizin_yeri = len(d.story) - 1    # içindekilerin ardı, son PageBreak'ten önce
    d._kapsam_notu = kapsam_notu


def _blok(baslik=None):
    """Kartı olmayan son bloğa başlık ekler, yoksa yeni blok açar."""
    if not d._bloklar or (d._bloklar[-1]['gruplar'] and baslik is not None):
        d._bloklar.append({'basliklar': [], 'gruplar': []})
    if baslik is not None:
        d._bloklar[-1]['basliklar'].append(baslik)
    return d._bloklar[-1]


def bolum(ad):
    d.tema.sonraki()
    d._bolum_var = True
    _blok(d._hp(ad, d._renkli('h1'), 0))


def konu(ad, renk=None):
    d.tema.sonraki(renk)
    _blok(d._hp(ad, d._renkli('h2'), 1 if d._bolum_var else 0))


def H(metin):
    """Hesap satırı: açık zeminli, sol çizgili."""
    t = Table([[Paragraph(S(metin), _st_adim)]], colWidths=[_IW])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F4F5F7')),
                           ('LINEBEFORE', (0, 0), (0, -1), 2, colors.HexColor(d.ana)),
                           ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                           ('LEFTPADDING', (0, 0), (-1, -1), 8)]))
    return t


def M(maddeler):
    """Madde listesi; her madde ayrı adımdır (kart gerekirse maddeler arasından bölünür)."""
    return [Paragraph(S(m), _st_madde, bulletText='•') for m in maddeler]


def TB(satirlar, genislikler=None, baslik=None):
    """Tablo; ilk satır başlık. genislikler: oranlar (toplam 1). baslik: 'Tablo 8.5 – Açıklama' (kitap tablosunda zorunlu)."""
    veri = [[Paragraph(S(str(h)), ss['cellh'] if i == 0 else ss['cell']) for h in r] for i, r in enumerate(satirlar)]
    t = Table(veri, colWidths=[g * _IW for g in genislikler] if genislikler else [_IW / len(satirlar[0])] * len(satirlar[0]))
    st = [('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(d.ana)), ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#AAAAAA')),
          ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]
    t.setStyle(TableStyle(st))
    if not baslik:
        return t
    dis = Table([[Paragraph('<b><font color="%s">%s</font></b>' % (d.ana, S(baslik)), ss['cap'])], [t]], colWidths=[_IW])
    dis.setStyle(TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                             ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]))
    return dis


def G(yol, altyazi, maxh=170):
    """Çözümün parçası olan grafik (hesap.py'nin çizdiği PNG); kitap şekli için soru(sekil=...) kullan."""
    from PIL import Image as PI
    with PI.open(yol) as im:
        gen, yuk = im.size
    h = min(maxh, _IW * yuk / gen)
    img = Image(yol, width=h * gen / yuk, height=h)
    img.hAlign = 'CENTER'
    t = Table([[img], [Paragraph(S(altyazi), ss['cap'])]], colWidths=[_IW])
    t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('TOPPADDING', (0, 0), (-1, -1), 1), ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]))
    return t


def R(no, ad):
    """hesap.py'nin sonuc.json'a yazdığı biçimli değer."""
    yol = os.path.join(_work, 'sonuc.json')
    veri = {}
    if os.path.exists(yol):
        with open(yol, encoding='utf-8') as f:
            veri = json.load(f)
    if ad not in veri.get(no, {}):
        raise KeyError('hesap.py içinde yok: %s/%s' % (no, ad))
    return veri[no][ad]


def _giris_mi(f):
    return hasattr(f, 'getPlainText') and f.getPlainText().rstrip().endswith(':')


class _Kart(Flowable):
    """Bant + baş (soru, şekil, ÇÖZÜM) + adımlar. Sayfaya sığmayan kart adım sınırından bölünür."""

    def __init__(self, no, konular, bas, adimlar, renk, devam=False):
        super().__init__()
        self.no, self.konular, self.bas, self.adimlar, self.renk, self.devam = no, konular, bas, adimlar, renk, devam
        self.spaceAfter = _KART_ARA
        self._bant_olustur()

    def _bant_olustur(self):
        renk = _KARMA if len(self.konular) > 1 else self.renk
        self._bant_renk = renk
        no = 'Soru %s%s' % (self.no, ' (devam)' if self.devam else '')
        yazi = 'KARMA · ' + ' + '.join(self.konular) if len(self.konular) > 1 else self.konular[0]
        self._p_no = Paragraph('<font color="%s">%s</font>' % (renk, no), _st_no)
        self._p_konu = Paragraph('<font color="%s">%s</font>' % (renk, S(yazi)), _st_konu)
        self._gen_no = 0.3 * FW
        self._gen_konu = FW - self._gen_no - 2 * _IC
        h1 = self._p_no.wrap(self._gen_no, FH)[1]
        h2 = self._p_konu.wrap(self._gen_konu, FH)[1]
        self._bant_h = max(h1, h2) + 10

    def _yukseklik(self, f):
        h = f.wrap(_IW, FH)[1]
        return h + _ARA

    def _bas_h(self):
        return self._bant_h + _ARA + sum(self._yukseklik(f) for f in self.bas)

    def wrap(self, aW, aH):
        self._olc()
        self.width = FW
        self.height = self._bas_h() + sum(self._yukseklik(f) for f in self.adimlar) + _IC / 2
        return self.width, self.height

    def _olc(self):
        sinir = FH - 2
        ilk = self._yukseklik(self.adimlar[0]) if self.adimlar else 0
        if self._bas_h() + ilk + _IC / 2 > sinir:
            raise ValueError('Soru %s: soru metni, şekil ve ilk adım bir sayfaya sığmıyor; böl ya da küçült' % self.no)
        for f in self.adimlar:
            if self._bant_h + _ARA + self._yukseklik(f) + _IC / 2 > sinir:
                raise ValueError('Soru %s: adım bir sayfadan uzun, böl' % self.no)

    def split(self, aW, aH):
        self.wrap(aW, aH)
        if self.height <= FH - 2:
            return []                   # bütün kalır: sonraki sayfaya geçer
        kalan = aH - self._bas_h() - _IC / 2
        n = 0
        for f in self.adimlar:
            h = self._yukseklik(f)
            if h > kalan:
                break
            kalan -= h
            n += 1
        sigan = n
        while n and _giris_mi(self.adimlar[n - 1]):      # ":" ile biten adım sonraki adımdan ayrılmaz
            n -= 1
        if n == 0:
            if aH < FH - 2 or not sigan:
                return []
            n = sigan                                    # boş sayfada başka yol yok: kural gevşer, derleme çökmez
        return [_Kart(self.no, self.konular, self.bas, self.adimlar[:n], self.renk, self.devam),
                _Kart(self.no, self.konular, [], self.adimlar[n:], self.renk, True)]

    def en_az(self):
        """Kartın başlıklarıyla birlikte sayfada kalması için gereken en küçük yükseklik."""
        h = self.wrap(FW, FH)[1]
        if h <= FH - 2:
            return h
        return self._bas_h() + (self._yukseklik(self.adimlar[0]) if self.adimlar else 0) + _IC / 2

    def kuyruk(self, tam):
        """Boş sayfadan başlarsa son parçanın altında kalan yer."""
        k = self
        while k.wrap(FW, FH)[1] > tam:
            k = k.split(FW, tam)[1]
        return tam - k.wrap(FW, FH)[1] - _KART_ARA

    def draw(self):
        c = self.canv
        W, Y = self.width, self.height
        c.saveState()
        c.setFillColor(colors.HexColor(acik(self._bant_renk)))
        c.rect(0, Y - self._bant_h, W, self._bant_h, fill=1, stroke=0)
        c.setFillColor(colors.HexColor(self._bant_renk))
        c.rect(0, Y - self._bant_h, 3.5, self._bant_h, fill=1, stroke=0)
        c.setStrokeColor(_CIZGI)
        c.setLineWidth(0.6)
        c.rect(0, 0, W, Y, fill=0, stroke=1)
        c.restoreState()
        h = self._p_no.wrap(self._gen_no, FH)[1]
        self._p_no.drawOn(c, _IC, Y - self._bant_h + (self._bant_h - h) / 2)
        h = self._p_konu.wrap(self._gen_konu, FH)[1]
        self._p_konu.drawOn(c, self._gen_no + _IC, Y - self._bant_h + (self._bant_h - h) / 2)
        y = Y - self._bant_h - _ARA
        for f in list(self.bas) + list(self.adimlar):
            h = f.wrap(_IW, FH)[1]
            y -= h
            f.drawOn(c, _IC, y)
            y -= _ARA


def _sekil_parcalari(no, sekil):
    parca = []
    for num, alt in sekil:
        if num not in d.figs:
            raise KeyError('Soru %s: şekil yok (figs.json): %s' % (no, num))
        _, rc = d.figs[num]
        wpt, hpt = rc[2] - rc[0] + 10, rc[3] - rc[1] + 10
        w = min(wpt * 0.92, _IW - 4)
        h = w * hpt / wpt
        if h > 200:
            h = 200
            w = h * wpt / hpt
        img = Image(os.path.join(_work, 'fig', num + '.png'), width=w, height=h)
        img.hAlign = 'CENTER'
        yazi = Paragraph('<b><font color="%s">Şekil %s</font></b> – %s' % (d.ana, num, S(alt)), ss['cap'])
        t = Table([[img], [yazi]], colWidths=[_IW])
        t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('TOPPADDING', (0, 0), (-1, -1), 1), ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]))
        parca.append(t)
    return parca


def soru(no, konular, metin, adimlar, sonuc=None, notu=None, varsayim=None, sekil=(), ek=(), bagli=None):
    """no: kaynaktaki numara. konular: ilki ana konu; birden çoksa KARMA. adimlar: str | H | M | TB | G | flowable.
    ek: sorunun kendi verisi (ör. TB), soru metninin ardına, ÇÖZÜM'den önce konur.
    bagli: bu sorunun dayandığı sorunun numarası; ikisi yan yana kalır."""
    kutu = Table([[Paragraph(S(metin), _st_soru)]], colWidths=[_IW])
    kutu.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F7F8FA')),
                              ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 6)]))
    baslik = Paragraph('<b><font color="%s">ÇÖZÜM</font></b>' % d.ana, ss['boxt'])
    bas = [kutu] + list(ek) + _sekil_parcalari(no, sekil) + [baslik]
    parcalar = []
    for a in adimlar:
        if isinstance(a, str):
            parcalar.append(Paragraph(S(a), _st_adim))
        elif isinstance(a, list):
            parcalar += a
        else:
            parcalar.append(a)
    if varsayim:
        parcalar.append(Paragraph('<b><font color="%s">Varsayım:</font></b> %s' % (_VARSAYIM, S(varsayim)), _st_adim))
        d._varsayimlar.append((no, varsayim))
    if sonuc:
        t = Table([[Paragraph('<b>Sonuç:</b> %s' % S(sonuc), _st_adim)]], colWidths=[_IW])
        t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(d.tema.zemin)),
                               ('BOX', (0, 0), (-1, -1), 0.7, colors.HexColor(d.ana)),
                               ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
        parcalar.append(t)
    if notu:
        parcalar.append(Paragraph(S(notu), _st_not))
    d._dizin.setdefault(konular[0], []).append(no)
    kart = _Kart(no, list(konular), bas, parcalar, d.ana)
    blok = _blok()
    for g in blok['gruplar']:
        if bagli and any(k.no == bagli for k in g):
            g.append(kart)
            return
    blok['gruplar'].append([kart])


def _paketle(boylar, ilk, tam, kuyruk=None):
    """Best-fit decreasing: boylar sayfalara dağıtılır. ilk: içinde bulunulan sayfada kalan yer, tam: boş sayfa.
    Dönüş: (sayfa başına öğe sırası listesi, son sayfada kalan yer). Sayfadan uzun öğe kendi kutusunu açar;
    son parçasının altında kalan yere (kuyruk[i]) başka öğe konabilir."""
    kuyruk = kuyruk or {}
    kutular = [{'kalan': ilk, 'oge': [], 'uzun': False}]
    for i in sorted(range(len(boylar)), key=lambda x: (-boylar[x], x)):
        h = boylar[i]
        if h > tam:
            kutular.append({'kalan': kuyruk.get(i, tam - h % tam), 'oge': [i], 'uzun': True})
            continue
        uygun = [k for k in kutular if k['kalan'] >= h]
        if uygun:
            k = min(uygun, key=lambda x: x['kalan'])
        else:
            k = {'kalan': tam, 'oge': [], 'uzun': False}
            kutular.append(k)
        k['oge'].append(i)
        k['kalan'] -= h
    ilk_kutu, geri = kutular[0], kutular[1:]
    geri.sort(key=lambda k: (not k['uzun'], k['kalan']))     # en boş sayfa sona: sonraki konu orada başlayabilsin
    sira = [ilk_kutu] + geri
    return [k['oge'] for k in sira if k['oge']], sira[-1]['kalan']


def _yerlestir():
    """Kartları ölç, konu konu en az boşlukla sayfalara dağıt, story'ye ekle."""
    tam = FH - 2
    kalan = tam
    for b in d._bloklar:
        basliklar = b['basliklar']
        bas_h = sum(p.wrap(FW, FH)[1] + p.getSpaceBefore() + p.getSpaceAfter() for p in basliklar)
        boylar = [sum(k.wrap(FW, FH)[1] + _KART_ARA for k in g) for g in b['gruplar']]
        if not boylar:
            d.story += basliklar
            continue
        ilk = kalan - bas_h
        if ilk < min(boylar) and not any(h > tam for h in boylar):
            ilk = tam - bas_h
        kuyruk = {i: g[0].kuyruk(tam) for i, g in enumerate(b['gruplar']) if len(g) == 1 and boylar[i] > tam}
        plan, kalan = _paketle(boylar, ilk, tam, kuyruk)
        sira = [b['gruplar'][i] for sayfa in plan for i in sayfa]
        d.story.append(CondPageBreak(bas_h + sira[0][0].en_az() + 1))
        d.story += basliklar
        for g in sira:
            d.story += g


def make():
    if d._dizin_yeri is not None:
        satir = [['Konu', 'Sorular']] + [[k, ', '.join(n)] for k, n in d._dizin.items()]
        veri = [[Paragraph(str(h), ss['cellh'] if i == 0 else ss['cell']) for h in r] for i, r in enumerate(satir)]
        t = Table(veri, colWidths=[0.35 * FW, 0.65 * FW], repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(d.ana)),
                               ('LINEBELOW', (0, 0), (-1, -1), 0.4, _CIZGI), ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
        ek = [Spacer(1, 10), Paragraph('Soru dizini', d._renkli('h2')), t]
        if d._kapsam_notu:
            ek += [Spacer(1, 8), Paragraph('<b>Kapsam notu.</b> ' + S(d._kapsam_notu), ss['cap'])]
        d.story[d._dizin_yeri:d._dizin_yeri] = ek
    _yerlestir()
    for no, metin in d._varsayimlar:
        print('VARSAYIM %s: %s' % (no, metin), file=sys.stderr)
    d.make()
