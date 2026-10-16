# Uzeyir Doctor

Uzeyir Doctor is a native Linux app that checks common system problems and explains its findings in Turkish or English. It focuses on storage and SSD health, services, network and repository status, update problems, installed Flatpak apps and their folder access.

The app uses GTK 4 and libadwaita with a black, gray and white interface, bundled Manrope typography, animated transitions and an option to reduce motion. Diagnostics run locally in the background. Findings are displayed with their evidence and suggested next steps; the app does not apply repairs or change system settings.

Uzeyir Doctor is published separately from [Uzeyir Control](https://github.com/Tubix777/linux-control), which combines hardware, wheel and diagnostics tools. Doctor has its own app ID, `uzeyir-doctor` command and preferences file, so it can be installed alongside Uzeyir Control.

## Download

Get the latest packages from [Uzeyir Doctor Releases](https://github.com/Tubix777/uzeyir-doctor/releases):

- Debian, Ubuntu, Deepin and Zorin: `.deb`
- Fedora: `.rpm`
- Arch: `.pkg.tar.zst`; an offline build recipe is included too
- Source: `.tar.gz`

Packages target Ubuntu 24.04/26.04, Deepin 25, Fedora 44 and current Arch. Zorin editions based on Ubuntu 24.04 can use the Ubuntu 24.04 package. The app needs GTK 4.12 or newer and libadwaita 1.5 or newer.

Install a downloaded package using the matching system package manager. The download page shows the command for the selected package. No helper runs with elevated privileges. Optional system tools can provide additional diagnostic information; unsupported checks are reported as unavailable.

## Run from source

On a Linux desktop with Python 3.11+, PyGObject, GTK 4, libadwaita, Cairo and librsvg installed:

```sh
./run.sh
```

To start directly in English or open the download page:

```sh
./run.sh --language en
./run.sh --downloads
```

The bundled font is licensed under the SIL Open Font License; see `licenses/Manrope-OFL.txt`. See [installation notes](docs/install.md), [permissions and privacy](docs/permissions.md), [validation notes](docs/validation.md) and [attribution](ATTRIBUTION.md).

## License

Application code is available under GPL-3.0-or-later. Bundled third-party assets retain their own licenses; see `COPYING` and `licenses/`.
