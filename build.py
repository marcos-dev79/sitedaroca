#!/usr/bin/env python3
"""Build do site estático para publicação."""

import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
DATA_SRC = ROOT / "data" / "cidadezinhas.json"
CRIME_SRC = ROOT / "data" / "zonas-crime.json"
ASSETS = ROOT / "assets"

SITE_NAME = "Dev Remoto na Roça"
SITE_DESC = (
    "Cidadezinhas do interior com dados do IBGE, Atlas IDH e SIM/DATASUS."
)
SITE_URL = "https://marcos-dev79.github.io/sitedaroca"


def load_cities():
    with open(DATA_SRC, encoding="utf-8") as f:
        return json.load(f)


def load_crime() -> list:
    if not CRIME_SRC.exists():
        return []
    with open(CRIME_SRC, encoding="utf-8") as f:
        payload = json.load(f)
    return payload.get("zonas_crime") or []


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def nav() -> str:
    return """<nav class="site-nav">
  <a class="brand" href="index.html">🌾 <span>Dev Remoto</span> na Roça</a>
</nav>"""


def head(title: str, desc: str = SITE_DESC, page: str = "index", css_href: str = "assets/css/site.css") -> str:
    url = f"{SITE_URL}/{page}.html" if SITE_URL else ""
    og = f'<meta property="og:url" content="{url}">' if url else ""
    return f"""<meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
  <meta name="description" content="{desc}">
  <meta name="theme-color" content="#0f172a">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  {og}
  <meta property="og:locale" content="pt_BR">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{desc}">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🌾</text></svg>">
  <link rel="stylesheet" href="{css_href}">"""


