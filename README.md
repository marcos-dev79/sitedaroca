# Dev Remoto na Roça

Mapa interativo com cidadezinhas brasileiras para quem trabalha remoto e quer morar no interior. O conjunto atual tem **136 municípios**, ordenados por IDH (Atlas 2010). **54** têm o pacote completo de serviços no JSON; as demais entram com `"hidden": true` e aparecem no mapa conforme os checkboxes.

Site: [https://marcos-dev79.github.io/sitedaroca/](https://marcos-dev79.github.io/sitedaroca/)

Isto **não é um conselho profissional**. Faça sua própria pesquisa e valide no local.

## Critérios (inclusão no JSON)

- Até 20 mil habitantes (IBGE 2024, SIDRA 6579)
- Entre 20 e 50 km de uma cidade média (≥150 mil hab.)
- Até ~1h30 de uma cidade grande (≥500 mil hab.; ~120 km em linha reta a 80 km/h, não é Google Maps)
- UPA no CNES (tipo 73) **ou** emergência 24h municipal (IBGE MUNIC 2021)
- Escola / estrutura educacional municipal (MUNIC 2021)
- Taxa de homicídios ≤ 15 por 100 mil (SIM/DATASUS 2022–2024). Município sem série no SIM **não** é descartado por violência
- Ranking por IDH municipal (Atlas 2010)

Não há cota por região.

Farmácia (CNES tipo 43), delegacia (MUNIC 2023), mercado e Correios **não** excluem o município. Se faltar algum, o registro vai com `"hidden": true`.

Mercado e Correios são **proxy** (sede ≥ 2 mil hab. + farmácia no CNES): não há cadastro nacional aberto. Vale conferir no local.

Distribuição atual: **107** Sul/Sudeste · **10** Centro-Oeste · **18** Nordeste · **1** Norte.

## Mapa

- **Filtro de região:** chips (Todas, Sudeste, Sul, Centro-Oeste, Nordeste, Norte)
- **Altitude:** 0 m (todas), > 300 m, > 500 m, > 1000 m (sede municipal, Atlas 2010)
- **Serviços (checkboxes):** UPA/emergência, escola, mercado, farmácia, delegacia, Correios. Marcado = a cidade precisa ter aquele item. **Por padrão só UPA está marcado**, então as 136 aparecem
- A barra de filtros fica sobre o mapa: recolhe ao arrastar/zoom e abre de novo ao passar o mouse (ou tocar em “Filtros”)
- **Popup:** nome/UF e IDH; altitude; cidade média; cidade grande; saúde, educação e segurança
- **Zonas de Crime:** botão vermelho, desligado por padrão. **30** maiores taxas do país (qualquer tamanho) + **100** com ≥100 mil hab. + **Rio de Janeiro** como referência. Ícone de explosão. Popup: nome, IDH, mortes/100 mil, população.

## Fontes

- IBGE estimativas de população 2024
- IBGE MUNIC 2021 (saúde, educação) e 2023 (segurança)
- Atlas IDHM 2010 (PNUD/IPEA/FJP) — IDH, coordenadas e altitude da sede
- SIM/DATASUS (homicídios X85–Y09)
- CNES/DATASUS (UPA, farmácia)

## Estrutura

```
ROCA/
├── assets/                  # CSS, JS e imagens fonte
├── data/
│   ├── cidadezinhas.json    # municípios do mapa (gerado)
│   ├── zonas-crime.json     # 30 gerais + 100 (≥100 mil) + Rio (gerado)
│   ├── ibge-pop-2024.json
│   ├── dados2010-ref.csv
│   └── cache/               # bases MUNIC/CNES/SIM (não versionar)
├── dist/                    # Site gerado (não versionar)
├── build.py                 # Gera dist/ para publicação
├── rebuild_cidadezinhas.py  # Recalcula o JSON com IBGE/CNES/SIM
├── rebuild_zonas_crime.py   # Recalcula zonas-crime.json
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
- **Zonas de crime:** `rebuild_zonas_crime.py` → `data/zonas-crime.json` → `python3 build.py`
- **Layout:** `build.py` (`build_index()`)
- **Estilo:** `assets/css/site.css`
- **Mapa (Leaflet, filtros, popup):** `assets/js/mapa.js`

Scripts opcionais (não rodam no CI):

```bash
python3 rebuild_zonas_crime.py   # atualiza data/zonas-crime.json
python3 gerar-imagem-sp.py       # PNG estático com cidades de SP
```

## Compartilhar uma busca

Os filtros do mapa vivem na URL, então qualquer combinação é um link. O botão
**Copiar link** na barra de filtros copia o endereço do estado atual.

| Parâmetro | Valores | Exemplo |
| --- | --- | --- |
| `regiao` | `all`, `Sudeste`, `Sul`, `Centro-Oeste`, `Nordeste`, `Norte` | `?regiao=Sul` |
| `alt` | `0`, `300`, `500`, `1000` (altitude mínima em metros) | `?alt=500` |
| `infra` | chaves de `infra` separadas por vírgula (vazio = não exigir nada) | `?infra=upa_ou_emergencia_24h,farmacia` |
| `cor` | `regiao`, `idh`, `violencia` | `?cor=idh` |
| `q` | texto livre da busca | `?q=serra` |
| `cidade` | código IBGE — abre o popup daquele município | `?cidade=3519055` |

Parâmetros ausentes caem no padrão (todas as regiões e altitudes, só UPA exigida, cor por
região). Valores desconhecidos são ignorados em vez de quebrar o mapa.

## Licença

Conteúdo e dados compilados para uso informativo. População, UPA, IDH e infraestrutura mudam — valide sempre no local antes de decidir.
