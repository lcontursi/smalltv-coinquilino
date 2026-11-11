# Chat, Telegram e voce

[Manuale](README.md) · [English](../manual/chat.md)

## Scrivergli da Home Assistant

Crea un aiutante *Testo* (lunghezza massima 255), per esempio `input_text.parla_con_alessio`,
impostalo come `chat_entity` e mettilo in una plancia. Scrivi e premi invio: la risposta compare sul
cubo (e, con `chat_reply_phone: true`, sul telefono). `chat_from` dice chi scrive (predefinito:
`owner`).

Le risposte le scrive Claude, con la conversazione recente, quello che il personaggio sa e — quando
chiedi della casa — quello che gli strumenti di Assist di Home Assistant dicono dei dispositivi
esposti (oppure, con l'elenco, le luci accese, le temperature e le entità in `control`). Senza chiave funzionano
solo i comandi qui sotto.

### Comandi che non hanno bisogno di Claude

| Scrivi | Fa |
|---|---|
| *ricordati che …* | aggiunge un ricordo lungo |
| *dimentica …* | toglie i ricordi che ci somigliano (e blocca un interesse, se lo è) |
| *non parlare più di …* / *puoi riparlare di …* | blocca / sblocca un interesse |
| *ricordami di … alle 18* / *tra 20 minuti* / *domani alle 9* | un promemoria (nella lista, con `reminders_todo`) |
| *fatto …* / *ho fatto …* | spunta la voce della lista che ci somiglia |

## Telegram

1. Crea un bot con @BotFather.
2. Aggiungi l'integrazione **Telegram bot** di Home Assistant, piattaforma **Polling** (niente di
   esposto su internet), con il token; aggiungi ogni ID chat autorizzato (te lo dice @id_bot).
3. Manda `/start` al bot, poi scrivi gli stessi ID nel file personale:

```yaml
telegram_chats:
  123456789: Zio Mario
  987654321: Zia Anna
telegram_commanders: [123456789]   # chi può comandare la casa (predefinito: la chat di owner)
```

Poi:

- ogni messaggio riceve una risposta, scritta da Claude, come "Zio Mario" o "Zia Anna";
- avvisi, promemoria, idee e il riassunto della domenica arrivano lì (`telegram_notify: true`), con
  i pulsanti 👍/👎; `notify:` resta di riserva;
- `/aiuto` dice cosa sa fare; `/foto` dice quante foto ci sono nell'album;
- una foto mandata al bot finisce nell'album; rispondile «togli» per toglierla;
- `telegram_aloud: true` dice le risposte anche a voce in casa;
- `telegram_event` / `telegram_bot` servono solo con più di un bot.

Il bot va usato solo dal personaggio.

## Comandi alla casa

Ci sono due strade. Quella consigliata usa il **server MCP** di Home Assistant; l'altra un elenco di
entità nel file personale.

### Con il server MCP di Home Assistant (consigliata)

1. In Home Assistant aggiungi l'integrazione **Model Context Protocol Server** (*Impostazioni →
   Dispositivi e servizi → Aggiungi integrazione*). Nelle opzioni lascia solo **Device control**;
   *Read-only* va spento, se no i comandi non ci sono.
2. Scegli quali dispositivi il personaggio può vedere e comandare dove lo fai già per gli assistenti
   vocali: *Impostazioni → Assistenti vocali → Esponi*.
3. Crea un token di lunga durata (il tuo profilo → *Sicurezza*) e imposta:

```yaml
ha_mcp_url: http://homeassistant.local:8123/api/mcp
ha_mcp_token: !secret ha_mcp_token
control_confirm: [climate]
```

In chat Claude riceve allora gli strumenti di Assist di Home Assistant: legge da solo lo stato dei
dispositivi esposti (e le liste) e usa nomi, aree e alias come li hai dati in Home Assistant. Prima di
eseguire un comando il personaggio applica le sue regole: un sì/no da fuori casa, per i domini in
`control_confirm`, per più di 3 comandi, per un'intera area o un dominio senza il nome di un
dispositivo e per gli annunci in casa. Dice "fatto" solo quando Home Assistant dice quali dispositivi
ha cambiato e, per acceso/spento, dopo aver riletto lo stato nuovo. Ogni richiesta, conferma e
risultato è nel log (`home.read`, `home.confirm`, `home.action`).

