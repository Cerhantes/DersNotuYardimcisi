"""ÖRNEK içerik betiği — kaynaktan bağımsız, genel bir konu (ısı iletimi, 3 kart). Yalnızca üslubu gösterir;
ders adı, kaynak satırı, kapsam ve formüller her seferinde verilen kaynaktan gelir. Kurallar için ../USLUP.md.
Kalıp: kart = bir kavram · her formül: etiket + formül + (kaynaktaki no) + terimler + ► kısa not ·
sabit/tipik değer tablosu kartın içinde · sağ sütunda sembolleri gösteren şema · "Uygulama:" satırı.
Çalıştırma: PYTHONPATH=<skill>/scripts python -W ignore ornek_kagit.py <cikti.pdf> <work>
(önce ornek_semalar.py <work> çalışmış olmalı)
"""
import sys
from fslib import *

d = Sheet(sys.argv[1], sys.argv[2], 'ISI İLETİMİ – FORMÜL KAĞIDI',
          'Ders adı · Kapsam: Bölüm n.1–n.4 (Fourier yasası, düzlem duvar, ısıl direnç) · '
          'Denklem numaraları kaynaktakiyle aynıdır',
          'Isı İletimi – Formül Kağıdı', 'Yazar, Kitap Adı, Bölüm n')
E = d.E

# 1 ─ Fourier yasası
k_tbl = d.tbl([['Malzeme', 'k (W/m·K)'],
               ['Bakır', '≈ 400'], ['Alüminyum', '≈ 237'], ['Karbon çeliği', '≈ 50'],
               ['Tuğla', '≈ 0,7'], ['Cam yünü', '≈ 0,04'], ['Hava', '≈ 0,026']],
              [3.6 * cm, 2.4 * cm], 'Tablo 2.1 – Isıl iletkenlik (oda sıcaklığı)')
d.card('1 · Fourier Yasası (Fourier\'s law of conduction)', [
    E(r'q=-k\,\frac{dT}{dx}', '(2.1)',
      terms(('q', 'ısı akısı (W/m²)'), ('k', 'ısıl iletkenlik (W/m·K)'), ('T', 'sıcaklık'), ('x', 'ısı akışı yönündeki konum')),
      label='Isı akısı', note='Eksi işareti: ısı, sıcaklığın azaldığı yönde akar.'),
    E(r'q=k\,\frac{T_1-T_2}{L}', '',
      terms(('T_1, T_2', 'sıcak ve soğuk yüz sıcaklıkları'), ('L', 'kalınlık (m)')),
      label='Kararlı hal, düzlem levha (doğrusal profil)'),
] + k_tbl, fig='profil', figw=0.40, cap='Düzlem levhada sıcaklık sıcak yüzden soğuk yüze doğrusal azalır; q bu yönde akar.')

# 2 ─ düzlem duvar ve ısıl direnç
d.card('2 · Düzlem Duvar ve Isıl Direnç (thermal resistance)', [
    E(r'Q=k\,A\,\frac{T_1-T_2}{L}', '(3.1)',
      terms(('Q', 'duvardan geçen ısı (W)'), ('A', 'duvar alanı (m²)')), label='Duvardan geçen ısı'),
    E(r'L=\frac{k\,A\,\Delta T}{Q}', '', 'Gereken kalınlık hesabında kullanılan ters çözülmüş biçim.', label='Kalınlık'),
    E(r'R=\frac{L}{k\,A},\qquad Q=\frac{\Delta T}{R}', '(3.2)',
      terms(('R', 'ısıl direnç (K/W)'), ('ΔT', 'sıcaklık farkı (K)')), label='İletim direnci',
      note='Ohm yasası benzeri: ΔT ↔ gerilim, Q ↔ akım.'),
    E(r'R_{\mathrm{taş}}=\frac{1}{h\,A}', '(3.3)', terms(('R_taş', 'taşınım direnci (K/W)'), ('h', 'taşınım katsayısı (W/m²·K)')), label='Yüzeydeki taşınım direnci'),
    '<b>Uygulama:</b> 10 m², 20 cm tuğla (k = 0,7), ΔT = 20 °C → Q = 0,7 × 10 × 20/0,2 = 700 W; kalınlık 10 cm olsaydı 1400 W.',
], fig='kalinlik', figw=0.40, cap='Q ∝ 1/L: kalınlık iki katı → ısı kaybı yarı.')

# 3 ─ katmanlı duvar
d.card('3 · Katmanlı Duvar: Seri Dirençler', [
    E(r'R_{\mathrm{top}}=R_1+R_2+\cdots,\qquad Q=\frac{T_1-T_2}{R_{\mathrm{top}}}', '',
      terms(('R_1, R_2', 'katmanların dirençleri'), ('R_top', 'toplam direnç')), label='Seri katmanlar'),
    E(r'T_i=T_1-Q\,R_1', '', terms(('T_i', 'iki katman arasındaki ara yüz sıcaklığı')), label='Ara yüz sıcaklığı',
      note='En büyük sıcaklık düşüşü en büyük dirençli katmandadır.'),
    E(r'\frac{1}{R_{\mathrm{top}}}=\frac{1}{R_1}+\frac{1}{R_2}', '', 'Aynı ΔT altında yan yana yollar (ör. duvar + pencere).',
      label='Paralel yollar'),
    '<b>Uygulama:</b> tuğlaya 5 cm cam yünü (k = 0,04): R = 0,0286 + 0,125 = 0,154 K/W → Q = 20/0,154 ≈ 130 W (%81 azalma).',
], fig='devre', figw=0.40, cap='Katmanlar seri dirençler gibi davranır; yalıtım katmanında sıcaklık hızla düşer.')

d.make()
