#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Erzeugt data/titles.json fuer den Poster-Lauf.

Enthaelt NUR Titel und Kennungen - keine Bewertungen, keine Merklisten,
nichts Persoenliches. Die Datei liegt in einem oeffentlichen Repo.
"""
import json, os
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
raus = []
for datei, art in (("films.json", "film"), ("series.json", "serie")):
    for x in json.load(open(os.path.join(B, "data", datei), encoding="utf-8")):
        raus.append({"id": x.get("id"), "art": art,
                     "titel": x.get("titel_de"), "originaltitel": x.get("originaltitel"),
                     "jahr": x.get("erscheinungsjahr"),
                     "imdb_id": x.get("imdb_id"), "tmdb_id": x.get("tmdb_id")})
zeilen = ",\n    ".join(json.dumps(t, ensure_ascii=False) for t in raus)
open(os.path.join(B, "data", "titles.json"), "w", encoding="utf-8").write(
    '{\n  "hinweis": "Nur Titel und Kennungen fuer den Poster-Lauf. Keine persoenlichen Daten.",\n'
    '  "anzahl": %d,\n  "titel": [\n    %s\n  ]\n}\n' % (len(raus), zeilen))
print("data/titles.json: %d Titel" % len(raus))
