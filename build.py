#!/usr/bin/env python3
"""Build do site estático para publicação."""

import json
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
DATA_SRC = ROOT / "data" / "cidadezinhas.json"
ASSETS = ROOT / "assets"

SITE_NAME = "Dev Remoto na Roça"
SITE_DESC = (
    "Estratégia para devs remotos morarem no interior: 150 cidadezinhas "
    "com infraestrutura básica, segurança e proximidade de centros urbanos."
)
SITE_URL = ""  # preencher após deploy, ex: https://seuusuario.github.io/roca-remoto


def load_cities():
    with open(DATA_SRC, encoding="utf-8") as f:
        return json.load(f)


def nav() -> str:
    return """<nav class="site-nav">
  <a class="brand" href="index.html">🌾 <span>Dev Remoto</span> na Roça</a>
</nav>"""


def head(title: str, desc: str = SITE_DESC, page: str = "index") -> str:
    url = f"{SITE_URL}/{page}.html" if SITE_URL else ""
    og = f'<meta property="og:url" content="{url}">' if url else ""
    return f"""<meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
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
  <link rel="stylesheet" href="assets/css/site.css">"""


def footer() -> str:
    return f"""<footer class="site-footer">
  <p>{SITE_NAME} · Dados: IBGE 2024, IPS Brasil · Mapa interativo com 150 municípios</p>
</footer>"""


def build_index(stats: dict) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  {head(SITE_NAME, page="index")}
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin="">
</head>
<body>
  {nav()}

  <header class="map-header">
    <h1>Top {stats["total"]} Cidadezinhas para Dev Remoto na Roça</h1>
    <p>Municípios de até ~15 mil hab., com infraestrutura básica, proximidade de cidade média e grande centro, e perfil para chácara afastada 3–7 km.</p>
    <div class="map-controls">
      <input type="search" id="search" placeholder="Buscar cidade, UF ou região…" aria-label="Buscar cidade">
      <div class="filter-chips">
        <button class="chip active" data-regiao="all" type="button">Todas</button>
        <button class="chip" data-regiao="Sudeste" type="button">Sudeste</button>
        <button class="chip" data-regiao="Sul" type="button">Sul</button>
        <button class="chip" data-regiao="Centro-Oeste" type="button">Centro-Oeste</button>
        <button class="chip" data-regiao="Nordeste" type="button">Nordeste</button>
        <button class="chip" data-regiao="Norte" type="button">Norte</button>
      </div>
    </div>
    <div class="map-stats">
      <span class="stat">Total: {stats["total"]}</span>
      <span class="stat">Visíveis: <span id="visible-count">{stats["total"]}</span></span>
      <span class="stat">Sul/Sudeste: {stats["ss"]}</span>
      <span class="stat">CO: {stats["co"]}</span>
      <span class="stat">NE: {stats["ne"]}</span>
      <span class="stat">N: {stats["n"]}</span>
    </div>
  </header>

  <div class="map-wrap">
    <div id="map-loading" class="map-loading">Carregando mapa…</div>
    <div id="map"></div>
    <div class="map-legend">
      <div><span style="background:#16a34a"></span>Sudeste</div>
      <div><span style="background:#2563eb"></span>Sul</div>
      <div><span style="background:#ca8a04"></span>Centro-Oeste</div>
      <div><span style="background:#dc2626"></span>Nordeste</div>
      <div><span style="background:#9333ea"></span>Norte</div>
    </div>
  </div>

  {footer()}
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
  <script src="assets/js/mapa.js"></script>
</body>
</html>"""


def build_404() -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  {head("Página não encontrada — " + SITE_NAME)}
</head>
<body>
  {nav()}
  <div class="error-page">
    <h1>404</h1>
    <p>Esta página não existe.</p>
    <a href="index.html" class="btn btn-primary">Voltar ao início</a>
  </div>
  {footer()}
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
    stats = stats_from(cities)

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    (DIST / "assets" / "css").mkdir(parents=True)
    (DIST / "assets" / "js").mkdir(parents=True)
    (DIST / "data").mkdir()

    shutil.copy2(ASSETS / "css" / "site.css", DIST / "assets" / "css" / "site.css")
    shutil.copy2(ASSETS / "js" / "mapa.js", DIST / "assets" / "js" / "mapa.js")
    img_sp = ASSETS / "img" / "cidades-sp-100.png"
    if img_sp.exists():
        (DIST / "assets" / "img").mkdir(parents=True, exist_ok=True)
        shutil.copy2(img_sp, DIST / "assets" / "img" / "cidades-sp-100.png")
    shutil.copy2(DATA_SRC, DIST / "data" / "cidadezinhas.json")

    (DIST / "index.html").write_text(build_index(stats), encoding="utf-8")
    (DIST / "404.html").write_text(build_404(), encoding="utf-8")
    (DIST / ".nojekyll").touch()
    (DIST / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")

    print(f"Site gerado em: {DIST}")
    print(f"  index.html, 404.html")
    print(f"  {stats['total']} cidades | SS={stats['ss']} CO={stats['co']} NE={stats['ne']} N={stats['n']}")
    print("\nPublicar: faça upload da pasta dist/ ou configure GitHub Pages / Netlify apontando para dist/")


if __name__ == "__main__":
    main()
