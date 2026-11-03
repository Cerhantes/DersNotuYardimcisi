#!/usr/bin/env bash
# Skill'lerin Python ortamını hazırlar (Mac/Linux). Tekrar çalıştırmak güvenlidir; ortam hazırsa hemen biter.
# Son satır: PY=<ortamın python yolu>. Sistem Python'una dokunmaz, yönetici hakkı istemez.
# Her şey tek klasörde durur: ~/.claude/ders-notu-yardimcisi (kaldırmak için silmek yeter).
#   DERS_NOTU_EV=<klasör>  başka klasör kullan    DERS_NOTU_UV=1  sistem Python'unu atla, uv ile kur
set -u

HERE=$(cd "$(dirname "$0")" && pwd)
REQ="$HERE/requirements.txt"
ROOT="${DERS_NOTU_EV:-$HOME/.claude/ders-notu-yardimcisi}"
ENVD="$ROOT/env"
STAMP="$ENVD/.istekler"
TEST='import pymupdf, reportlab, matplotlib, PIL, numpy'

vpy() { if [ -x "$ENVD/Scripts/python.exe" ]; then echo "$ENVD/Scripts/python.exe"; else echo "$ENVD/bin/python"; fi; }
hazir() { [ -x "$(vpy)" ] && cmp -s "$REQ" "$STAMP" && "$(vpy)" -c "$TEST" >/dev/null 2>&1; }
paketler() {
    echo "Paketler indiriliyor (ilk kurulumda 1-3 dakika)..."
    "$(vpy)" -m pip install -q --disable-pip-version-check -r "$REQ" &&
        "$(vpy)" -c "$TEST" && cp "$REQ" "$STAMP"
}

sistem_python() {
    for c in python3 python3.13 python3.12 python3.11 python3.10 python py; do
        p=$(command -v "$c" 2>/dev/null) || continue
        # Mac: /usr/bin/python3 Xcode araçları yokken çalıştırılınca kurulum penceresi açar
        if [ "$p" = /usr/bin/python3 ] && [ "$(uname)" = Darwin ] && ! xcode-select -p >/dev/null 2>&1; then continue; fi
        if "$p" -c 'import sys, venv, ensurepip; sys.exit(sys.version_info < (3, 10))' >/dev/null 2>&1; then
            echo "$p"; return 0
        fi
    done
    return 1
}

uv_ile_kur() {
    UVD="$ROOT/uv"
    if [ ! -x "$UVD/uv" ]; then
        echo "uv ile Python indiriliyor..."
        mkdir -p "$UVD"
        if command -v curl >/dev/null 2>&1; then curl -LsSf https://astral.sh/uv/install.sh
        else wget -qO- https://astral.sh/uv/install.sh; fi | env UV_UNMANAGED_INSTALL="$UVD" sh >/dev/null || return 1
    fi
    UV_PYTHON_INSTALL_DIR="$ROOT/python" UV_PYTHON_PREFERENCE=only-managed \
        "$UVD/uv" venv --quiet --seed --python 3.12 "$ENVD"
}

if hazir; then echo "PY=$(vpy)"; exit 0; fi

mkdir -p "$ROOT"
if [ "${DERS_NOTU_UV:-}" != 1 ] && SP=$(sistem_python); then
    echo "Python ortamı kuruluyor: $SP"
    rm -rf "$ENVD"
    if "$SP" -m venv "$ENVD" && paketler; then echo "PY=$(vpy)"; exit 0; fi
    echo "Sistem Python'u ile olmadı, uv deneniyor."
fi

rm -rf "$ENVD"
if uv_ile_kur && paketler; then echo "PY=$(vpy)"; exit 0; fi

echo "KURULUM BAŞARISIZ: İnternet bağlantısını kontrol et; sorun sürerse https://www.python.org/downloads/ adresinden Python kurup yeniden dene." >&2
exit 1
