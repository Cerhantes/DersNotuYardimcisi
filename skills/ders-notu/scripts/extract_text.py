# Kitaptan sayfa aralığının metnini çıkarır ve PDF sayfa no ↔ kitap sayfa no farkını gösterir.
# Kullanım: python -W ignore extract_text.py <kitap.pdf> <ilk> <son> <cikti.txt>
# <ilk>/<son>: PDF görüntüleyicideki sayfa numaraları (1'den başlar, dahil).
import pymupdf as fitz, sys

src, a, b, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
d = fitz.open(src)
with open(out, 'w', encoding='utf-8') as f:
    for i in range(a - 1, b):
        p = d[i]
        f.write(f'\n===== PDF sayfa {i + 1} (idx {i}) imgs={len(p.get_images())} draws={len(p.get_drawings())}\n')
        f.write(p.get_text())

# Ofset kontrolü: ilk ve son sayfanın baş/son satırlarında kitabın basılı sayfa numarası görünür.
for i in (a - 1, b - 1):
    lines = [l for l in d[i].get_text().splitlines() if l.strip()]
    print(f'PDF sayfa {i + 1}: bas={lines[:2]!r} son={lines[-2:]!r}')
print('sayfa sayisi:', d.page_count, '->', out)
