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
        # Die Datei muss klein genug bleiben, um ueber die Contents-API ins Repo
        # zu passen (ueber ~115 KB bricht der Aufruf ab). Darum nur, was der
        # Poster-Lauf wirklich braucht: tmdb_id hat im Skript Vorrang, die
        # imdb_id steht deshalb nur dort, wo keine tmdb_id vorhanden ist.
        e = {"id": x.get("id"), "art": art, "titel": x.get("titel_de"),
             "jahr": x.get("erscheinungsjahr"), "tmdb_id": x.get("tmdb_id")}
        if not x.get("tmdb_id"):
            e["imdb_id"] = x.get("imdb_id")
        ot = x.get("originaltitel")
        if ot and ot != x.get("titel_de"):
            e["originaltitel"] = ot
        raus.append(e)
zeilen = ",\n    ".join(json.dumps(t, ensure_ascii=False) for t in raus)
open(os.path.join(B, "data", "titles.json"), "w", encoding="utf-8").write(
    '{\n  "hinweis": "Nur Titel und Kennungen fuer den Poster-Lauf. Keine persoenlichen Daten.",\n'
    '  "anzahl": %d,\n  "titel": [\n    %s\n  ]\n}\n' % (len(raus), zeilen))
print("data/titles.json: %d Titel" % len(raus))
