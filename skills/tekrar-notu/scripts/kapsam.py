"""Atlanan detay denetimi: kaynaktaki numaralı öğeler ve sayısal değerler tekrar notunda var mı?

python -W ignore kapsam.py <kaynak.pdf> <out.pdf> [--from SAYFA] [--to SAYFA]

Raporlar:
  1) Denklem numaraları  '(8.12)'         — notta numarasıyla geçmeli
  2) Tablo numaraları    'Tablo 8.3'      — notta tablo olarak (ya da adıyla) geçmeli
  3) Şekil numaraları    'Şekil 8.24'     — notta görsel ya da atıf olarak geçmeli
  4) Sayısal değerler    '0,5–2', '1100 °C', '%300' ... kaynakta olup notta hiç geçmeyenler, bağlamıyla
Eksik listesindeki HER satırı oku: gerçekten atlanmış bir bilgi ise nota ekle; yalnız ara hesap,
sayfa numarası, tekrar eden ifade ise bırak. Hedef: eksik listede bilgi taşıyan satır kalmaması.
Bu kural denklem numaraları için geçerli değildir: ara adım denklemi de yazılır, denetimi ortak/denklem_kapsam.py yapar.
"""
import sys, re, argparse
import pymupdf

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('out')
ap.add_argument('--from', dest='p0', type=int, default=1); ap.add_argument('--to', dest='p1', type=int, default=10 ** 6)
a = ap.parse_args()


def text(path, p0=1, p1=10 ** 6):
    d = pymupdf.open(path)
    pages = []
    for i, p in enumerate(d):
        if p0 <= i + 1 <= p1:
            t = p.get_text()
            t = '\n'.join(l for l in t.split('\n')[3:])   # sayfa üstü başlık satırlarını at
            pages.append((i + 1, t))
    return pages


def norm(s):
    return re.sub(r'\s+', ' ', s.replace('−', '−').replace('–', '-').replace('−', '-'))


src = text(a.src, a.p0, a.p1)
outt = norm(' '.join(t for _, t in text(a.out)))
outt_nospace = outt.replace(' ', '')
miss = 0


def report(title, items):
    global miss
    print('\n== %s: %d eksik' % (title, len(items)))
    for x in items: print('   ', x)
    miss += len(items)


allsrc = ' '.join(t for _, t in src)
eqs = sorted(set(re.findall(r'\((\d+\.\d+[a-z]?)\)', allsrc)), key=lambda s: [int(x) for x in re.findall(r'\d+', s)])
report('Denklem numaraları', [e for e in eqs if e not in outt and not re.search(
    r'\(\s*%s\s*[-–]|[-–]\s*%s\)' % (re.escape(e), re.escape(e.split('.')[-1])), outt)])
for kind in ('Tablo', 'Şekil'):
    nums = sorted(set(re.findall(kind + r'\s+(\d+\.\d+)', allsrc)), key=lambda s: [int(x) for x in s.split('.')])
    report(kind + ' numaraları', [n for n in nums if not re.search(kind + r'\s+' + re.escape(n) + r'(?!\d)', outt)])

# sayısal değerler: ondalık, aralık, yüzde, birimli sayı
num_re = re.compile(r'(%\s?\d+(?:[,\.]\d+)?|\d+(?:[,\.]\d+)?\s?[-–−]\s?\d+(?:[,\.]\d+)?|\d+[,\.]\d+|\d{2,}(?:\s\d{3})*)')
seen, items, calc = set(), [], []
for pg, t in src:
    for line in t.split('\n'):
        for m in num_re.finditer(line):
            v = norm(m.group(1)).strip()
            if v in seen: continue
            seen.add(v)
            vv = v.replace(' ', '')
            if vv in outt_nospace: continue
            if re.fullmatch(r'\d{2,3}', vv) and int(vv) < 400: continue      # sayfa/şekil no gürültüsü
            ls = line.strip()
            row = 's.%d  %-14s  …%s…' % (pg, v, ls[:90])
            if re.match(r'^\d+(\.\d+)+\s', ls) or re.search(r'(Soru|Tablo|Denklem|Problem|Şekil)\w*\s*[\d\.–\-, ]*' + re.escape(m.group(1)), ls):
                continue                                                  # bölüm/soru/tablo numarası
            (calc if ('=' in ls or '→' in ls) else items).append(row)
report('Notta geçmeyen sayısal değerler (bilgi — HER BİRİNE BAK)', items)
report('Notta geçmeyen ara hesap değerleri (çözüm adımları — sonuç notta varsa atlanabilir)', calc)
print('\nTOPLAM eksik aday:', miss)
