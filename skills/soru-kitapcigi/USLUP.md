# Soru Kitapçığı üslup rehberi

İçerik betiğini yazmadan önce bu dosyayı ve `examples/ornek_soru_kitapcigi.py`'yi oku. Örnekten kalıbı al, içerik kullanıcının kaynağından gelir.

## Soru metni

- Anlamı, verileri ve birimleri değiştirmeden Türkçeye çevrilir.
- **Kelimesi kelimesine çevirme:** cümleyi anlamından yeniden Türkçe kur, yazdıktan sonra Türkçe okunuşunu kontrol et. `far downstream` → "çok akış aşağısında" değil, "akış yönünde çok ileride". Yerleşik terimler (`akış aşağısı`, `sınır tabaka`) kalır.
- Terimin İngilizcesi gerekirse parantezde: `kapalı besleyici (blind riser)`.
- Başka soruya atıf numarasıyla kalır: `Problem 5.84'teki yolluk`.

## Sayısal çözüm

- Önce kabuller ve verilenler, sonra adımlar; her hesap satırı `H(...)` ile.
- Bağıntı önce sembolle, sonra sayılarla yazılır: `Q = k A ΔT / L = 0,7 × 10 × 20 / 0,2 = 700 W`.
- Ondalık ayırıcı virgül, her sonuçta birim. Sonuçlar `R(no, ad)` ile gelir.
- Çok değerli sonuç tabloyla (`TB`) verilir.

## Sözel çözüm

- Kısa giriş cümlesinden sonra `M([...])`; her maddede kalın anahtar kelime: `<b>Metaller:</b> ısıyı serbest elektronlar da taşır.`
- Sorunun istediği kadar yazılır; konu anlatımına dönüşmez.

## Sonuç ve not

- `sonuc=` tek cümle: sorunun cevabı. Sözel soruda ana fikir.
- `notu=` yalnız işe yarayan uyarı ya da yorum için: geçerlilik koşulu, sık yapılan hata.
- `varsayim=` soruda ya da kaynakta olmayan her değer için.
- Kaçınılacaklar: "bu soruda", "görüldüğü gibi", "sonuç olarak" gibi dolgu; sonucu cümle cümle tekrar etmek.
