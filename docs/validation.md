# Validation

## 0.3.0 Graphite validation — 24 October 2026

The 111-test native suite passes in a private Fedora 44 KWin/Wayland
session (only the dpkg-deb tool test is skipped on this host). The production
stylesheet parses without warnings. Native Pango reports the bundled Inter
family; the upstream font and complete OFL notice are in the release source.

All pages were rendered in Turkish and English at 960 × 620 and 1320 × 900.
This includes module downloads, keyboard focus, the update dialog and compact
Flatpak controls. Public images and the finite navigation recording are taken
from real GTK widgets using explicit synthetic fixtures, with a demo wheel and
no local logs, private profiles or device serials. The GIF is a scaled recording;
the application itself uses GTK's frame clock and the desktop renderer.

Motion tests cover pixel continuity when interrupted, live input picking,
rapid navigation, manual scan-scroll interruption, resize/hide/close and both
reduced-motion preferences. State and language tests retain selected values.

Distribution jobs repeat the native suite, build and install the matching
package and open every installed view plus the update dialog. Zorin uses its
Ubuntu base; these checks do not exercise a physical wheel, fan or real system
authorization.

# 0.2.0 interaction validation

Tests cover exact first-frame and interrupted-frame pixels, intermediate frames,
rapid navigation, unsaved input, copy feedback, keyboard focus after rebuilds,
expanded findings, failed scans, resize, hide, close and live reduced motion.
The two installed views are checked on Ubuntu 24.04/26.04, Deepin 25, Fedora 44
and current Arch. Public previews contain no host diagnostic output.

# Validation

Release package workflows build from a single canonical source archive and validate the native GTK application and its diagnostic/download views in these Linux environments:

- Ubuntu 24.04 and 26.04
- Deepin 25
- Fedora 44
- Arch Linux

Each platform job builds and installs its native package, validates the desktop entry, checks that installed application files match the source and opens both views in a private compositor. Diagnostic parsing and SSD status handling use synthetic inputs and mocked system responses; the test suite does not write to hardware.

Zorin 18 is covered through the Ubuntu 24.04 DEB package and system-family detection. It is not a separate release-workflow container. Other distros may work when they provide GTK 4.12, libadwaita 1.5 and the listed Python GTK libraries, but they are not included in the published package matrix.

Check the release's `SHA256SUMS` before using downloaded files. The release workflow also compares the DEB, RPM and Arch package source payloads to the same canonical source archive.

## Update coverage

Update tests use synthetic release metadata and package bytes. They cover numeric
version order, correct app/OS selection, untrusted URLs, missing digests, checksum
and size failures, cancellation, retry, queued callbacks, explicit installation,
PackageKit authorization flags, native installer results and installed-version
verification. Real system authorization is not bypassed or exercised by GUI tests.
The installed package smoke check opens the update dialog without network requests.

## Release checks, 18 October 2026

The 111-test suite passed in Ubuntu 24.04/26.04, Deepin 25, Fedora 44 and Arch.
Fedora/Arch skip only the dpkg-deb-specific tool test; a separate full compositor
run includes the GUI tests that the headless RPM build check skips. All installed
views and the update dialog open from the native packages. An immediate dialog
close regression covers libadwaita 1.5 as well as newer versions. These checks use
isolated containers and do not claim physical hardware or system-authentication coverage.
