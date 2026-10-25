# -*- coding: utf-8 -*-
"""Prueft die Anime-Empfehlungen von @teacher__light und den Grundzustand der App."""
import os, json, asyncio
from playwright.async_api import async_playwright
SCR = os.path.dirname(os.path.abspath(__file__)); URL = "file://" + SCR + "/app/index.html"
res = []
def chk(n, ok, e=""): res.append((n, bool(ok), e))

TITEL = ["Pokémon", "Digimon Adventure", "One Piece", "Kikis kleiner Lieferservice",
         "Little Witch Academia", "Chihiros Reise ins Zauberland", "Inazuma Eleven",
         "Haikyu!!", "Blue Lock", "Kleine Katze Chi", "Hamtaro", "Spy x Family",
         "Avatar – Der Herr der Elemente", "Naruto", "My Hero Academia",
         "Your Lie in April", "Violet Evergarden", "A Silent Voice"]

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        fehler = []; pg.on("pageerror", lambda x: fehler.append(str(x)))
        await pg.goto(URL); await pg.wait_for_timeout(1800)

        # ---------- Grundzustand ----------
        r = await pg.evaluate("""(()=>({filme:DATA.items.filter(i=>i.kind==='film').length,
          serien:DATA.items.filter(i=>i.kind==='serie').length,
          rest:DATA.items.filter(i=>i.kind==='restaurant').length,
          akt:DATA.items.filter(i=>i.kind==='aktivitaet').length}))()""")
        chk("515 Filme", r["filme"] == 515, json.dumps(r))
        chk("380 Serien", r["serien"] == 380, json.dumps(r))
        chk("Restaurants und Aktivitaeten unberuehrt", r["rest"] == 41 and r["akt"] == 3, json.dumps(r))

        # ---------- alle 18 Titel da, mit Empfehlungsblock ----------
        r = await pg.evaluate("""(soll)=>{
          const out={};
          soll.forEach(t=>{
            const i=DATA.items.find(x=>x.title===t);
            out[t]= i ? {id:i.id, fsk:i.fsk, art:i.kind,
              empf:(i.empfehlungen||[]).filter(e=>/teacher__light/.test(e.quelle||'')
                   && e.liste==='Welcher Anime passt zu deinem Kind?')
                   .map(e=>({ab:e.alter_ab, kat:e.kategorie})),
              stufe:(i.paedagogik||{}).stufe} : null;});
          return out;}""", TITEL)
        fehlend = [t for t, v in r.items() if not v]
        chk("alle 18 Titel im Bestand", not fehlend, json.dumps(fehlend, ensure_ascii=False))
        ohne = [t for t, v in r.items() if v and not v["empf"]]
        chk("alle 18 mit Empfehlungsblock", not ohne, json.dumps(ohne, ensure_ascii=False))
        doppelt = [t for t, v in r.items() if v and len(v["empf"]) > 1]
        chk("kein Block doppelt", not doppelt, json.dumps(doppelt, ensure_ascii=False))

        # Alter laut Beitrag
        SOLL_ALTER = {"Pokémon":7,"Digimon Adventure":9,"One Piece":13,
          "Kikis kleiner Lieferservice":6,"Little Witch Academia":8,
          "Chihiros Reise ins Zauberland":10,"Inazuma Eleven":9,"Haikyu!!":13,
          "Blue Lock":14,"Kleine Katze Chi":5,"Hamtaro":5,"Spy x Family":13,
          "Avatar – Der Herr der Elemente":9,"Naruto":12,"My Hero Academia":14,
          "Your Lie in April":13,"Violet Evergarden":14,"A Silent Voice":15}
        falsch = [t for t, v in r.items() if v and v["empf"] and v["empf"][0]["ab"] != SOLL_ALTER[t]]
        chk("Altersangaben wie im Beitrag", not falsch, json.dumps(falsch, ensure_ascii=False))
        kat = sorted({v["empf"][0]["kat"] for v in r.values() if v and v["empf"]})
        chk("sechs Kategorien", len(kat) == 6, json.dumps(kat, ensure_ascii=False))

        # ---------- Was Noah sehen kann ----------
        noah = await pg.evaluate("""(soll)=>{
          state.audience='noah';
          const drin=[], raus=[];
          soll.forEach(t=>{const i=DATA.items.find(x=>x.title===t); if(!i) return;
            (weightOf(i)>0 ? drin : raus).push(t+' (FSK '+i.fsk+')');});
          const pool=rouletteCandidates('serie').filter(i=>weightOf(i)>0);
          const schlimm=pool.filter(i=>i.fsk===null||i.fsk===undefined||Number(i.fsk)>6);
          return {drin, raus, schlimm:schlimm.map(i=>i.title)};}""", TITEL)
        chk("Noah sieht nichts ueber FSK 6", not noah["schlimm"], json.dumps(noah["schlimm"], ensure_ascii=False))
        chk("Titel ohne FSK bleiben bei Noah draussen",
            any("Hamtaro" in x for x in noah["raus"]), json.dumps(noah["raus"], ensure_ascii=False)[:300])

        # ---------- Empfehlungsfilter kennt die neue Liste ----------
        r = await pg.evaluate("""(()=>{
          state.audience='familie';
          const d=filterDefs('serie').find(x=>x.key==='empfehlung');
          return d? d.options.map(o=>o.v) : null;})()""")
        chk("Quellenfilter kennt @teacher__light",
            r and any('teacher__light' in str(v) for v in r), json.dumps(r, ensure_ascii=False)[:200])

        # ---------- Detailblatt zeigt Empfehlung und Disclaimer ----------
        r = await pg.evaluate("""(()=>{
          const i=DATA.items.find(x=>x.title==='Naruto');
          openSheet(i.id);
          const txt=document.querySelector('.sheet').textContent;
          const offen=!!document.querySelector('.sheet');
          return {offen, hatAlter:/empfohlen ab 12/i.test(txt),
                  hatDisclaimer:/keine Altersfreigabe/i.test(txt),
                  hatFlimmo:/FLIMMO/.test(txt), hatWarnung:/⚠/.test(txt),
                  fsk16:/FSK 16|16/.test(txt)};})()""")
        await pg.wait_for_timeout(300)
        chk("Detailblatt zeigt das Empfehlungsalter", r["hatAlter"], json.dumps(r))
        chk("Detailblatt sagt: keine Altersfreigabe", r["hatDisclaimer"], json.dumps(r))
        chk("Naruto zeigt die FLIMMO-Besprechung", r["hatFlimmo"], json.dumps(r))
        chk("Naruto traegt die Warnung", r["hatWarnung"], json.dumps(r))
        await pg.evaluate("closeSheet()"); await pg.wait_for_timeout(200)

        # ---------- Einstufung ----------
        r = await pg.evaluate("""(soll)=>{
          const out={};
          soll.forEach(t=>{const i=DATA.items.find(x=>x.title===t);
            if(i) out[t]=(i.paedagogik||{}).stufe||null;});
          return out;}""", TITEL)
        mit = {t: v for t, v in r.items() if v}
        chk("fuenf neue Titel eingestuft, Rest bewusst offen",
            len(mit) >= 7, json.dumps(mit, ensure_ascii=False))

        # ---------- Suche findet sie ----------
        r = await pg.evaluate("""(()=>{
          const f=(q)=>DATA.items.filter(i=>i.searchText.includes(q)).map(i=>i.title);
          return {chi:f('sweet home'), yourlie:f('sekunden in moll'),
                  avatar:f('last airbender'), silent:f('koe no katachi')};})()""")
        chk("Chi ueber 'Sweet Home' auffindbar", r["chi"], json.dumps(r["chi"], ensure_ascii=False))
        chk("Your Lie ueber den dt. Titel auffindbar", r["yourlie"], json.dumps(r["yourlie"], ensure_ascii=False))
        chk("Avatar ueber den Originaltitel auffindbar", r["avatar"], json.dumps(r["avatar"], ensure_ascii=False))

        # ---------- nichts kaputt ----------
        r = await pg.evaluate("""(()=>{
          state.audience='wir'; go({name:'home'}); render();
          const h=document.querySelector('#view').textContent.length;
          go({name:'collection',kind:'serie'}); render();
          const c=document.querySelectorAll('.card').length;
          go({name:'familie'}); render();
          const f=document.querySelector('#view').textContent.length;
          go({name:'home'}); render();
          return {home:h, karten:c, familie:f};})()""")
        chk("Startseite rendert", r["home"] > 200, json.dumps(r))
        chk("Sammlung rendert Karten", r["karten"] > 0, json.dumps(r))
        chk("Familienbereich rendert", r["familie"] > 200, json.dumps(r))

        chk("keine Seitenfehler", not fehler, "; ".join(fehler[:2]))
        await b.close()

asyncio.run(main())
ok = sum(1 for _, o, _ in res if o)
for n, o, e in res:
    print("  %-4s %-48s %s" % ("OK" if o else "FEHL", n, e if not o else ("[%s]" % e[:110] if e else "")))
print("\n%d von %d bestanden" % (ok, len(res)))
