#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
ARTIFACT_DIR="${ROOT_DIR}/artifacts/installers"
BUILD_DIR="${ROOT_DIR}/build/packaging/linux"
PKG_ROOT="${BUILD_DIR}/tet4d"

cd "${ROOT_DIR}"
mkdir -p "${ARTIFACT_DIR}" "${BUILD_DIR}"

VERSION="$(${PYTHON_BIN} -c "from pathlib import Path; import tomllib; data = tomllib.loads(Path('pyproject.toml').read_text(encoding='utf-8')); print(data['project']['version'])")"
ARCH_LABEL="$(dpkg --print-architecture)"
ARTIFACT_PATH="${ARTIFACT_DIR}/tet4d_${VERSION}_${ARCH_LABEL}.deb"

"${PYTHON_BIN}" -m pip install --upgrade pip
"${PYTHON_BIN}" -m pip install -e . pyinstaller
"${PYTHON_BIN}" -m PyInstaller --noconfirm --clean packaging/pyinstaller/tet4d.spec

rm -rf "${PKG_ROOT}"
mkdir -p \
  "${PKG_ROOT}/DEBIAN" \
  "${PKG_ROOT}/opt/tet4d" \
  "${PKG_ROOT}/usr/bin" \
  "${PKG_ROOT}/usr/share/applications"

cp -R "${ROOT_DIR}/dist/tet4d/." "${PKG_ROOT}/opt/tet4d/"

cat > "${PKG_ROOT}/usr/bin/tet4d" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
exec /opt/tet4d/tet4d "$@"
EOF
chmod 755 "${PKG_ROOT}/usr/bin/tet4d"

cat > "${PKG_ROOT}/usr/share/applications/tet4d.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=tet4d
Comment=2D/3D/4D Tetris launcher
Exec=/usr/bin/tet4d
Terminal=false
Categories=Game;LogicGame;
EOF

cat > "${PKG_ROOT}/DEBIAN/control" <<EOF
Package: tet4d
Version: ${VERSION}
Section: games
Priority: optional
Architecture: ${ARCH_LABEL}
Maintainer: mousomer
Description: 2D/3D/4D Tetris launcher
EOF

rm -f "${ARTIFACT_PATH}"
dpkg-deb --build --root-owner-group "${PKG_ROOT}" "${ARTIFACT_PATH}"

echo "Created ${ARTIFACT_PATH}"
