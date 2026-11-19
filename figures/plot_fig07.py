# -*- coding: utf-8 -*-
"""Figure 7 from plot-ready pre/post and ortho tables only."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
from common import apply_style, panel_label  # noqa: E402

DATA = HERE
SHARED = HERE
OUT = HERE / "fig07.png"
MILESTONES = ["China 2021", "EU27 2020", "EU27 2024"]
UNITS = ["n/L", "n/kg"]


def _rain_pair(ax, vals: pd.DataFrame, title: str, ylab: str, p_holm: float | None) -> None:
    pre = vals.loc[vals["period"] == "pre", "value"].to_numpy()
    post = vals.loc[vals["period"] == "post", "value"].to_numpy()
    data = [pre, post]
    parts = ax.violinplot(data, positions=[0, 1], showextrema=False, showmeans=False, showmedians=False)
    for b, color in zip(parts["bodies"], ["#9ecae1", "#fcbba1"]):
        b.set_facecolor(color)
        b.set_alpha(0.75)
    ax.boxplot(
        data,
        positions=[0, 1],
        widths=0.18,
        showfliers=False,
        patch_artist=True,
        boxprops=dict(facecolor="white"),
        medianprops=dict(color="black"),
    )
    rng = np.random.default_rng(0)
    for i, y in enumerate(data):
        if len(y) == 0:
            continue
        n = min(len(y), 2000)
        yy = y if len(y) <= 2000 else rng.choice(y, n, replace=False)
        ax.scatter(rng.normal(i, 0.04, size=len(yy)), yy, s=3, color="#333333", alpha=0.12)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Pre", "Post"])
    ax.set_ylabel(ylab)
    ax.set_title(title, fontsize=10)
    if p_holm is not None and np.isfinite(p_holm):
        stars = "***" if p_holm < 0.001 else "**" if p_holm < 0.01 else "*" if p_holm < 0.05 else "ns"
        ax.text(0.5, 0.92, stars, transform=ax.transAxes, ha="center", fontsize=11)


def main() -> Path:
    apply_style()
    values = pd.read_csv(DATA / "fig07_panel_AF_prepost_values.csv", encoding="utf-8-sig")
    stats = pd.read_csv(DATA / "fig07_panel_AF_prepost_stats.csv", encoding="utf-8-sig")
    ortho = pd.read_csv(DATA / "fig07_panel_GI_ortho_ratio.csv", encoding="utf-8-sig")

    fig = plt.figure(figsize=(14, 12))
    gs = fig.add_gridspec(3, 3, height_ratios=[1, 1, 0.95], hspace=0.45, wspace=0.30)
    labs = "ABCDEF"
    k = 0
    for unit in UNITS:
        for milestone in MILESTONES:
            ax = fig.add_subplot(gs[0 if unit == "n/L" else 1, MILESTONES.index(milestone)])
            sub = values[
                (values["milestone"] == milestone)
                & (values["unit"] == unit)
                & (values["metric"] == "BSRI")
            ]
            st = stats[
                (stats["milestone"] == milestone)
                & (stats["unit"] == unit)
                & (stats["metric"] == "BSRI")
            ]
            p = float(st.iloc[0]["p_holm"]) if len(st) else np.nan
            _rain_pair(ax, sub, f"{milestone} | {unit} | BSRI", "BSRI", p)
            panel_label(ax, labs[k])
            k += 1

    last_im = None
    for c, milestone in enumerate(MILESTONES):
        ax = fig.add_subplot(gs[2, c])
        sub = ortho[ortho["milestone"] == milestone]
        pivot = sub.pivot_table(index="compartment", columns="unit", values="ratio", aggfunc="first")
        last_im = ax.imshow(pivot.to_numpy(), aspect="auto", cmap="RdBu_r", vmin=0.5, vmax=1.5)
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index, fontsize=7)
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns, fontsize=8)
        ax.set_title(milestone, fontsize=10)
        panel_label(ax, "GHI"[c])
    if last_im is not None:
        fig.colorbar(last_im, ax=fig.axes[-3:], fraction=0.03, pad=0.02, label="Post/Pre median ratio (BSRI)")
    fig.savefig(OUT)

    # entropy companion
    fig2, axes = plt.subplots(2, 3, figsize=(14, 7))
    k = 0
    for r, unit in enumerate(UNITS):
        for c, milestone in enumerate(MILESTONES):
            ax = axes[r, c]
            sub = values[
                (values["milestone"] == milestone)
                & (values["unit"] == unit)
                & (values["metric"] == "risk_entropy")
            ]
            st = stats[
                (stats["milestone"] == milestone)
                & (stats["unit"] == unit)
                & (stats["metric"] == "risk_entropy")
            ]
            p = float(st.iloc[0]["p_holm"]) if len(st) else np.nan
            _rain_pair(ax, sub, f"{milestone} | {unit} | Entropy", "Risk entropy", p)
            panel_label(ax, labs[k])
            k += 1
    fig2.tight_layout()
    fig2.savefig(HERE / "fig07_entropy_companion.png")
    plt.close("all")
    print("wrote", OUT)
    print("wrote", HERE / "fig07_entropy_companion.png")
    return OUT


if __name__ == "__main__":
    main()
