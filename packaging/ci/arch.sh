#!/usr/bin/env bash
set -euo pipefail
pacman -Syu --noconfirm --needed base-devel python python-gobject python-cairo gtk4 libadwaita fontconfig librsvg desktop-file-utils weston dbus
packaging/run_checks.sh
# makepkg must run without root; its build directory is isolated from checkout.
id -u builder >/dev/null 2>&1 || useradd -m builder
build_root="$(mktemp -d /tmp/uzeyir-doctor-build.XXXXXX)"
trap 'rm -rf "$build_root"' EXIT
cp -a . "$build_root/project"
chown -R builder:builder "$build_root"
runuser -u builder -- bash -euc 'cd "$1/project"; python3 packaging/build_arch.py --output dist' _ "$build_root"
mkdir -p dist
cp "$build_root/project/dist"/uzeyir-doctor-* dist/
pacman -U --noconfirm dist/uzeyir-doctor-*.pkg.tar.zst
desktop-file-validate /usr/share/applications/io.github.Tubix777.UzeyirDoctor.desktop
bash packaging/verify_installed.sh
