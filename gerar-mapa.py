#!/usr/bin/env python3
"""Gera mapa interativo HTML das cidadezinhas para dev remoto na roça."""

import json
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "cidadezinhas.json"
OUT = ROOT / "_source_mapa.html"

REGIAO_CORES = {
    "Sul": "#2563eb",
    "Sudeste": "#16a34a",
    "Centro-Oeste": "#ca8a04",
    "Nordeste": "#dc2626",
    "Norte": "#9333ea",
}

REGIAO_SUL_SUDESTE = {"Sul", "Sudeste"}


def main():
    with open(DATA, encoding="utf-8") as f:
        payload = json.load(f)

    cities = payload["cidadezinhas"]
    n = len(cities)
    ss = sum(1 for c in cities if c["regiao"] in REGIAO_SUL_SUDESTE)
    outros = n - ss
    co = sum(1 for c in cities if c["regiao"] == "Centro-Oeste")
    ne = sum(1 for c in cities if c["regiao"] == "Nordeste")
    no = sum(1 for c in cities if c["regiao"] == "Norte")

    markers_js = []
    for c in cities:
        cor = REGIAO_CORES.get(c["regiao"], "#64748b")
        grupo = "Sul / Sudeste" if c["regiao"] in REGIAO_SUL_SUDESTE else "Demais regiões"
        popup = (
            f"<b>#{c['rank']} — {c['nome']}/{c['uf']}</b><br>"
            f"Pop.: ~{c['pop']:,} hab. | {c['regiao']}<br>"
            f"Cidade média: {c['cidade_media']}<br>"
            f"Grande centro: {c['grande_centro']}<br>"
            f"<em>{c['nota']}</em>"
        ).replace("'", "\\'")
        markers_js.append(
            f"  L.circleMarker([{c['lat']}, {c['lng']}], {{"
            f"radius: 7, fillColor: '{cor}', color: '#fff', weight: 1.5, fillOpacity: 0.85"
            f"}}).bindPopup('{popup}').addTo(map);"
        )

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Top {n} Cidadezinhas — Dev Remoto na Roça</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: system-ui, -apple-system, sans-serif; background: #0f172a; color: #e2e8f0; }}
    header {{
      padding: 1.25rem 1.5rem;
      background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
      border-bottom: 1px solid #334155;
    }}
    header h1 {{ font-size: 1.35rem; font-weight: 700; margin-bottom: 0.35rem; }}
    header p {{ font-size: 0.9rem; color: #94a3b8; max-width: 720px; line-height: 1.5; }}
    .stats {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-top: 0.75rem; font-size: 0.85rem; }}
    .stat {{ background: #1e293b; padding: 0.35rem 0.75rem; border-radius: 6px; border: 1px solid #334155; }}
    #map {{ height: calc(100vh - 140px); min-height: 480px; }}
    .legend {{
      position: absolute; bottom: 24px; right: 12px; z-index: 1000;
      background: rgba(15,23,42,0.92); padding: 12px 14px; border-radius: 8px;
      border: 1px solid #334155; font-size: 0.8rem; line-height: 1.8;
    }}
    .legend span {{ display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }}
  </style>
</head>
<body>
  <header>
    <h1>🌾 Top {n} Cidadezinhas para Dev Remoto na Roça</h1>
    <p>Municípios de até ~15 mil hab., com infraestrutura básica, proximidade de cidade média e grande centro, e perfil para chácara afastada 3–7 km.</p>
    <div class="stats">
      <span class="stat">Total: {n} cidades</span>
      <span class="stat">Sul / Sudeste: {ss}</span>
      <span class="stat">Centro-Oeste: {co}</span>
      <span class="stat">Nordeste: {ne}</span>
      <span class="stat">Norte: {no}</span>
    </div>
  </header>
  <div id="map"></div>
  <div class="legend">
    <div><span style="background:#16a34a"></span>Sudeste</div>
    <div><span style="background:#2563eb"></span>Sul</div>
    <div><span style="background:#ca8a04"></span>Centro-Oeste</div>
    <div><span style="background:#dc2626"></span>Nordeste</div>
    <div><span style="background:#9333ea"></span>Norte</div>
  </div>
  <script>
    const map = L.map('map', {{ center: [-15.5, -52.0], zoom: 4, minZoom: 3 }});
    L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
      attribution: '&copy; OpenStreetMap &copy; CARTO',
      subdomains: 'abcd', maxZoom: 19
    }}).addTo(map);

{chr(10).join(markers_js)}
  </script>
</body>
</html>
"""
    OUT.write_text(html, encoding="utf-8")
    print(f"Mapa gerado: {OUT}")
    print(f"Total={n} | Sul/Sudeste={ss} | CO={co} | NE={ne} | Norte={no}")


if __name__ == "__main__":
    main()
