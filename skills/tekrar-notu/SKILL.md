---
name: tekrar-notu
description: Use when the user asks for a review/summary PDF of material they already studied ("tekrar notu", "özet çıkar", "tekrar etmek için özet", "madde madde özet", "bilmem gerekenler", "sınav öncesi tekrar") from a lecture-note or textbook PDF, in any course — especially when no detail may be skipped, every topic must be bullet points, and figures should support the text. Starts by asking only for the source file path.
---

# Tekrar Notu (Kaynaktan Madde Madde Türkçe PDF Özet)

Konuyu zaten çalışmış birinin **tekrar** etmesi için, kaynaktaki her başlıkta bilinmesi gereken **her bilgiyi** madde madde veren, formülleri numaralarıyla, eğilimleri oklarla gösteren, kaynağın kendi şekilleriyle desteklenen PDF üretir. Not **yeniden öğretmez** (uzun anlatım paragrafı yok) ama **hiçbir detayı atlamaz**: kullanıcı için en önemli ölçüt budur. Skill hiçbir derse, kitaba ya da klasöre bağlı değildir.

## Tekrar notunun biçimi (kullanıcının standardı)

Belge şu parçalardan oluşur, bu sırayla:

1. **Kapak + tek sayfalık içindekiler.** Kapakta kaynak (dosya adı, sayfa sayısı, künye), kapsam (hangi bölümler; kaynakta "ek bilgi"/sınav dışı işaretli bölümler varsa öyle işaretlenir ama **atlanmaz**), "nasıl kullanılır" kutusu (renk kodları, ok anlamları).
2. **0. Semboller** tablosu (kaynakta sembol listesi varsa tamamı).
3. **Kaynağın her bölümü, aynı sıra ve numarayla.** Her bölümde:
   - **Maddeler** (`B`): her olgu, liste, koşul, neden, sayısal değer bir madde. Kaynakta "3 neden", "5 önlem" gibi sayılı liste varsa sayısı başlıkta yazılır ve hepsi verilir. Önemli terim **kalın**, İngilizcesi parantezde.
   - **Formüller** (`E`): kaynaktaki her numaralı denklem, numarasıyla; problemlerde gereken ters çözülmüş biçimler de.
   - **Tablolar** (`T`): kaynaktaki her tablo, numarası ve **tüm değerleriyle**.
   - **Şekiller** (`F`, `F2`): kaynağın kendi şekilleri, numaralarıyla; altyazı = şeklin söylediği bilgi (ne gösterdiği + dikkat edilecek nokta). İkili şekiller yan yana (`F2`).
   - **Kutular** (`X`/`BX`): `tanim` (mavi) tanımlar · `onemli` (turuncu) sınavda kritik / karıştırılan noktalar · `ornek` (yeşil) çözümlü örnek: verilen → yol → sonuç · `ipucu` sezgi · `ozet` (konunun rengi) bölüm sonu **HIZLI KONTROL** listesi.
4. **"Neyi değiştirirsem ne olur?" tablosu** — konu parametre–sonuç ilişkileri içeriyorsa: satır = değiştirilen parametre (↑), sütun = etkilenen büyüklükler (↑ ↓ —), son sütun "Diğer".
5. **Problem çözme**: çözüm sırası kutusu + kaynaktaki her çözümlü problemin özeti tablosu (problem no · konu · yol ve sonuç); bir problem çok sonuç veriyorsa (ör. tüm büyüklükler tablosu) sonuçların **tamamı** ayrı tablo.
6. **Kitap/kaynak sorularına kısa yanıtlar** — kaynakta varsa hepsi.
7. **Formül özeti** tablosu.
8. **Kendini Sına — kısa cevaplı**: kaynaktaki soruların hepsi, **cevabıyla**. Sayısal cevaplar Python ile hesaplanıp doğrulanır.

