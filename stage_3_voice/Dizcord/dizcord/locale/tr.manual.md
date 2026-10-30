=== 1. Hoş geldin
# Dizcord'a hoş geldin

Dizcord, Discord ve diğer tüm sesli sohbetler için gerçek zamanlı bir çevirmendir. Tamamen senin bilgisayarında
çalışır.

- **Diğerlerini kendi dilinde duyarsın.** Uygulama Discord'da insanların söylediklerini dinler, yazıya döker,
  çevirir, altyazı gösterir ve çeviriyi sana doğal bir sesle okuyabilir.
- **Onlar seni kendi dillerinde duyar.** Mikrofona konuşursun. Uygulama söylediğini çevirir ve bir sanal ses
  kablosu üzerinden Discord'da söyler.
- **Metin de çevrilir.** Sunuculardaki, özel mesajlardaki ve alt başlıklardaki Discord mesajlarını, fareyle
  seçtiğin her metni ve OCR ile ekrandaki metni çevirir. Onların dilinde de yazabilirsin.
- **Başlamak ücretsiz.** Ücretsiz, anahtarsız profili hesap ve ödeme olmadan çalışır. Ücretli bulut motorları
  isteğe bağlıdır.

Bu kılavuzun on iki bölümü var. Sonraki ve Önceki düğmelerini kullan ya da listeden bir bölüme tıkla. Her bölüm
değiştirdiğinde anlatıcı eskisini bırakır ve yenisini okur. Ses, uygulamanın dilinde bilgisayarında çalışan doğal
bir sestir. İnternet gerektirmez ve ücretsizdir.

=== 2. İlk başlatma
# İlk başlatma

**Adım 1. Uygulamayı aç.** Dizcord.exe'ye ya da Dizcord.bat'a çift tıkla. İlk seferde uygulama kendi klasörünün
içinde kendine ait bir Python kopyası kurar. Bu yaklaşık 750 megabayt indirir, birkaç dakika sürer ve yönetici
izni gerektirmez. Windows'a hiçbir şey kurulmaz.

Sonra uygulamanın dilini seçersin. Her şey o dilde görünür, rehber ve bu kılavuz da o dilde sesli okunur.
Uygulama o dilin sesini bir kez indirir, yaklaşık 60 megabayt. Ardından kısa bir rehberli tur ilk adımları
gösterir. Yalnızca bu ilk seferde açılır; bu sekmeden tekrar izleyebilirsin.

**Adım 2. Bir sanal ses kablosu kur.** Ücretsiz olan VB-Audio Virtual Cable'ı kur ve bilgisayarı yeniden başlat.
Klasörün dışındaki tek şey budur, çünkü Windows'un sanal bir mikrofon oluşturmak için bir sürücüye ihtiyacı vardır.

**Adım 3. Discord'u ayarla.** Discord'u aç, sonra Kullanıcı Ayarları, sonra Ses ve Görüntü.

- Giriş Aygıtı: VB-Audio Virtual Cable'dan CABLE Output.
- Çıkış Aygıtı: kulaklığın.
- Gürültü Azaltma, Yankı Engelleme ve Otomatik Kazanç Kontrolü'nü kapat.

**Adım 4. Uygulamayı ayarla.** Ücretsiz, anahtarsız profilini seç. Çıkış sekmesinde çevrilmiş sesini CABLE Input'a
gönder. Giriş sekmesinde Sadece Discord uygulaması yöntemini bırak ve gerçek mikrofonunu seç. Canlı sekmesinde
dilleri seç. Sonra Başlat'a ya da F5 tuşuna bas.

Konuşma modeli Whisper small yaklaşık 460 megabayttır ve ilk kullanımda indirilir.

=== 3. Ana pencere
# Ana pencere

En üstte profil kutusu var. Bir profil motorlar, diller ve aygıtlarla ilgili tüm ayarlarını saklar. Profilleri
kaydedebilir, farklı kaydedebilir, silebilir, içe ve dışa aktarabilirsin. Dışa aktarılan profiller asla API
anahtarlarını içermez.

Değişikliklerin yaptıktan yaklaşık bir saniye sonra otomatik kaydedilir. Bunu Ayarlar sekmesinden kapatabilirsin.

Profil kutusunun yanında üç düğme var:

- **Altyazılar**, sürükleyebileceğin, fare tekerleğiyle boyutlandırabileceğin ve sağ tıkla ayarlayabileceğin yüzen
  bir altyazı penceresi gösterir.
