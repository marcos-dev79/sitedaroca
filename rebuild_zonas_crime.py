#!/usr/bin/env python3
"""Gera data/zonas-crime.json: 30 gerais + 100 com pop ≥100 mil + Rio de Janeiro."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "data" / "zonas-crime.json"
REF = ROOT / "data" / "dados2010-ref.csv"
POP_CACHE = ROOT / "data" / "ibge-pop-2024.json"
HOM = ROOT / "data" / "cache" / "homicidios.csv"

TOP_GERAL = 30
TOP_100K = 100
MIN_POP_100K = 100_000
MIN_YEAR = 2022
RIO_IBGE = "3304557"


def load_pop() -> dict[str, int]:
    return {row["cod"]: row["pop"] for row in json.loads(POP_CACHE.read_text(encoding="utf-8"))}


def load_refs() -> dict[str, dict]:
    refs = {}
    with open(REF, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            refs[str(row["cod7"])] = {
                "nome": row["municipio"],
                "uf": row["UF"],
                "idh": float(row["idhm"]),
                "lat": float(row["lat"]),
                "lng": float(row["long"]),
            }
    return refs


def load_homicidios() -> dict[str, dict]:
    by_cod: dict[str, dict] = {}
    with open(HOM, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            year = int(row["year"])
            if year < MIN_YEAR:
                continue
            cod = str(row["ibge_code"]).zfill(7)
            rec = by_cod.get(cod)
            if rec is None or year > rec["ano"]:
                by_cod[cod] = {
                    "ano": year,
                    "homicidios": int(float(row["homicide_count"])),
                }
    return by_cod


def entry(cod: str, h: dict, r: dict, p: int) -> dict:
    return {
        "nome": r["nome"],
        "uf": r["uf"],
        "idh": round(r["idh"], 3),
        "taxa_homicidios_100k": round(h["homicidios"] / p * 100_000, 1),
        "pop": p,
        "homicidios": h["homicidios"],
        "homicidios_ano": h["ano"],
        "ibge": cod,
        "lat": round(r["lat"], 4),
        "lng": round(r["lng"], 4),
        "hidden": True,
    }


def main() -> None:
    pop = load_pop()
    refs = load_refs()
    hom = load_homicidios()

    ranked = []
    for cod, h in hom.items():
        p = pop.get(cod)
        r = refs.get(cod)
        if not p or not r:
            continue
        ranked.append(entry(cod, h, r, p))

    ranked.sort(key=lambda c: (-c["taxa_homicidios_100k"], -c["homicidios"], c["nome"]))

    top30 = [{**c, "grupo": "top30_geral"} for c in ranked[:TOP_GERAL]]
    seen = {c["ibge"] for c in top30}

    large = [
        {**c, "grupo": "top100_min_100k"}
        for c in ranked
        if c["pop"] >= MIN_POP_100K and c["ibge"] not in seen
    ][:TOP_100K]
    seen.update(c["ibge"] for c in large)

    selected = top30 + large

    rio = next((c for c in ranked if c["ibge"] == RIO_IBGE), None)
    if rio and rio["ibge"] not in seen:
        selected.append({**rio, "grupo": "referencia"})

    for i, c in enumerate(selected, 1):
        c["rank"] = i

    n30 = sum(1 for c in selected if c["grupo"] == "top30_geral")
    n100 = sum(1 for c in selected if c["grupo"] == "top100_min_100k")
    nref = sum(1 for c in selected if c["grupo"] == "referencia")

    payload = {
        "meta": {
            "titulo": f"{len(selected)} municípios — zonas de crime",
            "criterios": [
                f"{TOP_GERAL} maiores taxas do país, sem piso de população",
                f"Mais {TOP_100K} maiores taxas entre municípios ≥ {MIN_POP_100K:,} hab. (sem duplicar as 30)",
                "Rio de Janeiro incluso como referência, se ainda não estiver na lista",
                f"Taxa = óbitos SIM (X85–Y09, último ano ≥ {MIN_YEAR}) / pop. IBGE 2024 × 100 mil",
                "IDH municipal Atlas 2010",
            ],
            "fontes": [
                "SIM/DATASUS — homicídios por município",
                "IBGE Estimativas de população 2024",
                "Atlas IDHM 2010 (PNUD/IPEA/FJP)",
            ],
            "aviso": "Indicativo. As 30 gerais incluem municípios pequenos cuja taxa oscila com poucos óbitos.",
            "contagem": {"top30_geral": n30, "top100_min_100k": n100, "referencia": nref},
        },
        "zonas_crime": selected,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Gravado {OUT} com {len(selected)} municípios ({n30} geral + {n100} ≥100k + {nref} referência)")
    print("Top 5 geral:", [(c["nome"], c["uf"], c["pop"], c["taxa_homicidios_100k"]) for c in top30[:5]])
    if large:
        print("1ª ≥100k:", large[0]["nome"], large[0]["uf"], large[0]["taxa_homicidios_100k"])
    if rio:
        print("Rio:", rio["taxa_homicidios_100k"], "/100 mil", "já na lista" if rio["ibge"] in {c["ibge"] for c in top30 + large} else "adicionado")


if __name__ == "__main__":
    main()
