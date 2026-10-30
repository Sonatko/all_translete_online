=== 1. Bienvenida
# Te damos la bienvenida a Dizcord

Dizcord es un traductor en tiempo real para Discord y cualquier otro chat de voz. Funciona entero en tu PC.

- **Oyes a los demás en tu idioma.** La app escucha lo que dice la gente en Discord, lo escribe, lo traduce,
  muestra subtítulos y puede leerte la traducción con una voz natural.
- **Ellos te oyen en su idioma.** Hablas al micrófono. La app traduce lo que dijiste y lo dice en Discord a través
  de un cable de audio virtual.
- **También texto.** Traduce mensajes de Discord en servidores, mensajes directos e hilos, cualquier texto que
  selecciones con el ratón y el texto de la pantalla con OCR. También puedes escribir en su idioma.
- **Gratis para empezar.** El perfil llamado Gratis, sin claves, funciona sin cuenta y sin pagar. Los motores de
  pago en la nube son opcionales.

Este manual tiene doce capítulos. Usa los botones Siguiente y Anterior, o haz clic en un capítulo de la lista.
Cada vez que cambias de capítulo, el narrador deja el anterior y lee el nuevo. La voz es una voz natural en el
idioma de la app que funciona en tu PC. No necesita internet y no cuesta nada.

=== 2. Primer inicio
# Primer inicio

**Paso 1. Abre la app.** Haz doble clic en Dizcord.exe, o en Dizcord.bat. La primera vez, la app crea su propia
copia privada de Python dentro de su carpeta. Esto descarga unos 750 megabytes, tarda unos minutos y no necesita
permisos de administrador. No se instala nada en Windows.

Después eliges el idioma de la app. Todo se muestra en ese idioma, y la guía y este manual se leen en voz alta en
él. La app descarga la voz de ese idioma una vez, unos 60 megabytes. Luego, una visita guiada corta te enseña los
primeros pasos. Solo se abre esta primera vez; puedes repetirla desde esta pestaña.

**Paso 2. Instala un cable de audio virtual.** Instala VB-Audio Virtual Cable, que es gratis, y reinicia el PC.
Es lo único fuera de la carpeta, porque Windows necesita un controlador para crear un micrófono virtual.

**Paso 3. Configura Discord.** Abre Discord, luego Ajustes de usuario, luego Voz y vídeo.

- Dispositivo de entrada: CABLE Output, de VB-Audio Virtual Cable.
- Dispositivo de salida: tus auriculares.
- Desactiva la Supresión de ruido, la Cancelación de eco y el Control automático de ganancia.

**Paso 4. Configura la app.** Elige el perfil Gratis, sin claves. En la pestaña Salida, envía tu voz traducida a
CABLE Input. En la pestaña Entrada, deja el método Solo la app de Discord y elige tu micrófono real. En la pestaña
En directo, elige los idiomas. Luego pulsa Iniciar, o la tecla F5.

El modelo de voz, Whisper small, ocupa unos 460 megabytes y se descarga la primera vez que lo usas.

=== 3. La ventana principal
# La ventana principal

Arriba está el cuadro de perfil. Un perfil guarda todos tus ajustes de motores, idiomas y dispositivos. Puedes
guardar, guardar como, eliminar, importar y exportar perfiles. Los perfiles exportados nunca contienen tus claves
de API.

Tus cambios se guardan automáticamente un segundo después de hacerlos. Puedes desactivarlo en la pestaña Ajustes.

Junto al cuadro de perfil hay tres botones:

- **Subtítulos** muestra una ventana flotante de subtítulos que puedes arrastrar, cambiar de tamaño con la rueda
  del ratón y configurar con el clic derecho.
- **Chat** activa la traducción de los mensajes de texto de Discord.
- **Iniciar** pone en marcha el traductor de voz. La tecla F5 hace lo mismo.

Las pestañas son: Panel, En directo, Texto, Entrada, Salida, Voz a texto, Traducción, Modelo de IA, Voz, Claves de
API, Configuración, Ajustes, Manual y Registro. Los próximos capítulos explican las que más vas a usar.

=== 4. Panel
# Panel

El Panel es tu centro de control. Es la primera pestaña y lo muestra todo de un vistazo.

- La **tarjeta del traductor de voz** inicia y detiene la traducción de voz en directo, y muestra lo que está
  haciendo: reconociendo, traduciendo o hablando.
- La **tarjeta de la traducción del chat** inicia y detiene la traducción de los mensajes de Discord. También
  tiene la opción de leer en voz alta los mensajes traducidos, uno tras otro, o dejando que un mensaje nuevo
  interrumpa al que se está leyendo.
