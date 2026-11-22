#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Uebernimmt covers/streaming.json aus dem Poster-Lauf in die Stammdaten.

Aufruf:  python3 tools/merge_streaming.py <pfad/zu/streaming.json>

Schreibt je Film/Serie:
  verfuegbarkeit_de           Liste {anbieter, typ, geprueft_am, quelle, provider_id}
  verfuegbarkeit_geprueft_am  Datum des Abrufs (auch wenn die Liste leer ist)
  verfuegbarkeit_link         TMDb-Seite mit allen Angeboten
  verfuegbarkeit_quelle       "JustWatch über TMDb"

Regeln:
- Ein Treffer der Titelsuche wird nur uebernommen, wenn Titel UND Jahr (+-1)
  passen. Sonst bleibt der alte Stand, der Titel steht im Bericht
  (Lehre aus "Stilles Wasser" -> "Still Waters").
- Physische Angebote (DVD/Blu-ray, Videobuster) aus der Handrecherche bleiben
  erhalten - die kennt JustWatch nicht.
- Ein alter Handhinweis (streaming_hinweis) wandert nach streaming_hinweis_alt,
  damit er den frischen Daten nicht widerspricht.
- Nichts sonst am Eintrag wird angefasst; persoenliche Daten liegen ohnehin
  nicht in diesen Dateien.
"""
import json, os, re, sys, unicodedata, collections

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATEN = os.path.join(BASE, "data")
QUELLE = "JustWatch über TMDb"
TYP = {"flatrate": "abo", "free": "kostenlos", "ads": "kostenlos mit Werbung"}


def norm(t):
    t = unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", t)


def titel_passt(eintrag, item):
    """Fuer Treffer der Titelsuche: Titel und Jahr muessen stimmen."""
    soll = {norm(item.get(k)) for k in ("titel_de", "title", "titel", "originaltitel", "original_title")} - {""}
    ist = norm(eintrag.get("tmdb_titel"))
    if not ist or ist not in soll:
        return False
    j1, j2 = eintrag.get("tmdb_jahr"), eintrag.get("erwartet_jahr")
    return bool(j1 and j2 and abs(int(j1) - int(j2)) <= 1)


PHYSISCH = re.compile(r"dvd|blu-?ray|videobuster", re.I)
# Gleiche Dienste unter einem Namen - sonst meldet der Vergleich alt/neu
# "Disney+" gegen "Disney Plus" als Verlust.
GLEICH = [("netflix", r"^netflix\b"), ("disney", r"^disney\s*(\+|plus)"),
          ("rtl", r"^rtl\s*(\+|plus)(\s+(premium|max))?$"), ("apple", r"^apple\s*tv(\s*(\+|plus))?$"),
          ("sky", r"^(sky(\s*(go|q|x|stream))?|wow|sky\s*/\s*wow)$"), ("prime", r"^(amazon\s+)?prime\s*video\b")]


def dienst(name):
    for key, muster in GLEICH:
        if re.search(muster, name or "", re.I):
            return key
    return norm(name)


def physisch(x):
    if not isinstance(x, dict) or x.get("quelle") == QUELLE:
        return False
    return x.get("typ") == "physisch" or bool(PHYSISCH.search(x.get("anbieter") or ""))


def eintraege(ang, datum):
    out, gesehen = [], set()
    for kat, typ in TYP.items():
        for p in ang.get(kat) or []:
            schl = (p["name"], typ)
            if schl in gesehen:
                continue
            gesehen.add(schl)
            out.append({"anbieter": p["name"], "typ": typ, "geprueft_am": datum,
                        "quelle": QUELLE, "provider_id": p.get("id")})
    leih = {p["name"]: p.get("id") for p in ang.get("rent") or []}
    kauf = {p["name"]: p.get("id") for p in ang.get("buy") or []}
    for name in list(leih) + [n for n in kauf if n not in leih]:
        typ = "leihen_kaufen" if (name in leih and name in kauf) else ("leihen" if name in leih else "kauf")
        out.append({"anbieter": name, "typ": typ, "geprueft_am": datum,
                    "quelle": QUELLE, "provider_id": leih.get(name) or kauf.get(name)})
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    s = json.load(open(sys.argv[1], encoding="utf-8"))
    stand = s.get("titel") or {}
    bericht = collections.Counter()
    abgelehnt, verloren = [], []
    for datei in ("films.json", "series.json"):
        pfad = os.path.join(DATEN, datei)
        items = json.load(open(pfad, encoding="utf-8"))
        for it in items:
            e = stand.get(it.get("id"))
            if not e:
                bericht["ohne Abruf"] += 1
                continue
            if e.get("gefunden_ueber") not in ("tmdb_id", "imdb_id") and not titel_passt(e, it):
                abgelehnt.append("%s (%s): TMDb nennt %r %s" % (
                    it.get("titel_de") or it.get("id"), it.get("id"), e.get("tmdb_titel"), e.get("tmdb_jahr")))
                bericht["abgelehnt"] += 1
                continue
            datum = e.get("geholt_am") or s.get("stand")
            alt = it.get("verfuegbarkeit_de") or []
            behalten = [x for x in alt if physisch(x)]
            neu = eintraege(e, datum) + behalten
            ohne_aufpreis = ("abo", "kostenlos", "kostenlos mit Werbung", "werbefinanziert", "gratis")
            alt_frei = {dienst(x.get("anbieter") if isinstance(x, dict) else x) for x in alt
                        if not isinstance(x, dict) or (x.get("typ") in ohne_aufpreis and not physisch(x)
                                                       and not re.search(r"leih|kauf|channel", x.get("anbieter") or "", re.I))}
            neu_frei = {dienst(x["anbieter"]) for x in neu if x["typ"] in ohne_aufpreis}
            neu_abo = {x["anbieter"] for x in neu if x["typ"] == "abo"}
            if alt_frei - neu_frei:
                verloren.append("%s: %s" % (it.get("titel_de") or it.get("id"), ", ".join(sorted(alt_frei - neu_frei))))
            if it.get("streaming_hinweis"):
                it["streaming_hinweis_alt"] = it.pop("streaming_hinweis")
            it["verfuegbarkeit_de"] = neu
            it["verfuegbarkeit_geprueft_am"] = datum
            it["verfuegbarkeit_link"] = e.get("link")
            it["verfuegbarkeit_quelle"] = QUELLE
            bericht["uebernommen"] += 1
            bericht["mit Abo-Angebot" if neu_abo else "ohne Abo-Angebot"] += 1
        with open(pfad, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
            f.write("\n")
    print("Streaming-Stand %s: %s" % (s.get("stand"), dict(bericht)))
    if abgelehnt:
        print("\nAbgelehnt (Titelsuche passt nicht):")
        for z in abgelehnt: print("  -", z)
    if verloren:
        print("\nAngebote ohne Aufpreis, die JustWatch nicht mehr meldet (%d):" % len(verloren))
        for z in verloren[:40]: print("  -", z)


if __name__ == "__main__":
    main()
