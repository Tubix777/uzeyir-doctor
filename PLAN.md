# Uzeyir Doctor publication plan

## First standalone release

- [x] Separate the diagnostic app from the three-module Uzeyir Control shell.
- [x] Give it an independent app ID, command, settings file and GitHub download page.
- [x] Keep Turkish/English, the monochrome design, bundled typography and reduced-motion-aware animations.
- [x] Prepare reproducible source, Debian-family, Fedora and Arch package workflows.
- [x] Complete standalone documentation and check source contents.
- [x] Build and install packages in supported Linux containers; open both native views.
- [x] Create `Tubix777/uzeyir-doctor`, publish its reviewed source and wait for green CI.
- [x] Publish `v0.1.0` with source, DEB, RPM, source RPM, Arch package/build recipe and checksums.
- [x] Download the public assets and verify checksums and source consistency.

## Completed release

`v0.1.0` is published at <https://github.com/Tubix777/uzeyir-doctor/releases/tag/v0.1.0>. The five Linux release jobs passed; each distro ran 74 tests and opened the installed diagnostics and downloads views. The seven public assets match GitHub's published digests and `SHA256SUMS`. All 65 files in the public source archive match this repository revision, and the Arch build bundle contains that same source archive with a pinned hash.

## Later releases

For each change, update the version, advance `source-date-epoch`, write release notes, build packages from one canonical source archive, verify the platform jobs, and attach the same source and packages to the GitHub release. Preserve the user's settings and existing Uzeyir Control installation.
