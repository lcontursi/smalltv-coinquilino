# Coinquilino — manuale

[English](../manual/README.md) · [Torna al progetto](../../README.it.md)

Coinquilino è un'app AppDaemon per Home Assistant che dà alla tua casa un personaggio — Alessio,
un ragazzino di 10 anni, o Bandit, una moto — che vive in un GeekMagic SmallTV Ultra. Home
Assistant decide cosa conta; il personaggio lo mostra sul cubo, lo scrive su Telegram e, se vuoi, lo
dice a voce.

Questo manuale descrive tutte le funzioni e tutte le opzioni. La versione breve è nel
[README](../../README.it.md).

## Indice

1. [Installazione](installazione.md) — firmware, AppDaemon, l'app, il file personale, il primo avvio.
2. [Configurazione](configurazione.md) — da dove si leggono le impostazioni e tutte le opzioni per argomento.
3. [Home Assistant](home-assistant.md) — l'evento `coinquilino_say`, i blueprint, liste e
   calendari, i sensori che pubblica, la plancia, più cubi.
4. [Sul cubo](sul-cubo.md) — nuvoletta, lavagnetta, schermate, vetrina del giorno, foto, la
   cameretta, le feste, la notte.
5. [Il personaggio](personaggio.md) — il regista, le chiacchiere e i loro tetti, memoria e diario,
   carattere e idee, Claude e i costi.
6. [Chat, Telegram e voce](chat.md) — scrivergli, Telegram, comandi alla casa, promemoria, Siri e
   CarPlay, la voce.
7. [Privacy e sicurezza](privacy.md) — cosa esce di casa, le protezioni.
8. [Log e problemi](problemi.md) — leggere il log, i problemi più comuni.

## In una figura

```
 Home Assistant ──────────────► Coinquilino (AppDaemon) ───── HTTP ─────► SmallTV Ultra
  persone, meteo, sensori         decide quando parlare,                   (glimmer + canale
  liste, calendari                disegna fotogrammi 240×200,              Pixel) mostra i
  automazioni / blueprint ──►     chiede le frasi a Claude                 fotogrammi
   evento coinquilino_say         (facoltativo), Telegram, voce
                       ◄──────── sensori: umore, ricordi, ultima frase, spesa delle API
```

## Le parole di questo manuale

| Parola | Significato |
|---|---|
| **frase** | quello che il personaggio dice, nella nuvoletta |
| **lavagnetta** | la tavoletta accanto ad Alessio con un grafico, un radar o un disegno |
| **schermata** | un'immagine a tutto cubo (meteo della settimana, casa, corrente) |
| **chiacchiera** | una frase gratuita costruita dai dati (meteo, casa, notizie…), senza Claude |
| **regista** | la chiamata periodica a Claude che sceglie cosa vale la pena dire |
| **vetrina** | le cose di oggi (grafici, disegno, diario, frasi buone) che tornano a giro |
| **file personale** | `coinquilino_personale.yaml`, le tue impostazioni, mai pubblicato |
