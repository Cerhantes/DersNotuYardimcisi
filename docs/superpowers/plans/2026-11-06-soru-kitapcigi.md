# Soru Kitapçığı Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Plugin'e, konuya göre seçilmiş soruları kitabın şekilleriyle ve doğrulanmış çözümlerle kart kart dizen `soru-kitapcigi` skill'ini eklemek.

**Architecture:** `solib.py`, `tekrar-notu`'nun `tnlib`/`notlib` katmanı üzerine bölünebilir tek bir kart flowable'ı ekler. `denetim.py` PDF'i `sorular.json` ve `sonuc.json` ile karşılaştırır. Şekil kesme, envanter ve sayfa farkı mevcut betiklerden gelir.

**Tech Stack:** Python, reportlab, PyMuPDF, `ortak/kur.*` ortamı; testler stdlib `unittest` (yeni bağımlılık yok).

**Spec:** `docs/superpowers/specs/2026-11-06-soru-kitapcigi-design.md`

**Tasarımdan bilinçli sapma:** Tasarım `notlib`'in kopyalanmasını söylüyordu. `solib` kopya yerine `tekrar-notu/scripts`'ten içe aktarır; `tekrar-notu` zaten `ders-notu` betiklerine bağlı ve skill'ler birlikte kuruluyor, yani kopyanın sağlayacağı bağımsızlık yok.

## Global Constraints

- Renkler yalnız `ortak/tema.py` paletinden; mor/lacivert yok, koyu dolgulu bant yok, zemin açık.
- Her komut `PYTHONIOENCODING=utf-8` ve `$PY -W ignore` ile. `$PY` = `~/.claude/ders-notu-yardimcisi/env/Scripts/python.exe` (Windows).
- Yazı tipleri `ortak/fonts`'tan, ondalık ayırıcı virgül.
- Soru numaraları kaynakla aynı, sorunun verileri değiştirilmez.
- Repoya kitap içeriği girmez: örnek ve testler kitaptan bağımsız, kendi yazdığımız ısı iletimi sorularıyla.
- Commit başlıkları Türkçe karakterle, mesaj `git commit -F <utf-8 dosya>` ile. Sonuna oturumun Co-Authored-By ve Claude-Session satırları eklenir. **Push yalnız kullanıcı isteyince.**
- Yeni Python dosyaları Write ile yazılır (Bash heredoc `\n`/`\\` bozar).

## Review Focus

- Konu başlığının hemen ardından sayfadan uzun kart geldiğinde `LayoutError`/sonsuz döngü olmadan bölünmeli (Task 2 testi).
- Tek bir adım (dev tablo, büyük şekil) sayfadan uzunsa anlaşılır `ValueError` vermeli, reportlab hatası değil (Task 2 testi).
- `Soru 5.1` ile `Soru 5.10` karışmamalı; `8.35 / 8.73` gibi birleşik numara ve numarasız toplu sorular (`S12`) desteklenmeli (Task 3 testi).
- `figs.json` yokken derleme çalışmalı; kartın istediği şekil yoksa hangi numara olduğu söylenmeli (Task 2 testi).
- Metninde şekil atfı olup şekli olmayan kart yakalanmalı; örnekteki "şekilden" sorunu budur (Task 3 testi).

---

### Task 1: Envanterde şekil birleştirme ve eksik listesi

**Files:**
- Modify: `ortak/envanter.py` (`sekil_kopya`, `ozet`, `main`, üst açıklama)
- Create: `tests/test_envanter.py`
- Modify: `.github/workflows/kurulum.yml` (test adımı)

**Interfaces:**
- Produces: `sekil_kopya(kaynak_yer: str, hedef_yer: str) -> None` hedefteki `figs.json` ile numara bazında birleştirir, çakışmada kaynak kazanır. `sekil_eksik(yer: str, nolar: list[str]) -> list[str]`. CLI: `envanter.py <pdf> --sekil-eksik 5.1,5.2` → `HAZIR: 5.1` ve `EKSİK ŞEKİL: 5.2`; ikisi de yoksa ilgili satır `yok` der.

