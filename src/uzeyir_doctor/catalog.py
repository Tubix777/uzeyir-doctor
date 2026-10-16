"""Known Turkish/English diagnostic UI messages; device evidence stays intact."""

TRANSLATIONS = dict(line.split("\t", 1) for line in """
Devre hareketi görseldir; fan yalnız pozitif, güncel RPM okumasında döner. Hızı ölçekli değildir.	Circuit activity is decorative; the fan rotates only with a positive, fresh RPM reading. Rotation is not to scale.
Donanım	Hardware
Direksiyon	Racing wheel
Sorun Teşhisi	Diagnostics
Sorun teşhisi	Diagnostics
Ayarlar	Settings
Dil	Language
Türkçe	Turkish
İngilizce	English
Hareketi azalt	Reduce motion
Geçiş animasyonlarını azalt	Reduce transition animations
Canlı veriler anında güncellenmeye devam eder.	Live data continues to update immediately.
Bilgisayarın, tek bir yerde.	Your computer, in one place.
Donanım, direksiyon ve sistem teşhisi	Hardware, racing wheel and system diagnostics
Yerel ve özel	Local and private
Yerel çalışır	Runs locally
Bilgisayarını anla	Understand your computer
BİLGİSAYARINI ANLA	UNDERSTAND YOUR COMPUTER
Sorun ne? Birlikte bakalım.	What's wrong? Let's take a look.
Linux kontrolleri, anlaşılır açıklamalar ve uygulanabilir adımlar.	Linux checks, clear explanations and practical next steps.
Sistemi tara	Scan system
Yerel çalışır · Sistem ayarlarını değiştirmez	Runs locally · Does not change system settings
Henüz tarama yapılmadı. İlk kontrol birkaç saniye sürer.	No scan yet. The first check takes a few seconds.
Bir uygulamada sorun mu var?	Having trouble with an application?
Kurulu Flatpak uygulamasını seç. İstersen erişemediği klasörü de kontrol et.	Choose an installed Flatpak application. You can also check a folder it cannot access.
Uygulamalar yükleniyor…	Loading applications…
Kontrol edilecek Flatpak uygulaması	Flatpak application to check
Klasör seç	Choose folder
Uygulamayı kontrol et	Check application
Klasör seçimi isteğe bağlıdır.	Choosing a folder is optional.
Bulgular burada görünecek.	Findings will appear here.
Kurulu Flatpak uygulaması bulunamadı	No installed Flatpak applications found
kişisel	user
Kontrol edilecek klasör	Folder to check
Yalnız yerel klasörler kontrol edilebilir.	Only local folders can be checked.
Klasörü değiştir	Change folder
Sistem kontrol ediliyor…	Checking the system…
Tarama tamamlanamadı. Sistem ayarlarında değişiklik yapılmadı.	The scan could not finish. No system settings were changed.
Tarama tamamlanamadı; hiçbir ayar değiştirilmedi.	The scan could not finish; no settings were changed.
Gözlem ve önerilen adımlar	Evidence and suggested steps
Kanıtlar ve çözüm adımları	Evidence and next steps
Kanıtlar ve önerilen adımlar	Evidence and suggested steps
İyi	Good
Dikkat	Attention
Önemli	Important
Bilgi	Information
Kontrol edilemedi	Could not check
Doğrudan gözlem	Direct observation
Sistem diski	System disk
Kişisel dosyaların diski	Personal files disk
Disk doluluğu	Disk usage
Disk kapasitesi okunamadı.	Disk capacity could not be read.
Diskteki boş alan çok az; kurulum ve güncellemeler etkilenebilir.	Free disk space is very low; installations and updates may be affected.
Bu dosya sisteminde yeterli boş alan görünüyor.	This filesystem appears to have enough free space.
Büyük dosyaları dosya yöneticisinden incele.	Review large files in your file manager.
Gereksiz olduğundan emin olduğun dosyaları kaldır; ardından tekrar tara.	Remove files you are sure you no longer need, then scan again.
Kullanıcı servisleri	User services
Sistem servisleri	System services
Servisler	Services
Servis durumu okunamadı; sağlıklı olduğu varsayılmadı.	Service status could not be read; it was not assumed healthy.
Başarısız durumda servis bulunmadı.	No failed services found.
İlgili servisin durumunu ve hata kaydını incele.	Review the affected service's status and error log.
Servisin görevini anlamadan yeniden başlatma veya devre dışı bırakma.	Understand the service's purpose before restarting or disabling it.
İşletim sistemi	Operating system
Kontroller yerel bilgisayarda çalışır.	Checks run on this computer.
Yönetici yetkisi istenmez.	Administrator privileges are not requested.
Sistem bilgisi okunamadı.	System information could not be read.
Disk bilgisi okunamadı.	Disk information could not be read.
Bu sistemde systemctl bulunamadı.	No systemctl was found on this system.
Ağ bağlantısı	Network connection
NetworkManager durumu okunamadı.	NetworkManager status could not be read.
NetworkManager bir ağ bağlantısı bildiriyor. İnternet erişimi ayrıca test edilmedi.	NetworkManager reports a network connection. Internet access was not tested separately.
NetworkManager bağlı bir ağ bildirmiyor.	NetworkManager does not report a connected network.
Masaüstünün ağ menüsünde Wi-Fi veya kablo bağlantısını kontrol et.	Check Wi-Fi or cable connectivity in the desktop network menu.
NetworkManager aracı bulunamadı; ağ testi yapılmadı.	NetworkManager's tool was not found; no network test was performed.
SSD sağlığı	SSD status
SSD sağlık verisi okunamadı; diğer kontroller tamamlandı.	SSD data could not be read; the other checks completed.
RPM depoları	RPM repositories
Bu sistemde Fedora tarzı RPM depo dizini bulunmuyor.	No Fedora-style RPM repository directory was found on this system.
Depo yapılandırması	Repository configuration
Bazı depo dosyaları okunamadı veya geçerli biçimde değil.	Some repository files could not be read or have an invalid format.
İlgili depo dosyasını incele. Bu uygulama dosyada değişiklik yapmaz.	Review the affected repository file. This application does not modify it.
Etkin RPM deposu bulunamadı. Atomik Fedora sürümlerinde güncelleme yolu farklı olabilir.	No enabled RPM repositories found. Atomic Fedora editions may use a different update mechanism.
Klasöre erişim	Folder access
Flatpak dosya erişimi sorgusu tamamlanamadı.	The Flatpak file-access query could not finish.
Flatpak bu klasöre doğrudan erişim olmadığını bildiriyor. Dosya seçme penceresi üzerinden verilen erişim farklı olabilir.	Flatpak reports no direct access to this folder. Access granted through a file picker may differ.
Doğrudan erişim: yok	Direct access: none
Önce uygulamanın Dosya aç menüsünden dosyayı seçmeyi dene.	First try choosing the file from the application's Open File menu.
Kalıcı klasör erişimi gerekiyorsa uygulamanın izinlerini incele; yalnız gerekli klasöre izin ver.	If persistent folder access is needed, review application permissions and allow only the required folder.
İzin durumu doğrulandı; hata nedeni henüz kesin değil	Permissions verified; the cause of the error is still uncertain
Yalnız okuma	Read only
Okuma ve yazma	Read and write
yalnız okuma	read only
okuma ve yazma	read and write
Sorun sürüyorsa dosyanın biçimini ve normal dosya izinlerini kontrol et.	If the problem persists, check the file format and ordinary file permissions.
Flatpak beklenen erişim yanıtını vermedi; sonuç tahmin edilmedi.	Flatpak did not return the expected access response; no result was guessed.
Uygulama kurulumu	Application installation
Seçilen kurulumdaki uygulama bilgisi okunamadı.	Application information could not be read from the selected installation.
Seçilen Flatpak kurulumu okunabildi.	The selected Flatpak installation could be read.
Çalışma ortamı	Runtime
Gerekli Flatpak çalışma ortamı kurulu görünüyor.	The required Flatpak runtime appears to be installed.
Gerekli çalışma ortamı doğrulanamadı.	The required runtime could not be verified.
Uygulamanın çalışma ortamı bilgisi doğrulanamadı.	The application's runtime information could not be verified.
Seçilen klasör	Selected folder
Klasör mevcut değil veya okunamıyor.	The folder does not exist or cannot be read.
Açılış testi	Launch check
Uygulama çalıştırılmadı. Kurulum ve izin bulguları, açılış hatasının nedenini tek başına kanıtlamaz.	The application was not launched. Installation and permission findings alone do not prove the cause of a launch failure.
Uygulamayı normal şekilde açıp sonucu gözlemle.	Open the application normally and observe the result.
Gerekli araç kurulu değil.	The required tool is not installed.
Kontrol zaman aşımına uğradı.	The check timed out.
Kontrol tamamlanamadı.	The check could not finish.
Tahmini kalan ömür	Estimated remaining endurance
Model bilinmiyor	Unknown model
Yedek kapasite eşik altında	Spare capacity is below its threshold
Sıcaklık güvenli aralığın dışında	Temperature is outside its safe range
Denetleyici güvenilirlik kaybı bildiriyor	The controller reports degraded reliability
Depolama salt okunur duruma geçmiş	Storage has switched to read-only mode
Geçici bellek yedekleme sorunu	Volatile-memory backup problem
Kalıcı bellek bölgesi salt okunur veya güvenilir değil	Persistent memory is read-only or unreliable
Tanınmayan bir kritik SMART uyarısı bildirildi	An unrecognized critical SMART warning was reported
Geçerli bir SMART kayıt zamanı yok; SSD’nin güncel kalan ömür yüzdesi doğrulanamadı.	No valid SMART recording time exists; the SSD's current remaining-endurance percentage could not be verified.
SMART bilgisi henüz kaydedilmemiş veya kayıt zamanı geçersiz.	SMART data has not been recorded or the recording time is invalid.
SMART kaydı doğrulanamadı	SMART record could not be verified
Kaynak: UDisks2 önbelleğindeki NVMe SMART kaydı	Source: cached NVMe SMART record in UDisks2
SMART kaydı: son 24 saat içinde	SMART record: within the last 24 hours
SMART kaydı 24 saatten eski; güncel bir kalan ömür yüzdesi gösterilemiyor.	The SMART record is over 24 hours old; a current remaining-endurance percentage cannot be shown.
SMART kaydı 24 saatten eski; güncel bir kalan ömür yüzdesi gösterilemiyor. Önceki kayıtta kritik SMART uyarısı var; güncel durumu ayrıca doğrula.	The SMART record is over 24 hours old; a current remaining-endurance percentage cannot be shown. The previous record contains a critical SMART warning; verify the current state separately.
Önemli dosyalarının yedeğini kontrol et; kayıtlı uyarıyı güncel bir SMART raporuyla doğrula.	Check backups of important files and verify the recorded warning with a current SMART report.
Eski SMART kaydı; güncel durum doğrulanmadı	Old SMART record; current state not verified
Bu yüzde, üreticinin tahmini dayanıklılığından kalan payı gösterir; genel sağlık garantisi veya arıza olasılığı değildir.	This percentage represents the remaining portion of the manufacturer's endurance estimate; it is not a general health guarantee or a probability of failure.
NVMe dayanıklılık yüzdesi alınamadı veya desteklenmiyor; kalan ömür tahmin edilmedi.	The NVMe endurance percentage could not be read or is unsupported; remaining endurance was not guessed.
Üreticinin dayanıklılık tahmini; arıza tahmini değil	Manufacturer's endurance estimate; not a failure prediction
SMART kaydında ayrıca kritik uyarı bulunuyor; bu uyarı kalan ömür yüzdesinden bağımsızdır.	The SMART record also contains a critical warning; this warning is independent of the remaining-endurance percentage.
SSD SMART bilgisi için gerekli yerel D-Bus bağlantısı kullanılamıyor.	The local D-Bus connection required for SSD SMART data is unavailable.
SSD SMART bilgisine erişilemedi; UDisks2 hizmeti veya erişim izni kullanılamıyor.	SSD SMART data could not be accessed; UDisks2 or access permissions are unavailable.
SSD donanım bilgisi beklenen biçimde alınamadı.	SSD hardware information was not received in the expected format.
SATA SSD saptandı. Kalan ömür yüzdesi üreticiye özgü SMART değerlerine bağlı; bu sürümde doğrulanamıyor.	A SATA SSD was detected. Remaining-endurance percentage depends on vendor-specific SMART values and cannot be verified in this version.
Katı hal depolama saptandı; bu cihaz için desteklenen bir kalan ömür yüzdesi alınamadı.	Solid-state storage was detected; no supported remaining-endurance percentage could be read for this device.
Yüzde sağlayan desteklenen bir SSD saptanamadı; sağlık yüzdesi tahmin edilmedi.	No supported SSD providing a percentage was detected; a health percentage was not guessed.
Etkin direksiyon	Active wheel
Cihazları tara (Ctrl+R)	Scan devices (Ctrl+R)
Görünüm	Appearance / Görünüm
Uygulama teması	Application theme
Dekoratif geçişleri kapat; canlı giriş anında güncellenir	Disable decorative transitions; live input remains immediate
Wheel Control hakkında	About Wheel Control
Tanı bilgilerini kopyala  Ctrl+D	Copy Diagnostics  Ctrl+D
Direksiyon algılanmadı	No racing wheel detected
Logitech direksiyonunu USB ile bağla, uygunsa PC/PS3 moduna al, ardından yeniden tara.	Connect your Logitech wheel by USB, switch it to PC/PS3 mode when applicable, then scan again.
Tekrar tara	Scan Again
Demoyu aç	Open Demo
Bağlı	Connected
G29 PS4 modunda. Linux kuvvet geri bildirimi ve dönüş açısı kontrolünü etkinleştirmek için donanım anahtarını PS3 konumuna al, ardından yeniden bağla.	G29 is in PS4 mode. Move the hardware selector to PS3, then reconnect it to enable Linux force feedback and range control.
Bazı ayarlar salt okunur. Paketli udev kuralı yönetici tarafından kurulmalı; ardından direksiyonu yeniden bağla.	Some settings are read-only. The packaged udev rule requires administrator installation; then reconnect the wheel.
Canlı giriş	Live input
Canlı giriş, direksiyon ayarları ve oyun profilleri	Live input, wheel settings and game profiles.
Gaz	Throttle
Fren	Brake
Debriyaj	Clutch
Yön tuşu: merkezde	D-pad: centered
Tuşlar: yok	Buttons: none
Direksiyon ayarları	Wheel settings
Uyumluluk modu	Compatibility mode
Eski oyunlar için cihazı yeniden tanıtır	Re-enumerates the wheel for older games
Değiştir	Switch
Dönüş açısı	Rotation range
Azami direksiyon dönüşü	Maximum steering lock
Kuvvet geri bildirimi	Force feedback
Genel etki gücü	Global effect strength
Otomatik merkezleme	Auto-center
Oyun dışında direksiyonu merkezler	Centers the wheel outside games
Pedalları birleştir	Combine pedals
Gaz ve freni tek eksen olarak sunar	Expose throttle and brake as a single axis
Yay	Spring
Yay etkilerinin gücü	Strength of spring effects
Sönümleyici	Damper
Sönümleme etkilerinin gücü	Strength of damper effects
Sürtünme	Friction
Sürtünme etkilerinin gücü	Strength of friction effects
Doygunluk LED'leri	Clipping LEDs
Direksiyon LED'lerini canlı kuvvet geri bildirimi göstergesi olarak kullan	Use the wheel LEDs as a live force-feedback meter
Gelişmiş kuvvet etkileri	Advanced force effects
Uygula	Apply
Kuvvet geri bildirimi zirvesi	Force-feedback peak
Zirveyi sıfırla	Reset Peak
Profiller	Profiles
Bu ayarları bir oyun için kaydet	Save these settings for a game
Yükle	Load
Mevcut ayarları kaydet	Save Current
Profil oluştur	Create profile
Profil içe aktar	Import profile
Profil dışa aktar	Export profile
Profili sil	Delete profile
Hazır	Ready
Yalnız giriş	Input only
Sınırlı erişim	Limited access
Giriş kullanılamıyor	Input unavailable
Salt okunur: cihaz izni gerekiyor	Read-only: device permission required
Canlı giriş kullanılamıyor. Cihaz izinlerini kontrol et ve direksiyonu yeniden bağla.	Live input is unavailable. Check device permissions and reconnect the wheel.
Ayarlar uygulandı	Settings applied
Yazılabilir ayar yok	No writable settings available
Profil Oluştur	Create Profile
Rally, Drift veya F1 gibi kısa bir ad seç.	Choose a short name such as Rally, Drift, or F1.
Profil adı	Profile name
İptal	Cancel
Oluştur	Create
Profil adı boş olamaz	Profile name cannot be empty
Bu adla bir profil zaten var	A profile with that name already exists
En az bir profil gerekiyor	At least one profile is required
Profil silinsin mi?	Delete profile?
Sil	Delete
Profil Dışa Aktar	Export Profile
Profil İçe Aktar	Import Profile
Yalnız yerel dosyalar desteklenir	Only local files are supported
Tanı bilgileri panoya kopyalandı	Diagnostics copied to clipboard
Uyumluluk modu değiştirilsin mi?	Switch compatibility mode?
Direksiyon bağlantısı kesilip yeniden bağlanacak. Önce oyunu kapat ve ellerini çek: direksiyon kalibrasyon yapabilir.	The wheel will disconnect and reconnect. Close your game first and keep your hands clear: the wheel may calibrate.
Modu Değiştir	Switch Mode
Mod değişiyor; direksiyonun yeniden bağlanması bekleniyor	Switching mode; waiting for the wheel to reconnect
Kuvvet geri bildirimi zirvesi sıfırlandı	Force-feedback peak reset
Linux için yerel bir direksiyon kontrol merkezi.	A native Linux control center for racing wheels.
merkezde	centered
yukarı	up
sağ-yukarı	up-right
sağ	right
sağ-aşağı	down-right
aşağı	down
sol-aşağı	down-left
sol	left
sol-yukarı	up-left
bilinmiyor	unknown
yok	none
doygunluk yok	no clipping
sınıra yakın	near limit
doygunluk	clipping
benzetimli giriş	simulated input
CPU kullanımı	CPU usage
CPU sıcaklığı	CPU temperature
GPU kullanımı	GPU usage
GPU sıcaklığı	GPU temperature
Bellek	Memory
Depolama	Storage
Sıcaklıklar	Temperatures
Sensörler	Sensors
Fanlar	Fans
Fan kontrolü	Fan control
Güç profili	Power profile
Sistem	System
Donanım bilgisi	Hardware information
İşlemci	Processor
Ekran kartı	Graphics card
Anakart	Motherboard
Çekirdek	Kernel
Çalışma süresi	Uptime
Bağlantı	Connection
Veri bekleniyor…	Waiting for data…
Kullanılamıyor	Unavailable
Desteklenmiyor	Unsupported
Sensör ara	Search sensors
Ölçümleri dışa aktar	Export measurements
Tanı raporunu dışa aktar	Export diagnostics
Yenile	Refresh
Dengeli	Balanced
Performans	Performance
Güç tasarrufu	Power saver
Yalnız izleme	Monitoring only
RGB aydınlatma	RGB lighting
OpenRGB bağlantısı	OpenRGB connection
Renk	Color
Parlaklık	Brightness
Bağlan	Connect
Bağlantıyı yenile	Refresh connection
Verileri kopyala	Copy data
Kapat	Close
Tamam	OK
Kaydet	Save
""".strip().splitlines())

