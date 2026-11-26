#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Uebernimmt ein Research-Paket (Liste von Eintraegen im Schema der series.json
bzw. films.json) in die Stammdaten.

Aufruf:  python3 tools/import_research.py <paket.json> serie|film

Regeln (aus dem Grossimport ab 2000 und den Anime-Importen):
- Dubletten ueber id, imdb_id, tmdb_id und Titel + Jahr. Titelschluessel unter
  drei Zeichen zaehlen nicht (sonst verschmelzen nicht-lateinische Titel).
- Neuer Eintrag: wird angehaengt, tmdb_id als Zahl, created_at/updated_at gesetzt.
- Vorhandener Eintrag: nur Felder fuellen, die dort leer sind. Geschuetzte Felder
  (poster_url, fsk, fsk_quelle, fsk_stand, paedagogik, empfehlungen, universen)
  werden nie ueberschrieben.
- Persoenliche Daten liegen nicht in diesen Dateien und werden nie angefasst.
"""
import json, os, re, sys, unicodedata, datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATEI = {"serie": "series.json", "film": "films.json"}
SCHUETZEN = {"poster_url", "fsk", "fsk_quelle", "fsk_stand", "paedagogik", "empfehlungen", "universen"}


def norm(t):
    t = unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", t)


def schluessel(e):
    jahr = e.get("erscheinungsjahr") or e.get("startYear")
    out = set()
    for k in ("titel_de", "originaltitel", "title"):
        n = norm(e.get(k))
        if len(n) >= 3 and jahr:
            out.add((n, int(jahr)))
    return out


def leer(v):
    return v is None or v == "" or v == [] or v == {}


def main():
    if len(sys.argv) < 3 or sys.argv[2] not in DATEI:
        sys.exit(__doc__)
    paket = json.load(open(sys.argv[1], encoding="utf-8"))
    pfad = os.path.join(BASE, "data", DATEI[sys.argv[2]])
    bestand = json.load(open(pfad, encoding="utf-8"))
    heute = datetime.date.today().isoformat()
    neu = ergaenzt = 0
    for e in paket:
        if e.get("tmdb_id") not in (None, ""):
            e["tmdb_id"] = int(e["tmdb_id"])
        treffer = None
        for b in bestand:
            if (b.get("id") == e.get("id")
                    or (e.get("imdb_id") and b.get("imdb_id") == e.get("imdb_id"))
                    or (e.get("tmdb_id") and b.get("tmdb_id") == e.get("tmdb_id"))
                    or (schluessel(b) & schluessel(e))):
                treffer = b
                break
        if treffer is None:
            e.setdefault("created_at", e.get("datenerhebung_am") or heute)
            e["updated_at"] = heute
            bestand.append(e)
            neu += 1
            print("  neu:      %s (%s)" % (e.get("titel_de"), e.get("id")))
        else:
            felder = [k for k, v in e.items()
                      if k not in SCHUETZEN and k != "id" and not leer(v) and leer(treffer.get(k))]
            for k in felder:
                treffer[k] = e[k]
            if felder:
                treffer["updated_at"] = heute
                ergaenzt += 1
            print("  vorhanden: %s (%s) - ergaenzt: %s" % (treffer.get("titel_de"), treffer.get("id"),
                                                          ", ".join(felder) or "nichts"))
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(bestand, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("%s: %d neu, %d ergaenzt, jetzt %d Eintraege" % (DATEI[sys.argv[2]], neu, ergaenzt, len(bestand)))


if __name__ == "__main__":
    main()
