# Prepares the skills' Python environment (Windows). Safe to re-run; returns at once when ready.
# Last line of output: PY=<path to the environment's python>. Leaves system Python alone, needs no admin rights.
# Everything lives in one folder: ~/.claude/ders-notu-yardimcisi (delete it to uninstall).
#   $env:DERS_NOTU_EV=<folder>  use another folder    $env:DERS_NOTU_UV=1  skip system Python, install with uv
# This file stays ASCII: Windows PowerShell 5.1 misreads UTF-8 without a BOM.
$ErrorActionPreference = 'Continue'

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$req = Join-Path $here 'requirements.txt'
$root = if ($env:DERS_NOTU_EV) { $env:DERS_NOTU_EV } else { Join-Path $HOME '.claude\ders-notu-yardimcisi' }
$envd = Join-Path $root 'env'
$stamp = Join-Path $envd '.istekler'
$vpy = Join-Path $envd 'Scripts\python.exe'
$test = 'import pymupdf, reportlab, matplotlib, PIL, numpy'

function Done { Write-Output ('PY=' + ($vpy -replace '\\', '/')); exit 0 }

function Ready {
    if (-not ((Test-Path $vpy) -and (Test-Path $stamp))) { return $false }
    if ((Get-FileHash $req).Hash -ne (Get-FileHash $stamp).Hash) { return $false }
    & $vpy -c $test *> $null
    return ($LASTEXITCODE -eq 0)
}

function Packages {
    Write-Host 'Paketler indiriliyor (ilk kurulumda 1-3 dakika)...'
    & $vpy -m pip install -q --disable-pip-version-check -r $req | Out-Host
    if ($LASTEXITCODE -ne 0) { return $false }
    & $vpy -c $test | Out-Host
    if ($LASTEXITCODE -ne 0) { return $false }
    Copy-Item $req $stamp
    return $true
}

function Clear-Env { if (Test-Path $envd) { Remove-Item -Recurse -Force $envd } }

function Find-Python {
    # The Microsoft Store 'python' shortcut fails this check, so it is skipped.
    $probe = 'import sys, venv, ensurepip; sys.exit(sys.version_info < (3, 10))'
    foreach ($c in @(@('py', '-3'), @('python'), @('python3'))) {
        if (-not (Get-Command $c[0] -ErrorAction SilentlyContinue)) { continue }
        $extra = @($c | Select-Object -Skip 1)
        & $c[0] @extra -c $probe *> $null
        if ($LASTEXITCODE -eq 0) { return , $c }
    }
    return $null
}

function Install-WithUv {
    $uvd = Join-Path $root 'uv'
    $uv = Join-Path $uvd 'uv.exe'
    if (-not (Test-Path $uv)) {
        Write-Host 'uv ile Python indiriliyor...'
        New-Item -ItemType Directory -Force $uvd | Out-Null
        $env:UV_UNMANAGED_INSTALL = $uvd
        # Child process: the official installer may call exit.
        & powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = 'Tls12'; irm https://astral.sh/uv/install.ps1 | iex" *> $null
        if (-not (Test-Path $uv)) { return $false }
    }
    $env:UV_PYTHON_INSTALL_DIR = Join-Path $root 'python'
    $env:UV_PYTHON_PREFERENCE = 'only-managed'
    & $uv venv --quiet --seed --python 3.12 $envd | Out-Host
    return ($LASTEXITCODE -eq 0)
}

if (Ready) { Done }

New-Item -ItemType Directory -Force $root | Out-Null

if ($env:DERS_NOTU_UV -ne '1') {
    $sp = Find-Python
    if ($sp) {
        Write-Host ('Python ortami kuruluyor: ' + ($sp -join ' '))
        Clear-Env
        $extra = @($sp | Select-Object -Skip 1)
        & $sp[0] @extra -m venv $envd
        if (($LASTEXITCODE -eq 0) -and (Packages)) { Done }
        Write-Host 'Sistem Python ile olmadi, uv deneniyor.'
    }
}

Clear-Env
if ((Install-WithUv) -and (Packages)) { Done }

[Console]::Error.WriteLine('KURULUM BASARISIZ: Internet baglantisini kontrol et; sorun surerse https://www.python.org/downloads/ adresinden Python kurup yeniden dene.')
exit 1
