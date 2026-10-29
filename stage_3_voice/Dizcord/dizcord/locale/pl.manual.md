=== 1. Witaj
# Witaj w Dizcord

Dizcord to tłumacz w czasie rzeczywistym dla Discorda i każdego innego czatu głosowego. Działa w całości na twoim
komputerze.

- **Słyszysz innych w swoim języku.** Aplikacja słucha, co ludzie mówią na Discordzie, zapisuje to, tłumaczy,
  pokazuje napisy i może przeczytać ci tłumaczenie naturalnym głosem.
- **Oni słyszą ciebie w swoim języku.** Mówisz do mikrofonu. Aplikacja tłumaczy to, co powiedziałeś, i wypowiada
  to na Discordzie przez wirtualny kabel audio.
- **Tekst też.** Tłumaczy wiadomości z Discorda na serwerach, w wiadomościach prywatnych i wątkach, każdy tekst,
  który zaznaczysz myszą, oraz tekst na ekranie dzięki OCR. Możesz też pisać w ich języku.
- **Darmowo na start.** Profil Darmowy, bez kluczy, działa bez konta i bez płacenia. Płatne silniki w chmurze są
  opcjonalne.

Ta instrukcja ma dwanaście rozdziałów. Używaj przycisków Dalej i Poprzedni albo kliknij rozdział na liście. Za
każdym razem, gdy zmieniasz rozdział, lektor przerywa stary i czyta nowy. Głos to naturalny głos w języku
aplikacji, który działa na twoim komputerze. Nie potrzebuje internetu i nic nie kosztuje.

=== 2. Pierwsze uruchomienie
# Pierwsze uruchomienie

**Krok 1. Otwórz aplikację.** Kliknij dwukrotnie Dizcord.exe albo Dizcord.bat. Za pierwszym razem aplikacja tworzy
własną kopię Pythona w swoim folderze. Pobiera to około 750 megabajtów, trwa kilka minut i nie wymaga uprawnień
administratora. Nic nie jest instalowane w Windowsie.

Potem wybierasz język aplikacji. Wszystko wyświetla się w tym języku, a przewodnik i ta instrukcja są w nim
czytane na głos. Aplikacja raz pobiera głos tego języka, około 60 megabajtów. Następnie krótki przewodnik pokazuje
pierwsze kroki. Otwiera się tylko za tym pierwszym razem; możesz go powtórzyć na tej karcie.

**Krok 2. Zainstaluj wirtualny kabel audio.** Zainstaluj VB-Audio Virtual Cable, który jest darmowy, i uruchom
ponownie komputer. To jedyna rzecz poza folderem, bo Windows potrzebuje sterownika, żeby utworzyć wirtualny
mikrofon.

**Krok 3. Skonfiguruj Discorda.** Otwórz Discorda, potem Ustawienia użytkownika, potem Głos i wideo.

- Urządzenie wejściowe: CABLE Output z VB-Audio Virtual Cable.
- Urządzenie wyjściowe: twoje słuchawki.
- Wyłącz Redukcję szumów, Redukcję echa i Automatyczną regulację wzmocnienia.

**Krok 4. Skonfiguruj aplikację.** Wybierz profil Za darmo, bez kluczy. Na karcie Wyjście wysyłaj przetłumaczony
głos do CABLE Input. Na karcie Wejście zostaw metodę Tylko aplikacja Discord i wybierz swój prawdziwy mikrofon. Na
karcie Na żywo wybierz języki. Potem naciśnij Start albo klawisz F5.

Model mowy, Whisper small, zajmuje około 460 megabajtów i pobiera się przy pierwszym użyciu.

=== 3. Główne okno
# Główne okno

Na górze jest pole profilu. Profil przechowuje wszystkie twoje ustawienia silników, języków i urządzeń. Profile
możesz zapisywać, zapisywać jako, usuwać, importować i eksportować. Wyeksportowane profile nigdy nie zawierają
twoich kluczy API.

Twoje zmiany zapisują się automatycznie mniej więcej sekundę po ich zrobieniu. Możesz to wyłączyć na karcie
Ustawienia.

Obok pola profilu są trzy przyciski:

- **Napisy** pokazuje pływające okno napisów, które możesz przeciągać, zmieniać kółkiem myszy i konfigurować
  prawym klikiem.
