"""Kaynak PDF'i tanıtır, metni çıkarır ve formül adaylarını listeler.

Kullanım: py -W ignore find_formulas.py <kaynak.pdf> <work> [ilk son] [--toc-depth N]
  ilk/son : PDF görüntüleyici sayfa numaraları (1 tabanlı, dahil); verilmezse yalnızca künye + içindekiler yazılır.
Çıktı (aralık verildiyse):
  <work>/metin.txt          sayfa işaretli tam metin  (===== PDF sayfa N)
  <work>/formul_adaylari.txt  denklem numaralı ya da matematik yazı tipli satırlar, sayfa numarasıyla
Kaynak bir ders kitabı da, daha önce hazırlanmış bir ders notu PDF'i de olabilir.
"""
import os, re, sys
import pymupdf as fitz

argv = sys.argv[1:]
depth = 2
if '--toc-depth' in argv:
    k = argv.index('--toc-depth'); depth = int(argv[k + 1]); del argv[k:k + 2]
args = argv
src, work = args[0], args[1]
os.makedirs(work, exist_ok=True)
d = fitz.open(src)
m = d.metadata or {}
print('Dosya   :', src)
print('Başlık  :', m.get('title') or '-', '| Yazar:', m.get('author') or '-', '| Sayfa:', d.page_count)

toc = [t for t in d.get_toc() if t[0] <= depth]
if toc:
    print('\nİçindekiler (PDF sayfa no):')
    for i, (lv, title, pg) in enumerate(toc):
        nxt = next((t[2] for t in toc[i + 1:] if t[0] <= lv), d.page_count + 1)
        print('  ' * (lv - 1) + '- %s  [%d–%d]' % (title.strip(), pg, max(pg, nxt - 1)))
else:
    print('\nYer imi yok: içindekiler sayfasını metinden oku (ilk ~15 sayfa).')

if len(args) < 4:
    sys.exit(0)

a, b = int(args[2]), int(args[3])
EQNUM = re.compile(r'\(\s*\d{1,2}\s*[.\-–]\s*\d{1,3}[a-z]?\s*\)\s*$')
MATHFONT = re.compile(r'(?i)math|cambria|cmmi|cmsy|cmex|symbol|mt ?extra|stix|times.*italic')
cands, n_eq, render = [], 0, set()
with open(os.path.join(work, 'metin.txt'), 'w', encoding='utf-8') as f:
    for i in range(a - 1, b):
        p = d[i]
        f.write('\n===== PDF sayfa %d\n' % (i + 1))
        f.write(p.get_text())
        for blk in p.get_text('dict')['blocks']:
            for ln in blk.get('lines', []):
                txt = ''.join(s['text'] for s in ln['spans']).strip()
                if len(txt) < 3:
                    continue
                if EQNUM.fullmatch(txt):        # numara ayrı satırda (ör. tablo hücresi): önceki formüle bağla
                    if cands and cands[-1].startswith('s.%-4d mat' % (i + 1)) and not EQNUM.search(cands[-1]):
                        cands[-1] = cands[-1].replace(' mat ', ' NO  ', 1) + '   ' + txt
                    else:                       # denklem metni okunamadı (özel kodlu matematik yazı tipi)
                        cands.append('s.%-4d NO  %s   [metin yok -> sayfayı render et]' % (i + 1, txt))
                        render.add(i + 1)
                    n_eq += 1
                    continue
                mathy = sum(len(s['text']) for s in ln['spans'] if MATHFONT.search(s['font']))
                has_num = bool(EQNUM.search(txt))
                if has_num or ('=' in txt and mathy >= 0.3 * len(txt)):
                    n_eq += has_num
                    cands.append('s.%-4d %s %s' % (i + 1, 'NO ' if has_num else 'mat', txt))

# Ofset kontrolü: sayfanın ilk/son satırlarında kitabın basılı sayfa numarası görünür.
for i in (a - 1, b - 1):
    lines = [l for l in d[i].get_text().splitlines() if l.strip()]
    print('PDF sayfa %d: baş=%r son=%r' % (i + 1, lines[:2], lines[-2:]))
with open(os.path.join(work, 'formul_adaylari.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(cands))
print('\n%d aday (%d tanesi numaralı) -> %s' % (len(cands), n_eq, os.path.join(work, 'formul_adaylari.txt')))
print('Metin -> %s' % os.path.join(work, 'metin.txt'))
if render:
    print('Denklem metni okunamayan sayfalar (review.py --pages ile render edip Read ile oku): %s'
          % ','.join(map(str, sorted(render))))
print('Not: adaylar yalnızca yol göstericidir; formüller metnin tamamı okunarak doğrulanır '
      '(kesir/kök içeren denklemler PDF metninde parçalı çıkar, gerekirse sayfayı render edip bak).')
