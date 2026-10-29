=== 1. Benvenuto
# Benvenuto in Dizcord

Dizcord è un traduttore in tempo reale per Discord e qualsiasi altra chat vocale. Funziona interamente sul tuo PC.

- **Senti gli altri nella tua lingua.** L'app ascolta ciò che le persone dicono su Discord, lo scrive, lo traduce,
  mostra i sottotitoli e può leggerti la traduzione con una voce naturale.
- **Loro sentono te nella loro lingua.** Parli nel microfono. L'app traduce ciò che hai detto e lo pronuncia su
  Discord tramite un cavo audio virtuale.
- **Anche il testo.** Traduce i messaggi di Discord nei server, nei messaggi diretti e nei thread, qualsiasi testo
  che evidenzi col mouse e il testo sullo schermo con l'OCR. Puoi anche scrivere nella loro lingua.
- **Gratis per iniziare.** Il profilo Gratis, senza chiavi, funziona senza account e senza pagare. I motori a
  pagamento nel cloud sono facoltativi.

Questo manuale ha dodici capitoli. Usa i pulsanti Avanti e Precedente, oppure clicca su un capitolo nell'elenco.
Ogni volta che cambi capitolo, il narratore smette di leggere il vecchio e legge il nuovo. La voce è una voce
naturale nella lingua dell'app che gira sul tuo PC. Non serve internet e non costa nulla.

=== 2. Primo avvio
# Primo avvio

**Passo 1. Apri l'app.** Fai doppio clic su Dizcord.exe, o su Dizcord.bat. La prima volta l'app crea la propria
copia di Python dentro la sua cartella. Scarica circa 750 megabyte, richiede qualche minuto e non servono diritti di
amministratore. In Windows non viene installato nulla.

Poi scegli la lingua dell'app. Tutto appare in quella lingua, e la guida e questo manuale vengono letti ad alta
voce in quella lingua. L'app scarica una volta la voce di quella lingua, circa 60 megabyte. Dopo, un breve tour
guidato ti mostra i primi passi. Si apre solo questa prima volta; puoi rivederlo da questa scheda.

**Passo 2. Installa un cavo audio virtuale.** Installa VB-Audio Virtual Cable, che è gratis, e riavvia il PC. È
l'unica cosa fuori dalla cartella, perché Windows ha bisogno di un driver per creare un microfono virtuale.

**Passo 3. Configura Discord.** Apri Discord, poi Impostazioni utente, poi Voce e video.

- Dispositivo di input: CABLE Output, di VB-Audio Virtual Cable.
- Dispositivo di output: le tue cuffie.
- Disattiva Soppressione del rumore, Cancellazione dell'eco e Controllo automatico del guadagno.

**Passo 4. Configura l'app.** Scegli il profilo Gratis, senza chiavi. Nella scheda Uscita, manda la tua voce
tradotta su CABLE Input. Nella scheda Ingresso, lascia il metodo Solo l'app Discord e scegli il tuo vero microfono.
Nella scheda Dal vivo, scegli le lingue. Poi premi Avvia, o il tasto F5.

Il modello vocale, Whisper small, pesa circa 460 megabyte e si scarica la prima volta che lo usi.

=== 3. La finestra principale
# La finestra principale

In alto c'è la casella dei profili. Un profilo conserva tutte le impostazioni di motori, lingue e dispositivi. Puoi
salvare, salvare con nome, eliminare, importare ed esportare i profili. I profili esportati non contengono mai le
tue chiavi API.

Le modifiche si salvano automaticamente circa un secondo dopo averle fatte. Puoi disattivarlo nella scheda
Impostazioni.

Accanto alla casella dei profili ci sono tre pulsanti:

- **Sottotitoli** mostra una finestra mobile dei sottotitoli che puoi trascinare, ridimensionare con la rotellina e
  configurare col clic destro.
- **Chat** attiva la traduzione dei messaggi di testo di Discord.
- **Avvia** fa partire il traduttore vocale. Il tasto F5 fa lo stesso.