- La **tarjeta Tú** es donde pones tu nombre de Discord y el idioma en el que escribes.
- La **tarjeta de herramientas** tiene accesos a seleccionar para traducir, el OCR y la ventana de subtítulos.
- La **tarjeta de atajos** te recuerda tus atajos de teclado.
- Abajo, Últimas traducciones muestra las últimas frases traducidas.

Los ajustes que aparecen en dos sitios, por ejemplo en el Panel y en la pestaña Texto, siempre están sincronizados.

=== 5. Traducción de voz en directo
# Traducción de voz en directo

Es la función principal. Funciona en dos direcciones, y cada una se puede activar por separado.

**Entrada: ellos hablan, tú oyes.** La app escucha solo la app de Discord, así que nunca oye su propia voz, tu
juego ni tu música, y sigue escuchando mientras habla. Reconoce la voz, la traduce, muestra subtítulos y, si
quieres, dice la traducción. Eliges el idioma que hablan, o Detectar automáticamente. Elegir el idioma hace que el
reconocimiento en tu PC sea casi el doble de rápido.

**Saliente: tú hablas, ellos oyen.** La app escucha tu micrófono, traduce lo que dices y lo dice en Discord a
través del cable virtual. Tu propia voz no se envía a Discord, solo la traducción. La app te avisa si Discord usa
tu micrófono real en lugar del cable.

**Oír a las personas, la tecla F9.** Por defecto oyes solo las traducciones. Mientras el traductor funciona, la app
baja Discord en el mezclador de volumen de Windows y le devuelve el volumen cuando pulsas Detener. Pulsa F9, o el
botón Oír a las personas, para oír también sus propias voces. Puedes cambiar la tecla en la pestaña Entrada.

**Una sola voz, en orden.** Las traducciones de la llamada y los mensajes del chat leídos en voz alta comparten una
sola voz, así que nunca se pisan. Todo se dice en el orden en que se habló y no se salta nada: la siguiente frase
se prepara mientras suena la actual, y cuando se acumulan frases la voz habla un poco más rápido.

**Quién habla.** La voz de la app puede decir quién habló, por ejemplo las dos primeras letras del nombre, o el
nombre completo. Elígelo en la pestaña Salida, en La voz de la app. En las llamadas los nombres vienen de la propia
app de Discord: en la pestaña Salida, en Quién habla, añade una vez tu propia aplicación de Discord. Los mensajes
del chat siempre llevan el nombre del autor.

En la pestaña **En directo** defines los idiomas de las dos direcciones, ves los medidores de nivel y lees la
transcripción. Puedes usar un botón de pulsar para hablar, y el cuadro Escribe para hablar, donde escribes una
frase, se traduce y se dice en Discord. La opción Responder en el idioma que hablan hace que tu idioma de salida
siga el último idioma detectado de la otra persona.

En la pestaña **Entrada** eliges qué escuchar y cómo empieza tu micrófono: actividad de voz, pulsar para hablar o
alternar. También hay un control de sensibilidad. La app reconoce su propia voz cuando tu micrófono la oye, y la
ignora.

En la pestaña **Salida** eliges dónde suenan las traducciones, el cable virtual para tu voz, la voz de la app y
quién habla.

Todos los dispositivos de sonido están también juntos en un solo sitio, en la pestaña Ajustes, en Dispositivos de
sonido.

=== 6. Motores: voz a texto, traducción, IA y voz
# Motores

Cada paso de la traducción puede usar un motor distinto, y puedes cambiarlos cuando quieras. Se guardan en tu
perfil.

- **Pestaña Voz a texto.** Convierte la voz en texto. La opción gratis es Whisper, que funciona en tu PC. Las
  opciones en la nube necesitan una clave: OpenAI, Groq, Deepgram, ElevenLabs, Azure y Google. En esta pestaña hay
  una prueba de micrófono.
- **Pestaña Traducción.** La opción gratis es Google Translate, que no necesita clave. Otras son DeepL, Azure,
  LibreTranslate, MyMemory y el motor sin conexión Argos. Puedes elegir el tono: natural, informal, formal o
  literal. Un glosario fija cómo se traducen ciertas palabras, como nombres y términos de juegos.
- **Pestaña Modelo de IA.** Se usa cuando el motor de traducción es el modelo de IA. Puede ser un modelo en la nube
  o uno que funcione en tu PC, por ejemplo con Ollama o LM Studio. Puedes añadir instrucciones extra para jerga o
  nombres.
