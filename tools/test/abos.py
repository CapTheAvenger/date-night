# -*- coding: utf-8 -*-
"""Prueft die Abo-Anzeige: in welchem unserer Streaming-Abos laeuft ein Titel ohne Aufpreis."""
import os, json, asyncio
from playwright.async_api import async_playwright
SCR = os.path.dirname(os.path.abspath(__file__)); URL = "file://" + SCR + "/app/index.html"
res = []
def chk(n, ok, e=""): res.append((n, bool(ok), e))

# Synthetische Faelle: (Daten, erwartete Abos, erwartete Gratis, Beschreibung)
FAELLE = [
  ([{"anbieter": "Netflix", "typ": "abo"}], ["netflix"], [], "Netflix im Abo"),
  ([{"anbieter": "Netflix Standard with Ads", "typ": "abo"}], ["netflix"], [], "Netflix-Werbestufe zaehlt"),
  ([{"anbieter": "Disney Plus", "typ": "abo"}], ["disney"], [], "Disney Plus"),
  ([{"anbieter": "RTL+", "typ": "abo"}], ["rtl"], [], "RTL+"),
  ([{"anbieter": "RTL+ Max Amazon Channel", "typ": "abo"}], [], [], "RTL+-Channel bei Amazon zaehlt NICHT"),
  ([{"anbieter": "Apple TV+", "typ": "abo"}], ["apple"], [], "Apple TV+"),
  ([{"anbieter": "Apple TV", "typ": "abo"}], ["apple"], [], "Apple TV (neuer Name) als Abo"),
  ([{"anbieter": "Apple TV", "typ": "kauf"}], [], [], "Apple TV Kauf zaehlt NICHT"),
  ([{"anbieter": "Apple TV Store", "typ": "kauf"}], [], [], "Apple TV Store zaehlt NICHT"),
  ([{"anbieter": "Sky Go", "typ": "abo"}], ["sky"], [], "Sky Go"),
  ([{"anbieter": "WOW", "typ": "abo"}], ["sky"], [], "WOW = Sky-Katalog"),
  ([{"anbieter": "Sky/WOW", "typ": "abo"}], ["sky"], [], "Sky/WOW"),
  ([{"anbieter": "Amazon Prime Video", "typ": "abo"}], ["prime"], [], "Prime Video"),
  ([{"anbieter": "Prime Video", "typ": "abo"}], ["prime"], [], "Prime Video kurz"),
  ([{"anbieter": "Amazon Prime Video with Ads", "typ": "werbefinanziert"}], ["prime"], [], "Prime mit Werbung"),
  ([{"anbieter": "Amazon Video", "typ": "kauf"}], [], [], "Amazon Video (Laden) zaehlt NICHT"),
  ([{"anbieter": "Amazon Prime Video", "typ": "kauf"}], [], [], "Prime Video als Kauf zaehlt NICHT"),
  ([{"anbieter": "HBO Max Amazon Channel", "typ": "abo"}], [], [], "HBO-Channel zaehlt NICHT"),
  ([{"anbieter": "HBO Max", "typ": "abo"}], [], [], "HBO Max ist kein Abo von uns"),
  ([{"anbieter": "Paramount+", "typ": "abo"}], [], [], "Paramount+ ist kein Abo von uns"),
  ([{"anbieter": "Joyn", "typ": "kostenlos mit Werbung"}], [], ["Joyn"], "Joyn kostenlos"),
  ([{"anbieter": "ARD Mediathek", "typ": "abo"}], [], ["ARD Mediathek"], "Mediathek gilt als kostenlos"),
  ([{"anbieter": "Joyn Plus", "typ": "abo"}], [], [], "Joyn Plus kostet"),
  ([{"anbieter": "Leih/Kauf (u. a. Prime Video)", "typ": "abo"}], [], [], "Leih/Kauf-Text mit Prime im Namen zaehlt NICHT"),
  (["Disney+"], ["disney"], [], "Altformat: nur Text"),
  # Nachpruefung 22.11.: unbekannte Typen und Ladennamen nie als Abo
  ([{"anbieter": "Amazon Prime Video", "typ": "kaufen"}], [], [], "Typ 'kaufen' zaehlt NICHT"),
  ([{"anbieter": "Netflix", "typ": "rent"}], [], [], "Typ 'rent' zaehlt NICHT"),
  ([{"anbieter": "Apple TV", "typ": "Kauf/Leihe"}], [], [], "Typ 'Kauf/Leihe' zaehlt NICHT"),
  ([{"anbieter": "Amazon Prime Video (Kauf)", "typ": "abo"}], [], [], "Name mit '(Kauf)' zaehlt NICHT"),
  ([{"anbieter": "Netflix", "typ": ""}], ["netflix"], [], "leerer Typ zaehlt wie Abo"),
  ([{"anbieter": "ZDF", "typ": "abo"}], [], ["ZDF"], "ZDF gilt als kostenlos"),
  ([{"anbieter": "3sat", "typ": "abo"}], [], ["3sat"], "3sat gilt als kostenlos"),
  ([{"anbieter": "Joyn (kostenlos mit Werbung)", "typ": "abo"}], [], ["Joyn (kostenlos mit Werbung)"], "Joyn mit Zusatz kostenlos"),
  ([{"anbieter": "Joyn Plus+", "typ": "abo"}], [], [], "Joyn Plus+ kostet"),
  ([{"anbieter": "Prime Video", "typ": "abo"}, {"anbieter": "Netflix", "typ": "abo"}], ["netflix", "prime"], [], "Reihenfolge wie Abo-Liste"),
]

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        fehler = []; pg.on("pageerror", lambda x: fehler.append(str(x)))
        await pg.goto(URL); await pg.wait_for_timeout(1800)

        # ---------- Abo-Liste kommt aus personal-data.json ----------
        r = await pg.evaluate("abos().map(a=>a.id+(a.werbung?'*':''))")
        chk("Sechs Abos, Prime mit Werbung", r == ["netflix", "disney", "rtl", "apple", "sky", "prime*"], json.dumps(r))

        # ---------- Zuordnungsregeln ----------
        for daten, soll_abo, soll_gratis, name in FAELLE:
            r = await pg.evaluate("""(d)=>{const s=aboStand({kind:'film',streaming:d});
               return {a:s.abos.map(x=>x.id), g:s.gratis}}""", daten)
            chk("Regel: " + name, r["a"] == soll_abo and r["g"] == soll_gratis, json.dumps(r, ensure_ascii=False))

        r = await pg.evaluate("aboStand({kind:'film',streaming:[]})")
        chk("Ohne Daten: nicht geprueft", r["geprueft"] is False and not r["abos"], json.dumps(r))
        r = await pg.evaluate("aboStand({kind:'film',streaming:[],streaming_checked_at:'2026-11-23'})")
        chk("Leer, aber geprueft: geprueft", r["geprueft"] is True, json.dumps(r))

        # Alter Handhinweis verschwindet, sobald JustWatch-Daten da sind
        r = await pg.evaluate("""(()=>{const a=normalize({id:'x1',titel_de:'X',verfuegbarkeit_de:[],streaming_hinweis:'alt'},'film');
           const b=normalize({id:'x2',titel_de:'Y',verfuegbarkeit_de:[],streaming_hinweis:'alt',verfuegbarkeit_quelle:'JustWatch über TMDb'},'film');
           return [a.streaming_hinweis,b.streaming_hinweis]})()""")
        chk("Handhinweis nur ohne frische Daten", r == ["alt", None], json.dumps(r))

        # ---------- Bestand ----------
        r = await pg.evaluate("""(()=>{
          const fs=DATA.items.filter(i=>i.kind==='film'||i.kind==='serie');
          const mit=fs.filter(i=>aboStand(i).abos.length);
          const z={}; mit.forEach(i=>aboStand(i).abos.forEach(a=>z[a.id]=(z[a.id]||0)+1));
          return {gesamt:fs.length, mit:mit.length, je:z,
            geprueft:fs.filter(i=>aboStand(i).geprueft).length}})()""")
        chk("Bestand hat Titel in unseren Abos", r["mit"] > 50, json.dumps(r))
        print("  Bestand:", json.dumps(r))

        # ---------- Detailansicht: Netflix-Serie ----------
        sid = await pg.evaluate("""(DATA.items.find(i=>i.kind==='serie'&&aboStand(i).abos.some(a=>a.id==='netflix'))||{}).id""")
        await pg.evaluate("(id)=>openSheet(id)", sid); await pg.wait_for_timeout(400)
        z = await pg.evaluate("""(()=>{const e=document.querySelector('.sheet .detail-top .abo-zeile');
          return e?{t:e.innerText, n:e.querySelectorAll('.badge.abo').length}:null})()""")
        chk("Detailkopf zeigt 'In euren Abos' mit Netflix", z and "In euren Abos" in z["t"] and "Netflix" in z["t"], json.dumps(z, ensure_ascii=False))
        # Verfuegbarkeitsblock: eigenes Abo zuerst und markiert
        r = await pg.evaluate("""(()=>{const bs=[...document.querySelectorAll('.sheet .block')].find(b=>/verfügbar bei/i.test(b.innerText));
          if(!bs) return null; const first=bs.querySelector('.badge'); return {cls:first.className, t:first.innerText}})()""")
        chk("Verfügbarkeit: eigenes Abo steht vorn, grün markiert", r and "stream-mine" in r["cls"], json.dumps(r, ensure_ascii=False))
        await pg.evaluate("closeSheet && closeSheet()") if await pg.evaluate("typeof closeSheet==='function'") else None
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(200)

        # ---------- Detailansicht: nur Kauf ----------
        kid = await pg.evaluate("""(DATA.items.find(i=>(i.kind==='serie'||i.kind==='film')&&i.streaming.length&&!aboStand(i).abos.length&&!aboStand(i).gratis.length)||{}).id""")
        await pg.evaluate("(id)=>openSheet(id)", kid); await pg.wait_for_timeout(400)
        z = await pg.evaluate("(document.querySelector('.sheet .detail-top .abo-zeile')||{}).innerText")
        chk("Nur Kauf/Leihen: 'In keinem eurer Abos'", z and "In keinem eurer Abos" in z, str(z))
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(200)

        # ---------- Detailansicht: ohne Daten ----------
        oid = await pg.evaluate("""(DATA.items.find(i=>(i.kind==='film'||i.kind==='serie')&&!aboStand(i).geprueft)||{}).id""")
        if oid:
            await pg.evaluate("(id)=>openSheet(id)", oid); await pg.wait_for_timeout(400)
            z = await pg.evaluate("(document.querySelector('.sheet .detail-top .abo-zeile')||{}).innerText")
        else:   # nach einem vollen JustWatch-Abgleich gibt es keinen solchen Titel mehr
            z = await pg.evaluate("aboZeile({kind:'film',streaming:[]})")
        chk("Ohne Daten: 'noch nicht geprüft' statt geraten", z and "noch nicht geprüft" in z, str(z))
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(200)

        # ---------- Restaurants: keine Abo-Zeile ----------
        rid = await pg.evaluate("(DATA.items.find(i=>i.kind==='restaurant')||{}).id")
        await pg.evaluate("(id)=>openSheet(id)", rid); await pg.wait_for_timeout(400)
        z = await pg.evaluate("!!document.querySelector('.sheet .abo-zeile')")
        chk("Restaurant ohne Abo-Zeile", z is False)
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(200)

        # ---------- Filter "In unseren Abos" ----------
        for kind in ("serie", "film"):
            r = await pg.evaluate("""(k)=>{
              const opts=filterDefs(k).find(d=>d.key==='streaming');
              const alle=applyFilters(k).length;
              state.filters[k]=Object.assign({},state.filters[k]||{}, {streaming:'__abo'});
              const nur=applyFilters(k); const ok=nur.every(i=>aboStand(i).abos.length>0);
              state.filters[k].streaming='__abo_gratis';
              const mitGratis=applyFilters(k).length;
              state.filters[k].streaming='all';
              return {hatOption: !!opts && opts.options.some(o=>o.v==='__abo'), alle:alle, nur:nur.length, ok:ok, mitGratis:mitGratis}}""", kind)
            hinweis = await pg.evaluate("""(k)=>{state.filters[k]=Object.assign({},state.filters[k]||{}, {streaming:'__abo'});
              const n=streamUngeprueftCount(k); state.filters[k].streaming='all'; return [n, streamUngeprueftCount(k)]}""", kind)
            soll = await pg.evaluate("(k)=>byKind(k).filter(i=>!isArchived(i)&&!aboStand(i).geprueft).length", kind)
            chk("Filter %s: sagt, wie viele Titel ohne Daten fehlen" % kind, hinweis[0] == soll and hinweis[1] == 0, json.dumps(hinweis + [soll]))
            chk("Filter %s: Option vorhanden, nur Abo-Titel" % kind,
                r["hatOption"] and r["ok"] and 0 < r["nur"] < r["alle"] and r["mitGratis"] >= r["nur"], json.dumps(r))

        # ---------- Roulette mit Abo-Filter ----------
        await pg.evaluate("go({name:'roulette', kind:'serie'})"); await pg.wait_for_timeout(300)
        await pg.evaluate("state.filters.serie=Object.assign({},state.filters.serie||{}, {streaming:'__abo'}); render()")
        await pg.wait_for_timeout(200)
        sel = await pg.evaluate("""(()=>{const s=[...document.querySelectorAll('select')].find(x=>[...x.options].some(o=>o.value==='__abo'));
          return s?s.value:null})()""")
        chk("Roulette-Filterleiste hat 'In unseren Abos'", sel == "__abo", str(sel))
        ok_all = True
        for _ in range(5):
            await pg.evaluate("spin('serie')"); await pg.wait_for_timeout(2600)
            r = await pg.evaluate("""(()=>{const id=state.lastResult.serie; const i=DATA.byId.get(id);
              const z=document.querySelector('.abo-zeile.kompakt');
              return {abo: i?aboStand(i).abos.map(a=>a.id):[], zeile: z?z.innerText:null}})()""")
            if not r["abo"] or not r["zeile"] or "In euren Abos" not in r["zeile"]:
                ok_all = False; print("  Roulette:", r)
        chk("Roulette zieht nur Abo-Titel und zeigt das Abo am Ergebnis", ok_all)
        await pg.evaluate("state.filters.serie.streaming='all'; render()")

        # ---------- Mobil: kein seitliches Scrollen im Detail ----------
        await pg.evaluate("(id)=>openSheet(id)", sid); await pg.wait_for_timeout(400)
        r = await pg.evaluate("""(()=>{const s=document.querySelector('.sheet'); const z=document.querySelector('.sheet .abo-zeile').getBoundingClientRect();
           return {sw:s.scrollWidth, cw:s.clientWidth, rechts:z.right, vw:innerWidth}})()""")
        chk("Mobil: Abo-Zeile passt in die Breite", r["sw"] <= r["cw"] + 1 and r["rechts"] <= r["vw"], json.dumps(r))
        await pg.screenshot(path=os.path.join(SCR, "abos-hell.png"))

        # ---------- Dunkel: Kontrast der gruenen Plakette ----------
        await pg.evaluate("document.documentElement.setAttribute('data-theme','dark')"); await pg.wait_for_timeout(200)
        r = await pg.evaluate("""(()=>{
          const e=document.querySelector('.sheet .badge.abo'); const cs=getComputedStyle(e);
          const rgb=(c)=>c.match(/[\\d.]+/g).slice(0,3).map(Number);
          const lum=(c)=>{const v=rgb(c).map(x=>{x/=255;return x<=.03928?x/12.92:Math.pow((x+.055)/1.055,2.4)});return .2126*v[0]+.7152*v[1]+.0722*v[2]};
          let el=e, bg='rgba(0, 0, 0, 0)';
          while(el){const b=getComputedStyle(el).backgroundColor; if(b && !/rgba\\(0, 0, 0, 0\\)/.test(b) && !/, 0\\.1/.test(b) ){bg=b;break;} el=el.parentElement;}
          const L1=lum(cs.color), L2=lum(bg); const k=(Math.max(L1,L2)+.05)/(Math.min(L1,L2)+.05);
          return {farbe:cs.color, grund:bg, kontrast:Math.round(k*10)/10}})()""")
        chk("Dunkel: Abo-Plakette lesbar (Kontrast >= 4.5)", r["kontrast"] >= 4.5, json.dumps(r))
        await pg.screenshot(path=os.path.join(SCR, "abos-dunkel.png"))

        chk("Keine Skriptfehler", not fehler, "; ".join(fehler[:3]))
        await b.close()

asyncio.run(main())
ok = sum(1 for r in res if r[1])
for n, g, e in res:
    print(("  OK  " if g else "  FEHL") + "  " + n + ("" if g else "   " + e))
print("\n%d von %d bestanden" % (ok, len(res)))
