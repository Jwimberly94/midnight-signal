#!/bin/sh
set -eu

APP_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
VENV_DIR="$APP_DIR/.venv"
PYTHON="$VENV_DIR/bin/python"

if [ ! -x "$PYTHON" ]; then
    python3 -m venv "$VENV_DIR"
fi

if ! "$PYTHON" -c 'import PySide6.QtWebEngineWidgets, vlc' >/dev/null 2>&1; then
    "$PYTHON" -m pip install -r "$APP_DIR/requirements.txt"
fi

exec "$PYTHON" "$APP_DIR/midnightsignal.py" "$@"
