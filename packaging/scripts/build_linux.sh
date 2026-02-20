#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
ARTIFACT_DIR="${ROOT_DIR}/artifacts/installers"

cd "${ROOT_DIR}"
mkdir -p "${ARTIFACT_DIR}"

"${PYTHON_BIN}" -m pip install --upgrade pip
"${PYTHON_BIN}" -m pip install -r requirements.txt pyinstaller
"${PYTHON_BIN}" -m PyInstaller --noconfirm --clean packaging/pyinstaller/tet4d.spec

ARCHIVE_PATH="${ARTIFACT_DIR}/tet4d-linux.tar.gz"
tar -czf "${ARCHIVE_PATH}" -C dist tet4d

echo "Created ${ARCHIVE_PATH}"