- **Sohbet**, Discord metin mesajlarının çevirisini açar.
- **Başlat**, ses çevirmenini başlatır. F5 tuşu da aynı işi yapar.

Sekmeler şunlar: Pano, Canlı, Metin, Giriş, Çıkış, Konuşma, Çeviri, Yapay zekâ modeli, Ses, API anahtarları,
Kurulum, Ayarlar, Kılavuz ve Günlük. Sonraki bölümler en çok kullanacaklarını anlatır.

=== 4. Pano
# Pano

Pano senin kontrol merkezindir. İlk sekmedir ve her şeyi tek bakışta gösterir.

- **Ses çevirmeni kartı** canlı ses çevirisini başlatır ve durdurur, ne yaptığını gösterir: tanıma, çeviri ya da
  konuşma.
- **Sohbet çevirisi kartı** Discord mesajlarının çevirisini başlatır ve durdurur. Çevrilen mesajları sırayla ya da
  yeni bir mesajın okunanı bölmesine izin vererek sesli okuma seçeneği de vardır.
- **Sen kartı**, Discord adını ve yazdığın dili girdiğin yerdir.
- **Araçlar kartı**, seçerek çeviri, OCR ve altyazı penceresi için kısayollar içerir.
- **Kısayollar kartı** klavye kısayollarını hatırlatır.
- Altta Son çeviriler, son çevrilen satırları gösterir.

İki yerde görünen ayarlar, örneğin Pano'da ve Metin sekmesinde olanlar, her zaman eşit kalır.

=== 5. Canlı ses çevirisi
# Canlı ses çevirisi

Bu ana özelliktir. İki yönde çalışır ve her yön ayrı açılabilir.

**Gelen: onlar konuşur, sen duyarsın.** Uygulama sadece Discord uygulamasını dinler; bu yüzden kendi sesini,
oyununu ya da müziğini asla duymaz ve konuşurken dinlemeye devam eder. Konuşmayı tanır, çevirir, altyazı gösterir
ve istersen çeviriyi söyler. Onların konuştuğu dili ya da Otomatik algıla'yı seçersin. Dili seçmek,
bilgisayarındaki tanımayı yaklaşık iki kat hızlandırır.

**Giden: sen konuşursun, onlar duyar.** Uygulama mikrofonunu dinler, söylediğini çevirir ve sanal kablo üzerinden
Discord'da söyler. Kendi sesin Discord'a gönderilmez, yalnızca çeviri gider. Discord kablo yerine gerçek
mikrofonunu kullanırsa uygulama seni uyarır.

**İnsanları duy, F9 tuşu.** Varsayılan olarak sadece çevirileri duyarsın. Çevirmen çalışırken uygulama Discord'u
Windows ses karıştırıcısında kısar ve Durdur'a bastığında sesini geri verir. Onların kendi seslerini de duymak için
F9'a ya da İnsanları duy düğmesine bas. Tuşu Giriş sekmesinden değiştirebilirsin.

**Tek ses, sırayla.** Görüşme çevirileri ve sesli okunan sohbet mesajları tek bir sesi paylaşır, bu yüzden asla
birbirinin üstüne konuşmaz. Her şey söylendiği sırayla söylenir ve hiçbir şey atlanmaz: şu anki cümle çalarken
sonraki hazırlanır, cümleler birikince ses biraz daha hızlı konuşur.

**Kim konuşuyor.** Uygulamanın sesi kimin konuştuğunu söyleyebilir, örneğin adın ilk iki harfini ya da tam adı.
Bunu Çıkış sekmesinde, Uygulamanın sesi altında seç. Görüşmelerde adlar doğrudan Discord uygulamasından gelir:
Çıkış sekmesinde, Kim konuşuyor altında kendi Discord uygulamanı bir kez ekle. Sohbet mesajlarında her zaman
yazarın adı vardır.

**Canlı** sekmesinde iki yönün dillerini ayarlar, seviye göstergelerini izler ve dökümü okursun. Bir bas-konuş
düğmesi ve Söylemek için yaz kutusu kullanabilirsin: bir satır yazarsın, çevrilir ve Discord'da söylenir. Onların
konuştuğu dilde cevap ver seçeneği, çıkış dilinin karşı tarafta en son algılanan dili izlemesini sağlar.

