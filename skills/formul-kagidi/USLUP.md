# Formül kağıdı üslup rehberi

Biçimin ana kuralları SKILL.md'deki "Formül kağıdının biçimi" bölümündedir. Bu dosya, örneklerde görülen ayrıntıları toplar.
Betikleri yazmadan önce bu dosyayı ve `examples/ornek_semalar.py` ile `examples/ornek_kagit.py`'yi baştan sona oku.
Örnekler kaynaktan bağımsız genel bir konuyu (ısı iletimi) işler. Örnekten içeriği değil **kalıbı** al.

## Başlık bandı

- Başlık: `'KONU – FORMÜL KAĞIDI'` (büyük harf).
- Alt satır, ` · ` ile ayrılmış: ders adı · kapsam (`Bölüm 5` ya da `ilk vize: Bölüm 5.1–5.6` + parantezde konu adları) · `Denklem numaraları kaynaktakiyle aynıdır`.
- Bant ve kart başlıkları açık zemin üstüne ana renkte metindir; her kart sıradaki rengi alır (bkz. SKILL.md, Renk).

## Kart

- Başlık: `'n · Türkçe Ad (English term)'` ya da iki kavram birleşiyorsa `'n · Ana Kavram: Alt Kavram'`.
- Etiket kısa ve isim halinde: `'Isı akısı'`, `'Oran formu (n = 2)'`, `'Kararlı hal, düzlem levha'`.
- `terms(...)` açıklamaları küçük harfle başlar, birim parantezde: `('k', 'ısıl iletkenlik (W/m·K)')`.
  Aynı kartta daha önce adlandırılmış sembol tekrar adlandırılmaz.
- **Kelimesi kelimesine çevirme:** cümleyi anlamından yeniden Türkçe kur, yazdıktan sonra Türkçe okunuşunu kontrol et. `far downstream` → "çok akış aşağısında" değil, "akış yönünde çok ileride". Yerleşik terimler (`akış aşağısı`, `sınır tabaka`) kalır.
- `note=` tek satır ve şu türlerden biri: işaret/yön anlamı, geçerlilik koşulu, tipik aralık, sık yapılan hata, benzetme.
- Kartın son satırı genellikle bir **uygulama**: `'<b>Uygulama:</b> verilenler → hesap = sonuç; değişen durumda sonuç.'`
  Kaynağın çözümlü örneğinden alınır ve kartın formüllerinin nasıl zincirlendiğini gösterir.
- Sabitler tablosu (`d.tbl`) kartın formüllerinden sonra, `items` listesine eklenerek: `[...] + d.tbl(...)`. Tablo başlığı kaynaktaki numarasıyla.
- Uzun formülde `fs=11.8`. İki eşdeğer biçim tek satırda `\qquad` ile.

## Şemalar (dglib)

- Her kartın sağında bir şema. Türler: **ölçülü kesit** (boyutlar `dim` ile, semboller formüldekiyle aynı), **eğri üzerinde semboller**
  (faz/profil/akış diyagramı), **eğilim grafiği** (orantı formülü + okunan 1–2 nokta), **karşılaştırma çubukları**.
- Sembol etiketleri mathtext ve formüldekiyle **aynı yazım** (`r'$T_1$'`), 10–11 pt; açıklama yazıları Türkçe, küçük harf, 6,5–8,5 pt.
- Renk anlamı tutarlı: büyüklük çizgisi/eğri `RED` ya da `BLUE`, ölçüler `GRN`, akış/vektör `KOYU`, yardımcı çizgiler `GREY` (kesikli/noktalı).
- Etiketler hiçbir çizginin, okun ya da başka etiketin **üstünde değil**: eğrinin ucunun yanına (`ha='left'`), okun üstüne/altına, gerekirse noktalı kılavuz çizgiyle dışarı.
- Eksen sayıları gereksizse kaldır (`set_xticks([])`); eğilim grafiğinde eksen adları birimiyle (`'kalınlık L (cm)'`).
- Şema altyazısı (`cap=`): şemanın **gösterdiği sonuç**, tek cümle (`'Q ∝ 1/L: kalınlık iki katı → ısı kaybı yarı.'`).
