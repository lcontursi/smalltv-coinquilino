# Log e problemi

[Manuale](README.md) · [English](../manual/troubleshooting.md)

## Leggere il log

Il log dell'add-on AppDaemon ha una riga per ogni cosa successa:

```
SAY    free chatter weather.now       : Fuori ci sono 14 gradi e c'è il sole.
QUEUE  free event   person.leave      : Anna (person.anna)
QUEUE  paid timer   director
CLAUDE paid timer   director          : 1834+62 token | oggi 12/150, ultima ora 3/20 | 0.0004 $
SAY    paid timer   director          : Zio Mario, la biblioteca nuova apre sabato.
SAY    free (fallback) event person.arrive : Ciao Anna, eccoti a casa.
SKIP   free event   say               : luci_casa_vuota: già detto
ACT    free chat    home.agenda       : todo.alessio: chiamare la nonna
```

- `SAY` detto · `QUEUE` in attesa del suo turno · `SKIP` scartato, con il motivo · `CLAUDE` una
  chiamata all'API, con i token veri, i tetti e il costo · `ACT` un'azione fatta su Home Assistant.
- `free` / `paid`: a pagamento solo quando la frase l'ha scritta Claude; `free (fallback)` vuol dire
  che doveva scriverla Claude ma è stata usata una frase già pronta (niente chiave, nessuno in casa,
  tetto raggiunto, errore — il motivo è nel log).
- Gruppi: `chatter` (chiacchiere gratuite), `event` (è successo qualcosa), `timer` (regista,
  disegno, diario, lavoro notturno), `chat`.

### I nomi del log

Sono anche i nomi per `chatter_day_max` e `voice_kinds`:

| Chiacchiere | | Eventi e turni | |
|---|---|---|---|
| `weather.now` | meteo di adesso | `person.arrive` / `person.leave` | arrivi, uscite |
| `weather.forecast` | previsioni | `weather.rain_soon` / `rain_stop` / `wind` / `change` / `morning` | avvisi del meteo |
| `weather.chart` | la settimana sulla lavagnetta | `plane.overhead` | aereo sopra casa |
| `home.status` / `home.people` | la casa, chi c'è | `holiday` | feste, compleanni |
| `home.agenda` | l'agenda di oggi | `say` | `coinquilino_say` |
| `news.headline` | una notizia | `director` / `drawing` / `diary` | i turni di Claude |
| `sky.sun` / `calendar.today` | il sole, il giorno | `chat.reply` | risposte in chat |
| `planes.nearby` / `planes.radar` | aerei | `me.reminder` | promemoria |
| `me.fact` / `me.gallery` | curiosità, disegni | `home.temperature` | una stanza che cambia in fretta |
| | | `home.read` / `home.confirm` / `home.action` | comandi alla casa: letture, sì/no, azioni |
| `claude.usage` / `claude.chart` / `api.usage` | Claude | `memory.night` / `character.week` / `me.idea` | lavoro notturno |
| `screen.weather` / `screen.home` / `screen.power` | schermate | `claude.low` / `claude.refilled` | sessione di Claude |
| `me.showcase` | la vetrina del giorno | `api.budget` | avviso della spesa |

## I problemi più comuni

**Sul cubo c'è solo la faccia per tanto tempo.** Di notte è normale. Di giorno la prima frase dopo un
riavvio arriva entro un minuto e mezzo; poi, con la sola faccia sullo schermo, ci riprova ogni minuto.
Se non arriva niente, cerca `chiacchiere in pausa` nel log (livello debug) — casa vuota, citofono
(`quiet_seconds`), cose in coda.

**`cubo non raggiungibile`.** Il Wi-Fi del cubo è debole: qualche time-out ogni tanto è normale e si
riprende. Se dura, controlla l'IP e che il cubo abbia il firmware con il canale Pixel.

**`il cubo rifiuta il token`.** `token:` non è uguale al token API del cubo (tra virgolette se
comincia con 0).

**`Entity … not found in the default namespace`.** È un controllo di AppDaemon: l'entità non è
ancora nella sua copia degli stati (per esempio una lista appena creata). La chiamata parte lo
stesso; se si ripete, controlla il nome dell'entità.

**"Entità non trovata" in plancia dopo un riavvio di Home Assistant.** I sensori dell'app tornano
entro 5 minuti.

**I comandi non funzionano (server MCP).** Controlla in quest'ordine:

- `server MCP di Home Assistant non raggiungibile` — l'indirizzo in `ha_mcp_url` (dall'add-on
  funziona sempre `http://<IP di Home Assistant>:8123/api/mcp`) o il token: dev'essere un token di
  lunga durata di un utente con accesso;
- Claude risponde sulla casa ma non comanda mai — nell'integrazione è acceso *Read-only*, oppure non è
  scelto *Device control*;
- `nome sconosciuto ad Assist` — il dispositivo non è esposto agli assistenti vocali, o ha un altro
  nome: esponilo, o dagli un alias, in *Impostazioni → Assistenti vocali → Esponi*;
- `SKIP … home.action … lo stato non è cambiato` — Home Assistant ha accettato il comando ma il
  dispositivo non è cambiato (spento, lento): il personaggio dice che non c'è riuscito.

**Claude non scrive mai.** Guarda la riga di avvio (`battute da Claude SI/NO`), poi cerca
`free (fallback)` e il suo motivo: nessuno di `presence` in casa, notte, tetto raggiunto, chiave
sbagliata.

**Ripete qualcosa.** Gli argomenti già detti oggi sono nei dati che riceve Claude, e la stessa
chiacchiera non torna prima di 3 ore; per i messaggi di Home Assistant usa `key` e `repeat_hours`.
Scrivigli in chat *"non parlare più di …"* per bloccare un argomento.

**Ho cambiato il file personale ma non succede niente.** L'app lo controlla ogni 20 secondi; il log
scrive `coinquilino_personale.yaml e' cambiato: riparto`. Un errore di YAML compare nel log all'avvio.

## Sviluppo

```sh
pip install pillow requests pyyaml pytest ruff
ruff check apps tests
pytest -q
```

I test girano senza AppDaemon e senza rete, con un Home Assistant finto e un cubo finto
(`tests/conftest.py`); caricano anche tutti i blueprint e controllano i campi che mandano.
