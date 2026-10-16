# Uzeyir Doctor publication plan

## First standalone release

- [x] Separate the diagnostic app from the three-module Uzeyir Control shell.
- [x] Give it an independent app ID, command, settings file and GitHub download page.
- [x] Keep Turkish/English, the monochrome design, bundled typography and reduced-motion-aware animations.
- [x] Prepare reproducible source, Debian-family, Fedora and Arch package workflows.
- [x] Complete standalone documentation and check source contents.
- [x] Build and install packages in supported Linux containers; open both native views.
- [x] Create `Tubix777/uzeyir-doctor`, publish its reviewed source and wait for green CI.
- [ ] Publish `v0.1.0` with source, DEB, RPM, source RPM, Arch package/build recipe and checksums.
- [ ] Download the public assets and verify checksums and source consistency.

## Later releases

For each change, update the version, advance `source-date-epoch`, write release notes, build packages from one canonical source archive, verify the platform jobs, and attach the same source and packages to the GitHub release. Preserve the user's settings and existing Uzeyir Control installation.
