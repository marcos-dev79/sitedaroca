# Dev Remoto na Roça

Site estático com guia para desenvolvedores remotos morarem no interior do Brasil, incluindo mapa interativo com **150 cidadezinhas**.

## Estrutura

```
ROCA/
├── assets/          # CSS e JS fonte
├── data/            # JSON com as 150 cidadezinhas
├── dist/            # Site pronto para publicação (gerado pelo build)
├── build.py         # Script de build
└── README.md
```

## Build local

```bash
python3 build.py
```

Abra `dist/index.html` no navegador ou sirva localmente:

```bash
cd dist && python3 -m http.server 8080
# http://localhost:8080
```

> O mapa carrega `data/cidadezinhas.json` via fetch — precisa de servidor HTTP (não funciona abrindo o HTML direto do disco em alguns navegadores).

## Publicação

A pasta **`dist/`** é o artefato final. Faça upload dela ou configure o host para publicar seu conteúdo.

### GitHub Pages

1. Crie um repositório e envie o projeto
2. Em **Settings → Pages**, escolha **GitHub Actions** ou publique a branch `gh-pages` com o conteúdo de `dist/`

Workflow sugerido (`.github/workflows/deploy.yml`):

```yaml
name: Deploy site
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python3 build.py
      - uses: JamesIves/github-pages-deploy-action@v4
        with:
          folder: dist
```

Se o site ficar em `https://usuario.github.io/ROCA/`, edite `SITE_URL` em `build.py` e rode o build de novo.

### Netlify

1. Conecte o repositório
2. **Build command:** `python3 build.py`
3. **Publish directory:** `dist`

Ou arraste a pasta `dist/` em [app.netlify.com/drop](https://app.netlify.com/drop).

### Cloudflare Pages

- Build command: `python3 build.py`
- Output directory: `dist`

## Editar conteúdo

- **Cidadezinhas:** edite `data/cidadezinhas.json` e rode `python3 build.py`
- **Artigo:** edite a função `build_index()` em `build.py`
- **Estilo:** `assets/css/site.css`
- **Mapa:** `assets/js/mapa.js`

## Licença

Conteúdo e dados compilados para uso informativo. Valide sempre no local antes de decidir morar em qualquer município.
