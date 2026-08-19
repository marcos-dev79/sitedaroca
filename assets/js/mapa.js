const REGIAO_CORES = {
  Sul: "#2563eb",
  Sudeste: "#16a34a",
  "Centro-Oeste": "#ca8a04",
  Nordeste: "#dc2626",
  Norte: "#9333ea",
};

let map;
let markersLayer;
let allCities = [];
let activeRegiao = "all";
let minAltitude = 0;

function popupHtml(c) {
  const idh =
    typeof c.idh === "number" ? c.idh.toFixed(3) : "n/d";
  const alt =
    typeof c.altitude === "number" ? `${c.altitude} m` : "n/d";
  const saude = c.saude || "não informado";
  const educacao = c.educacao || "não informado";
  const seguranca = c.seguranca || "não informado";
  return (
    `<b>${c.nome}/${c.uf}</b> (IDH: ${idh})<br>` +
    `Altitude: ${alt}<br>` +
    `Cidade média: ${c.cidade_media}<br>` +
    `Cidade grande: ${c.grande_centro}<br>` +
    `<b>Saúde:</b> ${saude}<br>` +
    `<b>Educação:</b> ${educacao}<br>` +
    `<b>Segurança:</b> ${seguranca}`
  );
}

const INFRA_KEYS = [
  "upa_ou_emergencia_24h",
  "escola",
  "mercado",
  "farmacia",
  "delegacia",
  "correios",
];

function currentQuery() {
  const search = document.getElementById("search");
  return search ? search.value : "";
}

function requiredInfra() {
  return INFRA_KEYS.filter((key) => {
    const el = document.querySelector(`input[data-infra="${key}"]`);
    return !el || el.checked;
  });
}

function matchesFilter(c, query) {
  const infra = c.infra || {};
  for (const key of requiredInfra()) {
    if (!infra[key]) return false;
  }
  const altOk =
    minAltitude <= 0 ||
    (typeof c.altitude === "number" && c.altitude > minAltitude);
  if (!altOk) return false;
  const q = query.trim().toLowerCase();
  const regiaoOk = activeRegiao === "all" || c.regiao === activeRegiao;
  if (!regiaoOk) return false;
  if (!q) return true;
  const hay = `${c.nome} ${c.uf} ${c.regiao} ${c.altitude ?? ""} ${c.cidade_media} ${c.grande_centro || ""} ${c.saude || ""} ${c.educacao || ""} ${c.seguranca || ""} ${c.nota || ""}`.toLowerCase();
  return hay.includes(q);
}

function renderMarkers(query = "") {
  if (!markersLayer) return;
  markersLayer.clearLayers();
  const filtered = allCities.filter((c) => matchesFilter(c, query));
  let plotted = 0;
  for (const c of filtered) {
    if (typeof c.lat !== "number" || typeof c.lng !== "number") continue;
    L.circleMarker([c.lat, c.lng], {
      radius: 7,
      fillColor: REGIAO_CORES[c.regiao] || "#64748b",
      color: "#fff",
      weight: 1.5,
      fillOpacity: c.hidden ? 0.45 : 0.85,
    })
      .bindPopup(popupHtml(c))
      .addTo(markersLayer);
    plotted += 1;
  }
  const el = document.getElementById("visible-count");
  if (el) el.textContent = plotted;
}

function setupFilters() {
  const search = document.getElementById("search");
  const chips = document.querySelectorAll(".chip[data-regiao]");
  const altChips = document.querySelectorAll(".chip[data-alt]");
  const bar = document.getElementById("map-controls");

  if (search) {
    search.addEventListener("input", () => renderMarkers(search.value));
  }

  document.querySelectorAll("input[data-infra]").forEach((box) => {
    box.addEventListener("change", () => renderMarkers(currentQuery()));
  });

  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      chips.forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      activeRegiao = chip.dataset.regiao;
      renderMarkers(currentQuery());
    });
  });

  altChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      altChips.forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      minAltitude = Number(chip.dataset.alt) || 0;
      renderMarkers(currentQuery());
    });
  });

  if (!map || !bar) return;

  const collapse = () => {
    if (bar.contains(document.activeElement)) return;
    bar.classList.add("collapsed");
  };
  const expand = () => bar.classList.remove("collapsed");

  map.on("dragstart zoomstart", collapse);
  bar.addEventListener("pointerenter", expand);
  bar.addEventListener("focusin", expand);
  bar.addEventListener("click", () => {
    if (bar.classList.contains("collapsed")) expand();
  });
}

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

    map = L.map("map", { center: [-15.5, -52.0], zoom: 4, minZoom: 3 });
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      attribution: "&copy; OpenStreetMap &copy; CARTO",
      subdomains: "abcd",
      maxZoom: 19,
    }).addTo(map);

    markersLayer = L.layerGroup().addTo(map);
    renderMarkers();
    setupFilters();
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
