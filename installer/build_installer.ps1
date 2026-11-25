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
    [Parameter(Mandatory = $true)][string]$InnoSetup,
    # Optional code signing. Pass either -CertificateThumbprint (certificate in
    # the Windows certificate store) or -Certificate/-CertificatePassword (PFX).
    [string]$SignTool = '',
    [string]$Certificate = '',
    [string]$CertificatePassword = '',
    [string]$CertificateThumbprint = '',
    [string]$TimestampUrl = 'http://timestamp.digicert.com'
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$build = Join-Path $repo 'build\FinalCif-zh'
$dist = Join-Path $repo 'dist'
$script:SignToolPath = $SignTool

function Invoke-CodeSign {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not $script:SignToolPath) {
        $candidates = Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin\*\x64\signtool.exe" `
            -ErrorAction SilentlyContinue | Sort-Object FullName -Descending
        if ($candidates) { $script:SignToolPath = $candidates[0].FullName }
    }
    if (-not $script:SignToolPath -or -not (Test-Path $script:SignToolPath)) {
        throw 'signtool.exe not found. Pass -SignTool <path>.'
    }
    $signArgs = @('sign', '/fd', 'SHA256', '/tr', $TimestampUrl, '/td', 'SHA256')
    if ($CertificateThumbprint) {
        $signArgs += @('/sha1', $CertificateThumbprint)
    } else {
        $signArgs += @('/f', $Certificate)
        if ($CertificatePassword) { $signArgs += @('/p', $CertificatePassword) }
    }
    $signArgs += $Path
    & $script:SignToolPath @signArgs
    if ($LASTEXITCODE -ne 0) { throw "signtool failed for $Path ($LASTEXITCODE)" }
    $sig = Get-AuthenticodeSignature $Path
    if ($sig.Status -ne 'Valid') { throw "Signature check failed for ${Path}: $($sig.Status)" }
    Write-Host "==> signed $Path"
}

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

Write-Host "==> removing obsolete localization files"
foreach ($leftover in @(
        'Lib\site-packages\sitecustomize.py',
        'Lib\site-packages\checkdef_zh.json',
        '中文版说明.txt',
        'check.def')) {
    $path = Join-Path $build $leftover
    if (Test-Path $path) { Remove-Item $path -Force }
}

Write-Host "==> checking PLATON check.def"
$checkdef = Join-Path $build 'finalcif\datafiles\check.def'
if (-not (Test-Path $checkdef)) {
    & (Join-Path $build 'python.exe') -I (Join-Path $repo 'scripts\fetch_checkdef.py') $checkdef
}

Write-Host "==> patching fastmolwidget labels"
& (Join-Path $build 'python.exe') -I (Join-Path $PSScriptRoot 'patch_fastmolwidget.py') `
    (Join-Path $build 'Lib\site-packages') (Join-Path $PSScriptRoot 'fastmolwidget_labels.json')

Write-Host "==> trimming unused components"
& (Join-Path $build 'python.exe') -I (Join-Path $PSScriptRoot 'trim_runtime.py') $build

Write-Host "==> adding documents"
Copy-Item (Join-Path $repo 'README.md') $build -Force
Copy-Item (Join-Path $repo 'README.en.md') $build -Force
Copy-Item (Join-Path $repo 'LICENSE') $build -Force
Copy-Item (Join-Path $repo 'THIRD_PARTY_NOTICES.md') $build -Force
Copy-Item (Join-Path $PSScriptRoot 'README-zh.txt') $build -Force

if ($Certificate -or $CertificateThumbprint) {
    Write-Host "==> signing application launcher"
    Invoke-CodeSign (Join-Path $build 'finalcif.exe')
}

Write-Host "==> compiling installer"
& (Join-Path $InnoSetup 'ISCC.exe') (Join-Path $PSScriptRoot 'finalcif-zh.iss')
if ($LASTEXITCODE -ne 0) { throw "ISCC failed ($LASTEXITCODE)" }

if ($Certificate -or $CertificateThumbprint) {
    Write-Host "==> signing installer"
    $setup = Get-ChildItem $dist -Filter '*.exe' |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    Invoke-CodeSign $setup.FullName
}

Write-Host "==> done: $dist"
Get-ChildItem $dist | Select-Object Name, Length