TEMPLATES = [tuple(line.split("\t", 1)) for line in """
Seçilen klasör: {name}	Selected folder: {name}
{name} kontrol ediliyor…	Checking {name}…
{count} kontrol tamamlandı · {alerts} dikkat gerektiren bulgu	{count} checks completed · {alerts} findings need attention
{count} kontrol tamamlandı. {alerts} bulgu dikkat gerektiriyor.	{count} checks completed. {alerts} findings need attention.
Kullanım: %{number}	Usage: {number}%
Boş alan: {number} GB	Free space: {number} GB
Başarısız durumda {count} servis bulundu. Bu bulgu tek başına uygulama hatasının nedenini kanıtlamaz.	{count} failed services found. This finding alone does not prove the cause of an application error.
{count} etkin depo tanımı bulundu. Depoların erişilebilirliği ve güncelleme işlemi test edilmedi.	{count} enabled repository definitions found. Repository availability and the update process were not tested.
Flatpak doğrudan erişim bildiriyor: {access}. Bu, uygulamanın dosyayı başarıyla açtığını kanıtlamaz.	Flatpak reports direct access: {access}. This does not prove the application can successfully open the file.
Doğrudan erişim: {access}	Direct access: {access}
SMART kaydı: {hours} saat önce; güncel kabul edilmedi.	SMART record: {hours} hours ago; not considered current.
Üreticinin bildirdiği tahmini ömür kullanımı: %{number}	Estimated endurance used, reported by the manufacturer: {number}%
Görünüm kaydedilemedi: {error}	Could not save appearance: {error}
Hareket tercihi kaydedilemedi: {error}	Could not save motion preference: {error}
Cihaz taraması başarısız: {error}	Device scan failed: {error}
{count} ayar uygulandı; değişmeyen: {names}. Cihaz izinlerini kontrol et.	Applied {count} settings; unchanged: {names}. Check device permissions.
{name} yüklendi — direksiyona göndermek için Uygula'ya bas	Loaded {name} — press Apply to send to wheel
Profil kaydedilemedi: {error}	Could not save profile: {error}
{name} kaydedildi	Saved {name}
Profil oluşturulamadı: {error}	Could not create profile: {error}
{name} oluşturuldu	Created {name}
“{name}” kaldırılacak. Direksiyondaki ayarlar değişmeyecek.	“{name}” will be removed. Settings on the wheel will not change.
Profil silinemedi: {error}	Could not delete profile: {error}
{name} silindi	Deleted {name}
Profil dışa aktarılamadı: {error}	Could not export profile: {error}
{name} dışa aktarıldı	Exported {name}
Profil içe aktarılamadı: {error}	Could not import profile: {error}
{name} içe aktarıldı	Imported {name}
{name} adında bir profil zaten var	A profile named {name} already exists
Mod değiştirilemedi: {error}	Could not switch mode: {error}
Zirve sıfırlanamadı: {error}	Could not reset peak: {error}
Yön tuşu: {direction}	D-pad: {direction}
Tuşlar: {state}	Buttons: {state}
{percent}% — {state}	{percent}% — {state}
SSD · {model}	SSD · {model}
Uzeyir Doctor {version} · İlk çalışan prototip · Günlükler dışarı gönderilmez	Uzeyir Doctor {version} · Working prototype · Logs are not uploaded
""".strip().splitlines()]

