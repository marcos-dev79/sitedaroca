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
  const idh =
    typeof c.idh === "number" ? c.idh.toFixed(3) : "n/d";
  const taxa =
    typeof c.taxa_homicidios_100k === "number"
      ? c.taxa_homicidios_100k.toFixed(1)
      : "n/d";
  const pop =
    typeof c.pop === "number" ? c.pop.toLocaleString("pt-BR") : "n/d";
  const mortes = c.homicidios != null ? c.homicidios : "n/d";
  const ano = c.homicidios_ano || "n/d";
  const rank = c.rank != null ? `#${c.rank}` : "";
  const grupo = {
    top30_geral: "entre as 30 maiores taxas do país",
    top100_min_100k: "entre as 100 mais violentas com ≥100 mil hab.",
    referencia: "incluída como referência",
  }[c.grupo] || "";
  return (
    `<b>${c.nome}/${c.uf}</b> ${rank}<br>` +
    `IDH: ${idh}<br>` +
    `Mortes: ${taxa}/100 mil hab.<br>` +
    `Habitantes: ${pop}<br>` +
    `Homicídios: ${mortes} (${ano}; SIM/DATASUS)` +
    (grupo ? `<br>${grupo}` : "")
  );
}

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

  const crimeBtn = document.getElementById("toggle-crime");
  if (crimeBtn) {
    crimeBtn.addEventListener("click", () => {
      crimeVisible = !crimeVisible;
      crimeBtn.classList.toggle("active", crimeVisible);
      crimeBtn.setAttribute("aria-pressed", crimeVisible ? "true" : "false");
      renderCrimeLayer();
    });
  }

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

    map = L.map("map", { center: [-15.5, -52.0], zoom: 4, minZoom: 3 });
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      attribution: "&copy; OpenStreetMap &copy; CARTO",
      subdomains: "abcd",
      maxZoom: 19,
    }).addTo(map);

    markersLayer = L.layerGroup().addTo(map);
    crimeLayer = L.layerGroup();
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
