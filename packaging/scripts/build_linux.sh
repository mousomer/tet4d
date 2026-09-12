#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# Packaging resolves its own interpreter and never consults the governed
# local resolver: that reads machine configuration, which a release must not
# depend on. System Python on PATH is not an approved packaging interpreter.
if [[ -z "${PYTHON_BIN:-}" ]]; then
  if [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
    PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
  else
  echo "packaging: no approved Python. Set PYTHON_BIN to an absolute interpreter" >&2
  echo "packaging: path, or create .venv. System Python on PATH is not approved." >&2
  exit 1
  fi
fi
ARTIFACT_DIR="${ROOT_DIR}/artifacts/installers"
BUILD_DIR="${ROOT_DIR}/build/packaging/linux"
PKG_ROOT="${BUILD_DIR}/tet4d"
SMOKE_XDG_DATA_HOME="${BUILD_DIR}/smoke-xdg"

cd "${ROOT_DIR}"
mkdir -p "${ARTIFACT_DIR}" "${BUILD_DIR}"

VERSION="$(${PYTHON_BIN} -c "from pathlib import Path; import tomllib; data = tomllib.loads(Path('pyproject.toml').read_text(encoding='utf-8')); print(data['project']['version'])")"
ARCH_LABEL="$(dpkg --print-architecture)"
ARTIFACT_PATH="${ARTIFACT_DIR}/tet4d_${VERSION}_${ARCH_LABEL}.deb"

"${PYTHON_BIN}" -m pip install --upgrade pip
"${PYTHON_BIN}" -m pip install -e . pyinstaller
"${PYTHON_BIN}" -m PyInstaller --noconfirm --clean packaging/pyinstaller/tet4d.spec

rm -rf "${SMOKE_XDG_DATA_HOME}"
mkdir -p "${SMOKE_XDG_DATA_HOME}"
env \
  XDG_DATA_HOME="${SMOKE_XDG_DATA_HOME}" \
  SDL_VIDEODRIVER=dummy \
  SDL_AUDIODRIVER=dummy \
  "${ROOT_DIR}/dist/tet4d/tet4d" --runtime-smoke-check

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
