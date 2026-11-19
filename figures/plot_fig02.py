# -*- coding: utf-8 -*-
"""Figure 2 from plot-ready mean-rank tables only."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
from common import INDEX_ORDER, SCENARIO_LABELS, apply_style, index_color, panel_label  # noqa: E402

DATA = HERE
SHARED = HERE
OUT = HERE / "fig02.png"


def main() -> Path:
    apply_style()
    rounds = pd.read_csv(DATA / "fig02_panel_AF_mean_rank_rounds.csv", encoding="utf-8-sig")
    letters = pd.read_csv(DATA / "fig02_panel_AF_letters.csv", encoding="utf-8-sig")
    fig, axes = plt.subplots(2, 3, figsize=(14, 8), sharey=True)
    for _, meta in letters[["panel", "unit", "label"]].drop_duplicates().iterrows():
        panel, unit, label = meta["panel"], meta["unit"], meta["label"]
        r = 0 if unit == "n/L" else 1
        c = ["natural", "intersection", "full_equal_split"].index(label)
        ax = axes[r, c]
        sub = rounds[(rounds["panel"] == panel)]
        let = letters[letters["panel"] == panel].set_index("index")["letter"]
        data = [sub.loc[sub["index"] == idx, "mean_rank"].to_numpy() for idx in INDEX_ORDER]
        bp = ax.boxplot(data, positions=np.arange(10), widths=0.55, patch_artist=True, showfliers=False,
                        medianprops=dict(color="black", lw=1.2))
        for patch, idx in zip(bp["boxes"], INDEX_ORDER):
            patch.set_facecolor(index_color(idx))
            patch.set_alpha(0.85)
        rng = np.random.default_rng(0)
        for i, idx in enumerate(INDEX_ORDER):
            y = data[i]
            ax.scatter(rng.normal(i, 0.05, size=len(y)), y, s=8, color="black", alpha=0.35, zorder=3)
            if len(y):
                ax.text(i, np.nanmin(y) - 0.15, let.get(idx, ""), ha="center", va="top", fontsize=8)
        ax.set_xticks(range(10))
        ax.set_xticklabels(INDEX_ORDER, rotation=60, ha="right", fontsize=8)
        if c == 0:
            ax.set_ylabel("Mean rank (lower = better)")
        ax.set_title(f"{SCENARIO_LABELS.get(label, label)} | {unit}", fontsize=11)
        ax.set_ylim(1.5, 10.5)
        ax.invert_yaxis()
        panel_label(ax, panel)
    fig.tight_layout()
    fig.savefig(OUT)
    plt.close(fig)
    print("wrote", OUT)
    return OUT


if __name__ == "__main__":
    main()
