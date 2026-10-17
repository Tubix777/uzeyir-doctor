# Installation

Download packages from <https://github.com/Tubix777/uzeyir-doctor/releases>.

- Ubuntu 24.04/26.04, Deepin 25 and Ubuntu-based Zorin 18: download the `.deb` and install it with your package manager. For example, in the download directory run `sudo apt install ./uzeyir-doctor_0.2.0-1_all.deb`.
- Fedora 44: download the `.rpm` and run `sudo dnf install ./uzeyir-doctor-0.2.0-1.fc44.noarch.rpm`.
- Arch Linux: download the `.pkg.tar.zst` and run `sudo pacman -U ./uzeyir-doctor-0.2.0-1-any.pkg.tar.zst`. The adjacent build archive contains the pinned source and PKGBUILD for an offline `makepkg` build.

Package names contain the release version. Replace `0.2.0` in these examples when installing a later release. Package managers resolve required runtime libraries. The app requires GTK 4.12 and libadwaita 1.5 or newer.

The app command is `uzeyir-doctor`. To launch the standalone source checkout, install its system GTK/Python prerequisites and run `./run.sh`. See `README.md` for source launch options.

Packages install the desktop entry, app icon, Python sources and license/documentation files. They do not install a privileged helper, udev rule or system service.
