"""ÖRNEK içerik betiği — kitaptan bağımsız, genel bir konu (ısı iletimi). Yalnızca KALIBI gösterir:
bölüm girişi, terim yazımı, kutular, denklem + sembol açıklaması, şekil + terimler, çözümlü örnek, özet, Kendini Sına.
Kurallar için ../USLUP.md. Gerçek notta konu, künye, şekil ve denklem numaraları kullanıcının kitabından gelir.

Çalıştırma: PYTHONPATH=<skill>/scripts python -W ignore ornek_ders_notu.py <cikti.pdf> <work>
<work>'te figs.json yoksa gri yer tutucu şekiller üretilir (gerçek akışta crop_figs.py üretir).
"""
import sys, os, json
from notlib import *

out, work = sys.argv[1], sys.argv[2]


def yer_tutucu(work, nums):
    if os.path.exists(os.path.join(work, 'figs.json')):
        return
    from PIL import Image as PI, ImageDraw
    os.makedirs(os.path.join(work, 'fig'), exist_ok=True)
    figs = {}
    for n in nums:
        im = PI.new('RGB', (520, 300), (225, 230, 238)); ImageDraw.Draw(im).text((20, 20), 'Şekil %s (yer tutucu)' % n, fill=(60, 60, 60))
        im.save(os.path.join(work, 'fig', n + '.png')); figs[n] = [0, [0, 0, 520, 300]]
    json.dump(figs, open(os.path.join(work, 'figs.json'), 'w'))


yer_tutucu(work, ['2.1', '2.2', '3.1'])
d = Doc(out, 'ISI İLETİMİ', 'Fourier Yasası, Isıl Direnç ve Bileşik Duvarlar — Ders Notu', 'Isı İletimi – Ders Notu',
        work, 'Kaynak: örnek içerik (kitaptan bağımsız)')
M = lambda s: '<font name="Math">%s</font>' % s   # satır içi matematik

d.cover([
    '<b>Kapsam:</b> Ders kitabı PDF sayfaları a–b (Bölüm n.1 – n.4)',
    '<b>Kaynak:</b> Yazar(lar) – <i>Kitap Adı</i>, baskı, yayınevi, yıl (Bölüm n).',
    '<b>Şekiller:</b> Tüm şekiller ders kitabından alınmıştır; numaraları kitaptaki numaralarla aynıdır.',
], [
    'Not, konuyu hiç bilmeyen birinin sırayla okuyarak öğrenebileceği şekilde kurgulanmıştır: önce <b>ısının neden ve nasıl aktığı</b>, '
    'sonra <b>tek bir duvardan geçen ısının hesabı</b>, en sonunda da <b>katmanlı duvarlar ve yalıtım</b> anlatılır.',
    'Mavi kutular <b>tanımları</b>, turuncu kutular <b>mutlaka bilinmesi gerekenleri</b>, yeşil kutular <b>çözümlü örnekleri</b>, konu renginde kutular ise '
    '<b>bölüm özetlerini</b> içerir. Şekillerdeki İngilizce etiketlerin Türkçe karşılıkları her şeklin altında verilmiştir.',
])

# =====================================================================
d.h1('1. Giriş: Isı Nedir, Nasıl Aktarılır?')
d.p('Bir fincan sıcak çayın zamanla soğuması ya da kışın evden dışarı ısı kaçması, günlük hayatta en sık karşılaştığımız enerji aktarımlarıdır. '
    'Temel fikir basittir: <b>sıcaklık farkı olan her yerde ısı, sıcak bölgeden soğuk bölgeye doğru akar.</b>')
d.box('tanim', '<b>Isı transferi</b> (heat transfer): Sıcaklık farkı nedeniyle iki sistem ya da bir sistemin iki bölgesi arasında gerçekleşen enerji aktarımıdır.')
d.p('Isı üç yolla aktarılır: katı içinde ya da birbirine değen cisimler arasında <b>iletim</b> (conduction), hareket eden akışkanla <b>taşınım</b> (convection) '
    've elektromanyetik dalgalarla <b>ışınım</b> (radiation). Bu not iletimi anlatır; taşınım yalnızca duvar yüzeyindeki sınır koşulu olarak girer.')
d.box('onemli', ['Bir duvardan geçen ısıyı belirleyen <b>dört büyüklük</b> vardır ve notun geri kalanı bunların etrafında şekillenir:',
                 '1) İki yüz arasındaki <b>sıcaklık farkı</b>,<br/>2) Duvarın <b>alanı</b>,<br/>3) Duvarın <b>kalınlığı</b>,<br/>4) Malzemenin <b>ısıl iletkenliği</b>.'],
      title='İLETİMİN DÖRT BELİRLEYİCİSİ')
