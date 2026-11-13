"""
La mente del coinquilino: ricordi a lungo termine, carattere che cambia, eta' che cresce,
comandi della chat (ricordati / dimentica / ricordami). Niente Home Assistant qui dentro:
solo dati e regole, cosi' si prova facilmente.

  Ricordi      fatti, abitudini, tormentoni e preferenze che restano per settimane
  Carattere    tratti (0-10) e interessi, ritoccati poco alla volta dal riscontro della famiglia
  eta()        quanti anni ha adesso (cresce piu' in fretta di un bimbo vero, fino a un massimo)
  comando()    capisce "ricordati che...", "dimentica...", "ricordami di ... alle 10"
"""
import json
import re
from datetime import date, datetime, timedelta

MAX_RICORDI = 40
MAX_TESTO = 140
FATTO_GIORNI = 10         # 3.1: un fatto non riconfermato da 10 giorni si dimentica
TIPI = ("fatto", "abitudine", "tormentone", "preferenza")

TRATTI = {"chiacchierone": 5, "ironico": 4, "curioso": 7, "affettuoso": 8}
INTERESSI = {"aerei": 5, "spazio": 5, "moto": 5, "animali": 5, "meteo": 3, "mare": 3,
             "cibo": 3, "musica": 3, "dinosauri": 3, "sport": 3}
PASSO_TRATTI = 1          # di quanto puo' cambiare un tratto in una settimana
PASSO_INTERESSI = 2


def _clamp(v, lo=0, hi=10):
    try:
        return max(lo, min(hi, int(round(float(v)))))
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ ricordi
class Ricordi:
    """Lista di ricordi [{testo, tipo, dal, ultimo}] con un tetto. I ricordi nascono solo
    da cose successe davvero (eventi, chat, diario) o dette in chat ("ricordati che")."""

    def __init__(self, items=None):
        self.items = [r for r in (items or []) if isinstance(r, dict) and r.get("testo")]

    def add(self, testo, tipo="fatto", oggi=None):
        oggi = (oggi or date.today()).isoformat()
        testo = " ".join(str(testo).split())[:MAX_TESTO].rstrip(" .") + "."
        for r in self.items:
            if r["testo"].lower() == testo.lower():
                r["ultimo"] = oggi
                return r
        r = {"testo": testo, "tipo": tipo if tipo in TIPI else "fatto", "dal": oggi, "ultimo": oggi}
        self.items.append(r)
        self._cap()
        return r

    def forget(self, query):
        """Toglie i ricordi che contengono tutte le parole importanti di query."""
        words = [w for w in re.findall(r"\w+", query.lower()) if len(w) > 3]
        if not words:
            return 0
        keep = [r for r in self.items if not all(w in r["testo"].lower() for w in words)]
        n = len(self.items) - len(keep)
        self.items = keep
        return n

    def replace(self, new_items, oggi=None):
        """Lista riscritta dal lavoro notturno: valida, tiene le date dei ricordi gia' noti."""
        oggi = (oggi or date.today()).isoformat()
        old = {r["testo"].lower(): r for r in self.items}
        out = []
        for it in new_items or []:
            if isinstance(it, str):
                it = {"testo": it}
            if not isinstance(it, dict) or not str(it.get("testo", "")).strip():
                continue
            testo = " ".join(str(it["testo"]).split())[:MAX_TESTO]
            prev = old.get(testo.lower(), {})
            out.append({"testo": testo,
                        "tipo": it.get("tipo") if it.get("tipo") in TIPI else prev.get("tipo", "fatto"),
                        "dal": prev.get("dal", oggi),
                        "ultimo": oggi if it.get("confermato") or not prev else prev.get("ultimo", oggi)})
        if not out and self.items:
            return False                      # risposta vuota: meglio tenere quelli di prima
        self.items = out
        self._cap()
        return True

    def scadi(self, oggi=None, giorni=FATTO_GIORNI):
        """3.1 (CU): un fatto non riconfermato da `giorni` giorni si dimentica (abitudini e
        preferenze restano). Ritorna quanti ne ha tolti."""
        oggi = oggi or date.today()
        limite = (oggi - timedelta(days=giorni)).isoformat()
        keep = [r for r in self.items if r.get("tipo") != "fatto" or r.get("ultimo", "") >= limite]
        n = len(self.items) - len(keep)
        self.items = keep
        return n

    def _cap(self):
        if len(self.items) > MAX_RICORDI:     # via i piu' vecchi mai riconfermati
            self.items.sort(key=lambda r: r.get("ultimo", ""))
            self.items = self.items[-MAX_RICORDI:]

    def prompt(self):
        if not self.items:
            return ""
        return "Cose che ricordi (la tua memoria a lungo termine):\n" + "\n".join(
            f"- {r['testo']}" for r in self.items)

    def to_json(self):
        return list(self.items)


