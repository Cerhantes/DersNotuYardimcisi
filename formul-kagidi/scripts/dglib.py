"""Formül kağıdı şemaları için matplotlib yardımcıları.

Şema betiği (<work>/semalar.py):
    import sys; from dglib import *
    init(sys.argv[1])                       # <work>; PNG'ler <work>/dg/ içine yazılır

    def kesit():
        fig, ax = plt.subplots(figsize=(3.4, 2.6))
        ...                                 # çiz; etiketler formüldeki sembollerin AYNISI olsun (r'$T_1$')
        ax.set_aspect('equal'); ax.axis('off')
        save(fig, 'kesit')                  # -> <work>/dg/kesit.png, içerik betiğinde fig='kesit'

    if __name__ == '__main__':
        run(kesit, ...)                     # ya da yalnızca bir tanesi: python semalar.py <work> kesit

Çalıştırma: PYTHONPATH=<skill>/scripts python -W ignore semalar.py <work> [şema_adı ...]
"""
import os, sys
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Arc, Circle, FancyArrowPatch, Rectangle, Ellipse, Wedge

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'mathtext.fontset': 'cm'})
BLUE, RED, GRN, ORG, NAVY, GREY = '#2E6DB4', '#C0504D', '#2E8B57', '#E08A00', '#1F3A5F', '#777777'
# Dolgu renkleri: katı/gövde, akışkan/1. katman, 2. malzeme/katman, açık bölge
FILL_GREY, FILL_ORANGE, FILL_BLUE, FILL_LILAC = '#D9D9D9', '#F6D7A7', '#A9C4E4', '#F2ECF7'

OUT = None


def init(work):
    global OUT
    OUT = os.path.join(work, 'dg'); os.makedirs(OUT, exist_ok=True)


def save(fig, name):
    assert OUT, 'önce init(<work>) çağır'
    fig.savefig(os.path.join(OUT, name + '.png'), dpi=300, bbox_inches='tight', pad_inches=0.04, facecolor='white')
    plt.close(fig)
    print('şema:', os.path.join(OUT, name + '.png'))


def run(*funcs):
    """Komut satırında ad verildiyse yalnızca o şemaları çizer (sys.argv[2:]).
    Sonunda çizilenleri tek kontrol görüntüsünde birleştirir: <work>/dg/_kontrol.png (Read ile aç)."""
    want = set(sys.argv[2:])
    done = []
    for f in funcs:
        if not want or f.__name__ in want:
            n0 = set(os.listdir(OUT)) if OUT else set()
            f()
            done += [os.path.join(OUT, p) for p in sorted(os.listdir(OUT)) if p.endswith('.png')
                     and not p.startswith('_') and (p not in n0 or p == f.__name__ + '.png')]
    done = list(dict.fromkeys(done))
    if done:
        from PIL import Image, ImageDraw
        ims = [Image.open(p).convert('RGB') for p in done]
        W = 1600; rows, row, x = [], [], 0
        for im in ims:
            sc = min(1.0, 760 / im.width); im = im.resize((int(im.width * sc), int(im.height * sc)))
            if row and x + im.width > W: rows.append(row); row, x = [], 0
            row.append(im); x += im.width + 20
        rows.append(row)
        H = sum(max(i.height for i in r) + 40 for r in rows)
        sheet = Image.new('RGB', (W, H), 'white'); dr = ImageDraw.Draw(sheet); y = 0; k = 0
        for r in rows:
            x = 0
            for im in r:
                sheet.paste(im, (x, y + 22)); dr.rectangle([x, y + 22, x + im.width, y + 22 + im.height], outline='#BBBBBB')
                dr.text((x + 2, y + 4), os.path.basename(done[k]), fill='black'); x += im.width + 20; k += 1
            y += max(i.height for i in r) + 40
        p = os.path.join(OUT, '_kontrol.png'); sheet.save(p)
        print('KONTROL: %s  <- derlemeden önce Read ile aç (çakışan/kesik etiket, formülden farklı sembol)' % p)


def arrow(ax, p, q, c='k', lw=1.4, ms=10, st='-|>', ls='-'):
    """p'den q'ya ok (kuvvet, hız vektörü)."""
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=st, mutation_scale=ms, color=c, lw=lw, linestyle=ls,
                                 shrinkA=0, shrinkB=0))


def dim(ax, p, q, txt, off=(0, 0), c=GREY, fs=9, **kw):
    """İki uçlu ölçü oku + ortasında etiket (off ile kaydır)."""
    arrow(ax, p, q, c=c, lw=0.9, ms=7, st='<|-|>')
    if txt:
        m = ((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1])
        ax.text(*m, txt, color=c, fontsize=fs, ha='center', va='center', **kw)


def angarc(ax, c, r, a0, a1, txt, tr=None, col=RED, fs=10):
    """c merkezli, a0–a1 derece arası açı yayı + etiket (tr: etiketin merkeze uzaklığı)."""
    ax.add_patch(Arc(c, 2 * r, 2 * r, theta1=min(a0, a1), theta2=max(a0, a1), color=col, lw=1.1))
    if txt:
        am = np.radians((a0 + a1) / 2); tr = tr or r * 1.35
        ax.text(c[0] + tr * np.cos(am), c[1] + tr * np.sin(am), txt, color=col, fontsize=fs, ha='center', va='center')


def clean_axes(ax, keep=('bottom', 'left')):
    """Grafiklerde gereksiz çerçeveyi kaldırır."""
    for s in ('top', 'right', 'bottom', 'left'):
        ax.spines[s].set_visible(s in keep)
