---
name: soru-kitapcigi
description: Use when the user asks for a solved question booklet ("soru kitapçığı", "çözümlü sorular", "soruları çöz", "bölüm sonu problemlerini çöz", "soru bankası") from a textbook's end-of-chapter problems or from a question-set PDF, in any course. Selects the questions that belong to the topics the user names, keeps each question and its solution together on one card labelled with its topic, and adds the book's figures and tables a question depends on. For notes without solved problems use ders-notu or tekrar-notu instead. Starts by asking only for the source file path.
---

# Soru Kitapçığı (Kaynaktan Türkçe Çözümlü Soru PDF'i)

Ders kitabının bölüm sonu problemlerinden ya da toplu soru PDF'lerinden, belirtilen konulara giren soruları seçip konu konu dizilmiş, Türkçe **çözümlü soru kitapçığı** üretir. Altyapı `scripts/` içindedir; her seferinde `sorular.json`, `hesap.py` ve içerik betiği yazılır. Skill hiçbir derse bağlı değildir.

## Kitapçığın biçimi (kullanıcının standardı)

- **Soru ve çözüm tek karttır.** Kart bir sayfaya sığıyorsa bölünmez. Sığmıyorsa adım arasından bölünür, bant `(devam)` ile tekrar eder; soru metni ile çözümün başı aynı sayfada kalır.
- **Bant:** `Soru 5.82` ve sağda sorunun konu başlığı. Birkaç konu birlikte gerekiyorsa `KARMA · 5.2 Katılaşma + 5.8 Kum Döküm`.
- **Kart sırası:** soru metni, gerekirse kitaptan şekil ve tablo, `ÇÖZÜM`, adımlar, `Sonuç` kutusu, kısa not.
- **Numaralar kaynakla aynıdır;** sorunun verileri ve değerleri değiştirilmez.
- **Sayfa düzeni önceliklidir:** kartlar ölçülür, aynı konu içinde en az boşluk kalacak biçimde sayfalara dağıtılır (otomatik). Numara sırası korunmaz; konular karışmaz, `bagli` sorular yan yana kalır.
- **Belge:** kapak, içindekiler, konu başına soru numaralı dizin, kapsam notu, konu konu kartlar.
- Çıktı: `<kaynağın klasörü>/<Konu>_Cozumlu_Sorular.pdf`. Dil Türkçe, ondalık ayırıcı virgül.

Yasaklar: şekli olmayan "şekilden" sorusu, kaynağı belirtilmeden kullanılan tipik değer, kontrol edilmemiş sayısal sonuç, yeni soru uydurmak.

## Seçim

- Konuları kullanıcı yazar ya da ders belgesinden (DUB) çıkarılır. Belli değilse konu listesi sorulur.
- Konuya giren soruların **tamamı** alınır. Kullanıcı sayı verirse farklı alt konu ve türlerden o kadar soru seçilir.
- Karma soru, ana konusu kapsamdaysa alınır ve ana konunun altına yazılır. Çözümü esas olarak kapsam dışı konuyu gerektiriyorsa çıkarılır ve kapsam notunda anılır.
- Sınavda çıkmayacak türden, çözümü çok uzun tablo gerektiren sorular (kabaca 20 satırdan uzun) alınmaz; `cikarilan` listesine ve kapsam notuna yazılır.
- Kitap verisine dayanan soru kitaptan tamamlanır. Kitapta da bulunamayan değer için `varsayim=` ile açıkça varsayım yapılır ya da soru nedeniyle birlikte çıkarılır.

## Ortam (Windows / Mac / Linux)

Kullanıcının elle bir şey kurması gerekmez.

