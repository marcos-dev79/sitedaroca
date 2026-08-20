/* Mapa das cidadezinhas — Leaflet, filtros na sidebar e estado compartilhável na URL. */

const REGIOES = ["Sudeste", "Sul", "Centro-Oeste", "Nordeste", "Norte"];

const REGIAO_CORES = {
  Sul: "#2563eb",
  Sudeste: "#16a34a",
  "Centro-Oeste": "#ca8a04",
  Nordeste: "#dc2626",
  Norte: "#9333ea",
};

const COR_SEM_DADO = "#64748b";

const INFRA_KEYS = [
  "upa_ou_emergencia_24h",
  "escola",
  "mercado",
  "farmacia",
  "delegacia",
  "correios",
];

const INFRA_LABELS = {
  upa_ou_emergencia_24h: "🏥 UPA / emergência",
  escola: "🏫 Escola",
  mercado: "🛒 Mercado",
  farmacia: "💊 Farmácia",
  delegacia: "🚓 Delegacia",
  correios: "📮 Correios",
};

const INFRA_PADRAO = ["upa_ou_emergencia_24h"];

/* Faixas calibradas sobre o conjunto atual (IDH 0,514–0,793; homicídios 5,1–14,8). */
const FAIXAS_IDH = [
  { max: 0.65, cor: "#414487", texto: "IDH < 0,650" },
  { max: 0.7, cor: "#2a788e", texto: "0,650 – 0,699" },
  { max: 0.75, cor: "#22a884", texto: "0,700 – 0,749" },
  { max: Infinity, cor: "#7ad151", texto: "≥ 0,750" },
];

const FAIXAS_VIOLENCIA = [
  { max: 7.5, cor: "#41b6c4", texto: "≤ 7,5 / 100 mil" },
  { max: 11, cor: "#fdae61", texto: "7,5 – 11 / 100 mil" },
  { max: Infinity, cor: "#d73027", texto: "> 11 / 100 mil" },
];

function faixaDe(valor, faixas) {
  if (typeof valor !== "number" || Number.isNaN(valor)) return null;
  return faixas.find((f) => valor < f.max) || faixas[faixas.length - 1];
}

const MODOS_COR = {
  regiao: {
    cor: (c) => REGIAO_CORES[c.regiao] || COR_SEM_DADO,
    legenda: () => REGIOES.map((r) => ({ cor: REGIAO_CORES[r], texto: r })),
  },
  idh: {
    cor: (c) => (faixaDe(c.idh, FAIXAS_IDH) || {}).cor || COR_SEM_DADO,
    legenda: () => FAIXAS_IDH.map((f) => ({ cor: f.cor, texto: f.texto })),
  },
  violencia: {
    cor: (c) =>
      (faixaDe(c.taxa_homicidios_100k, FAIXAS_VIOLENCIA) || {}).cor || COR_SEM_DADO,
    legenda: () =>
      FAIXAS_VIOLENCIA.map((f) => ({ cor: f.cor, texto: f.texto })).concat([
        { cor: COR_SEM_DADO, texto: "sem série no SIM" },
      ]),
  },
};

const NUM = new Intl.NumberFormat("pt-BR");

const state = {
  regiao: "all",
  altitude: 0,
  query: "",
  infra: new Set(INFRA_PADRAO),
  cor: "regiao",
  cidade: null,
};

let map;
let markersLayer;
let allCities = [];
let markerPorIbge = new Map();
let crimeLayer;
let crimeZones = [];
let crimeVisible = false;

const CRIME_BURST_SVG =
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="26" height="26" aria-hidden="true">' +
  '<path fill="#dc2626" stroke="#fff" stroke-width="1.2" stroke-linejoin="round" ' +
  'd="M16 2 18.2 11.2 28 8.2 21.2 16 30 20.2 20.5 21.2 22.5 30 16 23.2 9.5 30 11.5 21.2 2 20.2 10.8 16 4 8.2 13.8 11.2Z"/>' +
  "</svg>";

function crimeIcon() {
  return L.divIcon({
    className: "crime-icon",
    html: CRIME_BURST_SVG,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
    popupAnchor: [0, -14],
  });
}

