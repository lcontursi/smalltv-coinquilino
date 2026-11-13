# Home Assistant

[Manuale](README.md) · [English](../manual/home-assistant.md)

Coinquilino è pensato come un'estensione di Home Assistant: le tue automazioni decidono cosa vale la
pena dire, il personaggio lo dice bene. Questa pagina spiega cosa Home Assistant può mandargli, cosa
legge da Home Assistant e cosa gli restituisce.

## L'evento `coinquilino_say`

Tutto quello che Home Assistant vuole far dire al personaggio passa da un solo evento. Lancialo da
un'automazione, da uno script o da *Strumenti per sviluppatori → Eventi*:

```yaml
- event: coinquilino_say
  event_data:
    text: "La lavatrice ha finito."
    away: notify
    night: defer
```

I campi sono tutti facoltativi:

| Campo | Valori | Significato |
|---|---|---|
| `text` | frase | detta così com'è (senza Claude) |
| `about` | argomento | la scrive Claude con la voce del personaggio (conta nei tetti) |
| `telegram` | true/false | anche sul telefono (Telegram, o `notify`) |
| `away` | `say` · `notify` · `skip` | a casa vuota: la dice comunque (predefinito), solo sul telefono, niente |
| `night` | `say` · `defer` · `skip` | di notte: la dice (predefinito), al risveglio, niente |
| `wait` | true/false | in coda con gli altri avvisi (intervallo minimo, tetto orario) invece che subito |
| `key` | testo | identifica il messaggio: la stessa chiave non si ripete… |
| `repeat_hours` | numero | …prima di tante ore (predefinito 12) |
| `remember` | frase | un fatto per la memoria di oggi, senza dirlo |
| `quiet_seconds` | secondi | niente chiacchiere per un po' (per esempio, ha appena suonato il citofono) |
| `expect_arrival` | true | qualcuno sta entrando: il saluto parte subito |
| `mood`, `minutes` | umore, minuti | un umore per qualche minuto (per esempio `welcome`) |
| `cube` (o `instance`) | nome dell'istanza | solo quel cubo, se ne hai più d'uno |

Note:

- I messaggi mandati con questo evento non sono mai bloccati dal tetto dei messaggi spontanei
  (`message_gap_hours`).
- `away: notify` e nessuno in casa → arriva sul telefono, non sul cubo.
- Con `night: defer` il messaggio si tiene e si dice al mattino, sul cubo e sul telefono.
- Un messaggio con `key` scartato (notte, casa vuota) non consuma la chiave.

### Lo script blueprint

