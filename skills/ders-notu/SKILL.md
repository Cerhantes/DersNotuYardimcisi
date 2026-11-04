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
3. **Metnin tamamını oku** (`Read` ile, parça parça). İçeriği yazmadan önce tüm aralığı oku; şekil numaralarını ve denklemleri listele.
4. **Şekilleri tespit et**
   `$PY -W ignore $SK/scripts/detect_figs.py $B <work> <ilk> <son> [1. adımdaki bayraklar]`
5. **Kes ve gözle kontrol et**
   `$PY -W ignore $SK/scripts/crop_figs.py $B <work> [--cap-above]` → `<work>/sheet_*.png` temas sayfalarının **hepsini** `Read` ile aç. Kümeler her başlığa otomatik atanır (en yakın küme + aynı satır/sütundaki alt şekiller); kitapta başlık şeklin üstündeyse `--cap-above` ver. `UYARI` satırları kontrol edilecek sayfaları gösterir. Tipik hatalar ve düzeltmeleri:
   - Küme yanlış şekle gitmiş / alt şekil eksik → `split.json`: `{"225": {"5.6": [0], "5.7": [1, 2]}}` (küme sırası det.json'daki sıradır).
   - Kesime gövde metni, denklem veya başlık girmiş, ya da şeklin bir parçası dışarıda kalmış → `over.json`: `{"5.18": [255, [x0, y0, x1, y1]]}`. Koordinatları det.json kümelerinden ve `page.get_text('dict')` satır kutularından türet.
   - Hatalar çoksa (ör. etiketler kesik ya da her şekle metin giriyor) önce 1. adımdaki bayrakları gözden geçir (`--label-font`, `--label-len`, `--pad`).
   Düzeltip `crop_figs.py`'yi yeniden çalıştır; temas sayfaları temiz olana kadar tekrarla.
6. **İçerik betiğini yaz** (`<work>/<konu>.py`). Önce `$SK/USLUP.md`'yi (üslup rehberi) ve `$SK/examples/ornek_ders_notu.py`'yi baştan sona oku, aynı kalıbı izle. Örnek kitaptan bağımsız genel bir konudur; içerik, künye ve numaralar 1. adımdan ve kitaptan gelir. API aşağıda.
7. **Derle**: `PYTHONPATH=$SK/scripts $PY -W ignore <work>/<konu>.py <work>/out.pdf <work>`
8. **Sayfa düzenini gözle kontrol et**: `$PY $SK/scripts/sheets.py <work>/out.pdf <work>/rv` → `rv_*.png` sayfalarının hepsini aç. Şüpheli sayfayı tek başına yüksek çözünürlükte render edip bak. Kontrol listesi: içindekiler tek sayfa mı, şekil kendi paragrafıyla aynı sayfada mı, sayfa sonunda yalnız başlık/yarım kutu var mı, büyük boşluk var mı, denklemlerde kutucuk (eksik glif) var mı, sayfa başında önceki paragraftan kalmış 1–2 satırlık artık var mı (notlib paragrafları zaten üstte ≥2 / altta ≥3 satır kalacak şekilde böler — `MIN_HEAD`, `MIN_TAIL`; görürsen o metin `d.p` dışında bir yolla eklenmiştir).
9. **Kopyala ve raporla**: PDF'leri kitabın klasörüne (`dirname $B`, ya da kullanıcının söylediği yere) kopyala, `ls` ile doğrula. İçerik betiğini ve `figs.json`'u `<pdf klasörü>/.kaynak/<PDF adı>/` içine de kopyala; sonradan düzeltme istenirse iş baştan yapılmaz. Son mesajda yolları, sayfa sayılarını, PDF ↔ kitap sayfa eşlemesini ve kapsanan bölümleri açıkça yaz ve işin bittiğini söyle.

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
| `UYARI denklem tek satıra sığmadı` | Denklemi iki `d.eq` satırına böl (ikinci satırın numarası `''`) veya kısalt; kutu içinde iki `d.beq` kullan |
| Denklemde/metinde boş kutu | Carlito'da olmayan glif (∛ ∝ ≃ vb.). `notlib.Paragraph` bunları otomatik olarak matematik ya da yedek yazı tipine çevirir; hiçbirinde yoksa `UYARI` basar, simgeyi değiştir |
| İçindekiler iki sayfaya taştı | İçerik betiğinde `ss['toc1']`/`ss['toc2']` fontSize/leading'i küçült (ör. 9.6/11 ve 8.4/9.4; satır dolgusu notlib'de zaten 1 pt) veya küçük alt başlıkları `h2` yerine `h3` yap (h3 içindekilere girmez). İki bölümlük uzun notlarda ~55 girdi sınırdır |
| İçindekilerde sayfa numaraları yanlış/boş | `d.make()` (multiBuild) kullan, `build` değil; içerik betiğinde `build` adlı değişken/fonksiyon tanımlama |
| Başlık sayfa sonunda yalnız, şekli/tablosu sonraki sayfada | Artık otomatik (`fig`/`table`/`end_keep` önceki başlıkları kendi bloğuna alır); hâlâ oluyorsa araya başka öğe girmiştir → `h1(..., need=...)` / `h2(..., need=...)` büyüt |
| Uzun tablo yüzünden sayfa altında büyük boşluk | Artık otomatik: sayfanın 1/3'ünden uzun tablolar satır arasından bölünür, başlık satırı tekrar eder |
| Şekil sayfa sonunda metninden koptu | `fig(..., keep=...)` ya da `begin_keep/end_keep` ile paragrafla birlikte tut; `maxh` küçült |
| Kesimde gövde metni / başlık görünüyor | `over.json` ile elle kesim ver (otomatik tespit her kitapta birkaç şekilde bunu yapar; temas sayfalarını atlama) |