**Giriş** sekmesinde neyin dinleneceğini ve mikrofonunun nasıl başlayacağını seçersin: ses etkinliği, bas-konuş ya
da aç-kapa. Bir hassasiyet ayarı da vardır. Uygulama, mikrofonun kendi sesini duyduğunda onu tanır ve yok sayar.

**Çıkış** sekmesinde çevirilerin nerede çalacağını, sesin için sanal kabloyu, uygulamanın sesini ve kimin
konuştuğunu seçersin.

Tüm ses aygıtları ayrıca tek bir yerde, Ayarlar sekmesindeki Ses aygıtları bölümünde toplanmıştır.

=== 6. Motorlar: konuşma, çeviri, yapay zekâ ve ses
# Motorlar

Çevirinin her adımı farklı bir motor kullanabilir ve bunları istediğin zaman değiştirebilirsin. Profilinde
saklanırlar.

- **Konuşma sekmesi.** Konuşmayı metne çevirir. Ücretsiz seçenek, bilgisayarında çalışan Whisper'dır. Bulut
  seçenekleri bir anahtar ister: OpenAI, Groq, Deepgram, ElevenLabs, Azure ve Google. Bu sekmede bir mikrofon testi
  vardır.
- **Çeviri sekmesi.** Ücretsiz seçenek anahtar gerektirmeyen Google Çeviri'dir. Diğerleri DeepL, Azure,
  LibreTranslate, MyMemory ve çevrimdışı motor Argos'tur. Tonu seçebilirsin: doğal, rahat, resmî ya da birebir. Bir
  sözlük, adlar ve oyun terimleri gibi bazı kelimelerin nasıl çevrileceğini sabitler.
- **Yapay zekâ modeli sekmesi.** Çeviri motoru yapay zekâ modeli olduğunda kullanılır. Bulutta bir model ya da
  örneğin Ollama veya LM Studio ile bilgisayarında çalışan bir model olabilir. Argo ya da adlar için ek talimatlar
  ekleyebilirsin.
- **Ses sekmesi.** Çevirileri seslendiren motor. Ücretsiz seçenek Microsoft Edge nöral sesleridir. Piper ve Kokoro
  çevrimdışı çalışır. ElevenLabs, OpenAI, Azure ve Google ücretlidir. Her yön için bir ses seç ya da uygulamanın her
  dil için doğal bir ses seçmesine izin ver. Her yön için sesin hızını, perdesini ve düzeyini de ayarlayabilirsin.
  Bunlar her ses motoruyla çalışır.

Her sekmede bir test düğmesi vardır, böylece bir motoru kullanmadan önce deneyebilirsin.

Başlangıç profilleri şunlardır: Ücretsiz, anahtarsız. OpenAI. Edge ile Groq. ElevenLabs ile Claude. Ve Whisper,
Ollama ve Piper ile Tamamen çevrimdışı.

=== 7. API anahtarları
# API anahtarları

Ücretsiz motorlar anahtar gerektirmez. Ücretli ya da bulut tabanlı bir motor istiyorsan o şirketten bir API
anahtarı gerekir.

**API anahtarları** sekmesini aç ve her anahtarı kendi kutusuna yapıştır. Tüm anahtarlar tek bir yerde, uygulama
klasöründeki data, keys nokta json dosyasında tutulur. Anahtarlar asla profillerin içinde saklanmaz ve bir profili
dışa aktardığında dahil edilmez, böylece profilleri güvenle paylaşabilirsin.

Bu dosyayı gizli tut. Klasörün tamamını başka bir bilgisayara kopyalarsan anahtarların da onunla gider.

Piper, Kokoro, Argos ve NVIDIA ekran kartı kitaplıkları gibi isteğe bağlı yerel motorlar install extras nokta bat
ile ya da uygulamada motorun yanındaki Şimdi yükle düğmesiyle kurulur.

=== 8. Discord metnini çevirmek
# Discord metnini çevirmek

**Sohbet** düğmesine bas ya da Pano'daki sohbet kartını kullan. Uygulama, Discord uygulamasında gördüğün mesajları
bir ekran okuyucu gibi Windows erişilebilirlik özellikleriyle okur. Token ya da bot gerektirmez ve Discord'a hiçbir
şey göndermez.