**I nomi.** I dispositivi si trovano con il nome che vedi in Home Assistant (e con gli alias che gli
dai in *Assistenti vocali → Esponi*). Prima di eseguire un comando il personaggio controlla che il
nome esista: se Claude ne ha usato uno più lungo che lo contiene (con il nome del dispositivo davanti,
per esempio), lo corregge subito; altrimenti Claude riceve i nomi esposti più simili e riprova.
Niente parte finché il nome non è giusto.

**"Spegnila".** I comandi con un pronome — *accendila*, *spegnila*, *alzala* — valgono per l'ultimo
dispositivo nominato; l'ultimo comando fatto in casa negli ultimi 30 minuti è tra i dati che riceve
Claude.

Per provare: *"la luce della scrivania è accesa?"* (una lettura), poi *"accendi la luce della
scrivania"* e *"spegnila"*.

### Con un elenco di entità

Con una lista bianca `control:` (e senza `ha_mcp_url`) la chat (e Telegram, da `telegram_commanders`) può accendere e
spegnere le luci e regolare i climi:

```yaml
control:
  - light.*
  - climate.salone
control_confirm: [climate]          # questi domini chiedono "Devo…? sì/no"
control_switch: input_boolean.alessio_comandi
control_verify_seconds: 8
```

- *"spegni la luce dello studio"*, *"metti il salone a 20 gradi"*, *"accendi tutte le luci della
  cucina"*.
- Le domande funzionano anche senza lista: *"chi c'è in casa?"*, *"la luce dell'ingresso è
  accesa?"*, *"quanti gradi ci sono nello studio?"*.
- Chiede un sì/no per i domini in `control_confirm`, per più di 3 entità e sempre quando chi scrive è
  fuori casa.
- Dice "fatto" solo dopo aver riletto lo stato nuovo (entro `control_verify_seconds`); se Home
  Assistant rifiuta, lo dice. Un clima che non accetta `turn_off` viene messo in modalità `off`.
- Solo le entità della lista, solo luci e climi. Le notizie e gli altri testi da fuori non arrivano
  mai allo strumento dei comandi.

## I promemoria

- *"ricordami di chiamare la nonna alle 18"*, *"ricordami tra 20 minuti di spegnere il forno"*,
  *"ricordami domani alle 9 della riunione"*.
- Con `reminders_todo` il promemoria diventa una voce con scadenza in quella lista: la vedi anche
  nell'app di Home Assistant e puoi aggiungerne da lì, da Assist o da Alexa.
- Alla scadenza: sul cubo (anche di notte) e sul telefono, sempre — i promemoria non sono mai bloccati
  dal tetto dei messaggi.

## Siri e CarPlay

Siri non trova un bot di Telegram per nome ("manda un messaggio ad Alessio" non funziona). Invece:

1. Sull'iPhone, in *Comandi rapidi*, crea un comando chiamato **Alessio**: *Detta testo* → azione
   dell'app Home Assistant *Esegui azione* `input_text.set_value` sul tuo `chat_entity`, valore = il
   testo dettato.
2. Imposta `chat_reply_phone: true`: la risposta arriva anche come notifica sul telefono (Telegram,
   o `notify`), che CarPlay legge ad alta voce.

"Ehi Siri, Alessio" → detti → ti legge la risposta. Con un Echo Auto, *"Alexa, aggiungi … alla lista
delle cose da fare"* riempie la lista di Alexa, che `reminders_todo` può leggere.

## La voce

```yaml
voice_player: media_player.studio
voice_tts: tts.edge_tts            # qualunque entità tts.*
voice_language: it-IT-ElsaNeural
voice_options: {pitch: "+80Hz", rate: "+8%"}
voice_volume: 0.5
voice_switch: input_boolean.voce_alessio   # spento = muto, il cubo parla lo stesso
voice_kinds: [person.arrive, chat.reply, plane.overhead, holiday, director, diary,
              weather.rain_soon, weather.wind, say, me.reminder, home.action]
```

Dice ad alta voce solo i tipi in `voice_kinds`, mai di notte (tranne risposte e promemoria) e mai
sopra al citofono (`quiet_seconds`). I motori in cloud (Google Translate, Edge TTS) mandano la frase a
Google/Microsoft; quelli locali (Piper) no. `voice_volume` su un PC cambia il volume di sistema.
