# Ders Notu Yardımcısı

Ders kitabı ya da ders notu PDF'lerinden Türkçe çalışma materyali (PDF) üreten üç [Claude Code](https://claude.com/claude-code) skill'i.

*Three Claude Code skills that turn textbook PDFs into Turkish study material: lecture notes, review sheets and formula sheets.*

| Skill | Ne yapar |
|---|---|
| `ders-notu` | Ders kitabından, kitabın kendi şekilleriyle, konuyu sıfırdan anlatan Türkçe ders notu |
| `tekrar-notu` | Ders notu ya da kitaptan madde madde, hiçbir ayrıntıyı atlamayan tekrar özeti |
| `formul-kagidi` | Şemalarla desteklenmiş, her terimi adlandırılmış formül kağıdı |

## Kurulum

Tek gereken Claude Code. Claude Code'a şunu yaz:

> https://github.com/Cerhantes/DersNotuYardimcisi skill'lerini kur

Ya da kendin kurmak istersen Claude Code içinde şu iki komutu çalıştır:

```
/plugin marketplace add Cerhantes/DersNotuYardimcisi
/plugin install ders-notu-yardimcisi@ders-notu-yardimcisi
```

Ardından `/reload-plugins` yaz ya da Claude Code'u yeniden başlat.

Kurulumdan sonra listede üç skill görünür. Python, paketler ve yazı tipleri için bir şey yapman gerekmez. İlk kullanımda skill eksikleri kendisi kurar (1–3 dakika, yönetici şifresi istemez). Bilgisayarda Python yoksa onu da indirir. Yazı tipleri repoyla birlikte gelir.

## Kullanım

Claude Code'da "şu kitaptan ders notu çıkar", "bu nottan tekrar özeti çıkar" ya da "formül kağıdı hazırla" de. Skill yalnızca PDF'in yolunu sorar.

Komutla başlatmak için: `/ders-notu-yardimcisi:ders-notu`, `/ders-notu-yardimcisi:tekrar-notu`, `/ders-notu-yardimcisi:formul-kagidi`.

## Güncelleme ve kaldırma

```
claude plugin marketplace update ders-notu-yardimcisi
claude plugin update ders-notu-yardimcisi@ders-notu-yardimcisi
```

Kendiliğinden güncellensin istersen: `/plugin` → Marketplaces → `ders-notu-yardimcisi` → Enable auto-update.

Kaldırmak için `claude plugin uninstall ders-notu-yardimcisi@ders-notu-yardimcisi` çalıştır ve Python ortamının durduğu `~/.claude/ders-notu-yardimcisi` klasörünü sil. Sistemdeki Python'a dokunulmaz.

## Claude için kurulum talimatı

Kullanıcı bu repodan kurulum isterse:

1. `claude plugin marketplace add Cerhantes/DersNotuYardimcisi`
2. `claude plugin install ders-notu-yardimcisi@ders-notu-yardimcisi --scope user`
3. Python ortamını şimdiden hazırla. Bu iki komutu, kurulan plugin'in kök klasöründen çalıştır (`claude plugin list --json` çıktısındaki `installPath`):
   - Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File ortak/kur.ps1`
   - Mac/Linux: `bash ortak/kur.sh`

   Son satır `PY=<yol>` ise ortam hazırdır. Bu betik Python yoksa [uv](https://docs.astral.sh/uv/) ile indirir; elle Python ya da paket kurma.
4. Kullanıcıya `/reload-plugins` yazmasını ya da Claude Code'u yeniden başlatmasını söyle.

## Notlar

- Üç skill birlikte kurulur: `tekrar-notu`, `ders-notu`'nun şekil kırpma betiklerini kullanır; hepsi `ortak/` klasörünü paylaşır.
- Her skill'in `USLUP.md` dosyası üslup rehberidir. `examples/` klasöründeki betikler kitaptan bağımsız, genel bir konuyu (ısı iletimi) işleyen kalıp örnekleridir; kitap olmadan da derlenir.

## Lisans

Üretilen PDF'lerde ana renk konudan konuya değişir, zeminler açıktır.

Kod MIT, bkz. [LICENSE](LICENSE). `ortak/fonts/` içindeki Carlito yazı tipi SIL Open Font License 1.1 ile dağıtılır, bkz. [OFL.txt](ortak/fonts/OFL.txt).
