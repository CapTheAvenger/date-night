# date-night

Private Date-Night-Sammlung. Dieses Repository enthaelt **keine persoenlichen
Daten** – keine Bewertungen, keine Favoriten, keine Notizen, keine Fotos.
Die bleiben in der App selbst.

Hier liegt nur, was fuer die Poster-Beschaffung noetig ist.

## Was hier liegt

| Pfad | Zweck |
|---|---|
| `data/titles.json` | Titel, Jahr, IMDb-/TMDb-Kennung der 81 Filme und Serien |
| `tools/fetch_posters.py` | holt die Poster von TMDb und verkleinert sie |
| `.github/workflows/poster.yml` | laesst das Skript bei GitHub laufen |
| `covers/` | Ergebnis: je ein JPEG pro Titel plus `index.json` |

Warum der Umweg ueber GitHub: die Umgebung, in der die App gebaut wird, kommt
an keinen Bildserver heran. GitHubs Rechner schon.

## Einrichtung (einmalig)

1. **TMDb-Schluessel holen** – kostenlos auf
   <https://www.themoviedb.org/settings/api> (Konto anlegen, "API Read Access"
   bzw. "API Key (v3 auth)" kopieren).
2. **Als Secret hinterlegen** – hier im Repository unter
   *Settings → Secrets and variables → Actions → New repository secret*,
   Name exakt `TMDB_API_KEY`, Wert der Schluessel.
   Der Schluessel steht danach nirgends im Klartext im Repository.
3. **Lauf starten** – Reiter *Actions* → *Poster holen* → *Run workflow*.

Danach laeuft es ausserdem automatisch jeden Montag um 04:17 UTC, damit neu
hinzugekommene Titel ihr Cover bekommen.

## Was der Lauf macht

Fuer jeden Eintrag aus `data/titles.json`:

1. Suche bei TMDb ueber `tmdb_id`, sonst `imdb_id`, sonst Titel + Jahr
   (Jahrestreffer muss auf ein Jahr genau passen, sonst wird verworfen).
2. Poster herunterladen, auf maximal 400x600 verkleinern, als JPEG speichern.
3. Ergebnis in `covers/index.json` vermerken.

**Es wird nichts erfunden.** Findet der Lauf kein Poster, bleibt der Titel
ohne Cover und taucht in der Zusammenfassung unter "Ohne Poster" auf.
Vorhandene Dateien werden nur ersetzt, wenn TMDb ein anderes Poster fuehrt.

## Herkunft der Bilder

Poster von [TMDb](https://www.themoviedb.org). Dieses Projekt ist privat und
wird von TMDb weder unterstuetzt noch zertifiziert.