- `SK` = bu skill yüklenirken en üstte yazan **Base directory** yolu (yolu varsayma). `DN=$SK/../ders-notu`.
- **İşe başlarken bir kez:** Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File "$SK/../../ortak/kur.ps1"`; Mac/Linux: `bash "$SK/../../ortak/kur.sh"`. İlk seferde 1–3 dk sürer, kullanıcıya haber ver.
- Çıktının son satırı `PY=<yol>`. Sistemdeki `py`/`python` kullanılmaz. `KURULUM BAŞARISIZ` derse mesajı ilet.
- Her komutta `PYTHONIOENCODING=utf-8` ve `$PY -W ignore`. Komutlar Bash sözdizimindedir.

## Renk

Renkler yalnız `ortak/tema.py` paletinden gelir: `petrol kiremit yesil hardal mavi kirmizi turkuaz zeytin`. Her `konu()` sıradaki rengi alır; `konu('...', renk='yesil')` ile seçilebilir. Karma bant sabit renktedir. Hex renk yazma, koyu dolgulu bant kullanma.

## Konum bağımsızlığı

Bütün yollar mutlak. `<work>` = oturum scratchpad'i varsa `<scratch>/sk-<konu>`, yoksa `$TEMP/soru-kitapcigi/<konu>`. Son PDF kaynağın klasörüne yazılır; yazılamıyorsa sor. Ders belgesi kaynağın klasöründe ve üst klasöründe aranır.

## Akış

0. **Yalnızca kaynak yolunu iste.** Birden çok kaynak verilebilir (ör. toplu soru PDF'i + kitap). Toplu soru PDF'i verildiyse aynı klasörde ya da mesajda kitap var mı bak; şekil ve tablolar kitaptan gelir.
1. **Envanter:** `$PY -W ignore $SK/../../ortak/envanter.py $B` → içindekiler ve önceki içerik betikleri. Konuları ve problem sayfalarını belirle, sonra `envanter.py $B <problem aralıkları> --work <work>`. Okunan yalnız soru sayfalarıdır; konu anlatımı, özet ve kaynakça okunmaz. Metni okunmayan (taranmış) sayfaları `$SK/../formul-kagidi/scripts/review.py $B <work> 130 --pages n` ile render edip görerek oku.
2. **Sınıflandır:** kapsama giren soruları `<work>/sorular.json`'a yaz:
   ```json
   {"sorular": [{"no": "5.82", "konular": ["5.2 ...", "5.8 ..."], "sayfa": 412, "sekiller": ["5.10"], "tablolar": ["8.3"], "bagli": "5.84", "sayisal": true, "cevap": "≈ 0,5 dk"}],
    "cikarilan": [{"no": "5.92", "neden": "..."}]}
   ```
   `konular`da ilki ana konudur ve bantta aynen yazılan metinle eşleşir. `sekiller`, `tablolar`, `bagli`, `sayisal`, `cevap` isteğe bağlıdır; `cevap` kaynakta cevap varsa yazılır.
3. **Çözmeden önce sor:** konu başına soru sayısını ve toplamı `AskUserQuestion` ile bildir: devam mı, daraltılsın mı? Soru sayısı token'ı doğrudan belirler; 100 soru üzerinde bunu açıkça söyle.
4. **Yalnız sorular okunur:** konu anlatımı okunmaz; konu başlıkları içindekilerden gelir, çözümler soruların üzerinden yapılır. Soru kitabın bir denklemine, tablosuna ya da şekline dayanıyorsa `$PY -W ignore $SK/../../ortak/envanter.py $B --bul 8.30,8.4` ile sayfasını bul, yalnız o sayfayı oku (`envanter.py $B 495-495 --work <work>`, sonra `<work>/metin.txt`). Sayısal veri kitap tablosundan geliyorsa tahmin etme, tabloyu oku. Sözel bir sorunun cevabından emin değilsen ilgili alt bölümün sayfalarını içindekilerden bulup oku.
5. **Şekiller:** `$PY -W ignore $SK/../../ortak/envanter.py $B --sekil-eksik 5.1,5.2` → yalnız `EKSİK ŞEKİL` satırındakiler kesilir: `$PY -W ignore $DN/scripts/detect_figs.py $B <work> <ilk> <son>` → `$PY -W ignore $DN/scripts/crop_figs.py $B <work>` → temas sayfalarını aç (hata düzeltmeleri `ders-notu` skill'inde: `split.json`, `over.json`) → `envanter.py $B --sekil-kaydet <work> --yalniz <eksik numaralar>` (aralıktaki eski, elle düzeltilmiş kesimler ezilmez). Sonra `envanter.py $B --sekil-al <work>`. Problem şekilleri (`FIGURE P5–32` gibi) varsayılan başlık aramasına takılmaz: `--cap` ver ya da `over.json` ile kes; numarasız şekle soru numarasıyla ad ver. Kitap tabloları değerleriyle `TB(..., baslik='Tablo n – Açıklama')` ile yazılır.
6. **Bağlı sorular:** "Problem 5.84'teki yolluk" gibi soruda eksik veri karta eklenir; hem `sorular.json`'a hem `soru(..., bagli='5.84')`'e yazılır, iki soru yan yana kalır.
7. **Hesap:** `<work>/hesap.py` (kalıp `$SK/examples/ornek_hesap.py`), `PYTHONPATH=$SK/scripts $PY -W ignore <work>/hesap.py <work>`. Kartta yazılacak sonuçları `h.kaydet(no, ad, deger, birim, ondalik)` ile kaydet, ara değerleri kaydetme. Kaynakta cevap varsa karşılaştır, uyuşmazlığı raporla.
8. **İçerik:** önce `$SK/USLUP.md` ve `$SK/examples/ornek_soru_kitapcigi.py`'yi oku. Konu konu `<work>/p01.py`, `p02.py`… **Write aracıyla** yaz (ilki `start` ve `kapak`, sonuncusu `make()`), `cat p*.py > kitapcik.py`. Sonuçlar elle değil `R(no, ad)` ile yazılır.
9. **Derle:** `PYTHONPATH=$SK/scripts $PY -W ignore <work>/kitapcik.py <work>/out.pdf <work>`. stderr'deki `VARSAYIM` ve `UYARI` satırlarına bak.
10. **Denetle:** `$PY -W ignore $SK/scripts/denetim.py <work>/out.pdf <work>`. `DENETİM TAMAM` görmeden bitirme. `UZUN KART` sayfalarına bak, `CEVAP KARŞILAŞTIR` satırlarını çözümle karşılaştır.
11. **Gözle kontrol:** `$PY -W ignore $SK/../../ortak/sayfa_fark.py <work>/out.pdf <work>` → yalnız `AÇILACAK` görsellerini aç, `TAŞMA` ve `BÖLÜNMÜŞ HÜCRE?` satırlarını gider.
12. **Kopyala ve raporla:** PDF'i `dirname $B`'ye; `kitapcik.py`, `hesap.py`, `sorular.json`, `sonuc.json`'u `<dirname $B>/.kaynak/<PDF adı>/` içine kopyala. Rapor: yol, sayfa ve soru sayısı, çıkarılanlar ve nedenleri, varsayımlar, cevap karşılaştırması, soru dışında okunan sayfalar.

## Çözümlerin güvenilirliği

- Kaynakta cevap yoksa çözümü Claude yapar; `kapak(..., kaynakta_cevap=False)` bunu kapağa yazar.
- Kaynakta cevap varsa `kaynakta_cevap=True`, çözüm cevapla karşılaştırılır.
- Emin olunmayan çözüm kesin gibi yazılmaz: `notu=` ile söylenir ve raporda listelenir.

## solib API (`from solib import *`)

```python
d = start(out, work, 'KONU', 'Konu – Çözümlü Sorular', 'Kaynak: Yazar, Kitap')
kapak(['<b>Kapsam:</b> ...'], kaynakta_cevap=False, kapsam_notu='Çıkarılan sorular ve nedenleri')
bolum('Bölüm 5 – Döküm')                 # içindekilerde 1. düzey
konu('5.2 Metallerin Katılaşması')       # 2. düzey, sıradaki renk
soru('5.82', ['5.2 Katılaşma', '5.8 Kum Döküm'], 'Soru metni',
     ['paragraf adım', H('hesap satırı'), M(['madde', 'madde']), TB([['Başlık', 'B'], ['a', 'b']], [0.6, 0.4], baslik='Tablo 8.5 – Açıklama'), G(work + '/grafik.png', 'Altyazı')],
     sonuc='≈ %s' % R('5.82', 't'), notu='kısa not', varsayim='k = 50 W/m·K alındı', sekil=[('5.10', 'Türkçe altyazı')], ek=[TB(soruda_verilen_tablo)], bagli='5.84')
