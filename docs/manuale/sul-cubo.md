# Sul cubo

[Manuale](README.md) · [English](../manual/on-the-cube.md)

Il cubo mostra un'immagine 240×200 disegnata in Home Assistant e mandata via Wi-Fi al canale Pixel
di glimmer. Ecco cosa vedi.

## La nuvoletta

Ogni frase compare in una nuvoletta, divisa in pagine che girano ogni 4,5 secondi; mentre "parla",
il personaggio muove la bocca.

- Una frase resta `show_minutes` (20) o finché non arriva altro. Un **testo lungo** (il diario,
  una risposta lunga) continua a girare le pagine per tutto quel tempo — la bocca si muove solo nei
  primi due giri — così chi passa dopo lo legge tutto.
- Di notte le frasi spariscono dopo due minuti, tranne le risposte a te.

## La lavagnetta

Accanto ad Alessio, una tavoletta con:

- il **meteo della settimana** (3 giorni prima, oggi, 3 dopo) e, quando arrivano pioggia o raffiche,
  il **grafico orario**;
- il **radar** degli aerei intorno a casa;
- i grafici del **consumo di Claude** (con i sensori `sensor.claude_usage_*`);
- il **disegno** di oggi, in pixel art 24×24 disegnato da Claude (al massimo ogni `drawing_hours`);
- la **galleria** degli ultimi disegni.

`cards: false` la spegne.

## Le schermate a tutto cubo

Con `screens: true` (predefinito), immagini che occupano tutto il cubo:

- **meteo**: la settimana a confronto con i giorni prima;
- **casa**: chi c'è, le temperature delle stanze con la variazione dell'ultima ora, le luci accese;
- **corrente**: con `power_sensor` (W) ed `energy_sensor` (kWh da mezzanotte), adesso e oggi contro
  ieri.

Lavagnette e schermate restano finché non arriva altro (`show_minutes`, almeno `card_seconds`).

## La vetrina del giorno

Quello che il personaggio ha fatto o calcolato oggi torna a giro quando non c'è niente di nuovo: il
grafico della settimana, le schermate della casa e della corrente, il disegno di oggi, la curiosità
del giorno, il diario (quello di ieri finché non scrive quello di stasera), le frasi migliori del
regista delle ultime 3 ore (non quelle con le temperature di adesso, che invecchiano).

- Ogni cosa torna almeno 20 minuti dopo che è uscita; se sul cubo c'è solo la faccia, dopo 6.
- Con la sola faccia sul cubo, la chiacchiera successiva arriva dopo 1 minuto.

## Le chiacchiere

Frasi costruite dai dati senza Claude, scelte a giro: meteo di adesso, previsioni, la casa, chi c'è,
notizie, il sole, il giorno, aerei vicini, una curiosità, l'agenda, il consumo delle API, la
vetrina. Ogni tipo ha un intervallo minimo e un tetto al giorno, spalmato sulle ore di veglia perché
anche la sera ci sia qualcosa da dire; la stessa identica frase non torna prima di 3 ore. I tetti si
cambiano con `chatter_day_max` (nomi del log: `news.headline`, `weather.now`…).

## Le foto di famiglia

Manda una foto al bot di Telegram: compare subito, quasi a tutto schermo nella cornice della
lavagnetta, poi torna a giro ogni `photo_every_minutes` (30) per `photo_seconds` (40), ogni foto al
massimo `photo_day_max` (3) volte al giorno, mai di notte. Se ne tengono fino a `photo_max` (50): le
più vecchie si tolgono.

- L'album è `/media/coinquilino` (`photo_dir`): si gestisce dal pannello *Media* di Home Assistant.
- Dalla plancia: ne scegli una (`photo_select`), la mostri subito, la togli.
- Su Telegram: `/foto` dice quante sono; rispondi «togli» a una foto che hai mandato per toglierla.
- Le foto non escono di casa: non vanno a Claude.

## La cameretta

Con `scenes: true` la cameretta di Alessio cambia: i colori e la finestra della stagione, nebbia e
neve vere dal meteo, un calendarietto con la data, un oggetto diverso sulla mensola ogni giorno,
preso dagli interessi del personaggio. Gli aerei sopra casa si vedono dalla finestra.

## Le feste e i costumi

Halloween, Natale, Capodanno, Pasqua, i compleanni (`birthdays`) e il santo patrono (`local_feast`)
portano costumi e addobbi, e una frase la prima volta della giornata. `feste: false` li spegne.

## L'umore

La faccia segue un umore: `happy`, `welcome` (è arrivato qualcuno), `rain`, `sleep`, `tired`
(sessione di Claude sopra `tired_at`), `moto` (giornata da moto: `moto_days` con la temperatura
giusta). Il regista può cambiarlo per qualche minuto; anche `mood` in `coinquilino_say`.

## La notte

Da `night_start` a `night_end`:

- `night_clock: alessio` (predefinito) — il suo orologio scuro: l'ora grande, la data in italiano,
  la luna, qualche stella, Alessio che dorme in un angolo; cambia una volta al minuto;
- `night_clock: glimmer` — il quadrante notturno di glimmer;
- `night_clock: off` — la cameretta scurita da `night_dim`.

Sta zitto fino al mattino (le risposte a te arrivano comunque); gli avvisi con `night: defer` li dice
al risveglio.

## Bandit

`character: bandit` sostituisce Alessio con una moto in pixel art: stesse funzioni, frasi sue, non
cresce.
