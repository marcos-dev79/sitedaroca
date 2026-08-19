# Dev Remoto na Roça

Mapa interativo com cidadezinhas brasileiras para quem trabalha remoto e quer morar no interior. O conjunto atual tem **113 municípios** (47 com serviços completos visíveis por padrão), ordenados por IDH.

Site: [https://marcos-dev79.github.io/sitedaroca/](https://marcos-dev79.github.io/sitedaroca/)

Site: [https://marcos-dev79.github.io/sitedaroca/](https://marcos-dev79.github.io/sitedaroca/)

Isto **não é um conselho profissional**. Faça sua própria pesquisa e valide no local.

## Critérios

- Até 20 mil habitantes (IBGE 2024)
- Entre 30 e 50 km de uma cidade média (≥150 mil hab.)
- Até 1h30 de uma cidade grande (≥500 mil hab.)
- UPA (CNES) ou emergência 24h municipal (IBGE MUNIC 2021) e escola (MUNIC 2021)
- Farmácia, delegacia, mercado e Correios: no JSON; `hidden` se faltar algum (aparecem com o filtro desmarcado; por padrão só UPA está exigido)
- Taxa de homicídios ≤ 15 por 100 mil habitantes (SIM/DATASUS)
- Ranking por IDH municipal (Atlas 2010)

Não há cota por região; os filtros do mapa por região permanecem.

Distribuição atual: **86** Sul/Sudeste · **9** Centro-Oeste · **17** Nordeste · **1** Norte.

## Estrutura

```
ROCA/
├── assets/                  # CSS, JS e imagens fonte
├── data/
│   └── cidadezinhas.json    # municípios do mapa (gerado)
├── dist/                    # Site gerado (não versionar)
├── build.py                 # Gera dist/ para publicação
├── rebuild_cidadezinhas.py  # Recalcula o JSON com IBGE/CNES/SIM
└── .github/workflows/deploy.yml
```

## Build local

```bash
python3 build.py
cd dist && python3 -m http.server 8080
```

Abra [http://localhost:8080](http://localhost:8080).

O mapa carrega `data/cidadezinhas.json` via fetch — precisa de servidor HTTP (não abra o HTML direto do disco).

## Publicação

A pasta **`dist/`** é o artefato final. O GitHub Actions gera ela no CI.

### GitHub Pages

O workflow `.github/workflows/deploy.yml` já está configurado:

1. Push em `main` (ou `master`)
2. Em **Settings → Pages**, source = **GitHub Actions**

O build roda `python3 build.py` e publica `dist/`.

Se a URL do site mudar, edite `SITE_URL` em `build.py`.

### Netlify

- **Build command:** `python3 build.py`
- **Publish directory:** `dist`

### Cloudflare Pages

- **Build command:** `python3 build.py`
- **Output directory:** `dist`

## Editar conteúdo

- **Cidades do mapa:** `data/cidadezinhas.json`, depois `python3 build.py`
- **Layout do mapa:** `build.py` (`build_index()`)
- **Estilo:** `assets/css/site.css`
- **Mapa (Leaflet, filtros, popup):** `assets/js/mapa.js`

Scripts opcionais (não rodam no CI):

```bash
python3 rebuild_cidadezinhas.py   # atualiza data/cidadezinhas.json (precisa das bases em data/cache/)
python3 build.py
python3 gerar-imagem-sp.py        # PNG estático com cidades de SP (opcional)
```

## Licença

Conteúdo e dados compilados para uso informativo. População, UPA, IDH e infraestrutura mudam — valide sempre no local antes de decidir.
