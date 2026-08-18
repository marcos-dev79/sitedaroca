# Dev remoto na roça: a estratégia que me fez trocar o apartamento pela chácara

Sou desenvolvedor. Trabalho para empresas de fora. Moro no interior.

Não foi fuga — foi **estratégia**. Depois de anos em cidade grande, percebi que ganhar em dólar ou euro enquanto paga aluguel de capital é jogar o jogo no modo difícil. Mudei as regras: **custo de vida de interior, renda de gringa**.

Este post resume os fundamentos que usei para escolher onde morar — e no final, um **mapa com as top 150 cidadezinhas do Brasil** que se encaixam nesse perfil.

---

## 1. Cidade pequena, histórico de segurança, até 15 mil habitantes

Grande demais vira caos. Pequena demais vira isolamento.

O ponto doce: **município de até 15 mil habitantes**, com **histórico consistente de segurança** — baixa criminalidade, comunidade onde todo mundo se conhece, polícia que de fato patrulha a região.

Não procuro paraíso. Procuro **previsibilidade**: um lugar onde deixo a porta aberta sem paranoia e onde a violência não é pauta do dia a dia.

---

## 2. Até 50 km de uma cidade média

A cidadezinha não precisa ter *tudo*. Precisa estar **a no máximo 50 km de uma cidade média** — aquela com 80 a 300 mil habitantes, shopping, hospital maior, especialistas, aeroporto regional.

É o **colchão de infraestrutura**: o dia a dia acontece na roça, mas quando preciso de algo que a cidade pequena não tem, estou a menos de uma hora de carro.

---

## 3. Até 2 horas de um grande centro

Emergências médicas sérias, voos internacionais, eventos, networking — eventualmente você precisa de uma metrópole.

Critério: **até 2 horas de carro de um grande centro** (capital estadual ou metrópole com mais de 1 milhão de habitantes).

Não é morar perto de tudo. É morar longe *com linha de escape*.

---

## 4. Chácara entre 3 e 7 km da cidadezinha

Aqui mora a diferença entre "interior" e "roça de verdade".

Procuro propriedade **afastada 3 a 7 km do centro da cidade pequena** — longe o suficiente para silêncio, céu estrelado e privacidade; perto o suficiente para ir ao mercado, buscar remédio ou levar a criança na escola em 10–15 minutos.

Não é isolamento. É **perímetro inteligente**.

---

## 5. A cidadezinha precisa ter o básico: UPA, escola, farmácia, mercado, açougue

Sem isso, a estratégia desmorona.

Checklist obrigatório:

- **UPA** (Unidade de Pronto Atendimento) — atendimento 24h para urgências
- **Escola** — rede municipal ou estadual funcional
- **Farmácia** — pelo menos uma com estoque decente
- **Mercado** — abastecimento semanal
- **Açougue** — parece detalhe, mas no interior faz diferença

Em emergência, vou rápido até a UPA. De lá, **ambulância me transfere para hospital maior** na cidade média ou no grande centro. Esse encadeamento é inegociável.

---

## 6. Autossuficiência: água e saneamento por conta própria

Na chácara, **água e esgoto são sua responsabilidade**:

