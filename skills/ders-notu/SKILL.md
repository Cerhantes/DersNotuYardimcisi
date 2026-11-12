---
name: ders-notu
description: Use when the user asks to turn a textbook PDF (any course, any book) into Turkish lecture notes ("ders notu çıkar", "not çıkar", "konu anlatımı PDF"), especially when the notes must teach from scratch, reuse the textbook's own figures, and come out as a PDF with clean page layout. Starts by asking only for the book's file path.
---

# Ders Notu (Kitaptan Türkçe PDF Ders Notu)

Bir ders kitabı PDF'inin verilen sayfa aralığından, konuyu **sıfırdan öğreten**, **kitabın kendi şekillerini** kullanan ve **sayfa düzeni temiz** bir Türkçe PDF ders notu üretir. Altyapı `scripts/` içindedir; her seferinde sadece içerik betiği yazılır.

## Kullanıcının standart beklentileri

- Not, konuyu hiç bilmeyen birinin baştan sona okuyarak öğrenebileceği şekilde: önce temel fizik/kavram, sonra yöntemler; terimlerin İngilizcesi parantez içinde.
- Şekiller **kitaptan kesilir**, numaraları kitaptakiyle aynıdır; her şeklin altında Türkçe açıklama + "Şekildeki terimler: English = Türkçe" satırı.
- Şekil, kendisini anlatan paragrafla aynı sayfada; başlık sayfa sonunda yalnız kalmaz; konu bütünlüğü korunur.
- Kapak + **tek sayfalık** içindekiler + bölüm özetleri + sonda "Genel Tekrar / Kendini Sına" soruları.
- Birden fazla konu istenirse her biri **ayrı PDF**. Çıktılar kitabın bulunduğu klasöre kaydedilir (`<kitabın klasörü>\<Konu>_Ders_Notu.pdf`).
- Kullanıcı sayfa numarası verirse bunlar **PDF görüntüleyici numarasıdır** (kitabın basılı numarası değil).
- Skill hiçbir kitaba bağlı değildir: kitap adı, yazar, ders adı, bölüm sınırları ve yazı tipleri her seferinde kitabın kendisinden çıkarılır.

## Ortam (Windows / Mac / Linux)

Kullanıcının elle bir şey kurması gerekmez; Python, paketler ve yazı tipleri aşağıdaki adımla hazır olur.

