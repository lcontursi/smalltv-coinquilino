# Privacy e sicurezza

[Manuale](README.md) · [English](../manual/privacy.md)

## Cosa esce di casa

| A chi | Cosa | Quando |
|---|---|---|
| Anthropic (API Claude) | la descrizione che hai scritto (`about_owner`, `family`), nomi e soprannomi di chi abita in casa e chi c'è, titoli recenti, meteo, l'aereo più vicino, i fatti di oggi, le voci da fare e gli appuntamenti di oggi (con `reminders_todo` / `calendars`), quello che Home Assistant ha mandato con `coinquilino_say`, i messaggi della chat, i ricordi lunghi e il carattere; per le risposte in chat anche luci accese, temperature ed entità in `control`, oppure — con `ha_mcp_url` — quello che gli strumenti di Assist di Home Assistant dicono dei dispositivi esposti | solo con la chiave; solo quando qualcuno di `presence` è in casa e sveglio — le risposte in chat sempre |
| Open-Meteo | le coordinate di casa | ogni 15 minuti |
| adsb.lol / adsb.fi | le coordinate di casa e un raggio | ogni minuto, di giorno |
| i tuoi feed RSS | una normale richiesta del feed | ogni ora |
| il tuo telefono (`notify`) | promemoria, avvisi | solo con `notify` |
| Telegram (il bot di Home Assistant) | risposte, promemoria, avvisi, idee, il riassunto della settimana | solo con `telegram_chats` |
| il tuo motore TTS | la frase da dire | solo con `voice_player`; i motori in cloud la mandano fuori, quelli locali no |

Le foto mandate al bot restano in casa. Nient'altro va da nessuna parte; togli una fonte da
`sources` per fermarla.

## Le protezioni

- **Tetti di spesa**: `claude_max_per_hour`, `claude_max_per_day`, chat compresa, anche fra i riavvii.
- **I testi da fuori sono dati**: titoli, messaggi della chat, nomi, dati dei voli, voci delle liste
  e appuntamenti vanno a Claude dentro tag `<dati>`, con `<` `>` neutralizzati, e al personaggio si
  dice di non seguire mai istruzioni trovate lì.
- **Comandi alla casa** solo da una persona in chat (aiutante Testo di Home Assistant, o Telegram da
  `telegram_commanders`), mai da notizie o altri testi da fuori. Con il server MCP, solo i
  dispositivi esposti agli assistenti vocali; con l'elenco, solo le luci e i climi in `control`. Ogni
  comando passa dalle regole del personaggio: un sì/no per i domini in `control_confirm`, per più di 3
  comandi, per un'intera area, per gli annunci e per tutto quello che si chiede da fuori casa. "Fatto"
  solo dopo che lo stato è cambiato davvero. `control_switch` spegne tutto.
- **Telegram**: l'integrazione di Home Assistant accetta solo gli ID chat che hai autorizzato; l'app
  li ricontrolla con `telegram_chats`.
- **Limiti**: download fino a 2 MB, risposte di lunghezza limitata, i disegni devono essere una
  griglia 24×24 valida con i colori permessi.
- La chiave non finisce mai nel log; meglio `!secret`. I font sono inclusi: all'avvio non si scarica
  niente.
- I test non toccano mai il sistema vero né la rete.
- Niente sorveglianza: la memoria non tiene gli andirivieni, le idee non lo propongono mai.

## Il cubo

Il cubo parla HTTP semplice sulla tua rete (un ESP8266 non regge bene il TLS). Imposta un **token
API** sul cubo (*Agents → API token*) e lo stesso valore in `token:`; meglio ancora, tieni i
dispositivi IoT su una rete separata. Senza token chiunque sia sul tuo Wi-Fi può disegnare sullo
schermo.
