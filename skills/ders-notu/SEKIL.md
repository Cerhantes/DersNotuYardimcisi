# Şekil kesimi: bayraklar, düzeltme, sorun giderme

Bu dosyayı **şu durumlarda** baştan sona oku: `hazirla.py` `UYARI` ya da `ŞEKİL BAŞLIĞI BULUNAMADI` dedi, temas sayfasında
yanlış, eksik ya da kirli bir kesim gördün, `sekil_kenar.py` `KENAR` satırı verdi veya bir şekli elle yeniden kesmen gerekiyor.
Temas sayfaları temizse ve uyarı yoksa okumana gerek yok.

## Komutlar (hazirla.py'nin içinde çalışanlar; yeniden çalıştırmak için)

- Kitabın yazı tipleri ve künyesi: `$PY -W ignore $SK/scripts/book_info.py $B [--toc-depth 2]`
- Tespit: `$PY -W ignore $SK/scripts/detect_figs.py $B <work> <ilk> <son> [bayraklar]` → `<work>/det.json`.
  Birden çok aralıkta her aralık için ayrı çalışır ve det.json'u ezer: aralıklar için `hazirla.py`'yi kullan
  (birleştirir) ya da yalnız bir aralığı yeniden tespit ediyorsan sonra `hazirla.py`'yi yeniden çalıştır.
  `hazirla.py`'nin seçtiği bayraklar `<work>/bayraklar.txt`'de durur.
- Kesim: `$PY -W ignore $SK/scripts/crop_figs.py $B <work> [--cap-above]` → `<work>/fig/*.png`, `figs.json`, `sheet_*.png`
- Kırpık şekil: `$PY -W ignore $SK/../../ortak/sekil_kenar.py <work>/fig`
- Gözden geçirilmiş şekilleri envantere kaydet: `$PY -W ignore $SK/../../ortak/envanter.py $B --sekil-kaydet <work>`
  (tek bir şekli kaydetmek için `--yalniz 5.2`; sonraki işler bunları `--sekil-al` ile alır, yeniden kesmez)

## Bayraklar

`hazirla.py` bayrakları aralığın kendi sayfalarından seçer ve gerekçesini yazar; yanlış seçtiyse aynı bayrağı elle vererek
seçimin önüne geç (`hazirla.py ... --cap-font 'Bodoni-Bold'`).

- `--cap`: başlık satırını tanıyan regex (varsayılan `FIGURE|Figure|Fig.|ŞEKİL|Şekil` + `n.m`). Başlık "Şekil 3-2",
  "Fig 4.1" gibi farklı biçimdeyse uyarla.
- `--cap-font`: başlığın ilk parçasının yazı tipi. Başlık satırları kalın bir yazı tipiyle başlıyorsa varsayılan yeter;
  değilse o yazı tipini ver. Metin içi "Fig. 5.7" atfının başlık sanılmasını bu önler.
- `--label-font`: şekil içi etiketlerin yazı tipi. Etiketler gövde metninden **farklı** bir yazı tipindeyse
  (ör. Helvetica'ya karşı Sabon) onu ver, daha temiz sonuç verir; aynıysa `auto` kalsın.
- `--label-len` (auto kipinde etiket sayılan en uzun satır, varsayılan 40), `--pad` (kümeleme mesafesi, 12 pt).
- `--cap-above`: kitapta başlık şeklin **üstünde**.

Hatalar çoksa (etiketler kesik ya da her şekle metin giriyor) tek tek düzeltmeden önce bayrakları gözden geçir.

## Temas sayfasında görülen hatalar ve düzeltmeleri

Kümeler her başlığa otomatik atanır (en yakın küme + aynı satır/sütundaki alt şekiller). `UYARI idx n: … küme` satırları
bakılacak sayfaları gösterir; çoğu zararsızdır (ikinci küme bir denklem ya da kutu), ama her birine bak.

- **Küme yanlış şekle gitmiş / alt şekil eksik** → `<work>/split.json`: `{"225": {"5.6": [0], "5.7": [1, 2]}}`
  (anahtar sayfa idx'i, değer det.json'daki küme sıraları).
- **Kesime gövde metni ya da denklem girmiş, veya şeklin bir parçası dışarıda kalmış** → `<work>/over.json`:
  `{"5.18": [255, [x0, y0, x1, y1]]}` (sayfa idx, pt). Koordinatları det.json kümelerinden ve
  `page.get_text('dict')` satır kutularından türet. Otomatik tespit her kitapta birkaç şekilde bunu yapar; temas
  sayfalarını atlama.
- **Bir sayfayı tümden elle vermek** → `<work>/skip.json`: `[471]` ve o sayfanın şekilleri over.json'da.
- **Şekil başlığı kesimde görünüyor** → elle silme: `crop_figs.py` başlık alanını (`det.json` → `capboxes`) over.json
  kesimlerinde de siler ve boş kenarı kırpar. Hâlâ görünüyorsa `--cap` ve `--cap-font` bayraklarına bak.
- **`kesimde yalnız başlık var`** → şekil vektör değil ya da küme bulunamadı: over.json ile ver.

Düzeltip `crop_figs.py`'yi yeniden çalıştır; temas sayfaları temiz olana kadar tekrarla (split.json ve over.json
korunur, `hazirla.py` yeniden çalıştırılsa da).

## Kırpık şekil (KENAR satırları)

`sekil_kenar.py` kesimin kenarına değen mürekkebi bulur. Her `KENAR` satırının şeklini kaynağıyla karşılaştır: kesik yazı ya
da çizgi varsa kesimi over.json ile genişlet; komşu yazıdan kalan iz varsa kesimi daralt ya da beyazlat. Çerçeveli şekil,
tablo çizgisi, kenara uzanan grafik eksenleri doğal olarak değer, hata değildir. Küçük ölçekli temas sayfasında bu kesikler
kolay kaçar: şüphelide `fig/<no>.png`'yi tek başına aç.

## Sık hatalar

| Belirti | Neden / Çözüm |
|---|---|
| Hiç şekil bulunmadı | Başlık biçimi farklı (`--cap`) ya da başlık kalın değil (`--cap-font`); `book_info.py`'nin yazı tipi çıktısına bak. Aralıkta gerçekten şekil yoksa normaldir |
| Şekil etiketleri kesimin dışında | Etiket yazı tipi `--label-font`'a uymuyor; `auto` kullan ya da doğru yazı tipini ver, uzun etiketler için `--label-len` artır |
| Şekil yanlış numarayla kesildi | Metin içi "Fig. 5.7" atfı başlık sanıldı; `--cap-font` kalın yazı tipini eşlemeli |
| Kesimde gövde metni / denklem görünüyor | `over.json` ile elle kesim ver. Şekil başlıkları otomatik silinir |
| `envanterin şekil dizininde olup kesilmeyen numaralar` | Kitapta bak: gerçekten şekilse split.json / over.json ile ver; satır başına düşmüş metin içi atıfsa yok say |
