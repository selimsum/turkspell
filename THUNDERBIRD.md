# Turkspell Thunderbird Dağıtım ve Yayınlama Rehberi

Bu kılavuz, **Turkspell** Türkçe yazım denetimi sözlüğünün **Mozilla Thunderbird** için paketlenmesi, [addons.thunderbird.net (ATN)](https://addons.thunderbird.net/) üzerinde listelenmesi ve kullanıcılara sunulması süreçlerini adım adım açıklar.

---

## 1. Genel Bakış ve Uyumluluk

Turkspell, Thunderbird için modern WebExtension / MailExtension sözlük mimarisine tam uyumlu olarak hazırlanmıştır.

* **Minimum Desteklenen Sürüm:** Thunderbird 68.0+ (Thunderbird 102, 115 "Supernova", 128 "Nebula" ve üzeri) ile SeaMonkey 2.53.24+ (Gecko 60.0+ altyapısı).
* **Doğrulama Durumu:** Mozilla `addons-linter` ve `web-ext lint` araçları ile doğrulanmış, 0 hata ve 0 uyarı ile tam uyumludur.
* **Sunulan Profiller:**
  1. **Evrensel Profil (`turkspell-thunderbird.xpi`):** Hem TDK hem Dil Derneği kurallarını kapsayan geniş hazneli sözlük.
  2. **TDK 2026 Resmî Profil (`turkspell-thunderbird-tdk.xpi`):** Yalnızca Türk Dil Kurumu'nun güncel yazım kurallarını ve düzeltme işaretlerini içeren resmî sözlük.

---

## 2. Dağıtım Paketlerinin Üretimi

Eklenti paketlerini yerel ortamda üretmek için `build/package_addon.py` betiği kullanılır:

```bash
# Sadece Thunderbird paketlerini veya tüm profilleri paketlemek için:
python build/package_addon.py --profile all
```

Üretilen dosyalar:
* `turkspell-thunderbird.xpi` (Evrensel sözlük paketi)
* `turkspell-thunderbird-tdk.xpi` (TDK resmî sözlük paketi)

Paketlerin geçerliliğini doğrulamak için:
```bash
npx addons-linter turkspell-thunderbird.xpi
```

---

## 3. addons.thunderbird.net (ATN) Üzerinden Dağıtım Adımları

### Adım 1: Developer Hub Hesabı ile Giriş Yapın
1. Tarayıcınızda [https://addons.thunderbird.net/developers/](https://addons.thunderbird.net/developers/) adresine gidin.
2. Sağ üstte yer alan **Giriş Yap (Log in)** düğmesine tıklayarak Mozilla / Thunderbird hesabınızla oturum açın (hesabınız yoksa aynı ekrandan ücretsiz oluşturabilirsiniz).

### Adım 2: Yeni Eklenti Gönderimi Başlatın
1. Geliştirici panelinde **"Submit a New Add-on"** (Yeni Bir Eklenti Gönder) bağlantısına tıklayın.
2. Dağıtım kanalı seçeneğinde:
   * **"On this site" (Bu sitede yayınlansın):** Kullanıcıların doğrudan Thunderbird içindeki Eklenti Yöneticisinden veya addons.thunderbird.net sitesinden tek tıkla arayıp yükleyebilmesi için bu seçeneği seçin.
3. **Sözleşmeyi Onaylayın:** Thunderbird Geliştirici Dağıtım Sözleşmesini onaylayıp devam edin.

### Adım 3: `.xpi` Paketini Yükleyin
1. **Dosya Seç:** Bilgisayarınızdaki `turkspell-thunderbird.xpi` dosyasını seçin ve yükleyin.
2. **Otomatik İnceleme:** ATN doğrulama motoru paketinizi tarar (`manifest.json`, `dictionaries/tr.dic`, `dictionaries/tr.aff`).
3. Herhangi bir hata veya uyarı çıkmadan doğrulama başarıyla tamamlanacaktır.

### Adım 4: Eklenti Mağaza Bilgilerini Doldurun

Sayfada yer alan alanları aşağıdaki hazır metaveriler ile doldurabilirsiniz:

#### Temel Bilgiler:
* **Eklenti Adı (Name):** `Turkspell - Türkçe Yazım Denetimi`
  *(TDK profili için: `Turkspell - Türkçe Yazım Denetimi (TDK 2026)`)*
* **Kategori (Category):** `Dictionaries & Language Packs` (Sözlükler ve Dil Paketleri)
* **Desteklenen Diller:** `Türkçe (Turkish)`
* **Lisans:** `MIT License`
* **Proje / Ana Sayfa URL:** `https://github.com/selimsum/turkspell`

#### Kısa Özet (Summary - En fazla 250 karakter):
```text
Hem Türk Dil Kurumu hem Dil Derneği kurallarını destekleyen evrensel, modern Türkçe yazım denetimi sözlüğü.
```
*(TDK profili için: `Sadece Türk Dil Kurumu (TDK 2026) güncel kurallarını ve sözlüğünü esas alan resmî Türkçe yazım denetimi eklentisi.`)*

#### Detaylı Açıklama (Description - Markdown):
```markdown
### Turkspell - Thunderbird Türkçe Yazım Denetimi

Turkspell, Mozilla Thunderbird için geliştirilmiş modern, yüksek doğruluklu ve düşük bellek tüketimli Türkçe imla denetimi sözlüğüdür.

#### Öne Çıkan Özellikler:
* **Çift Standart Uyumu:** Hem Türk Dil Kurumu (TDK) hem de Dil Derneği kurallarını kapsayan evrensel sözlük haznesi.
* **Zengin Morfoloji:** Fiil çekimleri, bileşik sözcükler, yapım ekleri ve türetilmiş formlarda yüksek doğruluk.
* **Düşük Yanlış Alarm Oranı:** Günlük ve resmî yazışmalarda doğru sözcükleri yanlış işaretlemez, akıcı bir yazım deneyimi sağlar.
* **Gizlilik Odaklı ve Çevrimdışı:** Yazışmalarınız herhangi bir uzak sunucuya gönderilmez, denetim tamamen yerel olarak bilgisayarınızda gerçekleşir.

#### Thunderbird'de Nasıl Aktifleştirilir?
1. Eklentiyi kurun ve Thunderbird'ü yeniden başlatın (gerekirse).
2. Yeni bir e-posta yazma penceresi açın (**İleti Yaz**).
3. Üst menüden **Seçenekler -> Yazım Denetimi -> Diller** yolunu izleyin (veya metin alanına sağ tıklayın).
4. Listeden **Türkçe** seçeneğini işaretleyin.
```

#### Etiketler (Tags):
`türkçe`, `yazım denetimi`, `sözlük`, `imla`, `turkish`, `spellcheck`, `dictionary`, `tdk`

### Adım 5: İncelemeye Gönderin
* Bilgileri tamamladıktan sonra **"Submit Version"** düğmesine tıklayın.
* Sözlük eklentileri genellikle kısa bir otomatik onay sürecinin ardından Thunderbird eklenti dizininde kamuya açık olarak yayınlanır.

---

## 4. Kullanıcı Kurulumu ve Testi

### A. Yerel `.xpi` Dosyasıyla Test Etme
1. Thunderbird uygulamasını açın.
2. Sağ üstteki hamburger menüden veya `Araçlar` menüsünden **Eklentiler ve Temalar** (Add-ons and Themes) sekmesini açın.
3. Sağ üstteki **Çark (Ayarlar)** simgesine tıklayın ve **"Dosyadan Eklenti Kur..."** (Install Add-on From File) seçeneğini seçin.
4. `turkspell-thunderbird.xpi` dosyasını seçin ve gelen uyarıda **Ekle** düğmesine tıklayın.

### B. E-posta Yazarken Yazım Denetimini Kullanma
1. Thunderbird ana penceresinden **"Yeni İleti"** (Write) düğmesine basın.
2. E-posta gövdesine Türkçe metin yazın.
3. Yazım denetiminin devrede olduğunu doğrulamak için metin alanına sağ tıklayıp **"Yazım Denetimi" -> "Türkçe"** seçeneğinin işaretli olduğunu kontrol edin.
4. Hatalı yazılan kelimelerin altı kırmızı dalgalı çizgiyle çizilecek, sağ tıklandığında Turkspell'in doğru Türkçe önerileri listelenecektir.

---

## 5. SeaMonkey ile Kullanım

* **SeaMonkey 2.53.24 ve Üzeri:**
  Modern SeaMonkey sürümleri WebExtension sözlüklerini destekler. `turkspell-thunderbird.xpi` veya `turkspell-addon.xpi` paketini SeaMonkey Eklenti Yöneticisi (`about:addons`) üzerinden *"Dosyadan Eklenti Yükle..."* seçeneğiyle doğrudan kurabilirsiniz.

* **Eski SeaMonkey Sürümleri (2.53.1 - 2.53.23 veya 2.49):**
  Eski sürümlerde WebExtension sözlük API'si bulunmadığından, `dist/turkspell-universal/` (veya repo kökündeki) `tr.aff` ve `tr.dic` dosyalarını doğrudan SeaMonkey profilinizdeki `dictionaries/` klasörüne kopyalayarak kullanabilirsiniz:
  - **Windows:** `%APPDATA%\Mozilla\SeaMonkey\Profiles\<profil_adı>\dictionaries\`
  - **Linux:** `~/.mozilla/seamonkey/<profil_adı>/dictionaries/`
  - **macOS:** `~/Library/Application Support/SeaMonkey/Profiles/<profil_adı>/dictionaries/`
