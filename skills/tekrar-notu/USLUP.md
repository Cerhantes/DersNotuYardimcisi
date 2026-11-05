# Tekrar notu üslup rehberi

İçerik betiğini yazmadan önce bu dosyayı ve `examples/ornek_tekrar_notu.py`'yi baştan sona oku. Örnek kitaptan bağımsız genel bir
konuyu (ısı iletimi) kısaca işler. Örnekten içeriği değil **kalıbı** al. İçerik her zaman kullanıcının kaynağından gelir ve
kaynaktaki **her** bilgi notta yer alır (SKILL.md'deki "Tekrar notunun biçimi").

## Ses

- Okur konuyu çalışmış, hatırlamak istiyor. **Anlatma, hatırlat.** Paragraf yok; `P()` yalnız tek cümlelik bağlam ya da bir listenin başlığı için.
- Madde dili kısa ve isim ağırlıklı: `'Metallerde <b>yüksek</b>: serbest elektronlar ısıyı da taşır.'` Gereksiz fiil, bağlaç ve "dır/dir" atılabilir.
- Neden-sonuç zinciri okla: `kalınlık ↑ → R ↑ → Q ↓`. Eğilim `↑` / `↓`, çok güçlü etki `↓↓`, etkisiz `—`.
- Örnek ve istisna parantezde: `(ör. bakır, alüminyum)`.
- **Kelimesi kelimesine çevirme:** cümleyi anlamından yeniden Türkçe kur, yazdıktan sonra Türkçe okunuşunu kontrol et. `far downstream` → "çok akış aşağısında" değil, "akış yönünde çok ileride". Yerleşik terimler (`akış aşağısı`, `sınır tabaka`) kalır.
- Terim ilk geçtiğinde **kalın**, İngilizcesi parantezde.

## Bölüm iskeleti

Her kaynak bölümü için sıra:

1. `d.h1('n. Başlık')` (kaynaktaki numara ve sırayla; ek bilgi bölümleri başlıkta `(ek bilgi)` ile işaretlenir).
2. Bölümün ana tanımı varsa `BX('tanim', ['<b>Terim (English):</b> tanım.'])`.
3. Maddeler, formüller, tablolar, şekiller: kaynağın sırasıyla.
4. Sınavda kritik ya da sık karıştırılan nokta: `X('onemli', ...)`.
5. Bölüm sonu: `BX('ozet', [...], 'BÖLÜM n HIZLI KONTROL')` → 4–7 madde, bölümün formülleri ve eğilimleri sıkıştırılmış halde.

## Kalıplar

**Sayılı liste** (kaynakta "üç yol", "beş neden"):

```python
P('<b>Isı aktarımının yolları (3):</b>')
B(['<b>İletim (conduction):</b> …', '<b>Taşınım (convection):</b> …', '<b>Işınım (radiation):</b> …'], num=True)
```

Sayı başlıkta yazılır ve listenin **tamamı** verilir. Ezber gerektiren kısa liste `onemli` kutusunda tek satırda `·` ile ayrılır:
`X('onemli', ['<b>Isı kaybı nasıl azaltılır? (4 yol — ezberle)</b>', '(a) k ↓ · (b) L ↑ · (c) A ↓ · (d) ΔT ↓'])`

**Formül + sonuçları**: `E()` ile kaynaktaki numarasıyla. Hemen ardından `B()` ile:
- formülden çıkan sonuç (`'Q ∝ 1/L → kalınlık iki katı, ısı kaybı yarı.'`),
- problemlerde gereken **ters çözülmüş biçim** kalın (`'<b>L = k A ΔT / Q</b> (kalınlık hesabında en çok kullanılan biçim)'`),
- geçerlilik koşulu (`'Yalnız kararlı halde ve sabit k için.'`).

**Karşılaştırma**: iki sütunlu `T()`; hücrede maddeler `• …<br/>• …`.

**Alt türler**: `d.h3('1) Tür adı')`, altında `B()`. Türler numaralı başlıklarla sırayla verilir.

**Şekil**: `F()` tek, `F2()` ikili. Altyazı şeklin **söylediği bilgi**: ne gösterdiği + dikkat edilecek nokta, `(a) …; (b) …` biçiminde.

**Çözümlü örnek** (`X('ornek', ...)`): `'<b>Örnek n.m (konu):</b> verilenler.'` + tek satırda yol ve sonuç (sonuçlar kalın).

**Sezgi** (`X('ipucu', ...)`): grafik okuma, akılda tutma yolu, benzetme. En fazla 2 cümle.

## Kitabın sonundaki bölümler

- **Semboller** (`d.h1('0. Semboller (hepsini tanıyabilmelisin)')`): dört sütun `['Sembol', 'Anlamı', 'Sembol', 'Anlamı']`, genişlik `[0.12, 0.38, 0.1, 0.4]`.
- **Problem çözme**: `X('onemli', ['<b>Çözüm sırası:</b> 1) … → 2) … → 3) …'])` + tablo `['Problem', 'Konu', 'Yol ve sonuç']`, genişlik `[0.13, 0.19, 0.68]`, sonuçlar kalın.
  Çok sonuç veren problemin bütün sonuçları ayrı bir `T()` ile.
- **Kaynak sorularına kısa yanıtlar**: `B(['<b>n.m</b> yanıt.', ...])`. Kısa yanıtlı iki soru tek maddede birleşebilir.
- **"Neyi Değiştirirsem Ne Olur?"**: ilk sütun `'Değişiklik'` (`'Kalınlık L ↑'`), sonra etkilenen büyüklükler, son sütun `'Diğer'`. Hücreler `↑ ↓ ↓↓ —`, kısa neden parantezde.
- **Formül Özeti**: `['Konu', 'Bağıntı']`, genişlik `[0.24, 0.76]`; aynı konudaki bağıntılar `;` ile tek hücrede.
- **Kendini Sına — Kısa Cevaplı**: `B(['<b>1.</b> Soru? Kısa cevap → hesap → <b>sonuç</b>.', ...])`. Sayısal cevaplar Python ile hesaplanıp doğrulanır.
  Kaynakta olmayan ek sorular `d.h3('Ek sorular')` altında ve raporda "benim eklediklerim" olarak belirtilir.

## Kapak

- Satırlar: `<b>Kaynak:</b>` (dosya adı, sayfa sayısı, künye, bölüm aralığı), `<b>Kapsam:</b>` (hangi bölümler; sınav kapsamı ve "ek bilgi" bölümleri belirtilir, hiçbiri atlanmaz),
  `<b>Şekiller</b>` (kaynaktan alındığı, numaraların aynı olduğu).
- "Nasıl kullanılır" iki paragraf: (1) tekrar için yazıldığı, her bilginin madde madde, formüllerin numarasıyla, eğilimlerin okla (↑ artar, ↓ azalır, → sonuç) verildiği;
  (2) kutu renklerinin anlamı ve notun sonunda neler olduğu.
