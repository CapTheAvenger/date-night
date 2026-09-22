#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Holt Poster von TMDb und legt sie als kleine JPEGs unter covers/ ab.

Liest data/titles.json (nur Titel und Kennungen, keine persoenlichen Daten)
und laeuft in einer GitHub Action, weil diese Umgebung freies Internet hat.
Braucht das Repository-Secret TMDB_API_KEY (kostenlos auf themoviedb.org).

Es wird nichts erfunden: findet der Lauf kein Poster, bleibt der Eintrag ohne
Cover und wird im Bericht als offen gefuehrt. Bereits vorhandene Dateien werden
nur ersetzt, wenn sich das Poster bei TMDb geaendert hat.
"""
import json, os, re, sys, time, io, pathlib, urllib.parse, urllib.request

WURZEL   = pathlib.Path(__file__).resolve().parent.parent
DATEN    = WURZEL / "data"
COVERS   = WURZEL / "covers"
SCHLUESSEL = os.environ.get("TMDB_API_KEY", "").strip()
BASIS    = "https://api.themoviedb.org/3"
BILD     = "https://image.tmdb.org/t/p/w500"
SPRACHE  = "de-DE"
ZIEL     = (400, 600)          # Kartengroesse, doppelte Aufloesung reicht

if not SCHLUESSEL:
    sys.exit("TMDB_API_KEY fehlt. In den Repository-Secrets hinterlegen.")

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow fehlt (pip install pillow).")


def hole(pfad, **params):
    params["api_key"] = SCHLUESSEL
    url = BASIS + pfad + "?" + urllib.parse.urlencode(params)
    for versuch in range(4):
        try:
            with urllib.request.urlopen(url, timeout=25) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            if versuch == 3:
                print("  ! Abruf fehlgeschlagen: %s" % e)
                return None
            time.sleep(1.5 * (versuch + 1))
    return None


def dateiname(cid):
    """IDs koennen Doppelpunkte enthalten (tmp:...) - daraus einen Dateinamen machen."""
    return re.sub(r"[^A-Za-z0-9._-]", "_", str(cid)) + ".jpg"


def finde(eintrag, art):
    """Rueckgabe: (tmdb_id, poster_path, wie_gefunden) oder (None, None, Grund)."""
    tmdb_typ = "movie" if art == "film" else "tv"

    if eintrag.get("tmdb_id"):
        d = hole("/%s/%s" % (tmdb_typ, eintrag["tmdb_id"]), language=SPRACHE)
        if d and d.get("poster_path"):
            return d["id"], d["poster_path"], "tmdb_id"

    if eintrag.get("imdb_id"):
        d = hole("/find/" + eintrag["imdb_id"], external_source="imdb_id", language=SPRACHE)
        if d:
            treffer = (d.get("movie_results") or []) if art == "film" else (d.get("tv_results") or [])
            if treffer and treffer[0].get("poster_path"):
                return treffer[0]["id"], treffer[0]["poster_path"], "imdb_id"

    # Notloesung: Titelsuche, nur bei eindeutigem Jahrestreffer uebernehmen
    titel = eintrag.get("originaltitel") or eintrag.get("titel")
    jahr  = eintrag.get("jahr")
    if not titel:
        return None, None, "kein Titel"
    p = {"query": titel, "language": SPRACHE, "include_adult": "false"}
    if jahr:
        p["year" if art == "film" else "first_air_date_year"] = jahr
    d = hole("/search/" + tmdb_typ, **p)
    treffer = (d or {}).get("results") or []
    if not treffer:
        # zweiter Versuch ohne Jahr
        p.pop("year", None); p.pop("first_air_date_year", None)
        d = hole("/search/" + tmdb_typ, **p)
        treffer = (d or {}).get("results") or []
    for t in treffer[:3]:
        if not t.get("poster_path"):
            continue
        datum = t.get("release_date") or t.get("first_air_date") or ""
        if jahr and datum[:4] and abs(int(datum[:4]) - int(jahr)) > 1:
            continue
        return t["id"], t["poster_path"], "Titelsuche"
    return None, None, "kein Poster gefunden"


def lade_bild(poster_path):
    url = BILD + poster_path
    for versuch in range(3):
        try:
            with urllib.request.urlopen(url, timeout=40) as r:
                return r.read()
        except Exception:
            time.sleep(1.5 * (versuch + 1))
    return None


def speichere(rohdaten, ziel):
    im = Image.open(io.BytesIO(rohdaten)).convert("RGB")
    im.thumbnail(ZIEL, Image.LANCZOS)
    im.save(ziel, "JPEG", quality=84, optimize=True, progressive=True)
    return ziel.stat().st_size


def main():
    COVERS.mkdir(exist_ok=True)
    index_pfad = COVERS / "index.json"
    index = {}
    if index_pfad.exists():
        index = json.loads(index_pfad.read_text(encoding="utf-8")).get("cover", {})

    neu = aktualisiert = unveraendert = 0
    offen = []

    quelle = json.loads((DATEN / "titles.json").read_text(encoding="utf-8"))
    for e in quelle["titel"]:
        cid   = e.get("id")
        art   = e.get("art")
        titel = e.get("titel") or cid
        tid, ppath, wie = finde(e, art)
        if not ppath:
            offen.append("%s (%s): %s" % (titel, cid, wie))
            print("  - %-52s %s" % (titel[:52], wie)); continue

        alt = index.get(cid) or {}
        ziel = COVERS / dateiname(cid)
        if alt.get("poster_path") == ppath and ziel.exists():
            unveraendert += 1; continue

        rohdaten = lade_bild(ppath)
        if not rohdaten:
            offen.append("%s (%s): Download fehlgeschlagen" % (titel, cid)); continue
        groesse = speichere(rohdaten, ziel)
        if alt:
            aktualisiert += 1
        else:
            neu += 1
        index[cid] = {
            "datei": "covers/" + ziel.name,
            "art": art,
            "titel": titel,
            "tmdb_id": tid,
            "poster_path": ppath,
            "gefunden_ueber": wie,
            "bytes": groesse,
            "geholt_am": time.strftime("%Y-%m-%d"),
        }
        print("  + %-52s %6d B  (%s)" % (titel[:52], groesse, wie))
        time.sleep(0.12)

    index_pfad.write_text(json.dumps({
        "hinweis": "Poster von TMDb (themoviedb.org). Dieses Projekt ist privat und "
                   "wird nicht von TMDb unterstuetzt oder zertifiziert.",
        "stand": time.strftime("%Y-%m-%d"),
        "anzahl": len(index),
        "cover": index,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("\nneu %d | aktualisiert %d | unveraendert %d | ohne Poster %d"
          % (neu, aktualisiert, unveraendert, len(offen)))
    if offen:
        print("\nOhne Poster:")
        for z in offen:
            print("  -", z)
    zus = os.environ.get("GITHUB_STEP_SUMMARY")
    if zus:
        with open(zus, "a", encoding="utf-8") as f:
            f.write("## Poster-Lauf\n\n")
            f.write("| neu | aktualisiert | unveraendert | ohne Poster |\n|--:|--:|--:|--:|\n")
            f.write("| %d | %d | %d | %d |\n\n" % (neu, aktualisiert, unveraendert, len(offen)))
            if offen:
                f.write("### Ohne Poster\n\n" + "\n".join("- " + z for z in offen) + "\n")


if __name__ == "__main__":
    main()
