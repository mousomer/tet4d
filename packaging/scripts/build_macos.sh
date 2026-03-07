#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
ARTIFACT_DIR="${ROOT_DIR}/artifacts/installers"
BUILD_DIR="${ROOT_DIR}/build/packaging/macos"

cd "${ROOT_DIR}"
mkdir -p "${ARTIFACT_DIR}" "${BUILD_DIR}"

VERSION="$(${PYTHON_BIN} -c "from pathlib import Path; import tomllib; data = tomllib.loads(Path('pyproject.toml').read_text(encoding='utf-8')); print(data['project']['version'])")"
ARCH_RAW="$(uname -m)"
case "${ARCH_RAW}" in
  arm64|aarch64)
    ARCH_LABEL="arm64"
    ;;
  x86_64)
    ARCH_LABEL="x64"
    ;;
  *)
    ARCH_LABEL="${ARCH_RAW}"
    ;;
esac

APP_DIR="${BUILD_DIR}/tet4d.app"
PAYLOAD_DIR="${APP_DIR}/Contents/Resources/tet4d-runtime"
MACOS_DIR="${APP_DIR}/Contents/MacOS"
DMG_STAGE_DIR="${BUILD_DIR}/dmg-root"
DMG_PATH="${ARTIFACT_DIR}/tet4d-${VERSION}-macos-${ARCH_LABEL}.dmg"

"${PYTHON_BIN}" -m pip install --upgrade pip
"${PYTHON_BIN}" -m pip install -e . pyinstaller
"${PYTHON_BIN}" -m PyInstaller --noconfirm --clean packaging/pyinstaller/tet4d.spec

rm -rf "${APP_DIR}" "${DMG_STAGE_DIR}"
mkdir -p "${PAYLOAD_DIR}" "${MACOS_DIR}" "${DMG_STAGE_DIR}"
cp -R "${ROOT_DIR}/dist/tet4d/." "${PAYLOAD_DIR}/"

cat > "${MACOS_DIR}/tet4d" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../Resources/tet4d-runtime" && pwd)"
exec "${APP_ROOT}/tet4d" "$@"
EOF
chmod +x "${MACOS_DIR}/tet4d"

cat > "${APP_DIR}/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleDisplayName</key>
    <string>tet4d</string>
    <key>CFBundleExecutable</key>
    <string>tet4d</string>
    <key>CFBundleIdentifier</key>
    <string>io.github.mousomer.tet4d</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>tet4d</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>${VERSION}</string>
    <key>CFBundleVersion</key>
    <string>${VERSION}</string>
    <key>LSMinimumSystemVersion</key>
    <string>13.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
  </dict>
</plist>
EOF

cp -R "${APP_DIR}" "${DMG_STAGE_DIR}/"
ln -s /Applications "${DMG_STAGE_DIR}/Applications"

rm -f "${DMG_PATH}"
hdiutil create \
  -volname "tet4d" \
  -srcfolder "${DMG_STAGE_DIR}" \
  -ov \
  -format UDZO \
  "${DMG_PATH}"

echo "Created ${DMG_PATH}"
