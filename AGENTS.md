# Uzeyir Doctor project rules

- Keep Uzeyir Doctor a standalone read-only GTK 4/libadwaita diagnostic app. Do not copy Anvil Control or Wheel Control modules into this repository.
- Keep the Turkish and English interface, dark monochrome palette, Manrope font, keyboard access, transitions and reduced-motion support consistent across both pages.
- Run system probes off the GTK main thread. Never invent SMART percentages, diagnosis results or progress. Do not install privileged helpers, modify system files, or apply repairs automatically.
- Keep package identifiers, command, settings directory and source archive aligned with `pyproject.toml` and `packaging/`.
- For every published version, update `pyproject.toml`, its `source-date-epoch`, release notes and RPM changelog, then publish the verified source archive, DEB, RPM, source RPM and Arch package/build recipe together on GitHub Releases.
- Keep package recipes usable from the canonical release source archive; don't depend on unpinned downloads.
- Do not commit generated packages, local scan output, personal settings, caches or build directories.
