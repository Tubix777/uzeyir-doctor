#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends python3 python3-gi python3-cairo python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 fontconfig librsvg2-common desktop-file-utils weston dbus-daemon dpkg-dev binutils
packaging/run_checks.sh
python3 packaging/build_deb.py --output dist
apt-get install -y --reinstall --no-install-recommends ./dist/uzeyir-doctor_*_all.deb
desktop-file-validate /usr/share/applications/io.github.Tubix777.UzeyirDoctor.desktop
bash packaging/verify_installed.sh