Le schede sono: Pannello, Dal vivo, Testo, Ingresso, Uscita, Parlato, Traduzione, Modello IA, Voce, Chiavi API,
Configurazione, Impostazioni, Manuale e Log. I prossimi capitoli spiegano quelle che userai di più.

=== 4. Pannello
# Pannello

Il Pannello è la tua centrale di controllo. È la prima scheda e mostra tutto a colpo d'occhio.

- La **scheda del traduttore vocale** avvia e ferma la traduzione vocale dal vivo, e mostra cosa sta facendo:
  riconoscimento, traduzione o pronuncia.
- La **scheda della traduzione della chat** avvia e ferma la traduzione dei messaggi di Discord. Ha anche l'opzione
  di leggere ad alta voce i messaggi tradotti, uno dopo l'altro, oppure lasciando che un nuovo messaggio
  interrompa quello in lettura.
- La **scheda Tu** è dove inserisci il tuo nome su Discord e la lingua in cui scrivi.
- La **scheda degli strumenti** ha scorciatoie per evidenzia per tradurre, l'OCR e la finestra dei sottotitoli.
- La **scheda delle scorciatoie** ti ricorda le scorciatoie da tastiera.
- In basso, Ultime traduzioni mostra le ultime frasi tradotte.

Le impostazioni che compaiono in due posti, per esempio nel Pannello e nella scheda Testo, restano sempre
sincronizzate.

=== 5. Traduzione vocale dal vivo
# Traduzione vocale dal vivo

È la funzione principale. Funziona in due direzioni, e ognuna si può attivare separatamente.

**In entrata: loro parlano, tu senti.** L'app ascolta solo l'app Discord, quindi non sente mai la propria voce, il
tuo gioco o la tua musica, e continua ad ascoltare mentre parla. Riconosce il parlato, lo traduce, mostra i
sottotitoli e, se vuoi, pronuncia la traduzione. Scegli la lingua che parlano, o Rilevamento automatico. Scegliere
la lingua rende il riconoscimento sul tuo PC circa due volte più veloce.

**In uscita: tu parli, loro sentono.** L'app ascolta il tuo microfono, traduce ciò che dici e lo pronuncia su
Discord tramite il cavo virtuale. La tua voce non viene inviata a Discord, solo la traduzione. L'app ti avvisa se
Discord usa il tuo vero microfono invece del cavo.

**Senti le persone, il tasto F9.** Di base senti solo le traduzioni. Mentre il traduttore è attivo, l'app abbassa
Discord nel mixer del volume di Windows e gli ridà il volume quando premi Ferma. Premi F9, o il pulsante Senti le
persone, per sentire anche le loro voci. Puoi cambiare il tasto nella scheda Ingresso.

**Una sola voce, in ordine.** Le traduzioni della chiamata e i messaggi della chat letti ad alta voce condividono
una sola voce, quindi non parlano mai uno sopra l'altro. Tutto viene detto nell'ordine in cui è stato pronunciato e
niente viene saltato: la frase successiva viene preparata mentre suona quella attuale, e quando le frasi si
accumulano la voce parla un po' più veloce.

**Chi sta parlando.** La voce dell'app può dire chi ha parlato, per esempio le prime due lettere del nome, o il
nome completo. Sceglilo nella scheda Uscita, sotto La voce dell'app. Nelle chiamate i nomi arrivano dall'app
Discord stessa: nella scheda Uscita, sotto Chi sta parlando, aggiungi una volta la tua applicazione Discord. I
messaggi della chat hanno sempre il nome dell'autore.

Nella scheda **Dal vivo** imposti le lingue delle due direzioni, guardi gli indicatori di livello e leggi la
trascrizione. Puoi usare un pulsante push-to-talk, e la casella Scrivi per parlare, dove scrivi una frase che viene
tradotta e pronunciata su Discord. L'opzione Rispondi nella lingua che parlano fa seguire alla tua lingua di uscita
l'ultima lingua rilevata dall'altra persona.

