# Claude Code skill'leri: ders notu, tekrar notu, formül kağıdı

Ders kitabı ya da ders notu PDF'lerinden Türkçe çalışma materyali (PDF) üreten üç [Claude Code](https://claude.com/claude-code) skill'i.

*Three Claude Code skills that turn textbook PDFs into Turkish study material: lecture notes, review sheets and formula sheets.*

| Skill | Ne yapar |
|---|---|
| `ders-notu` | Ders kitabından, kitabın kendi şekilleriyle, konuyu sıfırdan anlatan Türkçe ders notu |
| `tekrar-notu` | Ders notu ya da kitaptan madde madde, hiçbir ayrıntıyı atlamayan tekrar özeti |
| `formul-kagidi` | Şemalarla desteklenmiş, her terimi adlandırılmış formül kağıdı |

Kullanım: Claude Code'da `/ders-notu`, `/tekrar-notu` ya da `/formul-kagidi` yaz ya da "şu kitaptan ders notu çıkar" de. Skill yalnızca PDF'in yolunu sorar.

## Kurulum

### 1. Python ve paketler

| | Windows | Mac |
|---|---|---|
| Python | [python.org](https://www.python.org/downloads/) kurulumu (`py` komutu gelir) | `brew install python` (`python3`) |
| Paketler | `py -m pip install reportlab pymupdf pypdf pillow matplotlib numpy` | `python3 -m pip install reportlab pymupdf pypdf pillow matplotlib numpy` |

### 2. Yazı tipi (yalnız Mac)

PDF'ler Calibri yazı tipiyle dizilir. Windows'ta Calibri hazır gelir. Mac'te Microsoft Office kuruluysa
Office'in içinden otomatik bulunur. Office yoksa Calibri ile birebir aynı ölçülerdeki açık kaynak Carlito'yu kur:

```
brew install --cask font-carlito
```

Kurmazsan da çalışır: matplotlib ile gelen DejaVu kullanılır, PDF'ler ~%10 uzun çıkar.

### 3. Skill'leri indir

Claude Code kişisel skill'leri `~/.claude/skills/` klasöründen okur.

**Klasör yoksa ya da boşsa:**

```
git clone https://github.com/Cerhantes/DersNotuYardimcisi.git ~/.claude/skills                    # Mac
git clone https://github.com/Cerhantes/DersNotuYardimcisi.git "%USERPROFILE%\.claude\skills"      # Windows
```

**Klasörde başka skill'lerin varsa** (`git clone` dolu klasöre yazmaz):

```
cd ~/.claude/skills
git init
git remote add origin https://github.com/Cerhantes/DersNotuYardimcisi.git
git pull origin main
```

`.gitignore` yalnız bu üç skill'i takip eder. Klasördeki diğer skill'lerine dokunulmaz.

Ardından Claude Code'u yeniden başlat.

## Güncelleme

```
cd ~/.claude/skills && git pull
```

## Notlar

- `tekrar-notu`, kaynakta şekil bulamazsa `ders-notu`'nun şekil kırpma betiklerini kullanır. İkisini birlikte kur.
- Her skill'in `USLUP.md` dosyası üslup rehberidir. `examples/` klasöründeki betikler kitaptan bağımsız, genel bir konuyu (ısı iletimi) işleyen
  kalıp örnekleridir; kitap olmadan da derlenir (`examples/` içindeki her dosyanın başında çalıştırma satırı var).

## Lisans

MIT — bkz. [LICENSE](LICENSE).
