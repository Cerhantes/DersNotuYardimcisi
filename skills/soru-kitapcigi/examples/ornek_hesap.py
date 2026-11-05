"""ÖRNEK hesap betiği: içerik betiğindeki sayısal sonuçlar buradan gelir (R('2.1', 'q') ile okunur).
Çalıştırma: PYTHONPATH=<skill>/scripts python -W ignore ornek_hesap.py <work>
"""
import sys
from hesaplib import Hesap

h = Hesap(sys.argv[1])

# 2.1: düzlem duvar, Fourier yasası
k, A, dT, L = 0.7, 10, 20, 0.2
h.kaydet('2.1', 'Q', k * A * dT / L, 'W', 0)

# 2.2: aynı duvar, kalınlık iki katı
h.kaydet('2.2', 'Q', k * A * dT / (2 * L), 'W', 0)

# 3.1: seri dirençler
R1, R2 = 0.2 / (0.7 * 10), 0.05 / (0.04 * 10)
h.kaydet('3.1', 'Rtop', R1 + R2, 'K/W', 3)
h.kaydet('3.1', 'Q', 20 / (R1 + R2), 'W', 0)
