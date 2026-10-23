# Uzeyir Doctor 0.3.0 — Graphite / Inter

Daha okunaklı, tutarlı ve sakin bir yerel arayüz. Graphite görünümü siyah, gri ve
beyaz paleti mat yüzeyler, ince sınırlar ve daha rahat boşluklarla birleştirir.

## Görünüm ve kullanım

- Inter değişken yazı tipi lisansı ve sabit kaynak kaydıyla pakete dahil edildi.
  Font yalnız uygulama içinde yüklenir; çevrimiçi font isteği yapılmaz.
- Temel metin 15 px, sayfa başlıkları 29 px. Menü, açıklama, düğme ve veri
  boyutları ortak bir hiyerarşi kullanır. Sayısal değerler sabit aralıklıdır.
- Sayfa başlıkları görevi doğrudan adlandırır. Sol menü, indirme sayfaları,
  tarama kartları ve güncelleme penceresi ortak Graphite görünümündedir.
- Dar pencerede Flatpak seçimi ve eylemleri iki satıra geçer. Aynı kontroller
  kullanıldığı için seçim ve kaydedilmemiş değerler korunur.

## Hareket

- Sayfa geçişi 300 ms ve 16 px; sol menü göstergesi 260 ms. Hızlı seçimlerde
  önceki hareketin görünen karesi korunur; giriş alanları hemen kullanılabilir.
- Kart girişi 280 ms, açılan ayrıntılar 220 ms. Düğme tepkileri kısa ve ölçülüdür.
  Sabit bilgi kartlarında gereksiz fare üzeri hareket kaldırıldı.
- Tarama tamamlanması ve kopyalama kısa geri bildirim verir. Gerçek ölçüm,
  tarama ve indirme verileri geciktirilmez; ilerleme uydurulmaz.
- Hareketi azaltma ve masaüstünün animasyon tercihi bütün geçişlere uygulanır.
  Gizleme, yeniden boyutlandırma ve kapatma devam eden hareketi sonlandırır.

## Güncelleme ve paketler

Ctrl+U ile mevcut uygulama içi güncelleyiciye ulaşılır. Paket boyutu, GitHub
SHA-256 özeti ve SHA256SUMS indirmede; dosya tekrar kurulum öncesinde doğrulanır.
Kurulum kullanıcı eylemi ve normal sistem yetkilendirmesiyle başlar.

DEB (Ubuntu / Deepin / Zorin / Debian), Fedora RPM ve kaynak RPM, Arch pacman
paketi, sabit kaynaklı çevrimdışı PKGBUILD, kaynak arşivi ve SHA256SUMS birlikte
sunulur. Bütün paketler tek kanonik kaynak arşivini kullanır. Python ≥ 3.11,
GTK ≥ 4.12 ve libadwaita ≥ 1.5 gerekir. Zorin kapsamı Ubuntu tabanı üzerindendir.

[Kurulum ve dosyalar](install.md) · [Doğrulama kapsamı](validation.md) ·
[Inter lisansı ve kaynağı](../licenses/Inter-source.txt)

## English

Graphite adds matte monochrome surfaces and bundled Inter typography. Larger,
consistent labels and controls improve readability; compact Flatpak controls
adapt without rebuilding widgets. Interruptible 300 ms / 16 px page transitions,
260 ms sidebar selection and subtle feedback keep navigation responsive.
Reduced motion, keyboard access, unsaved input and the verified in-app updater
are preserved. Diagnostics remain read-only; no new device permissions or
privileged helpers are added. Distribution packages share one canonical source.

---

# Uzeyir Doctor 0.2.0 — akıcı geçişler ve uygulama içinden güncelleme

## Uygulama içinden güncelleme

Üst çubuk veya Ctrl+U yeni güncelleme penceresini açar. GitHub'daki kararlı sürüm
sistem paketine göre seçilir; notlar gösterilir. İndirme gerçek byte ilerlemesi,
iptal ve yeniden deneme sunar. Boyut, API SHA-256 ve SHA256SUMS doğrulanır;
kurulumdan hemen önce dosya yeniden kontrol edilir.

