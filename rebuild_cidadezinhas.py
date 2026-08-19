#!/usr/bin/env python3
"""Reconstrói cidadezinhas.json com critérios IBGE + violência + infraestrutura."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "cidadezinhas.json"
REF = ROOT / "data" / "dados2010-ref.csv"
POP_CACHE = ROOT / "data" / "ibge-pop-2024.json"
CACHE = ROOT / "data" / "cache"

MAX_CANDIDATES = 1000
MAX_POP = 20_000
MEDIUM_MIN_POP = 150_000
MEDIUM_MIN_KM = 30
MEDIUM_MAX_KM = 50
LARGE_MIN_POP = 500_000
DRIVE_KMH = 80
MAX_LARGE_HOURS = 1.5
MAX_LARGE_KM = DRIVE_KMH * MAX_LARGE_HOURS  # 120 km
MAX_TAXA_HOMICIDIO = 15.0

UF_REGIAO = {
    "AC": "Norte", "AP": "Norte", "AM": "Norte", "PA": "Norte", "RO": "Norte",
    "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste",
    "PB": "Nordeste", "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste", "SE": "Nordeste",
    "GO": "Centro-Oeste", "MT": "Centro-Oeste", "MS": "Centro-Oeste", "DF": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
}


def haversine(lat1, lng1, lat2, lng2) -> float:
    r = 6371
    p = math.pi / 180
    a = (
        math.sin((lat2 - lat1) * p / 2) ** 2
        + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lng2 - lng1) * p / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def fmt_km(km: float) -> str:
    return f"{km:.0f} km"


def fmt_time(km: float) -> str:
    minutes = max(15, int(round(km / DRIVE_KMH * 60 / 15) * 15))
    h, m = divmod(minutes, 60)
    if h == 0:
        return f"~{m} min"
    if m == 0:
        return f"~{h}h"
    return f"~{h}h{m:02d}"


def yes(val: str) -> bool:
    v = (val or "").strip().lower()
    return v in {"sim", "s", "1", "true"}


def load_pop() -> dict[str, int]:
    return {row["cod"]: row["pop"] for row in json.loads(POP_CACHE.read_text(encoding="utf-8"))}


def load_refs(pop: dict[str, int]) -> list[dict]:
    rows = []
    with open(REF, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cod = str(row["cod7"])
            p = pop.get(cod)
            if not p:
                continue
            rows.append({
                "cod": cod,
                "nome": row["municipio"],
                "uf": row["UF"],
                "regiao": UF_REGIAO.get(row["UF"], ""),
                "idh": float(row["idhm"]),
                "idh_renda": float(row["idhm_renda"]),
                "idh_longev": float(row["idhm_longev"]),
                "idh_edu": float(row["idhm_edu"]),
                "lat": float(row["lat"]),
                "lng": float(row["long"]),
                "pop": p,
            })
    return rows


def nearest(origin: dict, pool: list[dict], min_km: float, max_km: float):
    best = None
    best_d = max_km + 1
    for t in pool:
        if t["cod"] == origin["cod"]:
            continue
        d = haversine(origin["lat"], origin["lng"], t["lat"], t["lng"])
        if min_km <= d <= max_km and d < best_d:
            best, best_d = t, d
    return (best, best_d) if best else None


def load_csv_by_cod(path: Path) -> dict[str, dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return {row["CodMun"]: row for row in csv.DictReader(f)}


def load_homicidios() -> dict[str, dict]:
    by_cod: dict[str, dict] = {}
    with open(CACHE / "homicidios.csv", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            year = int(row["year"])
            if year < 2022:
                continue
            cod = str(row["ibge_code"]).zfill(7)
            rec = by_cod.get(cod)
            if rec is None or year > rec["ano"]:
                by_cod[cod] = {
                    "ano": year,
                    "homicidios": int(float(row["homicide_count"])),
                    "taxa_homicidios_100k": float(row["homicide_rate_per_100k"]),
                }
    return by_cod


def load_cnes_flags() -> dict[str, dict]:
    path = CACHE / "cnes_flags.json"
    if not path.exists():
        print("CNES flags ausentes — rode o parse do zip DATASUS")
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    print(f"CNES: {len(raw)} municípios")
    return raw


def pad7_from6(cod6: str, refs: list[dict]) -> dict[str, str]:
    m = {}
    for r in refs:
        m[r["cod"][:6]] = r["cod"]
    return m


def build_saude(row: dict | None, cnes: dict, taxa: float | None) -> str:
    parts = []
    if row:
        if yes(row.get("Msau451", "")):
            parts.append("emergência 24h municipal (IBGE MUNIC)")
        elif yes(row.get("Msau452", "")):
            parts.append("emergência 24h em outro serviço público")
        if yes(row.get("Msau29", "")):
            eq = row.get("Msau2911") or ""
            parts.append(f"Saúde da Família ({eq} equipes)" if eq not in {"", "-"} else "Saúde da Família")
        if yes(row.get("Msau25", "")):
            parts.append("estabelecimento de saúde da gestão municipal")
    if cnes.get("upa"):
        parts.append("UPA no município (CNES)")
    if cnes.get("pronto_socorro"):
        parts.append("pronto-socorro (CNES)")
    if cnes.get("farmacia"):
        parts.append("farmácia cadastrada no CNES")
    if not parts:
        parts.append("infraestrutura de saúde não confirmada nas bases")
    return "; ".join(parts)


def build_educacao(row: dict | None) -> str:
    if not row:
        return "dado educacional municipal não disponível"
    org = row.get("Medu01") or ""
    if org.startswith("Não") or org in {"", "-"}:
        return "sem estrutura municipal de educação declarada (MUNIC 2021)"
    bits = [f"órgão de educação: {org}"]
    if yes(row.get("Medu14", "")):
        bits.append("conselho municipal de educação")
    if yes(row.get("Medu35", "")):
        bits.append("conselho de alimentação escolar")
    if yes(row.get("Medu501", "")):
        bits.append("demanda de pré-escola mapeada")
    return "; ".join(bits)


def build_seguranca(row: dict | None, hom: dict | None) -> str:
    bits = []
    if hom:
        bits.append(
            f"taxa de homicídios {hom['taxa_homicidios_100k']:.1f}/100 mil hab. "
            f"({hom['homicidios']} óbito{'s' if hom['homicidios'] != 1 else ''} em {hom['ano']}; SIM/DATASUS)"
        )
    else:
        bits.append("taxa de homicídios não disponível no SIM 2022–2024")
    if row:
        if yes(row.get("MSEG161", "")):
            bits.append("delegacia de polícia civil (MUNIC 2023)")
        else:
            bits.append("sem delegacia de polícia civil declarada (MUNIC 2023)")
    return "; ".join(bits) if bits else "sem dado de segurança"


def main():
    pop = load_pop()
    refs = load_refs(pop)
    medium = [r for r in refs if r["pop"] >= MEDIUM_MIN_POP]
    large = [r for r in refs if r["pop"] >= LARGE_MIN_POP]
    print(f"Municípios IBGE: {len(refs)} | médias ≥150k: {len(medium)} | grandes ≥500k: {len(large)}")

    geo = []
    small = [r for r in refs if r["pop"] <= MAX_POP]
    for r in small:
        med = nearest(r, medium, MEDIUM_MIN_KM, MEDIUM_MAX_KM)
        big = nearest(r, large, 0, MAX_LARGE_KM)
        if not med or not big:
            continue
        geo.append({**r, "medium": med[0], "medium_km": med[1], "large": big[0], "large_km": big[1]})
    geo.sort(key=lambda c: (-c["idh"], c["pop"], c["nome"]))
    print(f"Passo 1 (geografia): {len(geo)} candidatas")
    geo = geo[:MAX_CANDIDATES]
    print(f"Limitadas a {len(geo)}")

    hom = load_homicidios()
    saude = load_csv_by_cod(CACHE / "munic2021_saude.csv")
    edu = load_csv_by_cod(CACHE / "munic2021_educacao.csv")
    seg = load_csv_by_cod(CACHE / "munic2023_seguranca.csv")
    cnes_raw = load_cnes_flags()
    map6 = pad7_from6("", refs)
    # rebuild map6 properly
    map6 = {r["cod"][:6]: r["cod"] for r in refs}
    cnes = {}
    for c6, flags in cnes_raw.items():
        c7 = map6.get(c6)
        if c7:
            cnes[c7] = flags

    kept = []
    dropped = Counter()
    for c in geo:
        h = hom.get(c["cod"])
        srow = saude.get(c["cod"])
        erow = edu.get(c["cod"])
        grow = seg.get(c["cod"])
        cn = cnes.get(c["cod"], {})

        has_upa = bool(cn.get("upa") or (srow and yes(srow.get("Msau451", ""))))
        has_escola = bool(erow and erow.get("Medu01") and not str(erow.get("Medu01")).startswith("Não"))
        has_delegacia = bool(grow and yes(grow.get("MSEG161", "")))
        has_farmacia = bool(cn.get("farmacia"))
        has_mercado = has_farmacia and c["pop"] >= 2000
        has_correios = c["pop"] >= 2000

        if h is not None and h["taxa_homicidios_100k"] > MAX_TAXA_HOMICIDIO:
            dropped[f"homicidio>{int(MAX_TAXA_HOMICIDIO)}"] += 1
            continue
        if not has_upa:
            dropped["sem_upa_emergencia"] += 1
            continue
        if not has_escola:
            dropped["sem_escola"] += 1
            continue
        if not has_delegacia:
            dropped["sem_delegacia"] += 1
            continue
        if not has_farmacia:
            dropped["sem_farmacia"] += 1
            continue
        if not has_mercado:
            dropped["sem_mercado"] += 1
            continue
        if not has_correios:
            dropped["sem_correios"] += 1
            continue

        kept.append({
            **c,
            "hom": h,
            "saude_txt": build_saude(srow, cn, None),
            "educacao_txt": build_educacao(erow),
            "seguranca_txt": build_seguranca(grow, h),
            "infra": {
                "upa_ou_emergencia_24h": has_upa,
                "escola": has_escola,
                "mercado": has_mercado,
                "farmacia": has_farmacia,
                "delegacia": has_delegacia,
                "correios": has_correios,
            },
        })

    kept.sort(key=lambda c: (-c["idh"], c["pop"], c["nome"]))
    print(f"Passo 2: {len(kept)} após filtros")
    print("Descarte:", dict(dropped))

    entries = []
    for i, c in enumerate(kept, 1):
        entries.append({
            "rank": i,
            "nome": c["nome"],
            "uf": c["uf"],
            "regiao": c["regiao"],
            "pop": c["pop"],
            "idh": round(c["idh"], 3),
            "idh_renda": round(c["idh_renda"], 3),
            "idh_longev": round(c["idh_longev"], 3),
            "idh_edu": round(c["idh_edu"], 3),
            "ibge": c["cod"],
            "lat": round(c["lat"], 4),
            "lng": round(c["lng"], 4),
            "cidade_media": f"{c['medium']['nome']} ({fmt_km(c['medium_km'])})",
            "grande_centro": f"{c['large']['nome']} ({fmt_time(c['large_km'])}, {fmt_km(c['large_km'])})",
            "homicidios": None if not c["hom"] else c["hom"]["homicidios"],
            "homicidios_ano": None if not c["hom"] else c["hom"]["ano"],
            "taxa_homicidios_100k": None if not c["hom"] else round(c["hom"]["taxa_homicidios_100k"], 1),
            "saude": c["saude_txt"],
            "educacao": c["educacao_txt"],
            "seguranca": c["seguranca_txt"],
            "infra": c["infra"],
            "nota": (
                f"IDH {c['idh']:.3f} (Atlas 2010)"
                + (
                    f"; homicídios {c['hom']['taxa_homicidios_100k']:.1f}/100 mil ({c['hom']['ano']})"
                    if c["hom"]
                    else "; taxa de homicídios indisponível no SIM 2022–2024"
                )
                + "; validar comércio e Correios no local"
            ),
        })

    reg = Counter(e["regiao"] for e in entries)
    payload = {
        "meta": {
            "titulo": f"{len(entries)} cidadezinhas para dev remoto na roça",
            "criterios": [
                "Até 20 mil habitantes (IBGE 2024)",
                "Entre 30 e 50 km de cidade média (≥150 mil hab.)",
                "Até 1h30 de cidade grande (≥500 mil hab.; ~120 km a 80 km/h)",
                "UPA no CNES (tipo 73) ou emergência 24h municipal (MUNIC 2021 MSAU451)",
                "Escola: estrutura educacional municipal (MUNIC 2021)",
                "Delegacia de polícia civil (MUNIC 2023 MSEG161)",
                "Farmácia ativa no CNES (tipo 43)",
                "Mercado/Correios: sede municipal ≥2 mil hab. com farmácia (não há cadastro nacional aberto de mercearias/agências)",
                f"Taxa de homicídios ≤ {int(MAX_TAXA_HOMICIDIO)}/100 mil (SIM/DATASUS 2022–2024); municípios sem série não foram descartados por violência",
            ],
            "fontes": [
                "IBGE Estimativas de população 2024 (SIDRA 6579)",
                "IBGE MUNIC 2021 (saúde e educação) e MUNIC 2023 (segurança pública)",
                "Atlas IDHM 2010 (PNUD/IPEA/FJP)",
                "SIM/DATASUS — homicídios por município (X85–Y09)",
                "CNES/DATASUS — estabelecimentos (UPA, farmácia), se disponível",
            ],
            "distribuicao": {
                "sul_sudeste": reg["Sul"] + reg["Sudeste"],
                "centro_oeste": reg["Centro-Oeste"],
                "nordeste": reg["Nordeste"],
                "norte": reg["Norte"],
            },
            "aviso": "Isto não é conselho profissional. Faça sua própria pesquisa e valide no local.",
        },
        "cidadezinhas": entries,
    }
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Gravado {DATA} com {len(entries)} cidades")
    if entries:
        print("Top 5 IDH:", [(e["nome"], e["uf"], e["idh"]) for e in entries[:5]])
        print("Regiões:", dict(reg))


if __name__ == "__main__":
    main()
