#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruefung des Bestands ohne Browser. BLOCKER stoppen, Hinweise nicht.

Ersatz fuer das verlorene check_data.py - bewusst auf die Regeln beschraenkt,
die in diesem Projekt schon einmal Schaden angerichtet haben.
"""
import json, os, re, sys, unicodedata, collections

B = os.path.dirname(os.path.abspath(__file__))
blocker, hinweise = [], []

def lade(n):
    return json.load(open(os.path.join(B, "data", n), encoding="utf-8"))

filme, serien = lade("films.json"), lade("series.json")
alle = [("film", x) for x in filme] + [("serie", x) for x in serien]

def norm(t):
    t = unicodedata.normalize("NFKD", (t or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", t)

# --- eindeutige Kennungen ---------------------------------------------------
for feld in ("id", "imdb_id", "tmdb_id"):
    z = collections.Counter(x.get(feld) for _, x in alle if x.get(feld))
    for wert, n in z.items():
        if n > 1:
            blocker.append("%s doppelt vergeben: %r (%dx)" % (feld, wert, n))

# --- Titel + Jahr nicht doppelt --------------------------------------------
gesehen = {}
for art, x in alle:
    for t in (x.get("titel_de"), x.get("originaltitel")):
        k = norm(t)
        if len(k) < 3:          # nicht-lateinische Titel nie ueber den leeren Schluessel paaren
            continue
        paar = (k, x.get("erscheinungsjahr"))
        if paar in gesehen and gesehen[paar] != x.get("id"):
            blocker.append("Titel+Jahr doppelt: %r %s (%s / %s)" %
                           (t, x.get("erscheinungsjahr"), gesehen[paar], x.get("id")))
        gesehen[paar] = x.get("id")

# --- FSK: nur erlaubte Stufen, nie geraten ---------------------------------
ERLAUBT = {0, 6, 12, 16, 18, None}
for art, x in alle:
    if x.get("fsk") not in ERLAUBT:
        blocker.append("unerlaubte FSK %r bei %s" % (x.get("fsk"), x.get("titel_de")))
    if x.get("fsk") is not None and not x.get("fsk_quelle"):
        hinweise.append("FSK ohne Quelle: %s" % x.get("titel_de"))
    if x.get("fsk") is None:
        hinweise.append("ohne FSK: %s (%s)" % (x.get("titel_de"), x.get("id")))

# --- Empfehlungen: Pflichtfelder, plausible Alter ---------------------------
for art, x in alle:
    for e in (x.get("empfehlungen") or []):
        if not e.get("quelle"):
            blocker.append("Empfehlung ohne Quelle bei %s" % x.get("titel_de"))
        a = e.get("alter_ab")
        if a is not None and not (0 <= a <= 18):
            blocker.append("Empfehlungsalter %r unplausibel bei %s" % (a, x.get("titel_de")))
        if e.get("beitrag_url") and not str(e["beitrag_url"]).startswith("https://"):
            hinweise.append("Beitrag-Adresse nicht https: %s" % x.get("titel_de"))

# --- paedagogik: erlaubte Stufen, Quelle wenn eingestuft -------------------
STUFEN = {"mehrwert", "solide", "spass", None}
for art, x in alle:
    p = x.get("paedagogik") or {}
    if p.get("stufe") not in STUFEN:
        blocker.append("unerlaubte Stufe %r bei %s" % (p.get("stufe"), x.get("titel_de")))
    if p.get("stufe") and not p.get("quelle"):
        blocker.append("Einstufung ohne Quelle bei %s" % x.get("titel_de"))
    if p.get("ampel") not in ("gruen", "gelb", "rot", None):
        blocker.append("unerlaubte Ampel %r bei %s" % (p.get("ampel"), x.get("titel_de")))

# --- Feldtypen, an denen die App schon zerbrochen ist -----------------------
# werte_hinweise MUSS eine Liste sein: die Detailansicht ruft darauf .map() auf.
# Harte Regel nur dort, wo die App ohne Absicherung .map() aufruft und
# ein String die ganze Detailansicht zerreisst (am 25.10. passiert).
MUSS_LISTE = ("werte_hinweise", "genres", "empfehlungen",
              "verfuegbarkeit_de", "universen")
# Hier vertraegt die App einen String, sauber ist er trotzdem nicht.
SOLL_LISTE = ("quellen", "themen_schlagworte", "produktionsland", "sprache_original",
              "filmabend_typ", "regie", "hauptdarsteller")
for art, x in alle:
    for feld in MUSS_LISTE:
        if feld in x and x[feld] is not None and not isinstance(x[feld], list):
            blocker.append("%s ist keine Liste bei %s (%s)" %
                           (feld, x.get("titel_de"), type(x[feld]).__name__))
    for feld in SOLL_LISTE:
        if feld in x and x[feld] is not None and not isinstance(x[feld], list):
            hinweise.append("%s ist keine Liste bei %s" % (feld, x.get("titel_de")))

# --- Pflichtfelder ----------------------------------------------------------
for art, x in alle:
    for feld in ("id", "titel_de", "content_status"):
        if not x.get(feld):
            blocker.append("%s fehlt bei %r" % (feld, x.get("titel_de") or x.get("id")))
    if x.get("content_status") not in ("ACTIVE", "ARCHIVED", "UPCOMING"):
        hinweise.append("content_status %r bei %s" % (x.get("content_status"), x.get("titel_de")))

# --- persoenliche Daten unberuehrt -----------------------------------------
# Das Kinderprofil muss seine Obergrenze behalten - sie entscheidet, was dem
# Kind angezeigt wird. Diese Zeile darf nie "repariert" werden.
pfad = os.path.join(B, "data", "personal-data.json")
if os.path.exists(pfad):
    pd = json.load(open(pfad, encoding="utf-8"))
    kind = [p for p in pd.get("profile", []) if p.get("rolle") == "kind"]
    if not kind:
        blocker.append("kein Kinderprofil mehr vorhanden")
    elif kind[0].get("max_fsk") != 6:
        blocker.append("max_fsk des Kinderprofils ist nicht mehr 6")

print("Filme %d | Serien %d" % (len(filme), len(serien)))
print("BLOCKER: %s" % ("keine" if not blocker else len(blocker)))
for z in blocker: print("  !", z)
print("Hinweise (%d)" % len(hinweise))
for z in hinweise[:12]: print("  -", z)
if len(hinweise) > 12: print("  ... und %d weitere" % (len(hinweise) - 12))
sys.exit(1 if blocker else 0)
