# Ders Notu Yardımcısı

Ders kitabını ya da ders notunu ver, Claude Code sana Türkçe ders notu, tekrar notu ve formül kağıdını PDF olarak hazırlasın.

Aynı konu (Fourier yasası), üç farklı çıktı:

<table>
<tr>
<td width="33%" valign="top"><img src="docs/ornek-ders-notu.png" alt="Ders notu örneği"></td>
<td width="33%" valign="top"><img src="docs/ornek-tekrar-notu.png" alt="Tekrar notu örneği"></td>
<td width="33%" valign="top"><img src="docs/ornek-formul-kagidi.png" alt="Formül kağıdı örneği"></td>
</tr>
</table>

## Kurulum

Claude Code içinde şu iki komutu çalıştır:

```
/plugin marketplace add Cerhantes/DersNotuYardimcisi
/plugin install ders-notu-yardimcisi@ders-notu-yardimcisi
```

Sonra `/reload-plugins` yaz ya da Claude Code'u yeniden başlat.

Başka bir şey kurman gerekmez. İlk kullanımda skill, gereken Python ortamını 1–3 dakikada kendisi hazırlar. Yönetici şifresi istemez, sistemdeki Python'a dokunmaz.

## Kullanım

Claude Code'a ne istediğini yaz:

> Şu kitabın 6. bölümünden ders notu çıkar

> Bu nottan tekrar notu hazırla

> Vize konuları için formül kağıdı hazırla

Komutla da başlatabilirsin:

| Çıktı | Komut |
|---|---|
| Ders notu | `/ders-notu-yardimcisi:ders-notu` |
| Tekrar notu | `/ders-notu-yardimcisi:tekrar-notu` |
| Formül kağıdı | `/ders-notu-yardimcisi:formul-kagidi` |

Skill önce PDF'in yolunu, kapsam belli değilse konuyu sorar. Bölüm sonu problemlerinin okunup okunmayacağını da sana bırakır. Bitince PDF'i kaynağın bulunduğu klasöre kaydeder.

## Güncelleme ve kaldırma

Terminalde güncellemek için:

```
claude plugin marketplace update ders-notu-yardimcisi
claude plugin update ders-notu-yardimcisi@ders-notu-yardimcisi
```

Kendiliğinden güncellensin istersen: `/plugin` → Marketplaces → `ders-notu-yardimcisi` → Enable auto-update.

Kaldırmak için `claude plugin uninstall ders-notu-yardimcisi@ders-notu-yardimcisi` çalıştır ve Python ortamının durduğu `~/.claude/ders-notu-yardimcisi` klasörünü sil.

## Lisans

Kod MIT, bkz. [LICENSE](LICENSE). `ortak/fonts/` içindeki Carlito yazı tipi SIL Open Font License 1.1 ile dağıtılır, bkz. [OFL.txt](ortak/fonts/OFL.txt).