- `SK` = bu skill yüklenirken en üstte yazan **Base directory** yolu (skill `~/.claude/skills` altında da, plugin önbelleğinde de olabilir; yolu varsayma).
- **İşe başlarken bir kez** Python ortamını hazırla:
  - Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File "$SK/../../ortak/kur.ps1"`
  - Mac/Linux: `bash "$SK/../../ortak/kur.sh"`
- Ortam hazırsa bu adım 1–2 sn sürer. İlk seferde Python ve paketleri indirir (1–3 dk, yönetici hakkı istemez, sistem Python'una dokunmaz); bu sürenin başında kullanıcıya haber ver.
- Çıktının son satırı `PY=<yol>`. Aşağıdaki komutlardaki `$PY` bu yoldur; sistemdeki `py`/`python` kullanılmaz. Betik `KURULUM BAŞARISIZ` derse mesajı kullanıcıya ilet.
- Her komutta `PYTHONIOENCODING=utf-8` ve `$PY -W ignore`. Komutlar Bash sözdizimindedir; yalnız PowerShell varsa `$env:PYTHONPATH="..."; & $PY ...` biçimine çevir.
- Yazı tipleri repoda gömülüdür (metin Carlito, matematik DejaVu Serif), kurulmaz.

## Renk

Ana renk **konudan konuya değişir**; PDF'ler tek bir koyu temaya dönmez. Otomatik çalışır, içerik betiğinde renk yazmak gerekmez.

- Renkler yalnız `ortak/tema.py`'deki paletten gelir: `petrol kiremit yesil hardal mavi kirmizi turkuaz zeytin`. Mor ve lacivert palette yoktur, hex renk yazma.
- Zeminler açık, başlıklar ana renkte metindir; koyu dolgulu bant kullanma.
- Her `h1` sıradaki rengi alır. Konuya uyan rengi seçmek için `d.h1('...', renk='yesil')`; tüm notu tek renk yapmak için `Doc(..., renk='petrol')`. `ozet` kutusu ve tablolar o anki konunun rengindedir.


## Konum bağımsızlığı

Skill, Claude Code hangi klasörde açılmış olursa olsun aynı çalışır; çalışma klasörüne (cwd) hiçbir şey yazmaz ve ondan hiçbir şey beklemez.

- Bütün yollar **mutlak** verilir: kitap (`B`), skill (`SK`), çalışma klasörü (`<work>`). Göreli yol ya da `cd` kullanma.
- `<work>` = oturumun scratchpad klasörü varsa `<scratch>/w`, yoksa `$TEMP/ders-notu/<konu>` (`mkdir -p`).
- Son PDF **kitabın bulunduğu klasöre** (`dirname $B`) yazılır. Kullanıcı başka bir yer söylerse oraya yazılır. Kitabın klasörü yazılamıyorsa kullanıcıya sor.
- Ders belgesi (DUB/izlence) kitabın klasöründe ve üst klasöründe aranır, cwd'de değil.
- Kitap cwd'nin dışındaysa dosya erişimi için izin istenebilir. Bu normal, yolu değiştirmeye gerek yok.

`B=<kitap.pdf, mutlak yol>` olarak:

## Token tasarrufu: envanter ve sayfa farkı

- **İşe başlarken, sırayla, kaynak metnini okumadan önce:**
  1. `$PY -W ignore $SK/../../ortak/envanter.py $B` → içindekiler ve önceki içerik betikleri; kapsamı belirle. Çözümlü örnekler kapsamdadır; özet, kaynakça ve kapsam dışı bölümler aralığa girmez.
  2. İçindekilerde bölüm sonu problemleri varsa `AskUserQuestion` ile sor: dahil edilsin mi (önerilen: hayır)? Evetse sayfalarını içindekilerden aralıklara ekle. Çözümlü kitapçık istenirse `soru-kitapcigi` skill'i kullanılır.
  3. `envanter.py $B 368-449 478-529 --work <work>` → bu işin metni `<work>/metin.txt`'ye yazılır; numara dizini ve şekiller `<dirname $B>/.kaynak/envanter/<kaynak adı>/` altında kalır.
- **Kaynak bir kez okunur:** kapsamı tutan önceki içerik betiği varsa `metin.txt`'yi baştan okuma, betiği oku. Betikte olmayan aralığın yalnız sayfalarını (`===== PDF sayfa N`) oku. Önceki betik yoksa `metin.txt`'yi oku. Önceki betikten çalışacaksan başlarken tek cümleyle hatırlat: o belgedeki hata ve eksikler bu belgeye de geçebilir, incelenmediyse önce incelenmesi önerilir. Kullanıcı yine de devam derse bekleme; raporda hangi betikten çalışıldığını yaz.
- **Formülleri kaynakla karşılaştır** (önceki betikten alınanlar dahil; hatalar belgeden belgeye geçer): `$PY -W ignore $SK/../../ortak/envanter.py $B --serit <work> [--aralik 6.1 6.40 | --no 6.1,6.2]` → numaralı denklemlerin kırpıntıları. Kaynak ders notuysa ve kitap aynı klasördeyse kitapla karşılaştır. Kesik görünen grup denklemlerde sayfaya bak.
- **Her derlemeden sonra:** `$PY -W ignore $SK/../../ortak/sayfa_fark.py <work>/out.pdf <work>` → yalnız `AÇILACAK` satırındaki `rv<n>.png` görsellerini aç, `TAŞMA` ve `BÖLÜNMÜŞ HÜCRE?` satırlarını gider. Görülmüş sayfayı yeniden açma; düzen akışı değiştiyse sayfa dengesi için `rv_ov.png` yeterli. Görüntü aracının sonucu boş ya da `media removed` dönerse o görsel görülmemiş sayılır: yeniden aç; görmediğin sayfa için "temiz" deme.

## Akış

0. **Başlangıç: sadece kaynak yolunu iste.** Kullanıcı kitabın yolunu vermediyse tek soru sor: kitabın PDF yolu. Ders adı, konu, sayfa aralığı sorma; bunlar kitaptan çıkar. (Yol tırnaklı, `~`, `Masaüstü` gibi verilebilir; `Masaüstü` = `~/Desktop`. Dosya bulunamazsa `ls` ile yakın adları göster.)
1. **Kitabı tanı**
   `$PY -W ignore $SK/scripts/book_info.py $B` → künye (başlık, yazar), PDF ↔ basılı sayfa farkı, bölümler ve PDF sayfa aralıkları, şekil başlığı/etiket yazı tipleri.
   - Kullanıcı konuyu bir ders belgesine atıfla verirse (ör. "DUB'de ilk vizeye kadar", "izlencedeki 3. hafta") kitabın klasöründe ve üst klasöründe o belgeyi ara (`*DUB*`, `*izlence*`, `*syllabus*`; .docx ise `word/document.xml`'den metni çıkar), haftalık konu listesini kitabın alt bölümleriyle eşle ve raporda bu eşlemeyi söyle.
   - Kullanıcı mesajında konu/sayfa aralığı zaten varsa doğrudan onu kullan. Yoksa bölüm listesini (ad + PDF aralığı) kısa bir tablo olarak göster ve hangi bölüm(ler)in istendiğini sor (`AskUserQuestion`, çok seçimli; uzun listede en olası 3–4 bölüm + "Other"). Alt bölüm gerekirse `--toc-depth 2/3`.
   - Yer imi yoksa kitabın kendi "Contents" sayfasını `extract_text.py` ile oku, basılı numaralara ofseti ekle.
   - Yazı tipi çıktısından `detect_figs.py` bayraklarını belirle: başlık satırları kalın bir yazı tipiyle başlıyorsa varsayılan `--cap-font` yeter, değilse o yazı tipini ver. Şekil etiketleri gövde metninden **farklı** bir yazı tipindeyse (ör. Helvetica'ya karşı Sabon) `--label-font <o yazı tipi>` ver (daha temiz); aynıysa varsayılan `auto` kalsın. Başlık "Şekil 3-2", "Fig 4.1" gibi farklı biçimdeyse `--cap` regex'ini uyarla.
   - Künyeden Doc'un `source` satırını ve kapaktaki kaynak paragrafını kur; ders/kapak adı konunun Türkçesi olur.
2. **Metni çıkar ve ofseti doğrula**
   `$PY -W ignore $SK/scripts/extract_text.py $B <ilk> <son> <work>/metin.txt`
   Basılı sayfa numaralarıyla book_info'daki farkı doğrula. Aralık bir bölümün ortasında başlıyor ya da bitiyorsa raporda hangi alt bölümleri kapsadığını söyle.
3. **Metnin tamamını oku** (`Read` ile, parça parça; envanterin `metin.txt`'si varsa yeniden çıkarma, önceki içerik betiği varsa bkz. Token tasarrufu). İçeriği yazmadan önce tüm aralığı oku; şekil numaralarını ve denklemleri listele.
4. **Şekilleri tespit et** (envanter şekilleri hazır diyorsa `envanter.py $B --sekil-al <work>` ile al, 5. adıma kadar atla)
   `$PY -W ignore $SK/scripts/detect_figs.py $B <work> <ilk> <son> [1. adımdaki bayraklar]`
5. **Kes ve gözle kontrol et**
   `$PY -W ignore $SK/scripts/crop_figs.py $B <work> [--cap-above]` → `<work>/sheet_*.png` temas sayfalarının **hepsini** `Read` ile aç. Kümeler her başlığa otomatik atanır (en yakın küme + aynı satır/sütundaki alt şekiller); kitapta başlık şeklin üstündeyse `--cap-above` ver. `UYARI` satırları kontrol edilecek sayfaları gösterir. Tipik hatalar ve düzeltmeleri:
   - Küme yanlış şekle gitmiş / alt şekil eksik → `split.json`: `{"225": {"5.6": [0], "5.7": [1, 2]}}` (küme sırası det.json'daki sıradır).
   - Kesime gövde metni ya da denklem girmiş, veya şeklin bir parçası dışarıda kalmış → `over.json`: `{"5.18": [255, [x0, y0, x1, y1]]}`. Koordinatları det.json kümelerinden ve `page.get_text('dict')` satır kutularından türet. Şekil başlığı elle silinmez: `crop_figs.py` başlık alanını (`det.json` → `capboxes`) over.json kesimlerinde de siler ve boş kenarı kırpar; başlık hâlâ görünüyorsa `--cap` ve `--cap-font` bayraklarına bak.
   - Hatalar çoksa (ör. etiketler kesik ya da her şekle metin giriyor) önce 1. adımdaki bayrakları gözden geçir (`--label-font`, `--label-len`, `--pad`).
   Düzeltip `crop_figs.py`'yi yeniden çalıştır; temas sayfaları temiz olana kadar tekrarla. Temizse **Kırpık şekil:** `$PY -W ignore $SK/../../ortak/sekil_kenar.py <work>/fig` → her `KENAR` satırının şeklini kaynağıyla karşılaştır; kesik yazı/çizgi varsa kesimi genişlet, komşu yazıdan kalan izi beyazlat. Küçük ölçekli temas sayfasında bu kesikler kolay kaçar. Sonra `envanter.py $B --sekil-kaydet <work>`.
6. **İçerik betiğini yaz** (`<work>/<konu>.py`). Önce `$SK/USLUP.md`'yi (üslup rehberi) ve `$SK/examples/ornek_ders_notu.py`'yi baştan sona oku, aynı kalıbı izle. Örnek kitaptan bağımsız genel bir konudur; içerik, künye ve numaralar 1. adımdan ve kitaptan gelir. API aşağıda.
7. **Derle**: `PYTHONPATH=$SK/scripts $PY -W ignore <work>/<konu>.py <work>/out.pdf <work>`
   - **Denklem kapsamı**: `$PY -W ignore $SK/../../ortak/denklem_kapsam.py $B <work>/out.pdf --from <ilk> --to <son>` (kaynak sayfa aralığı). **Ölçü, o işteki ana kaynaktır.** Kullanıcı hoca notlarını ana kaynak dediyse kitap değil onlar karşılaştırılır; `$B` ana kaynaktır, birden çok dosyaysa her biri için çalıştırılır. Ana kaynaktaki her denklem, numaralı numarasız, türetimin ve çözümlü örneklerin ara adımları dahil yazılı olur: `y ve z için benzer şekilde` demek, ara adımı atlamak ya da numarayı metinde anmak yetmez. `YOK` ve `YALNIZ ANILMIŞ` listesi boşalmadan belge teslim edilmez. Yalnız kullanıcının kapsam dışı bıraktığı alt bölümler `--disarida <dosya>` ile, gerekçesiyle dışarıda kalır ve raporda yazılır; önemsiz görmek gerekçe değildir. Çıkış kodu 2 ise ya da kaynağın denklemleri numarasızsa (slayt, görsel denklem) araç güvence vermez: ana kaynağın her sayfası görüntü olarak açılır, her denklem betikle tek tek karşılaştırılır; bu karşılaştırma yapılmadan belge teslim edilmez.
   - **Metinde kalan denklem:** Numaralı denklem yalnız metin içinde anılmaz (`… = … (3.27).` yetmez): kendi satırında numarasıyla gösterilir. Denetim: `$PY -W ignore $SK/../../ortak/denklem_kapsam.py - <work>/out.pdf` → `BELGEDE YALNIZ ANILMIŞ` listesi; denklemi tabloda/kutuda formülüyle yazılı olanlar ve gösterilmiş gruba atıflar hariç boşalmalı. Ana kaynak slaytsa (çıkış kodu 2) bu kip kaynak karşılaştırmasının yerini tutmaz, yanına eklenir.
   - **Şekil atıf denetimi:** `$PY -W ignore $SK/../../ortak/sekil_atif.py <work>/out.pdf` → `ANILAN AMA YOK` listesi boşalmadan belge teslim edilmez: metinde "Şekil n" diye anılan her şekil belgede açıklamasıyla bulunur. Ya şekli ekle ya da atfı kaldır/yeniden yaz. Kaynağın şekli bilerek konmadıysa (kapsam dışı) `--haric <dosya>` ile, her satıra `<no>  gerekçe` yazarak dışarıda bırak ve raporda söyle. `VAR AMA ANILMAMIŞ` bilgi içindir: şekle metinde numarayla atıf eklenmesi önerilir. `3-13a` gibi alt şekil atıfları `3-13` şekline sayılır.
   - **Belgeden bir şey çıkarınca ona atıf yapan yerleri de güncelle:** düzeltme/hata kutusu, kapak (kaynak listesi, sayfa sayısı), içindekiler, çapraz atıflar. Çıkan içeriğe ait madde ya silinir ya da yeni yerini söyler.
   - **Sayfa bölünmesi**: çok satırlı denklem, türetim adımları ve `:` ile biten giriş cümlesi kütüphanece denklemle aynı sayfada tutulur. Aynı konunun formül ve şekli bir bütünse `g = d.grup_bas(); ...; d.grup_son(g)` ile sar. Ayrı konuların (silindirik, küresel) her biri kendi başlığıyla başlar; bir konu başlıksız sayfa sonuna düşmez. Gözle kontrolde bir denklem grubunun iki sayfaya bölündüğü her yeri düzelt.
   - **Şekle numarayla atıf yap** ("Şekil 6.6'da …"); "aşağıdaki şekil", "yukarıdaki şekilde" deme. Sığmayan şeklin ardındaki metin kütüphanece öne akar (konu başlığını geçmez), şekil sonraki sayfaya geçebilir; yer bildiren atıf o zaman yanlış olur. Bir paragraf şekli adım adım okutuyorsa ("1 noktasından 2'ye …") ikisini `fig(..., keep=lambda f: [d_paragrafi] + f)` ya da `begin_keep/end_keep` ile kenetle.
   - **Şekil açıklaması** yana sığıyorsa (yanda ≥ 5,5 cm sütun ve açıklama şeklin boyunu aşmıyor) kütüphanece şeklin sağına yazılır, değilse altta kalır; derleme sonunda `BİLGİ: n şeklin açıklaması yanda` basılır. Elle ayar gerekmez.
8. **Sayfa düzenini gözle kontrol et**: `$PY $SK/scripts/sheets.py <work>/out.pdf <work>/rv` → ilk derlemede `rv_*.png` sayfalarının hepsini aç, sonraki derlemelerde yalnız `sayfa_fark.py`'nin `AÇILACAK` listesini (bkz. Token tasarrufu). Şüpheli sayfayı tek başına yüksek çözünürlükte render edip bak. Kontrol listesi: içindekiler tek sayfa mı, şekil kendi paragrafıyla aynı sayfada mı, sayfa sonunda yalnız başlık/yarım kutu var mı, büyük boşluk var mı, denklemlerde kutucuk (eksik glif) var mı, sayfa başında önceki paragraftan kalmış 1–2 satırlık artık var mı (notlib paragrafları zaten üstte ≥2 / altta ≥3 satır kalacak şekilde böler — `MIN_HEAD`, `MIN_TAIL`; görürsen o metin `d.p` dışında bir yolla eklenmiştir).
9. **Kopyala ve raporla**: PDF'leri kitabın klasörüne (`dirname $B`, ya da kullanıcının söylediği yere) kopyala, `ls` ile doğrula. İçerik betiğini ve `figs.json`'u `<pdf klasörü>/.kaynak/<PDF adı>/` içine de kopyala; sonradan düzeltme istenirse iş baştan yapılmaz. Son mesajda yolları, sayfa sayılarını, PDF ↔ kitap sayfa eşlemesini ve kapsanan bölümleri açıkça yaz ve işin bittiğini söyle. Sonuna şu öneriyi ekle: tekrar notu ve formül kağıdı bu notun içerik betiğinden üretilecek, kaçan hata ve ayrıntılar onlara da geçebilir; bu yüzden önce notu inceleyip düzeltmeleri bildirmesi, sonra sıradaki belgeyi istemesi önerilir.

## notlib API (`from notlib import *`)

```python
d = Doc(out, 'KONU BAŞLIĞI', 'Alt başlık — Ders Notu', 'Konu – Ders Notu', work,
        'Kaynak: <Yazar(lar)>, <Kitap adı>')          # künye book_info.py çıktısından