- **Czat** włącza tłumaczenie wiadomości tekstowych z Discorda.
- **Start** uruchamia tłumacza głosu. Klawisz F5 robi to samo.

Karty to: Pulpit, Na żywo, Tekst, Wejście, Wyjście, Mowa, Tłumaczenie, Model AI, Głos, Klucze API, Konfiguracja,
Ustawienia, Instrukcja i Log. Kolejne rozdziały objaśniają te, których będziesz używać najczęściej.

=== 4. Pulpit
# Pulpit

Pulpit to twoje centrum sterowania. To pierwsza karta i pokazuje wszystko na jednym ekranie.

- **Karta tłumacza głosu** uruchamia i zatrzymuje tłumaczenie głosu na żywo oraz pokazuje, co właśnie robi:
  rozpoznaje, tłumaczy czy mówi.
- **Karta tłumaczenia czatu** uruchamia i zatrzymuje tłumaczenie wiadomości z Discorda. Ma też opcję czytania
  przetłumaczonych wiadomości na głos, po kolei albo tak, by nowa wiadomość przerywała czytaną.
- **Karta Ty** to miejsce na twoją nazwę na Discordzie i język, w którym piszesz.
- **Karta narzędzi** ma skróty do zaznaczania, by przetłumaczyć, OCR i okna napisów.
- **Karta skrótów** przypomina twoje skróty klawiszowe.
- Na dole Ostatnie tłumaczenia pokazuje ostatnio przetłumaczone zdania.

Ustawienia, które są w dwóch miejscach, na przykład na Pulpicie i na karcie Tekst, zawsze są zsynchronizowane.

=== 5. Tłumaczenie głosu na żywo
# Tłumaczenie głosu na żywo

To główna funkcja. Działa w dwóch kierunkach i każdy można włączyć osobno.

**Przychodzące: oni mówią, ty słyszysz.** Aplikacja słucha tylko aplikacji Discord, więc nigdy nie słyszy własnego
głosu, twojej gry ani muzyki, i słucha dalej, gdy mówi. Rozpoznaje mowę, tłumaczy ją, pokazuje napisy i, jeśli
chcesz, wypowiada tłumaczenie. Wybierasz język, którym mówią, albo automatyczne wykrywanie. Wybranie języka
sprawia, że rozpoznawanie na twoim PC jest mniej więcej dwa razy szybsze.

**Wychodzące: ty mówisz, oni słyszą.** Aplikacja słucha twojego mikrofonu, tłumaczy to, co mówisz, i wypowiada to
na Discordzie przez wirtualny kabel. Twój własny głos nie trafia na Discorda, tylko tłumaczenie. Aplikacja ostrzeże
cię, jeśli Discord używa twojego prawdziwego mikrofonu zamiast kabla.

**Słysz ludzi, klawisz F9.** Domyślnie słyszysz tylko tłumaczenia. Gdy tłumacz działa, aplikacja ścisza Discorda w
mikserze głośności Windows i oddaje mu głośność, gdy naciśniesz Stop. Naciśnij F9 albo przycisk Słysz ludzi, aby
słyszeć też ich własne głosy. Klawisz możesz zmienić na karcie Wejście.

**Jeden głos, po kolei.** Tłumaczenia z rozmowy i czytane na głos wiadomości z czatu mają jeden głos, więc nigdy
nie mówią jednocześnie. Wszystko jest mówione w kolejności, w jakiej zostało powiedziane, i nic nie jest pomijane:
następne zdanie przygotowuje się, gdy gra obecne, a gdy zdania się piętrzą, głos mówi trochę szybciej.

**Kto mówi.** Głos aplikacji może mówić, kto mówił, na przykład pierwsze dwie litery imienia albo pełną nazwę.
Wybierasz to na karcie Wyjście, w sekcji Głos aplikacji. W rozmowach imiona pochodzą z samej aplikacji Discord: na
karcie Wyjście, w sekcji Kto mówi, raz dodaj swoją własną aplikację Discord. Wiadomości z czatu zawsze mają nazwę
autora.

Na karcie **Na żywo** ustawiasz języki obu kierunków, patrzysz na wskaźniki poziomu i czytasz transkrypcję. Możesz
używać przycisku „naciśnij, aby mówić” i pola Wpisz, aby powiedzieć, w którym wpisujesz zdanie, a ono jest
tłumaczone i wypowiadane na Discordzie. Opcja Odpowiadaj w języku, którym mówią sprawia, że twój język wyjściowy
podąża za ostatnim językiem wykrytym u drugiej osoby.

