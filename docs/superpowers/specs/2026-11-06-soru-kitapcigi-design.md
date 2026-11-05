# Soru Kitapçığı skill'i: kısa tasarım

## Amaç

Kitabın bölüm sonu problemlerinden ya da toplu soru PDF'lerinden, kullanıcının belirttiği konulara giren soruları seçip konu konu dizilmiş, Türkçe, **çözümlü soru kitapçığı** üretmek. Kullanım amacı sınava soru çözerek hazırlanmak. Biçim örneği: kullanıcının `Dokum_ve_Talasli_Imalat_Cozumlu_Sorular.pdf` dosyası (72 s., 191 soru). Biçimi örnek alınır; soruları repoya girmez.

## Kullanıcının kararları

- Soru ve çözüm dizgide bütün kalır.
- Her sorunun üstünde konu başlığı yazar; birkaç konu karışıyorsa belirtilir.
- Toplu soru verilmişse kullanıcının belirttiği konulardan soru seçilir.
- Soru kitaptaki şekle ya da tabloya dayanıyorsa kitaptan alınıp karta eklenir.
- Mevcut skill'lerin altyapısından yararlanılır.
- Önerilen renk, seçim ve doğrulama kuralları kabul edildi (aşağıda).

## Hedef dışı

Yeni soru üretmek, deneme sınavı, cevapsız kitapçık, not skill'lerinin yerine geçmek. Önceden görülen hatalar da yasak: şekli olmayan "şekilden" sorusu, kaynağı belirtilmeden kullanılan tipik değer, kontrol edilmemiş sayısal sonuç.

## Yaklaşımlar

- **Aynı plugin'de dördüncü skill (seçilen):** altyapı paylaşılır, kurulum değişmez.
- Ayrı repo: altyapının kopyalanması gerekir.
- `tekrar-notu`'na mod eklemek: o skill'in birimi madde listesi, buradaki birim soru kartı.

## Kart

- Üst bant: `Soru 5.82` + konu başlığı. Karma soruda `KARMA · 5.2 Katılaşma + 5.8 Kum Döküm`, ayırt edici renkle.
- Soru metni, gerekirse kitaptan şekil ve tablo, `ÇÖZÜM`, adımlar, `Sonuç` kutusu, kısa not.
- Numaralar kaynaktakiyle aynıdır. Sorunun verileri ve değerleri değiştirilmez.
- Sayfa düzeni önceliklidir: kartlar ölçülüp aynı konu içinde en az boşlukla dağıtılır, numara sırası korunmaz; konular karışmaz, bağlı sorular yan yana kalır (kullanıcı kararı).
- Kart bir sayfaya sığıyorsa bölünmez. Sığmıyorsa adım arasından bölünür, bant `(devam)` ile tekrar eder; soru metni ile çözüm başlangıcı aynı sayfada kalır.

## Belge

Kapak, tek konulu/karma açıklaması, konu başına soru numaralı içindekiler, kapsam notu (seçim ölçütü, çıkarılanlar ve nedenleri, kaynaktan alınan değerler), konu konu kartlar. Çıktı: `<kaynağın klasörü>/<Konu>_Cozumlu_Sorular.pdf`.

## Seçim

- Kullanıcı konuyu yazar ya da DUB'den çıkar. Belirtmediyse konu listesi sorulur.
- Konuya giren sorunun tamamı alınır. Kullanıcı sayı verirse farklı alt konu ve türlerden o kadar soru seçilir.
- Karma soru, ana konusu kapsamdaysa alınır ve ana konunun altına yazılır. Çözümü esas olarak kapsam dışı konuyu gerektiriyorsa çıkarılıp kapsam notunda anılır.
- Çözüme başlamadan önce kullanıcıya konu başına soru sayısı bildirilir. Uzun işlerde bu, token harcanmadan önce kapsamı daraltma fırsatıdır.

## Akış

1. Ortam ve `ortak/envanter.py`; konu ve problem sayfaları belirlenir, yalnız o aralıklar okunur.
2. Sorular `<work>/sorular.json`'a yazılır: no, sayfa, konu(lar), karma mı, gereken şekil/tablo, bağlı olduğu soru.
3. Soru dışında yalnız sorunun dayandığı numaralı sayfalar okunur (bkz. Okuma kapsamı).
4. Gereken şekiller `detect_figs`/`crop_figs` ile kesilir, envantere kaydedilir. Tablolar değerleriyle yazılır. Başka soruya bağlı soruda ("Problem 5.84'teki yolluk") eksik veri karta eklenir ve iki soru yan yana konur.
5. Konu konu içerik betiği (`p01.py`, `p02.py`, …), Write ile.
6. Sayısal sonuçlar `<work>/hesap.py` ile hesaplanır. Sonuç değeri karta bu hesaptan yazılır.
7. Derleme, `sayfa_fark.py` ile yalnız değişen sayfaların kontrolü, `denetim.py` ile otomatik kontrol.
8. Kopyalama (`.kaynak/` dahil) ve rapor.

## Okuma kapsamı

Yalnız soru sayfaları okunur (kullanıcı kararı). Önceki not betiğinden çalışılmaz: not, soruları ya zaten içerir ya da hiç okumamıştır. Soru kitabın bir denklemine, tablosuna ya da şekline dayanıyorsa `envanter.py --bul` ile yalnız o sayfa okunur. Daha önce kesilmiş şekiller envanterden kullanılır; yalnız eksikler kesilir (`--sekil-eksik`, `--yalniz`). `--sekil-kaydet` `figs.json`'u numara bazında birleştirir.

## Çözümlerin güvenilirliği

- Kaynakta cevap yoksa çözümü Claude yapar; kapakta açıkça yazar.
- Kaynakta cevap varsa çözüm onunla karşılaştırılır, uyuşmazlık raporlanır.
- Kitapta bulunamayan değer için varsayım yapıldıysa kartta "varsayım" olarak işaretlenir ve raporda listelenir.

## Yeni kod

- `skills/soru-kitapcigi/scripts/solib.py`: `tekrar-notu`'nun `tnlib`/`notlib` katmanı üzerine kart API'si (skill'ler birlikte kurulduğu için kopya tutulmaz).
- `denetim.py`: seçilen her soru PDF'te var mı, bandında konu var mı, soruda atıf yapılan şekil/tablo kartta var mı, kart bölünmüş mü.
- `SKILL.md`, `USLUP.md`, kitaptan bağımsız `examples/ornek_soru_kitapcigi.py`.
- Şekil kesme `ders-notu`'nun betiklerinden kullanılır.
- `README.md`, CI (`kurulum.yml`), plugin açıklaması güncellenir.
- Not skill'lerindeki problem sorusuna "çözümlü kitapçık için `soru-kitapcigi`" yönlendirmesi eklenir.

## Başarı ölçütü

Akış ya da talaş kitabından gerçek bir konu için kitapçık üretilir. Her soru bandında konu, gerekli şekil kartında bulunur, kart bölünmesi olmaz, sayısal sonuçlar `hesap.py` ile uyuşur, kitapta cevabı olan sorular karşılaştırılır. Kullanıcı biçimi örnekle kıyaslayıp onaylar.

## Oluşturucuya bırakılanlar

Kart yerleşiminin ayrıntıları, renk seçimi (`ortak/tema.py` paleti), `denetim.py` eşikleri.
