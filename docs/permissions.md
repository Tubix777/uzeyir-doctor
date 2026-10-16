# Permissions and privacy

Uzeyir Doctor runs checks on the local computer and does not upload scan results. It reads operating-system status and service metadata using the current user's access. Results that the current account cannot verify are marked unavailable; the app does not request administrator rights to hide that limitation.

SSD health is shown only when the system's UDisks service provides a recent SMART reading. The app reports the device's available wear estimate as supplied; it does not turn missing or unsupported data into a health percentage. Installing `udisks2` may make a system D-Bus disk service available on minimal systems.

Flatpak checks list installed apps and inspect their configured filesystem permissions. Choosing a folder is optional and checks whether that selected local folder matches the app's declared access. The folder path is used for the on-screen result only.

The release page is loaded only when the user opens downloads or asks to refresh the release. Download buttons open GitHub in the default browser. The app never installs a package, edits Flatpak overrides, changes system configuration or starts a root helper.

The language, reduced-motion preference and window preferences are saved in `~/.config/uzeyir-doctor/preferences.json` (or under `$XDG_CONFIG_HOME`). They remain on the computer and can be removed by deleting that file.