TRANSLATIONS.update(dict(line.split("\t", 1) for line in """
ÖN SÜRÜM	PREVIEW
ARAÇLAR	TOOLS
Bilgisayarın, tek yerde.	Your computer, in one place.
Sıcaklık, fan ve performans	Temperature, fans and performance
Canlı giriş ve oyun profilleri	Live input and game profiles
Sistem taraması ve çözüm adımları	System scans and next steps
Geçiş ve kaydırma animasyonlarını azalt	Reduce transition and scrolling animations
Yerel ve şeffaf	Local and transparent
sistem	system
Tarama tamamlanamadı	Scan could not finish
Bir kontrol sırasında hata oluştu. Tekrar taramayı deneyebilirsin.	An error occurred during a check. You can try scanning again.
Kanıt ve çözüm adımları	Evidence and next steps
Bilgisayarının nabzı.	Your computer's pulse.
Donanım bilgileri okunuyor…	Reading hardware information…
İlk ölçüm bekleniyor	Waiting for the first sample
Veri bekleniyor	Waiting for data
Canlı performans	Live performance
Son 120 ölçüm · CPU / GPU kullanımı (%)	Last 120 samples · CPU / GPU usage (%)
Sensörler ve fan devirleri	Sensors and fan speeds
Güncel değer · Oturumdaki en düşük / en yüksek	Current value · Session minimum / maximum
Sensör ara…	Search sensors…
Donanım kontrolleri	Hardware controls
Ayarlar yalnızca Uygula düğmesine bastığında değişir.	Settings change only when you press Apply.
Bu kurulumda donanım değiştirme kapalı.	Hardware changes are disabled in this installation.
Anakart fan kontrolü	Motherboard fan control
Önceki ayarı geri al	Restore previous settings
Eğriyi uygula	Apply curve
Özel fan eğrisi	Custom fan curve
Özel eğriyi uygula	Apply custom curve
Tam hız	Full speed
20–85 °C arasında artan sıcaklıklar; azalmayan hız ve son iki noktada %100 gerekiyor.	Temperatures must increase between 20–85 °C; speeds must not decrease and the last two points must be 100%.
Fan eğrisi beş tam sayı noktasından oluşmalı.	The fan curve must have five integer points.
Fan eğrisi güvenli sıcaklık ve hız sınırlarına uymuyor.	The fan curve does not meet safe temperature and speed limits.
Güvenli fan kanalı artık kullanılamıyor.	The validated fan channel is no longer available.
Geçersiz fan işlemi.	Invalid fan operation.
Paketli fan yardımcısı bulunamadı; fan kontrolü kapalı.	The packaged fan helper was not found; fan control is disabled.
Paketli fan yardımcısı ve doğrulanmış kanal gerekiyor.	A packaged fan helper and a validated channel are required.
Bu anakartta güvenli fan yazımı kullanılamıyor.	Safe fan writes are unavailable on this motherboard.
Yeni başarılı fan ölçümü bekleniyor.	Waiting for a new successful fan sample.
Fan ayarı uygulanıyor ve geri okunuyor…	Applying the fan setting and reading it back…
Sistemin sunduğu güç profilleri bekleniyor.	Waiting for the power profiles provided by the system.
Güç profili servisi veri sunmuyor.	The power-profile service is not providing data.
Güç profili uygulanıyor…	Applying power profile…
OpenRGB aygıtları henüz taranmadı.	OpenRGB devices have not been scanned yet.
Cihazları tara	Scan devices
Renk (#RRGGBB)	Color (#RRGGBB)
Kontrol edilebilir RGB aygıtı bulunamadı.	No controllable RGB devices found.
RGB aygıtları taranıyor…	Scanning RGB devices…
Geçerli bir #RRGGBB rengi gir.	Enter a valid #RRGGBB color.
RGB komutu gönderiliyor…	Sending RGB command…
OpenRGB komutu tamamlandı; ışıkları cihaz üzerinde kontrol et.	The OpenRGB command finished; check the lights on the device.
RGB ayarı uygulanamadı; aygıt erişimini kontrol et.	The RGB setting could not be applied; check device access.
Ölçüm okunamadı; yeniden denenecek.	The sample could not be read; it will be retried.
Canlı · 2 saniyede bir	Live · Every 2 seconds
Sıcaklık uyarısı	Temperature alert
Sıcaklık verisi yok	No temperature data
GPU telemetrisi kullanılamıyor	GPU telemetry is unavailable
Veri yok	No data
fan	fan
Duraklat	Pause
Sürdür	Resume
Duraklatıldı · Son ölçüm	Paused · Last sample
Dışa aktarmak için ilk ölçümü bekle.	Wait for the first sample before exporting.
Ölçümleri kaydet	Save measurements
Dosya kaydedildi.	File saved.
Dosya kaydedilemedi.	Could not save file.
Sürücü tarafından sunulan sensör bulunamadı.	No sensors were provided by the driver.
Uyarı eşiği bir bildirim tercihidir; donanımın güvenli sıcaklık sınırı değildir.	The alert threshold is a notification preference; it is not the hardware's safe temperature limit.
Yükselme	Rise
Düşme	Fall
balanced	Balanced
performance	Performance
power-saver	Power saver
Devir geçmişi için fan kanalı seçin.	Choose a fan channel to see speed history.
Canlı giriş, direksiyon ayarları ve oyun profilleri	Live input, wheel settings and game profiles
""".strip().splitlines()))

