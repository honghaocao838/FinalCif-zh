# Build the Windows installer for the Chinese FinalCif edition.
#
# 1. copies a pristine FinalCif installation (Python runtime + dependencies)
# 2. replaces the finalcif package with this repository's localized source
# 3. bundles check.def, patches the fastmolwidget labels, adds the notices
# 4. compiles installer\finalcif-zh.iss with Inno Setup
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1 `
#       -FinalCifInstall "C:\Program Files\FinalCif" `
#       -InnoSetup "C:\Program Files (x86)\Inno Setup 6"

param(
    [Parameter(Mandatory = $true)][string]$FinalCifInstall,
    [Parameter(Mandatory = $true)][string]$InnoSetup
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$build = Join-Path $repo 'build\FinalCif-zh'
$dist = Join-Path $repo 'dist'

if (-not (Test-Path (Join-Path $FinalCifInstall 'finalcif'))) {
    throw "Not a FinalCif installation: $FinalCifInstall"
}
if (-not (Test-Path (Join-Path $FinalCifInstall 'python.exe'))) {
    throw "python.exe not found in $FinalCifInstall"
}

Write-Host "==> staging runtime to $build"
New-Item -ItemType Directory -Force -Path $build | Out-Null
robocopy $FinalCifInstall $build /MIR /XF unins000.exe unins000.dat unins000.msg `
    /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed ($LASTEXITCODE)" }

Write-Host "==> replacing finalcif package with localized source"
Remove-Item (Join-Path $build 'finalcif') -Recurse -Force
robocopy (Join-Path $repo 'finalcif') (Join-Path $build 'finalcif') /E /XD __pycache__ `
    /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed ($LASTEXITCODE)" }
Get-ChildItem (Join-Path $build 'finalcif') -Recurse -Directory -Filter __pycache__ |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "==> checking PLATON check.def"
$checkdef = Join-Path $build 'finalcif\datafiles\check.def'
if (-not (Test-Path $checkdef)) {
    & (Join-Path $build 'python.exe') -I (Join-Path $repo 'scripts\fetch_checkdef.py') $checkdef
}

Write-Host "==> patching fastmolwidget labels"
& (Join-Path $build 'python.exe') -I (Join-Path $PSScriptRoot 'patch_fastmolwidget.py') `
    (Join-Path $build 'Lib\site-packages') (Join-Path $repo 'localization\translations\70-viewer.json')

Write-Host "==> adding documents"
Copy-Item (Join-Path $repo 'README.md') $build -Force
Copy-Item (Join-Path $repo 'LICENSE.md') $build -Force
Copy-Item (Join-Path $repo 'THIRD_PARTY_NOTICES.md') $build -Force
@"
FinalCIF 中文版（v180）
=====================

H.C 汉化，联系 honghaocao838@gmail.com，汉化自 FinalCif v180（Daniel Kratzert）。

启动：桌面「FinalCIF 中文版」，或运行本目录 finalcif.exe。
支持拖放 .cif、.res、.hkl 文件。

CheckCIF 的 PLAT 警报可点击查看解释，常用条目附中文，其余为官方英文原文。
保存的 CIF 内容与报告正文保持英文。
"@ | Set-Content -Path (Join-Path $build '中文版说明.txt') -Encoding UTF8

Write-Host "==> compiling installer"
& (Join-Path $InnoSetup 'ISCC.exe') (Join-Path $PSScriptRoot 'finalcif-zh.iss')
if ($LASTEXITCODE -ne 0) { throw "ISCC failed ($LASTEXITCODE)" }

Write-Host "==> done: $dist"
Get-ChildItem $dist | Select-Object Name, Length