- [ ] **Step 1: Testleri yaz** (`test_kaydet_figs_birlesir`: `{"1.1":[0,[0,0,1,1]]}` üstüne `{"2.1":...}` kopyalanınca iki anahtar da kalır ve `fig/` içindeki iki PNG de durur; `test_eksik`: `sekil_eksik(yer, ['1.1','9.9']) == ['9.9']`; `test_figs_yokken_eksik`: `figs.json` yoksa tümü eksik döner.) `ortak` klasörü `sys.path`'e eklenir.
- [ ] **Step 2: Çalıştır, başarısızlığı gör.** `"$PY" -W ignore -m unittest tests.test_envanter -v` → birleşmediği ve `sekil_eksik` olmadığı için FAIL.
- [ ] **Step 3: Kodu yaz.** `ozet`'teki mesaj: `Şekiller hazır (%d şekil): kartta gerekenleri --sekil-eksik ile denetle, eksikleri kes, gerisini --sekil-al ile al.`
- [ ] **Step 4: Testler geçer**, ayrıca üç skill'in örnekleri derlenir (CI'daki "Örnekleri derle" komutları yerelde).
- [ ] **Step 5: CI'a ekle:** `Örnekleri derle`den önce `"$PY" -W ignore -m unittest discover -s tests -v`.
- [ ] **Step 6: Commit:** `envanter: şekil listesi birleştirilir, eksik şekiller raporlanır`

### Task 2: `solib` kart katmanı ve örnek

