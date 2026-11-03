---
name: formul-kagidi
description: Use when the user asks for a formula sheet ("formül kağıdı", "formül sayfası", "formül özeti", "cheat sheet", "sınav için formüller") from a textbook PDF or from existing lecture-note PDFs, in any course — especially when formulas must be backed by diagrams, every term must be named under its formula, and the result must be a PDF. Starts by asking only for the source file path.
---

# Formül Kağıdı (Kaynaktan Türkçe PDF Formül Kağıdı)

Bir ders kitabı ya da ders notu PDF'inden, sınava/probleme hazır **formül kağıdı** üretir: konu başına kartlar, her formülün altında terim adları, sağda sembolleri gösteren şema. Altyapı `scripts/` içindedir; her seferinde yalnızca **şema betiği** ve **içerik betiği** yazılır. Skill hiçbir derse, kitaba ya da klasöre bağlı değildir: ders adı, kaynak satırı, kapsam ve formüller her seferinde verilen kaynaktan çıkarılır.

## Formül kağıdının biçimi (kullanıcının standardı)

Formül kağıdı **not değildir**: anlatım paragrafı, tarihçe, yöntem tanıtımı yoktur. Sayfadaki her şey şu parçalardan biridir:

1. **Başlık bandı**: `KONU – FORMÜL KAĞIDI` + alt satırda ders · kapsam (bölüm/alt bölüm aralığı) · "Denklem numaraları kaynaktakiyle aynıdır".
2. **Kart = bir kavram** (5–12 kart/konu). Kart başlığı: `n · Türkçe Ad (English term)`.
3. Kartın sol sütununda her formül için sırayla:
   - **etiket** (kalın, kısa: "Isı akısı", "Oran formu (n = 2)")
   - **formül** (mathtext) ........ **(kaynaktaki numara)**; numarası yoksa boş
   - **terimler satırı** — `terms(...)`: formüldeki **her sembol** için Türkçe ad + birim (aynı kartta daha önce tanımlanmamışsa)
   - gerekirse **► not**: geçerlilik koşulu, tipik değer aralığı, sık yapılan hata, eğilim (bir satır)
4. Formül türetilmiş biçimleri de içerir: problemde gereken **ters çözülmüş biçim** (ör. `L = k A ΔT / Q`), **oran formu** (sabit bilinmeden çözüm), sık kullanılan özel durum (ör. küre için V/A = D/6).
5. **Sağ sütunda şema**: formüldeki sembolleri (aynı yazımla) üzerinde gösteren kesit, vektör çizimi, diyagram ya da eğilim grafiği. Şema gerekmeyen kartta sağ sütuna sabitler tablosu ya da kısa kutu konur; ikisi de yoksa kart tam genişlik.
6. **Sabitler / tipik değerler tabloları** (kaynaktaki tablolar, numarasıyla) ilgili kartın içinde.
7. Son kart: **hesap sırası ve birimler** (hangi büyüklükten hangisine gidilir, birim dönüşümleri) — konu sayısal problem içeriyorsa.

