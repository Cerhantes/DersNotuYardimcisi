"""ÖRNEK içerik betiği — kaynaktan bağımsız, genel bir konu (ısı iletimi). Yalnızca KALIBI gösterir:
semboller tablosu, bölüm iskeleti (tanım → madde/formül/tablo/şekil → önemli → hızlı kontrol), problem tablosu,
kısa yanıtlar, eğilim tablosu, formül özeti, Kendini Sına. Kurallar için ../USLUP.md.
Gerçek notta konu, künye, numaralar ve her bilgi kullanıcının kaynağından gelir.

Çalıştırma: PYTHONPATH=<skill>/scripts py -W ignore ornek_tekrar_notu.py <cikti.pdf> <work>
<work>'te figs.json yoksa gri yer tutucu şekiller üretilir (gerçek akışta kaynak.py üretir).
"""
import sys, os, json
from tnlib import *

out, work = sys.argv[1], sys.argv[2]


def yer_tutucu(work, nums):
    if os.path.exists(os.path.join(work, 'figs.json')):
        return
    from PIL import Image as PI, ImageDraw
    os.makedirs(os.path.join(work, 'fig'), exist_ok=True)
    figs = {}
    for n in nums:
        im = PI.new('RGB', (480, 300), (225, 230, 238)); ImageDraw.Draw(im).text((20, 20), 'Sekil %s (yer tutucu)' % n, fill=(60, 60, 60))
        im.save(os.path.join(work, 'fig', n + '.png')); figs[n] = [0, [0, 0, 480, 300]]
    json.dump(figs, open(os.path.join(work, 'figs.json'), 'w'))


yer_tutucu(work, ['2.1', '2.2', '3.1'])
d = start(out, work, 'ISI İLETİMİ', 'Isı İletimi – Tekrar Notu', 'Kaynak: örnek içerik (kaynaktan bağımsız)')

d.cover([
    '<b>Kaynak:</b> Isi_Iletimi_Ders_Notu.pdf (n sayfa) — Yazar(lar), <i>Kitap Adı</i>, baskı, Bölüm n.1 – n.4.',
    '<b>Kapsam:</b> Ders notunun 1–3. bölümlerinin tamamı. Ek bilgi olarak işaretli bölüm yok.',
    '<b>Şekiller</b> kaynaktandır; numaraları kaynaktakiyle aynıdır.',
], [
    'Bu not yeniden öğretmek için değil, <b>tekrar</b> için yazıldı: her başlıkta bilmen gereken her bilgi madde madde, '
    'formüller numaralarıyla, eğilimler oklarla (↑ artar, ↓ azalır, → sonuç) verildi.',
    'Turuncu kutular sınavda en çok sorulan / karıştırılan noktalar, mavi kutular tanımlar, mor kutular bölüm sonu '
    'hızlı kontrol listesidir. Sonda tüm "neyi değiştirirsem ne olur" eğilimleri tek tabloda, problem sonuçları ve '
    'Kendini Sına sorularının cevapları vardır.',
])

# ======================================================================
d.h1('0. Semboller (hepsini tanıyabilmelisin)')
T([['Sembol', 'Anlamı', 'Sembol', 'Anlamı'],
   ['q', 'Isı akısı (W/m^2)', 'Q', 'Isı aktarım hızı (W)'],
   ['k', 'Isıl iletkenlik (W/m·K)', 'A', 'Isının geçtiği alan (m^2)'],
   ['L', 'Duvar kalınlığı (m)', 'ΔT', 'Sıcaklık farkı (K veya °C)'],
   ['R', 'Isıl direnç (K/W)', 'h', 'Taşınım katsayısı (W/m^2·K)']],
  [0.12, 0.38, 0.1, 0.4])

# ======================================================================
d.h1('1. Giriş: Isı Aktarımı')
BX('tanim', ['<b>Isı transferi (heat transfer):</b> sıcaklık farkı nedeniyle gerçekleşen enerji aktarımı; yönü daima sıcaktan soğuğa.'])
P('<b>Isı aktarımının yolları (3):</b>')
B(['<b>İletim (conduction):</b> katı içinde ya da değen cisimler arasında, madde hareket etmeden.',
   '<b>Taşınım (convection):</b> hareket eden akışkanla (ör. duvar yüzeyindeki rüzgâr).',
   '<b>Işınım (radiation):</b> elektromanyetik dalgalarla; ortam gerekmez.'], num=True)
