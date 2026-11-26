# -*- coding: utf-8 -*-
"""Prueft den Import von Captain Tsubasa (26.11.2026): Eintrag, Franchise, Noahs Merkliste, Detailansicht."""
import os, json, asyncio
from playwright.async_api import async_playwright
SCR = os.path.dirname(os.path.abspath(__file__)); URL = "file://" + SCR + "/app/index.html"
res = []
def chk(n, ok, e=""): res.append((n, bool(ok), e))
ID = "serie-captain-tsubasa"

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        fehler = []; pg.on("pageerror", lambda x: fehler.append(str(x)))
        await pg.goto(URL); await pg.wait_for_timeout(1800)
        r = await pg.evaluate("""(id)=>{const i=DATA.byId.get(id); if(!i) return null;
          return {kind:i.kind, fsk:i.fsk, title:i.title, uni:i.universes, kind_:istKinderinhalt(i),
            abo:aboStand(i).abos.map(a=>a.id), gratis:aboStand(i).gratis,
            n:DATA.items.filter(x=>x.kind==='serie').length,
            dup:DATA.items.filter(x=>/tsubasa/i.test(x.title)).length}}""", ID)
        chk("Serie da, genau einmal", r and r["kind"] == "serie" and r["dup"] == 1, json.dumps(r, ensure_ascii=False))
        chk("FSK 6", r and r["fsk"] == 6)
        chk("Kinderinhalt (eigene Einschaetzung ab 6)", r and r["kind_"])
        chk("Franchise captain-tsubasa", r and r["uni"] == ["captain-tsubasa"])
        chk("Abo: RTL+, Toggo kostenlos, Aniverse-Channel nicht", r and r["abo"] == ["rtl"] and "Toggo" in r["gratis"], json.dumps(r, ensure_ascii=False))
        r = await pg.evaluate("""(id)=>{
          const noah=audienceProfiles('noah')[0];
          return {wl:onWatchlist(DATA.byId.get(id), noah), alter:ageOk(DATA.byId.get(id), noah),
                  empf:empfehlungsAlterOk(DATA.byId.get(id), noah),
                  user:onWatchlist(DATA.byId.get(id),'user'), camila:onWatchlist(DATA.byId.get(id),'camila')}}""", ID)
        chk("Noah: auf der Merkliste, Alter passt", r["wl"] and r["alter"] and r["empf"], json.dumps(r))
        chk("Nur Noah, nicht Ich/Camila", not r["user"] and not r["camila"], json.dumps(r))
        r = await pg.evaluate("""(()=>{const u=(DATA.universes.get('captain-tsubasa')||{});
          const rel=(window.DN.relations.beziehungen||[]).filter(b=>b.von==='serie-captain-tsubasa');
          return {name:u.name, typ:rel.map(x=>x.typ), ext:rel.map(x=>x.externer_titel)}})()""")
        chk("Vier Beziehungen zu den Folgeserien", r["typ"] == ["has_sequel", "has_sequel", "related", "related"], json.dumps(r, ensure_ascii=False))
        await pg.evaluate("(id)=>openSheet(id)", ID); await pg.wait_for_timeout(500)
        t = await pg.evaluate("document.querySelector('.sheet').innerText")
        chk("Detail: Abo-Zeile RTL+", "In euren Abos" in t and "RTL+" in t)
        chk("Detail: eigene Einschaetzung sichtbar", "eigene Einschätzung" in t)
        chk("Detail: Folgeserien sichtbar", "Captain Tsubasa J" in t, t[:200])
        await pg.screenshot(path=os.path.join(SCR, "tsubasa.png"), full_page=False)
        q = await pg.evaluate("""(()=>state.researchQueue.filter(e=>/tsubasa/.test(e.id)).map(e=>e.id+':'+e.status))()""")
        chk("Aufgaben: Import und Franchise erledigt", "rq-tsubasa-import-2026-11-25:completed" in q and "rq-tsubasa-relations-2026-11-25:completed" in q, json.dumps(q))
        chk("Keine Skriptfehler", not fehler, "; ".join(fehler[:3]))
        await b.close()

asyncio.run(main())
ok = sum(1 for r in res if r[1])
for n, g, e in res:
    print(("  OK  " if g else "  FEHL") + "  " + n + ("" if g else "   " + e))
print("\n%d von %d bestanden" % (ok, len(res)))