function popupCrime(c) {
  const idh = typeof c.idh === "number" ? c.idh.toFixed(3) : "n/d";
  const taxa =
    typeof c.taxa_homicidios_100k === "number" ? c.taxa_homicidios_100k.toFixed(1) : "n/d";
  const pop = typeof c.pop === "number" ? c.pop.toLocaleString("pt-BR") : "n/d";
  const mortes = c.homicidios != null ? c.homicidios : "n/d";
  const ano = c.homicidios_ano || "n/d";
  const rank = c.rank != null ? `#${c.rank}` : "";
  const grupo = {
    top30_geral: "entre as 30 maiores taxas do país",
    top100_min_100k: "entre as 100 mais violentas com ≥100 mil hab.",
    referencia: "incluída como referência",
  }[c.grupo] || "";
  return (
    `<b>${escapeHtml(c.nome)}/${escapeHtml(c.uf)}</b> ${escapeHtml(rank)}<br>` +
    `IDH: ${escapeHtml(idh)}<br>` +
    `Mortes: ${escapeHtml(taxa)}/100 mil hab.<br>` +
    `Habitantes: ${escapeHtml(pop)}<br>` +
    `Homicídios: ${escapeHtml(mortes)} (${escapeHtml(ano)}; SIM/DATASUS)` +
    (grupo ? `<br>${escapeHtml(grupo)}` : "")
  );
}

/* ── Helpers ── */

