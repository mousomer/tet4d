$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$PythonBin = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { "python" }
$ArtifactDir = Join-Path $RootDir "artifacts\installers"

Set-Location $RootDir
New-Item -ItemType Directory -Path $ArtifactDir -Force | Out-Null

& $PythonBin -m pip install --upgrade pip
& $PythonBin -m pip install -r requirements.txt pyinstaller
& $PythonBin -m PyInstaller --noconfirm --clean packaging/pyinstaller/tet4d.spec

$ArchivePath = Join-Path $ArtifactDir "tet4d-windows.zip"
if (Test-Path $ArchivePath) {
  Remove-Item $ArchivePath -Force
}
Compress-Archive -Path (Join-Path $RootDir "dist\tet4d\*") -DestinationPath $ArchivePath

Write-Host "Created $ArchivePath"
