$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$PythonBin = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { "python" }
$ArtifactDir = Join-Path $RootDir "artifacts\installers"
$BuildDir = Join-Path $RootDir "build\packaging\windows"
$TempOutputDir = Join-Path $BuildDir "out"
$SmokeAppData = Join-Path $BuildDir "AppData\Roaming"
$WxsPath = Join-Path $BuildDir "tet4d.wxs"
$UpgradeCode = "{5B4CD54F-0F11-4D11-8A4E-A2E845E0C4D1}"
$WixToolDir = Join-Path $BuildDir ".dotnet-tools"
$WixVersion = "6.0.2"
$WixUiExtensionPackage = "WixToolset.UI.wixext/$WixVersion"

function Escape-WixXml {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Value
  )

  return [System.Security.SecurityElement]::Escape($Value)
}

function New-WixId {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Prefix,
    [Parameter(Mandatory = $true)]
    [string]$Value
  )

  $normalized = [regex]::Replace($Value, "[^A-Za-z0-9_]", "_")
  if ([string]::IsNullOrWhiteSpace($normalized)) {
    $normalized = "item"
  }
  if ($normalized[0] -match "[0-9]") {
    $normalized = "_$normalized"
  }
  if ($normalized.Length -gt 40) {
    $normalized = $normalized.Substring(0, 40)
  }
  $hashBytes = [System.Security.Cryptography.SHA1]::HashData(
    [System.Text.Encoding]::UTF8.GetBytes("$Prefix|$Value")
  )
  $hash = [System.BitConverter]::ToString($hashBytes).Replace("-", "").Substring(0, 10)
  return "${Prefix}${normalized}${hash}"
}

function Remove-PackagingArtifacts {
  param(
    [Parameter(Mandatory = $true)]
    [string[]]$Paths
  )

  foreach ($TargetPath in $Paths) {
    if (-not (Test-Path $TargetPath)) {
      continue
    }
    Get-ChildItem -Path $TargetPath -Filter *.msi -File -Recurse -ErrorAction SilentlyContinue |
      Remove-Item -Force -ErrorAction Stop
    Get-ChildItem -Path $TargetPath -Filter *.cab -File -Recurse -ErrorAction SilentlyContinue |
      Remove-Item -Force -ErrorAction Stop
  }
}

Set-Location $RootDir
New-Item -ItemType Directory -Path $ArtifactDir -Force | Out-Null
New-Item -ItemType Directory -Path $BuildDir -Force | Out-Null
New-Item -ItemType Directory -Path $WixToolDir -Force | Out-Null
Remove-PackagingArtifacts -Paths @($ArtifactDir, $BuildDir)
if (Test-Path $TempOutputDir) {
  Remove-Item $TempOutputDir -Recurse -Force
}
if (Test-Path $SmokeAppData) {
  Remove-Item $SmokeAppData -Recurse -Force
}
New-Item -ItemType Directory -Path $TempOutputDir -Force | Out-Null
New-Item -ItemType Directory -Path $SmokeAppData -Force | Out-Null

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
& dotnet tool update --tool-path $WixToolDir wix --version $WixVersion
if ($LASTEXITCODE -ne 0) {
  & dotnet tool install --tool-path $WixToolDir wix --version $WixVersion
}
if ($LASTEXITCODE -ne 0) {
  throw "Failed to install WiX toolset"
}

& wix extension add -g $WixUiExtensionPackage
if ($LASTEXITCODE -ne 0) {
  throw "Failed to add WixToolset.UI.wixext extension"
}

$PayloadRoot = Join-Path $RootDir "dist\tet4d"
if (-not (Test-Path $PayloadRoot)) {
  throw "PyInstaller did not create expected payload directory: $PayloadRoot"
}

$env:APPDATA = $SmokeAppData
$env:SDL_VIDEODRIVER = "dummy"
$env:SDL_AUDIODRIVER = "dummy"
& (Join-Path $PayloadRoot "tet4d.exe") --runtime-smoke-check
if ($LASTEXITCODE -ne 0) {
  throw "Packaged runtime smoke check failed for $PayloadRoot\tet4d.exe"
}

$payloadFiles = Get-ChildItem -Path $PayloadRoot -Recurse -File |
  Where-Object { $_.Extension -ne ".pdb" } |
  Sort-Object FullName
if (-not $payloadFiles) {
  throw "No payload files found under $PayloadRoot"
}

