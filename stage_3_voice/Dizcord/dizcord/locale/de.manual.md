=== 1. Willkommen
# Willkommen bei Dizcord

Dizcord ist ein Echtzeit-Übersetzer für Discord und jeden anderen Sprachchat. Er läuft komplett auf deinem PC.

- **Du hörst die anderen in deiner Sprache.** Die App hört, was Leute in Discord sagen, schreibt es auf,
  übersetzt es, zeigt Untertitel und kann dir die Übersetzung mit einer natürlichen Stimme vorlesen.
- **Sie hören dich in ihrer Sprache.** Du sprichst in dein Mikrofon. Die App übersetzt, was du gesagt hast, und
  spricht es über ein virtuelles Audiokabel in Discord.
- **Auch Text.** Sie übersetzt Discord-Nachrichten in Servern, Direktnachrichten und Threads, jeden Text, den du
  mit der Maus markierst, und Text auf dem Bildschirm per OCR. Du kannst auch in ihrer Sprache schreiben.
- **Kostenlos zum Einstieg.** Das Profil Kostenlos, ohne Schlüssel, funktioniert ohne Konto und ohne Bezahlung.
  Kostenpflichtige Cloud-Engines sind optional.

Dieses Handbuch hat zwölf Kapitel. Nutze die Knöpfe Weiter und Zurück, oder klicke auf ein Kapitel in der Liste.
Jedes Mal, wenn du das Kapitel wechselst, hört der Sprecher mit dem alten auf und liest das neue. Die Stimme ist
eine natürliche Stimme in der Sprache der App, die auf deinem PC läuft. Sie braucht kein Internet und kostet
nichts.

=== 2. Erster Start
# Erster Start

**Schritt 1. Öffne die App.** Doppelklicke auf Dizcord.exe oder Dizcord.bat. Beim ersten Mal baut die App eine
eigene Python-Kopie in ihrem Ordner auf. Dabei werden etwa 750 Megabyte heruntergeladen, das dauert ein paar
Minuten und braucht keine Administratorrechte. In Windows selbst wird nichts installiert.

Danach wählst du die Sprache der App. Alles wird in dieser Sprache angezeigt, und die Anleitung und dieses Handbuch
werden in ihr vorgelesen. Die App lädt die Stimme dieser Sprache einmal herunter, etwa 60 Megabyte. Danach zeigt
dir eine kurze geführte Tour die ersten Schritte. Sie öffnet sich nur dieses erste Mal; du kannst sie in diesem Tab
wiederholen.

**Schritt 2. Installiere ein virtuelles Audiokabel.** Installiere VB-Audio Virtual Cable, das kostenlos ist, und
starte den PC neu. Das ist das Einzige außerhalb des Ordners, denn Windows braucht einen Treiber für ein virtuelles
Mikrofon.

**Schritt 3. Richte Discord ein.** Öffne Discord, dann Benutzereinstellungen, dann Sprache und Video.

- Eingabegerät: CABLE Output, von VB-Audio Virtual Cable.
- Ausgabegerät: dein Headset.
- Schalte Rauschunterdrückung, Echounterdrückung und Automatische Verstärkungsregelung aus.

**Schritt 4. Richte die App ein.** Wähle das Profil Kostenlos, ohne Schlüssel. Im Tab Ausgang schickst du deine
übersetzte Stimme an CABLE Input. Im Tab Eingang lässt du die Methode Nur die Discord-App und wählst dein echtes
Mikrofon. Im Tab Live wählst du die Sprachen. Dann drück Start oder die Taste F5.

Das Sprachmodell, Whisper small, ist etwa 460 Megabyte groß und wird bei der ersten Nutzung heruntergeladen.

=== 3. Das Hauptfenster
# Das Hauptfenster

Oben ist das Profilfeld. Ein Profil speichert alle deine Einstellungen für Engines, Sprachen und Geräte. Du kannst
Profile speichern, unter neuem Namen speichern, löschen, importieren und exportieren. Exportierte Profile enthalten
nie deine API-Schlüssel.

Deine Änderungen werden etwa eine Sekunde danach automatisch gespeichert. Das kannst du im Tab Einstellungen
ausschalten.

Neben dem Profilfeld sind drei Knöpfe:

- **Untertitel** zeigt ein schwebendes Untertitelfenster, das du verschieben, mit dem Mausrad in der Größe ändern
  und per Rechtsklick einstellen kannst.
