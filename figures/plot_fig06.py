# -*- coding: utf-8 -*-
"""Figure 6 from plot-ready panel tables only."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
from common import apply_style, load_world, panel_label, smooth_grid  # noqa: E402

DATA = HERE
SHARED = HERE
OUT = HERE / "fig06.png"


def _grid_to_raster(df: pd.DataFrame):
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
    return z, [-180, 180, -90, 90]


def _outside_map(ax, grid: pd.DataFrame, unit: str) -> None:
    load_world(ax, SHARED)
    sub = grid[grid["unit"] == unit]
    if sub.empty:
        ax.set_title(f"No outside-hotspot cells | {unit}")
        return
    z, extent = _grid_to_raster(sub)
    z = smooth_grid(z, sigma=0.8)
    ax.imshow(z, origin="lower", extent=extent, cmap="YlOrRd", aspect="auto", interpolation="bilinear", zorder=1)
    ax.set_xlim(-180, 180)
    ax.set_ylim(-60, 85)
    ax.set_title(f"High entropy outside BSRI hotspot | {unit}")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")


def _scatter(ax, points: pd.DataFrame, corr: pd.DataFrame, unit: str) -> None:
    sub = points[points["unit"] == unit]
    ax.scatter(sub["BSRI"], sub["risk_entropy"], s=4, alpha=0.15, color="#4477AA", edgecolors="none")
    crow = corr[corr["unit"] == unit].iloc[0]
    ax.text(
        0.05,
        0.95,
        f"n={int(crow['n'])}\nSpearman r={float(crow['spearman_r']):.3f}\nPearson r={float(crow['pearson_r']):.3f}",
        transform=ax.transAxes,
        va="top",
        fontsize=9,
        bbox=dict(facecolor="white", alpha=0.85, edgecolor="none"),
    )
    ax.set_xlabel("BSRI")
    ax.set_ylabel("Risk entropy")
    ax.set_title(unit)


def main() -> Path:
    apply_style()
    grid = pd.read_csv(DATA / "fig06_panel_AC_outside_hotspot_grid.csv", encoding="utf-8-sig")
    points = pd.read_csv(DATA / "fig06_panel_BD_scatter_points.csv", encoding="utf-8-sig")
    corr = pd.read_csv(DATA / "fig06_panel_BD_correlation.csv", encoding="utf-8-sig")
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    for r, (unit, labs) in enumerate([("n/L", ("A", "B")), ("n/kg", ("C", "D"))]):
        _outside_map(axes[r, 0], grid, unit)
        panel_label(axes[r, 0], labs[0])
        _scatter(axes[r, 1], points, corr, unit)
        panel_label(axes[r, 1], labs[1])
    fig.tight_layout()
    fig.savefig(OUT)
    plt.close(fig)
    print("wrote", OUT)
    return OUT


if __name__ == "__main__":
    main()
