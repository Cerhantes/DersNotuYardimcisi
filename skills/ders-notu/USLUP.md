# Ders notu üslup rehberi

İçerik betiğini yazmadan önce bu dosyayı ve `examples/ornek_ders_notu.py`'yi baştan sona oku. Örnek, kitaptan bağımsız
genel bir konuyu (ısı iletimi) anlatır. Örnekten içeriği değil **kalıbı** al: içerik her zaman kullanıcının kitabından gelir.

## Okur ve ses

- Okur konuyu **hiç bilmiyor**. Not, onu baştan sona okuyarak öğretmeli: önce olgu/kavram, sonra mekanizma, sonra hesap, en son uygulama.
- Ses açıklayıcı ve sakin bir öğretmen sesi: "…anlamak için önce … bilmek gerekir", "…düşünelim", "Şekle bakıldığında …".
  İkinci tekil hitap ("düşünebilirsin") yalnızca ipucu kutularında, seyrek.
- Her h1 bölümü 1–2 cümlelik bir **giriş paragrafıyla** açılır: bu konu neden gerekli, öncekiyle bağı ne.
- Paragraflar 2–4 cümle. Bir paragraf tek bir fikri anlatır. Uzun açıklamayı bölüp araya şekil ya da kutu koy.

## Terimler ve sayılar

- **Kelimesi kelimesine çevirme:** cümleyi anlamından yeniden Türkçe kur, yazdıktan sonra Türkçe okunuşunu kontrol et. `far downstream` → "çok akış aşağısında" değil, "akış yönünde çok ileride". Yerleşik terimler (`akış aşağısı`, `sınır tabaka`) kalır.
- Terim ilk geçtiğinde **kalın**, İngilizcesi parantezde ve normal yazıyla: `<b>ısıl iletkenlik</b> (thermal conductivity)`.
  Sonraki geçişlerde yalnız Türkçesi.
- Kritik sonuç cümlesi kalın yazılır (paragrafın "aklında kalsın" kısmı), ama paragrafın en fazla 1–2 yeri.
- Sayılar birimleriyle ve kalın: `<b>1313 °C</b>`, `<b>%0,77 C</b>`. Ondalık ayırıcı virgül. Ekler kesmeyle: `1313 °C'de`, `Şekil 2.3'te`.
- Günlük hayattan bir benzetme (suda çözünen şeker, tahterevalli) kavramı somutlaştırıyorsa ekle: kısaysa parantezde, uzunsa ipucu kutusunda.

## Kutular (`d.box`)

| Tür | Ne zaman | Kalıp |
|---|---|---|
| `tanim` | Yeni, sınavda tanımı sorulabilecek kavram | `'<b>Terim</b> (English): tek-iki cümlelik tanım.'`; birden çok tanım varsa liste |
| `onemli` | Konunun iskeleti, sayılı faktörler, sık karıştırılan nokta | Giriş cümlesi + `1) …<br/>2) …`; `title='… N TEMEL FAKTÖRÜ'` gibi büyük harf başlık |
| `ipucu` | Sezgi, benzetme, "neden böyle?" açıklaması, karıştırılan iki kavramın farkı | 2–3 cümle; tek bir fikir |
| `ornek` | Çözümlü örnek (kitaptaki örnekler, numarasıyla) | Aşağıdaki kalıp. Yalnız sonuç listesi "örnek" diye adlandırılmaz: soru ve çözüm yoksa "tipik değerler" gibi bir cümle olur |
| `ozet` | Her h1 bölümünün sonu | `'• '` ile başlayan 4–6 madde, her biri tek cümle; `title='BÖLÜM n ÖZETİ'` |
| `terim` | Nadiren: şekil dışında bir terim listesi | `English = Türkçe; …` |

Çözümlü örnek kalıbı (kullanıcının onayladığı tam biçim): SORU, çizim, Verilen/İstenen, KABULLER, numaralı ÇÖZÜM adımları, çerçeveli SONUÇ, Yorum. Adım denklemleri metne yakın boyuttadır (10,8 pt); uzun örnek yalnız adım sınırında sayfaya bölünür.

```python
d.cozum('ÇÖZÜMLÜ ÖRNEK n.m – kısa konu adı',
        'Soru metni, kaynaktaki gibi tam.',
        d.kf('H2.11', 'Çizimin kısa açıklaması (slayt).', h=110),   # çizim yoksa None
        ('verilenler; ...', 'istenenler'),
        ['Sürekli rejim, tek boyutlu iletim.', 'k sabit.'],              # kabuller
        [('Fourier yasası, birim alan için:', ['q″ = k (T<sub>1</sub> − T<sub>2</sub>)/L', ('q″ = 1,4 × 10/0,005 = 2800 W/m²', '(1.2)')]),
         ('Isı kaybı:', ['q = q″ A = 2800 × 3 = 8400 W'])],             # (açıklama, [denklemler]) adımları
        ['<b>q = 8400 W</b>'],                                           # sonuç satırları
        yorum='Sonucun ne anlama geldiği (bir cümle).')
```

