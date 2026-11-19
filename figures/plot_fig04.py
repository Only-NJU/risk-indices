# -*- coding: utf-8 -*-
"""Figure 4 from plot-ready radar/heatmap value tables only."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
from common import INDEX_ORDER, RANK_METRICS, SCENARIO_LABELS, apply_style, panel_label  # noqa: E402

DATA = HERE
SHARED = HERE
OUT = HERE / "fig04.png"
FOCUS = ["BSRI", "MultiMP", "MPERI"]
STYLE = {
    "BSRI": dict(color="#4477AA", lw=2.4, ls="-"),
    "MultiMP": dict(color="#C44E52", lw=1.8, ls="-"),
    "MPERI": dict(color="#DD8452", lw=1.8, ls="--"),
}
METRIC_SHORT = {
    "Shannon_H'": "Shannon",
    "Simpson_D": "Simpson",
    "Pielou_J'": "Pielou",
    "Availability": "Availability",
    "quartile_coefficient_of_dispersion": "CQV",
    "mode_freq_ratio": "Mode freq.",
    "gini": "Gini",
}


def _radar(ax, radar: pd.DataFrame, unit: str) -> None:
    labels = [METRIC_SHORT[m] for m in RANK_METRICS]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels, fontsize=8)
    ax.set_ylim(0, 1)
    sub = radar[radar["unit"] == unit]
    for idx in FOCUS:
        vals = [
            float(sub.loc[(sub["index"] == idx) & (sub["metric"] == m), "value"].iloc[0])
            for m in RANK_METRICS
        ]
        vals_c = vals + vals[:1]
        st = STYLE[idx]
        ax.plot(angles, vals_c, color=st["color"], lw=st["lw"], ls=st["ls"], label=idx)
        ax.fill(angles, vals_c, color=st["color"], alpha=0.10)
    ax.set_title(unit, fontsize=11, pad=12)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.15), fontsize=8, frameon=False)


def _heat(ax, heat: pd.DataFrame, unit: str, scenario: str):
    sub = heat[(heat["unit"] == unit) & (heat["scenario"] == scenario)]
    mat = []
    for idx in INDEX_ORDER:
        mat.append(
            [
                float(sub.loc[(sub["index"] == idx) & (sub["metric"] == m), "value"].iloc[0])
                for m in RANK_METRICS
            ]
        )
    arr = np.asarray(mat, dtype=float)
    im = ax.imshow(arr, aspect="auto", cmap="YlGnBu", vmin=0, vmax=1)
    ax.set_yticks(range(len(INDEX_ORDER)))
    ax.set_yticklabels(INDEX_ORDER, fontsize=7)
    ax.set_xticks(range(len(RANK_METRICS)))
    ax.set_xticklabels([METRIC_SHORT[m] for m in RANK_METRICS], rotation=45, ha="right", fontsize=7)
    ax.set_title(f"{SCENARIO_LABELS[scenario]} | {unit}", fontsize=10)
    return im


def main() -> Path:
    apply_style()
    radar = pd.read_csv(DATA / "fig04_panel_AB_radar_values.csv", encoding="utf-8-sig")
    heat = pd.read_csv(DATA / "fig04_panel_CH_heatmap_values.csv", encoding="utf-8-sig")
    fig = plt.figure(figsize=(14, 12))
    gs = fig.add_gridspec(4, 3, height_ratios=[1.15, 1, 1, 1], hspace=0.55, wspace=0.35)

    for i, unit in enumerate(["n/L", "n/kg"]):
        ax = fig.add_subplot(gs[0, i], polar=True)
        _radar(ax, radar, unit)
        ax.text(-0.15, 1.08, "AB"[i], transform=ax.transAxes, fontsize=14, fontweight="bold")
    ax_leg = fig.add_subplot(gs[0, 2])
    ax_leg.axis("off")
    ax_leg.text(0.0, 0.8, "Radar: benefit-normalized\nseven-metric profile\n(natural scenario)", fontsize=10)

    labs = "CDEFGH"
    k = 0
    last_im = None
    for unit in ["n/L", "n/kg"]:
        for sc in ["natural", "intersection", "full_equal_split"]:
            ax = fig.add_subplot(gs[1 + k // 3, k % 3])
            last_im = _heat(ax, heat, unit, sc)
            panel_label(ax, labs[k], x=-0.12, y=1.08)
            k += 1

    cax = fig.add_axes([0.92, 0.12, 0.015, 0.55])
    fig.colorbar(last_im, cax=cax, label="Benefit-normalized score")
    fig.savefig(OUT)
    plt.close(fig)
    print("wrote", OUT)
    return OUT


if __name__ == "__main__":
    main()