[`blueprints/script/coinquilino/alessio_di.yaml`](../../blueprints/script/coinquilino/alessio_di.yaml)
(*Coinquilino: di' qualcosa*) mette l'evento in un modulo: crea uno script da lì e usalo come azione
nell'editor delle automazioni senza scrivere YAML.

## I blueprint

Le regole sulla casa stanno in Home Assistant, come blueprint di automazione in
[`blueprints/automation/coinquilino/`](../../blueprints/automation/coinquilino/). Copia la cartella
`blueprints/` nella cartella `blueprints/` di Home Assistant (oppure importa ogni file dal suo
indirizzo GitHub in *Impostazioni → Automazioni e scene → Blueprint*), poi *Crea automazione* da
ognuno che ti serve.

| Blueprint | Cosa fa | Campi |
|---|---|---|
| **Luci accese a casa vuota** | dopo N minuti con `zone.home` a 0 spegne le luci accese (tranne quelle da lasciare) e dice quali si sono spente davvero; a casa vuota solo sul telefono | zona, minuti (10), spegnile (sì), luci da non toccare |
| **Clima spento con la finestra aperta** | finestra aperta da N minuti e clima acceso: lo mette su off, lo dice, e rimette la modalità di prima quando la finestra si chiude | finestra, clima, minuti (3) |
| **Citofono** | quando suonano: sta zitto un minuto e se lo ricorda; se nessuno apre entro N minuti lo dice sul cubo e sul telefono (di notte al risveglio); se aprite, il saluto a chi entra parte subito | entità event della suonata, entità event dell'apertura, minuti (2), secondi di silenzio (60) |
| **Batterie scariche** | una volta al giorno, i sensori di batteria sotto la soglia in una frase (a casa vuota solo sul telefono); la stessa lista non torna prima di 3 giorni | soglia (20%), ora (10:00), sensori da ignorare |
| **Aggiornamenti di Home Assistant** | una volta al giorno gli `update.*` da installare, a chi è in casa; la stessa lista una volta a settimana | ora (18:00) |
| **Qualcuno sta arrivando** | con l'integrazione **Proximity**: sotto N km e in avvicinamento, Claude lo dice con la sua voce a chi è in casa; mai di notte | sensore di distanza, sensore di direzione, chi, km (5) |
| **Pacchi (17TRACK)** | quando un contatore di 17TRACK sale (consegnati, da ritirare…), dice la frase che hai scelto; a casa vuota solo sul telefono | sensore di 17TRACK, frase |
| **Raccolta dei rifiuti** | la sera prima, cosa passa domani, letto da un calendario (per esempio **Waste Collection Schedule**, che copre molti gestori della raccolta); a casa vuota solo sul telefono | calendario, ora (20:00), frase |

Ogni blueprint lancia solo `coinquilino_say`: aprilo per vedere esattamente cosa manda, e copialo
come punto di partenza per le tue regole.

## Liste e calendari

| Opzione | Esempio | Cosa fa |
|---|---|---|
| `reminders_todo` | `[todo.alessio]` | legge le voci da fare ogni 2 minuti |
| `calendars` | `[calendar.famiglia]` | legge gli appuntamenti di oggi e domani ogni 15 minuti |
| `calendar_minutes` | `60` | quanti minuti prima di un appuntamento avvisa |
| `workday` | `binary_sensor.workday_sensor` | lavorativo o festivo, in quello che sa di oggi |

- Una voce **con l'ora** la dice alla scadenza, sul cubo e sul telefono, una volta.
- Un **appuntamento** (non di tutto il giorno) lo annuncia `calendar_minutes` prima: "Fra 30 minuti:
  Dentista (alle 16:00)".
- Le voci senza ora e gli appuntamenti di oggi entrano in quello che il personaggio sa: può citarli,
  e una chiacchiera "Oggi in agenda: …" esce fino a 4 volte al giorno.
- In chat *"ricordami di chiamare la nonna alle 18"* aggiunge una voce con quella scadenza alla prima
  lista di `reminders_todo` (senza lista, il promemoria lo tiene nella sua memoria);
  *"fatto la nonna"* spunta la voce che ci somiglia.

Liste adatte: **Local To-do** (una lista solo per il personaggio), la lista di Alexa (la riempi da un
Echo, anche in macchina con Echo Auto), qualunque altro `todo.*`. Calendari: **Local Calendar**,
Google Calendar, CalDAV… Workday è l'integrazione **Workday** di Home Assistant.

## Il server MCP di Home Assistant

Con `ha_mcp_url` e `ha_mcp_token` la chat usa gli strumenti di Assist del **Model Context Protocol
Server** di Home Assistant: i dispositivi che esponi agli assistenti vocali, con i loro nomi, aree e
alias. Home Assistant conosce la casa; il personaggio aggiunge memoria, personalità, le sue regole di
conferma e il log. Vedi [Chat → Comandi alla casa](chat.md#con-il-server-mcp-di-home-assistant-consigliata).

## I sensori che pubblica

| Entità | Stato | Attributi |
|---|---|---|
| `sensor.<personaggio>_dice` | l'ultima frase | `tipo` (nome del log), `ora` |
| `sensor.<personaggio>_stato` | l'umore | età, festa, ricordi, carattere, interessi, promemoria, comandi dalla chat, idee, foto, ultimo messaggio, versione |
| `sensor.<istanza>_costo_api` | $ spesi nel mese | `mese`, `oggi`, `chiamate`, `budget` |

Li crea l'app (non sono nel registro delle entità) e tornano entro 5 minuti dopo un riavvio di Home
Assistant. I nomi si cambiano con `sensor`, `state_sensor`, `cost_sensor`.

## La plancia

[`examples/plancia.yaml`](../../examples/plancia.yaml) è una vista pronta: chat, interruttori (voce,
autonomia, comandi), umore ed età, ricordi, il registro delle automazioni `coinquilino_*`, i comandi
dalla chat, le idee, il grafico della spesa delle API, l'album delle foto e, se vuoi, l'anteprima
dal vivo.

Per l'anteprima imposta `preview: /homeassistant/www/coinquilino.png` e aggiungi una telecamera
*Local File* su `/config/www/coinquilino.png` (nell'esempio si chiama `camera.anteprima_cubo`).

Aiutanti utili (da *Impostazioni → Dispositivi e servizi → Aiutanti*):

| Aiutante | Opzione |
|---|---|
| Testo, max 255 | `chat_entity` |
| Interruttore | `voice_switch`, `autonomy_switch`, `control_switch` |
| Pulsante ×2 | `feedback_up`, `feedback_down` |
| Menu a discesa + Pulsante ×2 | `photo_select`, `photo_show_button`, `photo_delete_button` |

## Più cubi

Un'istanza per cubo in `apps.yaml`, ognuna con il suo `host` e, se vuoi, il suo `character`,
`chat_entity`, `voice_player`:

```yaml
cucina:
  module: coinquilino
  class: Coinquilino
  host: 192.168.1.51
  character: bandit
  chat_entity: input_text.parla_con_bandit
```

Ogni istanza ha la sua memoria (`memoria_<istanza>.json`) e i suoi sensori. Manda `cube: cucina` in
`coinquilino_say` per far parlare solo quello.
