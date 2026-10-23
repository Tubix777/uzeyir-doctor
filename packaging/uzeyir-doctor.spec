Name:           uzeyir-doctor
Version:        0.3.0
Release:        1%{?dist}
Summary:        Native Linux system diagnostics with clear next steps
License:        GPL-3.0-or-later AND OFL-1.1
URL:            https://github.com/Tubix777/uzeyir-doctor
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
BuildRequires:  python3
BuildRequires:  python3-gobject
BuildRequires:  python3-cairo
BuildRequires:  gtk4 >= 4.12
BuildRequires:  libadwaita >= 1.5
BuildRequires:  desktop-file-utils
Requires:       python3
Requires:       python3-gobject
Requires:       python3-cairo
Requires:       gtk4 >= 4.12
Requires:       libadwaita >= 1.5
Requires:       librsvg2
Recommends:     udisks2

%description
Uzeyir Doctor explains local Linux system findings and suggests clear next
steps, including storage, update, service and Flatpak permission checks. It
uses a monochrome GTK 4 interface, Turkish/English selection, optional reduced
motion and read-only diagnostics.

%prep
%autosetup

%build
# Pure Python sources; no build-time network access or wheel build required.

%install
install -d %{buildroot}%{_datadir}/uzeyir-doctor/src
cp -a src/. %{buildroot}%{_datadir}/uzeyir-doctor/src/
find %{buildroot}%{_datadir}/uzeyir-doctor -type d -name __pycache__ -prune -exec rm -rf {} +
install -Dm0755 packaging/uzeyir-doctor %{buildroot}%{_bindir}/uzeyir-doctor
install -Dm0644 share/io.github.Tubix777.UzeyirDoctor.desktop %{buildroot}%{_datadir}/applications/io.github.Tubix777.UzeyirDoctor.desktop
install -Dm0644 share/io.github.Tubix777.UzeyirDoctor.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/io.github.Tubix777.UzeyirDoctor.svg

%check
PYTHONPATH=src GDK_BACKEND=broadway GTK_A11Y=none %{__python3} -m unittest discover -s tests -v
desktop-file-validate %{buildroot}%{_datadir}/applications/io.github.Tubix777.UzeyirDoctor.desktop

%files
%license COPYING licenses/*.txt
%doc README.md ATTRIBUTION.md docs/install.md docs/permissions.md docs/validation.md
%{_bindir}/uzeyir-doctor
%{_datadir}/uzeyir-doctor/
%{_datadir}/applications/io.github.Tubix777.UzeyirDoctor.desktop
%{_datadir}/icons/hicolor/scalable/apps/io.github.Tubix777.UzeyirDoctor.svg

%changelog
* Sat Oct 24 2026 Uzeyir Doctor contributors - 0.3.0-1
- Introduce Graphite surfaces, bundled Inter and readable shared typography
- Refine interruptible navigation, control feedback and compact layouts

* Sat Oct 17 2026 Uzeyir Doctor contributors - 0.2.0-1
- Add interruptible frame-clock navigation and a sliding selection indicator
- Preserve diagnostic details and keyboard focus, improve operation feedback
- Verify reduced motion, rapid navigation, resizing and native distro packages

* Fri Oct 16 2026 Uzeyir Doctor contributors - 0.1.0-1
- Publish Uzeyir Doctor as a standalone diagnostic application
- Add native Fedora, Debian-family and Arch packages
