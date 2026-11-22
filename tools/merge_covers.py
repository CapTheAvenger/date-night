#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Uebernimmt neue Cover und fehlende Altersfreigaben aus dem Poster-Lauf.

Aufruf:  python3 tools/merge_covers.py <pfad/zu/covers>   (mit index.json, alter.json, *.jpg)

- poster_url wird nur bei Eintraegen OHNE Cover gesetzt (vorhandene bleiben).
- Treffer der Titelsuche nur, wenn Titel UND Jahr (+-1) stimmen - sonst Bericht.
- fsk wird nur gesetzt, wenn der Eintrag keine hat UND kein fsk_hinweis
  dagegen spricht. Eine gepflegte FSK wird NIE ueberschrieben.
- Kopiert die neuen JPEGs nach covers/ und schreibt die Liste der Dateien,
  die noch in den Asset-Speicher muessen, nach covers/_neu.txt.
"""
import json, os, re, sys, shutil, unicodedata

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATEN = os.path.join(BASE, "data")


def norm(t):
    t = unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", t)


def titel_passt(e, item):
    soll = {norm(item.get(k)) for k in ("titel_de", "title", "titel", "originaltitel", "original_title")} - {""}
    if norm(e.get("tmdb_titel")) not in soll:
        return False
    j1, j2 = e.get("tmdb_jahr"), e.get("erwartet_jahr")
    return bool(j1 and j2 and abs(int(j1) - int(j2)) <= 1)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    quelle = sys.argv[1]
    idx = json.load(open(os.path.join(quelle, "index.json"), encoding="utf-8"))["cover"]
    alter = json.load(open(os.path.join(quelle, "alter.json"), encoding="utf-8"))["freigaben"]
    os.makedirs(os.path.join(BASE, "covers"), exist_ok=True)
    neu_dateien, abgelehnt, fsk_neu = [], [], []
    for datei in ("films.json", "series.json"):
        pfad = os.path.join(DATEN, datei)
        items = json.load(open(pfad, encoding="utf-8"))
        for it in items:
            e = idx.get(it.get("id"))
            if e and not it.get("poster_url"):
                if e.get("gefunden_ueber") not in ("tmdb_id", "imdb_id") and not titel_passt(e, it):
                    abgelehnt.append("%s: TMDb nennt %r %s" % (it.get("titel_de") or it["id"], e.get("tmdb_titel"), e.get("tmdb_jahr")))
                else:
                    src = os.path.join(quelle, os.path.basename(e["datei"]))
                    if os.path.exists(src):
                        shutil.copy(src, os.path.join(BASE, e["datei"]))
                        it["poster_url"] = e["datei"]
                        neu_dateien.append(e["datei"])
            a = alter.get(it.get("id"))
            if a and it.get("fsk") is None and not it.get("fsk_hinweis"):
                # Ohne Cover-Eintrag weiss man nicht, wie TMDb den Titel gefunden
                # hat - dann nur mit fester Kennung uebernehmen.
                fest = it.get("tmdb_id") or it.get("imdb_id")
                if (e is None and fest) or (e is not None and (e.get("gefunden_ueber") in ("tmdb_id", "imdb_id") or titel_passt(e, it))):
                    it["fsk"] = a["fsk"]
                    it["fsk_quelle"] = "TMDb (DE)"
                    fsk_neu.append("%s: FSK %s" % (it.get("titel_de") or it["id"], a["fsk"]))
        with open(pfad, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
            f.write("\n")
    open(os.path.join(BASE, "covers", "_neu.txt"), "w").write("\n".join(neu_dateien) + ("\n" if neu_dateien else ""))
    print("neue Cover: %d | neue FSK: %d | abgelehnt: %d" % (len(neu_dateien), len(fsk_neu), len(abgelehnt)))
    for z in fsk_neu: print("  FSK  ", z)
    for z in abgelehnt: print("  NEIN ", z)


if __name__ == "__main__":
    main()
