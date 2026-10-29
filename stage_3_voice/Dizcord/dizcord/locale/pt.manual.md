=== 1. Bem-vindo
# Bem-vindo ao Dizcord

O Dizcord é um tradutor em tempo real para o Discord e qualquer outro chat de voz. Ele roda inteiro no seu PC.

- **Você ouve os outros no seu idioma.** O app escuta o que as pessoas dizem no Discord, escreve, traduz, mostra
  legendas e pode ler a tradução para você com uma voz natural.
- **Eles ouvem você no idioma deles.** Você fala no microfone. O app traduz o que você disse e fala no Discord
  por meio de um cabo de áudio virtual.
- **Texto também.** Ele traduz mensagens do Discord em servidores, mensagens diretas e tópicos, qualquer texto que
  você selecionar com o mouse, e texto da tela usando OCR. Você também pode escrever no idioma deles.
- **Grátis para começar.** O perfil chamado Grátis, sem chaves, funciona sem conta e sem pagamento. Os
  mecanismos pagos na nuvem são opcionais.

Este manual tem doze capítulos. Use os botões Próximo e Anterior, ou clique num capítulo da lista. Toda vez que
você muda de capítulo, o narrador para o antigo e lê o novo. A voz é uma voz natural no idioma do app que roda no
seu PC. Ela não precisa de internet e não custa nada.

=== 2. Primeiro início
# Primeiro início

**Passo 1. Abra o app.** Clique duas vezes em Dizcord.exe, ou em Dizcord.bat. Na primeira vez, o app monta a sua
própria cópia do Python dentro da pasta dele. Isso baixa cerca de 750 megabytes, leva alguns minutos e não
precisa de direitos de administrador. Nada é instalado no Windows.

Depois você escolhe o idioma do app. Tudo aparece nesse idioma, e o guia e este manual são lidos em voz alta
nele. O app baixa a voz desse idioma uma vez, cerca de 60 megabytes. Em seguida, um tour guiado curto mostra os
primeiros passos. Ele só abre nessa primeira vez; você pode vê-lo de novo nesta aba.

**Passo 2. Instale um cabo de áudio virtual.** Instale o VB-Audio Virtual Cable, que é grátis, e reinicie o PC.
É a única coisa fora da pasta, porque o Windows precisa de um driver para criar um microfone virtual.

**Passo 3. Configure o Discord.** Abra o Discord, depois Configurações de usuário, depois Voz e vídeo.

- Dispositivo de entrada: CABLE Output, do VB-Audio Virtual Cable.
- Dispositivo de saída: seus fones.
- Desligue Supressão de ruído, Cancelamento de eco e Controle automático de ganho.

**Passo 4. Configure o app.** Escolha o perfil Grátis, sem chaves. Na aba Saída, mande sua voz traduzida para CABLE
Input. Na aba Entrada, deixe o método Só o app do Discord e escolha o seu microfone de verdade. Na aba Ao vivo,
escolha os idiomas. Depois aperte Iniciar, ou a tecla F5.

O modelo de fala, Whisper small, tem cerca de 460 megabytes e é baixado na primeira vez que você o usa.

=== 3. A janela principal
# A janela principal

No topo fica a caixa de perfil. Um perfil guarda todas as suas configurações de mecanismos, idiomas e
dispositivos. Você pode salvar, salvar como, excluir, importar e exportar perfis. Perfis exportados nunca contêm
suas chaves de API.

Suas mudanças são salvas automaticamente cerca de um segundo depois que você as faz. Você pode desligar isso na
aba Configurações.

Ao lado da caixa de perfil há três botões:

- **Legendas** mostra uma janela flutuante de legendas que você pode arrastar, redimensionar com a roda do mouse
  e configurar com o clique direito.
- **Chat** liga a tradução das mensagens de texto do Discord.
- **Iniciar** começa o tradutor de voz. A tecla F5 faz o mesmo.

As abas são: Painel, Ao vivo, Texto, Entrada, Saída, Fala, Tradução, Modelo de IA, Voz, Chaves de API,
Configuração, Configurações, Manual e Log. Os próximos capítulos explicam as que você mais vai usar.

=== 4. Painel
# Painel

O Painel é o seu painel de controle. É a primeira aba e mostra tudo de uma vez.

- O **cartão do tradutor de voz** inicia e para a tradução de voz ao vivo, e mostra o que ele está fazendo:
  reconhecendo, traduzindo ou falando.
- O **cartão da tradução do chat** inicia e para a tradução das mensagens do Discord. Ele também tem a opção de
  ler as mensagens traduzidas em voz alta, uma depois da outra, ou deixando uma mensagem nova interromper a que
  está sendo lida.