TEMPLATES.extend(tuple(line.split("\t", 1)) for line in """
{count} kontrol tamamlandı · {alerts} dikkat gerektiren bulgu · {unknown} kontrol edilemeyen alan	{count} checks completed · {alerts} findings need attention · {unknown} areas could not be checked
Etkin profil: {profile}	Active profile: {profile}
Kanal {channel}	Channel {channel}
Algılanan RGB aygıtı: {count}	RGB devices detected: {count}
Kanal {channel} · Devir geçmişi henüz yok.	Channel {channel} · No speed history yet.
Kanal {channel} · Son {seconds} sn: 1 ölçüm · {rpm} RPM · Değişim için yeni ölçüm bekleniyor.	Channel {channel} · Last {seconds} s: 1 sample · {rpm} RPM · Waiting for another sample to measure a change.
Kanal {channel} · Son {seconds} sn: {count} ölçüm · {range} RPM · Son değişim {delta} RPM / {elapsed} sn.	Channel {channel} · Last {seconds} s: {count} samples · {range} RPM · Latest change {delta} RPM / {elapsed} s.
Kanal {channel} · Sıfır RPM okumaları tekrarlandı: {zero} sıfıra geçiş / {resume} pozitif devre dönüş. Fan bağlantısını ve BIOS Q-Fan ayarını kontrol edin.	Channel {channel} · Zero RPM readings repeated: {zero} transitions to zero / {resume} returns to positive speed. Check the fan connection and BIOS Q-Fan setting.
Kanal {channel} · Devir belirgin biçimde dalgalandı: {count} yön değişimi. Fan ayrıntılarındaki sıcaklık kaynağı, tepki süresi ve toleransı inceleyin.	Channel {channel} · Speed fluctuated substantially: {count} changes of direction. Review the temperature source, response time and tolerance in the fan details.
Kanal {channel} · Kısa aralıklarla {count} belirgin devir değişimi okundu. Fan ayrıntılarındaki tepki süresini inceleyin.	Channel {channel} · {count} substantial speed changes were read in short intervals. Review the response time in the fan details.
{device}: {value} °C — {threshold} °C uyarı eşiği aşıldı.	{device}: {value} °C — the {threshold} °C alert threshold was exceeded.
""".strip().splitlines())