Nella scheda **Ingresso** scegli cosa ascoltare e come parte il tuo microfono: rilevamento vocale, push-to-talk o
alternanza. C'è anche un controllo della sensibilità. L'app riconosce la propria voce quando il tuo microfono la
sente, e la ignora.

Nella scheda **Uscita** scegli dove suonano le traduzioni, il cavo virtuale per la tua voce, la voce dell'app e chi
sta parlando.

Tutti i dispositivi audio sono anche riuniti in un unico posto, nella scheda Impostazioni, sotto Dispositivi audio.

=== 6. Motori: parlato, traduzione, IA e voce
# Motori

Ogni passaggio della traduzione può usare un motore diverso, e puoi cambiarli in qualsiasi momento. Vengono salvati
nel tuo profilo.

- **Scheda Parlato.** Trasforma la voce in testo. La scelta gratuita è Whisper, che gira sul tuo PC. Le scelte nel
  cloud richiedono una chiave: OpenAI, Groq, Deepgram, ElevenLabs, Azure e Google. In questa scheda c'è una prova
  del microfono.
- **Scheda Traduzione.** La scelta gratuita è Google Traduttore, senza chiave. Le altre sono DeepL, Azure,
  LibreTranslate, MyMemory e il motore offline Argos. Puoi scegliere il tono: naturale, informale, formale o
  letterale. Un glossario stabilisce come tradurre certe parole, come nomi e termini di gioco.
- **Scheda Modello IA.** Si usa quando il motore di traduzione è il modello IA. Può essere un modello nel cloud o
  uno che gira sul tuo PC, per esempio con Ollama o LM Studio. Puoi aggiungere istruzioni extra per slang o nomi.
- **Scheda Voce.** Il motore che pronuncia le traduzioni. La scelta gratuita sono le voci neurali di Microsoft
  Edge. Piper e Kokoro funzionano offline. ElevenLabs, OpenAI, Azure e Google sono a pagamento. Scegli una voce per
  ogni direzione, o lascia che l'app scelga una voce naturale per ogni lingua. Per ogni direzione puoi anche
  impostare velocità, intonazione e volume della voce. Funzionano con qualsiasi motore vocale.

Ogni scheda ha un pulsante di prova, così puoi controllare un motore prima di usarlo.

I profili iniziali sono: Gratis, senza chiavi. OpenAI. Groq con Edge. Claude con ElevenLabs. E Completamente
offline, con Whisper, Ollama e Piper.

=== 7. Chiavi API
# Chiavi API

I motori gratuiti non hanno bisogno di chiavi. Se vuoi un motore a pagamento o nel cloud, ti serve una chiave API di
quell'azienda.

Apri la scheda **Chiavi API** e incolla ogni chiave nella sua casella. Tutte le chiavi stanno in un unico posto, nel
file data, keys punto json, dentro la cartella dell'app. Le chiavi non vengono mai salvate nei profili né incluse
quando esporti un profilo, quindi puoi condividere i profili senza rischi.

Tieni privato quel file. Se copi l'intera cartella su un altro PC, le tue chiavi vanno con lei.

I motori locali facoltativi, come Piper, Kokoro, Argos e le librerie per le schede video NVIDIA, si installano con
install extras punto bat, o con il pulsante Installa ora accanto al motore nell'app.

=== 8. Tradurre il testo di Discord
# Tradurre il testo di Discord

Premi il pulsante **Chat**, o usa la scheda della chat nel Pannello. L'app legge allora i messaggi che vedi
nell'app di Discord, usando le funzioni di accessibilità di Windows, come un lettore di schermo. Non servono token
né bot, e non invia nulla a Discord.