M = lambda s: '<font name="Math">%s</font>' % s      # satır içi matematik
d.cover([kapsam_satirlari...], [nasil_kullanilir_paragraflari...])   # kapak + içindekiler
d.h1('2. Fourier Yasası')             # altında need=9 cm yer yoksa yeni sayfa açar; newpage=True zorlar
d.h2('2.1 Isı Akısı', need=6)         # need: başlığın altında en az bu kadar cm yer yoksa sayfa atla
d.h3('Isıl Direnç'); d.p('paragraf', 'paragraf2'); d.bl(['madde', ...], num=False)
d.box('tanim' | 'onemli' | 'ornek' | 'ozet' | 'ipucu' | 'terim', 'metin' veya [liste], title=None)
d.eq('q = − k dT/dx', '(2.1)')        # numaralı denklem; kutu içinde d.beq(...)
d.fig('2.1', 'Türkçe açıklama', terms='Heat flux = ısı akısı; ...', scale=0.85, maxh=300)
d.table([[başlık...], [satır...]], widths=[0.2, 0.8], title='Tablo 2.1 – ...')
d.begin_keep(); ...; d.end_keep()       # aradakileri aynı sayfada tut (ör. soru listesi)
d.make()                                # multiBuild: içindekiler sayfa numaraları için 2 geçiş
```

Metin reportlab paragraf işaretlemesi kullanır: `<b>`, `<i>`, `<sub>`, `<super>`, `<br/>`, `<font color=...>`. `&`, `<` için `&amp;`, `&lt;`.

## Sık hatalar

| Belirti | Neden / Çözüm |
|---|---|
| `ModuleNotFoundError` / `python` bulunamadı | Sistem Python'u kullanılmış; Ortam bölümündeki kurulum betiğinin verdiği `$PY` ile çalıştır |
| `UnicodeEncodeError` konsola yazarken | `PYTHONIOENCODING=utf-8` |
| Yanlış sayfalar okundu | Kullanıcı numarası PDF numarasıdır; betikler 1 tabanlı alır, indeks = no − 1. Bölüm aralıkları book_info.py'den (zaten PDF numarası) |
| Hiç şekil bulunmadı | Başlık biçimi farklı (`--cap`) ya da başlık kalın değil (`--cap-font`); book_info.py'nin yazı tipi çıktısına bak |
| Şekil etiketleri kesimin dışında | Etiket yazı tipi `--label-font`'a uymuyor; `auto` kullan ya da doğru yazı tipini ver, uzun etiketler için `--label-len` artır |
| Şekil yanlış numarayla kesildi | Metin içi "Fig. 5.7" atfı başlık sanıldı; `--cap-font` kalın yazı tipini eşlemeli |
| `BİLGİ: n denklem tek satıra sığsın diye küçültüldü` / `… anlamlı yerinden bölündü` | Normal, bir şey yapma. Sığmayan denklem önce %3 adımlarla en çok %75'e küçülür (`EQ_MIN_ORAN`); yine sığmazsa önce bileşik ayraçlardan (`⇒`, virgül, noktalı virgül), olmazsa parantez dışındaki `=`, `+`, `−`'den bölünür. Kısa parça bütünün en az dörtte biridir (tek terim alt satıra düşmez), satırlar aynı boyutta (en az %90) yazılır, numara son satırdadır. Bölmeyi elle yapmak gerekmez |
| `UYARI denklem … bölünmeye çalışıldığı hâlde sığmadı` / `ELLE DÜZENLENECEK DENKLEMLER` | Uzun kısım tek bir parantezin içinde: uzun parçaya ad ver (ör. paydayı `Δ(s) = …` diye ayrı satırda tanımla, denklemde `…/Δ(s)` yaz) ya da `d.eq` satırlarına kendin böl (ikincinin numarası `''`) |
| Denklemde/metinde boş kutu | Carlito'da olmayan glif (∛ ∝ ≃ vb.). `notlib.Paragraph` bunları otomatik olarak matematik ya da yedek yazı tipine çevirir; hiçbirinde yoksa `UYARI` basar, simgeyi değiştir |
| İçindekiler iki sayfaya taştı | İçerik betiğinde `ss['toc1']`/`ss['toc2']` fontSize/leading'i küçült (ör. 9.6/11 ve 8.4/9.4; satır dolgusu notlib'de zaten 1 pt) veya küçük alt başlıkları `h2` yerine `h3` yap (h3 içindekilere girmez). İki bölümlük uzun notlarda ~55 girdi sınırdır |
| İçindekilerde sayfa numaraları yanlış/boş | `d.make()` (multiBuild) kullan, `build` değil; içerik betiğinde `build` adlı değişken/fonksiyon tanımlama |
| Başlık sayfa sonunda yalnız, şekli/tablosu sonraki sayfada | Artık otomatik (`fig`/`table`/`end_keep` önceki başlıkları kendi bloğuna alır); hâlâ oluyorsa araya başka öğe girmiştir → `h1(..., need=...)` / `h2(..., need=...)` büyüt |
| Uzun tablo yüzünden sayfa altında büyük boşluk | Artık otomatik: sayfanın 1/3'ünden uzun tablolar satır arasından bölünür, başlık satırı tekrar eder |
| Şekil sığmadı, sayfa altı boş kaldı | Artık otomatik: açıklaması alttaki şekilde önce açıklama yana alınır; olmazsa şekil %80'e kadar küçülür (gerekirse yan açıklamayla); o da olmazsa ardındaki paragraf, denklem, kutu ve çözümlü örnek boşluğa akar, şekil sonraki sayfanın başına geçer. Başlıklı şekilde ve şekilden hemen sonra başlık geliyorsa metin akmaz (konu dışına taşmasın): orada `maxh` küçült. Derleme sonunda `BİLGİ: sayfaya sığmayan şekiller: …` hangi yolun kullanıldığını sayar |
| Bir paragraf çevresinden biraz küçük yazılmış | `notlib`, genişliğe sığmayan bölünmez satır kalırsa yalnız o paragrafı en çok 1,5 pt küçültür ve `BİLGİ: n paragraf ... küçültüldü` basar; çoksa paragraftaki uzun bölünmez parçayı (uzun formül, birimli sayı zinciri) böl |
| Şekil sayfa sonunda metninden koptu | `fig(..., keep=...)` ya da `begin_keep/end_keep` ile paragrafla birlikte tut; `maxh` küçült |
| Kesimde gövde metni / denklem görünüyor | `over.json` ile elle kesim ver (otomatik tespit her kitapta birkaç şekilde bunu yapar; temas sayfalarını atlama). Şekil başlıkları otomatik silinir |