- **Pestaña Voz.** El motor que dice las traducciones. La opción gratis son las voces neuronales de Microsoft
  Edge. Piper y Kokoro funcionan sin conexión. ElevenLabs, OpenAI, Azure y Google son opciones de pago. Elige una
  voz para cada dirección, o deja que la app elija una voz natural para cada idioma. Para cada dirección también
  puedes ajustar la velocidad, el tono y el volumen de la voz. Funcionan con cualquier motor de voz.

Cada pestaña tiene un botón de prueba, para que compruebes un motor antes de usarlo.

Los perfiles iniciales son: Gratis, sin claves. OpenAI. Groq con Edge. Claude con ElevenLabs. Y Totalmente sin
conexión, con Whisper, Ollama y Piper.

=== 7. Claves de API
# Claves de API

Los motores gratis no necesitan claves. Si quieres un motor de pago o en la nube, necesitas una clave de API de esa
empresa.

Abre la pestaña **Claves de API** y pega cada clave en su cuadro. Todas las claves se guardan en un solo sitio, en
el archivo data, keys punto json, dentro de la carpeta de la app. Las claves nunca se guardan dentro de los perfiles
ni se incluyen al exportar un perfil, así que puedes compartir perfiles sin riesgo.

Mantén ese archivo en privado. Si copias la carpeta entera a otro PC, tus claves van con ella.

Los motores locales opcionales, como Piper, Kokoro, Argos y las bibliotecas para tarjetas gráficas NVIDIA, se
instalan con install extras punto bat, o con el botón Instalar ahora junto al motor en la app.

=== 8. Traducir texto de Discord
# Traducir texto de Discord

Pulsa el botón **Chat**, o usa la tarjeta del chat en el Panel. La app lee entonces los mensajes que ves en la app
de Discord, usando las funciones de accesibilidad de Windows, como un lector de pantalla. No necesita token ni bot,
y no envía nada a Discord.

Los mensajes nuevos se traducen y se dibujan sobre el texto original, dentro del propio Discord, o en una ventana
pequeña a su lado. Lo eliges en la pestaña Texto, en Mostrar traducciones. Funciona en servidores, mensajes
directos, grupos, hilos y publicaciones de foro, incluso con Discord en segundo plano. Los mensajes que ya están en
tu idioma, y tus propios mensajes, se omiten. Las traducciones solo se ven mientras Discord es la ventana activa,
así que nunca tapan tu juego.

**Lectura en voz alta.** Solo se leen en voz alta los mensajes nuevos. Los mensajes a los que vuelves
desplazándote, los editados y los antiguos se traducen en pantalla, pero nunca se leen. Los mensajes del chat
comparten la voz de la app con las traducciones de la llamada, así que nunca hablan a la vez.

La pestaña Texto tiene más herramientas:

- **Seleccionar para traducir.** Selecciona texto, o haz doble clic en una palabra, y aparece una ventanita con la
  traducción junto al ratón.
- **Ctrl+Alt+T** traduce la selección actual en cualquier app.
- **Ctrl+Alt+Y** sustituye lo que escribiste en el cuadro de mensajes de Discord por su traducción al idioma usado
  en ese chat.
- **Escribir en su idioma.** Escribe en la pestaña Texto y luego copia, pega en Discord o envía.
- **Ctrl+Alt+O** te deja arrastrar un recuadro sobre cualquier parte de la pantalla. La app lee el texto con OCR y
  muestra la traducción encima. Puede repetirse cada pocos segundos.
- **Texto copiado.** Opcionalmente, traduce todo lo que copias.

Puedes cambiar todos los atajos en la pestaña Texto. Para el OCR de otros alfabetos, como el ruso o el japonés,
añade ese idioma en la Configuración de Windows.

=== 9. Subtítulos y transcripciones
# Subtítulos y transcripciones

La **ventana de subtítulos** flota sobre tu juego o Discord. Arrástrala para moverla. Usa la rueda del ratón para
cambiar su tamaño. Haz clic derecho para ver opciones, como cuántas líneas mostrar, si se muestra el texto original
y el fondo. En Ajustes puedes cambiar el tamaño del texto y la fuente.

Cada conversación se puede guardar como una **transcripción**. Viene activado, y lo desactivas en la pestaña
Salida. Las transcripciones se guardan en la carpeta data, en transcripts, y puedes abrir esa carpeta desde la
pestaña Registro o desde Ajustes.

La pestaña Registro muestra lo que hace la app en tiempo real. También tiene botones para abrir los registros, las
transcripciones y la carpeta de la app. Si algo va mal, el registro es el primer sitio donde mirar.

La barra de estado de abajo muestra el retraso de cada etapa: reconocimiento de voz, traducción y voz, para que
veas qué motor va lento.

=== 10. Ajustes y actualizaciones
# Ajustes y actualizaciones

