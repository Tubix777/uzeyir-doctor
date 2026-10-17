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
