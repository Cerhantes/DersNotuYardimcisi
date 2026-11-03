# Kitabı tanır: künye, içindekiler (PDF sayfa numaralarıyla), PDF ↔ basılı sayfa farkı ve
# şekil başlığı / şekil etiketi yazı tipleri (detect_figs.py bayrakları için öneri).
# Kullanım: py -W ignore book_info.py <kitap.pdf> [--toc-depth 2] [--sample 40]
import pymupdf as fitz, re, argparse, collections

ap = argparse.ArgumentParser()
ap.add_argument('src')
ap.add_argument('--toc-depth', type=int, default=2, help='gösterilecek içindekiler derinliği')
ap.add_argument('--sample', type=int, default=40, help='yazı tipi/ofset için örneklenecek sayfa sayısı')
A = ap.parse_args()
d = fitz.open(A.src)
n = d.page_count

# 1) Künye
m = d.metadata or {}
print('== KÜNYE')
for k in ('title', 'author', 'subject', 'creationDate'):
    if m.get(k):
        print(f'  {k}: {m[k]}')
print(f'  sayfa sayısı: {n}')
first = ' | '.join(l.strip() for p in range(min(4, n)) for l in d[p].get_text().splitlines() if l.strip())[:400]
print(f'  ilk sayfalardan metin: {first}')

# 2) PDF ↔ basılı sayfa farkı: sayfanın ilk/son satırlarındaki tek başına duran sayıya bakılır
print('\n== SAYFA OFSETİ (PDF no − basılı no)')
step = max(1, n // A.sample)
offs = collections.Counter()
for i in range(n // 10, n, step):
    lines = [l.strip() for l in d[i].get_text().splitlines() if l.strip()]
    for l in lines[:3] + lines[-3:]:
        if re.fullmatch(r'\d{1,4}', l) and 0 <= (i + 1) - int(l) < 100:
            offs[(i + 1) - int(l)] += 1
            break
if offs:
    print('  ' + ', '.join(f'+{o}: {c} sayfa' for o, c in offs.most_common(5)))
    print('  (fark kitap boyunca değişebilir; kullanılan aralıkta extract_text.py çıktısıyla doğrula)')
else:
    print('  basılı sayfa numarası bulunamadı')

# 3) İçindekiler
print('\n== İÇİNDEKİLER (PDF sayfa no)')
toc = d.get_toc()
if toc:
    rows = [t for t in toc if t[0] <= A.toc_depth]
    for j, (lv, title, pg) in enumerate(rows):
        nxt = next((t[2] for t in rows[j + 1:] if t[0] <= lv), n + 1)
        print(f'  {"  " * (lv - 1)}{title.strip()}  [PDF {pg}–{max(pg, nxt - 1)}]')
else:
    print('  PDF\'de yer imi yok; kitabın kendi içindekiler sayfasını extract_text.py ile oku ve ofseti ekle.')

# 4) Yazı tipleri: şekil başlığı satırlarının ilk parçası + şekil alanındaki etiketler
print('\n== YAZI TİPLERİ (detect_figs.py için)')
cap_re = re.compile(r'^\s*(FIGURE|Figure|Fig\.|FIG\.|ŞEKİL|Şekil)\s*\d+[.\-]\d+')
capf, label, body = collections.Counter(), collections.Counter(), collections.Counter()
examples = {}
for i in range(n // 10, n, step):
    p = d[i]
    draws = [fitz.Rect(x['rect']) for x in p.get_drawings()] + [fitz.Rect(x['bbox']) for x in p.get_image_info()]
    for blk in p.get_text('dict')['blocks']:
        for ln in blk.get('lines', []):
            t = ''.join(s['text'] for s in ln['spans'])
            if cap_re.match(t):
                f = ln['spans'][0]['font']
                capf[f] += 1
                examples.setdefault(f, t.strip()[:60])
            for s in ln['spans']:
                body[s['font']] += len(s['text'])
                r = fitz.Rect(s['bbox'])
                if len(s['text'].strip()) <= 25 and any(dr.intersects(r) for dr in draws):
                    label[s['font']] += 1
print('  "Figure x.y" ile başlayan satırların ilk yazı tipi (kalın olan = başlık, diğerleri metin içi atıf):')
for f, c in capf.most_common(6):
    print(f'    {c:4d}  {f}   ör. {examples[f]!r}')
print('  çizim/resim alanına düşen kısa metinlerin yazı tipleri (şekil etiketi adayları):')
for f, c in label.most_common(6):
    print(f'    {c:4d}  {f}')
print('  gövde metni yazı tipleri (etiket regex\'i bunları YAKALAMAMALI):')
for f, c in body.most_common(4):
    print(f'    {c:6d}  {f}')
