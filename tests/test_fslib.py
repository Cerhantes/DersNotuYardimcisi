"""fslib formül dizgisi: sınırsız integral işaretinin kuyruğu sonraki harfe binmez."""
import os, shutil, sys, tempfile, unittest

import numpy as np
from PIL import Image

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, 'skills', 'formul-kagidi', 'scripts'))
import fslib


class IntegralAraligi(unittest.TestCase):
    def test_sinirsiz_integrale_aralik_eklenir(self):
        self.assertEqual(fslib._tex_duzelt(r'\frac{1}{C}\int i\,dt'), r'\dfrac{1}{C}\int\;i\,dt')
        self.assertEqual(fslib._tex_duzelt(r'\oint E'), r'\oint\;E')
        self.assertEqual(fslib._tex_duzelt(r'\left[\int f\,dt\right]'), r'\left[\int\;f\,dt\right]')

    def test_sinirli_ya_da_elle_aralikli_integrale_dokunulmaz(self):
        for t in (r'\int_0^t x', r'\int _0 x', r'\int^{a} x', r'\int\, f', r'\int\!f', r'\int\quad f', r'\integral'):
            self.assertEqual(fslib._tex_duzelt(t), t)

    def _parca_sayisi(self, tex):
        """Formül görüntüsündeki birbirine değmeyen mürekkep parçalarının sayısı (8-komşuluk)."""
        a = np.array(Image.open(fslib.eq_img(tex)[0]).convert('RGBA'))[:, :, 3] > 40
        gor, n = np.zeros_like(a), 0
        for y, x in zip(*np.nonzero(a)):
            if gor[y, x]:
                continue
            n += 1
            yigin = [(y, x)]; gor[y, x] = True
            while yigin:
                cy, cx = yigin.pop()
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < a.shape[0] and 0 <= nx < a.shape[1] and a[ny, nx] and not gor[ny, nx]:
                            gor[ny, nx] = True; yigin.append((ny, nx))
        return n

    def test_integral_isareti_harfe_degmez(self):
        k = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, k)
        eski, fslib._EQD = fslib._EQD, k
        self.addCleanup(setattr, fslib, '_EQD', eski)
        # ∫ (1 parça) + i (gövde ve nokta: 2 parça) = 3; kuyruk harfe değerse parçalar birleşir
        self.assertEqual(self._parca_sayisi(r'\int i'), 3)

if __name__ == '__main__':
    unittest.main()