d.box('ozet', ['• Sıcaklık farkı olan her yerde ısı sıcaktan soğuğa akar.',
               '• Üç aktarım yolu vardır: iletim, taşınım, ışınım; bu not iletimi anlatır.'],
      title='BÖLÜM 1 ÖZETİ')

# =====================================================================
d.h1('2. Fourier Yasası')
d.p('Duvardan ne kadar ısı geçtiğini hesaplayabilmek için önce, bir malzemenin içinde ısının hangi hızla aktığını veren yasayı bilmek gerekir.')
d.h2('2.1 Isı Akısı ve Sıcaklık Gradyanı')
d.p('Kalınlığı boyunca bir yüzü sıcak, öbür yüzü soğuk tutulan bir levha düşünelim (Şekil 2.1). Isı, sıcak yüzden soğuk yüze doğru akar ve '
    'levha içindeki sıcaklık bu yönde düzenli olarak azalır. Birim alandan birim zamanda geçen ısıya <b>ısı akısı</b> (heat flux) denir ve şu bağıntıyla verilir:')
d.eq('q = − k dT/dx', '(2.1)')
d.p('Burada ' + M('q') + ' ısı akısı (W/m²), ' + M('k') + ' malzemenin <b>ısıl iletkenliği</b> (thermal conductivity, W/m·K), ' + M('dT/dx') +
    ' ise sıcaklık gradyanıdır. <b>Eksi işareti, ısının sıcaklığın azaldığı yönde aktığını gösterir.</b>')
d.fig('2.1', 'Düzlem bir levhada tek boyutlu ısı iletimi: sıcaklık sıcak yüzden soğuk yüze doğrusal olarak azalır; ısı akısı aynı yöndedir. Eğimin işaretine dikkat edin.',
      terms='Hot surface = sıcak yüz; Cold surface = soğuk yüz; Heat flux = ısı akısı; Thickness = kalınlık.', scale=0.85)
d.box('tanim', '<b>Isıl iletkenlik</b> (thermal conductivity): Bir malzemenin ısıyı iletme yeteneğidir; 1 m kalınlığındaki malzemenin iki yüzü arasında 1 K fark varken '
      '1 m²\'den geçen ısıya eşittir.')
d.h2('2.2 Malzemelerin Isıl İletkenliği', need=8)
d.p('Metaller, serbest elektronları ısıyı da taşıdığı için çok iyi iletir; gazlar ise moleküller seyrek olduğu için çok kötü iletir. '
    'Yalıtım malzemelerinin çoğu, içinde hareketsiz hava hapseden gözenekli katılardır.')
d.table([['Malzeme', 'k (W/m·K), oda sıcaklığında'],
         ['Bakır', '≈ 400'], ['Alüminyum', '≈ 237'], ['Karbon çeliği', '≈ 50'], ['Tuğla', '≈ 0,7'],
         ['Su', '≈ 0,6'], ['Cam yünü', '≈ 0,04'], ['Hava', '≈ 0,026']], widths=[0.5, 0.5], title='Tablo 2.1 – Bazı malzemelerin ısıl iletkenliği (yaklaşık)')
d.box('ipucu', 'Kışın aynı sıcaklıktaki metal bir korkuluk tahta bir banktan çok daha soğuk hissettirir. Elinden ısıyı çok daha <b>hızlı çektiği</b> için böyledir: '
      'hissettiğin şey sıcaklık değil, ısı akısıdır.')
d.box('ozet', ['• Isı, sıcaklığın azaldığı yönde akar; akı sıcaklık gradyanıyla orantılıdır (Fourier yasası).',
               '• Orantı katsayısı ısıl iletkenliktir: metallerde yüksek, gazlarda ve yalıtkanlarda düşük.',
               '• Eksi işareti yönü gösterir; büyüklük hesabında sıcaklık farkının mutlak değeri kullanılır.'],
      title='BÖLÜM 2 ÖZETİ')

