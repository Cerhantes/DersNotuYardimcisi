# Sayfa düzeni ve dizgi: sorun giderme

Bu dosyayı **şu durumlarda** oku: derleme `UYARI` ya da `ELLE DÜZENLENECEK DENKLEMLER` bastı; `denetle.py` `TAŞMA` ya da
`BÖLÜNMÜŞ HÜCRE?` dedi; sayfa görsellerinde aşağıdaki tablodaki belirtilerden birini gördün; ya da renk seçmek istiyorsun.
Yazarken uyulacak düzen kuralları USLUP.md'nin "Sayfa düzeni için yazım" bölümündedir.

## Renk

Ana renk **konudan konuya değişir**; PDF'ler tek bir koyu temaya dönmez. Otomatik çalışır, içerik betiğinde renk yazmak gerekmez.

- Renkler yalnız `ortak/tema.py`'deki paletten gelir: `petrol kiremit yesil hardal mavi kirmizi turkuaz zeytin`. Mor ve lacivert
  palette yoktur, hex renk yazma.
- Zeminler açık, başlıklar ana renkte metindir; koyu dolgulu bant kullanma.
- Her `h1` sıradaki rengi alır. Konuya uyan rengi seçmek için `d.h1('...', renk='yesil')`; tüm notu tek renk yapmak için
  `Doc(..., renk='petrol')`. `ozet` kutusu ve tablolar o anki konunun rengindedir.

## Kütüphanenin kendiliğinden yaptıkları (elle uğraşma)

- Çok satırlı denklem, türetim adımları ve `:` ile biten giriş cümlesi denklemle aynı sayfada tutulur (zincir en çok 8 satır).
- Paragraflar sayfa sonunda üstte ≥ 2, altta ≥ 3 satır kalacak şekilde bölünür (`MIN_HEAD`, `MIN_TAIL`). Sayfa başında
  önceki paragraftan 1–2 satırlık artık görürsen o metin `d.p` dışında bir yolla eklenmiştir.
- Şekil açıklaması yana sığıyorsa (yanda ≥ 5,5 cm sütun ve açıklama şeklin boyunu aşmıyor) şeklin sağına yazılır, değilse
  altta kalır; derleme sonunda `BİLGİ: n şeklin açıklaması yanda` basılır.
- Sığmayan şekilde önce açıklama yana alınır, olmazsa şekil %80'e kadar küçülür, o da olmazsa ardındaki metin boşluğa akar
  (konu başlığını geçmez) ve şekil sonraki sayfaya geçer. Bu yüzden şekle yer bildiren atıf ("aşağıdaki şekil") yanlış olur.

## Sık hatalar

| Belirti | Neden / Çözüm |
|---|---|
| `BİLGİ: n denklem tek satıra sığsın diye küçültüldü` / `… anlamlı yerinden bölündü` | Normal, bir şey yapma. Sığmayan denklem önce %3 adımlarla en çok %75'e küçülür (`EQ_MIN_ORAN`); yine sığmazsa önce bileşik ayraçlardan (`⇒`, virgül, noktalı virgül), olmazsa parantez dışındaki `=`, `+`, `−`'den bölünür. Kısa parça bütünün en az dörtte biridir (tek terim alt satıra düşmez), satırlar aynı boyutta (en az %90) yazılır, numara son satırdadır. Bölmeyi elle yapmak gerekmez |
| `UYARI denklem … bölünmeye çalışıldığı hâlde sığmadı` / `ELLE DÜZENLENECEK DENKLEMLER` | Uzun kısım tek bir parantezin içinde: uzun parçaya ad ver (ör. paydayı `Δ(s) = …` diye ayrı satırda tanımla, denklemde `…/Δ(s)` yaz) ya da `d.eq` satırlarına kendin böl (ikincinin numarası `''`) |
| Denklemde/metinde boş kutu | Carlito'da olmayan glif (∛ ∝ ≃ vb.). `notlib.Paragraph` bunları otomatik olarak matematik ya da yedek yazı tipine çevirir; hiçbirinde yoksa `UYARI` basar, simgeyi değiştir |
| İçindekiler iki sayfaya taştı | İçerik betiğinde `ss['toc1']`/`ss['toc2']` fontSize/leading'i küçült (ör. 9.6/11 ve 8.4/9.4; satır dolgusu notlib'de zaten 1 pt) veya küçük alt başlıkları `h2` yerine `h3` yap (h3 içindekilere girmez). İki bölümlük uzun notlarda ~55 girdi sınırdır |
| İçindekilerde sayfa numaraları yanlış/boş | `d.make()` (multiBuild) kullan, `build` değil; içerik betiğinde `build` adlı değişken/fonksiyon tanımlama |
| Başlık sayfa sonunda yalnız, şekli/tablosu sonraki sayfada | Artık otomatik (`fig`/`table`/`end_keep` önceki başlıkları kendi bloğuna alır); hâlâ oluyorsa araya başka öğe girmiştir → `h1(..., need=...)` / `h2(..., need=...)` büyüt |
| Uzun tablo yüzünden sayfa altında büyük boşluk | Artık otomatik: sayfanın 1/3'ünden uzun tablolar satır arasından bölünür, başlık satırı tekrar eder |
| Şekil sığmadı, sayfa altı boş kaldı | Artık otomatik (yukarıya bak). Başlıklı şekilde ve şekilden hemen sonra başlık geliyorsa metin akmaz (konu dışına taşmasın): orada `maxh` küçült. Derleme sonunda `BİLGİ: sayfaya sığmayan şekiller: …` hangi yolun kullanıldığını sayar |
| Bir paragraf çevresinden biraz küçük yazılmış | `notlib`, genişliğe sığmayan bölünmez satır kalırsa yalnız o paragrafı en çok 1,5 pt küçültür ve `BİLGİ: n paragraf ... küçültüldü` basar; çoksa paragraftaki uzun bölünmez parçayı (uzun formül, birimli sayı zinciri) böl |
| Şekil sayfa sonunda metninden koptu | `fig(..., keep=...)` ya da `begin_keep/end_keep` ile paragrafla birlikte tut; `maxh` küçült |
| Denklem grubu iki sayfaya bölünmüş | `g = d.grup_bas(); ...; d.grup_son(g)` ile sar |
| `TAŞMA: sağ kenar diğer sayfaları aşıyor` | O sayfadaki uzun bölünmez parça (formül, URL, birimli sayı zinciri) ya da geniş tablo; böl ya da tablo `widths` ver |
| `BÖLÜNMÜŞ HÜCRE?` | Tablo hücresinde kelime/sayı ortadan bölünmüş: o sütunu genişlet (`widths`) ya da hücre metnini kısalt |
| Bir sayfadan emin değilsin | Tek başına yüksek çözünürlükte render edip bak: `$PY $SK/scripts/sheets.py <work>/out.pdf <work>/rv` ya da pymupdf ile 110–120 dpi |
