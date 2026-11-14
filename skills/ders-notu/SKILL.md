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

## Ek dosyalar: ne zaman okunur

| Dosya | Ne zaman |
|---|---|
| `$SK/USLUP.md` + `$SK/examples/ornek_ders_notu.py` | **Her işte**, içerik betiğini yazmadan önce, baştan sona |
| `$SK/SEKIL.md` | `hazirla.py` `UYARI`/`ŞEKİL BAŞLIĞI BULUNAMADI` dedi, temas sayfasında kötü kesim gördün, `KENAR` satırı var ya da bir şekli elle kesmen gerekiyor |
| `$SK/DUZEN.md` | Derleme `UYARI`/`ELLE DÜZENLENECEK` bastı, `denetle.py` `TAŞMA`/`BÖLÜNMÜŞ HÜCRE?` dedi, sayfa görselinde düzen sorunu gördün ya da renk seçeceksin |

Tetikleyici durum oluştuğunda dosyayı açmadan düzeltmeye girişme: oradaki yol çoğu zaman kısadır ve tahminle yapılan düzeltme yeni sorun açar.

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

## Konum bağımsızlığı

Skill, Claude Code hangi klasörde açılmış olursa olsun aynı çalışır; çalışma klasörüne (cwd) hiçbir şey yazmaz ve ondan hiçbir şey beklemez.

- Bütün yollar **mutlak** verilir: kitap (`B`), skill (`SK`), çalışma klasörü (`<work>`). Göreli yol ya da `cd` kullanma.
- `<work>` = oturumun scratchpad klasörü varsa `<scratch>/w`, yoksa `$TEMP/ders-notu/<konu>` (`mkdir -p`).
- Son PDF **kitabın bulunduğu klasöre** (`dirname $B`) yazılır. Kullanıcı başka bir yer söylerse oraya yazılır. Kitabın klasörü yazılamıyorsa kullanıcıya sor.
- Ders belgesi (DUB/izlence) kitabın klasöründe ve üst klasöründe aranır, cwd'de değil.
- Kitap cwd'nin dışındaysa dosya erişimi için izin istenebilir. Bu normal, yolu değiştirmeye gerek yok.

## Akış

`B=<kitap.pdf, mutlak yol>` olarak:

0. **Başlangıç: sadece kaynak yolunu iste.** Kullanıcı kitabın yolunu vermediyse tek soru sor: kitabın PDF yolu. Ders adı, konu, sayfa aralığı sorma; bunlar kitaptan çıkar. (Yol tırnaklı, `~`, `Masaüstü` gibi verilebilir; `Masaüstü` = `~/Desktop`. Dosya bulunamazsa `ls` ile yakın adları göster.)
1. **Kitabı tanı ve kapsamı belirle** (kaynak metnini okumadan önce)
   - `$PY -W ignore $SK/../../ortak/envanter.py $B` → içindekiler (PDF sayfa aralıklarıyla) ve aynı klasörde daha önce üretilmiş içerik betikleri.
   - `$PY -W ignore $SK/scripts/book_info.py $B` → künye (başlık, yazar), PDF ↔ basılı sayfa farkı. Künyeden Doc'un `source` satırını ve kapaktaki kaynak paragrafını kur; ders/kapak adı konunun Türkçesi olur. Yer imi yoksa kitabın kendi "Contents" sayfasını `extract_text.py $B <ilk> <son> <dosya>` ile oku, basılı numaralara farkı ekle.
   - Kullanıcı konuyu bir ders belgesine atıfla verirse (ör. "DUB'de ilk vizeye kadar", "izlencedeki 3. hafta") kitabın klasöründe ve üst klasöründe o belgeyi ara (`*DUB*`, `*izlence*`, `*syllabus*`; .docx ise `word/document.xml`'den metni çıkar), haftalık konu listesini kitabın alt bölümleriyle eşle ve raporda bu eşlemeyi söyle.
   - Kullanıcı mesajında konu/sayfa aralığı zaten varsa doğrudan onu kullan. Yoksa bölüm listesini (ad + PDF aralığı) kısa bir tablo olarak göster ve hangi bölüm(ler)in istendiğini sor (`AskUserQuestion`, çok seçimli; uzun listede en olası 3–4 bölüm + "Other"). Alt bölüm gerekirse `book_info.py --toc-depth 3`.
   - Çözümlü örnekler kapsamdadır; özet, kaynakça ve kapsam dışı bölümler aralığa girmez. İçindekilerde bölüm sonu problemleri varsa `AskUserQuestion` ile sor: dahil edilsin mi (önerilen: hayır)? Evetse sayfalarını aralıklara ekle. Çözümlü kitapçık istenirse `soru-kitapcigi` skill'i kullanılır.
2. **Hazırla** (metin, sayfa farkı, şekiller — tek komut)
   `$PY -W ignore $SK/scripts/hazirla.py $B <ilk-son> [<ilk-son> ...] --work <work>`
   - Bu işin metni `<work>/metin.txt`'ye yazılır; numara dizini ve şekiller `<dirname $B>/.kaynak/envanter/<kaynak adı>/` altında kalır.
   - Aralıktaki PDF ↔ basılı sayfa farkını raporda kullan. Aralık bir bölümün ortasında başlıyor ya da bitiyorsa raporda hangi alt bölümleri kapsadığını söyle.
   - Şekil bayrakları aralığın sayfalarından seçilir ve gerekçesi yazılır. `hepsi envanterde` derse şekiller daha önce gözden geçirilmiştir: 3. adıma geç.
   - Değilse **gözle kontrol atlanamaz**: `AÇILACAK TEMAS SAYFALARI`'nın **hepsini** `Read` ile aç. Kötü kesim, `UYARI` ya da `KENAR` satırı varsa **SEKIL.md'yi oku** ve oradaki yolla düzelt; temas sayfaları temiz olana kadar tekrarla. Temizse `$PY -W ignore $SK/../../ortak/envanter.py $B --sekil-kaydet <work>`.
3. **Kaynağı oku** (bir kez)
   - Kapsamı tutan önceki içerik betiği varsa `metin.txt`'yi baştan okuma, betiği oku; betikte olmayan aralığın yalnız sayfalarını (`===== PDF sayfa N`) oku. Önceki betikten çalışacaksan başlarken tek cümleyle hatırlat: o belgedeki hata ve eksikler bu belgeye de geçebilir, incelenmediyse önce incelenmesi önerilir. Kullanıcı yine de devam derse bekleme; raporda hangi betikten çalışıldığını yaz.
   - Önceki betik yoksa `metin.txt`'nin tamamını `Read` ile parça parça oku. İçeriği yazmadan önce tüm aralığı oku; şekil numaralarını ve denklemleri listele.
   - **Formülleri kaynakla karşılaştır** (önceki betikten alınanlar dahil; hatalar belgeden belgeye geçer): `$PY -W ignore $SK/../../ortak/envanter.py $B --serit <work> [--aralik 6.1 6.40 | --no 6.1,6.2]` → numaralı denklemlerin kırpıntıları. Kaynak ders notuysa ve kitap aynı klasördeyse kitapla karşılaştır. Kesik görünen grup denklemlerde sayfaya bak.
4. **İçerik betiğini yaz** (`<work>/<konu>.py`). Önce `$SK/USLUP.md`'yi ve `$SK/examples/ornek_ders_notu.py`'yi baştan sona oku, aynı kalıbı izle. Örnek kitaptan bağımsız genel bir konudur; içerik, künye ve numaralar kitaptan gelir. API aşağıda.
   - Ana kaynaktaki her denklem, numaralı numarasız, türetimin ve çözümlü örneklerin ara adımları dahil yazılı olur: `y ve z için benzer şekilde` demek, ara adımı atlamak ya da numarayı metinde anmak yetmez. Numaralı denklem kendi satırında numarasıyla gösterilir (`… = … (3.27).` yetmez).
   - Şekle numarayla atıf yap ("Şekil 6.6'da …"); "aşağıdaki şekil", "yukarıdaki şekilde" deme: sığmayan şekil sonraki sayfaya geçebilir.
5. **Derle ve denetle** (her derlemeden sonra ikisi birlikte)
   - `PYTHONPATH=$SK/scripts $PY -W ignore <work>/<konu>.py <work>/out.pdf <work>`
   - `$PY -W ignore $SK/scripts/denetle.py <work>/out.pdf <work> --kaynak $B --aralik <ilk-son> [...]` → üslup, denklem kapsamı (kaynakla ve belge içi), şekil atfı, sayfa farkı; her aracın çıktısı kendi başlığı altında, sonda `ENGEL` / `GÖZLE` / `AÇ` satırları.
   - `ENGEL` satırlarını gider, yeniden derle, yeniden denetle. `ÖNERİ` satırlarına bak, yerindeyse düzelt. `ANILAN AMA YOK`: ya şekli ekle ya da atfı kaldır/yeniden yaz (`3-13a` gibi alt şekil atfı `3-13`'e sayılır). `VAR AMA ANILMAMIŞ` bilgi içindir: şekle metinde numarayla atıf ekle. Derleme `UYARI` bastıysa ya da `TAŞMA`/`BÖLÜNMÜŞ HÜCRE?` varsa **DUZEN.md'yi oku**.
   - **Ölçü, o işteki ana kaynaktır.** Kullanıcı hoca notlarını ana kaynak dediyse kitap değil onlar karşılaştırılır: `--kaynak` o dosyadır; birden çok dosyaysa her biri için `$SK/../../ortak/denklem_kapsam.py <kaynak> <work>/out.pdf --from <ilk> --to <son>` ayrıca çalıştırılır.
   - Yalnız kullanıcının kapsam dışı bıraktığı alt bölümler dışarıda kalır: denklemler `--disarida <dosya>`, şekiller `--haric <dosya>` ile, her satırda gerekçesiyle; raporda yazılır. Önemsiz görmek gerekçe değildir.
   - **Belgeden bir şey çıkarınca ona atıf yapan yerleri de güncelle:** düzeltme/hata kutusu, kapak (kaynak listesi, sayfa sayısı), içindekiler, çapraz atıflar. Çıkan içeriğe ait madde ya silinir ya da yeni yerini söyler.
6. **Sayfa düzenini gözle kontrol et**: ilk derlemede `AÇ` satırındaki **bütün** sayfaları, sonraki derlemelerde yalnız yeni `AÇ` listesini aç; görülmüş sayfayı yeniden açma, düzen akışı değiştiyse sayfa dengesi için `rv_ov.png` yeterli. Kontrol listesi: içindekiler tek sayfa mı; şekil kendi paragrafıyla aynı sayfada mı; sayfa sonunda yalnız başlık/yarım kutu var mı; büyük boşluk var mı; denklemlerde kutucuk (eksik glif) var mı; bir denklem grubu iki sayfaya bölünmüş mü; sayfa başında önceki paragraftan kalmış 1–2 satırlık artık var mı. Sorun görürsen DUZEN.md.
7. **Kopyala ve raporla**: PDF'leri kitabın klasörüne (`dirname $B`, ya da kullanıcının söylediği yere) kopyala, `ls` ile doğrula. İçerik betiğini ve `figs.json`'u `<pdf klasörü>/.kaynak/<PDF adı>/` içine de kopyala; sonradan düzeltme istenirse iş baştan yapılmaz. Son mesajda yolları, sayfa sayılarını, PDF ↔ kitap sayfa eşlemesini, kapsanan bölümleri, dışarıda bırakılanları gerekçesiyle ve kaynakta yazmayan, senin eklediğin kabul ve yorumları açıkça yaz ve işin bittiğini söyle. Sonuna şu öneriyi ekle: tekrar notu ve formül kağıdı bu notun içerik betiğinden üretilecek, kaçan hata ve ayrıntılar onlara da geçebilir; bu yüzden önce notu inceleyip düzeltmeleri bildirmesi, sonra sıradaki belgeyi istemesi önerilir.

## Teslim şartları

Hepsi sağlanmadan belge teslim edilmez ve "bitti" denmez:

- [ ] `denetle.py` son çalıştırmada **ENGEL** satırı vermedi: üslup `KESİN` listesi, denklem kapsamında `YOK` ve `YALNIZ ANILMIŞ`, belge içi `BELGEDE YALNIZ ANILMIŞ`, şekil atfında `ANILAN AMA YOK` boş; `TAŞMA` yok.
- [ ] Denklem kapsamı çıkış kodu 2 verdiyse ya da kaynağın denklemleri numarasızsa (slayt, görsel denklem) araç güvence vermez: ana kaynağın her sayfası görüntü olarak açıldı ve her denklem betikle tek tek karşılaştırıldı.
- [ ] Dışarıda bırakılan her denklem ve şekil kullanıcının kapsam dışı bıraktığı bir alt bölümdendir ve gerekçesi dosyada yazılıdır.
- [ ] Şekil temas sayfalarının hepsi açıldı ve temiz (ya da şekiller envanterden geldi).
- [ ] İlk derlemede bütün sayfa görselleri, sonrakilerde her `AÇ` listesi açıldı. Görüntü aracının sonucu boş ya da `media removed` dönerse o görsel görülmemiş sayılır: yeniden aç; görmediğin sayfa için "temiz" deme.
- [ ] İçindekiler tek sayfa.

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
d.cozum(...)                          # tam çözümlü örnek, kalıbı USLUP.md'de; çizimi d.kf(no, açıklama, h=…)
d.table([[başlık...], [satır...]], widths=[0.2, 0.8], title='Tablo 2.1 – ...')
g = d.grup_bas(); ...; d.grup_son(g)  # formül + şekil bütününü aynı sayfada tut
d.begin_keep(); ...; d.end_keep()     # aradakileri aynı sayfada tut (ör. soru listesi)
d.make()                              # multiBuild (içindekiler için 2 geçiş) + <work>/kayit.json (üslup denetimi)
```

Metin reportlab paragraf işaretlemesi kullanır: `<b>`, `<i>`, `<sub>`, `<super>`, `<br/>`, `<font color=...>`. `&`, `<` için `&amp;`, `&lt;`.

## Sık hatalar

Şekil kesimiyle ilgili belirtiler SEKIL.md'de, sayfa düzeni ve denklem dizgisiyle ilgililer DUZEN.md'dedir.

| Belirti | Neden / Çözüm |
|---|---|
| `ModuleNotFoundError` / `python` bulunamadı | Sistem Python'u kullanılmış; Ortam bölümündeki kurulum betiğinin verdiği `$PY` ile çalıştır |
| `UnicodeEncodeError` konsola yazarken | `PYTHONIOENCODING=utf-8` |
| Yanlış sayfalar okundu | Kullanıcı numarası PDF numarasıdır; betikler 1 tabanlı alır, indeks = no − 1. Bölüm aralıkları envanter.py / book_info.py'den (zaten PDF numarası) |
| `kayit.json yok` (üslup denetimi) | Not eski bir notlib ile ya da `d.make()` çağrılmadan derlenmiş; güncel `$SK/scripts` ile yeniden derle |
| Üslup `KESİN` satırı yanlış görünüyor | Alıntıyı içerik betiğinde arat. Kural Türkçede gerçekten doğru bir yazımı yakalıyorsa (ör. "bu şekilde" anlamında bir cümle) cümleyi yeniden kur; denetçiyi devre dışı bırakma, raporda kullanıcıya bildir |