- O **cartão Você** é onde você coloca seu nome no Discord e o idioma em que escreve.
- O **cartão de ferramentas** tem atalhos para selecionar para traduzir, OCR e a janela de legendas.
- O **cartão de atalhos** lembra os seus atalhos de teclado.
- Embaixo, Últimas traduções mostra as últimas frases traduzidas.

Opções que aparecem em dois lugares, por exemplo no Painel e na aba Texto, ficam sempre sincronizadas.

=== 5. Tradução de voz ao vivo
# Tradução de voz ao vivo

Esta é a função principal. Ela funciona em duas direções, e cada uma pode ser ligada separadamente.

**Entrada: eles falam, você ouve.** O app escuta só o app do Discord, então nunca ouve a própria voz, o seu jogo ou
a sua música, e continua ouvindo enquanto fala. Ele reconhece a fala, traduz, mostra legendas e, se você quiser,
fala a tradução. Você escolhe o idioma que eles falam, ou Detectar automaticamente. Escolher o idioma deixa o
reconhecimento no seu PC cerca de duas vezes mais rápido.

**Saída: você fala, eles ouvem.** O app escuta o seu microfone, traduz o que você diz e fala no Discord pelo cabo
virtual. Sua própria voz não é enviada ao Discord, só a tradução. O app avisa se o Discord usar o seu microfone de
verdade em vez do cabo.

**Ouvir as pessoas, a tecla F9.** Por padrão você ouve só as traduções. Enquanto o tradutor roda, o app abaixa o
Discord no mixer de volume do Windows e devolve o volume quando você aperta Parar. Aperte F9, ou o botão Ouvir as
pessoas, para ouvir também a voz delas. Você pode trocar a tecla na aba Entrada.

**Uma voz, em ordem.** As traduções da chamada e as mensagens do chat lidas em voz alta usam uma só voz, então
nunca falam uma por cima da outra. Tudo é dito na ordem em que foi falado, e nada é pulado: a próxima frase é
preparada enquanto a atual toca, e quando as frases se acumulam a voz fala um pouco mais rápido.

**Quem está falando.** A voz do app pode dizer quem falou, por exemplo as duas primeiras letras do nome, ou o nome
completo. Escolha isso na aba Saída, em A voz do app. Nas chamadas os nomes vêm do próprio app do Discord: na aba
Saída, em Quem está falando, adicione uma vez o seu próprio aplicativo do Discord. As mensagens do chat sempre têm
o nome do autor.

Na aba **Ao vivo** você define os idiomas das duas direções, vê os medidores de nível e lê a transcrição. Você
pode usar um botão de aperte para falar, e a caixa Digite para falar, onde você digita uma frase e ela é
traduzida e falada no Discord. A opção Responder no idioma que eles falam faz o seu idioma de saída seguir o
último idioma detectado da outra pessoa.

Na aba **Entrada** você escolhe o que escutar e como o seu microfone começa: detecção de voz, aperte para falar ou
alternar. Há também um controle de sensibilidade. O app reconhece a própria voz quando o seu microfone a ouve, e a
ignora.

Na aba **Saída** você escolhe onde as traduções tocam, o cabo virtual da sua voz, a voz do app e quem está falando.

Todos os dispositivos de som também ficam juntos num só lugar, na aba Configurações, em Dispositivos de som.

=== 6. Mecanismos: fala, tradução, IA e voz
# Mecanismos

Cada etapa da tradução pode usar um mecanismo diferente, e você pode trocá-los a qualquer momento. Eles ficam
salvos no seu perfil.

- **Aba Fala.** Transforma fala em texto. A opção grátis é o Whisper, que roda no seu PC. As opções na nuvem
  precisam de uma chave: OpenAI, Groq, Deepgram, ElevenLabs, Azure e Google. Há um teste de microfone nesta aba.
- **Aba Tradução.** A opção grátis é o Google Tradutor, que não precisa de chave. Outras são DeepL, Azure,
  LibreTranslate, MyMemory e o mecanismo offline Argos. Você pode definir o tom: natural, casual, formal ou
  literal. Um glossário fixa como certas palavras, como nomes e termos de jogo, são traduzidas.
- **Aba Modelo de IA.** Usada quando o mecanismo de tradução é o modelo de IA. Pode ser um modelo na nuvem ou um
  rodando no seu PC, por exemplo com Ollama ou LM Studio. Você pode adicionar instruções extras para gírias ou
  nomes.
