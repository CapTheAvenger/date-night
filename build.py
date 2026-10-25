#!/usr/bin/env python3
"""Baut aus den kanonischen JSON-Dateien in data/ die data/*.js fuer das Artifact.
   Quelle der Wahrheit sind immer die .json-Dateien."""
import json, os
BASE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(BASE, "data")
MAP = {"films": "films", "series": "series", "restaurants": "restaurants",
       "activities": "activities", "relations": "relations",
       "personal-data": "personal", "research-queue": "researchQueue",
       "family": "family", "cover-assets": "coverAssets"}
for fname, key in MAP.items():
    src = os.path.join(D, fname + ".json")
    if not os.path.exists(src):
        print("fehlt:", src); continue
    data = json.load(open(src, encoding="utf-8"))
    out = "window.DN=window.DN||{};window.DN.%s=%s;\n" % (key, json.dumps(data, ensure_ascii=False))
    open(os.path.join(D, fname.replace("-", "_") + ".js"), "w", encoding="utf-8").write(out)
    n = len(data) if isinstance(data, list) else "obj"
    print("%-20s -> %s.js (%s)" % (fname + ".json", fname.replace("-", "_"), n))
