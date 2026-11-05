"""ÖRNEK içerik betiği: kaynaktan bağımsız, genel bir konu (ısı iletimi). Soruları bu örnek için yazılmıştır, kitaptan alınmamıştır.
Kalıp: bant + soru + gerekirse şekil + ÇÖZÜM adımları + sonuç + not. Kurallar için ../USLUP.md.

Çalıştırma (önce ornek_hesap.py):
  PYTHONPATH=<skill>/scripts python -W ignore ornek_soru_kitapcigi.py <cikti.pdf> <work>
<work>'te figs.json yoksa gri yer tutucu şekil üretilir (gerçek akışta şekiller kitaptan kesilir).
"""
import json, os, sys
from solib import *

out, work = sys.argv[1], sys.argv[2]


def yer_tutucu(work, nums):
    if os.path.exists(os.path.join(work, 'figs.json')):
        return
    from PIL import Image as PI, ImageDraw
    os.makedirs(os.path.join(work, 'fig'), exist_ok=True)
    figs = {}
    for n in nums:
        im = PI.new('RGB', (480, 220), (225, 230, 238))
        ImageDraw.Draw(im).text((20, 20), 'Sekil %s (yer tutucu)' % n, fill=(90, 90, 90))
        im.save(os.path.join(work, 'fig', n + '.png'))
        figs[n] = [0, [0, 0, 480, 220]]
    json.dump(figs, open(os.path.join(work, 'figs.json'), 'w'))


yer_tutucu(work, ['2.1'])
ILETIM, DUVAR = '2. Fourier Yasası', '3. Düzlem Duvar ve Isıl Direnç'

d = start(out, work, 'ISI İLETİMİ', 'Isı İletimi – Çözümlü Sorular', 'Kaynak: örnek içerik (kitaptan bağımsız)')
kapak(['<b>Kapsam:</b> Fourier yasası, düzlem duvar, ısıl direnç (5 soru)'], kaynakta_cevap=False,
      kapsam_notu='Bu örnekte soru çıkarılmamıştır. Gerçek kitapçıkta çıkarılan sorular ve nedenleri burada yazar.')

bolum('Bölüm 2 – Isı İletimi')

konu(ILETIM)
soru('2.1', [ILETIM],
     '10 m² alanlı, 20 cm kalınlığında tuğla duvarın (k = 0,7 W/m·K) iki yüzü arasındaki sıcaklık farkı 20 °C\'dir. '
     'Şekil 2.1\'i de kullanarak duvardan geçen ısıyı bulunuz.',
     ['Kararlı hal, tek boyutlu iletim, sabit k kabul edilir.',
      H('Q = k A ΔT / L = 0,7 × 10 × 20 / 0,2 = <b>%s</b>' % R('2.1', 'Q'))],
     sonuc='Duvardan geçen ısı %s.' % R('2.1', 'Q'),
     sekil=[('2.1', 'Düzlem duvarda doğrusal sıcaklık profili.')])

soru('2.2', [ILETIM],
     'Soru 2.1\'deki duvarın kalınlığı iki katına çıkarılırsa ısı kaybı nasıl değişir?',
     ['Q, L ile ters orantılıdır (Q ∝ 1/L).', H('Q = 0,7 × 10 × 20 / 0,4 = <b>%s</b>' % R('2.2', 'Q'))],
     sonuc='Isı kaybı yarıya iner: %s.' % R('2.2', 'Q'),
     notu='Eşitlik yalnız kararlı hal ve sabit k için geçerlidir.')

soru('2.3', [ILETIM],
     'Metallerin ısıl iletkenliği yalıtkanlardan neden çok daha yüksektir? Tablo 2.1\'deki değerlerle açıklayınız.',
     [M(['<b>Metaller:</b> ısıyı serbest elektronlar da taşır.',
         '<b>Yalıtkanlar:</b> gözeneklerdeki hareketsiz hava iletimi düşürür.']),
      TB([['Malzeme', 'k (W/m·K)'], ['Bakır', '≈ 400'], ['Tuğla', '≈ 0,7'], ['Cam yünü', '≈ 0,04']], [0.6, 0.4])],
     sonuc='Fark, ısıyı taşıyan mekanizmadan kaynaklanır.')

konu(DUVAR)
soru('3.1', [DUVAR, ILETIM],
     '10 m² alanlı duvar, 20 cm tuğla (k = 0,7 W/m·K) ve 5 cm cam yününden oluşmaktadır. İki dış yüz arasındaki fark 20 °C\'dir. '
     'Toplam ısıl direnci ve duvardan geçen ısıyı bulunuz.',
     ['Katmanlar seri bağlıdır, dirençler toplanır.',
      H('R_1 = 0,2 / (0,7 × 10) ; R_2 = 0,05 / (0,04 × 10)'),
      H('R_{top} = R_1 + R_2 = <b>%s</b>' % R('3.1', 'Rtop')),
      H('Q = ΔT / R_{top} = 20 / R_{top} = <b>%s</b>' % R('3.1', 'Q'))],
     sonuc='R_{top} = %s, Q = %s.' % (R('3.1', 'Rtop'), R('3.1', 'Q')),
     varsayim='Cam yünü için k = 0,04 W/m·K alındı; soruda verilmemiştir.')

soru('3.2', [DUVAR],
     'Pencere camı duvara göre çok ince bir tabaka olmasına rağmen ısı kaybını neden büyük ölçüde belirler?',
     ['Paralel yollarda ısı en düşük dirençli yolu tercih eder: aynı ΔT altında akı direnci küçük olan yolda büyür.'],
     sonuc='Düşük dirençli cam, toplam ısı kaybında baskındır.')

make()