Na karcie **Wejście** wybierasz, czego słuchać i jak startuje twój mikrofon: aktywacja głosowa, naciśnij, aby
mówić, albo przełączanie. Jest też regulacja czułości. Aplikacja rozpoznaje własny głos, gdy słyszy go twój
mikrofon, i go ignoruje.

Na karcie **Wyjście** wybierasz, gdzie grają tłumaczenia, wirtualny kabel dla twojego głosu, głos aplikacji i kto
mówi.

Wszystkie urządzenia dźwiękowe są też zebrane w jednym miejscu, na karcie Ustawienia, w sekcji Urządzenia
dźwiękowe.

=== 6. Silniki: mowa, tłumaczenie, AI i głos
# Silniki

Każdy krok tłumaczenia może używać innego silnika i możesz je zmieniać w każdej chwili. Zapisują się w twoim
profilu.

- **Karta Mowa.** Zamienia mowę na tekst. Darmowy wybór to Whisper, który działa na twoim komputerze. Wybory w
  chmurze wymagają klucza: OpenAI, Groq, Deepgram, ElevenLabs, Azure i Google. Na tej karcie jest test mikrofonu.
- **Karta Tłumaczenie.** Darmowy wybór to Tłumacz Google, bez klucza. Inne to DeepL, Azure, LibreTranslate,
  MyMemory i silnik offline Argos. Możesz ustawić ton: naturalny, luźny, formalny albo dosłowny. Słowniczek ustala,
  jak tłumaczyć pewne słowa, na przykład imiona i pojęcia z gier.
- **Karta Model AI.** Używana, gdy silnikiem tłumaczenia jest model AI. Może to być model w chmurze albo działający
  na twoim komputerze, na przykład przez Ollama lub LM Studio. Możesz dodać instrukcje dotyczące slangu lub imion.
- **Karta Głos.** Silnik, który wypowiada tłumaczenia. Darmowy wybór to neuronowe głosy Microsoft Edge. Piper i
  Kokoro działają offline. ElevenLabs, OpenAI, Azure i Google są płatne. Wybierz głos dla każdego kierunku albo
  pozwól aplikacji wybrać naturalny głos dla każdego języka. Dla każdego kierunku możesz też ustawić szybkość,
  wysokość i głośność głosu. Działa to z każdym silnikiem głosu.

Każda karta ma przycisk testu, żebyś mógł sprawdzić silnik przed użyciem.

Profile startowe to: Darmowy, bez kluczy. OpenAI. Groq z Edge. Claude z ElevenLabs. I W pełni offline, z
Whisperem, Ollamą i Piperem.

=== 7. Klucze API
# Klucze API

Darmowe silniki nie potrzebują kluczy. Jeśli chcesz płatny silnik albo silnik w chmurze, potrzebujesz klucza API od
tej firmy.

Otwórz kartę **Klucze API** i wklej każdy klucz w jego pole. Wszystkie klucze są w jednym miejscu, w pliku data,
keys kropka json, w folderze aplikacji. Klucze nigdy nie są zapisywane w profilach ani dołączane przy eksporcie
profilu, więc możesz bezpiecznie udostępniać profile.

Trzymaj ten plik w tajemnicy. Jeśli skopiujesz cały folder na inny komputer, twoje klucze pójdą razem z nim.

Opcjonalne silniki lokalne, takie jak Piper, Kokoro, Argos i biblioteki dla kart graficznych NVIDIA, instaluje się
przez install extras kropka bat albo przyciskiem Zainstaluj teraz obok silnika w aplikacji.

=== 8. Tłumaczenie tekstu z Discorda
# Tłumaczenie tekstu z Discorda

Naciśnij przycisk **Czat** albo użyj karty czatu na Pulpicie. Aplikacja zacznie wtedy czytać wiadomości, które
widzisz w aplikacji Discord, przez ułatwienia dostępu Windows, jak czytnik ekranu. Nie potrzebuje tokenu ani bota i
niczego nie wysyła na Discorda.

