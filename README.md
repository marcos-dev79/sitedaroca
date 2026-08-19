# Dev Remoto na Roça

Mapa interativo com cidadezinhas brasileiras para quem trabalha remoto e quer morar no interior. O conjunto atual tem **113 municípios**, ordenados por IDH (Atlas 2010). **47** têm o pacote completo de serviços no JSON; as demais entram com `"hidden": true` e aparecem no mapa conforme os checkboxes.

Site: [https://marcos-dev79.github.io/sitedaroca/](https://marcos-dev79.github.io/sitedaroca/)

Isto **não é um conselho profissional**. Faça sua própria pesquisa e valide no local.

## Critérios (inclusão no JSON)

- Até 20 mil habitantes (IBGE 2024, SIDRA 6579)
- Entre 30 e 50 km de uma cidade média (≥150 mil hab.)
- Até ~1h30 de uma cidade grande (≥500 mil hab.; ~120 km em linha reta a 80 km/h, não é Google Maps)
- UPA no CNES (tipo 73) **ou** emergência 24h municipal (IBGE MUNIC 2021)
- Escola / estrutura educacional municipal (MUNIC 2021)
- Taxa de homicídios ≤ 15 por 100 mil (SIM/DATASUS 2022–2024). Município sem série no SIM **não** é descartado por violência
- Ranking por IDH municipal (Atlas 2010)

Não há cota por região.

Farmácia (CNES tipo 43), delegacia (MUNIC 2023), mercado e Correios **não** excluem o município. Se faltar algum, o registro vai com `"hidden": true`.

Mercado e Correios são **proxy** (sede ≥ 2 mil hab. + farmácia no CNES): não há cadastro nacional aberto. Vale conferir no local.

Distribuição atual: **86** Sul/Sudeste · **9** Centro-Oeste · **17** Nordeste · **1** Norte.

## Mapa

- **Filtro de região:** chips (Todas, Sudeste, Sul, Centro-Oeste, Nordeste, Norte)
- **Serviços (checkboxes):** UPA/emergência, escola, mercado, farmácia, delegacia, Correios. Marcado = a cidade precisa ter aquele item. **Por padrão só UPA está marcado**, então as 113 aparecem
- A barra de filtros fica sobre o mapa: recolhe ao arrastar/zoom e abre de novo ao passar o mouse (ou tocar em “Filtros”)
- **Popup:** nome/UF e IDH; cidade média; cidade grande; saúde, educação e segurança
- Cidades `hidden` ficam um pouco mais transparentes quando visíveis

## Fontes

- IBGE estimativas de população 2024
- IBGE MUNIC 2021 (saúde, educação) e 2023 (segurança)
- Atlas IDHM 2010 (PNUD/IPEA/FJP)
- SIM/DATASUS (homicídios X85–Y09)
- CNES/DATASUS (UPA, farmácia)

## Estrutura

```
ROCA/
├── assets/                  # CSS, JS e imagens fonte
├── data/
│   ├── cidadezinhas.json    # municípios do mapa (gerado)
│   ├── ibge-pop-2024.json
│   ├── dados2010-ref.csv
│   └── cache/               # bases MUNIC/CNES/SIM (não versionar)
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

Abra [http://localhost:8080](http://localhost:8080). Use um servidor HTTP; não abra o HTML direto do disco.

As cidades vão embutidas no `index.html` (`window.CIDADEZINHAS`). CSS e JS saem com hash no nome (`site.<hash>.css`, `mapa.<hash>.js`) para o GitHub Pages não servir script antigo.

Para atualizar a lista de municípios (precisa das bases em `data/cache/`):

```bash
python3 rebuild_cidadezinhas.py
python3 build.py
```

## Publicação

A pasta **`dist/`** é o artefato final. O GitHub Actions gera ela no CI.

### GitHub Pages

O workflow `.github/workflows/deploy.yml`:

1. Push em `main` (ou `master`)
2. Em **Settings → Pages**, source = **GitHub Actions**

O build roda `python3 build.py` e publica `dist/`. Se a URL mudar, edite `SITE_URL` em `build.py`.

Depois do deploy, o GitHub pode guardar o HTML por alguns minutos. Se o mapa parecer antigo, atualize com hard refresh (Ctrl+Shift+R).

### Netlify

- **Build command:** `python3 build.py`
- **Publish directory:** `dist`

### Cloudflare Pages

- **Build command:** `python3 build.py`
- **Output directory:** `dist`

## Editar conteúdo

- **Cidades:** `rebuild_cidadezinhas.py` → `data/cidadezinhas.json` → `python3 build.py`
- **Layout:** `build.py` (`build_index()`)
- **Estilo:** `assets/css/site.css`
- **Mapa (Leaflet, filtros, popup):** `assets/js/mapa.js`

Scripts opcionais (não rodam no CI):

```bash
python3 gerar-imagem-sp.py   # PNG estático com cidades de SP
```

## Licença

Conteúdo e dados compilados para uso informativo. População, UPA, IDH e infraestrutura mudam — valide sempre no local antes de decidir.
