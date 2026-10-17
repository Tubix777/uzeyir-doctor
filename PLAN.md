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

## 0.2.0 — smooth navigation and reliable feedback

- [x] Inspect the existing page transitions and diagnostic feedback.
- [x] Add short interruptible transitions and a shared navigation indicator.
- [x] Preserve expanded evidence; show accurate failure and copy feedback.
- [x] Verify fast navigation, focus, resize, language, reduced motion and close behavior.
- [x] Validate both installed views and packages in all five distro containers.
- [x] Publish and verify the source, distro assets and checksums on GitHub.

## In-app updates — added before publication

- [x] Check newer releases only in this app's official repository; select the OS package.
- [x] Add release notes, optional startup checks and a new-release notification.
- [x] Download asynchronously with actual byte progress, cancellation and retry.
- [x] Verify size, GitHub asset SHA-256 and SHA256SUMS before installation.
- [x] Use the existing PackageKit service with explicit user action and system authorization;
  fall back clearly to the distro's native package installer when unavailable.
- [x] Verify the installed version before restart; preserve the working app on failure.
- [x] Test tampered packages, offline state, stale results, cancellation and close.
- [x] Revalidate packages and publish detailed updated documentation and releases.

## 0.2.0 publication complete — 18 October 2026

[v0.2.0](https://github.com/Tubix777/uzeyir-doctor/releases/tag/v0.2.0) is published.
All five distro jobs and the release job passed. The 111-test suite and installed
diagnostics/download/update views passed; Fedora/Arch skip only the dpkg-deb tool test.
All seven public assets match their GitHub size/digest and SHA256SUMS. All 81 files
in the canonical source match the tagged revision; Arch and source RPM embed the
same archive. The live updater selected, downloaded and verified DEB/RPM/Arch
packages while comparing against 0.1.0. Real system authorization was not exercised.

[Release verification](docs/release-verification.json) records the tagged release;
this completion record was added after the tag.