Diğer kurallar:
- Dil Türkçe; ondalık ayırıcı virgül. Eğilim gösterimi: `↑` artar, `↓` azalır, `→` sonuç/sebep zinciri.
- Kaynakta olmayan bilgi uydurulmaz. Kendi eklediğin derleme (eğilim tablosu, Kendini Sına cevapları) raporda "benim eklediklerim" olarak söylenir.
- Birden çok kaynak istenirse her biri **ayrı PDF**: `<kaynağın klasörü>\<Kaynak adı kökü>_Tekrar_Notu.pdf` (ör. `Isi_Ders_Notu.pdf` → `Isi_Tekrar_Notu.pdf`).

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
- Her `d.h1` sıradaki rengi alır. Konuya uyan rengi seçmek için `d.h1('...', renk='yesil')`; tüm notu tek renk yapmak için `start(..., renk='petrol')`.


## Konum bağımsızlığı

- Tüm yollar **mutlak**: kaynak `B`, skill `SK`, çalışma klasörü `<work>` = oturum scratchpad'i varsa `<scratch>/tn-<konu>`, yoksa `$TEMP/tekrar-notu/<konu>`. cwd'ye hiçbir şey yazılmaz.
- Son PDF kaynağın klasörüne (`dirname $B`) kopyalanır; kullanıcı başka yer söylerse oraya.

## Akış

0. **Yalnızca kaynak yolunu iste** (verilmediyse). Ders adı/konu/sayfa sorma; kaynaktan çıkar. Birden çok kaynak verilebilir → her biri için 1–9 ayrı.
1. **Kaynağı çıkar**: `$PY -W ignore $SK/scripts/kaynak.py $B <work>` → künye, içindekiler, `metin.txt`, `fig/*.png`, `figs.json`, `figsheet*.png`.
   - Şekil başlığı farklı biçimdeyse (`Fig 4-1`, `Figure 3.2`) `--cap` regex'ini uyarla.
   - **Şekil bulunamadıysa** (kaynak bir ders kitabı ve şekilleri vektör çizimse): `$SK/../ders-notu` skill'inin `detect_figs.py` + `crop_figs.py` adımlarıyla `<work>/figs.json` ve `<work>/fig/` üret (aynı biçim).
2. **Temas sayfalarının hepsini `Read` ile aç**: her şekil doğru numarada ve tam mı (başlıksız görseller listesine de bak).
3. **Metnin tamamını oku** (`Read`, parça parça, hiçbir sayfa atlanmadan). Yazmadan önce envanter çıkar: bölümler; her bölümdeki sayılı listeler; denklem numaraları; tablo numaraları; şekil numaraları; çözümlü örnek/problemler; sorular.
4. **İçerik betiğini yaz**: `<work>/tekrar.py`. Önce `$SK/USLUP.md`'yi (üslup rehberi) ve `$SK/examples/ornek_tekrar_notu.py`'yi baştan sona oku, aynı yapıyı izle. Örnek kaynaktan bağımsız genel bir konudur; içerik kaynaktan gelir. API aşağıda.
   - **Uzun kaynak (> ~40 sayfa):** `metin.txt`'yi ~300 satırlık parçalarla oku; her parçayı okur okumaz o bölümlerin içeriğini `<work>/p01.py`, `p02.py`… dosyalarına **Write aracıyla** yaz (ilk parça `start(...)` ve `d.cover(...)` içerir, son parça `d.make()` ile biter), en sonda `cat p*.py > tekrar.py`. Bash heredoc ile Python yazma — Türkçe kesme işaretli metinde tırnaklar kırılır.
5. **Derle**: `PYTHONPATH=$SK/scripts $PY -W ignore <work>/tekrar.py <work>/out.pdf <work>`
6. **Kapsam denetimi**: `$PY -W ignore $SK/scripts/kapsam.py $B <work>/out.pdf --from <ilk içerik sayfası>`
   - Denklem / Tablo / Şekil numarası eksikse → ekle (şekil görsel olarak konmadıysa en azından atıfla anılmalı).
   - "bilgi — HER BİRİNE BAK" listesindeki her satırı oku; bilgi taşıyorsa nota ekle. Hedef: bu listede yalnız bilerek dışarıda bırakılmış öğeler kalması.
   - "ara hesap" listesi: çözümün **sonucu** notta varsa bırak; sonuç yoksa ekle.
   - 5–6'yı liste temizlenene kadar tekrarla.
