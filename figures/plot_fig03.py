# -*- coding: utf-8 -*-
"""Figure 3 from plot-ready panel tables only."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
from common import INDEX_ORDER, apply_style, index_color, panel_label  # noqa: E402

DATA = HERE
SHARED = HERE
OUT = HERE / "fig03.png"


def main() -> Path:
    apply_style()
    rounds = pd.read_csv(DATA / "fig03_panel_AF_mean_rank_rounds.csv", encoding="utf-8-sig")
    letters = pd.read_csv(DATA / "fig03_panel_AF_letters.csv", encoding="utf-8-sig")
    heat = pd.read_csv(DATA / "fig03_panel_GH_compartment_mean_rank.csv", encoding="utf-8-sig")
    bars = pd.read_csv(DATA / "fig03_panel_IJ_bsri_overall_order.csv", encoding="utf-8-sig")

    fig = plt.figure(figsize=(14, 16))
    gs = fig.add_gridspec(4, 3, height_ratios=[1, 1, 1.05, 0.95], hspace=0.45, wspace=0.28)

    # A–F
    meta = letters[["panel", "unit", "label"]].drop_duplicates()
    # order panels A-F
    for _, row in meta.sort_values("panel").iterrows():
        panel, unit, label = row["panel"], row["unit"], row["label"]
        idx_panel = "ABCDEF".index(panel)
        r, c = divmod(idx_panel, 3)
        ax = fig.add_subplot(gs[r, c])
        sub = rounds[rounds["panel"] == panel]
        let = letters[letters["panel"] == panel].set_index("index")["letter"]
        data = [sub.loc[sub["index"] == i, "mean_rank"].to_numpy() for i in INDEX_ORDER]
        bp = ax.boxplot(data, positions=np.arange(10), widths=0.55, patch_artist=True, showfliers=False,
                        medianprops=dict(color="black", lw=1.1))
        for patch, i in zip(bp["boxes"], INDEX_ORDER):
            patch.set_facecolor(index_color(i))
            patch.set_alpha(0.85)
        for j, i in enumerate(INDEX_ORDER):
            y = data[j]
            if len(y):
                ax.text(j, np.nanmin(y) - 0.12, let.get(i, ""), ha="center", va="top", fontsize=7)
        ax.set_xticks(range(10))
        ax.set_xticklabels(INDEX_ORDER, rotation=60, ha="right", fontsize=7)
        ax.set_ylim(1.5, 10.5)
        ax.invert_yaxis()
        ax.set_title(f"{label} | {unit}", fontsize=10)
        if c == 0:
            ax.set_ylabel("Mean rank")
        panel_label(ax, panel)

    # G–H
    last_im = None
    for col, unit, lab in [(0, "n/L", "G"), (1, "n/kg", "H")]:
        ax = fig.add_subplot(gs[2, col])
        sub = heat[heat["unit"] == unit]
        pivot = sub.pivot_table(index="index", columns="compartment", values="mean_rank", aggfunc="mean")
        pivot = pivot.reindex(INDEX_ORDER).dropna(axis=1, how="all")
        last_im = ax.imshow(pivot.to_numpy(), aspect="auto", cmap="viridis_r", vmin=1, vmax=10)
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index, fontsize=7)
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns, rotation=60, ha="right", fontsize=7)
        ax.set_title(unit)
        panel_label(ax, lab)
    cax = fig.add_subplot(gs[2, 2])
    fig.colorbar(last_im, cax=cax)
    cax.set_ylabel("Mean rank (lower = better)")

    # I–J
    for col, unit, lab in [(0, "n/L", "I"), (1, "n/kg", "J")]:
        ax = fig.add_subplot(gs[3, col])
        sub = bars[bars["unit"] == unit].sort_values("overall_order")
        x = np.arange(len(sub))
        ax.bar(x, sub["overall_order"], color="#4477AA", width=0.7)
        ax.set_xticks(x)
        ax.set_xticklabels(sub["compartment"], rotation=60, ha="right", fontsize=7)
        ax.set_ylabel("BSRI overall order")
        ax.set_ylim(0.5, 4.0)
        ax.set_title(unit)
        panel_label(ax, lab)
    fig.add_subplot(gs[3, 2]).axis("off")

    fig.savefig(OUT)
    plt.close(fig)
    print("wrote", OUT)
    return OUT


if __name__ == "__main__":
    main()