X('onemli', 'Bu notun konusu <b>iletim</b>dir. Taşınım yalnız duvar yüzeyindeki direnç olarak (R = 1/(hA)) girer.')

# ======================================================================
d.h1('2. Fourier Yasası')
E('q = −k dT/dx', '(2.1)')
B(['Akı, sıcaklık gradyanıyla <b>doğru orantılı</b>; orantı katsayısı k.',
   '<b>Eksi işareti:</b> ısı, sıcaklığın azaldığı yönde akar. Büyüklük hesabında |ΔT| kullanılır.',
   'Kararlı halde düzlem levhada T(x) doğrusal → dT/dx = −ΔT/L sabit.'])
F2('2.1', '2.2', 'Düzlem levhada tek boyutlu iletim: T, sıcak yüzden soğuk yüze doğrusal azalır.',
   '(a) Metallerde k yüksek: serbest elektronlar; (b) gözenekli yalıtkanda hapsolmuş hava k\'yı düşürür.', h=130)
T([['Malzeme', 'k (W/m·K)'], ['Bakır', '≈ 400'], ['Alüminyum', '≈ 237'], ['Karbon çeliği', '≈ 50'],
   ['Tuğla', '≈ 0,7'], ['Su', '≈ 0,6'], ['Cam yünü', '≈ 0,04'], ['Hava', '≈ 0,026']], [0.5, 0.5],
  'Tablo 2.1 – Isıl iletkenlik (oda sıcaklığı, yaklaşık)')
X('ipucu', 'Metal korkuluk tahtadan daha soğuk hissettirir: sıcaklıkları aynı, ama metal elden ısıyı <b>daha hızlı</b> çeker (k ↑ → q ↑).')
BX('ozet', ['q = −k dT/dx; ısı sıcaklığın azaldığı yönde.',
            'k: metal ↑ (Cu ≈ 400), gaz ↓ (hava ≈ 0,026); yalıtkanlar hapsolmuş hava sayesinde düşük k.',
            'Kararlı hal + sabit k → doğrusal sıcaklık profili.'], 'BÖLÜM 2 HIZLI KONTROL')

# ======================================================================
d.h1('3. Düzlem Duvar ve Isıl Direnç')
E('Q = k A (T_1 − T_2) / L', '(3.1)')
B(['Q ∝ 1/L → kalınlık iki katı, ısı kaybı <b>yarı</b>.',
   'Ters çözülmüş biçim: <b>L = k A ΔT / Q</b> (gereken kalınlık hesabında en çok kullanılan biçim).',
   'Yalnız <b>kararlı halde</b> ve <b>sabit k</b> için geçerli.'])
E('R = L / (k A)     Q = ΔT / R', '(3.2)')
E('R_{taş} = 1 / (h A)', '(3.3)')
d.h3('1) Seri katmanlar')
B(['Aynı Q her katmandan geçer → dirençler toplanır: <b>R_{top} = R_1 + R_2 + …</b>',
   'Sıcaklık düşüşü katmanlara dirençleriyle orantılı paylaşılır: ΔT_i = Q R_i.'])
d.h3('2) Paralel yollar')
B(['Aynı ΔT her yolda → iletkenlikler (1/R) toplanır: <b>1/R_{top} = 1/R_1 + 1/R_2</b>.',
   'En düşük dirençli yol (ör. pencere camı, metal bağlantı) ısı kaybını belirler → <b>ısıl köprü</b>.'])
F('3.1', 'İki katmanlı duvar ve eşdeğer ısıl devre: seri dirençler; en büyük sıcaklık düşüşü en büyük dirençli katmanda.', maxh=190)
X('onemli', ['<b>Isı kaybı nasıl azaltılır? (4 yol — ezberle)</b>',
             '(a) k ↓ (yalıtkan malzeme) · (b) L ↑ · (c) A ↓ · (d) ΔT ↓'])
X('ornek', ['<b>Örnek 3.1 (yalıtım):</b> 10 m^2, 20 cm tuğla (k = 0,7), ΔT = 20 °C; üstüne 5 cm cam yünü (k = 0,04).',
            'Tuğla: Q = 0,7 × 10 × 20/0,2 = <b>700 W</b>. R_1 = 0,0286, R_2 = 0,125 K/W → Q = 20/0,1536 ≈ <b>130 W</b> (<b>%81</b> azalma).'])