- Tek işlemlik adımlar birleştirilir; ana kaynaktaki ara denklemler atlanmaz.
- Kaynakta yazmayan kabul ve yorumlar raporda "benim eklediklerim" olarak listelenir.
- Kısa, tek hesaplık bir örnek için eski kısa kutu da kullanılabilir:

```python
d.box('ornek', [
    '<b>Verilen:</b> … <b>İstenen:</b> …',
    '<b>(a) …:</b> ilk adımın açıklaması',
    d.beq('Q = k A (T<sub>1</sub> − T<sub>2</sub>) / L = … = 700 W'),   # hesap satırı: formül = sayılar = sonuç
    '<b>(b) …:</b> …',
    'Yorum: sonucun ne anlama geldiği (bir cümle).'],
    title='ÇÖZÜMLÜ ÖRNEK n.m – kısa konu adı')
```

## Denklemler

- Denklem önce bir cümleyle tanıtılır ("… şu bağıntıyla tanımlanır:"), sonra `d.eq(..., '(n.m)')` ile kitaptaki numarasıyla yazılır.
- Hemen arkasından gelen paragraf **her sembolü** açıklar: `'Burada ' + M('q') + ' ısı akısı, ' + M('k') + ' … dır.'`
- Satır içi sembol her zaman `M('…')` ile, alt/üst simgeler `<sub>`/`<super>` ile.
- Türetilmiş ya da ters çözülmüş biçimler numarasız `d.eq(..., '')` olarak verilir.
- Numaralı denklem paragrafın içinde `M('…') + ' (3.27)'` biçiminde bırakılmaz; `d.eq('…', '(3.27)')` ile kendi satırına alınır.

## Şekiller

- Şekil önce paragrafta anılır ("(Şekil 2.1a)"), `d.fig` hemen o paragraftan sonra gelir.
- Altyazı = **ne gösterdiği + nereye dikkat edilmeli**. Kitabın altyazısının çevirisiyle yetinme; bir cümle yorum ekle ("…dikkat edin").
- Şekilde İngilizce etiket varsa **hepsi** `terms='English = Türkçe; …'` içinde.
- Boyut: tam genişlik şekil `scale=0.85`; küçük yazılı şekil `maxh=280–320`; basit şema `maxh=200–230`.

## Sayfa düzeni için yazım

Kütüphane bölünmeleri çoğunlukla kendisi yönetir; yazarken şu dördüne dikkat et (sorun çıkarsa DUZEN.md):

- Aynı konunun formülü ve şekli bir bütünse `g = d.grup_bas(); ...; d.grup_son(g)` ile sar.
- Ayrı konuların (silindirik, küresel) her biri kendi başlığıyla başlar; bir konu başlıksız sayfa sonuna düşmez.
- Bir paragraf şekli adım adım okutuyorsa ("1 noktasından 2'ye …") ikisini `fig(..., keep=lambda f: [d_paragrafi] + f)`
  ya da `begin_keep/end_keep` ile kenetle.
- Renk yazma (otomatik; hex renk ve koyu dolgulu bant kullanılmaz). Elle seçim gerekirse DUZEN.md › Renk.

## Listeler

- Madde kalıbı `'<b>Başlık:</b> açıklama cümlesi.'` Maddeler paralel yapıda olsun: hepsi aynı türden şeyleri saysın.
- Kitapta "üç tür", "dört faktör" gibi sayılı bir liste varsa sayı metinde söylenir ve **hepsi** verilir. Sıra önemliyse `num=True`.

## Bölüm sonu ve not sonu

- Her h1 bölümü `ozet` kutusuyla kapanır.
- Not sonu: `d.h1('Genel Tekrar ve Kendini Sına')` → bütün notun özeti (`ozet`, `title='TÜM NOTUN ÖZETİ'`, her madde `'<b>Konu:</b> özet'`)
  → `d.begin_keep()` + `d.h3('Kendini Sına (cevaplar notun içinde)')` + numaralı sorular + `d.end_keep()`.
- Kendini Sına soruları kavram ("… neden …?"), karşılaştırma ("… ile … farkı nedir?") ve sayısal ("… bulun.") soruların karışımı. Cevapları notta olmalı.

## Kapak

- Kapsam satırları: `<b>Kapsam:</b>` (PDF sayfa aralığı + bölüm numaraları), `<b>Kaynak:</b>` (tam künye: yazarlar, kitap adı italik, baskı, yayınevi, yıl, bölüm),
  `<b>Şekiller:</b>` (kitaptan alındığı, numaraların aynı olduğu).
- "Nasıl kullanmalısın" kutusu iki paragraf: (1) notun kurgusu, konuların sırası; (2) kutu renklerinin anlamı + şekil terimlerinin altta verildiği.