make()
```

`sekil` kitap şekli, `ek` sorunun kendi verisi (ikisi de ÇÖZÜM'den önce); `G` soruda istenen ve `hesap.py`'de çizilen grafik (çözümün içinde).

Metinler `S()`'den geçer: `t_o`, `D_{ort}`, `f^2`, `V^{−1/n}`; kalın `<b>`, `&` → `&amp;`, `<` → `&lt;`.

## Sık hatalar

| Belirti | Çözüm |
|---|---|
| `ValueError: adım bir sayfadan uzun` | Tabloyu ikiye böl ya da uzun adımı `M` ile maddelere ayır |
| `KeyError: şekil yok (figs.json)` | 5. adım: kes, `--sekil-kaydet`, `--sekil-al` |
| `KeyError: hesap.py içinde yok` | `hesap.py`'yi çalıştır ya da kaydı ekle |
| `SORUN: bantta konu uyuşmuyor` | `soru()` konuları ile `sorular.json` aynı metin olmalı |
| `SORUN: şekilsiz atıf` | Şekli `sekil=` ile karta ekle ya da atfı kaldır; karşılanamıyorsa soruyu kapsam notuna taşı |
| `SORUN: soru Tablo n'e atıf yapıyor` | Tabloyu `TB(..., baslik='Tablo n – ...')` ile karta ekle |
| `SORUN: hesap sonucu kartta yok` | Sonucu `R()` ile yaz ya da ara değeri `hesap.py`'den çıkar |
| `ModuleNotFoundError` / `UnicodeEncodeError` | Kurulum betiğinin verdiği `$PY`, `PYTHONIOENCODING=utf-8` |