# Parameterized messages also support translator(source, **values).
TRANSLATIONS.update(TEMPLATES)

# SMART interpretation consists of a small set of known complete paragraphs.
_endurance = "Bu yüzde, üreticinin tahmini dayanıklılığından kalan payı gösterir; genel sağlık garantisi veya arıza olasılığı değildir."
_missing = "NVMe dayanıklılık yüzdesi alınamadı veya desteklenmiyor; kalan ömür tahmin edilmedi."
_exhausted = " Üreticinin dayanıklılık tahmini dolmuş görünüyor; bu tek başına SSD arızası anlamına gelmez."
_critical = " SMART kaydında ayrıca kritik uyarı bulunuyor; bu uyarı kalan ömür yüzdesinden bağımsızdır."
for _base in (_endurance, _missing):
    for _extra, _translated_extra in (
        (_exhausted, " The manufacturer's endurance estimate appears exhausted; this alone does not mean the SSD has failed."),
        (_critical, " The SMART record also contains a critical warning; it is independent of the remaining-endurance percentage."),
        (_exhausted + _critical, " The manufacturer's endurance estimate appears exhausted; this alone does not mean the SSD has failed. The SMART record also contains a critical warning; it is independent of the remaining-endurance percentage."),
    ):
        TRANSLATIONS[_base + _extra] = TRANSLATIONS[_base] + _translated_extra