7. **Düzen denetimi**: `$PY -W ignore $SK/scripts/duzen.py <work>/out.pdf <work>` → şüpheli satırlar + `rv_*.png`.
   - Şüpheli satırların gerçek hata türleri: yalnız kalan `↑.` ya da tek kelime; kelime/sayı ortasından bölünmüş tablo hücresi (`83–86 HR | A`, `4000–500 | 0`); `HAM ALT ÇİZGİ` (`F_c` S()'den geçmemiş); `HAM İŞARETLEME` (`&amp;`).
   - Yanlış alarm: bilerek `<br/>` ile bölünmüş başlık, yan yana birleşik okunan tablo hücreleri (`246698`), tek hücreli `—`.
   - Sonra **bütün** `rv_*.png` görüntülerini aç: içindekiler tek sayfa mı, sayfa sonunda yalnız başlık var mı, şekil okunur mu (küçük yazılı şekil → `F(..., maxh=330, scale=1.0)` tek başına), büyük boşluk var mı, sayfa başında önceki paragraftan kalmış 1–2 satırlık artık var mı (notlib paragrafları zaten üstte ≥2 / altta ≥3 satır kalacak şekilde böler — `MIN_HEAD`, `MIN_TAIL`). Şüpheli sayfayı `pymupdf` ile 110–120 dpi render edip yakından bak.
8. **Kopyala**: `cp <work>/out.pdf "<dirname $B>/<kök>_Tekrar_Notu.pdf"`; `cmp` ile doğrula. `tekrar.py` ve `figs.json`'u `<dirname $B>/.kaynak/<kök>_Tekrar_Notu/` içine de kopyala; sonradan düzeltme istenirse iş baştan yapılmaz.
9. **Rapor**: dosya yolu, sayfa sayısı, kapsanan bölümler, kapsam denetimi sonucu (kalan bilerek dışarıda bırakılanlar), "benim eklediklerim" (eğilim tablosu, cevaplar).

## tnlib API (`from tnlib import *`)

```python
d = start(out, work, 'KONU (BÜYÜK HARF)', 'Konu – Tekrar Notu', 'Kaynak: Yazar & Yazar, Kitap, Bölüm n')
d.cover([kapsam satırları...], [nasıl kullanılır paragrafları...])     # kapak + içindekiler
d.h1('2. Başlık')                  # yeni bölüm (altında 9 cm yoksa sayfa atlar); d.h2('2.1 ...', need=6); d.h3('...')
B(['madde', ('>', 'alt madde'), ...], num=False)   # madde listesi
P('serbest paragraf')              # kısa bağlam cümlesi için; anlatım paragrafı yazma
E('Q = k A (T_1 − T_2) / L', '(3.1)')             # numaralı denklem; aynı satıra 2 denklem: araya 2+ boşluk
X('onemli', ['satır', 'satır'], title=None)        # kutu: tanim | onemli | ornek | ozet | ipucu | terim
BX('ozet', ['madde', ...], 'BÖLÜM 2 HIZLI KONTROL')  # madde listeli kutu
T([[başlık...], [satır...]], [0.3, 0.7], 'Tablo 2.1 – ...', fs=None)  # fs=8.4: dar, çok sütunlu tablo
F('3.1', 'altyazı', maxh=200, scale=0.8, terms='Layer = katman; ...')  # tek şekil
F2('2.1', '2.2', 'altyazı a', 'altyazı b', h=150)                      # yan yana iki şekil
d.make()
```

Yazım (hepsi `S()` süzgecinden geçer): `t_o` → t<sub>o</sub>, `D_{ort}` → D<sub>ort</sub>, `f^2` / `V^{−1/n}` → üst simge (`/ , .` içeren üs **mutlaka** `{}` içinde: `x^{1/n}`, `V^{0,2}`). Parantezsiz indis tek öğedir, ardındaki sembole taşmaz: `h_1A` → h<sub>1</sub>A, `d^2T` → d<sup>2</sup>T, `h_fA` → h<sub>f</sub>A; `T_ort`, `N_Re`, `T_iç`, `T_s1` bütün kalır, `e^2x` üstel olduğu için bütün kalır. Bitişik küçük harflerde `S()` kelime indis sanır, sınırla: `A_{c}k`; rakam + harf indis de `{}` ister: `x_{1a}`. Noktalı ve üslü semboller de indis alır: `Ė_g`, `q̇_0`, `q″_x`. Kalın `<b>`, italik `<i>`, `<br/>`. Metinde `&` → `&amp;`, `<` → `&lt;` (yalnız `start`'ın `source` argümanında düz `&`). Oklar, `=` ve paragrafın son kelimesi otomatik bağlanır.

## Sık hatalar

| Belirti | Neden / Çözüm |
|---|---|
| Satır sonunda yalnız `↑.` ya da tek kelime | Metin `S()`'den geçmemiş (doğrudan `d.p` / `d.bl` kullanılmış) → `B`/`P`/`X` kullan |
| Tablo hücresinde `83–86 HR` / `A`, `4000–500` / `0` | Sütun dar: birimi satır başlığına taşı, `fs=8.4`, başlığı `<br/>` ile böl, genişlikleri yeniden dağıt (toplam 1) |
| Hücrede kelime ortadan bölünmüş (`ka` / `dar`) | Hücre metnini kısalt ya da sütunu genişlet |
| Şekil altında ham `F_c` | `terms=` metni `F()` dışında verilmiş; `F(..., terms=...)` kullan |
| Sayfa başlığında `&amp;` | `start(... source=...)` içinde düz `&` yaz |
| İndis yanlış yere taşmış (`A_ck` → A<sub>ck</sub>, `x^ab`) | Bitişik küçük harfleri `S()` kelime sanır; `{}` ile sınırla: `A_{c}k`, `x^{a}b` |
| İki denklem yapışık (`F = R sin β N = R cos β`) | `E()` içinde araya en az 2 boşluk koy |
| Küçük yazılı şekil okunmuyor (ör. proses–pürüzlülük çizelgesi) | `F2` yerine tek başına `F(..., maxh=330, scale=1.0)` |
| `UYARI denklem tek satıra sığmadı` | Denklemi iki `E` satırına böl (ikincinin numarası `''`); açıklama metnini denklemden çıkarıp `P`/`B`'ye taşı |
| Denklem numarası numara sütununda iki satıra bölünmüş (`(6.106–6.10` / `7)`) | Birleşik numaralı denklemi ayrı `E` satırlarına ayır, her biri kendi numarasıyla (kapsam denetimi de böyle her numarayı görür) |
| Kapsam denetiminde "Şekil numaraları eksik" | O şekiller notta hiç anılmamış: ilgili maddenin yanına `F`/`F2` ekle (fotoğraf/ürün şekilleri dahil — kaynakta varsa notta da olmalı) |
| `h1` başlığı sayfa sonunda yalnız, tablosu sonraki sayfada | Artık otomatik: `T`/`F`/`F2` hemen önündeki başlıkları kendi bloğuna alır. Hâlâ oluyorsa başlık ile şekil/tablo arasına başka bir öğe (ör. `B`, `P`) girmiştir → `d.h1('...', need=16–18)` |
| Sayfa altında büyük boşluk, uzun tablo sonraki sayfada bütün halde | Artık otomatik: sayfanın 1/3'ünden uzun tablolar satır arasından bölünür (başlık satırı tekrar eder; başlık + tablo adı + ilk 3 satır birlikte kalır). Kısa tablolar tek parça kalır |
| Sayfa altında büyük boşluk, sonraki sayfa büyük şekille başlıyor | Şekil sığmadığı için kaçınılmaz; boşluk %40'ı aşıyorsa şekli `maxh` küçülterek ya da şekilden sonraki 1–2 maddeyi şeklin önüne alarak dene |
| `kaynak.py` sıralamada `TypeError` | Eski sürüm; `6.18a` gibi harfli numaralar için sıralama anahtarı düzeltildi — skill'deki güncel betiği kullan |
| Bölüm başlığı sayfa sonunda tek kaldı | `d.h2(..., need=12–14)` |
| Kapsam denetiminde çözümlü problem değerleri eksik | Problemin tüm sonuçları ayrı tabloyla verilmeli, yalnız seçilmiş birkaçı değil |
| `kaynak.py` hiç şekil bulmadı | Başlık biçimi farklı (`--cap`) ya da şekiller vektör → ders-notu skill'inin detect/crop adımları |
| `ModuleNotFoundError` / `python` bulunamadı / `UnicodeEncodeError` | Ortam bölümündeki kurulum betiğinin verdiği `$PY` ile çalıştır / `PYTHONIOENCODING=utf-8` |
