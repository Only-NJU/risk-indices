# -*- coding: utf-8 -*-
"""Figure 1 from plot-ready panel tables only."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image

HERE = Path(__file__).resolve().parent
from common import apply_style, panel_label  # noqa: E402

DATA = HERE
SHARED = HERE
OUT = HERE / "fig01.png"
RECOMMENDED_N = 5


def _draw_unit(ax, curves: pd.DataFrame, wilcox: pd.DataFrame, unit: str) -> None:
    sub = curves[curves["unit"] == unit].sort_values("n_neighbors")
    ax.fill_between(sub["n_neighbors"], sub["pielou_ci_low"], sub["pielou_ci_high"], color="#4477AA", alpha=0.18)
    ax.plot(sub["n_neighbors"], sub["pielou_mean"], "-o", color="#4477AA", ms=4, lw=1.6, label="Pielou J'")
    ax2 = ax.twinx()
    ax2.plot(sub["n_neighbors"], sub["shannon_mean"], "-s", color="#228833", ms=3.5, lw=1.3, label="Shannon H'")
    ax2.set_ylabel("Shannon H'", color="#228833")
    ax.axvline(RECOMMENDED_N, color="#666666", ls="--", lw=1.0)
    w = wilcox[wilcox["unit"] == unit].sort_values("n_upper")
    if not w.empty:
        y0, y1 = ax.get_ylim()
        band = (y1 - y0) * 0.12
        ax.set_ylim(y0, y1 + band)
        yb = y1 + band * 0.35
        for _, row in w.iterrows():
            ax.text((row["n_lower"] + row["n_upper"]) / 2, yb, row["stars"], ha="center", va="bottom", fontsize=7)
    ax.set_xlabel("k (nearest neighbours)")
    ax.set_ylabel("Pielou J'")
    ax.set_xticks(range(2, 17, 2))
    ax.text(0.98, 0.02, unit, transform=ax.transAxes, ha="right", va="bottom", fontsize=11)


def main() -> Path:
    apply_style()
    curves = pd.read_csv(DATA / "fig01_panel_BC_curves.csv", encoding="utf-8-sig")
    wilcox = pd.read_csv(DATA / "fig01_panel_BC_wilcoxon.csv", encoding="utf-8-sig")
    fig = plt.figure(figsize=(14, 7))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.15, 1.0], wspace=0.25, hspace=0.35)
    ax_a = fig.add_subplot(gs[:, 0])
    ax_a.imshow(Image.open(DATA / "fig01_panel_A_prisma.tif"))
    ax_a.axis("off")
    panel_label(ax_a, "A", x=0.0, y=1.02)
    ax_b = fig.add_subplot(gs[0, 1])
    _draw_unit(ax_b, curves, wilcox, "n/L")
    panel_label(ax_b, "B")
    ax_c = fig.add_subplot(gs[1, 1])
    _draw_unit(ax_c, curves, wilcox, "n/kg")
    panel_label(ax_c, "C")
    fig.savefig(OUT)
    plt.close(fig)
    print("wrote", OUT)
    return OUT


if __name__ == "__main__":
    main()