- **Chat** schaltet die Übersetzung der Discord-Textnachrichten ein.
- **Start** startet den Sprachübersetzer. Die Taste F5 macht dasselbe.

Die Tabs sind: Übersicht, Live, Text, Eingang, Ausgang, Spracherkennung, Übersetzung, KI-Modell, Stimme,
API-Schlüssel, Einrichtung, Einstellungen, Handbuch und Log. Die nächsten Kapitel erklären die, die du am meisten
benutzt.

=== 4. Übersicht
# Übersicht

Die Übersicht ist deine Schaltzentrale. Sie ist der erste Tab und zeigt alles auf einen Blick.

- Die **Karte des Sprachübersetzers** startet und stoppt die Live-Sprachübersetzung und zeigt, was er gerade tut:
  erkennen, übersetzen oder sprechen.
- Die **Karte der Chat-Übersetzung** startet und stoppt die Übersetzung der Discord-Nachrichten. Sie kann
  übersetzte Nachrichten auch vorlesen, eine nach der anderen, oder so, dass eine neue Nachricht die gerade
  gelesene unterbricht.
- In der **Karte Du** trägst du deinen Discord-Namen und die Sprache ein, in der du schreibst.
- Die **Werkzeug-Karte** hat Abkürzungen zu Markieren zum Übersetzen, OCR und dem Untertitelfenster.
- Die **Tastenkürzel-Karte** erinnert dich an deine Tastenkürzel.
- Unten zeigt Letzte Übersetzungen die zuletzt übersetzten Zeilen.

Einstellungen, die an zwei Stellen vorkommen, zum Beispiel in der Übersicht und im Tab Text, bleiben immer
synchron.

=== 5. Live-Sprachübersetzung
# Live-Sprachübersetzung

Das ist die Hauptfunktion. Sie arbeitet in zwei Richtungen, und jede kann einzeln eingeschaltet werden.

**Eingehend: Sie sprechen, du hörst.** Die App hört nur die Discord-App, also hört sie nie ihre eigene Stimme, dein
Spiel oder deine Musik, und sie hört weiter zu, während sie spricht. Sie erkennt die Sprache, übersetzt sie, zeigt
Untertitel und spricht, wenn du willst, die Übersetzung. Du wählst die Sprache, die sie sprechen, oder Automatisch
erkennen. Wenn du die Sprache wählst, ist die Erkennung auf deinem PC etwa doppelt so schnell.

**Ausgehend: du sprichst, sie hören.** Die App hört dein Mikrofon, übersetzt, was du sagst, und spricht es über das
virtuelle Kabel in Discord. Deine eigene Stimme wird nicht an Discord geschickt, nur die Übersetzung. Die App warnt
dich, wenn Discord dein echtes Mikrofon statt des Kabels nutzt.

**Leute hören, die Taste F9.** Standardmäßig hörst du nur die Übersetzungen. Solange der Übersetzer läuft, macht
die App Discord im Windows-Lautstärkemixer leise und gibt ihm seine Lautstärke zurück, wenn du Stopp drückst. Drück
F9 oder die Schaltfläche Leute hören, um auch ihre eigenen Stimmen zu hören. Die Taste kannst du im Tab Eingang
ändern.

**Eine Stimme, der Reihe nach.** Die Übersetzungen aus dem Anruf und die vorgelesenen Chatnachrichten teilen sich
eine Stimme, sie reden also nie durcheinander. Alles wird in der Reihenfolge gesagt, in der es gesprochen wurde,
und nichts wird ausgelassen: Der nächste Satz wird vorbereitet, während der aktuelle läuft, und wenn sich Sätze
stauen, spricht die Stimme etwas schneller.

**Wer spricht.** Die Stimme der App kann sagen, wer gesprochen hat, zum Beispiel die ersten zwei Buchstaben des
Namens oder den ganzen Namen. Das wählst du im Tab Ausgang unter Die Stimme der App. In Anrufen kommen die Namen
aus der Discord-App selbst: Im Tab Ausgang trägst du unter Wer spricht einmal deine eigene Discord-Anwendung ein.
Chatnachrichten haben immer den Namen des Autors.

Im Tab **Live** stellst du die Sprachen beider Richtungen ein, siehst die Pegelanzeigen und liest das Transkript.
Du kannst einen Push-to-Talk-Knopf nutzen und das Feld Tippen zum Sprechen, in das du eine Zeile tippst, die
übersetzt und in Discord gesprochen wird. Die Option In der Sprache antworten, die sie sprechen, lässt deine
Ausgabesprache der zuletzt bei der anderen Person erkannten Sprache folgen.

