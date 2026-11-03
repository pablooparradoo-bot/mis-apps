#!/usr/bin/env python3
"""Actualiza coplas/catalogo.json a partir del listado público de Acordes Gaditanos.

Guarda solo datos de catálogo: título, año, tipo, agrupación, modalidad, autores y
enlace. Nunca guarda letras ni acordes. Pide una página cada PAUSA segundos, respeta
robots.txt y se detiene si la web responde con un límite o un bloqueo.
"""
import datetime, html.parser, json, os, re, sys, time, unicodedata, urllib.error, urllib.parse, urllib.request, urllib.robotparser

BASE = "https://acordesgaditanos.com"
UA = "catalogo-coplas/1.0 (app personal; github.com/pablooparradoo-bot/mis-apps)"
RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "catalogo.json")
PAUSA = 2.0
MAX_FICHAS = 300  # fichas por ejecución; lo que falte se completa al día siguiente
NOVEDADES = 30

TIPOS = [
    (r"final de popurr?[ií]", "Final de popurrí"), (r"popurr[ií]", "Popurrí"), (r"cuarteta", "Cuarteta"),
    (r"presentaci[oó]n", "Presentación"), (r"pasodoble", "Pasodoble"), (r"tango", "Tango"),
    (r"estribillo", "Estribillo"), (r"testamento", "Testamento"), (r"credo", "Credo"),
]


def analizar_titulo(t):
    """Devuelve (tipo, letra, agrupación) a partir del título del listado."""
    tipo, resto = "Otra", t.strip()
    for patron, nombre in TIPOS:
        m = re.match(patron + r"\b\s*", resto, re.I)
        if m:
            tipo, resto = nombre, resto[m.end():]
            break
    letra = ""
    q = re.search(r'"([^"]+)"', resto)
    if q:
        fuera = (resto[:q.start()] + " " + resto[q.end():]).strip(" :")
        if fuera and resto.startswith('"'):
            letra, resto = q.group(1), fuera
        else:  # To me pasa a mi: "Los desgraciaitos"
            resto = f"{resto[:q.start()].strip(' :')} ({q.group(1)})"
    resto = re.sub(r"^(original|in[eé]dito)\s+", "", resto, flags=re.I)
    resto = re.sub(r"^de el\s+", "El ", resto, flags=re.I)
    return tipo, letra, resto.strip()


class Listado(html.parser.HTMLParser):
    """Recoge los enlaces a coplas agrupados bajo los títulos h2 de cada año."""
    def __init__(self):
        super().__init__()
        self.anio = None; self.en_h2 = False; self.txt = ""; self.href = None; self.a = ""; self.items = []

    def handle_starttag(self, tag, attrs):
        if tag == "h2":
            self.en_h2, self.txt = True, ""
        elif tag == "a" and self.anio:
            m = re.search(r"/acordes/([^/?#\"]+)/?$", dict(attrs).get("href") or "")
            if m:
                self.href, self.a = m.group(1), ""

    def handle_data(self, d):
        if self.en_h2:
            self.txt += d
        if self.href:
            self.a += d

    def handle_endtag(self, tag):
        if tag == "h2":
            self.en_h2 = False
            m = re.match(r"\s*(\d{4})\b", self.txt)
            self.anio = int(m.group(1)) if m else None
        elif tag == "a" and self.href:
            self.items.append({"s": self.href, "t": re.sub(r"\s+", " ", self.a).strip(), "y": self.anio})
            self.href = None


def analizar_ficha(h):
    """Extrae de la página de una copla solo agrupación, modalidad y autores."""
    from html import unescape
    def enlaces(ruta):
        vistos = []
        for nombre in re.findall(r'href="[^"]*/%s/[^"/]+/?"[^>]*>\s*([^<]+?)\s*</a>' % ruta, h):
            nombre = unescape(nombre)
            if nombre not in vistos:
                vistos.append(nombre)
        return vistos
    grupos = enlaces("agrupacion")
    m = re.search(r'alt="[^"]*-\s*(Comparsa|Chirigota|Coro|Cuarteto)\b[^"]*"', h)
    return {"a": grupos[-1] if grupos else None, "m": m.group(1) if m else "",
            "le": enlaces("autor/letra"), "mu": enlaces("autor/musica")}


class Parada(Exception):
    pass


def pedir(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        if e.code in (401, 403, 429, 503):
            raise Parada(f"la web responde {e.code} en {url}")
        raise


def fusionar(actual, listado, hoy):
    previas = {c["s"]: c for c in actual.get("coplas", [])}
    coplas, nuevas = [], []
    for it in listado:
        c = previas.get(it["s"], {})
        tipo, letra, grupo = analizar_titulo(it["t"])
        fila = {"s": it["s"], "t": it["t"], "y": it["y"], "k": tipo, "n": letra,
                "a": c.get("a") if c.get("f") else grupo, "m": c.get("m", ""),
                "le": c.get("le", []), "mu": c.get("mu", [])}
        if c.get("f"):
            fila["f"] = 1
        if it["s"] not in previas:
            nuevas.append(it["s"])
        coplas.append(fila)
    vivas = {c["s"] for c in coplas}
    nov = nuevas + [s for s in actual.get("novedades", []) if s in vivas and s not in nuevas]
    return {"actualizado": actual.get("actualizado", hoy), "coplas": coplas, "novedades": nov[:NOVEDADES]}, nuevas


def main():
    hoy = datetime.date.today().isoformat()
    with open(RUTA, encoding="utf-8") as f:
        actual = json.load(f)
    robots = urllib.robotparser.RobotFileParser()
    try:
        robots.parse(pedir(BASE + "/robots.txt").splitlines())
    except (Parada, urllib.error.URLError) as e:
        print(f"Sin robots.txt legible ({e}); sigo solo con el listado.")
    if not robots.can_fetch(UA, BASE + "/lista/"):
        print("robots.txt no permite leer el listado. No hago nada."); return 0

    p = Listado(); p.feed(pedir(BASE + "/lista/"))
    previas = len(actual.get("coplas", []))
    if len(p.items) < max(50, previas * 0.9):
        print(f"Listado sospechoso: {len(p.items)} coplas frente a {previas}. No toco el catálogo."); return 1
    datos, nuevas = fusionar(actual, p.items, hoy)
    print(f"Listado: {len(p.items)} coplas, {len(nuevas)} nuevas.")

    pendientes = [c for c in datos["coplas"] if not c.get("f")][:MAX_FICHAS]
    hechas = 0
    try:
        for c in pendientes:
            url = f"{BASE}/acordes/{c['s']}/"
            if not robots.can_fetch(UA, url):
                print("robots.txt no permite leer las fichas."); break
            time.sleep(PAUSA)
            try:
                fic = analizar_ficha(pedir(url))
            except urllib.error.URLError as e:
                print(f"Salto {c['s']}: {e}"); continue
            if fic["a"]:
                c["a"] = fic["a"]
            c.update(m=fic["m"], le=fic["le"], mu=fic["mu"], f=1)
            hechas += 1
    except Parada as e:
        print(f"Paro por prudencia: {e}")
    print(f"Fichas completadas: {hechas}. Pendientes: {sum(not c.get('f') for c in datos['coplas'])}.")

    def sin_fecha(d):
        return {k: v for k, v in d.items() if k != "actualizado"}
    if sin_fecha(datos) != sin_fecha(actual):
        datos["actualizado"] = hoy
        with open(RUTA, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, separators=(",", ":"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