Kullanıcı başlattığında mevcut PackageKit hizmeti ve normal sistem yetkilendirmesi
kullanılır. Hizmet yoksa yerel paket kurucusu/komut akışına geçilir. Kurulu sürüm
sorgulanmadan başarı gösterilmez. Açılış kontrolü isteğe bağlı ve başlangıçta kapalıdır.
Yeni ayrıcalıklı yardımcı veya geniş cihaz izni kurulmaz. İlk güncelleyici sürümünü
kurduktan sonra sonraki sürümler uygulamadan alınabilir.


## Kullanıcı deneyimi

- Teşhis ve indirme ekranı 360 ms içinde kısa mesafeli hareketle karışır.
  Geçiş sırasında yeniden gezinmek son çizilen kareden devam eder; son seçim hemen açılır.
- Sol menüdeki seçim göstergesi, kart girişleri ve açılan ayrıntılar ortak bir ritim kullanır.
  Yeni sayfanın üzerine ikinci bir kart solması bindirilmez.
- Tarama düğmesi işlemin sürdüğünü belirtir; gerçek tamamlanmada kısa bir vurgu oynar.
  Etkinlik sinyali ve sonuçlara otomatik kaydırma korunur; elle kaydırmak hareketi durdurur.
- Komut kopyalanınca düğmede kısa onay görünür. Paket listesi yenilenince eski
  zamanlayıcılar bırakılır, klavye odağı karşılık gelen eylemde tutulur.
- Dil ve filtre değişimi açık kanıt/çözüm ayrıntılarını korur.

## Düzeltmeler ve doğrulama

- Geçişin ilk karesindeki kararma düzeltildi. İlk geçiş ve kesilen geçiş, çizilen
  görüntünün piksel olarak korunduğu testlerle kontrol edilir.
- Başarısız tarama tamamlanan kontrol olarak sayılmaz; hata durumu dil değişince korunur.
- Tıklama alanları sayfanın hareketini takip eder. Küçültme, gizleme, kapatma ve
  hareket azaltma devam eden geçişi sonlandırır.
- Yerel GTK testleri hızlı gezinmeyi, kaydedilmemiş girdileri, klavye odağını ve
  işlem yaşam döngüsünü kapsar. Beş dağıtım işi kurulu iki görünümü de açar.

- Ubuntu 24.04 ve Deepin 25 üzerindeki eski libadwaita ile açılış anında
  kapatılan güncelleme penceresinin yeniden açılması düzeltildi.
- GitHub tanıtımı gerçek arayüz önizlemeleri, sık sorulan sorular, katkı rehberi
  ve hata/özellik bildirim şablonlarıyla yenilendi.

## İndirme dosyaları

| Sistem | Dosya |
| --- | --- |
| Ubuntu 24.04/26.04, Deepin 25, Zorin 18, Debian 13 | `uzeyir-doctor_0.2.0-1_all.deb` |
| Fedora 44 | `uzeyir-doctor-0.2.0-1.fc44.noarch.rpm` |
| Güncel Arch Linux | `uzeyir-doctor-0.2.0-1-any.pkg.tar.zst` |
| Çevrimdışı Arch derleme | `uzeyir-doctor-0.2.0-arch-build.tar.gz` |
| Kaynak ve kaynak RPM | `uzeyir-doctor-0.2.0.tar.gz`, `uzeyir-doctor-0.2.0-1.fc44.src.rpm` |

`SHA256SUMS` paketleri ve kaynak arşivlerini kapsar. Hepsi tek kanonik kaynak
arşivinden üretilir. Python ≥ 3.11, GTK ≥ 4.12 ve libadwaita ≥ 1.5 gerekir.
Zorin 18 desteği Ubuntu 24.04 tabanını kullanır. Teşhis yerel ve salt okunurdur;
SSD yüzdesi yalnız desteklenen güncel veriyle gösterilir. Bu sürüm onarım uygulamaz.

## English

Version 0.2.0 adds short interruptible page transitions, a shared selection
indicator, calmer entrances, real-operation completion feedback and copy
confirmations. Expanded findings and keyboard focus survive rebuilds; failed
scans no longer count as completed checks. Pixel-continuity, rapid navigation,
input, resize and reduced-motion regressions are covered. Packages are built
from one canonical source archive and validated in five Linux environments.

---

# Uzeyir Doctor 0.1.0

First standalone release: local system and Flatpak diagnostics, recent NVMe SMART
information, Turkish/English, monochrome GTK 4 design, Manrope and reduced motion.
Fedora RPM, Debian-family DEB and Arch packages, source, offline recipe and checksums.
