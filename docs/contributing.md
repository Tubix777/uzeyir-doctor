# Katkı rehberi / Contributing

Uzeyir Doctor için hata düzeltmeleri, çeviriler ve tekrarlanabilir arayüz iyileştirmeleri
kabul edilir. Önce [AGENTS.md](../AGENTS.md), [plan](../PLAN.md) ve
[doğrulama kapsamını](validation.md) oku.

## Yerel çalışma

1. Depoyu klonla ve değişikliğin için ayrı bir dal aç.
2. [Kurulum rehberindeki](install.md) sistem GTK/Python bağımlılıklarını kur.
3. `./run.sh` ile normal kullanıcı olarak çalıştır.
4. Değişen davranışı Türkçe ve İngilizce, dar/geniş pencere ve hareket azaltma ile dene.
5. İlgili testleri çalıştır. GUI için `packaging/run_checks.sh` ayrı bir Weston
   compositor başlatır; gerçek masaüstündeki ayarları veya cihazları değiştirmez.

## Arayüz ve davranış

- Siyah/gri/beyaz paleti, Manrope tipografisini, görünür klavye odağını koru.
- Animasyonlar kesilince son seçim doğru görünmeli; giriş değerleri kaybolmamalı.
- Dil değişimi açık ayrıntıları ve kaydedilmemiş kullanıcı seçimlerini korumalı.
- Ölçüm, ağ ve dosya işlerini GTK ana döngüsünde çalıştırma.
- Tanılama salt okunur; veri yoksa uydurma yüzde veya ilerleme gösterme.
- İşlem başarısını gerçek sonuçla doğrula. Hata ve iptal akışlarını da ele al.
- Ekran kayıtlarında temsili veri kullan; kişisel sistem günlüklerini commit etme.

## Pull request

Somut sorunu, önce/sonra davranışını, test sonucunu ve kalan sınırları açıkla.
Görsel bir değişiklikte temsili verilerle ekran görüntüsü veya kısa kayıt ekle.
Testin bir davranış hatasını yakalaması gerekir; yalnız uygulama kodunu tekrar eden
testler ekleme. Hata düzeltmesine ilgili regresyon testi eklemek yararlıdır.

## Yayın

Sürüm, `pyproject.toml`, Python sürüm sabiti ve RPM tanımıyla tutarlı olmalı.
`source-date-epoch` yeni yayın zamanı için ilerletilir. Kaynak arşivi bir kez
üretilir; bütün dağıtımlar aynı arşivden paketlenir. CI kurulu uygulamanın dosyalarını,
SVG'lerini, sayfalarını ve güncelleme penceresini ayrı compositor altında açar.

Etiket yayını DEB, RPM, kaynak RPM, Arch paketi, sabit kaynaklı Arch derleme tarifi,
kaynak arşivi ve `SHA256SUMS` üretir. Sürüm notları değişiklikleri, kurulumu ve
sınırlamaları açıklamalıdır. Gerçek donanım ve yetkilendirme testleri ile konteyner
kontrolleri birbirinin yerine sunulmaz.

## English

Keep changes focused, preserve Turkish/English and reduced-motion behavior, and
run the relevant checks. Use synthetic data in public screenshots. Explain the
problem, resulting behavior, validation and remaining limits in pull requests.
Release artifacts must share one canonical source archive. Read the project rules
before changing device access, diagnostics or the updater.
