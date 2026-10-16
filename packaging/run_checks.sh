#!/usr/bin/env bash
# A private Wayland session; does not use or control the user's desktop.
set -euo pipefail
project_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$project_root"
command -v weston >/dev/null
command -v dbus-run-session >/dev/null
test_runtime="$(mktemp -d)"
chmod 700 "$test_runtime"
trap 'rm -rf "$test_runtime"' EXIT
export XDG_RUNTIME_DIR="$test_runtime"
export GTK_A11Y=none GDK_BACKEND=wayland GSK_RENDERER=cairo
export WAYLAND_DISPLAY=uzeyir-doctor-test
export PYTHONPATH="$project_root/src"
dbus-run-session -- bash -euo pipefail -c '
  weston --backend=headless --renderer=pixman --socket="$WAYLAND_DISPLAY" --width=1600 --height=1800 --idle-time=0 --log="$XDG_RUNTIME_DIR/weston.log" &
  compositor_pid=$!
  trap '\''kill "$compositor_pid" 2>/dev/null || true; wait "$compositor_pid" 2>/dev/null || true'\'' EXIT
  for attempt in {1..100}; do
    if [ -S "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" ]; then break; fi
    if ! kill -0 "$compositor_pid" 2>/dev/null; then cat "$XDG_RUNTIME_DIR/weston.log"; exit 1; fi
    sleep 0.1
  done
  if [ ! -S "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" ]; then cat "$XDG_RUNTIME_DIR/weston.log"; exit 1; fi
  if (( $# )); then
    "$@"
  else
    python3 -W ignore::DeprecationWarning -m unittest discover -s tests -v
  fi
' checks "$@"