- **Aba Voz.** O mecanismo que fala as traduções. A opção grátis são as vozes neurais do Microsoft Edge. Piper e
  Kokoro funcionam offline. ElevenLabs, OpenAI, Azure e Google são opções pagas. Escolha uma voz para cada
  direção, ou deixe o app escolher uma voz natural para cada idioma. Para cada direção você também pode definir a
  velocidade, o tom e o volume da voz. Eles funcionam com qualquer mecanismo de voz.

Cada aba tem um botão de teste, para você conferir um mecanismo antes de usá-lo.

Os perfis iniciais são: Grátis, sem chaves. OpenAI. Groq com Edge. Claude com ElevenLabs. E Totalmente offline,
com Whisper, Ollama e Piper.

=== 7. Chaves de API
# Chaves de API

Os mecanismos grátis não precisam de chaves. Se você quiser um mecanismo pago ou na nuvem, precisa de uma chave de
API dessa empresa.

Abra a aba **Chaves de API** e cole cada chave na sua caixa. Todas as chaves ficam num só lugar, no arquivo
data, keys ponto json, dentro da pasta do app. As chaves nunca ficam dentro dos perfis e nunca vão junto quando
você exporta um perfil, então você pode compartilhar perfis com segurança.

Mantenha esse arquivo privado. Se você copiar a pasta inteira para outro PC, suas chaves vão junto.

Mecanismos locais opcionais, como Piper, Kokoro, Argos e as bibliotecas para placas de vídeo NVIDIA, são
instalados com install extras ponto bat, ou com o botão Instalar agora ao lado do mecanismo no app.

=== 8. Traduzindo texto do Discord
# Traduzindo texto do Discord

Aperte o botão **Chat**, ou use o cartão do chat no Painel. O app então lê as mensagens que você vê no app do
Discord, usando os recursos de acessibilidade do Windows, como um leitor de tela. Ele não precisa de token nem de
bot, e não envia nada ao Discord.

As mensagens novas são traduzidas e desenhadas sobre o texto original, dentro do próprio Discord, ou numa janela
pequena ao lado dele. Você escolhe isso na aba Texto, em Mostrar traduções. Funciona em servidores, mensagens
diretas, grupos, tópicos e posts de fórum, mesmo com o Discord em segundo plano. Mensagens que já estão no seu
idioma, e as suas próprias mensagens, são puladas. As traduções só aparecem enquanto o Discord é a janela ativa,
então elas nunca cobrem o seu jogo.

**Leitura em voz alta.** Só as mensagens novas são lidas em voz alta. As mensagens para as quais você rola de
volta, as mensagens editadas e as antigas são traduzidas na tela, mas nunca lidas. As mensagens do chat usam a
mesma voz do app que as traduções da chamada, então as duas nunca falam ao mesmo tempo.

A aba Texto tem mais ferramentas:

- **Selecionar para traduzir.** Selecione um texto, ou dê clique duplo numa palavra, e aparece um popup com a
  tradução perto do mouse.
- **Ctrl+Alt+T** traduz a seleção atual em qualquer app.
- **Ctrl+Alt+Y** troca o que você digitou na caixa de mensagem do Discord pela tradução no idioma usado naquele
  chat.
- **Escrever no idioma deles.** Digite na aba Texto e depois copie, cole no Discord ou envie.
- **Ctrl+Alt+O** deixa você arrastar uma caixa sobre qualquer parte da tela. O app lê o texto com OCR e mostra a
  tradução por cima. Isso pode se repetir a cada poucos segundos.
- **Texto copiado.** Opcionalmente, traduz tudo o que você copia.

Você pode mudar todos os atalhos na aba Texto. Para OCR em outros alfabetos, como russo ou japonês, adicione esse
idioma nas Configurações do Windows.

=== 9. Legendas e transcrições
# Legendas e transcrições

A **janela de legendas** flutua sobre o seu jogo ou o Discord. Arraste para movê-la. Use a roda do mouse para
redimensioná-la. Clique com o botão direito para opções, como quantas linhas mostrar, se mostra o texto original
e o fundo. Nas Configurações você pode mudar o tamanho do texto e a fonte.

Cada conversa pode ser salva como uma **transcrição**. Isso vem ligado, e você desliga na aba Saída. As
transcrições são salvas na pasta data, em transcripts, e você pode abrir essa pasta pela aba Log ou pelas
Configurações.

A aba Log mostra o que o app está fazendo em tempo real. Ela também tem botões para abrir os logs, as
transcrições e a pasta do app. Se algo der errado, o log é o primeiro lugar para olhar.

A barra de status embaixo mostra o atraso de cada etapa: reconhecimento de fala, tradução e voz, para você ver
qual mecanismo está lento.

=== 10. Configurações e atualizações
# Configurações e atualizações

