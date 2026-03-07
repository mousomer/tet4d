$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$PythonBin = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { "python" }
$ArtifactDir = Join-Path $RootDir "artifacts\installers"
$BuildDir = Join-Path $RootDir "build\packaging\windows"
$WxsPath = Join-Path $BuildDir "tet4d.wxs"
$UpgradeCode = "{5B4CD54F-0F11-4D11-8A4E-A2E845E0C4D1}"
$WixToolDir = Join-Path $BuildDir ".dotnet-tools"

Set-Location $RootDir
New-Item -ItemType Directory -Path $ArtifactDir -Force | Out-Null
New-Item -ItemType Directory -Path $BuildDir -Force | Out-Null
New-Item -ItemType Directory -Path $WixToolDir -Force | Out-Null

if (-not $env:DOTNET_CLI_HOME) {
  $env:DOTNET_CLI_HOME = Join-Path $BuildDir ".dotnet-cli-home"
}
New-Item -ItemType Directory -Path $env:DOTNET_CLI_HOME -Force | Out-Null
$env:DOTNET_SKIP_FIRST_TIME_EXPERIENCE = "1"
$env:DOTNET_CLI_TELEMETRY_OPTOUT = "1"

$Version = & $PythonBin -c "from pathlib import Path; import tomllib; data = tomllib.loads(Path('pyproject.toml').read_text(encoding='utf-8')); print(data['project']['version'])"
if ($LASTEXITCODE -ne 0) {
  throw "Failed to read project version from pyproject.toml"
}

$WindowsVersion = & $PythonBin -c @"
from pathlib import Path
import tomllib

version = tomllib.loads(Path('pyproject.toml').read_text(encoding='utf-8'))['project']['version']
parts = [part for part in str(version).split('.') if part]
while len(parts) < 3:
    parts.append('0')
print('.'.join(parts[:3]))
"@
if ($LASTEXITCODE -ne 0) {
  throw "Failed to normalize Windows installer version"
}

if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
  throw "dotnet is required to build the WiX MSI installer"
}

$DotnetVersion = & dotnet --version
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($DotnetVersion)) {
  throw "Failed to determine installed dotnet SDK version"
}
$DotnetMajor = 0
if (-not [int]::TryParse(($DotnetVersion -split "\.")[0], [ref]$DotnetMajor)) {
  throw "Failed to parse dotnet SDK version '$DotnetVersion'"
}
if ($DotnetMajor -lt 6) {
  throw "WiX 6 requires .NET SDK 6 or newer; found '$DotnetVersion'. Install .NET 6+ or point PATH to a newer dotnet SDK."
}

& $PythonBin -m pip install --upgrade pip
& $PythonBin -m pip install -e . pyinstaller
& $PythonBin -m PyInstaller --noconfirm --clean packaging/pyinstaller/tet4d.spec

$env:PATH = "$WixToolDir;$env:PATH"
& dotnet tool update --tool-path $WixToolDir wix --version 6.*
if ($LASTEXITCODE -ne 0) {
  & dotnet tool install --tool-path $WixToolDir wix --version 6.*
}
if ($LASTEXITCODE -ne 0) {
  throw "Failed to install WiX toolset"
}

@"
<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs">
  <Package
    Name="tet4d"
    Manufacturer="mousomer"
    Version="$WindowsVersion"
    UpgradeCode="$UpgradeCode"
    Language="1033"
    Scope="perMachine">
    <MajorUpgrade DowngradeErrorMessage="A newer version of tet4d is already installed." />
    <StandardDirectory Id="ProgramFiles64Folder">
      <Directory Id="INSTALLFOLDER" Name="tet4d">
        <Files Include="!(bindpath.Payload)\**">
          <Exclude Files="!(bindpath.Payload)\**\*.pdb" />
        </Files>
      </Directory>
    </StandardDirectory>
  </Package>
</Wix>
"@ | Set-Content -Path $WxsPath -Encoding UTF8

$ArtifactPath = Join-Path $ArtifactDir "tet4d-$Version-windows-x64.msi"
if (Test-Path $ArtifactPath) {
  Remove-Item $ArtifactPath -Force
}

& wix build `
  -arch x64 `
  -bindpath "Payload=$(Join-Path $RootDir 'dist\tet4d')" `
  -out $ArtifactPath `
  $WxsPath

if ($LASTEXITCODE -ne 0) {
  throw "WiX build failed"
}

Write-Host "Created $ArtifactPath"