# ------------------------------------------------------------------ carattere
class Carattere:
    def __init__(self, data=None):
        data = data or {}
        self.tratti = dict(TRATTI)
        self.tratti.update({k: v for k, v in (data.get("tratti") or {}).items()
                            if k in TRATTI and _clamp(v) is not None})
        self.interessi = dict(INTERESSI)
        self.interessi.update({k: v for k, v in (data.get("interessi") or {}).items()
                               if _clamp(v) is not None})
        self.aggiornato = data.get("aggiornato")
        # argomenti di cui non si parla piu' ("dimentica gli aerei"): il lavoro settimanale non li rialza
        self.bloccati = [str(x) for x in (data.get("bloccati") or [])]
        for k in self.bloccati:
            self.interessi.pop(k, None)
        # riscontro della settimana: tipo di frase -> {"su": n, "giu": n, "risposte": n}
        self.riscontro = data.get("riscontro") or {}

    def segna(self, kind, voce):
        r = self.riscontro.setdefault(kind, {"su": 0, "giu": 0, "risposte": 0})
        r[voce] = r.get(voce, 0) + 1

    def interessi_in(self, testo):
        """Gli interessi nominati nel testo, anche al plurale o al singolare ("aerei" / "aereo")."""
        t = testo.lower()
        out = []
        for k in list(self.interessi) + [b for b in self.bloccati if b not in self.interessi]:
            stem = re.escape(k[:-1] if len(k) >= 5 else k)
            if re.search(rf"\b{stem}\w{{0,2}}\b", t):
                out.append(k)
        return out

    def blocca(self, nome):
        """Non se ne parla piu': via l'interesse, e il lavoro settimanale non lo riporta su."""
        self.interessi.pop(nome, None)
        if nome not in self.bloccati:
            self.bloccati.append(nome)

    def sblocca(self, nome, peso=3):
        """Si puo' riparlarne: torna come interesse debole, che poi cresce o cala da solo."""
        if nome in self.bloccati:
            self.bloccati.remove(nome)
            self.interessi[nome] = peso

    def aggiorna(self, nuovo, oggi=None):
        """Applica i ritocchi proposti, al massimo di un passo per tratto: niente salti."""
        for k, v in ((nuovo or {}).get("tratti") or {}).items():
            v = _clamp(v)
            if k in self.tratti and v is not None:
                d = max(-PASSO_TRATTI, min(PASSO_TRATTI, v - self.tratti[k]))
                self.tratti[k] = _clamp(self.tratti[k] + d)
        for k, v in ((nuovo or {}).get("interessi") or {}).items():
            v = _clamp(v)
            k = str(k).lower().strip()[:20]
            if v is None or not k or k in self.bloccati:
                continue
            cur = self.interessi.get(k, 0)
            d = max(-PASSO_INTERESSI, min(PASSO_INTERESSI, v - cur))
            self.interessi[k] = _clamp(cur + d)
        self.interessi = {k: v for k, v in self.interessi.items() if v > 0}
        if len(self.interessi) > 14:          # tiene i 14 interessi piu' forti
            self.interessi = dict(sorted(self.interessi.items(), key=lambda kv: -kv[1])[:14])
        self.aggiornato = (oggi or date.today()).isoformat()
        self.riscontro = {}

    def preferiti(self, n=3):
        return [k for k, _ in sorted(self.interessi.items(), key=lambda kv: -kv[1])[:n]]

    def scegli(self, rng, opzioni=None):
        """Un interesse a caso, pesato: quelli forti escono piu' spesso."""
        items = [(k, v) for k, v in self.interessi.items() if not opzioni or k in opzioni]
        if not items:
            return None
        return rng.choices([k for k, _ in items], weights=[v for _, v in items])[0]

    def prompt(self):
        def q(v):
            return ("pochissimo" if v <= 2 else "poco" if v <= 4 else "abbastanza" if v <= 6
                    else "molto" if v <= 8 else "tantissimo")
        tr = ", ".join(f"{q(v)} {k}" for k, v in self.tratti.items())
        stop = f" Non parlare mai di: {', '.join(self.bloccati)}." if self.bloccati else ""
        return (f"Il tuo carattere adesso: {tr}. I tuoi interessi del momento: "
                + ", ".join(self.preferiti(4)) + "." + stop)

    def to_json(self):
        return {"tratti": self.tratti, "interessi": self.interessi, "bloccati": self.bloccati,
                "aggiornato": self.aggiornato, "riscontro": self.riscontro}