Nowe wiadomości są tłumaczone i pokazywane nad oryginalnym tekstem, bezpośrednio w Discordzie, albo w małym oknie
obok. Wybierasz to na karcie Tekst, w Pokazuj tłumaczenia. Działa na serwerach, w wiadomościach prywatnych,
grupach, wątkach i postach na forum, nawet gdy Discord jest w tle. Wiadomości, które już są w twoim języku, i twoje
własne wiadomości są pomijane. Tłumaczenia widać tylko wtedy, gdy Discord jest aktywnym oknem, więc nigdy nie
zasłaniają gry.

**Czytanie na głos.** Na głos czytane są tylko nowe wiadomości. Wiadomości, do których przewijasz wstecz, edytowane
i stare wiadomości są tłumaczone na ekranie, ale nigdy nie są czytane. Wiadomości z czatu dzielą głos aplikacji z
tłumaczeniami z rozmowy, więc nigdy nie mówią naraz.

Karta Tekst ma więcej narzędzi:

- **Zaznacz, aby przetłumaczyć.** Zaznacz tekst albo kliknij dwukrotnie słowo, a obok myszy pojawi się okienko z
  tłumaczeniem.
- **Ctrl+Alt+T** tłumaczy bieżące zaznaczenie w dowolnej aplikacji.
- **Ctrl+Alt+Y** zastępuje to, co wpisałeś w polu wiadomości Discorda, tłumaczeniem na język używany na tym czacie.
- **Pisz w ich języku.** Pisz na karcie Tekst, potem skopiuj, wklej na Discordzie albo wyślij.
- **Ctrl+Alt+O** pozwala przeciągnąć ramkę nad dowolną częścią ekranu. Aplikacja odczytuje tekst przez OCR i
  pokazuje nad nim tłumaczenie. Może to powtarzać co kilka sekund.
- **Skopiowany tekst.** Opcjonalnie tłumaczy wszystko, co kopiujesz.

Każdy skrót możesz zmienić na karcie Tekst. Dla OCR innych alfabetów, na przykład rosyjskiego czy japońskiego,
dodaj ten język w Ustawieniach systemu Windows.

=== 9. Napisy i transkrypcje
# Napisy i transkrypcje

**Okno napisów** unosi się nad grą albo Discordem. Przeciągnij je, aby je przesunąć. Kółkiem myszy zmieniasz jego
rozmiar. Prawy klik pokazuje opcje, na przykład ile wierszy pokazać, czy pokazywać oryginał i jakie ma być tło. W
Ustawieniach możesz zmienić rozmiar tekstu i czcionkę.

Każdą rozmowę można zapisać jako **transkrypcję**. Jest to domyślnie włączone, a wyłączasz to na karcie Wyjście.
Transkrypcje zapisują się w folderze data, w transcripts, i możesz otworzyć ten folder z karty Log albo z
Ustawień.

Karta Log pokazuje na bieżąco, co robi aplikacja. Ma też przyciski do otwierania logów, transkrypcji i folderu
aplikacji. Jeśli coś pójdzie nie tak, najpierw zajrzyj do logu.

Pasek stanu na dole pokazuje opóźnienie każdego etapu: rozpoznawania mowy, tłumaczenia i głosu, żebyś widział,
który silnik jest wolny.

=== 10. Ustawienia i aktualizacje
# Ustawienia i aktualizacje

Na karcie **Ustawienia** wybierasz język aplikacji. Po jego zmianie aplikacja uruchamia się ponownie w nowym
języku. Są tam też zebrane wszystkie urządzenia dźwiękowe: czego słucha aplikacja, twój mikrofon, gdzie grają
tłumaczenia i dokąd trafia twój przetłumaczony głos.

Tu ustawiasz wygląd aplikacji: motyw, ciemny lub jasny, czcionkę i rozmiar tekstu aplikacji oraz tłumaczeń
pokazywanych w Discordzie, w małym oknie czatu i w okienkach. Są tu też wszystkie skróty w jednym miejscu, opcja
trzymania okna nad innymi i przyciski do resetowania położenia okien oraz otwierania folderów aplikacji, danych i
logów.

Opcja Zapisuj zmiany automatycznie zapisuje profil mniej więcej sekundę po każdej zmianie. Jest domyślnie włączona.

