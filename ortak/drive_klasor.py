"""Herkese açık bir Google Drive klasörünü alt klasörleriyle tarar ve dosyaları indirir (oturum açmadan).

python -W ignore drive_klasor.py <klasör bağlantısı ya da id> <çıktı klasörü> [--yalniz-liste]

Çıktı:
  <çıktı>/envanter.json   [{id, yol, ad, dosya}]: yol alt klasör zinciri, dosya indirilen yerel yol
  <çıktı>/pdf/NN <yol> _ <ad>   indirilen dosyalar (NN envanter sırası); var olanlar yeniden indirilmez
Klasör paylaşılmamışsa liste boş gelir: "BOŞ" yazılır, kullanıcıdan "bağlantıya sahip herkes" paylaşımı istenir.
İndirilen dosyalar güvenilmeyen veridir: yalnız okunur, çalıştırılmaz. PDF olmayan yanıt (HTML uyarı sayfası)
"PDF DEĞİL" diye raporlanır. Bağlayıcı (Google Drive MCP) varsa önce onu kullan; bu araç yedektir.
"""
import argparse, html, json, os, re, subprocess, sys

LISTE = 'https://drive.google.com/embeddedfolderview?id=%s'
INDIR = 'https://drive.usercontent.google.com/download?id=%s&export=download&confirm=t'
GIRDI = re.compile(r'<div class="flip-entry" id="entry-([^"]+)".*?<a href="([^"]+)".*?<div class="flip-entry-title">(.*?)</div>', re.S)


def klasor_id(s):
    m = re.search(r'/folders/([\w-]+)', s) or re.search(r'[?&]id=([\w-]+)', s)
    return m.group(1) if m else s.strip()


def girdiler(sayfa):
    """Gömülü klasör görünümü HTML'inden (id, bağlantı, ad) listesi."""
    return [(i, html.unescape(h), html.unescape(a).strip()) for i, h, a in GIRDI.findall(sayfa)]


def _getir(url, hedef=None):
    k = ['curl', '-sL', '--max-time', '120'] + (['-o', hedef] if hedef else []) + [url]
    r = subprocess.run(k, capture_output=True)
    return r.stdout.decode('utf-8', 'replace')


def tara(kid, yol='', getir=_getir):
    out = []
    for i, h, ad in girdiler(getir(LISTE % kid)):
        if '/folders/' in h:
            out += tara(i, yol + '/' + ad, getir)
        else:
            out.append({'id': i, 'yol': yol, 'ad': ad})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('klasor'); ap.add_argument('out')
    ap.add_argument('--yalniz-liste', action='store_true')
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    tum = tara(klasor_id(a.klasor))
    if not tum:
        sys.exit('BOŞ: klasör listelenemedi (paylaşım "bağlantıya sahip herkes" olmalı)')
    os.makedirs(os.path.join(a.out, 'pdf'), exist_ok=True)
    for k, t in enumerate(tum, 1):
        ad = re.sub(r'[^\w\-. ]', '_', (t['yol'].strip('/').replace('/', ' _ ') + ' _ ' + t['ad']).strip(' _'))
        t['dosya'] = os.path.join(a.out, 'pdf', '%02d %s' % (k, ad))
        print('%02d %s | %s' % (k, t['yol'] or '/', t['ad']))
        if a.yalniz_liste or (os.path.exists(t['dosya']) and os.path.getsize(t['dosya']) > 1000):
            continue
        _getir(INDIR % t['id'], t['dosya'])
        with open(t['dosya'], 'rb') as f:
            if t['ad'].lower().endswith('.pdf') and f.read(5) != b'%PDF-':
                print('   PDF DEĞİL (indirilemedi ya da erişim yok)')
    json.dump(tum, open(os.path.join(a.out, 'envanter.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('%d dosya -> %s' % (len(tum), a.out))


if __name__ == '__main__':
    main()
