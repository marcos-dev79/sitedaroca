#!/usr/bin/env python3
"""Adiciona cidadezinhas ao dataset com base em população, proximidade e IDH."""

import argparse
import csv
import gzip
import json
import math
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "cidadezinhas.json"
REF = ROOT / "data" / "dados2010-ref.csv"
POP_CACHE = ROOT / "data" / "ibge-pop-2024.json"
ADD_COUNT = 150

MAX_POP = 15_000
MEDIUM_MIN = 80_000
MEDIUM_MAX = 300_000
LARGE_MIN = 400_000
MAX_MEDIUM_KM = 50
MAX_LARGE_KM = 130
DRIVE_SPEED_KMH = 65

CAPITAIS = {
    "AC": "Rio Branco",
    "AL": "Maceió",
    "AP": "Macapá",
    "AM": "Manaus",
    "BA": "Salvador",
    "CE": "Fortaleza",
    "DF": "Brasília",
    "ES": "Vitória",
    "GO": "Goiânia",
    "MA": "São Luís",
    "MT": "Cuiabá",
    "MS": "Campo Grande",
    "MG": "Belo Horizonte",
    "PA": "Belém",
    "PB": "João Pessoa",
    "PR": "Curitiba",
    "PE": "Recife",
    "PI": "Teresina",
    "RJ": "Rio de Janeiro",
    "RN": "Natal",
    "RS": "Porto Alegre",
    "RO": "Porto Velho",
    "RR": "Boa Vista",
    "SC": "Florianópolis",
    "SP": "São Paulo",
    "SE": "Aracaju",
    "TO": "Palmas",
}

UF_REGIAO = {
    "AC": "Norte",
    "AP": "Norte",
    "AM": "Norte",
    "PA": "Norte",
    "RO": "Norte",
    "RR": "Norte",
    "TO": "Norte",
    "AL": "Nordeste",
    "BA": "Nordeste",
    "CE": "Nordeste",
    "MA": "Nordeste",
    "PB": "Nordeste",
    "PE": "Nordeste",
    "PI": "Nordeste",
    "RN": "Nordeste",
    "SE": "Nordeste",
    "GO": "Centro-Oeste",
    "MT": "Centro-Oeste",
    "MS": "Centro-Oeste",
    "DF": "Centro-Oeste",
    "ES": "Sudeste",
    "MG": "Sudeste",
    "RJ": "Sudeste",
    "SP": "Sudeste",
    "PR": "Sul",
    "RS": "Sul",
    "SC": "Sul",
}

# Nova leva com cobertura nacional, priorizando IDH dentro de cada região.
REGION_QUOTAS = {
    "Sudeste": 60,
    "Sul": 45,
    "Centro-Oeste": 25,
    "Nordeste": 17,
    "Norte": 3,
}


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6371
    p = math.pi / 180
    a = (
        math.sin((lat2 - lat1) * p / 2) ** 2
        + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lng2 - lng1) * p / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(a))