function escapeHtml(valor) {
  return String(valor ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function decimal(valor, casas) {
  return typeof valor === "number" ? valor.toFixed(casas).replace(".", ",") : null;
}

/* ── Popup ── */

function tagsInfra(c) {
  const infra = c.infra || {};
  const itens = INFRA_KEYS.map((key) => {
    const tem = Boolean(infra[key]);
    const estado = tem ? "Tem" : "Não consta";
    return (
      `<li class="tag ${tem ? "on" : "off"}" title="${escapeHtml(estado)}">` +
      `${escapeHtml(INFRA_LABELS[key])}</li>`
    );
  });
  return `<ul class="city-tags">${itens.join("")}</ul>`;
}

function linhaViolencia(c) {
  const faixa = faixaDe(c.taxa_homicidios_100k, FAIXAS_VIOLENCIA);
  if (!faixa) return `<span class="risk risk-na">homicídios: sem série</span>`;
  const nivel = FAIXAS_VIOLENCIA.indexOf(faixa);
  const taxa = decimal(c.taxa_homicidios_100k, 1);
  return (
    `<span class="risk risk-${nivel}" style="--risk:${faixa.cor}">` +
    `${escapeHtml(taxa)} homicídios/100 mil</span>`
  );
}

function popupHtml(c) {
  const idh = decimal(c.idh, 3) || "n/d";
  const pop = typeof c.pop === "number" ? `${NUM.format(c.pop)} hab.` : "população n/d";
  const selo = c.hidden
    ? `<span class="badge-hidden" title="Falta algum serviço da lista">serviços incompletos</span>`
    : "";
  const nota = c.nota ? `<p class="city-nota">${escapeHtml(c.nota)}</p>` : "";

  const detalhes = [
    ["Saúde", c.saude],
    ["Educação", c.educacao],
    ["Segurança", c.seguranca],
  ]
    .filter(([, texto]) => texto)
    .map(([rotulo, texto]) => `<p><b>${rotulo}:</b> ${escapeHtml(texto)}</p>`)
    .join("");

  return (
    `<article class="city-card">` +
    `<header class="city-head">` +
    `<h3>${escapeHtml(c.nome)}/${escapeHtml(c.uf)}</h3>` +
    (typeof c.rank === "number" ? `<span class="city-rank">#${c.rank}</span>` : "") +
    `</header>` +
    `<p class="city-meta">${escapeHtml(pop)} · IDH ${escapeHtml(idh)} · ${linhaViolencia(c)}</p>` +
    (selo ? `<p class="city-selo">${selo}</p>` : "") +
    tagsInfra(c) +
    `<dl class="city-logistica">` +
    `<div><dt>🏙️ Cidade média</dt><dd>${escapeHtml(c.cidade_media || "n/d")}</dd></div>` +
    `<div><dt>🚗 Cidade grande</dt><dd>${escapeHtml(c.grande_centro || "n/d")}</dd></div>` +
    `</dl>` +
    nota +
    (detalhes
      ? `<details class="city-fontes"><summary>Ver detalhes das fontes</summary>${detalhes}</details>`
      : "") +
    `</article>`
  );
}

/* O conteúdo do popup é um NÓ, não uma string: o _updateContent() do Leaflet
   reescreve innerHTML a cada update() e fecharia o <details> aberto pelo usuário.
   Com um nó, ele só o reanexa — o estado sobrevive. Criado na primeira abertura. */
function popupNode(layer) {
  if (!layer._cardNode) {
    const node = document.createElement("div");
    node.innerHTML = popupHtml(layer.cidade);
    layer._cardNode = node;
  }
  return layer._cardNode;
}

/* ── Estado na URL ── */

function lerUrl() {
  const p = new URLSearchParams(location.search);

  const regiao = p.get("regiao");
  if (regiao && (regiao === "all" || REGIOES.includes(regiao))) state.regiao = regiao;

  const altitude = Number(p.get("alt"));
  if ([0, 300, 500, 1000].includes(altitude)) state.altitude = altitude;

  const q = p.get("q");
  if (q) state.query = q;

  if (p.has("infra")) {
    const pedidos = p.get("infra").split(",").filter((k) => INFRA_KEYS.includes(k));
    state.infra = new Set(pedidos);
  }

  const cor = p.get("cor");
  if (cor && MODOS_COR[cor]) state.cor = cor;

  state.cidade = p.get("cidade");
}

function escreverUrl() {
  const p = new URLSearchParams();
  if (state.regiao !== "all") p.set("regiao", state.regiao);
  if (state.altitude > 0) p.set("alt", String(state.altitude));
  if (state.query.trim()) p.set("q", state.query.trim());

  const infra = INFRA_KEYS.filter((k) => state.infra.has(k));
  if (infra.join(",") !== INFRA_PADRAO.join(",")) p.set("infra", infra.join(","));

  if (state.cor !== "regiao") p.set("cor", state.cor);
  if (state.cidade) p.set("cidade", state.cidade);

  const qs = p.toString();
  history.replaceState(null, "", qs ? `?${qs}` : location.pathname);
}

/* ── Filtro ── */

function matchesFilter(c) {
  const infra = c.infra || {};
  for (const key of state.infra) {
    if (!infra[key]) return false;
  }
  if (state.altitude > 0 && !(typeof c.altitude === "number" && c.altitude > state.altitude)) {
    return false;
  }
  if (state.regiao !== "all" && c.regiao !== state.regiao) return false;

  const q = state.query.trim().toLowerCase();
  if (!q) return true;
  const hay = `${c.nome} ${c.uf} ${c.regiao} ${c.altitude ?? ""} ${c.cidade_media} ${c.grande_centro || ""} ${c.saude || ""} ${c.educacao || ""} ${c.seguranca || ""} ${c.nota || ""}`.toLowerCase();
  return hay.includes(q);
}

/* ── Render ── */

function renderLegenda() {
  const el = document.getElementById("map-legend");
  if (!el) return;
  const itens = MODOS_COR[state.cor].legenda();
  el.innerHTML = itens
    .map(
      (i) =>
        `<div><span style="background:${escapeHtml(i.cor)}"></span>${escapeHtml(i.texto)}</div>`
    )
    .join("") +
    (crimeVisible
      ? '<div class="legend-crime"><span class="legend-burst"></span>Zonas de crime</div>'
      : "");
}

function renderMarkers() {
  if (!markersLayer) return;
  markersLayer.clearLayers();
  markerPorIbge = new Map();

  const corDe = MODOS_COR[state.cor].cor;
  const filtered = allCities.filter(matchesFilter);
  let plotted = 0;

  for (const c of filtered) {
    if (typeof c.lat !== "number" || typeof c.lng !== "number") continue;
    const marker = L.circleMarker([c.lat, c.lng], {
      radius: 7,
      fillColor: corDe(c),
      color: "#fff",
      weight: 1.5,
      fillOpacity: c.hidden ? 0.45 : 0.85,
    }).bindPopup(popupNode, { maxWidth: 320, minWidth: 240, autoPanPadding: [24, 24] });

    marker.cidade = c;
    marker.cidadeIbge = c.ibge;
    marker.addTo(markersLayer);
    if (c.ibge) markerPorIbge.set(String(c.ibge), marker);
    plotted += 1;
  }

  const contador = document.getElementById("visible-count");
  if (contador) contador.textContent = plotted;
  const total = document.getElementById("total-count");
  if (total) total.textContent = allCities.length;
  const vazio = document.getElementById("empty-state");
  if (vazio) vazio.hidden = plotted > 0;

  renderLegenda();
}

/* ── Sidebar ── */

const SIDEBAR_KEY = "roca:filtros-abertos";

function ehTelaEstreita() {
  return window.matchMedia("(max-width: 700px)").matches;
}

function setSidebar(aberta, persistir = true) {
  const bar = document.getElementById("map-controls");
  const toggle = document.getElementById("sidebar-toggle");
  if (!bar) return;
  bar.classList.toggle("collapsed", !aberta);
  if (toggle) toggle.setAttribute("aria-expanded", String(aberta));
  if (persistir) {
    try {
      localStorage.setItem(SIDEBAR_KEY, aberta ? "1" : "0");
    } catch (err) {
      /* modo privado: segue sem persistir */
    }
  }
}

function sidebarInicial() {
  let salvo = null;
  try {
    salvo = localStorage.getItem(SIDEBAR_KEY);
  } catch (err) {
    salvo = null;
  }
  if (salvo === "1") return true;
  if (salvo === "0") return false;
  return !ehTelaEstreita();
}

/* ── Controles ── */

function aplicarStateNosControles() {
  const search = document.getElementById("search");
  if (search) search.value = state.query;

  document.querySelectorAll(".chip[data-regiao]").forEach((chip) => {
    chip.classList.toggle("active", chip.dataset.regiao === state.regiao);
  });

  document.querySelectorAll(".chip[data-alt]").forEach((chip) => {
    const ativo = Number(chip.dataset.alt) === state.altitude;
    chip.classList.toggle("active", ativo);
    chip.setAttribute("aria-pressed", String(ativo));
  });

  document.querySelectorAll(".chip[data-cor]").forEach((chip) => {
    const ativo = chip.dataset.cor === state.cor;
    chip.classList.toggle("active", ativo);
    chip.setAttribute("aria-pressed", String(ativo));
  });

  document.querySelectorAll("input[data-infra]").forEach((box) => {
    box.checked = state.infra.has(box.dataset.infra);
  });
}

function atualizar() {
  escreverUrl();
  renderMarkers();
}

function limparFiltros() {
  state.regiao = "all";
  state.altitude = 0;
  state.query = "";
  state.infra = new Set(INFRA_PADRAO);
  state.cor = "regiao";
  state.cidade = null;
  aplicarStateNosControles();
  atualizar();
}

async function copiarLink() {
  const botao = document.getElementById("copy-link");
  const original = botao ? botao.textContent : "";
  let ok = false;
  try {
    await navigator.clipboard.writeText(location.href);
    ok = true;
  } catch (err) {
    const campo = document.createElement("textarea");
    campo.value = location.href;
    campo.setAttribute("readonly", "");
    campo.style.position = "fixed";
    campo.style.opacity = "0";
    document.body.appendChild(campo);
    campo.select();
    try {
      ok = document.execCommand("copy");
    } catch (err2) {
      ok = false;
    }
    document.body.removeChild(campo);
  }
  if (!botao) return;
  botao.textContent = ok ? "Link copiado!" : "Copie da barra de endereço";
  setTimeout(() => {
    botao.textContent = original;
  }, 2000);
}

function setupFilters() {
  const search = document.getElementById("search");
  if (search) {
    search.addEventListener("input", () => {
      state.query = search.value;
      atualizar();
    });
  }

  document.querySelectorAll("input[data-infra]").forEach((box) => {
    box.addEventListener("change", () => {
      if (box.checked) state.infra.add(box.dataset.infra);
      else state.infra.delete(box.dataset.infra);
      atualizar();
    });
  });

  document.querySelectorAll(".chip[data-regiao]").forEach((chip) => {
    chip.addEventListener("click", () => {
      state.regiao = chip.dataset.regiao;
      aplicarStateNosControles();
      atualizar();
    });
  });

  document.querySelectorAll(".chip[data-alt]").forEach((chip) => {
    chip.addEventListener("click", () => {
      state.altitude = Number(chip.dataset.alt) || 0;
      aplicarStateNosControles();
      atualizar();
    });
  });

  const crimeBtn = document.getElementById("toggle-crime");
  if (crimeBtn) {
    crimeBtn.addEventListener("click", () => {
      crimeVisible = !crimeVisible;
      crimeBtn.classList.toggle("active", crimeVisible);
      crimeBtn.setAttribute("aria-pressed", String(crimeVisible));
      renderCrimeLayer();
      renderLegenda();
    });
  }

  document.querySelectorAll(".chip[data-cor]").forEach((chip) => {
    chip.addEventListener("click", () => {
      state.cor = chip.dataset.cor;
      aplicarStateNosControles();
      atualizar();
    });
  });

  const limpar = document.getElementById("clear-filters");
  if (limpar) limpar.addEventListener("click", limparFiltros);

  const copiar = document.getElementById("copy-link");
  if (copiar) copiar.addEventListener("click", copiarLink);

  const toggle = document.getElementById("sidebar-toggle");
  const fechar = document.getElementById("sidebar-close");
  const bar = document.getElementById("map-controls");
  if (toggle) {
    toggle.addEventListener("click", () =>
      setSidebar(bar ? bar.classList.contains("collapsed") : true)
    );
  }
  if (fechar) fechar.addEventListener("click", () => setSidebar(false));

  if (bar) {
    L.DomEvent.disableClickPropagation(bar);
    L.DomEvent.disableScrollPropagation(bar);
  }

  if (map) {
    map.on("dragstart zoomstart", () => {
      if (ehTelaEstreita()) setSidebar(false, false);
    });
    map.on("popupopen", (e) => {
      const marker = e.popup._source;
      state.cidade = marker && marker.cidadeIbge ? String(marker.cidadeIbge) : null;
      escreverUrl();
      const detalhes = e.popup.getElement().querySelector("details");
      if (detalhes && !detalhes.dataset.wired) {
        detalhes.dataset.wired = "1";
        detalhes.addEventListener("toggle", () => e.popup.update());
      }
    });
    map.on("popupclose", () => {
      state.cidade = null;
      escreverUrl();
    });
  }
}

function renderCrimeLayer() {
  if (!crimeLayer) return;
  crimeLayer.clearLayers();
  if (!crimeVisible) {
    if (map && map.hasLayer(crimeLayer)) map.removeLayer(crimeLayer);
    return;
  }
  if (map && !map.hasLayer(crimeLayer)) crimeLayer.addTo(map);
  for (const c of crimeZones) {
    if (typeof c.lat !== "number" || typeof c.lng !== "number") continue;
    L.marker([c.lat, c.lng], { icon: crimeIcon(), zIndexOffset: 800 })
      .bindPopup(popupCrime(c))
      .addTo(crimeLayer);
  }
}

async function loadCrimeZones() {
  if (Array.isArray(window.ZONAS_CRIME) && window.ZONAS_CRIME.length) {
    return window.ZONAS_CRIME;
  }
  try {
    const res = await fetch(`data/zonas-crime.json?v=${Date.now()}`, { cache: "no-store" });
    if (!res.ok) return [];
    const payload = await res.json();
    return payload.zonas_crime || [];
  } catch {
    return [];
  }
}

function abrirCidadeDaUrl() {
  if (!state.cidade) return;
  const marker = markerPorIbge.get(String(state.cidade));
  if (!marker) {
    state.cidade = null;
    escreverUrl();
    return;
  }
  map.setView(marker.getLatLng(), Math.max(map.getZoom(), 8));
  marker.openPopup();
}

/* ── Dados ── */
async function loadCities() {
  if (Array.isArray(window.CIDADEZINHAS) && window.CIDADEZINHAS.length) {
    return window.CIDADEZINHAS;
  }
  const res = await fetch(`data/cidadezinhas.json?v=${Date.now()}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const payload = await res.json();
  return payload.cidadezinhas || [];
}

async function initMap() {
  const loading = document.getElementById("map-loading");
  try {
    allCities = await loadCities();
    crimeZones = await loadCrimeZones();
    lerUrl();

    map = L.map("map", { center: [-15.5, -52.0], zoom: 4, minZoom: 3, zoomControl: false });
    L.control.zoom({ position: "topright" }).addTo(map);
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      attribution: "&copy; OpenStreetMap &copy; CARTO",
      subdomains: "abcd",
      maxZoom: 19,
    }).addTo(map);

    markersLayer = L.layerGroup().addTo(map);
    crimeLayer = L.layerGroup();

    aplicarStateNosControles();
    setSidebar(sidebarInicial(), false);
    renderMarkers();
    setupFilters();
    escreverUrl();
    abrirCidadeDaUrl();
  } catch (err) {
    const wrap = document.querySelector(".map-wrap");
    if (wrap) {
      wrap.innerHTML =
        `<div class="map-loading" style="position:static;min-height:320px">` +
        `Erro ao carregar dados do mapa. Verifique se o site foi publicado com a pasta <code>data/</code>.</div>`;
    }
    console.error(err);
  } finally {
    if (loading) loading.style.display = "none";
  }
}

document.addEventListener("DOMContentLoaded", initMap);