Im Tab **Eingang** wählst du, was die App hört und wie dein Mikrofon startet: Sprachaktivierung, Push-to-Talk oder
Umschalten. Es gibt auch eine Empfindlichkeitsregelung. Die App erkennt ihre eigene Stimme, wenn dein Mikrofon sie
hört, und ignoriert sie.

Im Tab **Ausgang** wählst du, wo die Übersetzungen laufen, das virtuelle Kabel für deine Stimme, die Stimme der App
und wer spricht.

Alle Audiogeräte findest du außerdem gesammelt an einem Ort, im Tab Einstellungen unter Audiogeräte.

=== 6. Engines: Sprache, Übersetzung, KI und Stimme
# Engines

Jeder Schritt der Übersetzung kann eine andere Engine nutzen, und du kannst sie jederzeit wechseln. Sie werden in
deinem Profil gespeichert.

- **Tab Spracherkennung.** Macht aus Sprache Text. Die kostenlose Wahl ist Whisper, das auf deinem PC läuft.
  Cloud-Varianten brauchen einen Schlüssel: OpenAI, Groq, Deepgram, ElevenLabs, Azure und Google. In diesem Tab
  gibt es einen Mikrofontest.
- **Tab Übersetzung.** Die kostenlose Wahl ist Google Übersetzer, ohne Schlüssel. Andere sind DeepL, Azure,
  LibreTranslate, MyMemory und die Offline-Engine Argos. Du kannst den Ton wählen: natürlich, locker, förmlich oder
  wörtlich. Ein Glossar legt fest, wie bestimmte Wörter übersetzt werden, etwa Namen und Spielbegriffe.
- **Tab KI-Modell.** Wird genutzt, wenn die Übersetzungs-Engine das KI-Modell ist. Das kann ein Cloud-Modell sein
  oder eines auf deinem PC, zum Beispiel mit Ollama oder LM Studio. Du kannst zusätzliche Anweisungen für Slang
  oder Namen hinzufügen.
- **Tab Stimme.** Die Engine, die die Übersetzungen spricht. Die kostenlose Wahl sind die Neuralstimmen von
  Microsoft Edge. Piper und Kokoro laufen offline. ElevenLabs, OpenAI, Azure und Google sind kostenpflichtig.
  Wähle eine Stimme für jede Richtung, oder lass die App für jede Sprache eine natürliche Stimme wählen. Für jede
  Richtung kannst du außerdem Tempo, Tonhöhe und Lautstärke der Stimme einstellen. Das funktioniert mit jeder
  Stimm-Engine.

Jeder Tab hat einen Test-Knopf, damit du eine Engine prüfen kannst, bevor du sie nutzt.

Die Startprofile sind: Kostenlos, ohne Schlüssel. OpenAI. Groq mit Edge. Claude mit ElevenLabs. Und Komplett
offline, mit Whisper, Ollama und Piper.

=== 7. API-Schlüssel
# API-Schlüssel

Kostenlose Engines brauchen keine Schlüssel. Für eine kostenpflichtige oder Cloud-Engine brauchst du einen
API-Schlüssel dieser Firma.

Öffne den Tab **API-Schlüssel** und füge jeden Schlüssel in sein Feld ein. Alle Schlüssel liegen an einem Ort, in
der Datei data, keys Punkt json, im App-Ordner. Schlüssel werden nie in Profilen gespeichert und nie mit
exportiert, also kannst du Profile bedenkenlos teilen.

Halte diese Datei privat. Wenn du den ganzen Ordner auf einen anderen PC kopierst, kommen deine Schlüssel mit.

Optionale lokale Engines wie Piper, Kokoro, Argos und die Bibliotheken für NVIDIA-Grafikkarten installierst du mit
install extras Punkt bat, oder mit dem Knopf Jetzt installieren neben der Engine in der App.

=== 8. Discord-Text übersetzen
# Discord-Text übersetzen

Drücke den Knopf **Chat** oder nutze die Chat-Karte in der Übersicht. Die App liest dann die Nachrichten, die du in
der Discord-App siehst, über die Barrierefreiheitsfunktionen von Windows, wie ein Bildschirmleser. Sie braucht
kein Token und keinen Bot und schickt nichts an Discord.