**Files:**
- Create: `skills/soru-kitapcigi/scripts/solib.py`, `skills/soru-kitapcigi/examples/ornek_soru_kitapcigi.py`, `tests/test_solib.py`
- Modify: `skills/ders-notu/scripts/notlib.py`, `skills/tekrar-notu/scripts/notlib.py` (`cover`'a kutu başlığı parametresi)
- Modify: `.github/workflows/kurulum.yml` (örnek derleme)

**Interfaces:**
- Consumes: `tnlib.start`, `tnlib.S`, `notlib.Doc`, `tema.PALET`, `tema.acik`. `solib` başta `skills/tekrar-notu/scripts`'i `sys.path`'e ekler.
- Produces (`from solib import *`):
  - `start(out, work, title, header, source, subtitle='Çözümlü Sorular', renk=None) -> Doc`; `<work>/figs.json` yoksa `{}` yazar.
  - `kapak(kapsam: list[str], kaynakta_cevap: bool, kapsam_notu: str | None = None) -> None`. `kaynakta_cevap=False` ise kutuda şu cümle yer alır: `Kaynakta cevap anahtarı yoktur; çözümler Claude tarafından yapılmıştır, sayısal sonuçlar Python ile hesaplanmıştır.` Tek konulu/karma açıklaması da kutudadır.
  - `bolum(ad) -> None` (içindekilerde 1. düzey), `konu(ad, renk=None) -> None` (2. düzey, renk sırası ilerler).
  - `soru(no: str, konular: list[str], metin: str, adimlar: list, sonuc: str | None = None, notu: str | None = None, varsayim: str | None = None, sekil: list[tuple[str, str]] = ()) -> None`.
  - Adım yardımcıları: düz `str` paragraf; `H(metin)` hesap satırı; `M(maddeler: list[str])`; `TB(satirlar, genislikler=None)`; hepsi `S()`'den geçer.
  - `make() -> None`: içindekilerin ardına soru dizinini ekler, derler, her varsayım için stderr'e `VARSAYIM <no>: <metin>` basar.
  - `R(no: str, ad: str) -> str` `<work>/sonuc.json`'dan biçimli değer; yoksa `KeyError('hesap.py içinde yok: <no>/<ad>')`.
- Bant metni tam olarak: `Soru <no>` + sağda tek konuda `<konu>`, birden çok konuda `KARMA · <konu> + <konu>`. Bölünen parçada `Soru <no> (devam)`.

- [ ] **Step 1: Testleri yaz** (`tests/test_solib.py`, PDF'i PyMuPDF ile okur): `test_tek_konu_bant`; `test_karma_bant` (`KARMA · A + B`); `test_kisa_kart_bolunmez` (sayfa sonuna denk gelen kart bütünüyle sonraki sayfada, soru metni ile `Sonuç` aynı sayfada); `test_uzun_kart_devam` (40 adımlı kartta `Soru 9.9 (devam)` var, ilk sayfada soru metni ve `ÇÖZÜM` birlikte); `test_konu_ardindan_uzun_kart` (hata yok); `test_dev_adim_valueerror` (sayfadan uzun tablo mesajında soru no); `test_figs_yokken_derlenir`; `test_olmayan_sekil_mesaji` (`KeyError`, mesajda numara); `test_sekil_kartta` (PNG ile `figs.json` kurulur, kart sayfasında görsel var); `test_soru_dizini` (konu satırında `1.1, 1.2`); `test_kapak_cevap_cumlesi`; `test_R_virgul` (`sonuc.json`'da `{"1.1":{"q":"500 W"}}` → `R('1.1','q')=='500 W'`, olmayan ad KeyError).
- [ ] **Step 2: Çalıştır, başarısızlığı gör:** `"$PY" -W ignore -m unittest tests.test_solib -v` → `solib` yok.
- [ ] **Step 3: `notlib.Doc.cover(self, lines, contents, kutu='BU NOTU NASIL KULLANMALISIN?')` yap**, iki kopyada aynı kalsın (`diff` boş).
- [ ] **Step 4: `solib.py`'yi yaz.** Kart, tek `Flowable` alt sınıfı `_Kart`:
  - `wrap`: bant + soru + şekiller + `ÇÖZÜM` + adımlar + sonuç + not toplam yüksekliği; herhangi bir parça `FH`'den uzunsa `ValueError('Soru <no>: adım bir sayfadan uzun, böl')`.
  - `split(aW, aH)`: toplam `FH` içine sığıyorsa `[]` (sayfa atlar, bütün kalır). Sığmıyorsa parça sınırından böler; ilk parçada en az bant + soru + şekil + `ÇÖZÜM` + ilk adım olmalı, olmuyorsa `[]`. Kalan, `devam=True` ile yeni `_Kart`.
  - `draw`: açık zemin bant (`tema.acik`), ana renkli yazı ve sol şerit; karma bant sabit `PALET['kirmizi']`; dış ince çerçeve. Soru alanı açık gri, `ÇÖZÜM` ana renkli başlık.
  - `sonuc` için `tema.acik` zeminli çerçeveli `Sonuç:` kutusu; `notu` gri italik; `varsayim` için `Varsayım:` etiketli turuncu satır.
  - Şekil genişliği en çok `FW - 24`, yüksekliği en çok 200 pt; altyazı `Şekil <no> – <metin>`.
- [ ] **Step 5: Örneği yaz:** ısı iletimi, 2 konu, 5 özgün soru (tek konu, karma, tablolu, varsayımlı, 1 yer tutucu şekilli). `figs.json` ve yer tutucu şekli `ornek_ders_notu.py`'deki kalıpla üretir. Komut: `PYTHONPATH=skills/soru-kitapcigi/scripts "$PY" -W ignore skills/soru-kitapcigi/examples/ornek_soru_kitapcigi.py out/sk.pdf out/sk`
- [ ] **Step 6: Testler geçer, örneğin sayfaları gözle kontrol edilir** (`ortak/sayfa_fark.py`, `AÇILACAK` görselleri). Bant, kart ve sonuç kutusu kullanıcının örneğiyle karşılaştırılır.
- [ ] **Step 7: CI "Örnekleri derle"ye ekle** (`out/sk` ve `test -s out/sk.pdf`).
- [ ] **Step 8: Commit:** `soru-kitapcigi: kart altyapısı ve örnek`

### Task 3: `denetim.py` ve hesap kaydı

**Files:**
- Create: `skills/soru-kitapcigi/scripts/denetim.py`, `skills/soru-kitapcigi/scripts/hesaplib.py`, `tests/test_denetim.py`
- Modify: `skills/soru-kitapcigi/examples/ornek_soru_kitapcigi.py`

**Interfaces:**
- Consumes: Task 2 bant metni, `R`.
- Produces:
  - `Hesap(work).kaydet(no: str, ad: str, deger: float, birim: str = '', ondalik: int = 2) -> str`: virgüllü metni `<work>/sonuc.json`'a yazar ve döndürür. `reportlab` gerektirmeden çalışsın diye `solib`'de değil, `hesaplib.py` içinde durur. Task 2'deki `R` aynı `sonuc.json`'u okur.
  - `<work>/sorular.json`: `{"sorular":[{"no":"5.82","konular":["5.2 …","5.8 …"],"sayfa":412,"sekiller":["5.10"],"tablolar":["8.3"],"bagli":"5.84","sayisal":true,"cevap":"≈ 0,5 dk"}],"cikarilan":[{"no":"5.92","neden":"…"}]}`; `sekiller`, `tablolar`, `bagli`, `sayisal`, `cevap` isteğe bağlı.
  - `denetle(pdf: str, work: str) -> list[str]`; CLI `denetim.py <pdf> <work>`: sorun yoksa `DENETİM TAMAM: <n> soru`, çıkış 0; varsa her satır `SORUN: …`, çıkış 1. Ayrıca bilgi: `UZUN KART: <no>` (bölünmüş) ve `CEVAP KARŞILAŞTIR: <no> <cevap>`.

- [ ] **Step 1: Testleri yaz** (`solib` ile küçük PDF üretip): `test_eksik_soru` (json'da olup PDF'te yok); `test_fazla_soru`; `test_5_1_ve_5_10_karismaz` (5.1 varken 5.10 "var" sayılmaz); `test_birlesik_numara` (`8.35 / 8.73`); `test_numarasiz` (`S12`); `test_konu_eksik` (bant konusu json'la uyuşmaz); `test_karma_etiketi` (iki konulu soru KARMA değilse sorun); `test_sekil_eksik` (`sekiller` var, kartta görsel yok); `test_tablo_eksik` (`Tablo 8.3` kartta yazmıyor); `test_sekilsiz_atif` (kart metninde `Şekil 5.1` ya da `Fig. 5.1` geçiyor, görsel yok); `test_sayisal_sonuc_yok` (`sayisal` ama `sonuc.json`'da kaydı yok); `test_bagli_komsu` (`bagli` soru PDF'te komşu değilse sorun); `test_hesap_virgul` (`kaydet('1.1','q',500.123,'W',1)=='500,1 W'`); `test_temiz` (`DENETİM TAMAM`).
- [ ] **Step 2: Çalıştır, başarısızlığı gör.**
- [ ] **Step 3: Kodu yaz.** Kart sınırı: her sayfada `^Soru (\S.*?)( \(devam\))?$` ile eşleşen bant satırı, sınır sonraki banda ya da sayfa sonuna kadar. Numara tam eşleşir; `konu` bant satırının sağ yarısından okunur.
- [ ] **Step 4: Testler geçer**; örnek `hesap` ve `sorular.json` ile `DENETİM TAMAM` verir.
- [ ] **Step 5: Örneğin `hesap.py` kalıbını** `examples/ornek_hesap.py` olarak ekle, CI'da örnekten önce çalıştır, ardından `denetim.py` çalıştır.
- [ ] **Step 6: Commit:** `soru-kitapcigi: otomatik denetim ve hesap kaydı`

### Task 4: Skill metinleri ve depo entegrasyonu

**Files:**
- Create: `skills/soru-kitapcigi/SKILL.md`, `skills/soru-kitapcigi/USLUP.md`, `docs/ornek-soru-kitapcigi.png`
- Modify: `skills/{ders-notu,tekrar-notu,formul-kagidi}/SKILL.md` (problem sorusu), `README.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `tests/test_solib.py`

**Interfaces:**
- Consumes: Task 1–3 komutları.
- Produces: `/ders-notu-yardimcisi:soru-kitapcigi`.

- [ ] **Step 1: Test yaz** (`test_skill_komutlari_var`): `SKILL.md`'de adı geçen tüm `scripts/*.py` ve `ortak/*.py` dosyaları diskte var; frontmatter'da `name: soru-kitapcigi`.
- [ ] **Step 2: Başarısızlığı gör.**
- [ ] **Step 3: `SKILL.md` yaz.** Diğer skill'lerin Ortam, Renk, Konum bağımsızlığı, Token tasarrufu bölümleriyle aynı kurallar. Tasarımın Akış bölümü adım adım; şu ayrıntılar açıkça: seçim kuralları ve çözmeden önce `AskUserQuestion` ile sayı onayı; "önce not çıkarılmış" senaryosu (hatırlatma cümlesi, `--sekil-eksik`); şekil sırası `detect_figs` → `crop_figs` → `--sekil-kaydet` → `--sekil-al`; uzun işlerde konu konu `p01.py`, `p02.py` ve `cat`; `hesap.py` ile `R`; `denetim.py` temiz olmadan bitirmeme; rapor (çıkarılanlar, `VARSAYIM` satırları, cevap karşılaştırması, hangi betikten çalışıldığı). `description`: "çözümlü sorular", "soru kitapçığı", "problem çöz" gibi tetikleyiciler, not skill'lerinden ayrımı.
- [ ] **Step 4: `USLUP.md` yaz.** Çözüm üslubu: önce verilen ve aranan, sonra adımlar, sonuç kutusu tek cümle; birim ve virgül; kelimesi kelimesine çevirme kuralı; soru metni anlamı ve değerleri değiştirmeden Türkçe; sözel soruda madde ve kalın anahtar kelime.
- [ ] **Step 5: Üç not skill'inin** problem sorusuna tek cümle ekle: "Çözümlü kitapçık istenirse `soru-kitapcigi` skill'i kullanılır."
- [ ] **Step 6: README:** görsel tablosu 2×2 olur, dördüncü panel örnekten "SORU KİTAPÇIĞI – Soruyu çözümüyle, konu konu verir" bandıyla ve yine Fourier yasasıyla; komut tablosuna satır; ilk cümleye soru kitapçığı; `plugin.json` ve `marketplace.json` açıklamaları.
- [ ] **Step 7: Tüm testler ve CI derlemeleri yerelde geçer.**
- [ ] **Step 8: Commit:** `soru-kitapcigi: skill metinleri ve README`

### Task 5: Gerçek kaynakla kabul denemesi

**Files:** Çıktılar repoya girmez: `Kaynaklar\İmal\<Konu>_Cozumlu_Sorular.pdf` ve `.kaynak/`.

- [ ] **Step 1:** Skill'i güncel depo dosyalarından izleyerek Kalpakjian kitabının 8.3 Takım Aşınması konusundan kitapçık üret. Bu konu önce not çıkarılmış senaryosunu sınar: `Talasli_Imalat_Ders_Notu.pdf`'in `.kaynak` betiği varsa kullanılır.
- [ ] **Step 2:** Başarı ölçütü kontrolü: `DENETİM TAMAM`, `sayfa_fark.py` görselleri temiz, her şekil atfının şekli kartta, sayısal sonuçlar `sonuc.json` ile aynı.
- [ ] **Step 3:** Kullanıcıya PDF'i ve örnekle karşılaştırmayı göster, geri bildirimi uygula. Harcanan yaklaşık token'ı raporla.
- [ ] **Step 4:** Düzeltmeler repoya geldiyse commit: `soru-kitapcigi: gerçek deneme düzeltmeleri`. Push için kullanıcıya sor.