def fetch_json(url: str) -> list:
    req = urllib.request.Request(
        url,
        headers={"Accept-Encoding": "identity", "User-Agent": "ROCA/1.0"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        raw = resp.read()
        if raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
        return json.loads(raw.decode("utf-8"))


def load_population() -> dict[str, int]:
    if POP_CACHE.exists():
        cached = json.loads(POP_CACHE.read_text(encoding="utf-8"))
        return {row["cod"]: row["pop"] for row in cached}

    rows = []
    for row in fetch_json(
        "https://apisidra.ibge.gov.br/values/t/6579/n6/all/p/2024/v/9324"
    )[1:]:
        value = row["V"]
        if value in (None, "-", "...", ""):
            continue
        rows.append({"cod": str(row["D1C"]), "pop": int(value)})

    POP_CACHE.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return {row["cod"]: row["pop"] for row in rows}


def load_reference() -> list[dict]:
    pop = load_population()
    refs = []
    with open(REF, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            cod = str(row["cod7"])
            refs.append(
                {
                    "cod": cod,
                    "nome": row["municipio"],
                    "uf": row["UF"],
                    "idhm": float(row["idhm"]),
                    "lat": float(row["lat"]),
                    "lng": float(row["long"]),
                    "pop": pop.get(cod),
                }
            )
    return refs


def fmt_distance(km: float) -> str:
    return f"{km:.0f} km"


def fmt_time(km: float) -> str:
    minutes = max(15, round(km / DRIVE_SPEED_KMH * 60 / 15) * 15)
    if minutes < 60:
        return f"~{minutes} min"
    hours, mins = divmod(minutes, 60)
    if mins == 0:
        return f"~{hours}h"
    return f"~{hours}h{mins:02d}"


def nearest_in_set(origin: dict, pool: list[dict], max_km: float) -> tuple[dict, float] | None:
    best = None
    best_dist = max_km + 1
    for target in pool:
        dist = haversine(origin["lat"], origin["lng"], target["lat"], target["lng"])
        if dist <= max_km and dist < best_dist:
            best = target
            best_dist = dist
    if best is None:
        return None
    return best, best_dist


def build_candidates(existing: set[tuple[str, str]], refs: list[dict]) -> list[dict]:
    medium = [
        row
        for row in refs
        if row["pop"] and MEDIUM_MIN <= row["pop"] <= MEDIUM_MAX
    ]
    large = [
        row
        for row in refs
        if row["pop"] and (row["pop"] >= LARGE_MIN or row["nome"] == CAPITAIS.get(row["uf"]))
    ]

    candidates = []
    for row in refs:
        if not row["pop"] or row["pop"] > MAX_POP:
            continue
        if (row["nome"].upper(), row["uf"]) in existing:
            continue

        medium_hit = nearest_in_set(row, medium, MAX_MEDIUM_KM)
        large_hit = nearest_in_set(row, large, MAX_LARGE_KM)
        if not medium_hit or not large_hit:
            continue

        medium_city, medium_km = medium_hit
        large_city, large_km = large_hit
        candidates.append(
            {
                **row,
                "regiao": UF_REGIAO[row["uf"]],
                "medium_city": medium_city,
                "medium_km": medium_km,
                "large_city": large_city,
                "large_km": large_km,
            }
        )

    return candidates


def pick_by_region(candidates: list[dict]) -> list[dict]:
    selected = []
    used = set()

    for region, quota in REGION_QUOTAS.items():
        regional = sorted(
            [c for c in candidates if c["regiao"] == region],
            key=lambda c: (-c["idhm"], c["pop"], c["nome"]),
        )
        picked = 0
        for city in regional:
            key = (city["nome"].upper(), city["uf"])
            if key in used:
                continue
            selected.append(city)
            used.add(key)
            picked += 1
            if picked >= quota:
                break
        if picked < quota:
            raise SystemExit(
                f"Região {region}: apenas {picked} candidatas, esperado {quota}."
            )

    selected.sort(key=lambda c: (-c["idhm"], c["pop"], c["nome"]))
    return selected


def to_entry(city: dict, rank: int) -> dict:
    medium_name = city["medium_city"]["nome"]
    large_name = city["large_city"]["nome"]
    return {
        "rank": rank,
        "nome": city["nome"],
        "uf": city["uf"],
        "regiao": city["regiao"],
        "pop": city["pop"],
        "idh": round(city["idhm"], 3),
        "lat": round(city["lat"], 3),
        "lng": round(city["lng"], 3),
        "cidade_media": f"{medium_name} ({fmt_distance(city['medium_km'])})",
        "grande_centro": f"{large_name} ({fmt_time(city['large_km'])})",
        "nota": (
            f"IDH {city['idhm']:.3f} (Atlas 2010); perfil de cidade pequena com "
            "UPA, escola e comércio típicos para o porte — validar no local"
        ),
    }


def update_meta(payload: dict) -> None:
    cities = payload["cidadezinhas"]
    reg = Counter(c["regiao"] for c in cities)
    ss = reg["Sul"] + reg["Sudeste"]
    payload["meta"]["titulo"] = f"Top {len(cities)} cidadezinhas para dev remoto na roça"
    payload["meta"]["criterios"] = [
        "Até 15 mil habitantes (estimativa IBGE 2024)",
        "Até 50 km de cidade média (80–300 mil hab.)",
        "Até 2 h de grande centro (≥400 mil hab. ou capital)",
        "UPA, escola, farmácia, mercado e açougue (validar no local)",
        "Preferência por melhores índices de IDH (Atlas 2010)",
        "Chácara viável a 3–7 km do centro",
        "Internet via Starlink; fibra em expansão no interior",
    ]
    payload["meta"]["distribuicao"] = {
        "sul_sudeste": ss,
        "centro_oeste": reg["Centro-Oeste"],
        "nordeste": reg["Nordeste"],
        "norte": reg["Norte"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--force",
        action="store_true",
        help="Adicionar nova leva mesmo se o dataset já tiver 300 cidades",
    )
    args = parser.parse_args()

    payload = json.loads(DATA.read_text(encoding="utf-8"))
    existing_cities = payload["cidadezinhas"]
    if len(existing_cities) >= 300 and not args.force:
        raise SystemExit(
            f"Dataset já tem {len(existing_cities)} cidades. "
            "Use --force apenas se quiser adicionar outra leva."
        )
    existing_keys = {(c["nome"].upper(), c["uf"]) for c in existing_cities}
    start_rank = max(c.get("rank", idx + 1) for idx, c in enumerate(existing_cities))

    refs = load_reference()
    candidates = build_candidates(existing_keys, refs)
    picked = pick_by_region(candidates)
    if len(picked) != ADD_COUNT:
        raise SystemExit(f"Esperado {ADD_COUNT} novas cidades, obteve {len(picked)}.")

    new_entries = [to_entry(city, start_rank + idx + 1) for idx, city in enumerate(picked)]
    payload["cidadezinhas"] = existing_cities + new_entries
    update_meta(payload)

    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    reg = Counter(c["regiao"] for c in new_entries)
    print(f"Adicionadas {len(new_entries)} cidades (rank {start_rank + 1}–{start_rank + len(new_entries)})")
    print(f"Total agora: {len(payload['cidadezinhas'])}")
    print("Nova leva por região:", dict(reg))
    print(f"IDH: {new_entries[0]['nota'].split(';')[0]} … {new_entries[-1]['nota'].split(';')[0]}")


if __name__ == "__main__":
    main()