TRANSLATIONS.update(dict(line.split("\t", 1) for line in """
DONANIM · ANVIL CONTROL	HARDWARE · ANVIL CONTROL
CSV kaydet	Save CSV
JSON raporu	JSON report
Rengi / modu uygula	Apply color / mode
Sakin	Quiet
Yüksek soğutma	High cooling
Ayar uygulanamadı; yetki ve servis durumunu kontrol et.	Could not apply the setting; check authorization and service status.
Güç profili güncellendi.	Power profile updated.
Fan yardımcısından geçerli doğrulama yanıtı alınamadı.	The fan helper did not return a valid verification response.
Fan yardımcısının geri okuma yanıtı uyuşmuyor.	The fan helper's readback response does not match.
Fan ayarının geri okuması eksik veya beklenen modda değil.	Fan-setting readback is missing or is not in the expected mode.
İstenen fan eğrisi doğrulama için bulunamadı.	The requested fan curve was not available for verification.
İstenen fan ayarı zaten etkin; donanımdan doğrulandı, yeniden yazılmadı.	The requested fan setting is already active; hardware readback verified it and no rewrite was performed.
Fan ayarı uygulandı ve donanımdan geri okunarak doğrulandı.	The fan setting was applied and verified through hardware readback.
Önemli dosyalarının yedeğini kontrol et ve kritik SMART uyarısını incele.	Check backups of important files and review the critical SMART warning.
Yedeklerini kontrol et; yoğun yazma kullanımını ve olası disk değişimini planla.	Check backups and plan for heavy write usage and possible disk replacement.
Cihaz ayarları okunuyor…	Reading device settings…
Yükleniyor	Loading
""".strip().splitlines()))

