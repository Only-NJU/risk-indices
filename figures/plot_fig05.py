# -*- coding: utf-8 -*-
"""Figure 5 from plot-ready panel tables only."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

HERE = Path(__file__).resolve().parent
from common import apply_style, load_world, panel_label, smooth_grid  # noqa: E402

DATA = HERE
SHARED = HERE
OUT = HERE / "fig05.png"
CLASS_ORDER = ["data-sparse", "composition-complex", "mixed"]
CLASS_COLORS = {
    "data-sparse": "#4C78A8",
    "composition-complex": "#F58518",
    "mixed": "#54A24B",
}


def _grid_to_raster(df: pd.DataFrame):
    """Rebuild 2° raster from lon/lat centers."""
    lon = df["lon_center"].to_numpy(dtype=float)
    lat = df["lat_center"].to_numpy(dtype=float)
    val = df["value"].to_numpy(dtype=float)
    lon_edges = np.arange(-180, 180 + 2.0, 2.0)
    lat_edges = np.arange(-90, 90 + 2.0, 2.0)
    z = np.full((len(lat_edges) - 1, len(lon_edges) - 1), np.nan)
    lon_i = np.clip(((lon + 180) / 2.0).astype(int), 0, z.shape[1] - 1)
    lat_i = np.clip(((lat + 90) / 2.0).astype(int), 0, z.shape[0] - 1)
    for i, j, v in zip(lat_i, lon_i, val):
        z[i, j] = v
    extent = [-180, 180, -90, 90]
    return z, extent


def _map(ax, grid: pd.DataFrame, title: str, cmap: str, cbar_label: str):
    load_world(ax, SHARED)
    z, extent = _grid_to_raster(grid)
    z = smooth_grid(z, sigma=1.2)
    im = ax.imshow(
        z,
        origin="lower",
        extent=extent,
        cmap=cmap,
        aspect="auto",
        interpolation="bilinear",
        vmin=np.nanpercentile(z, 5),
        vmax=np.nanpercentile(z, 95),
        zorder=1,
    )
    ax.set_xlim(-180, 180)
    ax.set_ylim(-60, 85)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(title, fontsize=11)
    return im


def _raincloud(ax, df: pd.DataFrame, unit: str):
    comps = list(df["compartment_main"].value_counts().index)
    data = [df.loc[df["compartment_main"] == c, "BSRI"].to_numpy() for c in comps]
    n = len(comps)
    pmat = np.ones((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            pmat[i, j] = pmat[j, i] = mannwhitneyu(data[i], data[j], alternative="two-sided").pvalue
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    letters = [""] * n
    next_i = 0
    for i in range(n):
        if letters[i]:
            continue
        letter = alphabet[next_i]
        next_i += 1
        letters[i] += letter
        for j in range(i + 1, n):
            if pmat[i, j] >= 0.05 and letter not in letters[j]:
                letters[j] += letter

    parts = ax.violinplot(data, positions=range(n), showmeans=False, showmedians=False, showextrema=False)
    for b in parts["bodies"]:
        b.set_facecolor("#9ecae1")
        b.set_alpha(0.7)
    ax.boxplot(
        data,
        positions=range(n),
        widths=0.18,
        showfliers=False,
        patch_artist=True,
        boxprops=dict(facecolor="white"),
        medianprops=dict(color="black"),
    )
    rng = np.random.default_rng(0)
    for i, y in enumerate(data):
        x = rng.normal(i, 0.04, size=len(y))
        ax.scatter(x, y, s=3, color="#333333", alpha=0.15, zorder=2)
        ax.text(i, np.nanmax(y) + 0.002, letters[i], ha="center", fontsize=8)
    ax.set_xticks(range(n))
    ax.set_xticklabels(comps, rotation=60, ha="right", fontsize=7)
    ax.set_ylabel("BSRI")
    ax.set_title(unit)
    ax.text(0.98, 0.98, unit, transform=ax.transAxes, ha="right", va="top")


def _attr_bar(ax, shares: pd.DataFrame, unit: str):
    sub = shares[shares["unit"] == unit].set_index("class")
    vals = [float(sub.loc[k, "percent"]) if k in sub.index else 0.0 for k in CLASS_ORDER]
    bars = ax.bar(CLASS_ORDER, vals, color=[CLASS_COLORS[k] for k in CLASS_ORDER])
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1, f"{v:.1f}%", ha="center", fontsize=8)
    ax.set_ylim(0, max(vals) * 1.25 if vals else 1)
    ax.set_ylabel("Share of high-entropy sites (%)")
    ax.set_title(unit)
    ax.tick_params(axis="x", rotation=20)


def main() -> Path:
    apply_style()
    grid = pd.read_csv(DATA / "fig05_panel_AD_map_grid.csv", encoding="utf-8-sig")
    rain = pd.read_csv(DATA / "fig05_panel_EF_bsri_by_compartment.csv", encoding="utf-8-sig")
    shares = pd.read_csv(DATA / "fig05_panel_GH_attribution_shares.csv", encoding="utf-8-sig")

    fig = plt.figure(figsize=(16, 14))
    gs = fig.add_gridspec(3, 4, height_ratios=[1.1, 1.1, 1.0], hspace=0.35, wspace=0.30)

    ax = fig.add_subplot(gs[0, 0:2])
    im1 = _map(ax, grid[(grid["unit"] == "n/L") & (grid["metric"] == "BSRI")], "BSRI | n/L", "magma", "BSRI")
    panel_label(ax, "A")
    ax = fig.add_subplot(gs[0, 2:4])
    _map(ax, grid[(grid["unit"] == "n/kg") & (grid["metric"] == "BSRI")], "BSRI | n/kg", "magma", "BSRI")
    panel_label(ax, "B")
    ax = fig.add_subplot(gs[1, 0:2])
    im3 = _map(
        ax,
        grid[(grid["unit"] == "n/L") & (grid["metric"] == "risk_entropy")],
        "Risk entropy | n/L",
        "viridis",
        "Risk entropy",
    )
    panel_label(ax, "C")
    ax = fig.add_subplot(gs[1, 2:4])
    _map(
        ax,
        grid[(grid["unit"] == "n/kg") & (grid["metric"] == "risk_entropy")],
        "Risk entropy | n/kg",
        "viridis",
        "Risk entropy",
    )
    panel_label(ax, "D")
    if im1 is not None:
        fig.colorbar(im1, ax=fig.axes[0], fraction=0.03, pad=0.01, label="BSRI")
    if im3 is not None:
        fig.colorbar(im3, ax=fig.axes[2], fraction=0.03, pad=0.01, label="Risk entropy")

    ax = fig.add_subplot(gs[2, 0])
    _raincloud(ax, rain[rain["unit"] == "n/L"], "n/L")
    panel_label(ax, "E")
    ax = fig.add_subplot(gs[2, 1])
    _raincloud(ax, rain[rain["unit"] == "n/kg"], "n/kg")
    panel_label(ax, "F")

    ax = fig.add_subplot(gs[2, 2])
    _attr_bar(ax, shares, "n/L")
    panel_label(ax, "G")
    ax = fig.add_subplot(gs[2, 3])
    _attr_bar(ax, shares, "n/kg")
    panel_label(ax, "H")

    fig.savefig(OUT)
    plt.close(fig)
    print("wrote", OUT)
    return OUT


if __name__ == "__main__":
    main()
