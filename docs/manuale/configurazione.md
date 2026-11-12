# Configurazione

[Manuale](README.md) · [English](../manual/configuration.md)

## Da dove arrivano le impostazioni

Vincono le ultime:

1. i valori predefiniti;
2. il **file personale** `coinquilino_personale.yaml`, accanto ad `appdaemon.yaml` — nomi, entità,
   chiavi: tutto quello che riguarda te. È in `.gitignore` e non si pubblica;
3. l'**istanza** in `apps/apps.yaml` — solo quello che cambia da un cubo all'altro.

Il file commentato [`examples/coinquilino_personale.yaml`](../../examples/coinquilino_personale.yaml)
elenca ogni opzione con il suo valore predefinito. Salvare il file personale riavvia l'app entro 20
secondi.

I nomi dei tipi di chiacchiera (`chatter_day_max`, `voice_kinds`) sono quelli del log — vedi
[Log e problemi](problemi.md#i-nomi-del-log).

## Il cubo

| Opzione | Predefinito | Significato |
|---|---|---|
| `host` | — | IP del cubo (obbligatorio) |
| `token` | nessuno | token API di glimmer; tra virgolette se comincia con 0 |
| `character` | `alessio` | `alessio` o `bandit` |
| `gamma` | 1.6 | >1 scurisce i mezzitoni (il pannello è luminoso) |
| `saturation` | 1.4 | >1 colori più carichi |
| `night_dim` | 0.25 | luminosità di notte (con `night_clock: off`) |
| `night_clock` | `alessio` | di notte: `alessio` (il suo orologio), `glimmer` (quello di glimmer), `off` (cameretta scurita) |
| `wait_text` | — | il testo che glimmer mostra mentre aspetta i fotogrammi |
| `filler_show` | true | le chiacchiere riportano il cubo sul canale Pixel |

## Le persone e la casa

| Opzione | Predefinito | Significato |
|---|---|---|
| `owner` | — | come il personaggio chiama la persona principale ("Zio Mario") |
| `owner_entity` | — | il suo `person.*` |
| `presence` | tutte le persone | Claude si usa solo se almeno una di loro è in casa |
| `nicknames` | i nomi di HA | `person.* → nome` da usare nelle frasi |
| `city` | — | nelle frasi e nel meteo |
| `about_owner`, `family` | — | qualche frase su di te e sulla famiglia, per Claude |
| `persona` | quella di serie | sostituisce la descrizione del personaggio (avanzato) |
| `birthdays` | — | `"MM-GG": nome`, compreso quello del personaggio |
| `away_minutes` | 15 | uscite più brevi sono rimbalzi del GPS |
| `arrive_group_seconds` | 90 | chi arriva insieme riceve un saluto solo |
| `indoor_temperature` | media dei `climate.*` | sensori da mediare per "in casa ci sono N gradi" |
| `power_sensor`, `energy_sensor` | nessuno | W adesso, kWh da mezzanotte, per la schermata della corrente |
| `room_change_degrees` | 1.5 | una stanza che cambia di tanto in un'ora: lo dice |

## Di cosa parla

| Opzione | Predefinito | Significato |
|---|---|---|
| `sources` | `[casa, meteo, notizie, curiosita, aerei]` | togline una per spegnerla |
| `feeds` | — | feed RSS: `url`, `label`, `skip` (categorie o parole intere) |
| `local_feast` | — | il santo patrono: `{from: "MM-GG", to: "MM-GG", name: ...}` |
| `feste` | true | costumi e addobbi |
| `weather` | il primo `weather.*` | l'entità del meteo di adesso |
| `latitude`, `longitude` | `zone.home` | per Open-Meteo e gli aerei |
| `morning_at` | `"07:45"` | buongiorno con le previsioni |
| `diary_at` | `"21:00"` | da quest'ora scrive il diario |
| `plane_radius_km` | 15 | aerei considerati per radar e chiacchiere |
| `overhead_km` | 3 | "sopra casa": lo annuncia e si vede alla finestra |
| `plane_min_altitude_m` | 150 | più in basso sono a terra |
| `plane_gap_minutes` | 10 | al massimo un annuncio ogni 10 minuti |
| `plane_topic_minutes` | 60 | al massimo un discorso sugli aerei all'ora, in tutto |

## Quanto parla

| Opzione | Predefinito | Significato |
|---|---|---|
| `talk_every_minutes` | 5 | chiacchiere gratuite (1 minuto quando sul cubo c'è solo la faccia) |
| `chatter_minutes` | 25 | ogni quanto gira il regista |
| `min_gap_minutes` | 15 | tra due avvisi in coda (gli urgenti passano sempre) |
| `max_per_hour` | 4 | avvisi in coda per ora |
| `chatter_day_max` | quelli di serie | tetto al giorno per tipo, es. `{news.headline: 8}` |
| `show_minutes` | 20 | quanto restano una frase (corta o lunga), una lavagnetta, una schermata |
| `card_seconds` | 40 | durata minima di lavagnette e schermate |
| `cards` | true | grafici, radar e disegni sulla lavagnetta |
| `screens` | true | schermate a tutto cubo |
| `scenes` | true | la cameretta cambia ogni giorno |
| `drawing_hours` | 3 | al massimo un disegno ogni 3 ore |
| `night_start`, `night_end` | 23, 7 | dorme dalle… alle… |
| `message_gap_hours` | 3 | un messaggio spontaneo sul telefono ogni N ore, mai di notte |
| `spontaneous` | true | un'idea o una domanda al giorno, il riassunto della domenica |
| `ideas_avoid` | — | argomenti su cui non proporre idee |

## Claude

| Opzione | Predefinito | Significato |
|---|---|---|
| `anthropic_api_key` | nessuna | senza, frasi già pronte |
| `model` | `claude-haiku-5-5` | il modello |
| `claude_max_per_hour` / `claude_max_per_day` | 20 / 150 | tetti fissi, chat compresa |
| `claude_thinking` | false | lascia ragionare il modello anche sulle frasi brevi (costa di più) |
| `batch` | true | lavoro notturno con l'API Batch, a metà prezzo |
| `night_job_at` | `"03:30"` | ricordi ogni notte, carattere la domenica |
| `api_price_in` / `api_price_out` | 0.10 / 0.50 | $ per milione di token, per il sensore della spesa |
| `api_budget_month` | nessuno | $ al mese: avviso all'80% |
| `tired_at` | 80 | "stanco" sopra questa % della sessione Claude (sensori di consumo) |

## Il personaggio

| Opzione | Predefinito | Significato |
|---|---|---|
| `age` | 10 | età di Alessio (da 8 ha l'aspetto da ragazzino) |
| `grow` | false | true: cresce da `start_age`, un anno ogni `grow_days`, fino a `max_age` |
| `force_mood`, `force_festa` | — | per le prove: umore o festa fissi |
| `moto_days`, `moto_min`, `moto_max` | `[5, 6]`, 15, 30 | "giornata da moto": giorni e temperature |
| `feedback_up`, `feedback_down` | — | `input_button` 👍/👎 sull'ultima frase |

## Home Assistant

| Opzione | Predefinito | Significato |
|---|---|---|
| `ha_mcp_url`, `ha_mcp_token` | — | il server MCP di Home Assistant e un token di lunga durata: i comandi dalla chat ([dettagli](chat.md#con-il-server-mcp-di-home-assistant-consigliata)) |
| `reminders_todo` | — | liste todo da leggere (e dove finiscono i promemoria della chat) |
| `calendars` | — | calendari per gli appuntamenti di oggi e domani |
| `calendar_minutes` | 60 | quanto prima avvisa di un appuntamento |
| `workday` | — | `binary_sensor` di Workday: lavorativo o festivo |
| `notify` | — | servizio `notify.*` per i messaggi sul telefono (prima Telegram, se c'è) |
| `autonomy`, `autonomy_switch` | false | il regista può mandare un avviso sul telefono |
| `sensor` | `sensor.<nome>_dice` | l'ultima frase |
| `state_sensor` | `sensor.<nome>_stato` | umore, ricordi, idee… per la plancia |
| `cost_sensor` | `sensor.<istanza>_costo_api` | spesa delle API del mese |
| `preview` | nessuna | percorso PNG per l'anteprima del cubo |

## Chat, Telegram, voce, comandi, foto

Sono descritte con gli esempi in [Chat, Telegram e voce](chat.md) e
[Sul cubo](sul-cubo.md#le-foto-di-famiglia): `chat_entity`, `chat_from`, `chat_reply_phone`,
`telegram_chats`, `telegram_commanders`, `telegram_notify`, `telegram_aloud`, `telegram_event`,
`telegram_bot`, `control`, `control_confirm`, `control_switch`, `control_verify_seconds`,
`voice_player`, `voice_tts`, `voice_language`, `voice_options`, `voice_volume`, `voice_kinds`,
`voice_switch`, `photos`, `photo_every_minutes`, `photo_seconds`, `photo_day_max`, `photo_max`,
`photo_inbox`, `photo_dir`, `photo_saturation`, `photo_select`, `photo_show_button`,
`photo_delete_button`.