Diğer kurallar:
- Dil Türkçe; terimin İngilizcesi kart başlığında ve gerektiğinde parantezde. Ondalık ayırıcı virgül (mathtext'te `0{,}5`).
- Birden fazla konu istenirse her biri **ayrı PDF**: `<kaynağın klasörü>\<Konu>_Formul_Kagidi.pdf`.
- Kullanıcı sayfa numarası verirse bunlar **PDF görüntüleyici numarasıdır**.
- Formüller kaynakta olduğu gibi alınır; uydurma katsayı/değer yazılmaz. Kaynakta olmayan ama problemde gerekli bir yardımcı bağıntı eklenirse (ör. V = πDN) numarasız bırakılır.

## Ortam (Windows / Mac / Linux)

Kullanıcının elle bir şey kurması gerekmez; Python, paketler ve yazı tipleri aşağıdaki adımla hazır olur.

- `SK` = bu skill yüklenirken en üstte yazan **Base directory** yolu (skill `~/.claude/skills` altında da, plugin önbelleğinde de olabilir; yolu varsayma).
- **İşe başlarken bir kez** Python ortamını hazırla:
  - Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File "$SK/../ortak/kur.ps1"`
  - Mac/Linux: `bash "$SK/../ortak/kur.sh"`
- Ortam hazırsa bu adım 1–2 sn sürer. İlk seferde Python ve paketleri indirir (1–3 dk, yönetici hakkı istemez, sistem Python'una dokunmaz); bu sürenin başında kullanıcıya haber ver.
- Çıktının son satırı `PY=<yol>`. Aşağıdaki komutlardaki `$PY` bu yoldur; sistemdeki `py`/`python` kullanılmaz. Betik `KURULUM BAŞARISIZ` derse mesajı kullanıcıya ilet.
- Her komutta `PYTHONIOENCODING=utf-8` ve `$PY -W ignore`. Komutlar Bash sözdizimindedir; yalnız PowerShell varsa `$env:PYTHONPATH="..."; & $PY ...` biçimine çevir.
- Yazı tipleri repoda gömülüdür (metin Carlito, matematik DejaVu Serif), kurulmaz. Formüller matplotlib mathtext (Computer Modern) ile çizilir.

## Konum bağımsızlığı

- Bütün yollar **mutlak**: kaynak (`B`), skill (`SK`), çalışma klasörü (`<work>`). `cd` ya da göreli yol kullanma; cwd'ye hiçbir şey yazma.
- `<work>` = oturumun scratchpad'i varsa `<scratch>/fk-<konu>`, yoksa `$TEMP/formul-kagidi/<konu>`.
- Son PDF **kaynağın bulunduğu klasöre** (`dirname $B`) yazılır; kullanıcı başka yer söylerse oraya. Yazılamıyorsa sor.
- Ders belgesi (DUB/izlence/syllabus) kaynağın klasöründe ve üst klasöründe aranır.

## Akış

0. **Başlangıç: yalnızca kaynak yolunu iste.** Yol verilmediyse tek soru: kaynak PDF'in yolu (kitap ya da ders notu; birden fazla olabilir). Ders adı, konu, sayfa sorma; kaynaktan çıkar. Dosya bulunamazsa `ls` ile yakın adları göster.
1. **Kaynağı tanı**: `$PY -W ignore $SK/scripts/find_formulas.py $B <work>` → künye, sayfa sayısı, içindekiler (PDF sayfa aralıklarıyla).
   - Mesajda konu/aralık varsa onu kullan. Bir ders belgesine atıf varsa ("vize konuları", "DUB'deki ilk 5 hafta") belgeyi bul (.docx → `word/document.xml`, .doc → `antiword -m UTF-8.txt`), haftalık konuları bölümlerle eşle, raporda söyle. Yoksa bölüm listesini göster ve `AskUserQuestion` ile sor (çok seçimli).
   - Kaynak daha önce yapılmış bir **ders notuysa** onun bölümleri kapsamdır; ders notu bir kitaptan yapılmışsa ve kitap aynı klasördeyse denklem numaraları/tablolar için kitaba da bak.
2. **Metni ve adayları çıkar**: `$PY -W ignore $SK/scripts/find_formulas.py $B <work> <ilk> <son>` → `<work>/metin.txt`, `<work>/formul_adaylari.txt`.
   - "Denklem metni okunamayan sayfalar" çıktısı varsa (kitaplarda matematik özel kodlu yazı tipindedir, `=` gibi işaretler bozuk çıkar) o sayfaları `$PY -W ignore $SK/scripts/review.py $B <work> 130 --pages 372,373` ile render edip `Read` ile **görerek** oku.
3. **Envanter çıkar** (yazmadan önce aralığın tamamını oku): her formül için no, ad, semboller + birimler, koşul; tablolar (no, değerler); çözümlü örneklerde kullanılan ters/oran biçimleri; konunun hesap sırası. Bunları kartlara grupla (bir kart = bir kavram; kart başına 2–7 formül) ve her karta hangi şemanın gideceğini belirle.
4. **Şemaları çiz**: `<work>/semalar.py` (dglib). Önce `$SK/USLUP.md`'yi (üslup rehberi) ve `$SK/examples/ornek_semalar.py`'yi oku. `PYTHONPATH=$SK/scripts $PY -W ignore <work>/semalar.py <work>` → `<work>/dg/*.png` + `KONTROL:` satırındaki `<work>/dg/_kontrol.png`.
   - **Derlemeye geçmeden `_kontrol.png`'yi `Read` ile aç.** Bakılacaklar: etiket bir okun, eğrinin ya da başka etiketin üstünde mi · yazı kesik mi · semboller formüldekiyle aynı mı. Düzeltip yalnızca o şemayı yeniden çiz (`... semalar.py <work> sema_adi`) ve kontrol görüntüsüne yeniden bak.
   - Yerleşim kuralı: sembol etiketleri ok/vektör alanının ve eğrilerin **dışına**, boş bölgeye konur (eğrinin uç noktasının yanına `ha='left'`); ölçü okları (`dim`) gövdeden ayrı bir şeritte durur.
5. **İçerik betiğini yaz**: `<work>/kagit.py` (kalıp için `$SK/examples/ornek_kagit.py`'yi baştan sona oku; API aşağıda). Örnekler kaynaktan bağımsız genel bir konudur; içerik kaynaktan gelir.
6. **Derle**: `PYTHONPATH=$SK/scripts $PY -W ignore <work>/kagit.py <work>/out.pdf <work>`. Stderr'deki `UYARI` satırlarını gider (küçülen formül → böl, eksik glif → başka simge).
7. **Gözle kontrol et**: `$PY -W ignore $SK/scripts/review.py <work>/out.pdf <work>` → önce `rv_ov.png` (sayfa dengesi), sonra **her** `rv<n>.png`. Kontrol listesi: her sembol adlandırılmış mı · formüller okunaklı mı (çok küçülen yok) · numaralar kaynakla aynı mı · şema kartıyla aynı yükseklikte mi, sembolleri formülle aynı mı · sayfa altlarında yarım sayfalık boşluk var mı (kart sırasını değiştir: büyük kartın ardından sığan küçük kart; ya da `figmaxh`/`figw` ayarla) · kutu (eksik glif) var mı.
8. **Kopyala ve raporla**: PDF'leri `dirname $B`'ye kopyala, `ls` ile doğrula. Son mesajda yolları, sayfa sayılarını, kapsanan bölümleri/denklem aralığını ve kartların listesini yaz.

## fslib API (`from fslib import *`)

```python
d = Sheet(out, work, 'KONU – FORMÜL KAĞIDI', 'Ders · kapsam · Denklem numaraları kaynaktakiyle aynıdır',
          'Konu – Formül Kağıdı', 'Yazar, Kitap, Bölüm n', color='#1F3A5F')   # color: kart başlık rengi
E = d.E
E(r'tex', '(2.1)', terms(('q', 'ısı akısı (W/m²)'), ('k', 'ısıl iletkenlik')), label='Etiket', note='tek satır', fs=12.5)
d.card('1 · Başlık (English)', [E(...), E(...), 'serbest not satırı', ...] + d.tbl(rows, [3*cm, 2*cm], 'Tablo 2.1 – ...'),
       fig='sema_adi',          # <work>/dg/sema_adi.png | mutlak png yolu | d.tbl(...) | [P('<b>kutu</b> ...')] | None
       cap='şekil altı açıklama', figw=0.40, figmaxh=5.6*cm)
sym('T_1')                      # satır içi sembol: italik T + alt 1 (matematik yazı tipi); 'T_1, T_2' birden çok
P('<b>Birimler</b><br/>1 MPa = 1 N/mm²')   # serbest paragraf (sağ sütun kutusu için)
d.pagebreak(); d.make()
```

- `terms` sembol yazımı: `taban[_alt][^üst]` (`'V_c'`, `'R_t'`, `'ε_V'`, `'f_α, f_β'`). Birim parantez içinde açıklamaya yazılır.
- Metin reportlab işaretlemesi: `<b>`, `<i>`, `<sub>`, `<super>`, `<br/>`; `&` → `&amp;`, `<` → `&lt;`.
- `\frac` otomatik `\dfrac` olur. Kelime/kısaltma olan alt indisler dik yazılır: `u_{\mathrm{max}}`, `f_{\mathrm{lam}}`, `T_{\mathrm{donma}}` (şemalarda da); tek harfli değişken indisleri (`t_o`, `C_L`) italik kalır. Boşluk: `\,` `\quad` `\qquad`. Desteklenmeyen: `\begin{...}` (cases/aligned/matrix) → iki ayrı `E(...)` satırı yaz (ikincinin numarası `''`).

## dglib (şema betiği)

`init(work)`, `save(fig, ad)`, `run(f1, f2, ...)`, `arrow(ax, p, q, c)`, `dim(ax, p, q, metin, off)` (ölçü oku), `angarc(ax, merkez, r, a0, a1, metin, tr)` (açı yayı), `clean_axes(ax)`; renkler `BLUE RED GRN ORG NAVY GREY`, dolgular `FILL_GREY FILL_ORANGE FILL_BLUE FILL_LILAC`. Şema boyutu ~`figsize=(3.4, 2.6)`; sembol etiketleri mathtext (`r'$t_o$'`, fontsize 10–11), açıklama yazıları 6.5–8.5 pt.

## Sık hatalar

| Belirti | Neden / Çözüm |
|---|---|
| `ModuleNotFoundError` / `python` bulunamadı | Sistem Python'u kullanılmış; Ortam bölümündeki kurulum betiğinin verdiği `$PY` ile çalıştır |
| `UnicodeEncodeError` | `PYTHONIOENCODING=utf-8` |
| `formul_adaylari.txt` boş ya da bozuk karakterli | Kaynak matematiği özel kodlu yazı tipinde; listelenen sayfaları `review.py --pages` ile render edip görerek oku. Aday listesi yalnızca yol gösterir, envanter metnin tamamından çıkar |
| `UYARI: formül %.. küçültüldü` | Formülü iki `E` satırına böl ya da `fs=11.8` ver; şemalı kartta `figw`'yi küçült |
| `Kart bir sayfaya sığmıyor` | Kartı ikiye böl: `n · Başlık` + `n · Başlık (devam)`; ya da tabloyu `fig=` ile sağ sütuna taşı |
| Sayfa sonlarında büyük boşluk | Kartlar bölünmez (KeepTogether). Sırayı değiştir, uzun kartı böl, `figmaxh` düşür |
| `mathtext hatası` | Desteklenmeyen komut; `\text{}` → `\mathrm{}`, ortam (`\begin`) → ayrı satırlar, `\left`/`\right` eşleşmesini kontrol et |
| Metinde kutu (□) | `UYARI: ... hiçbir yazı tipinde yok` → simgeyi değiştir (ör. `∛` yerine `^(1/3)`); metin yazı tipinde olmayanlar otomatik olarak matematik ya da yedek yazı tipine çevrilir |
| Şemada etiketler üst üste / yazı kesik | Yalnızca o şemayı düzelt ve yeniden çiz; `ax.set_xlim/ylim` genişlet, etiketi `ha/va` ile hizala; PNG'yi açmadan derlemeye geçme |
| Şemadaki sembol formüldekinden farklı | Şema etiketlerini formüldeki sembolle aynı yaz (`r'$h_1$'`); kitap şekli farklı sembol kullanıyorsa formülünkini esas al |
| Terimler satırında sembol eksik | Formülü tek tek tara: sağ ve sol taraftaki her harf ya `terms` içinde ya da aynı kartta önceki bir formülün altında adlandırılmış olmalı |
