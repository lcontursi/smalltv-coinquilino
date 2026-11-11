# smalltv-coinquilino — note per Claude Code

App AppDaemon (4.5, Python ≥ 3.11) per Home Assistant: anima un personaggio (Alessio, o la moto
Bandit) su un GeekMagic SmallTV Ultra con firmware glimmer + la nostra patch del canale Pixel
(`firmware/glimmer-pixel-channel.patch`). Le frasi le scrive Claude via API (facoltativo); senza
chiave usa frasi già pronte. Testi del personaggio e commenti nel codice: in italiano.
README in due lingue (`README.md` inglese, `README.it.md` italiano).

## Struttura

- `apps/coinquilino/coinquilino.py` — l'app (classe `Coinquilino`). È molto grande (~180 KB):
  cerca con grep e leggi a pezzi, non tutto insieme. `VERSION` è definita qui.
- `alessio.py`, `bandit.py` — i personaggi: disegno dei fotogrammi 240×200 (Pillow), lavagnetta,
  foto, quadrante notturno (`render_night`).
- `hamcp.py` (3.0) — client del server MCP di HA (`/api/mcp`): strumenti di Assist, sessione, chiamate.
- `casa.py` — comandi alla casa: lista bianca, `prepara`, verifica (`riuscita`), alternativa
  (`set_hvac_mode`), conferme. Niente chiamate a HA qui dentro.
- `foto.py` — album delle foto (`quadro`, `Album`).
- `mente.py` — memoria lunga, carattere, rilevamento dei tormentoni (`formule`).
- `feste.py`, `aerei.py`, `grafici.py` — feste e costumi, aerei ADS-B, grafici della lavagnetta
  e (2.0) schermate a tutto cubo (`settimana`, `schermata_casa`, `schermata_consumi`).
- `meteo.py` (2.0) — i giorni di Open-Meteo (7 passati, oggi, 3 dopo) e le frasi di confronto.
  Con `past_days` l'indice 0 di `daily` NON è oggi: usare `meteo.oggi_i` / `self._giorni()`.
- `fonts/` — Fredoka e Silkscreen (OFL).
- `examples/` — `apps.yaml`, `coinquilino_personale.yaml` (tutte le opzioni documentate, con
  valori finti), `plancia.yaml` (plancia di HA).
- `firmware/` — patch di glimmer (base Avinava/glimmer `bf7fba4`) e istruzioni.
- `tests/` — pytest; un file per versione (`test_v12.py` … `test_v16.py`), `conftest.py` con il
  cubo finto e `make_app`.

## Comandi

```
python -m pytest -q
ruff check apps tests
```

Usa sempre il venv del progetto (`.venv/`, in `.gitignore`), non il Python di sistema:
`.venv/Scripts/python -m pytest -q` e `.venv/Scripts/python -m ruff check apps tests`.
Dipendenze: `pillow requests pyyaml pytest ruff`.

Prima di dire che una modifica è finita: tutti i test verdi e ruff pulito.

## Regole del codice

- **Niente dati personali nel repo**: nomi della famiglia, IP, entità reali, chat ID, chiavi,
  compleanni. Stanno in `coinquilino_personale.yaml` (in `.gitignore`). Negli esempi solo valori
  finti (`192.168.1.50`, `person.mario`…).
- **I test non toccano il sistema vero**: niente scritture in `/media` o fuori da `tmp_path`
  (il `conftest` imposta `photo_dir` su una cartella temporanea), niente rete.
- **AppDaemon**: `call_service` non restituisce gli errori di HA (finiscono solo nel log), quindi
  dopo un comando si rilegge lo stato (`casa.riuscita`) prima di dire "fatto". Le attese
  bloccanti vanno in un thread, non nel loop di AppDaemon. `terminate()` salva la memoria.
- **Sicurezza dei comandi**: la casa si comanda solo da chat o Telegram, solo da chi è
  autorizzato, solo entità in lista bianca; notizie e altri dati non arrivano mai allo strumento
  `comanda_casa`. Clima, più di 3 entità e comandi da fuori casa chiedono conferma.
- **API Claude**: modello `claude-haiku-5-5`. Le chiamate in tempo reale usano `QUICK_PARAMS`
  (pensiero disattivato, effort basso) con un secondo tentativo senza, se l'API risponde 400.
  Il lavoro notturno va in batch con il pensiero acceso (`max_tokens` 16000).
- Ogni nuova opzione va documentata in `examples/coinquilino_personale.yaml` e nei due README.

## Nuova versione

1. `VERSION` in `coinquilino.py` e `version` in `pyproject.toml`.
2. Voce in `CHANGELOG.md` (in inglese).
3. README.md e README.it.md allineati.
4. Test nuovi per quello che cambia, tutti verdi, ruff pulito.
