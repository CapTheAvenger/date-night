#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Traegt die Anime-Empfehlungen von @teacher__light in den Bestand ein.

Quelle: Instagram-Reel "Welcher Anime passt zu deinem Kind?" vom 25.10.2026,
sechs Kategorien zu je drei Titeln. Die Stammdaten kommen aus
import/anime-01.json und import/anime-02.json (recherchiert, mit Quellen),
die paedagogische Einschaetzung aus import/flimmo-anime.json.

Grundregeln dieses Projekts, die hier gelten:
- Nichts erfinden. Fehlende Werte bleiben null.
- Eine gepflegte fsk wird nie ueberschrieben.
- Persoenliche Daten werden nicht angefasst.
- Das Empfehlungsalter der Quelle ist KEINE Altersfreigabe.
"""
import json, collections, os, sys

BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(BASIS, "data")
HEUTE = "2026-10-25"
BEITRAG = "https://www.instagram.com/reel/De7Mfq3BzFD/"
QUELLE = "Instagram @teacher__light (Hilal Ebcin)"
LISTE = "Welcher Anime passt zu deinem Kind?"

# Schluessel -> (Kategorie, Alter laut Beitrag, Titel im Beitrag)
REEL = {
    "pokemon":     ("Abenteuer & Freundschaft", 7,  "Pokémon"),
    "digimon":     ("Abenteuer & Freundschaft", 9,  "Digimon Adventure"),
    "onepiece":    ("Abenteuer & Freundschaft", 13, "One Piece"),
    "kiki":        ("Magie & Fantasie",         6,  "Kikis kleiner Lieferservice"),
    "lwa":         ("Magie & Fantasie",         8,  "Little Witch Academia"),
    "chihiro":     ("Magie & Fantasie",         10, "Chihiros Reise ins Zauberland"),
    "inazuma":     ("Sport & Wettkämpfe",       9,  "Inazuma Eleven"),
    "haikyu":      ("Sport & Wettkämpfe",       13, "Haikyu!!"),
    "bluelock":    ("Sport & Wettkämpfe",       14, "Blue Lock"),
    "chi":         ("Humor & lustige Geschichten", 5, "Chi's Sweet Home"),
    "hamtaro":     ("Humor & lustige Geschichten", 5, "Hamtaro"),
    "spyfamily":   ("Humor & lustige Geschichten", 13, "Spy x Family"),
    "avatar":      ("Action & Spannung",        9,  "Avatar – Der Herr der Elemente"),
    "naruto":      ("Action & Spannung",        12, "Naruto"),
    "mha":         ("Action & Spannung",        14, "My Hero Academia"),
    "yourlie":     ("Tiefgründige Geschichten", 13, "Your Lie in April"),
    "violet":      ("Tiefgründige Geschichten", 14, "Violet Evergarden"),
    "silentvoice": ("Tiefgründige Geschichten", 15, "A Silent Voice"),
}

# Die Kategorie-Frage aus dem Beitrag, woertlich
FRAGE = {
    "Abenteuer & Freundschaft": "Dein Kind liebt Abenteuer & Freundschaft?",
    "Magie & Fantasie": "Dein Kind liebt Magie & Fantasie?",
    "Sport & Wettkämpfe": "Dein Kind liebt Sport & Wettkämpfe?",
    "Humor & lustige Geschichten": "Dein Kind liebt Humor & lustige Geschichten?",
    "Action & Spannung": "Dein Kind liebt Action & Spannung?",
    "Tiefgründige Geschichten": "Dein Teenager liebt tiefgründige Geschichten?",
}

# imdb_id -> Schluessel, fuer die beiden Titel, die schon im Bestand stehen
SCHON_DA = {"chihiro": "tt0245429", "haikyu": "serie-haikyu"}

# Zusatzhinweise je Titel, nur wo es etwas zu sagen gibt
HINWEIS = {
    "avatar": "Im Beitrag mit Sternchen: US-Zeichentrickserie, kein japanischer Anime.",
    "chi": "Sehr kurze Folgen (ca. 3 Minuten).",
    "hamtaro": "Keine deutsche Altersfreigabe belegbar; die Serie lief im RTL-II-Kinderprogramm.",
}

# Einstufung aus der FLIMMO-Besprechung. Mehrwert = vermittelt erkennbar etwas,
# solide = warmherzig ohne Lerneffekt, spass = Klamauk, Tempo oder Merchandising.
# Nur dort gesetzt, wo eine Besprechung vorliegt - sonst bleibt die Stufe offen.
STUFE_AUS_FLIMMO = {
    "pokemon":  "spass",     # FLIMMO: temporeich, weckt Sammel- und Konsumwuensche
    "kiki":     "mehrwert",  # Erwachsenwerden, Selbststaendigkeit; dazu Metacritic 85 / RT 98
    "inazuma":  "solide",    # Teamgeist, aber kein Lerneffekt
    "avatar":   "mehrwert",  # starke Identifikationsfigur, Verantwortung
    "naruto":   "spass",     # FLIMMO gelb: Gewalt als einziges Mittel der Konfliktloesung
}


def lade(p):
    with open(os.path.join(BASIS, p), encoding="utf-8") as f:
        return json.load(f, object_pairs_hook=collections.OrderedDict)


def schluessel_fuer(titel_de):
    """Ordnet den recherchierten Datensatz einem Reel-Schluessel zu."""
    t = titel_de.lower()
    for k, (_, _, name) in REEL.items():
        if name.lower() in t or t in name.lower():
            return k
    tabelle = {"kleine katze chi": "chi", "sekunden in moll": "yourlie",
               "avatar - der herr der elemente": "avatar",
               "a silent voice": "silentvoice"}
    return tabelle.get(t)


def empfehlung(k, fl):
    kat, alter, name = REEL[k]
    hinweis = HINWEIS.get(k)
    if fl and fl.get("gefunden") and fl.get("hinweis"):
        teil = "FLIMMO: " + fl["hinweis"]
        hinweis = (hinweis + " " + teil) if hinweis else teil
    return collections.OrderedDict([
        ("quelle", QUELLE),
        ("liste", LISTE),
        ("kategorie", kat),
        ("zitat", FRAGE[kat]),
        ("beitrag_url", BEITRAG),
        ("beitrag_datum", HEUTE),
        ("alter_ab", alter),
        ("alter_bis", None),
        ("hinweis", hinweis),
        ("erfasst_am", HEUTE),
    ])


def paedagogik(k, fl):
    if not (fl and fl.get("gefunden")):
        return collections.OrderedDict([
            ("stufe", None), ("flimmo_ab", None), ("ampel", None),
            ("mitnahme", None), ("hinweis", None),
            ("quelle", None), ("quelle_url", None), ("geprueft_am", HEUTE)])
    return collections.OrderedDict([
        ("stufe", STUFE_AUS_FLIMMO.get(k)),
        ("flimmo_ab", fl.get("flimmo_ab")),
        ("ampel", fl.get("ampel")),
        ("mitnahme", fl.get("mitnahme")),
        ("hinweis", fl.get("hinweis")),
        ("quelle", fl.get("quelle")),
        ("quelle_url", fl.get("quelle_url")),
        ("geprueft_am", HEUTE),
    ])


def serie_aus(r, k, fl):
    return collections.OrderedDict([
        ("id", r["imdb_id"]), ("imdb_id", r["imdb_id"]), ("tmdb_id", r.get("tmdb_id")),
        ("titel_de", r["titel_de"]), ("originaltitel", r.get("originaltitel")),
        ("erscheinungsjahr", r.get("erscheinungsjahr")),
        ("genres", r.get("genres") or []), ("subgenre", r.get("subgenre")),
        ("beschreibung_de", r.get("beschreibung_de")), ("beschreibung_es", None),
        ("bewertungen", r.get("bewertungen") or {}),
        ("verfuegbarkeit_de", r.get("verfuegbarkeit_de") or []),
        ("streaming_checked_at", HEUTE),
        ("sprache_original", r.get("sprache_original") or []),
        ("produktionsland", r.get("produktionsland") or []),
        ("fsk", r.get("fsk")), ("fsk_quelle", r.get("fsk_quelle")),
        ("fsk_stand", HEUTE if r.get("fsk") is not None else None),
        ("fsk_hinweis", r.get("fsk_hinweis")),
        ("poster_url", None), ("trailer_url", None),
        ("content_status", "ACTIVE"), ("vertrauensstufe", "mittel"),
        ("quellen", r.get("quellen") or []), ("datenerhebung_am", HEUTE),
        ("empfehlungen", [empfehlung(k, fl)]),
        ("seasons", []), ("anzahl_episoden", r.get("anzahl_episoden")),
        ("episodeRuntimeMin", r.get("episodeRuntimeMin")),
        ("sprachfassungen", None),
        ("startYear", r.get("startYear")), ("endYear", r.get("endYear")),
        ("productionStatus", r.get("productionStatus")),
        ("creator", r.get("creator")), ("regie", r.get("regie") or []),
        ("hauptdarsteller", r.get("hauptdarsteller") or []),
        ("themen_schlagworte", r.get("themen_schlagworte") or []),
        ("stimmung", r.get("stimmung")), ("tempo", r.get("tempo")),
        ("komplexitaet", r.get("komplexitaet")),
        ("filmtyp", r.get("filmtyp")), ("filmabend_typ", r.get("filmabend_typ") or []),
        ("universen", []), ("releases", []),
        ("werte_hinweise", r.get("werte_hinweise")),
        ("created_at", HEUTE), ("updated_at", HEUTE),
        ("paedagogik", paedagogik(k, fl)),
    ])


def film_aus(r, k, fl):
    return collections.OrderedDict([
        ("id", r["imdb_id"]), ("imdb_id", r["imdb_id"]), ("tmdb_id", r.get("tmdb_id")),
        ("titel_de", r["titel_de"]), ("originaltitel", r.get("originaltitel")),
        ("erscheinungsjahr", r.get("erscheinungsjahr")), ("release", None),
        ("laufzeit_min", r.get("laufzeit_min")),
        ("genres", r.get("genres") or []), ("subgenre", r.get("subgenre")),
        ("beschreibung_de", r.get("beschreibung_de")), ("beschreibung_es", None),
        ("bewertungen", r.get("bewertungen") or {}),
        ("verfuegbarkeit_de", r.get("verfuegbarkeit_de") or []),
        ("streaming_checked_at", HEUTE),
        ("sprache_original", r.get("sprache_original") or []),
        ("produktionsland", r.get("produktionsland") or []),
        ("fsk", r.get("fsk")), ("fsk_quelle", r.get("fsk_quelle")),
        ("fsk_stand", HEUTE if r.get("fsk") is not None else None),
        ("fsk_hinweis", r.get("fsk_hinweis")),
        ("poster_url", None), ("trailer_url", None),
        ("content_status", "ACTIVE"), ("vertrauensstufe", "mittel"),
        ("quellen", r.get("quellen") or []), ("datenerhebung_am", HEUTE),
        ("empfehlungen", [empfehlung(k, fl)]),
        ("regie", r.get("regie") or []),
        ("hauptdarsteller", r.get("hauptdarsteller") or []),
        ("themen_schlagworte", r.get("themen_schlagworte") or []),
        ("stimmung", r.get("stimmung")), ("tempo", r.get("tempo")),
        ("komplexitaet", r.get("komplexitaet")),
        ("filmtyp", r.get("filmtyp")), ("filmabend_typ", r.get("filmabend_typ") or []),
        ("universen", []), ("releases", []),
        ("werte_hinweise", r.get("werte_hinweise")),
        ("created_at", HEUTE), ("updated_at", HEUTE),
        ("paedagogik", paedagogik(k, fl)),
    ])


def main():
    filme = lade("data/films.json")
    serien = lade("data/series.json")
    flimmo = lade("import/flimmo-anime.json")
    neu = lade("import/anime-01.json") + lade("import/anime-02.json")

    vorhandene_ids = {x.get("id") for x in filme + serien}
    vorhandene_imdb = {x.get("imdb_id") for x in filme + serien if x.get("imdb_id")}
    vorhandene_tmdb = {x.get("tmdb_id") for x in filme + serien if x.get("tmdb_id")}

    zahl_neu = zahl_update = 0
    bericht = []

    for r in neu:
        k = schluessel_fuer(r["titel_de"])
        if not k:
            sys.exit("Kein Reel-Schluessel fuer %r" % r["titel_de"])
        fl = flimmo.get(k)
        if not r.get("imdb_id"):
            sys.exit("Ohne imdb_id kein Eintrag: %s" % r["titel_de"])
        if r["imdb_id"] in vorhandene_imdb or r["imdb_id"] in vorhandene_ids:
            bericht.append(("uebersprungen (schon da)", r["titel_de"])); continue
        if r.get("tmdb_id") and r["tmdb_id"] in vorhandene_tmdb:
            bericht.append(("uebersprungen (tmdb_id schon da)", r["titel_de"])); continue
        if r["art"] == "serie":
            serien.append(serie_aus(r, k, fl))
        else:
            filme.append(film_aus(r, k, fl))
        vorhandene_imdb.add(r["imdb_id"])
        if r.get("tmdb_id"): vorhandene_tmdb.add(r["tmdb_id"])
        zahl_neu += 1
        bericht.append(("neu", "%s (%s, FSK %s, Stufe %s)" % (
            r["titel_de"], r["art"], r.get("fsk"),
            paedagogik(k, fl)["stufe"] or "offen")))

    # Die beiden, die schon im Bestand stehen: nur den Empfehlungsblock ergaenzen
    for k, ident in SCHON_DA.items():
        ziel = None
        for x in filme + serien:
            if x.get("id") == ident: ziel = x; break
        if not ziel:
            bericht.append(("FEHLT", ident)); continue
        vorhanden = ziel.get("empfehlungen") or []
        if any(e.get("liste") == LISTE for e in vorhanden):
            bericht.append(("Empfehlung schon da", ziel["titel_de"])); continue
        vorhanden.append(empfehlung(k, flimmo.get(k)))
        ziel["empfehlungen"] = vorhanden
        ziel["updated_at"] = HEUTE
        zahl_update += 1
        bericht.append(("Empfehlung ergaenzt", ziel["titel_de"]))

    with open(os.path.join(D, "films.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps(filme, ensure_ascii=False, indent=2) + "\n")
    with open(os.path.join(D, "series.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps(serien, ensure_ascii=False, indent=2) + "\n")

    for art, text in bericht:
        print("  %-28s %s" % (art, text))
    print("\nneu: %d | Empfehlung ergaenzt: %d" % (zahl_neu, zahl_update))
    print("Bestand jetzt: %d Filme, %d Serien" % (len(filme), len(serien)))


if __name__ == "__main__":
    main()
