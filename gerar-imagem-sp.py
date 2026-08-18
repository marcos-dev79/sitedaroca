#!/usr/bin/env python3
"""Gera imagem estática com 100 cidadezinhas de SP (pop. ≤ 15 mil)."""

import gzip
import json
import os
import urllib.request
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "cidadezinhas.json"
IBGE_CACHE = ROOT / "data" / "ibge-sp-pop-2024.json"
OUT = ROOT / "assets" / "img" / "cidades-sp-100.png"
OUT_DIST = ROOT / "dist" / "assets" / "img" / "cidades-sp-100.png"

MAX_POP = 15_000
TARGET = 100
SIDRA_URL = "https://apisidra.ibge.gov.br/values/t/6579/n6/in%20n3%2035/p/2024/v/9324"

BG = "#0f172a"
PANEL = "#1e293b"
BORDER = "#334155"
TEXT = "#e2e8f0"
MUTED = "#94a3b8"
ACCENT = "#4ade80"


def fetch_json(url: str) -> list:
    req = urllib.request.Request(url, headers={"Accept-Encoding": "identity", "User-Agent": "ROCA/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read()
        if raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
        return json.loads(raw.decode("utf-8"))


def load_curated_sp() -> list[dict]:
    with open(DATA, encoding="utf-8") as f:
        return [c for c in json.load(f)["cidadezinhas"] if c["uf"] == "SP"]


def load_ibge_sp() -> list[tuple[str, int]]:
    if IBGE_CACHE.exists():
        cached = json.loads(IBGE_CACHE.read_text(encoding="utf-8"))
        return [(row["nome"], row["pop"]) for row in cached]

    rows = []
    for row in fetch_json(SIDRA_URL)[1:]:
        nome = row["D1N"].split(" - ")[0].strip()
        pop = int(row["V"])
        rows.append({"nome": nome, "pop": pop})

    IBGE_CACHE.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return [(row["nome"], row["pop"]) for row in rows]


def select_cities(curated: list[dict], ibge: list[tuple[str, int]]) -> list[tuple[str, int]]:
    under = [(n, p) for n, p in ibge if p <= MAX_POP]
    selected: list[tuple[str, int]] = []
    seen: set[str] = set()

    for city in sorted(curated, key=lambda c: c.get("rank", 999)):
        key = city["nome"].upper()
        if key in seen:
            continue
        pop = next((p for n, p in under if n.upper() == key), city["pop"])
        if pop <= MAX_POP:
            selected.append((city["nome"], pop))
            seen.add(key)

    for nome, pop in sorted(under, key=lambda x: (x[1], x[0])):
        if len(selected) >= TARGET:
            break
        if nome.upper() in seen:
            continue
        selected.append((nome, pop))
        seen.add(nome.upper())

    return selected[:TARGET]


def fmt_pop(pop: int) -> str:
    return f"{pop:,}".replace(",", ".")


def draw(cities: list[tuple[str, int]]) -> None:
    cols = 5
    rows = (len(cities) + cols - 1) // cols
    fig_w, fig_h = 20, 28
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows + 2.2)
    ax.axis("off")

    ax.text(
        cols / 2,
        rows + 1.55,
        "100 Cidadezinhas de SP para Dev Remoto na Roça",
        ha="center",
        va="center",
        fontsize=28,
        fontweight="bold",
        color=TEXT,
    )
    ax.text(
        cols / 2,
        rows + 0.85,
        "Municípios com até ~15 mil habitantes · População estimada IBGE 2024",
        ha="center",
        va="center",
        fontsize=14,
        color=MUTED,
    )

    cell_h = 1.0
    cell_w = 1.0
    pad_x = 0.08
    pad_y = 0.06

    for i, (nome, pop) in enumerate(cities):
        col = i % cols
        row = rows - 1 - (i // cols)
        x = col + pad_x
        y = row + pad_y

        rect = mpatches.FancyBboxPatch(
            (col + 0.04, row + 0.04),
            cell_w - 0.08,
            cell_h - 0.08,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            linewidth=1,
            edgecolor=BORDER,
            facecolor=PANEL,
        )
        ax.add_patch(rect)

        ax.text(
            x + 0.04,
            y + 0.62,
            f"{i + 1}. {nome}",
            ha="left",
            va="center",
            fontsize=11.5,
            fontweight="semibold",
            color=TEXT,
        )
        ax.text(
            x + 0.04,
            y + 0.28,
            f"{fmt_pop(pop)} hab.",
            ha="left",
            va="center",
            fontsize=10.5,
            color=ACCENT,
        )

    ax.text(
        cols / 2,
        -0.35,
        "Dev Remoto na Roça · Critério principal: até 15 mil hab. · Valide infraestrutura no local",
        ha="center",
        va="center",
        fontsize=11,
        color=MUTED,
    )

    fig.savefig(OUT, dpi=150, facecolor=BG, bbox_inches="tight", pad_inches=0.35)
    plt.close(fig)


def main():
    curated = load_curated_sp()
    ibge = load_ibge_sp()
    cities = select_cities(curated, ibge)
    if len(cities) < TARGET:
        raise SystemExit(f"Esperado {TARGET} cidades, obteve {len(cities)}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    draw(cities)
    OUT_DIST.parent.mkdir(parents=True, exist_ok=True)
    OUT_DIST.write_bytes(OUT.read_bytes())
    print(f"Imagem gerada: {OUT}")
    print(f"  Cópia em: {OUT_DIST}")
    print(f"  {len(cities)} municípios de SP (pop. ≤ {MAX_POP:,})")


if __name__ == "__main__":
    main()