BX('ozet', ['Q = kAΔT/L; L ↑ → Q ↓ (ters orantı).',
            'R = L/(kA); taşınım R = 1/(hA); seri → R toplanır, paralel → 1/R toplanır.',
            'En büyük ΔT en büyük dirençli katmanda; ince ama düşük k\'lı katman toplam direnci belirler.'], 'BÖLÜM 3 HIZLI KONTROL')

# ======================================================================
d.h1('4. Problem Çözme ve Kaynak Soruları')
X('onemli', ['<b>Çözüm sırası:</b> 1) her katmanın R = L/(kA), yüzeylerde R = 1/(hA) → 2) R_{top} (seri/paralel) → 3) Q = ΔT_{top}/R_{top} → '
             '4) ara yüz sıcaklıkları: T_{i+1} = T_i − Q R_i.'])
T([['Problem', 'Konu', 'Yol ve sonuç'],
   ['P1', 'Beton duvar', 'k = 1,4, A = 8 m^2, L = 0,3 m, ΔT = 15 °C → Q = 1,4 × 8 × 15/0,3 = <b>560 W</b>.'],
   ['P2', 'Gereken yalıtım', 'Tuğla duvar (R_1 = 0,0286 K/W), Q ≤ 200 W, ΔT = 20 → R_{top} = 0,1 → R_2 = 0,0714 → L_2 = R_2 k A = <b>≈ 2,9 cm</b> cam yünü.'],
   ['P3', 'Çelik levha', 'k = 50, A = 1 m^2, L = 1 cm, ΔT = 2 °C → Q = <b>10 kW</b>: metalde küçük ΔT bile büyük ısı akışı.']],
  [0.13, 0.19, 0.68], 'Problemlerin özeti')
d.h2('Kaynak sorularına kısa yanıtlar')
B(['<b>1</b> Eksi işareti: akı, sıcaklığın azaldığı yönde. <b>2</b> Kararlı hal: hiçbir noktada sıcaklık zamanla değişmez.',
   '<b>3</b> Gözenekli yalıtkanlar: katı iskelet ince, gözeneklerdeki hava hareketsiz → k havanınkine yakın.'])

# ======================================================================
d.h1('5. "Neyi Değiştirirsem Ne Olur?" — Tüm Eğilimler Tek Tabloda')
T([['Değişiklik', 'R', 'Q', 'Diğer'],
   ['Kalınlık L ↑', '↑', '↓ (Q ∝ 1/L)', 'Malzeme ve ağırlık ↑'],
   ['İletkenlik k ↑', '↓', '↑', 'Sıcaklık profili düzleşir'],
   ['Alan A ↑', '↓', '↑', '—'],
   ['Yüzeyde rüzgâr (h ↑)', 'R_{taş} ↓', '↑', 'Yüzey sıcaklığı ortam sıcaklığına yaklaşır'],
   ['Düşük k\'lı katman eklemek', '↑↑', '↓↓', 'En etkili önlem']],
  [0.26, 0.12, 0.2, 0.42])

# ======================================================================
d.h1('6. Formül Özeti')
T([['Konu', 'Bağıntı'],
   ['Fourier yasası', 'q = −k dT/dx'],
   ['Düzlem duvar', 'Q = kA(T_1 − T_2)/L; L = kAΔT/Q'],
   ['Isıl direnç', 'R = L/(kA); R_{taş} = 1/(hA); Q = ΔT/R'],
   ['Katmanlar', 'seri: R_{top} = ΣR_i; paralel: 1/R_{top} = Σ1/R_i; ΔT_i = Q R_i']], [0.24, 0.76])

# ======================================================================
d.h1('7. Kendini Sına — Kısa Cevaplı')
B(['<b>1.</b> Kalınlık iki katına çıkarsa? Q ∝ 1/L → <b>yarıya iner</b>.',
   '<b>2.</b> 10 cm bakır levhada ΔT = 10 °C → q = 400 × 10/0,1 = <b>40 000 W/m^2</b>.',
   '<b>3.</b> Seri iki katmanda en büyük sıcaklık düşüşü nerede? <b>Direnci en büyük</b> katmanda (ΔT_i = Q R_i).',
   '<b>4.</b> Neden pencere ısı kaybını belirler? Paralel yolda en düşük direnç → ısıl köprü.'])

d.make()
print('ok')