Yeni mesajlar çevrilir ve doğrudan Discord'un içinde, özgün metnin üstünde ya da yanındaki küçük bir pencerede
gösterilir. Bunu Metin sekmesinde Çevirileri göster altında seçersin. Sunucularda, özel mesajlarda, gruplarda, alt
başlıklarda ve forum gönderilerinde, Discord arka plandayken bile çalışır. Zaten senin dilinde olan mesajlar ve
kendi mesajların atlanır. Çeviriler yalnızca Discord etkin pencereyken görünür, bu yüzden oyununu asla kapatmaz.

**Sesli okuma.** Sadece yeni mesajlar sesli okunur. Geri kaydırdığın mesajlar, düzenlenen ve eski mesajlar ekranda
çevrilir ama asla okunmaz. Sohbet mesajları uygulamanın sesini görüşme çevirileriyle paylaşır, bu yüzden ikisi asla
aynı anda konuşmaz.

Metin sekmesinde başka araçlar da var:

- **Seçerek çevir.** Bir metni seç ya da bir kelimeye çift tıkla; farenin yanında çevirinin olduğu bir pencere
  çıkar.
- **Ctrl+Alt+T** her uygulamada geçerli seçimi çevirir.
- **Ctrl+Alt+Y**, Discord'un mesaj kutusuna yazdığını o sohbette kullanılan dile çevrilmiş haliyle değiştirir.
- **Onların dilinde yaz.** Metin sekmesinde yaz, sonra kopyala, Discord'a yapıştır ya da gönder.
- **Ctrl+Alt+O** ekranın herhangi bir yerine bir çerçeve çizmeni sağlar. Uygulama metni OCR ile okur ve çeviriyi
  üstünde gösterir. Birkaç saniyede bir tekrar edebilir.
- **Kopyalanan metin.** İstersen kopyaladığın her şeyi çevirir.

Tüm kısayolları Metin sekmesinden değiştirebilirsin. Rusça ya da Japonca gibi başka alfabelerde OCR için o dili
Windows Ayarları'ndan ekle.

=== 9. Altyazılar ve dökümler
# Altyazılar ve dökümler

**Altyazı penceresi** oyununun ya da Discord'un üstünde durur. Taşımak için sürükle. Boyutunu fare tekerleğiyle
değiştir. Seçenekler için sağ tıkla: kaç satır gösterileceği, orijinal metnin gösterilip gösterilmeyeceği ve arka
plan gibi. Ayarlar'dan metin boyutunu ve yazı tipini değiştirebilirsin.

Her konuşma bir **döküm** olarak kaydedilebilir. Bu varsayılan olarak açıktır ve Çıkış sekmesinden kapatılır.
Dökümler data klasöründe, transcripts altında saklanır; bu klasörü Günlük sekmesinden ya da Ayarlar'dan
açabilirsin.

Günlük sekmesi uygulamanın ne yaptığını anlık gösterir. Günlükleri, dökümleri ve uygulama klasörünü açmak için
düğmeleri de vardır. Bir şeyler ters giderse ilk bakılacak yer günlüktür.

Alttaki durum çubuğu her aşamanın gecikmesini gösterir: konuşma tanıma, çeviri ve ses; böylece hangi motorun yavaş
olduğunu görürsün.

=== 10. Ayarlar ve güncellemeler
# Ayarlar ve güncellemeler

**Ayarlar** sekmesi uygulamanın dilini belirler. Değiştirdikten sonra uygulama yeni dilde yeniden başlar. Tüm ses
aygıtları da burada bir aradadır: uygulamanın dinledikleri, mikrofonun, çevirilerin nerede çaldığı ve çevrilmiş
sesinin nereye gittiği.

Uygulamanın görünümünü yönetir: tema, koyu ya da açık, yazı tipi ve uygulamanın, Discord içindeki çevirilerin,
küçük sohbet penceresinin ve açılır pencerelerin metin boyutu. Tüm kısayollar da burada bir aradadır; ayrıca
pencereyi diğerlerinin üstünde tutma seçeneği ve pencere konumlarını sıfırlamak, uygulama, veri ve günlük
klasörlerini açmak için düğmeler bulunur.

Değişiklikleri otomatik kaydet seçeneği, profilini her değişiklikten yaklaşık bir saniye sonra kaydeder.
Varsayılan olarak açıktır.

