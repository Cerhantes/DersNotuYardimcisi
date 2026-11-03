"""ÖRNEK şema betiği — kaynaktan bağımsız, genel bir konu (ısı iletimi). Yalnızca üslubu ve dglib kullanımını gösterir:
- profil : ölçülü kesit + üzerinde sembollerle eğri (T_1, T_2, L, q) — semboller formüllerdekiyle aynı
- devre  : iki katmanlı duvar + eşdeğer ısıl devre (R_1, R_2, T_i)
- kalinlik: eğilim grafiği (Q ∝ 1/L) + üzerinde okunan iki nokta
Çalıştırma: PYTHONPATH=<skill>/scripts py -W ignore ornek_semalar.py <work>
"""
import sys
from dglib import *

init(sys.argv[1])


def profil():
    fig, ax = plt.subplots(figsize=(3.3, 2.5))
    ax.add_patch(Rectangle((1.0, 0.2), 1.6, 2.2, fc=FILL_GREY, ec='k', lw=0.9))
    ax.plot([1.0, 2.6], [2.1, 0.7], color=RED, lw=1.8)                       # doğrusal sıcaklık profili
    ax.text(0.92, 2.1, r'$T_1$', color=RED, fontsize=11, ha='right', va='center')
    ax.text(2.68, 0.7, r'$T_2$', color=RED, fontsize=11, ha='left', va='center')
    arrow(ax, (1.35, 0.5), (2.25, 0.5), c=NAVY, lw=1.4)               # etiket eğrinin dışında, boş bölgede
    ax.text(1.8, 0.6, r'$q$', color=NAVY, fontsize=11, ha='center', va='bottom')
    dim(ax, (1.0, 0.0), (2.6, 0.0), '', c=GRN); ax.text(1.8, -0.12, r'$L$', color=GRN, fontsize=11, ha='center', va='top')
    ax.text(0.45, 2.45, 'sıcak yüz', fontsize=7, ha='center'); ax.text(3.15, 2.45, 'soğuk yüz', fontsize=7, ha='center')
    arrow(ax, (1.8, 2.75), (2.4, 2.75), c=GREY, lw=0.9, ms=7); ax.text(2.48, 2.75, r'$x$', fontsize=10, va='center')
    ax.set_xlim(0, 3.6); ax.set_ylim(-0.45, 3.0); ax.set_aspect('equal'); ax.axis('off')
    save(fig, 'profil')


def devre():
    fig, ax = plt.subplots(figsize=(3.4, 2.6))
    ax.add_patch(Rectangle((0.6, 1.1), 1.0, 1.6, fc=FILL_ORANGE, ec='k', lw=0.9))   # katman 1 (ör. tuğla)
    ax.add_patch(Rectangle((1.6, 1.1), 0.5, 1.6, fc=FILL_BLUE, ec='k', lw=0.9))     # katman 2 (yalıtım)
    ax.plot([0.6, 1.6, 2.1], [2.5, 2.25, 1.3], color=RED, lw=1.6)                  # en büyük düşüş yalıtımda
    ax.text(0.52, 2.5, r'$T_1$', color=RED, fontsize=10, ha='right', va='center')
    ax.plot([1.6, 1.6], [2.25, 2.78], color=GREY, lw=0.5, ls=':')
    ax.text(1.6, 2.8, r'$T_i$', color=RED, fontsize=10, ha='center', va='bottom')
    ax.text(2.18, 1.3, r'$T_2$', color=RED, fontsize=10, ha='left', va='center')
    ax.text(1.1, 1.25, '1', fontsize=8, ha='center'); ax.text(1.85, 1.25, '2', fontsize=8, ha='center')
    # eşdeğer devre
    y = 0.45
    ax.plot([0.3, 0.75], [y, y], 'k', lw=0.9); ax.plot([1.45, 1.75], [y, y], 'k', lw=0.9); ax.plot([2.45, 2.9], [y, y], 'k', lw=0.9)
    zz = lambda x0, x1: ax.plot(np.linspace(x0, x1, 9), y + 0.09 * np.array([0, 1, -1, 1, -1, 1, -1, 1, 0]), 'k', lw=0.9)
    zz(0.75, 1.45); zz(1.75, 2.45)
    ax.text(1.1, y - 0.2, r'$R_1$', fontsize=10, ha='center', va='top'); ax.text(2.1, y - 0.2, r'$R_2$', fontsize=10, ha='center', va='top')
    for x, lab in [(0.3, r'$T_1$'), (1.6, r'$T_i$'), (2.9, r'$T_2$')]:
        ax.plot(x, y, 'o', color=RED, ms=3); ax.text(x, y + 0.16, lab, color=RED, fontsize=9, ha='center', va='bottom')
    arrow(ax, (2.95, y), (3.35, y), c=NAVY, lw=1.2, ms=8); ax.text(3.15, y + 0.1, r'$Q$', color=NAVY, fontsize=10, ha='center', va='bottom')
    ax.set_xlim(0, 3.5); ax.set_ylim(0.0, 3.1); ax.set_aspect('equal'); ax.axis('off')
    save(fig, 'devre')


def kalinlik():
    fig, ax = plt.subplots(figsize=(3.2, 2.2))
    L = np.linspace(0.05, 0.4, 100); Q = 0.7 * 10 * 20 / L
    ax.plot(L * 100, Q, color=NAVY, lw=1.8)
    for l in (0.1, 0.2):
        q = 0.7 * 10 * 20 / l
        ax.plot(l * 100, q, 'o', color=RED, ms=4)
        ax.text(l * 100 + 1.5, q + 120, f'{q:.0f} W', fontsize=7.5, va='bottom', color=RED)
    ax.text(26, 1500, r'$Q\propto 1/L$', fontsize=11)
    ax.set_xlabel('kalınlık L (cm)', fontsize=8); ax.set_ylabel('ısı kaybı Q (W)', fontsize=8)
    ax.tick_params(labelsize=7); clean_axes(ax)
    fig.tight_layout()
    save(fig, 'kalinlik')


if __name__ == '__main__':
    run(profil, devre, kalinlik)