Neue Nachrichten werden übersetzt und über den Originaltext gezeichnet, direkt in Discord, oder in einem kleinen
Fenster daneben. Das wählst du im Tab Text unter Übersetzungen anzeigen. Es funktioniert in Servern,
Direktnachrichten, Gruppen, Threads und Forenbeiträgen, sogar wenn Discord im Hintergrund ist. Nachrichten, die
schon in deiner Sprache sind, und deine eigenen werden übersprungen. Die Übersetzungen erscheinen nur, solange
Discord das aktive Fenster ist, sie verdecken also nie dein Spiel.

**Vorlesen.** Nur neue Nachrichten werden vorgelesen. Nachrichten, zu denen du zurückscrollst, bearbeitete und alte
Nachrichten werden auf dem Bildschirm übersetzt, aber nie vorgelesen. Chatnachrichten teilen sich die Stimme der
App mit den Übersetzungen aus dem Anruf, also sprechen die beiden nie gleichzeitig.

Der Tab Text hat weitere Werkzeuge:

- **Markieren zum Übersetzen.** Markiere Text oder doppelklicke ein Wort, und ein Popup mit der Übersetzung
  erscheint neben der Maus.
- **Strg+Alt+T** übersetzt die aktuelle Auswahl in jeder App.
- **Strg+Alt+Y** ersetzt, was du in Discords Nachrichtenfeld getippt hast, durch die Übersetzung in die Sprache,
  die in diesem Chat benutzt wird.
- **In ihrer Sprache schreiben.** Tippe im Tab Text, dann kopiere, füge in Discord ein oder sende.
- **Strg+Alt+O** lässt dich einen Rahmen über einen beliebigen Teil des Bildschirms ziehen. Die App liest den Text
  per OCR und zeigt die Übersetzung darüber. Das kann sich alle paar Sekunden wiederholen.
- **Kopierter Text.** Auf Wunsch wird alles übersetzt, was du kopierst.

Du kannst jedes Tastenkürzel im Tab Text ändern. Für OCR in anderen Schriften, etwa Russisch oder Japanisch, füge
die Sprache in den Windows-Einstellungen hinzu.

=== 9. Untertitel und Transkripte
# Untertitel und Transkripte

Das **Untertitelfenster** schwebt über deinem Spiel oder Discord. Zieh es, um es zu verschieben. Mit dem Mausrad
änderst du die Größe. Ein Rechtsklick zeigt Optionen, etwa wie viele Zeilen, ob der Originaltext gezeigt wird und
den Hintergrund. In den Einstellungen kannst du Textgröße und Schriftart ändern.

Jedes Gespräch kann als **Transkript** gespeichert werden. Das ist standardmäßig an, und du schaltest es im Tab
Ausgang aus. Transkripte werden im Ordner data unter transcripts gespeichert, und du kannst diesen Ordner über den
Tab Log oder die Einstellungen öffnen.

Der Tab Log zeigt in Echtzeit, was die App tut. Er hat auch Knöpfe, um die Logs, die Transkripte und den
App-Ordner zu öffnen. Wenn etwas schiefgeht, schau zuerst ins Log.

Die Statusleiste unten zeigt die Verzögerung jeder Stufe: Spracherkennung, Übersetzung und Stimme, damit du
siehst, welche Engine langsam ist.

=== 10. Einstellungen und Updates
# Einstellungen und Updates

Im Tab **Einstellungen** stellst du die Sprache der App ein. Nach einer Änderung startet die App in der neuen
Sprache neu. Außerdem sind dort alle Audiogeräte an einem Ort: was die App hört, dein Mikrofon, wo Übersetzungen
abgespielt werden und wohin deine übersetzte Stimme geht.

Er steuert das Aussehen der App: das Design, dunkel oder hell, die Schriftart und die Textgröße der App und der
Übersetzungen in Discord, im kleinen Chatfenster und in den Popups. Er hat auch alle Tastenkürzel an einem Ort,
eine Option, um das Fenster über anderen zu halten, und Knöpfe, um die Fensterpositionen zurückzusetzen und die
Ordner für App, Daten und Logs zu öffnen.

Die Option Änderungen automatisch speichern speichert dein Profil etwa eine Sekunde nach jeder Änderung. Sie ist
standardmäßig an.