$directoryIds = @{ "." = "INSTALLFOLDER" }
foreach ($file in $payloadFiles) {
  $relativePath = [System.IO.Path]::GetRelativePath($PayloadRoot, $file.FullName).Replace("/", "\")
  $relativeDir = [System.IO.Path]::GetDirectoryName($relativePath)
  while (-not [string]::IsNullOrWhiteSpace($relativeDir)) {
    if (-not $directoryIds.ContainsKey($relativeDir)) {
      $directoryIds[$relativeDir] = New-WixId "Dir" $relativeDir
    }
    $relativeDir = [System.IO.Path]::GetDirectoryName($relativeDir)
  }
}

$childDirectories = @{}
foreach ($relativeDir in ($directoryIds.Keys | Where-Object { $_ -ne "." })) {
  $parentDir = [System.IO.Path]::GetDirectoryName($relativeDir)
  if ([string]::IsNullOrWhiteSpace($parentDir)) {
    $parentDir = "."
  }
  if (-not $childDirectories.ContainsKey($parentDir)) {
    $childDirectories[$parentDir] = New-Object System.Collections.Generic.List[string]
  }
  $childDirectories[$parentDir].Add($relativeDir)
}

$directoryTreeBuilder = New-Object System.Text.StringBuilder
function Add-WixDirectoryTree {
  param(
    [string]$ParentDir,
    [int]$IndentLevel
  )

  if (-not $childDirectories.ContainsKey($ParentDir)) {
    return
  }

  foreach ($childDir in ($childDirectories[$ParentDir] | Sort-Object)) {
    $leafName = Split-Path -Path $childDir -Leaf
    $indent = ("  " * $IndentLevel)
    [void]$directoryTreeBuilder.AppendLine(
      "$indent<Directory Id=`"$($directoryIds[$childDir])`" Name=`"$(Escape-WixXml $leafName)`">"
    )
    Add-WixDirectoryTree -ParentDir $childDir -IndentLevel ($IndentLevel + 1)
    [void]$directoryTreeBuilder.AppendLine("$indent</Directory>")
  }
}
Add-WixDirectoryTree -ParentDir "." -IndentLevel 3

$componentsByDirectory = @{}
$componentRefs = New-Object System.Collections.Generic.List[string]
foreach ($file in $payloadFiles) {
  $relativePath = [System.IO.Path]::GetRelativePath($PayloadRoot, $file.FullName).Replace("/", "\")
  $relativeDir = [System.IO.Path]::GetDirectoryName($relativePath)
  if ([string]::IsNullOrWhiteSpace($relativeDir)) {
    $relativeDir = "."
  }
  $componentId = New-WixId "Cmp" $relativePath
  $fileId = New-WixId "Fil" $relativePath
  $sourcePath = "!(bindpath.Payload)\$relativePath"
  if (-not $componentsByDirectory.ContainsKey($relativeDir)) {
    $componentsByDirectory[$relativeDir] = New-Object System.Collections.Generic.List[string]
  }
  $componentsByDirectory[$relativeDir].Add(@"
      <Component Id="$componentId" Guid="*">
        <File Id="$fileId" Source="$(Escape-WixXml $sourcePath)" KeyPath="yes" />
      </Component>
"@.TrimEnd())
  $componentRefs.Add($componentId)
}

$payloadDirectoryRefs = New-Object System.Text.StringBuilder
foreach ($relativeDir in ($componentsByDirectory.Keys | Sort-Object)) {
  [void]$payloadDirectoryRefs.AppendLine("    <DirectoryRef Id=`"$($directoryIds[$relativeDir])`">")
  foreach ($componentXml in $componentsByDirectory[$relativeDir]) {
    [void]$payloadDirectoryRefs.AppendLine($componentXml)
  }
  [void]$payloadDirectoryRefs.AppendLine("    </DirectoryRef>")
}

$payloadComponentGroup = New-Object System.Text.StringBuilder
[void]$payloadComponentGroup.AppendLine("    <ComponentGroup Id=`"PayloadFiles`">")
foreach ($componentId in $componentRefs) {
  [void]$payloadComponentGroup.AppendLine("      <ComponentRef Id=`"$componentId`" />")
}
[void]$payloadComponentGroup.AppendLine("    </ComponentGroup>")

$wxsContent = @"
<?xml version="1.0" encoding="UTF-8"?>
<Wix
  xmlns="http://wixtoolset.org/schemas/v4/wxs"
  xmlns:ui="http://wixtoolset.org/schemas/v4/wxs/ui">
  <Package
    Name="tet4d"
    Manufacturer="mousomer"
    Version="$WindowsVersion"
    UpgradeCode="$UpgradeCode"
    Language="1033"
    Scope="perMachine">
    <MajorUpgrade DowngradeErrorMessage="A newer version of tet4d is already installed." />
    <MediaTemplate EmbedCab="yes" />
    <ui:WixUI Id="WixUI_InstallDir" InstallDirectory="INSTALLFOLDER" />
    <Feature Id="MainFeature" Title="tet4d" Level="1">
      <ComponentGroupRef Id="PayloadFiles" />
      <ComponentRef Id="StartMenuShortcutComponent" />
      <ComponentRef Id="DesktopShortcutComponent" />
    </Feature>
  </Package>
  <Fragment>
    <StandardDirectory Id="ProgramFiles64Folder">
      <Directory Id="INSTALLFOLDER" Name="tet4d">
$($directoryTreeBuilder.ToString().TrimEnd())
      </Directory>
    </StandardDirectory>
    <StandardDirectory Id="ProgramMenuFolder">
      <Directory Id="ProgramMenuTet4dFolder" Name="tet4d" />
    </StandardDirectory>
    <StandardDirectory Id="DesktopFolder" />
  </Fragment>
  <Fragment>
$($payloadDirectoryRefs.ToString().TrimEnd())
    <DirectoryRef Id="ProgramMenuTet4dFolder">
      <Component Id="StartMenuShortcutComponent" Guid="*">
        <Shortcut
          Id="StartMenuTet4dShortcut"
          Name="tet4d"
          Target="[INSTALLFOLDER]tet4d.exe"
          WorkingDirectory="INSTALLFOLDER" />
        <RemoveFolder Id="RemoveProgramMenuTet4dFolder" On="uninstall" />
        <RegistryValue
          Root="HKLM"
          Key="Software\mousomer\tet4d"
          Name="StartMenuShortcutInstalled"
          Type="integer"
          Value="1"
          KeyPath="yes" />
      </Component>
    </DirectoryRef>
    <DirectoryRef Id="DesktopFolder">
      <Component Id="DesktopShortcutComponent" Guid="*">
        <Shortcut
          Id="DesktopTet4dShortcut"
          Name="tet4d"
          Target="[INSTALLFOLDER]tet4d.exe"
          WorkingDirectory="INSTALLFOLDER" />
        <RegistryValue
          Root="HKLM"
          Key="Software\mousomer\tet4d"
          Name="DesktopShortcutInstalled"
          Type="integer"
          Value="1"
          KeyPath="yes" />
      </Component>
    </DirectoryRef>
$($payloadComponentGroup.ToString().TrimEnd())
  </Fragment>
</Wix>
"@
$wxsContent | Set-Content -Path $WxsPath -Encoding UTF8

$ArtifactPath = Join-Path $ArtifactDir "tet4d-$Version-windows-x64.msi"
$TempArtifactPath = Join-Path $TempOutputDir "tet4d-$Version-windows-x64.msi"

& wix build `
  -arch x64 `
  -ext WixToolset.UI.wixext `
  -bindpath "Payload=$(Join-Path $RootDir 'dist\tet4d')" `
  -out $TempArtifactPath `
  $WxsPath

if ($LASTEXITCODE -ne 0) {
  throw "WiX build failed"
}

if (-not (Test-Path $TempArtifactPath)) {
  throw "WiX build completed without creating expected MSI: $TempArtifactPath"
}

$ExternalCabFiles = Get-ChildItem -Path $BuildDir -Filter *.cab -File -Recurse -ErrorAction SilentlyContinue
if ($ExternalCabFiles) {
  $CabList = ($ExternalCabFiles | ForEach-Object { $_.FullName }) -join [Environment]::NewLine
  throw "Windows packaging must produce a single self-contained MSI. Unexpected external CAB output detected:`n$CabList"
}

Move-Item -Path $TempArtifactPath -Destination $ArtifactPath -Force

$ArtifactCabFiles = Get-ChildItem -Path $ArtifactDir -Filter *.cab -File -Recurse -ErrorAction SilentlyContinue
if ($ArtifactCabFiles) {
  $CabList = ($ArtifactCabFiles | ForEach-Object { $_.FullName }) -join [Environment]::NewLine
  throw "Installer artifact directory must not contain CAB sidecars:`n$CabList"
}

Write-Host "Created $ArtifactPath"
