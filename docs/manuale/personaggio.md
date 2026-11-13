# Il personaggio

[Manuale](README.md) · [English](../manual/character.md)

## Alessio

Un ragazzino di 10 anni (`age`), sveglio e un po' ironico, che chiama il padrone di casa "Zio". Ogni
frase deve portare qualcosa di concreto — un numero, un'ora, una differenza con ieri, una cosa da
fare — senza parlare da bimbo. Da 8 anni in su ha capelli, sopracciglia e maglietta; con
`grow: true` cresce col tempo (da `start_age`, un anno ogni `grow_days`, fino a
`max_age`).

`about_owner`, `family` e `nicknames` dicono a Claude chi abita in casa; `persona` sostituisce
l'intera descrizione, se vuoi un personaggio diverso.

## Il regista

Ogni `chatter_minutes` (25), se qualcuno di `presence` è in casa e sveglio e il cubo è libero,
Claude riceve quello che il personaggio sa — la casa, il meteo a confronto con i giorni prima, le
notizie, gli aerei, l'agenda, i fatti di oggi, i ricordi, gli argomenti già detti oggi — e scrive la
frase che vale di più, con un umore. Può anche segnare una notizia come raccontata e, con
`autonomy`, aggiungere un breve avviso per il telefono (al massimo uno ogni 3 ore).

Dalla 3.1 ogni turno ha un **argomento**, sorteggiato con un peso fra quelli che oggi hanno ancora
posto:

| Argomento | Peso | Al giorno | Cosa riceve Claude |
|---|---|---|---|
| `curiosita` | 5 | senza tetto | un tema che interessa a un ragazzino di 10 anni (`curiosities`), mai uno degli ultimi 20; Claude indica la voce di Wikipedia in italiano e la sua foto va sulla lavagnetta |
| `notizia` | 2 | 3 | le notizie non ancora raccontate; se nessuna è interessante salta |
| `meteo` | 2 | 2 | previsioni e confronti; solo un cambio vero, altrimenti salta |
| `casa` | 1 | 2 | chi c'è, agenda, temperature delle stanze, fatti di oggi, ricordi |
| `ricordo` | 1 | 1 | la memoria lunga |
| `domanda` | 1 | 1 | una domanda su un tema |
| `aerei` | 1 | 1 | l'aereo più vicino (solo se c'è) |

I tetti si cambiano con `director_topics_max` (per esempio `{curiosita: 0}` spegne le curiosità).
I ricordi lunghi arrivano solo per `ricordo` e `casa`. Le frasi non cominciano mai con il nome di
chi ascolta; quelle con le correzioni di Claude ("no, aspetta") e quelle con gradi, percentuali o
km/h che non sono nei dati si scartano; l'ora di adesso si toglie.

Gli argomenti già detti oggi (meteo di domani, aggiornamenti, temperature di adesso, consumo di
Claude, aerei) si riconoscono dal testo e non si ripetono; le temperature tornano solo se sono
cambiate di 2 gradi o sono passate 3 ore, oppure se le chiedi.

## Gli eventi a cui reagisce

| Evento | Frase |
|---|---|
| arriva qualcuno | un saluto, scritto da Claude (chi arriva insieme: un saluto solo) |
| esce qualcuno | "Fuori casa: Anna e Mario." (raggruppati) |
| pioggia in arrivo / smette / vento forte | un avviso (la fine della pioggia solo se ha smesso davvero) |
| cambio delle previsioni | "Domani 5 gradi in meno di oggi" (una volta al giorno) |
| mattino | il saluto con oggi a confronto con ieri |
| aereo sopra casa | compagnia, modello, quota, rotta |
| feste, compleanni | una frase e il costume |
| una stanza che cambia in fretta | "Studio: 2 gradi in meno in mezz'ora. Finestra aperta?" |
| sessione di Claude quasi finita / di nuovo piena | con i sensori `sensor.claude_usage_*` |
| `coinquilino_say` | quello che manda Home Assistant ([dettagli](home-assistant.md)) |

## La memoria

- **I fatti di oggi**: arrivi, uscite, avvisi, chat, quello che Home Assistant chiede di ricordare
  (`remember`). Servono al regista e al diario.
- **Il diario**: da `diary_at` (21:00) scrive qualche riga sulla giornata; il giorno dopo lo mostra
  nella vetrina.
- **La memoria lunga**: ogni notte alle `night_job_at` (03:30) Claude riscrive la lista dei ricordi
  con quello che vale per settimane: gusti delle persone, progetti, cose in sospeso. Conosce l'età
  di oggi del personaggio e lascia fuori le descrizioni di sé, gli andirivieni delle persone, i nomi
  dei dispositivi, le richieste sul programma.
- In chat:
  - *"ricordati che Anna ha la verifica venerdì"* — aggiunge un ricordo;
  - *"dimentica la verifica"* — lo toglie;
  - *"non parlare più di aerei"* — blocca un interesse per sempre (e toglie i ricordi su quello);
  - *"puoi riparlare di aerei"* — lo sblocca.

## Carattere e interessi

Tratti (curioso, ironico, chiacchierone…) e interessi si spostano un po' ogni domenica notte, in base
a quello che ti è piaciuto: i pulsanti 👍/👎 (`feedback_up` / `feedback_down`, o sotto i messaggi
Telegram) e se rispondi a quello che dice. Impara anche qualche curiosità alla settimana, che dice
come "Lo sapevi che…" e tiene nella vetrina. I tormentoni che ripete troppo vengono riconosciuti e
vietati.

## Scrive lui per primo

Con `spontaneous: true`, al massimo una volta al giorno, di giorno: un'idea per una cosa nuova che
potrebbe fare o una domanda per conoscere la famiglia, preparate di notte; la domenica il riassunto
della settimana. Le idee hanno 👍/👎 e finiscono in `apps/proposte.md`. `ideas_avoid` elenca gli
argomenti su cui non deve proporre idee. Non propone mai di sorvegliare le persone (orari di rientro,
chi esce con chi).

Tutti i messaggi spontanei sul telefono hanno un tetto unico: uno ogni `message_gap_hours` (3), mai di
notte. I promemoria e quello che manda Home Assistant passano sempre.

## Claude e i costi

- Le frasi le scrive `model` (Claude Haiku 5.5): chiamate brevi con il ragionamento spento e poco
  sforzo, fermate appena la frase si chiude; il lavoro notturno passa dall'API Batch a metà prezzo.
- Claude si chiama solo quando qualcuno di `presence` è in casa e sveglio — le risposte in chat
  sempre.
- Tetti fissi: `claude_max_per_hour` (20), `claude_max_per_day` (150), contati anche fra i riavvii.
  Oltre il tetto usa le frasi già pronte e lo scrive una volta nel log.
- La spesa si conta con `api_price_in` / `api_price_out` in `sensor.<istanza>_costo_api`; con
  `api_budget_month` avvisa all'80%.
- Uso tipico: qualche decina di chiamate al giorno, 2–4 mila token in entrata ciascuna (un
  messaggio in chat con il server MCP circa 8–9 mila, per l'elenco degli strumenti e la casa):
  molto meno di un dollaro al mese.
- Senza chiave funziona tutto con le frasi già pronte (niente regista, niente disegni, niente diario
  scritto da Claude).
