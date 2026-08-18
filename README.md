# Dev Remoto na Roça

Mapa interativo com **300 cidadezinhas** do Brasil para quem trabalha remoto e quer morar no interior.

Site: [https://marcos-dev79.github.io/sitedaroca/](https://marcos-dev79.github.io/sitedaroca/)

Isto **não é um conselho profissional**. Faça sua própria pesquisa e valide no local.

## Critérios

- Até ~15 mil habitantes (IBGE 2024)
- Até 50 km de uma cidade média (80–300 mil hab.)
- Até ~2 h de um grande centro (≥400 mil hab. ou capital)
- Preferência por melhores índices de IDH (Atlas 2010)
- UPA, escola, farmácia, mercado e açougue (validar no local)

Distribuição atual: **185** Sul/Sudeste · **65** Centro-Oeste · **44** Nordeste · **6** Norte.

## Estrutura

```
ROCA/
├── assets/                  # CSS, JS e imagens fonte
├── data/
│   └── cidadezinhas.json    # 300 municípios do mapa
├── dist/                    # Site gerado (não versionar)
├── build.py                 # Gera dist/ para publicação
├── expandir-cidadezinhas.py # Adiciona nova leva de municípios
├── enriquecer-originais.py  # Completa IDH e notas das cidades
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
python3 expandir-cidadezinhas.py      # nova leva de cidades (use --force se o dataset já tiver 300)
python3 enriquecer-originais.py       # IDH + notas no padrão da expansão
python3 gerar-imagem-sp.py            # PNG estático com 100 cidades de SP
```

## Licença

Conteúdo e dados compilados para uso informativo. População, UPA, IDH e infraestrutura mudam — valide sempre no local antes de decidir.