# ------------------------------------------------------------------ eta'
def eta(nascita, start_age=2, grow_days=30, max_age=12, oggi=None):
    """Anni compiuti: start_age il giorno in cui e' arrivato, poi uno ogni grow_days."""
    oggi = oggi or date.today()
    if isinstance(nascita, str):
        nascita = date.fromisoformat(nascita)
    giorni = max(0, (oggi - nascita).days)
    return min(max_age, start_age + giorni // max(1, int(grow_days)))


def eta_prompt(anni):
    if anni <= 3:
        return (f"Hai {anni} anni: parli come un bimbo piccolissimo, frasi brevissime e semplici, "
                "qualche parola un po' storpiata e buffa.")
    if anni <= 5:
        return (f"Hai {anni} anni: frasi semplici e allegre, fai tante domande, ti stupisci di "
                "tutto.")
    if anni <= 7:
        return (f"Hai {anni} anni: vai a scuola, sai leggere e contare, ti piace spiegare le cose "
                "che hai imparato.")
    if anni <= 9:
        return (f"Hai {anni} anni: sei sveglio e curioso, fai battute e usi parole un po' piu' "
                "ricche, ma resti un bambino.")
    return (f"Hai {anni} anni: sei un ragazzino in gamba, pratico e un po' ironico; parli in "
            "modo normale e preciso, sai tante cose e le dici in breve; resti gentile e mai "
            "sgarbato.")


def bimbo(anni):
    return "bimbo piccolo" if anni <= 5 else "bambino" if anni <= 9 else "ragazzino"


# ------------------------------------------------------------------ chat
ORE = r"(\d{1,2})(?:[:.](\d{2}))?"
DI = r"(?:(?:di|del|dello|della|degli|dei|delle)\s+)?"       # "di aerei", "degli aerei", "delle moto"


def comando(text, adesso=None):
    """("ricorda", testo) | ("dimentica", testo) | ("riparla", testo) | ("promemoria", quando, cosa) |
    ("promemoria?", cosa) se non si capisce l'ora | None."""
    adesso = adesso or datetime.now()
    t = " ".join(text.strip().split())
    t = re.sub(r"^(alessio|bandit)[,!:]?\s+", "", t, flags=re.I)
    m = re.match(r"(?:ricordami|ricordati(?=\s+di\s))\s+(?:di\s+|che\s+)?(.+)", t, re.I)
    if m:
        rest = m.group(1)
        r = re.search(r"\s+tra\s+(\d+)\s+(minut[oi]|or[ae])\s*$", rest, re.I)
        if r:
            n = int(r.group(1))
            quando = adesso + (timedelta(hours=n) if r.group(2).lower().startswith("or")
                               else timedelta(minutes=n))
            return ("promemoria", quando.replace(second=0, microsecond=0), rest[:r.start()].strip(" .,"))
        r = re.search(r"\s+(oggi\s+|domani\s+|stasera\s+)?(?:alle|per le|verso le)\s+" + ORE + r"\s*$",
                      rest, re.I)
        if r:
            h, mi = int(r.group(2)), int(r.group(3) or 0)
            if h > 23 or mi > 59:
                return ("promemoria?", rest)
            giorno = adesso.date() + timedelta(days=1 if (r.group(1) or "").strip().lower() == "domani" else 0)
            quando = datetime.combine(giorno, datetime.min.time()).replace(hour=h, minute=mi)
            if quando <= adesso and not r.group(1):
                quando += timedelta(days=1)             # "alle 7" detto alle 22: domattina
            return ("promemoria", quando, rest[:r.start()].strip(" .,"))
        return ("promemoria?", rest)
    m = re.match(r"ricorda(?:ti)?\s+(?:che\s+)?(.+)", t, re.I)
    if m:
        return ("ricorda", m.group(1).strip())
    m = re.match(r"dimentica(?:ti)?\s+(?:che\s+|di\s+|quella cosa su\s+)?(.+)", t, re.I)
    if m:
        return ("dimentica", m.group(1).strip())
    m = re.match(rf"(?:non parlare|smetti di parlare|basta parlare)\s+(?:pi[uù]\s+)?{DI}(.+)", t, re.I)
    if m:
        return ("dimentica", m.group(1).strip(" .!"))
    m = re.match(rf"(?:puoi|puoi pure|ora puoi)\s+(?:ri)?parlare\s+(?:ancora\s+|di nuovo\s+)?{DI}(.+)"
                 rf"|ricomincia a parlare\s+{DI}(.+)", t, re.I)
    if m:
        return ("riparla", (m.group(1) or m.group(2)).strip(" .!?"))
    return None


# ------------------------------------------------------------------ tormentoni
def _norm(t):
    return " ".join(re.sub(r"[^\w\s']", " ", t.lower()).split())


def formule(frasi, esclusi=(), minimo=2):
    """Pezzi di frase (tra una punteggiatura e l'altra) ripetuti in almeno `minimo` frasi
    diverse: i tormentoni da vietare ("booo", "ti voglio tanto bene"). esclusi: nomi propri,
    che si ripetono per forza ("Zio Mario")."""
    esclusi = {_norm(e) for e in esclusi if e}
    conta = {}
    for f in frasi:
        pezzi = {_norm(p) for p in re.split(r"[!?.,;:]+", f or "")}
        for p in pezzi:
            if not p or p in esclusi or len(p) < 3:
                continue
            conta[p] = conta.get(p, 0) + 1
    out = sorted((p for p, n in conta.items() if n >= minimo), key=lambda p: -conta[p])
    return out[:8]


# ------------------------------------------------------------------ risposte del lavoro notturno
def estrai_json(raw, tag):
    """Il JSON dentro <tag>...</tag> (anche se il tag non e' chiuso), oppure None."""
    m = re.search(rf"<{tag}>(.*?)(?:</{tag}>|$)", raw or "", re.S)
    if not m:
        return None
    body = m.group(1).strip()
    body = re.sub(r"^```(?:json)?|```$", "", body).strip()
    try:
        return json.loads(body)
    except ValueError:
        return None


# ------------------------------------------------------------------ idee gia' realizzate
# (nome, [espressioni che devono comparire tutte]): una funzione che Alessio ha gia'.
FUNZIONI = (
    ("spegne le luci a casa vuota", [r"\bluc[ei]\b|\blamp", r"vuot|nessuno|fuori casa|escono|uscit|dimentic"]),
    ("spegne il clima con la finestra aperta", [r"clima|condizionator|riscaldament|termosif", r"finestr"]),
    ("avvisa di pioggia o vento", [r"pioggi|piove|ombrell|vento", r"avvis|ti dico|ti scrivo|avvert|ti ricord"]),
    ("riassunto della settimana", [r"riassunt|resoconto", r"settiman"]),
    ("orologio di notte", [r"orolog", r"nott|dorm|sera|buio"]),
    ("diario serale", [r"diario"]),
    ("promemoria", [r"promemoria|ricordarti di|ricordarvi di"]),
    ("foto a giro", [r"\bfoto\b|album", r"mostr|fa vedere|a giro|ogni tanto|cornice"]),
    ("disegni", [r"disegn"]),
    ("comandi a luci e clima da chat o Telegram", [r"accend|spegn", r"telegram|chat|scrivere"]),
)


def idea_gia_fatta(testo):
    """Il nome della funzione che l'idea ripete, o None se e' nuova."""
    t = (testo or "").lower()
    for nome, pezzi in FUNZIONI:
        if all(re.search(p, t) for p in pezzi):
            return nome
    return None
