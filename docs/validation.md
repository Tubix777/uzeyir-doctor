# Validation

Release package workflows build from a single canonical source archive and validate the native GTK application and its diagnostic/download views in these Linux environments:

- Ubuntu 24.04 and 26.04
- Deepin 25
- Fedora 44
- Arch Linux

Each platform job builds and installs its native package, validates the desktop entry, checks that installed application files match the source and opens both views in a private compositor. Diagnostic parsing and SSD status handling use synthetic inputs and mocked system responses; the test suite does not write to hardware.

Zorin 18 is covered through the Ubuntu 24.04 DEB package and system-family detection. It is not a separate release-workflow container. Other distros may work when they provide GTK 4.12, libadwaita 1.5 and the listed Python GTK libraries, but they are not included in the published package matrix.

Check the release's `SHA256SUMS` before using downloaded files. The release workflow also compares the DEB, RPM and Arch package source payloads to the same canonical source archive.