I nuovi messaggi vengono tradotti e mostrati sopra il testo originale, direttamente dentro Discord, o in una
piccola finestra accanto. Lo scegli nella scheda Testo, sotto Mostra le traduzioni. Funziona nei server, nei
messaggi diretti, nei gruppi, nei thread e nei post del forum, anche con Discord in secondo piano. I messaggi già
nella tua lingua, e i tuoi messaggi, vengono saltati. Le traduzioni si vedono solo mentre Discord è la finestra
attiva, quindi non coprono mai il tuo gioco.

**Lettura ad alta voce.** Solo i messaggi nuovi vengono letti ad alta voce. I messaggi a cui torni scorrendo,
quelli modificati e quelli vecchi vengono tradotti sullo schermo, ma mai letti. I messaggi della chat condividono
la voce dell'app con le traduzioni della chiamata, quindi le due non parlano mai insieme.

La scheda Testo ha altri strumenti:

- **Evidenzia per tradurre.** Seleziona del testo, o fai doppio clic su una parola, e accanto al mouse appare un
  popup con la traduzione.
- **Ctrl+Alt+T** traduce la selezione attuale in qualsiasi app.
- **Ctrl+Alt+Y** sostituisce ciò che hai scritto nella casella dei messaggi di Discord con la traduzione nella
  lingua usata in quella chat.
- **Scrivi nella loro lingua.** Scrivi nella scheda Testo, poi copia, incolla su Discord o invia.
- **Ctrl+Alt+O** ti fa trascinare un riquadro su qualsiasi parte dello schermo. L'app legge il testo con l'OCR e
  mostra la traduzione sopra. Può ripetersi ogni pochi secondi.
- **Testo copiato.** Facoltativamente traduce tutto ciò che copi.

Puoi cambiare ogni scorciatoia nella scheda Testo. Per l'OCR di altri alfabeti, come il russo o il giapponese,
aggiungi quella lingua nelle Impostazioni di Windows.

=== 9. Sottotitoli e trascrizioni
# Sottotitoli e trascrizioni

La **finestra dei sottotitoli** fluttua sopra il gioco o Discord. Trascinala per spostarla. Usa la rotellina per
ridimensionarla. Clic destro per le opzioni, come quante righe mostrare, se mostrare il testo originale e lo
sfondo. Nelle Impostazioni puoi cambiare la dimensione del testo e il carattere.

Ogni conversazione può essere salvata come **trascrizione**. È attivo di serie, e lo disattivi nella scheda Uscita.
Le trascrizioni si salvano nella cartella data, sotto transcripts, e puoi aprire quella cartella dalla scheda Log o
dalle Impostazioni.

La scheda Log mostra cosa fa l'app in tempo reale. Ha anche pulsanti per aprire i log, le trascrizioni e la
cartella dell'app. Se qualcosa va storto, il log è il primo posto da guardare.

La barra di stato in basso mostra il ritardo di ogni fase: riconoscimento vocale, traduzione e voce, così vedi
quale motore è lento.

=== 10. Impostazioni e aggiornamenti
# Impostazioni e aggiornamenti

La scheda **Impostazioni** imposta la lingua dell'app. Dopo averla cambiata, l'app si riavvia nella nuova lingua.
Riunisce anche tutti i dispositivi audio in un unico posto: cosa ascolta l'app, il tuo microfono, dove suonano le
traduzioni e dove va la tua voce tradotta.

Controlla l'aspetto dell'app: il tema, scuro o chiaro, il carattere e la dimensione del testo dell'app e delle
traduzioni mostrate dentro Discord, nella finestra piccola della chat e nei popup. Ha anche tutte le scorciatoie in
un unico posto, un'opzione per tenere la finestra sopra le altre, e pulsanti per ripristinare la posizione delle
finestre e aprire le cartelle dell'app, dei dati e dei log.

L'opzione Salva le modifiche automaticamente mantiene il profilo salvato circa un secondo dopo ogni modifica. È
attiva di serie.