**Updates.** Drücke Nach Updates suchen. Wenn es auf GitHub eine neuere Version gibt, erscheint der Knopf Jetzt
aktualisieren. Er lädt die neue Version herunter und ersetzt die Programmdateien. Deine Einstellungen, Profile,
API-Schlüssel und heruntergeladenen Modelle bleiben unberührt. Wenn sich die Liste der nötigen Pakete geändert hat,
werden sie ebenfalls aktualisiert. Danach bietet die App einen Neustart an. Die App prüft außerdem still ein paar
Sekunden nach dem Start.

=== 11. Fehlerbehebung
# Fehlerbehebung

**Führe den Selbsttest aus.** Öffne eine Konsole im App-Ordner und führe `runtime\python.exe tools\selftest.py`
aus. Er spielt einen Testsatz in das virtuelle Kabel und testet beide Richtungen. Endet er mit dem Wort PASS,
funktionieren Erkennung, Übersetzung und Stimme.

**Starte den Anruftest.** `runtime\python.exe tools\calltest.py` spielt einen gespielten Sprachanruf in das
virtuelle Kabel. Er prüft, dass jeder Satz der Reihe nach übersetzt wird, dass die App nie ihre eigene Stimme hört
und dass nie zwei Stimmen gleichzeitig laufen. Starte ihn, wenn du in keinem Discord-Anruf bist.

**Niemand hört meine Übersetzung.** In Discord muss das Eingabegerät CABLE Output sein. In der App muss der Tab
Ausgang an CABLE Input senden. Prüfe, ob die Rauschunterdrückung in Discord aus ist.

**Die App hört nichts.** Prüfe im Tab Eingang die Methode. Mit Nur die Discord-App muss Discord geöffnet sein. Mit
Loopback muss das Gerät das sein, auf dem Discord läuft. Schau auf die Pegelanzeigen im Tab Live. Wenn sie sich
nicht bewegen, stimmt die Einstellung nicht.

**Meine Übersetzung ist doppelt zu hören, oder die App übersetzt sich selbst.** Nutze im Tab Eingang die Methode
Nur die Discord-App und trage ein Headset.

**Discord ist stumm.** Das ist Absicht, solange der Übersetzer läuft: Drück F9, um die Leute auch zu hören. Wenn
Dizcord abrupt geschlossen wurde, öffne es einmal, dann gibt es Discord seine Lautstärke zurück, oder dreh Discord
im Windows-Lautstärkemixer wieder auf.

**Die Leute hören meine echte Stimme.** In Discord muss das Eingabegerät CABLE Output sein, nicht dein Mikrofon.
Die App zeigt eine Warnung, wenn Discord dein echtes Mikrofon nutzt.

**Eine Engine schlägt fehl.** Öffne den Tab Log. Eine Meldung mit forbidden oder blocked bedeutet meist, dass der
Schlüssel oder das Modell für dein Konto nicht erlaubt ist. Versuche eine andere Engine und teste erneut.

**Die Chat-Übersetzung zeigt nichts.** Achte darauf, dass Discord das aktive Fenster ist und der Knopf Chat an
ist. Die Funktion ist für die Desktop-App von Discord gemacht.

**Immer noch hängen geblieben.** Starte die App mit Dizcord debug Punkt bat. Es öffnet eine Konsole, die Fehler
zeigt, was hilft, wenn du ein Problem meldest.

=== 12. Über dieses Handbuch
# Über dieses Handbuch

Du liest das in Dizcord eingebaute Handbuch. Der Sprecher ist eine natürliche Stimme in der Sprache der App. Sie
läuft auf deinem PC, funktioniert offline und schickt nichts irgendwohin.

- **Weiter und Zurück** wechseln das Kapitel. Der Sprecher hört mit dem alten Kapitel auf und beginnt das neue, und
  der neue Text erscheint gleichzeitig.
- **Vorlesen** schaltet den Sprecher ein oder aus. Ist er aus, ist das Handbuch nur Text.
- **Nochmal lesen** beginnt das aktuelle Kapitel von vorne.
- **Stopp** bringt den Sprecher zum Schweigen.
- **Stimme** und **Tempo** ändern, wie er klingt. Neben der Offline-Stimme kannst du eine Online-Stimme wählen,
  die Internet braucht, oder eine der Windows-Stimmen.
- **Geführte Tour wiederholen** zeigt die ersten Schritte noch einmal.

Der Sprecher schweigt, wenn du diesen Tab verlässt, und er beginnt nie von selbst, während du den Übersetzer
benutzt.

Das ist das Ende des Handbuchs. Viel Spaß mit Dizcord!