# =====================================================================
d.h1('3. Düzlem Duvar ve Isıl Direnç')
d.p('Fourier yasası bir noktadaki akıyı verir. Pratikte ise bütün bir duvardan geçen toplam ısı istenir; bunun için yasa duvarın kalınlığı boyunca uygulanır.')
d.h2('3.1 Tek Katmanlı Duvar')
d.p('Kararlı halde (sıcaklıklar zamanla değişmiyorsa) duvar boyunca sıcaklık doğrusal değişir ve (2.1) duvarın kalınlığı ' + M('L') + ' boyunca uygulanınca:')
d.eq('Q = k A (T<sub>1</sub> − T<sub>2</sub>) / L', '(3.1)')
d.p('Burada ' + M('Q') + ' duvardan geçen ısı (W), ' + M('A') + ' duvar alanı, ' + M('T<sub>1</sub>') + ' ve ' + M('T<sub>2</sub>') + ' iki yüzün sıcaklıklarıdır.')
d.h3('Isıl Direnç')
d.p('(3.1), elektrikteki Ohm yasasına çok benzer: sıcaklık farkı gerilime, ısı akımına karşılık gelir. Bu benzetmeyle duvarın <b>ısıl direnci</b> (thermal resistance) tanımlanır:')
d.eq('R = L / (k A),&nbsp;&nbsp;&nbsp;&nbsp; Q = (T<sub>1</sub> − T<sub>2</sub>) / R', '(3.2)')
d.fig('3.1', 'İki katmanlı duvar ve eşdeğer ısıl devresi: katmanlar seri dirençler gibi davranır; toplam sıcaklık düşüşü, katmanlar arasında dirençleriyle orantılı paylaşılır.',
      terms='Layer = katman; Interface = ara yüz; Thermal circuit = ısıl devre.', maxh=220)
d.p('Katmanlı bir duvarda (Şekil 3.1) aynı ısı bütün katmanlardan sırayla geçer; dirençler <b>seri</b> bağlıdır ve toplanır: ' + M('R<sub>top</sub> = R<sub>1</sub> + R<sub>2</sub> + …') + '.')
d.box('ornek', [
    '<b>Verilen:</b> 10 m² alanlı, 20 cm kalınlığında tuğla duvar (k = 0,7 W/m·K); iç yüz 20 °C, dış yüz 0 °C. <b>İstenen:</b> (a) duvardan geçen ısı, '
    '(b) duvara 5 cm cam yünü (k = 0,04 W/m·K) eklenirse yeni ısı kaybı.',
    '<b>(a) Tek katman:</b>',
    d.beq('Q = k A ΔT / L = 0,7 × 10 × 20 / 0,2 = 700 W'),
    '<b>(b) İki katman:</b> dirençler toplanır:',
    d.beq('R<sub>1</sub> = 0,2/(0,7 × 10) = 0,0286 K/W,&nbsp;&nbsp;&nbsp; R<sub>2</sub> = 0,05/(0,04 × 10) = 0,125 K/W'),
    d.beq('Q = 20 / (0,0286 + 0,125) ≈ 130 W'),
    'Yorum: İnce bir yalıtım katmanı, direnci tuğlanınkinin dört katından fazla olduğu için ısı kaybını yaklaşık <b>%81</b> azaltır.'],
    title='ÇÖZÜMLÜ ÖRNEK 3.1 – Yalıtımın ısı kaybına etkisi')
d.box('ozet', ['• Kararlı halde düzlem duvarda sıcaklık doğrusal değişir; Q = k A ΔT / L.',
               '• Isıl direnç R = L/(kA); seri katmanlarda dirençler toplanır.',
               '• Düşük k\'lı ince bir katman toplam direnci büyük ölçüde artırır: yalıtımın ilkesi budur.'],
      title='BÖLÜM 3 ÖZETİ')

# =====================================================================
d.h1('Genel Tekrar ve Kendini Sına')
d.box('ozet', ['<b>Fourier yasası:</b> q = −k dT/dx; ısı sıcaklığın azaldığı yönde akar.',
               '<b>Isıl iletkenlik:</b> metaller yüksek, gazlar ve gözenekli yalıtkanlar düşük.',
               '<b>Düzlem duvar:</b> Q = kAΔT/L; R = L/(kA); seri katmanlarda R toplanır.'],
      title='TÜM NOTUN ÖZETİ')
d.begin_keep()
d.h3('Kendini Sına (cevaplar notun içinde)')
d.bl(['Fourier yasasındaki eksi işareti neyi gösterir?',
      'Metaller neden gazlardan çok daha iyi ısı iletir?',
      'Isıl direnç ile elektrik direnci arasındaki benzerliği açıklayın.',
      'Duvarın kalınlığı iki katına çıkarsa ısı kaybı nasıl değişir?',
      '30 cm kalınlığında, 8 m² alanlı beton duvardan (k = 1,4 W/m·K) iç–dış farkı 15 °C iken geçen ısıyı bulun.'], num=True)
d.end_keep()

d.make()
print('ok')