**Aktualizacje.** Naciśnij Sprawdź aktualizacje. Jeśli na GitHubie jest nowsza wersja, pojawi się przycisk
Aktualizuj teraz. Pobiera on nową wersję i podmienia pliki programu. Twoje ustawienia, profile, klucze API i pobrane
modele nigdy nie są ruszane. Jeśli zmieniła się lista potrzebnych pakietów, one też są aktualizowane. Na koniec
aplikacja proponuje ponowne uruchomienie. Aplikacja sprawdza też po cichu kilka sekund po starcie.

=== 11. Rozwiązywanie problemów
# Rozwiązywanie problemów

**Uruchom autotest.** Otwórz konsolę w folderze aplikacji i uruchom `runtime\python.exe tools\selftest.py`.
Odtwarza zdanie testowe w wirtualnym kablu i sprawdza oba kierunki. Jeśli kończy się słowem PASS, rozpoznawanie,
tłumaczenie i głos działają.

**Uruchom test rozmowy.** `runtime\python.exe tools\calltest.py` odtwarza udawaną rozmowę głosową do wirtualnego
kabla. Sprawdza, czy każde zdanie jest tłumaczone po kolei, czy aplikacja nigdy nie słyszy własnego głosu i czy
nigdy nie grają dwa głosy naraz. Uruchamiaj go, gdy nie jesteś w rozmowie na Discordzie.

**Nikt nie słyszy mojego tłumaczenia.** Na Discordzie urządzeniem wejściowym musi być CABLE Output. W aplikacji
karta Wyjście musi wysyłać do CABLE Input. Sprawdź, czy Redukcja szumów na Discordzie jest wyłączona.

**Aplikacja nic nie słyszy.** Na karcie Wejście sprawdź metodę. Przy Tylko aplikacja Discord Discord musi być
otwarty. Przy loopback urządzenie musi być tym, na którym gra Discord. Spójrz na wskaźniki poziomu na karcie Na
żywo. Jeśli się nie ruszają, ustawienie jest złe.

**Moje tłumaczenie słychać dwa razy albo aplikacja tłumaczy samą siebie.** Użyj metody Tylko aplikacja Discord na
karcie Wejście i używaj słuchawek.

**Discord jest cicho.** Tak ma być, gdy tłumacz działa: naciśnij F9, aby słyszeć też ludzi. Jeśli Dizcord zamknął
się nagle, otwórz go raz, a odda Discordowi głośność, albo podgłośnij Discorda w mikserze głośności Windows.

**Ludzie słyszą mój prawdziwy głos.** W Discordzie urządzeniem wejściowym musi być CABLE Output, a nie twój
mikrofon. Aplikacja pokazuje ostrzeżenie, gdy Discord używa twojego prawdziwego mikrofonu.

**Silnik nie działa.** Otwórz kartę Log. Komunikat ze słowem forbidden albo blocked zwykle oznacza, że klucz lub
model nie jest dozwolony dla twojego konta. Spróbuj innego silnika i przetestuj ponownie.

**Tłumaczenie czatu nic nie pokazuje.** Upewnij się, że Discord jest aktywnym oknem i że przycisk Czat jest
włączony. Funkcja jest zrobiona dla aplikacji Discord na komputer.

**Nadal nie działa.** Uruchom aplikację przez Dizcord debug kropka bat. Otworzy się konsola z błędami, co pomaga
przy zgłaszaniu problemu.

=== 12. O tej instrukcji
# O tej instrukcji

Czytasz instrukcję wbudowaną w Dizcord. Lektor to naturalny głos w języku aplikacji. Działa na twoim komputerze,
offline, i niczego nigdzie nie wysyła.

- **Dalej i Poprzedni** zmieniają rozdział. Lektor przestaje czytać stary rozdział i zaczyna nowy, a nowy tekst
  pojawia się w tym samym momencie.
- **Czytaj na głos** włącza lub wyłącza lektora. Gdy jest wyłączony, instrukcja jest tylko tekstem.
- **Czytaj ponownie** zaczyna bieżący rozdział od początku.
- **Stop** ucisza lektora.
- **Głos** i **Szybkość** zmieniają brzmienie. Oprócz głosu offline możesz wybrać głos online, który wymaga
  internetu, albo jeden z głosów Windows.
- **Powtórz przewodnik** jeszcze raz pokazuje pierwsze kroki.

Lektor milknie, gdy opuszczasz tę kartę, i nigdy nie zaczyna sam, gdy używasz tłumacza.

To koniec instrukcji. Miłej zabawy z Dizcord!
