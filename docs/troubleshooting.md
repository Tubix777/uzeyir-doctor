# Sık sorulan sorular ve sorun giderme

## Hangi dosyayı indirmeliyim?

[Uzeyir Doctor Releases](https://github.com/Tubix777/uzeyir-doctor/releases/latest) sayfasındaki
Ubuntu/Deepin/Zorin için **DEB**, Fedora için **noarch RPM**, Arch için
**any.pkg.tar.zst** dosyasını seç. Kaynak RPM uygulama kurmak için değildir.
Tam sürüm koşulları ve komutlar [kurulum rehberinde](install.md).
Zorin desteği Ubuntu 24.04 tabanına dayanır; ayrı bir Zorin masaüstü testi değildir.

## Uygulama açılmıyor veya simgeler görünmüyor

Paketi sistem paket yöneticisiyle kur; bu, gerekli GTK, libadwaita, Python ve SVG
yükleyici bağımlılıklarını çözer. Asgari GTK 4.12, libadwaita 1.5 ve Python 3.11
gerekir. Eski dağıtımda bağımlılık kontrollerini atlama. Uygulamayı normal
kullanıcı olarak başlat. Kaynak sürümünde [README](../README.md) içindeki sistem
bağımlılıklarını kullan; rastgele bir pip ortamı sistem GTK kitaplıklarının yerini almaz.

## Animasyon görünmüyor veya geçişler anında oluyor

Üst çubuktaki **Hareketi azalt** tercihini ve masaüstünün animasyon/erişilebilirlik
ayarını kontrol et. Her iki tercih de dikkate alınır. Gizli bölümlerde gereksiz
animasyonlar durur. Tarama sonucuna otomatik kaydırmayı elle kaydırmak keser;
uygulama kullanıcıyla kaydırma yarıştırmaz.

## SSD yüzdesi, sensör veya kontrol neden kullanılamıyor?

Eksik veri, sıfır sağlık anlamına gelmez. Desteklenmeyen cihaz, okunamayan veri
ve eski ölçüm arayüzde ayrı belirtilir. SSD yüzdesi yalnız yeterli ve güncel NVMe
verisi varsa gösterilir; üreticinin kalan dayanıklılık tahminidir. Genel arıza
olasılığı değildir. SATA için tahmini sayı uydurulmaz. [İzinler ve sınırlar](permissions.md)
belgesini incele. Tanı araçlarının kurulu olmaması bazı kontrolleri sınırlar.

## Güncelleme nasıl gelir?

**Ctrl+U → Güncellemeleri kontrol et**. Uygulama yalnız kendi resmî deposundaki
uygun **kararlı** sürümleri seçer. Ön sürümler otomatik güncelleme önerisi olmaz.
Açılış kontrolü isteğe bağlıdır ve başlangıçta kapalıdır. Bu özelliği içeren sürümü
ilk kez paket olarak kurduktan sonra, sonraki sürümler bu pencereden alınabilir.

İndirme aşaması iptal edilebilir. Kurulum ayrı bir kullanıcı eylemidir ve normal
sistem yetkilendirmesi isteyebilir. Kurulu sürüm doğrulanmadan başarı ya da yeniden
başlatma gösterilmez. Tanı sonuçları GitHub'a gönderilmez.

## Güncelleme indirilemiyor veya doğrulanamıyor

Bağlantını kontrol edip yeniden dene. GitHub erişimi/rate limit veya henüz tüm
paketleri yüklenmemiş bir yayın geçici hata verebilir. Boyut ve SHA-256 uyuşmazsa
dosya kurulmaz. Doğrulamayı atlama; resmî sürüm sayfasını kontrol et.
Hata sırasında kurulum başlatılmadıysa çalışan sürüm kullanılmaya devam eder.

## Paket kurucusu açılmadı veya yetkilendirme iptal edildi

Mevcut PackageKit hizmeti yoksa uygulama dağıtımın dosya kurucusunu açmayı dener.
O da yoksa **Kurulum komutunu kopyala** ile doğrulanan yerel dosya için uygun
komutu alabilirsin. Sistem kurulumunu tamamladıktan sonra **Kurulumu doğrula**
düğmesini kullan. Daemon bağlantısı kaybolduysa aynı işlemi tekrarlamadan önce
kurulu sürümü doğrula; paket yöneticisinin devam eden işlemini zorla durdurma.

## Bir hata bildirmek istiyorum

[Hata bildirim formunu](https://github.com/Tubix777/uzeyir-doctor/issues/new/choose) aç.
Uygulama sürümü, dağıtım/sürüm, kurulum yöntemi ve tekrar adımları yeterli başlangıçtır.
Animasyon sorunu için pencere boyutu, hareket azaltma durumu ve mümkünse kısa bir
kayıt ekle. Kayıttaki kullanıcı adı, dosya yolu, seri numarası ve kişisel günlükleri
paylaşmadan önce gizle. Otomatik tanı yükleme yapılmaz.

## English

Use the package matching your distribution and the runtime versions in the install
guide. Update checks select only stable releases from this app's own repository;
installation requires an explicit action and normal system authorization. Invalid
or incomplete downloads never start installation. Reduced Motion follows both app
and desktop settings. Missing hardware data is reported as unavailable. Report
reproducible issues with app/distro versions and remove personal information first.