La pestaña **Ajustes** define el idioma de la app. Después de cambiarlo, la app se reinicia en el nuevo idioma.
También reúne todos los dispositivos de sonido en un solo sitio: lo que escucha la app, tu micrófono, dónde suenan
las traducciones y adónde va tu voz traducida.

Controla el aspecto de la app: el tema, oscuro o claro, la fuente y el tamaño del texto de la app y de las
traducciones que se muestran dentro de Discord, en la ventana pequeña del chat y en las ventanitas. También tiene
todos los atajos en un solo sitio, una opción para mantener la ventana encima de las demás, y botones para
restablecer las posiciones de las ventanas y abrir las carpetas de la app, de datos y de registros.

La opción Guardar cambios automáticamente mantiene tu perfil guardado un segundo después de cada cambio. Viene
activada.

**Actualizaciones.** Pulsa Buscar actualizaciones. Si hay una versión más nueva en GitHub, aparece el botón
Actualizar ahora. Descarga la nueva versión y sustituye los archivos del programa. Tus ajustes, perfiles, claves de
API y modelos descargados nunca se tocan. Si cambió la lista de paquetes necesarios, también se actualizan. Al
terminar, la app ofrece reiniciarse. La app también comprueba discretamente unos segundos después de abrirse.

=== 11. Solución de problemas
# Solución de problemas

**Ejecuta la autoprueba.** Abre una consola en la carpeta de la app y ejecuta
`runtime\python.exe tools\selftest.py`. Reproduce una frase de prueba en el cable virtual y prueba las dos
direcciones. Si termina con la palabra PASS, el reconocimiento, la traducción y la voz funcionan.

**Ejecuta la prueba de llamada.** `runtime\python.exe tools\calltest.py` reproduce una llamada de voz simulada en
el cable virtual. Comprueba que cada frase se traduce en orden, que la app nunca oye su propia voz y que nunca
suenan dos voces a la vez. Ejecútala cuando no estés en una llamada de Discord.

**Nadie oye mi traducción.** En Discord, el dispositivo de entrada tiene que ser CABLE Output. En la app, la
pestaña Salida tiene que enviar a CABLE Input. Comprueba que la Supresión de ruido está desactivada en Discord.

**La app no oye nada.** En la pestaña Entrada, revisa el método. Con Solo la app de Discord, Discord tiene que
estar abierto. Con loopback, el dispositivo tiene que ser donde suena Discord. Mira los medidores de nivel en la
pestaña En directo. Si no se mueven, el ajuste está mal.

**Mi traducción se oye dos veces, o la app se traduce a sí misma.** Usa el método Solo la app de Discord en la
pestaña Entrada, y usa auriculares.

**Discord no se oye.** Es a propósito mientras el traductor funciona: pulsa F9 para oír también a las personas. Si
Dizcord se cerró de golpe, ábrelo una vez y le devuelve el volumen a Discord, o sube Discord en el mezclador de
volumen de Windows.

**La gente oye mi voz real.** En Discord, el dispositivo de entrada tiene que ser CABLE Output, no tu micrófono. La
app muestra un aviso cuando Discord usa tu micrófono real.

**Un motor falla.** Abre la pestaña Registro. Un mensaje que dice forbidden, o blocked, suele significar que la
clave o el modelo no están permitidos para tu cuenta. Prueba otro motor y vuelve a probar.

**La traducción del chat no muestra nada.** Asegúrate de que Discord es la ventana activa y de que el botón Chat
está activado. La función está hecha para la app de escritorio de Discord.

**Sigues atascado.** Abre la app con Dizcord debug punto bat. Abre una consola que muestra los errores, lo que
ayuda cuando informas de un problema.

=== 12. Sobre este manual
# Sobre este manual

Estás leyendo el manual integrado en Dizcord. El narrador es una voz natural en el idioma de la app. Funciona en tu
PC, sin conexión, y no envía nada a ningún sitio.

- **Siguiente y Anterior** cambian de capítulo. El narrador deja de leer el capítulo anterior y empieza el nuevo,
  y el nuevo texto aparece a la vez.
- **Leer en voz alta** activa o desactiva el narrador. Cuando está desactivado, el manual es solo texto.
- **Leer otra vez** empieza el capítulo actual desde el principio.
- **Parar** hace callar al narrador.
- **Voz** y **Velocidad** cambian cómo suena. Además de la voz sin conexión, puedes elegir una voz en línea, que
  necesita internet, o una de las voces de Windows.
- **Repetir la visita guiada** vuelve a mostrar los primeros pasos.

El narrador se calla cuando sales de esta pestaña, y nunca empieza solo mientras usas el traductor.

Este es el final del manual. ¡Que disfrutes de Dizcord!
