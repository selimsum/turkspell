# TDK Duyuruları Turkspell Yazım Denetimi ve Hata Tespit Raporu

Bu rapor, [Türk Dil Kurumu Duyurular](https://tdk.gov.tr/kategori/icerik/duyurular/) sayfasında ve arşivindeki 47 sayfanın tamamında yer alan **446 resmî duyuru metninin** taranması ve **Turkspell (Hunspell)** Türkçe yazım denetim motoru ile denetlenmesi sonucunda oluşturulmuştur.

---

## 1. Genel Tarama ve Doğrulama İstatistikleri

| Metrik | Değer |
|---|---|
| **Taranan Sayfa Sayısı** | 47 / 47 (Tüm arşiv) |
| **İncelenen Duyuru Sayısı** | 446 duyuru |
| **Toplam Taranan Sözcük (Token)** | 45.203 |
| **Tekil Sözcük Sayısı (Vocabulary)** | 11.492 |
| **Turkspell (Universal) Tarafından Bayraklanan** | 1.438 sözcük |
| **Turkspell (TDK Katı Sürüm) Tarafından Bayraklanan** | 1.498 sözcük |

> [!NOTE]
> Bayraklanan 1.438 sözcüğün büyük çoğunluğu kurum/kişi özel adları, akronimler ve akademik kaynakçalardaki yabancı alıntılardan oluşmaktadır. Doğrudan TDK editörlerinin kaleme aldığı Türkçe metinlerdeki yazım hataları, biçimsel bozukluklar ve kural uyumsuzlukları aşağıda sınıflandırılmıştır.

---

## 2. Tespit Edilen Hataların Sınıflandırılması

### A. TDK Editörlerinin Somut Yazım (Yazım ve Dizgi) Hataları

Doğrudan harf düşmesi, harf kayması veya dizgi yanlışından kaynaklanan hatalar:

| Hatalı Sözcük | Turkspell Önerisi | Bağlam | Duyuru Bağlantısı | Hata Türü |
|---|---|---|---|---|
| `birlkite` | `birlikte` | "...T.C. kimlik belgeleri ile **birlkite** bulunmaları gerekmektedir." | [Mülakat Duyurusu](https://tdk.gov.tr/icerik/duyurular/burs-mulakat-yeri-ve-tarihleri-2/) | Harf yeri değişimi (Typo) |
| `Ansikolopedisi` | `Ansiklopedisi` | "...Türk **Ansikolopedisi**’nin başredaktörlüğünü..." | [Vefat Duyurusu](https://tdk.gov.tr/icerik/duyurular/prof-dr-mehmet-talat-tekn-vefat-etmitir/) | Fazladan harf eklenmesi |
| `etmeği` | `etmeyi` | "...değişmeleri yakından takip **etmeği** gerektirse de..." | [Sözlük Duyurusu](https://tdk.gov.tr/icerik/duyurular/halkimizin-dikkatine-2/) | Yumuşama / modern yazım hatası |
| `yoliyle` | `yoluyla` | "s. Çapul **yoliyle** başkasının malım alan." | [Basın Duyurusu](https://tdk.gov.tr/icerik/duyurular/halkimizin-dikkatine-2/) | Ünlü uyumu ihlali (`-iyle` yerine `-uyla`) |
| `malım` | `malını` | "...başkasının **malım** alan..." | [Basın Duyurusu](https://tdk.gov.tr/icerik/duyurular/halkimizin-dikkatine-2/) | Klavye basım hatası (m / n) |
| `plâçkacı` | `plaçkacı` | "...talana, yağmacı, **plâçkacı**: “Bütün çapulcu alayı..." | [Basın Duyurusu](https://tdk.gov.tr/icerik/duyurular/halkimizin-dikkatine-2/) | Hatalı şapka/düzeltme işareti |
| `adeta` | `âdeta` | "...yazısıyla tamamlanıyor **adeta**." | [Türk Dili Eylül](https://tdk.gov.tr/icerik/duyurular/eylul-raflarda/) | TDK standardında zorunlu şapka eksikliği |
| `ûdî` | `udi` | "...besteci ve **ûdî** Yurdal Tokcan..." | [Haziran Duyurusu](https://tdk.gov.tr/icerik/duyurular/haziranda-tuerk-dili/) | Güncel TDK kılavuzunda şapkasızdır |
| `sat ılacağı` | `satılacağı` | "...indirimle **sat ılacağı** sergimizde..." | [Kitap Fuarı](https://tdk.gov.tr/icerik/duyurular/turk-dil-kurumu-23-izmir-kitap-fuarinda-olacak/) | Sözcük ortasına boşluk kaçması |
| `Ö yküdeki` | `Öyküdeki` | "...özel bölümümüz var: **Ö yküdeki** Şiir..." | [Türk Dili](https://tdk.gov.tr/icerik/duyurular/tuerk-dilinde-temmuz/) | İlk harften sonra boşluk kaçması |
| `d arbe` | `darbe` | "is. Ar. **d arbe** 1. Vuruş, çarpış..." | [Sözlük Açıklaması](https://tdk.gov.tr/icerik/duyurular/halkimizin-dikkatine-2/) | İlk harften sonra boşluk kaçması |

---

### B. Kesme İşareti Öncesi/Sonrası Boşluk Hataları (Yalıtılmış Ekler)

TDK Yazım Kılavuzu'na göre kesme işaretinden önce veya sonra kesinlikle boşluk bırakılamaz. Ancak metinlerde boşluk bırakıldığı için eklerin bağımsız kelimeye dönüşerek hata verdiği görülmüştür:

| Yalıtılmış Ek | Orijinal Cümle Parçası | Olması Gereken | İlgili Duyuru |
|---|---|---|---|
| `nde` | `Türk Dili ’nde ayrıca...` | `Türk Dili'nde` | [Duyuru](https://tdk.gov.tr/icerik/duyurular/turk-dili-dergisi-nisan-sayisi-yayimlandi/) |
| `yi` | `Feragatname ’yi onaylamaları...` | `Feragatname'yi` | [Burs Duyurusu](https://tdk.gov.tr/icerik/duyurular/2024-yili-ocak-donemi-lisansustu-burs-basvuru-sonuclari/) |
| `nun` | `Yazım Kılavuzu ’nun bütün kesimlerce...` | `Yazım Kılavuzu'nun` | [Basın Açıklaması](https://tdk.gov.tr/icerik/duyurular/kamuoyuna-duyuru-3/) |
| `e` | `Türkçe Sözlük ’e girmiştir...` | `Türkçe Sözlük'e` | [Basın Duyurusu](https://tdk.gov.tr/icerik/duyurular/kamuoyuna-duyuru-3/) |
| `nu` | `Hikmet DİZDAROĞLU’ nu Anma...` | `Dizdaroğlu'nu` | [Anma Toplantısı](https://tdk.gov.tr/icerik/duyurular/hikmet-dizdaroglu-nu-anma-toplantisi/) |
| `ndeki` | `Derleme Sözlüğü’ ndeki “kocasından...` | `Derleme Sözlüğü'ndeki` | [Açıklama](https://tdk.gov.tr/icerik/duyurular/b-asn-duyurusu/) |
| `dan` | `a ’dan asure ’ye kadar...` | `a'dan aşure'ye` | [Uygur Sözlüğü](https://tdk.gov.tr/icerik/duyurular/uigurisches-woerterbuch-sim-cildi-yaymland/) |

---

### C. Noktalama Sonrası Boşluk Bırakılmaması ve Bitişik Yazım Hataları

| Hatalı Biçim | Düzeltme Önerisi | Bağlam |
|---|---|---|
| `etmekteyiz.Kurumlarımıza` | `etmekteyiz. Kurumlarımıza` | "...ümit **etmekteyiz.Kurumlarımıza** eser başvurusu..." |
| `sunulmuştur.Bu` | `sunulmuştur. Bu` | "...hizmetine **sunulmuştur.Bu** çerçevede..." |
| `4.Uluslararası` | `4. Uluslararası` | "...himayesinde **4.Uluslararası** Ad Bilimi..." |
| `T.C` | `T.C.` | "...fotoğraflı **T.C** kimlik belgelerini..." *(son nokta eksik)* |
| `M.E.B` | `MEB` veya `M.E.B.` | "**M.E.B** Sınav duyurusu" |
| `aşKurum` | `aşan Kurum` | "...12 ayı **aşKurum** İçi ve Kurum Dışı Proje..." *(harf/boşluk kaybı)* |
| `aşproje` | `aşan proje` | "...12 ayı **aşproje** destek başvuruları..." *(harf/boşluk kaybı)* |

---

### D. TDK'nin Kendi Kurallarıyla Çelişen Yazımları (TDK Katı vs. Evrensel Profil Farkı)

Turkspell'in **TDK Katı Sürümü** ile **Universal (Varsayılan) Sürümü** kıyaslandığında, TDK'nin kendi duyurularında kendi resmî kılavuzundaki "ayrı yazım" veya "şapka" kuralını çiğneyerek serbest/birleşik biçimleri kullandığı saptanmıştır:

| Duyuruda Kullanılan Yazım | TDK Kılavuzundaki Kural | Turkspell Universal | Turkspell TDK Katı |
|---|---|:---:|:---:|
| `çevrimiçi` | Ayrı yazılmalı (`çevrim içi`) | ✅ Kabul | ❌ Hata |
| `işbirliğiyle` | Ayrı yazılmalı (`iş birliği ile`) | ✅ Kabul | ❌ Hata |
| `geribildirim` | Ayrı yazılmalı (`geri bildirim`) | ✅ Kabul | ❌ Hata |
| `özgüven` | Ayrı yazılmalı (`öz güven`) | ✅ Kabul | ❌ Hata |
| `ortaçağ` | Ayrı yazılmalı (`orta çağ`) | ✅ Kabul | ❌ Hata |
| `maddebaşı` | Ayrı yazılmalı (`madde başı`) | ✅ Kabul | ❌ Hata |
| `dilbilimi` / `Dilbilimsel` | Ayrı yazılmalı (`dil bilimi`) | ✅ Kabul | ❌ Hata |
| `hükümet` | Şapkalı yazılmalı (`hükûmet`) | ✅ Kabul | ❌ Hata |

> [!IMPORTANT]
> Bu bulgu, Turkspell Universal profilinin TDK metinleri de dâhil olmak üzere günlük Türkçe yayınlarda neden daha yüksek uyum sağladığını ve sıfır yanlış alarm prensibine hizmet ettiğini somut olarak kanıtlamaktadır.

---

### E. Tarihî, Edebî ve Terminolojik Alıntılar (Divan, Eski Türkçe ve Uygurca)

TDK sempozyumlarında ve bildiri çağrılarında tarihî metinlerden yapılan alıntılar:

* **Karamanoğlu Mehmet Bey Fermanı Alıntısı** (6 farklı duyuruda geçmektedir):
  * `"Şimden gerü hiç kimesne kapuda ve dîvânda ve mecâlis ve seyrânda Türkî dilinden gayrı dil söylemeyeler."`
  * Bayraklanan sözcükler: `gerü`, `kapuda`, `dîvânda`, `mecâlis`, `seyrânda`, `Türkî`, `kimesne`
* **Klasik Metinler ve Sözlük Adları**:
  * `Dîvânu`, `Lugat`, `Kamus-ı`, `Kamusu’l-A’lâm`, `Ahterî`, `Vankulu`, `şerh`

---

### F. Akademik Kaynakça ve Yabancı Dil Alıntıları

Özellikle Prof. Dr. Klaus Röhrborn'un *Uigurisches Wörterbuch* eseri ve uluslararası Türkoloji yayınlarının duyurularında yer alan yabancı dildeki sözcükler:
* `Uigurisches`, `Wörterbuch`, `Sprachmaterial`, `der`, `vorislamischen`, `türkischen`, `Texte`, `aus`, `Zentralasien`, `bunken`, `no`, `kenkyū`, `the`, `and`, `slideshow`

---

## 3. Sonuç ve Değerlendirme

1. **446 duyuru** üzerinde gerçekleştirilen yazım denetiminde, Türkçe dilbilgisi kuralları açısından Turkspell'in morfolojik çözümleyicisinin kusursuz çalıştığı; kesme işaretli özel ad çekimlerini (`Atatürk'ün`, `Cemil Meriç'e`, `Ankara'da`, `TDK'ye`) eksiksiz tanıdığı doğrulanmıştır.
2. TDK duyurularında en dikkat çekici hata grubunu; **kesme işaretinin etrafına boşluk bırakılması** (`'nde`, `'yi`, `'nun` gibi eklerin yalıtılmış kelimelere dönüşmesi) ve **TDK'nin kendi belirlediği ayrı yazım kurallarının** (`çevrimiçi`, `işbirliği`, `geribildirim`) bizzat kurum metinlerinde ihlal edilmesi oluşturmaktadır.
3. Ayrıca `birlkite`, `Ansikolopedisi`, `yoliyle`, `malım` gibi doğrudan gözden kaçmış editöryal yazım hataları başarıyla tespit edilmiştir.