_critical_actual = " SMART kaydında ayrıca kritik uyarı bulunuyor; kalan ömür yüzdesinden bağımsız değerlendirilmelidir."
_unknown_warning = " Kritik SMART uyarılarının durumu doğrulanamadı."
for _base in (_endurance, _missing):
    for _extra, _english in (
        (_critical_actual, " The SMART record also contains a critical warning; evaluate it independently of the remaining-endurance percentage."),
        (_unknown_warning, " The status of critical SMART warnings could not be verified."),
        (_exhausted + _critical_actual, " The manufacturer's endurance estimate appears exhausted; this alone does not mean the SSD has failed. The SMART record also contains a critical warning; evaluate it independently of the remaining-endurance percentage."),
        (_exhausted + _unknown_warning, " The manufacturer's endurance estimate appears exhausted; this alone does not mean the SSD has failed. The status of critical SMART warnings could not be verified."),
    ):
        TRANSLATIONS[_base + _extra] = TRANSLATIONS[_base] + _english
TEMPLATES.append(("Fan işlemi başarısız: {error}", "Fan operation failed: {error}"))
TRANSLATIONS.update(TEMPLATES)
TRANSLATIONS["Renk seç"] = "Choose color"

# Shared redesign and official per-module distribution pages.
TRANSLATIONS.update(dict(line.split("\t", 1) for line in """
TERCİHLER	PREFERENCES
Klavye kısayolları	Keyboard shortcuts
Bu bölümün indirme sayfası	Downloads for this module
{app} indirme sayfası	{app} download page
İndirmeler	Downloads
İNDİRME MERKEZİ	DOWNLOAD CENTER
Panele dön	Back to dashboard
Anvil Control’ün bağımsız sürümünü ve resmî Linux paketlerini burada bulabilirsin.	Find the standalone Anvil Control release and official Linux packages here.
Wheel Control’ün bağımsız sürümü, kurulum paketleri ve kaynak kodu.	The standalone Wheel Control release, installation packages and source code.
Uzeyir Doctor ile donanım, direksiyon ve sistem teşhisini birlikte indir.	Download hardware, wheel controls and system diagnostics together with Uzeyir Doctor.
Birleşik uygulama	Combined application
Bağımsız uygulama	Standalone application
Ön sürüm	Preview release
Yayımlanan sürüm	Published release
Sürüm sayfası	Release page
Güncel sürümü kontrol et	Check for a newer release
Paket bilgileri bu sürümle birlikte gelir. Güncel sürümü istediğinde kontrol edebilirsin.	Package details are included with this version. You can check for a newer release whenever you want.
Paket seç	Choose package
Fedora · RPM	Fedora · RPM
Debian / Ubuntu · DEB	Debian / Ubuntu · DEB
Taşınabilir	Portable
Kaynak paketleri	Source packages
Kaynak RPM	Source RPM
İndir	Download
İndirdikten sonra	After downloading
Terminali indirilen dosyanın bulunduğu klasörde aç. Komutu kendin çalıştırabilirsin.	Open a terminal in the downloaded file’s folder. You can run this command yourself.
Kopyala	Copy
Komut kopyalandı	Command copied
Kaynak kod	Source code
Tüm sürümler	All releases
Sorun bildir	Report an issue
İndirme bağlantıları tarayıcıda açılır. Bu sayfa paket kurmaz veya sistem izinlerini değiştirmez.	Download links open in your browser. This page does not install packages or change system permissions.
Bu sürümde paket bulunamadı. Tüm sürümler sayfasını açabilirsin.	No package was found in this release. You can open the all releases page.
Bağlantı açılamadı. Varsayılan tarayıcını kontrol et.	Could not open the link. Check your default browser.
GitHub’daki sürüm kontrol ediliyor…	Checking the release on GitHub…
Güncel sürüm alınamadı. Kayıtlı bağlantıları kullanabilir veya daha sonra tekrar deneyebilirsin.	Could not fetch the latest release. You can use the included links or try again later.
Sürüm ve paket bağlantıları GitHub’dan güncellendi.	Release and package links were updated from GitHub.
Sistemin, canlı.	Your system, live.
Kullanımı, sıcaklıkları ve fanları tek bakışta takip et.	Track usage, temperatures and fans at a glance.
Sürüşü kendine uyarla.	Make the drive yours.
Canlı direksiyon girişi, hassas ayarlar ve oyun profillerin.	Live wheel input, precise settings and your game profiles.
USB ile bağla. Ayarlarını seç. Hazır olduğunda uygula.	Connect over USB. Choose your settings. Apply when ready.
Direksiyonunu bağla.	Connect your wheel.
Henüz bir direksiyon algılanmadı. Bağlandığında canlı giriş ve desteklenen ayarlar burada açılır.	No wheel has been detected yet. Live input and supported settings will appear here when it connects.
İlk bağlantı	First connection
USB bağlantısı	USB connection
Direksiyonu bilgisayara USB ile bağla; gerekiyorsa güç adaptörünü tak.	Connect the wheel over USB and plug in its power adapter if required.
Doğru çalışma modu	The right mode
Modelinin Linux için desteklediği modu seç. Logitech G29 için PS3 konumunu kullan.	Select your model’s supported Linux mode. Use the PS3 position for a Logitech G29.
Kendi profilin	Your own profile
Algılandıktan sonra bir oyun profili seç. Ayarlar yalnız Uygula dediğinde yazılır.	Once detected, choose a game profile. Settings are written only when you choose Apply.
Demo, arayüzü denemek içindir; gerçek direksiyon verisi veya cihaz testi değildir.	The demo lets you explore the interface; it is not real wheel data or a hardware test.
Sorunu gör. Çözümü bul.	See the issue. Find a fix.
Sistemini tara; ne olduğunu ve sonraki adımı açıkça gör.	Scan your system and see clearly what is happening and what to do next.
Tamamlanan kontrol	Completed checks
Dikkat gerektiren	Need attention
Doğrulanamayan	Unverified
Tarama sonuçları	Scan results
Dikkat gerektirenler	Need attention
İlk kontrolü başlat.	Start your first check.
Disk, SSD, servisler, ağ ve depolar için bulgular burada görünecek.	Findings for disks, SSDs, services, networking and repositories will appear here.
Kontroller bu bilgisayarda çalışır. Sonuçlar dışarı gönderilmez.	Checks run on this computer. Results are not sent anywhere.
Dikkat gerektiren bulgu yok.	No findings need attention.
Diğer kontrolleri görmek için filtreyi kapatabilirsin.	Turn off the filter to see the other checks.
""".strip().splitlines()))

TRANSLATIONS["Uzeyir Doctor’ün bağımsız uygulamasını ve Linux kurulum paketlerini indir."] = "Download the standalone Uzeyir Doctor application and Linux installation packages."
TRANSLATIONS["Sorunları anlaşılır biçimde gör."] = "Understand system issues clearly."