def cities_script(cities: list) -> str:
    payload = json.dumps(cities, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e")
    return f"<script>window.CIDADEZINHAS={payload};</script>"


def crime_script(zones: list) -> str:
    payload = json.dumps(zones, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e")
    return f"<script>window.ZONAS_CRIME={payload};</script>"


def footer(total: int) -> str:
    return f"""<footer class="site-footer">
  <p>{SITE_NAME} · Dados: IBGE 2024, Atlas IDH 2010 · Mapa interativo com {total} municípios</p>
</footer>"""


def build_index(stats: dict, cities: list, crime_zones: list, css_href: str, js_href: str) -> str:
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  {head(SITE_NAME, page="index", css_href=css_href)}
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin="">
</head>
<body>
  {nav()}

  <header class="map-header">
    <h1>Top {stats["total"]} Cidadezinhas para Dev Remoto na Roça</h1>
    <p>Até 20 mil hab., 20–50 km de cidade média (≥150 mil), até 1h30 de cidade grande (≥500 mil). UPA/emergência no conjunto. Homicídios ≤ 15/100 mil. Ordenado por IDH. Marque um serviço para exigir que a cidade o tenha.</p>
    <div class="map-stats">
      <span class="stat">Total: {stats["total"]}</span>
      <span class="stat">Visíveis: <span id="visible-count">{stats["total"]}</span></span>
      <span class="stat">Sul/Sudeste: {stats["ss"]}</span>
      <span class="stat">CO: {stats["co"]}</span>
      <span class="stat">NE: {stats["ne"]}</span>
      <span class="stat">N: {stats["n"]}</span>
    </div>
    <p class="map-disclaimer">Isto não é um conselho profissional. Faça sua própria pesquisa.</p>
  </header>

  <div class="map-wrap">
    <div id="map-loading" class="map-loading">Carregando mapa…</div>
    <div id="map"></div>
    <div class="map-controls" id="map-controls">
      <span class="filter-peek">Filtros</span>
      <div class="map-controls-body">
        <input type="search" id="search" placeholder="Buscar cidade, UF ou região…" aria-label="Buscar cidade">
        <div class="filter-chips">
          <button class="chip active" data-regiao="all" type="button">Todas</button>
          <button class="chip" data-regiao="Sudeste" type="button">Sudeste</button>
          <button class="chip" data-regiao="Sul" type="button">Sul</button>
          <button class="chip" data-regiao="Centro-Oeste" type="button">Centro-Oeste</button>
          <button class="chip" data-regiao="Nordeste" type="button">Nordeste</button>
          <button class="chip" data-regiao="Norte" type="button">Norte</button>
        </div>
        <div class="filter-chips" role="group" aria-label="Altitude">
          <button class="chip active" data-alt="0" type="button">0 m</button>
          <button class="chip" data-alt="300" type="button">&gt; 300 m</button>
          <button class="chip" data-alt="500" type="button">&gt; 500 m</button>
          <button class="chip" data-alt="1000" type="button">&gt; 1000 m</button>
        </div>
        <div class="infra-filters" role="group" aria-label="Serviços no município">
          <label><input type="checkbox" data-infra="upa_ou_emergencia_24h" checked> UPA / emergência</label>
          <label><input type="checkbox" data-infra="escola"> Escola</label>
          <label><input type="checkbox" data-infra="mercado"> Mercado</label>
          <label><input type="checkbox" data-infra="farmacia"> Farmácia</label>
          <label><input type="checkbox" data-infra="delegacia"> Delegacia</label>
          <label><input type="checkbox" data-infra="correios"> Correios</label>
        </div>
        <button class="chip chip-crime" id="toggle-crime" type="button" aria-pressed="false">Zonas de Crime</button>
      </div>
    </div>
    <div class="map-legend">
      <div><span style="background:#16a34a"></span>Sudeste</div>
      <div><span style="background:#2563eb"></span>Sul</div>
      <div><span style="background:#ca8a04"></span>Centro-Oeste</div>
      <div><span style="background:#dc2626"></span>Nordeste</div>
      <div><span style="background:#9333ea"></span>Norte</div>
      <div class="legend-crime"><span class="legend-burst"></span>Zonas de crime</div>
    </div>
  </div>

  {footer(stats["total"])}
  <script>
    if ("serviceWorker" in navigator) {{
      navigator.serviceWorker.getRegistrations().then(function (rs) {{
        rs.forEach(function (r) {{ r.unregister(); }});
      }});
    }}
  </script>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
  __CITIES_SCRIPT__
  __CRIME_SCRIPT__
  <script src="{js_href}"></script>
</body>
</html>"""
    return (
        html.replace("__CITIES_SCRIPT__", cities_script(cities)).replace(
            "__CRIME_SCRIPT__", crime_script(crime_zones)
        )
    )


def build_404(total: int, css_href: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  {head("Página não encontrada — " + SITE_NAME, css_href=css_href)}
</head>
<body>
  {nav()}
  <div class="error-page">
    <h1>404</h1>
    <p>Esta página não existe.</p>
    <a href="index.html" class="btn btn-primary">Voltar ao início</a>
  </div>
  {footer(total)}
</body>
</html>"""


def stats_from(cities: list) -> dict:
    reg = Counter(c["regiao"] for c in cities)
    ss = reg["Sul"] + reg["Sudeste"]
    return {
        "total": len(cities),
        "ss": ss,
        "sudeste": reg["Sudeste"],
        "sul": reg["Sul"],
        "co": reg["Centro-Oeste"],
        "ne": reg["Nordeste"],
        "n": reg["Norte"],
    }


def main():
    payload = load_cities()
    cities = payload["cidadezinhas"]
    crime_zones = load_crime()
    stats = stats_from(cities)

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    (DIST / "assets" / "css").mkdir(parents=True)
    (DIST / "assets" / "js").mkdir(parents=True)
    (DIST / "data").mkdir()

    css_hash = file_hash(ASSETS / "css" / "site.css")
    js_hash = file_hash(ASSETS / "js" / "mapa.js")
    css_name = f"site.{css_hash}.css"
    js_name = f"mapa.{js_hash}.js"
    css_href = f"assets/css/{css_name}"
    js_href = f"assets/js/{js_name}"
    shutil.copy2(ASSETS / "css" / "site.css", DIST / "assets" / "css" / css_name)
    shutil.copy2(ASSETS / "js" / "mapa.js", DIST / "assets" / "js" / js_name)
    img_sp = ASSETS / "img" / "cidades-sp-100.png"
    if img_sp.exists():
        (DIST / "assets" / "img").mkdir(parents=True, exist_ok=True)
        shutil.copy2(img_sp, DIST / "assets" / "img" / "cidades-sp-100.png")
    shutil.copy2(DATA_SRC, DIST / "data" / "cidadezinhas.json")
    if CRIME_SRC.exists():
        shutil.copy2(CRIME_SRC, DIST / "data" / "zonas-crime.json")

    (DIST / "index.html").write_text(
        build_index(stats, cities, crime_zones, css_href, js_href), encoding="utf-8"
    )
    (DIST / "404.html").write_text(build_404(stats["total"], css_href), encoding="utf-8")
    (DIST / ".nojekyll").touch()
    (DIST / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")

    print(f"Site gerado em: {DIST}")
    print(f"  index.html, 404.html")
    print(f"  {stats['total']} cidades | SS={stats['ss']} CO={stats['co']} NE={stats['ne']} N={stats['n']}")
    print("\nPublicar: faça upload da pasta dist/ ou configure GitHub Pages / Netlify apontando para dist/")


if __name__ == "__main__":
    main()