**Aggiornamenti.** Premi Cerca aggiornamenti. Se su GitHub c'è una versione più recente, appare il pulsante Aggiorna
ora. Scarica la nuova versione e sostituisce i file del programma. Impostazioni, profili, chiavi API e modelli
scaricati non vengono mai toccati. Se l'elenco dei pacchetti necessari è cambiato, vengono aggiornati anche quelli.
Alla fine l'app propone di riavviarsi. L'app controlla anche in silenzio qualche secondo dopo l'avvio.

=== 11. Risoluzione dei problemi
# Risoluzione dei problemi

**Esegui l'autotest.** Apri una console nella cartella dell'app ed esegui `runtime\python.exe tools\selftest.py`.
Riproduce una frase di prova nel cavo virtuale e prova entrambe le direzioni. Se finisce con la parola PASS,
riconoscimento, traduzione e voce funzionano.

**Esegui il test di chiamata.** `runtime\python.exe tools\calltest.py` riproduce una finta chiamata vocale nel cavo
virtuale. Controlla che ogni frase sia tradotta in ordine, che l'app non senta mai la propria voce e che due voci
non suonino mai insieme. Eseguilo quando non sei in una chiamata Discord.

**Nessuno sente la mia traduzione.** In Discord, il dispositivo di input deve essere CABLE Output. Nell'app, la
scheda Uscita deve inviare a CABLE Input. Controlla che in Discord la Soppressione del rumore sia disattivata.

**L'app non sente nulla.** Nella scheda Ingresso, controlla il metodo. Con Solo l'app Discord, Discord deve essere
aperto. Con loopback, il dispositivo deve essere quello su cui suona Discord. Guarda gli indicatori di livello
nella scheda Dal vivo. Se non si muovono, l'impostazione è sbagliata.

**La mia traduzione si sente due volte, o l'app traduce se stessa.** Usa il metodo Solo l'app Discord nella scheda
Ingresso, e usa le cuffie.

**Discord è muto.** È voluto mentre il traduttore è attivo: premi F9 per sentire anche le persone. Se Dizcord è
stato chiuso di colpo, aprilo una volta e ridà il volume a Discord, oppure alza Discord nel mixer del volume di
Windows.

**Le persone sentono la mia vera voce.** In Discord, il dispositivo di input deve essere CABLE Output, non il tuo
microfono. L'app mostra un avviso quando Discord usa il tuo vero microfono.

**Un motore non funziona.** Apri la scheda Log. Un messaggio che dice forbidden, o blocked, di solito significa che
la chiave o il modello non è consentito per il tuo account. Prova un altro motore, poi riprova.

**La traduzione della chat non mostra nulla.** Assicurati che Discord sia la finestra attiva e che il pulsante Chat
sia acceso. La funzione è pensata per l'app desktop di Discord.

**Ancora bloccato.** Avvia l'app con Dizcord debug punto bat. Apre una console che mostra gli errori, utile quando
segnali un problema.

=== 12. Su questo manuale
# Su questo manuale

Stai leggendo il manuale integrato in Dizcord. Il narratore è una voce naturale nella lingua dell'app. Gira sul tuo
PC, funziona offline e non invia nulla da nessuna parte.

- **Avanti e Precedente** cambiano capitolo. Il narratore smette di leggere il vecchio capitolo e inizia il nuovo, e
  il nuovo testo appare nello stesso momento.
- **Leggi ad alta voce** accende o spegne il narratore. Quando è spento, il manuale è solo testo.
- **Rileggi** ricomincia il capitolo attuale dall'inizio.
- **Ferma** zittisce il narratore.
- **Voce** e **Velocità** cambiano il suono. Oltre alla voce offline, puoi scegliere una voce online, che richiede
  internet, o una delle voci di Windows.
- **Rivedi il tour guidato** mostra di nuovo i primi passi.

Il narratore tace quando lasci questa scheda, e non parte mai da solo mentre usi il traduttore.

Questa è la fine del manuale. Buon divertimento con Dizcord!
