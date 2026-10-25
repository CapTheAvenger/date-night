#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Baut aus app.html die Datei app/index.html fuer die Playwright-Suiten.

app.html ist ein Fragment: die Kopfzeile mit Zeichensatz und VIEWPORT setzt
das Artifact beim Veroeffentlichen dazu. Ohne sie misst jeder Mobiltest falsch.
Datenstaende und Cover werden mitkopiert - sonst laufen die Suiten gegen einen
alten Stand und melden "bestanden", ohne die neuen Eintraege gesehen zu haben.
"""
import os, shutil, glob, json

QUELLE = "/home/claude/datenight/app.html"
SCR    = os.path.dirname(os.path.abspath(__file__))
ZIEL   = os.path.join(SCR, "app", "index.html")
ZIEL_DATEN = os.path.join(SCR, "app", "data")
os.makedirs(ZIEL_DATEN, exist_ok=True)

HUELLE_AUF = (
    '<!doctype html><html><head><meta charset=utf8>'
    '<meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover">'
    '<style>:root{color-scheme:light;box-sizing:border-box}'
    'body{margin:0;padding:0;font:14px -apple-system,BlinkMacSystemFont,sans-serif;'
    'background:#fff;color:#000}img{max-width:100%}'
    '[hidden]:not([hidden=until-found i]){display:none!important}</style></head><body>\n')
HUELLE_ZU = "\n</body></html>\n"

rumpf = open(QUELLE, encoding="utf-8").read()
open(ZIEL, "w", encoding="utf-8").write(HUELLE_AUF + rumpf + HUELLE_ZU)
print("gebaut: %s (%d Zeichen)" % (ZIEL, len(rumpf)))

n = 0
for pfad in glob.glob(os.path.join(os.path.dirname(QUELLE), "data", "*.js")):
    shutil.copy2(pfad, ZIEL_DATEN); n += 1
print("Daten kopiert: %d Dateien" % n)

QUELL_COVER = os.path.join(os.path.dirname(QUELLE), "covers")
ZIEL_COVER  = os.path.join(SCR, "app", "covers")
if os.path.isdir(QUELL_COVER) and os.listdir(QUELL_COVER):
    shutil.copytree(QUELL_COVER, ZIEL_COVER, dirs_exist_ok=True)
    print("Cover kopiert: %d Dateien" % len(os.listdir(ZIEL_COVER)))
else:
    print("Cover: keine lokal vorhanden (Testaufbau zeigt Ersatz-Cover)")

# Im Testaufbau gibt es keinen Asset-Speicher: /_blob/<id> geht ins Leere.
# Zuordnung auf lokale Dateien umbiegen, damit die Suiten echte Bilder laden.
ca = os.path.join(os.path.dirname(QUELLE), "data", "cover-assets.json")
if os.path.exists(ca):
    d = json.load(open(ca, encoding="utf-8"))
    d["cover"] = {k: k for k in d.get("cover", {})}
    d["hinweis"] = "TESTAUFBAU: auf lokale Dateien umgebogen, siehe huelle.py"
    open(os.path.join(ZIEL_DATEN, "cover_assets.js"), "w", encoding="utf-8").write(
        "window.DN=window.DN||{};window.DN.coverAssets=%s;\n" % json.dumps(d, ensure_ascii=False))
    print("Cover-Zuordnung fuer den Test umgebogen (%d)" % len(d["cover"]))
