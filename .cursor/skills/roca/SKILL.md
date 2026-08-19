---
name: roca
description: >-
  Dev Remoto na Roça (ROCA): static map of small Brazilian towns for remote
  workers. Use when editing this repo, cidadezinhas.json, rebuild_cidadezinhas.py,
  build.py, mapa.js, map filters, IBGE/CNES/SIM pipeline, GitHub Pages deploy,
  or sitedaroca.
---

# ROCA — Dev Remoto na Roça

Site estático: mapa Leaflet de municípios pequenos. Repo GitHub `marcos-dev79/sitedaroca`. Live: `https://marcos-dev79.github.io/sitedaroca/`. `SITE_URL` em `build.py` (sem barra no final).

Isto **não é conselho profissional**. Manter o aviso no header do mapa.

Não colocar PII no site (nome civil, e-mail). Autor Git ≠ conteúdo público.

## Stack e arquivos

| Peça | Função |
|------|--------|
| `rebuild_cidadezinhas.py` | Recalcula `data/cidadezinhas.json` |
| `build.py` | Gera `dist/` (HTML + assets com hash + JSON embutido) |
| `assets/js/mapa.js` | Mapa, filtros, popup |
| `assets/css/site.css` | Estilo |
| `data/cidadezinhas.json` | Dataset do mapa |
| `data/ibge-pop-2024.json` | População IBGE 2024 |
| `data/dados2010-ref.csv` | IDH, lat/lng, altitude (Atlas 2010) |
| `data/cache/` | MUNIC/CNES/SIM — **não versionar** |
| `dist/` | Artefato — **não versionar** |

Legado (não usar para o dataset atual): `expandir-cidadezinhas.py`, `enriquecer-originais.py`.

CI: `.github/workflows/deploy.yml` → `python3 build.py` → publica `dist/`. Pages = GitHub Actions.

## Workflow

1. Critério ou dado muda → editar constantes em `rebuild_cidadezinhas.py` (e copy em `build.py` / README se o usuário vir o texto).
2. `python3 rebuild_cidadezinhas.py` (precisa de `data/cache/`).
3. `python3 build.py`.
4. Local: `cd dist && python3 -m http.server 8080`.
5. Commit/push só se o usuário pedir. Não commitar `data/cache/`, `dist/`, zip CNES.

Após mudar CSS/JS, o hash no nome do arquivo no `dist/` muda sozinho (`site.<hash>.css`, `mapa.<hash>.js`). Cidades vão em `window.CIDADEZINHAS` no HTML.

## Critérios de inclusão (JSON)

Constantes atuais:

- pop ≤ **20_000** (IBGE 2024 SIDRA 6579)
- **20–50 km** de cidade média (pop ≥ **150_000**), Haversine
- até **1h30** de cidade grande (pop ≥ **500_000**) = **120 km** a 80 km/h (não é rota real)
- UPA CNES tipo **73** **ou** emergência 24h MUNIC 2021 `Msau451`
- escola MUNIC 2021 `Medu01` (não começa com “Não”)
- homicídios ≤ **15 / 100 mil** (SIM 2022–2024). Sem série no SIM → **não** descarta
- cap 1000 candidatas geo; hoje o pool geo é menor
- **sem cota por região**; chips de região só no mapa
- ordenar por IDH desc, depois pop, nome; `rank` = essa ordem

Não excluir por farmácia, delegacia, mercado ou Correios. Se faltar algum dos 6 flags de `infra` → `"hidden": true`.

**Mercado / Correios:** proxy (pop ≥ 2000 + farmácia CNES). Sem cadastro nacional aberto. Texto pede validar no local.

## Fontes

- IBGE pop 2024; MUNIC 2021 saúde/educação, 2023 segurança (`MSEG161` = delegacia)
- Atlas 2010: IDH, coords, **altitude da sede** (`alt` no CSV → `altitude` int metros)
- SIM/DATASUS homicídios X85–Y09 (`data/cache/homicidios.csv`)
- CNES: `data/cache/cnes_flags.json` (tipo 73 UPA, 43 farmácia; só ativos)

## JSON

`meta` + `cidadezinhas[]`. Campos úteis: `rank`, `nome`, `uf`, `regiao`, `pop`, `idh` (+ dimensões), `ibge`, `lat`, `lng`, `altitude`, `cidade_media`, `grande_centro`, `homicidios`, `homicidios_ano`, `taxa_homicidios_100k`, `saude`, `educacao`, `seguranca`, `infra{}`, `hidden`, `nota`.

`infra` keys: `upa_ou_emergencia_24h`, `escola`, `mercado`, `farmacia`, `delegacia`, `correios`.

`cidade_media`: `"Nome (N km)"`. `grande_centro`: `"Nome (~XhYY, N km)"`.

## Mapa (UI)

Barra overlay em `#map-controls`: recolhe em `dragstart`/`zoomstart`; abre em hover/focus/tap no selo “Filtros”. Não recolher se o foco está na barra.

Filtros:

- região: chips `data-regiao` (padrão `all`)
- altitude: chips `data-alt` = `0` \| `300` \| `500` \| `1000`. Padrão `0` (todas). Demais = `altitude > N`
- serviços: checkboxes `data-infra`. **Padrão: só UPA checked.** Marcado = exige o flag true

Popup: `Nome/UF (IDH)` · altitude · cidade média · cidade grande · Saúde / Educação / Segurança.

Hidden visível (quando o filtro permite): `fillOpacity` 0.45.

Copy do header: critérios + “marque um serviço para exigir”.

## Regras de produto

- Site em PT-BR. Mapa é a home (sem artigo no build atual).
- Não inventar comércio/Correios como fato.
- Não afrouxar homicídio/UPA/escola sem o usuário pedir.
- Atualizar README quando totais, critérios ou filtros mudarem.
- Dataset muda → sempre `rebuild` + `build.py` para o embed e o hash baterem.
