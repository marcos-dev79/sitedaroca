#!/usr/bin/env python3
"""Enriquece as 150 cidades originais com IDH e o mesmo padrão da expansão."""

import csv
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "cidadezinhas.json"
REF = ROOT / "data" / "dados2010-ref.csv"
POP_CACHE = ROOT / "data" / "ibge-pop-2024.json"
ORIGINAL_COUNT = 150
INFRA = (
    "perfil de cidade pequena com UPA, escola e comércio típicos "
    "para o porte — validar no local"
)
ALIASES = {
    ("SAO MIGUEL DO GOSTOSO", "RN"): "São Miguel de Touros",
}


def norm(text: str) -> str:
    stripped = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    cleaned = stripped.upper().replace("D'", "D ").replace("-", " ")
    return " ".join(cleaned.split())


def load_refs() -> dict[tuple[str, str], dict]:
    pop = {row["cod"]: row["pop"] for row in json.loads(POP_CACHE.read_text(encoding="utf-8"))}
    refs = {}
    with open(REF, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            refs[(norm(row["municipio"]), row["UF"])] = {
                "idhm": float(row["idhm"]),
                "pop": pop.get(str(row["cod7"])),
            }
    return refs


def find_ref(city: dict, refs: dict) -> dict | None:
    alias = ALIASES.get((norm(city["nome"]), city["uf"]))
    name = alias or city["nome"]
    return refs.get((norm(name), city["uf"]))


def clean_note(note: str) -> str:
    note = note.strip()
    while True:
        stripped = re.sub(
            r"^(IDH municipal não disponível[^\n;]*|IDH\s+[0-9.,]+\s*\([^)]*\))\s*;\s*",
            "",
            note,
            count=1,
            flags=re.IGNORECASE,
        )
        if stripped == note:
            break
        note = stripped
    if note.lower().startswith("nota:"):
        note = note.split(":", 1)[1].strip()
    idx = note.lower().rfind(INFRA.lower())
    if idx >= 0:
        note = note[:idx].rstrip(" ;")
    return note


def build_note(original: str, idhm: float | None) -> str:
    base = clean_note(original)
    if INFRA.lower() in base.lower():
        body = base
    elif base:
        body = f"{base}; {INFRA}"
    else:
        body = INFRA
    if idhm is None:
        return f"IDH municipal não disponível no Atlas 2010; {body}"
    return f"IDH {idhm:.3f} (Atlas 2010); {body}"


def ordered(city: dict) -> dict:
    out = {
        "rank": city["rank"],
        "nome": city["nome"],
        "uf": city["uf"],
        "regiao": city["regiao"],
        "pop": city["pop"],
        "lat": city["lat"],
        "lng": city["lng"],
        "cidade_media": city["cidade_media"],
        "grande_centro": city["grande_centro"],
        "nota": city["nota"],
    }
    if "idh" in city:
        # IDH logo após região/pop, como dado estruturado
        items = list(out.items())
        out = dict(items[:5] + [("idh", city["idh"])] + items[5:])
    return out


def main():
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    refs = load_refs()
    cities = payload["cidadezinhas"]
    missing = []

    for city in cities[:ORIGINAL_COUNT]:
        ref = find_ref(city, refs)
        idhm = ref["idhm"] if ref else None
        if ref and ref["pop"]:
            city["pop"] = ref["pop"]
        if idhm is not None:
            city["idh"] = round(idhm, 3)
        else:
            city.pop("idh", None)
            missing.append(f"{city['nome']}/{city['uf']}")
        city["nota"] = build_note(city.get("nota", ""), idhm)

    for city in cities[ORIGINAL_COUNT:]:
        ref = find_ref(city, refs)
        if ref:
            city["idh"] = round(ref["idhm"], 3)
        else:
            city.pop("idh", None)

    payload["cidadezinhas"] = [ordered(c) for c in cities]
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with_idh = sum(1 for c in payload["cidadezinhas"][:ORIGINAL_COUNT] if "idh" in c)
    print(f"Originais enriquecidas: {with_idh}/{ORIGINAL_COUNT} com IDH")
    if missing:
        print("Sem IDH:", ", ".join(missing))


if __name__ == "__main__":
    main()