- Poço artesiano ou cisterna + filtragem
- Fossa séptica ou biodigestor dimensionados
- Reserva para seca (caixa d'água, reservatório)

Não dependo de concessionária na porta. Dependo de **planejamento**.

---

## 7. Internet: Starlink como padrão, fibra como bônus

Trabalho remoto exige conexão estável. Ponto.

- **Starlink** é o padrão — funciona praticamente em qualquer ponto do Brasil rural
- Em muitos municípios do interior, **fibra óptica já chegou** ou está chegando (verificar no endereço exato antes de comprar)

Minha regra: **testar o sinal no terreno antes de fechar negócio**. Starlink tem período de teste; fibra depende do provedor local.

---

## 8. Energia independente: solar ou eólica é um plus

Rede elétrica existe na maioria dos lugares, mas **geração própria** muda o jogo:

- **Placa solar** — payback de 4–6 anos; zero preocupação com apagão
- **Eólica** — viável em regiões com vento constante (Sul, litoral, serras)

Não é requisito absoluto, mas quando a propriedade já tem estrutura ou terreno com insolação/vento favorável, é **critério de desempate**.

---

## 9. Trabalhar para a gringa e ganhar em dólar: você vive como rei no interior

A matemática é brutalmente simples.

Um dev pleno/sênior remoto para EUA/Europa ganha **US$ 3.000–8.000+/mês**. No interior:

- Aluguel de casa grande com quintal: **R$ 1.500–3.000**
- Chácara financiada ou comprada à vista com 2–3 anos de economia
- Mercado, combustível, escola — tudo **3 a 5 vezes mais barato** que capital
- Qualidade de vida: ar limpo, espaço, silêncio, segurança

Não estou "me escondendo" no interior. Estou **arbitrando geografia contra moeda forte**.

---

## Mapa: Top 150 cidadezinhas que se encaixam neste perfil

Com base nos critérios acima, montei um ranking de **150 municípios**:

| Distribuição | Quantidade |
|---|---|
| **Sul + Sudeste** | 80 (44 Sudeste + 36 Sul) |
| **Centro-Oeste** | 40 |
| **Nordeste** | 27 |
| **Norte** | 3 |

A segunda leva (101–150) adiciona **20** no Sul/Sudeste, **20** no Centro-Oeste e **10** no Nordeste.

### Como usar o mapa

Abra o site publicado ou, localmente, sirva a pasta `dist/`:

```bash
python3 build.py
cd dist && python3 -m http.server 8080
```

O mapa interativo está em [`mapa.html`](mapa.html) (ou `dist/mapa.html` após o build).

Cada ponto mostra:
- Nome e UF
- População estimada
- Cidade média de referência (≤50 km)
- Grande centro mais próximo (≤2 h)
- Nota sobre infraestrutura e perfil

### Destaques do ranking

| # | Cidade | UF | Por quê |
|---|---|---|---|
| 1 | Gavião Peixoto | SP | IPS #1 Brasil; saneamento e educação exemplares |
| 4 | Borá | SP | Zero roubos em 24 anos; PIB per capita altíssimo |
| 5 | Luzerna | SC | IPS top 10; colonização italiana; serviços completos |
| 7 | Arapuã | PR | 3,5 mil hab.; Mata Atlântica; calma |
| 83 | Anhanguera | GO | 913 hab.; ultra-rural; custo mínimo |
| 112 | Treze Tílias | SC | Colônia austríaca; qualidade de vida |
| 137 | Nossa Senhora do Livramento | MT | 30 km de Cuiabá; rural pantaneiro |
| 150 | Rio do Fogo | RN | Litoral; vento; potencial eólico |

> **Aviso:** População, UPA e disponibilidade de fibra mudam. Sempre valide no local antes de decidir. Este mapa é **ponto de partida**, não contrato.

---

## Fechando

Morar na roça trabalhando remoto não é romantizar o campo. É **engenharia de vida**:

1. Cidade pequena e segura (≤15 mil hab.)
2. Perto de cidade média (≤50 km) e grande centro (≤2 h)
3. Chácara afastada, mas não isolada (3–7 km)
4. UPA + escola + mercado + farmácia + açougue
5. Água e esgoto autossuficientes
6. Starlink (fibra se tiver)
7. Solar/eólica como plus
8. Renda em moeda forte

Se você é dev, já tem a ferramenta mais valiosa: **mobilidade geográfica**. O resto é escolher o ponto no mapa.

---

*Dados compilados a partir de estimativas IBGE 2024, IPS Brasil, indicadores locais e critérios de proximidade geográfica. Arquivo de dados: [`data/cidadezinhas.json`](data/cidadezinhas.json).*