A aba **Configurações** define o idioma do app. Depois de mudá-lo, o app reinicia no novo idioma. Ela também
reúne todos os dispositivos de som num só lugar: o que o app escuta, o seu microfone, onde as traduções tocam e
para onde vai a sua voz traduzida.

Ela controla a aparência do app: o tema, escuro ou claro, a fonte e o tamanho do texto do app e das traduções
mostradas dentro do Discord, na janela pequena do chat e nos popups. Ela também tem todos os atalhos num só
lugar, uma opção para manter a janela acima das outras, e botões para redefinir as posições das janelas e abrir
as pastas do app, de dados e de logs.

A opção Salvar mudanças automaticamente mantém o seu perfil salvo cerca de um segundo depois de cada mudança. Ela
vem ligada.

**Atualizações.** Aperte Procurar atualizações. Se houver uma versão mais nova no GitHub, aparece o botão
Atualizar agora. Ele baixa a nova versão e substitui os arquivos do programa. Suas configurações, perfis, chaves
de API e modelos baixados nunca são tocados. Se a lista de pacotes necessários mudou, eles também são
atualizados. Quando termina, o app oferece reiniciar. O app também verifica discretamente alguns segundos depois
de abrir.

=== 11. Solução de problemas
# Solução de problemas

**Rode o autoteste.** Abra um console na pasta do app e rode `runtime\python.exe tools\selftest.py`. Ele toca
uma frase de teste no cabo virtual e roda as duas direções. Se terminar com a palavra PASS, reconhecimento,
tradução e voz estão funcionando.

**Rode o teste de chamada.** `runtime\python.exe tools\calltest.py` toca uma chamada de voz de mentira no cabo
virtual. Ele confere se cada frase é traduzida em ordem, se o app nunca ouve a própria voz e se duas vozes nunca
tocam ao mesmo tempo. Rode quando você não estiver numa chamada do Discord.

**Ninguém ouve a minha tradução.** No Discord, o dispositivo de entrada precisa ser CABLE Output. No app, a aba
Saída precisa enviar para CABLE Input. Confira se a Supressão de ruído está desligada no Discord.

**O app não ouve nada.** Na aba Entrada, confira o método. Com Só o app do Discord, o Discord precisa estar aberto.
Com loopback, o dispositivo precisa ser aquele onde o Discord toca. Olhe os medidores de nível na aba Ao vivo. Se
eles não se mexem, a configuração está errada.

**Minha tradução é ouvida duas vezes, ou o app traduz a si mesmo.** Use o método Só o app do Discord na aba
Entrada, e use fones.

**O Discord está mudo.** Isso é de propósito enquanto o tradutor roda: aperte F9 para ouvir as pessoas também. Se o
Dizcord foi fechado de repente, abra-o uma vez e ele devolve o volume do Discord, ou aumente o Discord no mixer de
volume do Windows.

**As pessoas ouvem a minha voz de verdade.** No Discord, o dispositivo de entrada precisa ser CABLE Output, não o
seu microfone. O app mostra um aviso quando o Discord usa o seu microfone de verdade.

**Um mecanismo falha.** Abra a aba Log. Uma mensagem que diz forbidden, ou blocked, geralmente significa que a
chave ou o modelo não é permitido para a sua conta. Tente outro mecanismo e teste de novo.

**A tradução do chat não mostra nada.** Confira se o Discord é a janela ativa e se o botão Chat está ligado. A
função foi feita para o app de computador do Discord.

**Ainda travado.** Abra o app com Dizcord debug ponto bat. Ele abre um console que mostra os erros, o que ajuda
quando você relata um problema.

=== 12. Sobre este manual
# Sobre este manual

Você está lendo o manual embutido no Dizcord. O narrador é uma voz natural no idioma do app. Ela roda no seu PC,
funciona offline e não envia nada para lugar nenhum.

- **Próximo e Anterior** mudam de capítulo. O narrador para de ler o capítulo antigo e começa o novo, e o novo
  texto aparece ao mesmo tempo.
- **Ler em voz alta** liga ou desliga o narrador. Quando está desligado, o manual é só texto.
- **Ler de novo** começa o capítulo atual do início.
- **Parar** silencia o narrador.
- **Voz** e **Velocidade** mudam como ele soa. Além da voz offline, você pode escolher uma voz online, que
  precisa de internet, ou uma das vozes do Windows.
- **Ver o tour guiado de novo** mostra os primeiros passos outra vez.

O narrador fica em silêncio quando você sai desta aba, e nunca começa sozinho enquanto você usa o tradutor.

Este é o fim do manual. Divirta-se com o Dizcord!