**Güncellemeler.** Güncellemeleri denetle'ye bas. GitHub'da daha yeni bir sürüm varsa Şimdi güncelle düğmesi çıkar.
Yeni sürümü indirir ve program dosyalarını değiştirir. Ayarlarına, profillerine, API anahtarlarına ve indirilen
modellere asla dokunulmaz. Gerekli paketlerin listesi değiştiyse onlar da güncellenir. Bitince uygulama yeniden
başlatmayı önerir. Uygulama ayrıca açıldıktan birkaç saniye sonra sessizce kontrol eder.

=== 11. Sorun giderme
# Sorun giderme

**Kendi kendine testi çalıştır.** Uygulama klasöründe bir konsol aç ve `runtime\python.exe tools\selftest.py`
komutunu çalıştır. Sanal kabloya bir test cümlesi çalar ve iki yönü de dener. PASS kelimesiyle biterse tanıma,
çeviri ve ses çalışıyor demektir.

**Görüşme testini çalıştır.** `runtime\python.exe tools\calltest.py` sanal kabloya sahte bir sesli görüşme çalar.
Her cümlenin sırayla çevrildiğini, uygulamanın kendi sesini asla duymadığını ve iki sesin asla aynı anda
çalmadığını kontrol eder. Bir Discord görüşmesinde değilken çalıştır.

**Kimse çevirimi duymuyor.** Discord'da giriş aygıtı CABLE Output olmalı. Uygulamada Çıkış sekmesi CABLE Input'a
göndermeli. Discord'da Gürültü Azaltma'nın kapalı olduğunu kontrol et.

**Uygulama hiçbir şey duymuyor.** Giriş sekmesinde yöntemi kontrol et. Sadece Discord uygulaması ile Discord açık
olmalı. Loopback ile aygıt, Discord'un çaldığı aygıt olmalı. Canlı sekmesindeki seviye göstergelerine bak.
Kıpırdamıyorlarsa ayar yanlıştır.

**Çevirim iki kez duyuluyor ya da uygulama kendini çeviriyor.** Giriş sekmesinde Sadece Discord uygulaması
yöntemini kullan ve kulaklık tak.

**Discord'un sesi yok.** Çevirmen çalışırken bu bilerek yapılır: insanları da duymak için F9'a bas. Dizcord aniden
kapandıysa bir kez aç, Discord'un sesini geri verir; ya da Windows ses karıştırıcısında Discord'un sesini aç.

**İnsanlar gerçek sesimi duyuyor.** Discord'da giriş aygıtı mikrofonun değil, CABLE Output olmalı. Discord gerçek
mikrofonunu kullandığında uygulama bir uyarı gösterir.

**Bir motor hata veriyor.** Günlük sekmesini aç. forbidden ya da blocked diyen bir mesaj genelde anahtarın ya da
modelin hesabın için izinli olmadığı anlamına gelir. Başka bir motor dene ve yeniden test et.

**Sohbet çevirisi hiçbir şey göstermiyor.** Discord'un etkin pencere olduğundan ve Sohbet düğmesinin açık
olduğundan emin ol. Özellik, Discord'un masaüstü uygulaması için yapılmıştır.

**Hâlâ takıldın mı.** Uygulamayı Dizcord debug nokta bat ile başlat. Hataları gösteren bir konsol açılır; bir
sorunu bildirirken işe yarar.

=== 12. Bu kılavuz hakkında
# Bu kılavuz hakkında

Dizcord'a yerleşik kılavuzu okuyorsun. Anlatıcı, uygulamanın dilinde doğal bir sestir. Bilgisayarında çalışır,
çevrimdışı çalışır ve hiçbir yere bir şey göndermez.

- **Sonraki ve Önceki** bölümler arasında geçiş yapar. Anlatıcı eski bölümü okumayı bırakır ve yenisine başlar, yeni
  metin de aynı anda görünür.
- **Sesli oku** anlatıcıyı açar ya da kapatır. Kapalıyken kılavuz yalnızca metindir.
- **Yeniden oku** geçerli bölümü baştan başlatır.
- **Durdur** anlatıcıyı susturur.
- **Ses** ve **Hız** nasıl duyulacağını değiştirir. Çevrimdışı sesin yanı sıra internet gerektiren çevrimiçi bir
  ses ya da Windows seslerinden birini seçebilirsin.
- **Rehberli turu tekrar izle** ilk adımları yeniden gösterir.

Bu sekmeden çıkınca anlatıcı susar ve sen çevirmeni kullanırken asla kendiliğinden başlamaz.

Kılavuzun sonu bu. Dizcord'un tadını çıkar!
