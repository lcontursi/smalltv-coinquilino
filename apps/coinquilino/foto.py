"""
Le foto di famiglia sul cubo: a tutto schermo con un bordo, a giro.

  quadro(img)     una foto qualsiasi -> immagine 220x180 da mettere nella lavagnetta grande
                  (orizzontali ritagliate per riempire, verticali intere su sfondo sfocato)
  Album           le foto preparate in una cartella, al massimo `massimo`, in ordine di arrivo;
                  prossima() le restituisce a giro

Tutto resta in casa: le foto non vanno da nessuna parte, si preparano sul computer di
Home Assistant e si mandano al cubo come qualsiasi altra immagine.
"""
import json
import os
import re
import time

from PIL import Image, ImageFilter, ImageOps

W, H = 220, 180          # l'interno della lavagnetta grande (la cornice la disegna il personaggio)
ESTENSIONI = (".jpg", ".jpeg", ".png", ".webp", ".bmp")
PRONTA = re.compile(r"^\d{8}-\d{6}-\d{3}\.png$")      # una foto gia' preparata dall'album


def quadro(img, w=W, h=H):
    """Foto -> immagine w x h. Orientamento EXIF rispettato."""
    img = ImageOps.exif_transpose(img).convert("RGB")
    iw, ih = w, h
    r_foto, r_box = img.width / img.height, iw / ih
    if r_foto >= r_box * 0.8:
        # orizzontale (o quasi): riempie il riquadro, si ritaglia al centro
        inner = ImageOps.fit(img, (iw, ih), Image.LANCZOS, centering=(0.5, 0.45))
    else:
        # verticale: intera al centro, ai lati la stessa foto ingrandita e sfocata
        inner = ImageOps.fit(img, (iw, ih), Image.LANCZOS).filter(ImageFilter.GaussianBlur(8))
        inner = Image.blend(inner, Image.new("RGB", inner.size, (0, 0, 0)), 0.35)
        fg = ImageOps.contain(img, (iw, ih), Image.LANCZOS)
        inner.paste(fg, ((iw - fg.width) // 2, (ih - fg.height) // 2))
    return inner


class Album:
    """Cartella con le foto gia' preparate (PNG 220x180) e un indice per il giro."""

    def __init__(self, cartella, massimo=50):
        self.dir, self.massimo = cartella, max(1, int(massimo))
        os.makedirs(self.dir, exist_ok=True)
        self._stato = os.path.join(self.dir, "giro.json")
        self._scartate = set()                  # file non validi o non cancellabili: non riprovare

    def foto(self):
        return sorted(f for f in os.listdir(self.dir) if PRONTA.match(f))

    def sincronizza(self, eta_minima=10):
        """Immagini messe a mano nella cartella (es. dalla sezione Media di Home Assistant):
        si preparano e prendono il posto dell'originale. Ritorna (nomi nuovi, errori)."""
        nuove, errori = [], []
        for f in sorted(os.listdir(self.dir)):
            src = os.path.join(self.dir, f)
            if PRONTA.match(f) or f in self._scartate or not f.lower().endswith(ESTENSIONI) \
                    or not os.path.isfile(src):
                continue
            if time.time() - os.path.getmtime(src) < eta_minima:
                continue                                            # forse ancora in caricamento
            try:
                nuove.append(self.aggiungi(src))
            except Exception as e:                                  # non e' un'immagine valida
                errori.append(f"{f}: {e}")
            try:
                os.remove(src)
            except OSError as e:
                errori.append(f"{f}: non riesco a toglierla ({e})")
                self._scartate.add(f)
        return nuove, errori

    def togli(self, nome):
        try:
            os.remove(os.path.join(self.dir, os.path.basename(nome)))
            return True
        except OSError:
            return False

    @staticmethod
    def etichetta(nome):
        """20261030-113200-302.png -> '30/10 11:32'"""
        m = re.match(r"(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})", nome)
        return f"{m.group(3)}/{m.group(2)} {m.group(4)}:{m.group(5)}" if m else nome

    def aggiungi(self, sorgente):
        """sorgente: percorso o immagine PIL. Ritorna il nome della foto preparata."""
        img = Image.open(sorgente) if isinstance(sorgente, str) else sorgente
        base, ms = time.strftime('%Y%m%d-%H%M%S'), int(time.time() * 1000) % 1000
        nome = f"{base}-{ms:03d}.png"
        while os.path.exists(os.path.join(self.dir, nome)):         # stesso millesimo: il successivo
            ms = (ms + 1) % 1000
            nome = f"{base}-{ms:03d}.png"
        quadro(img).save(os.path.join(self.dir, nome), optimize=True)
        tutte = self.foto()
        for vecchia in tutte[:max(0, len(tutte) - self.massimo)]:   # oltre il massimo: via le piu' vecchie
            os.remove(os.path.join(self.dir, vecchia))
        return nome

    def _leggi(self):
        try:
            with open(self._stato) as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def prossima(self):
        """La foto dopo l'ultima mostrata (a giro, in ordine di arrivo) -> (nome, immagine) o None."""
        tutte = self.foto()
        if not tutte:
            return None
        ultima = self._leggi().get("ultima")
        dopo = [f for f in tutte if ultima is None or f > ultima]
        nome = dopo[0] if dopo else tutte[0]
        self.mostrata(nome)
        return nome, Image.open(os.path.join(self.dir, nome)).convert("RGB")

    def mostrata(self, nome):
        try:
            with open(self._stato, "w") as f:
                json.dump({"ultima": nome}, f)
        except OSError:
            pass

    def apri(self, nome):
        return Image.open(os.path.join(self.dir, nome)).convert("RGB")
