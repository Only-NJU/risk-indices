# -*- coding: utf-8 -*-
"""Shared helpers for standalone main-text figure scripts."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter
from scipy.stats import ttest_rel

INDEX_ORDER = [
    "ORI",
    "ERI",
    "MPERI",
    "MultiMP",
    "NPI",
    "PHI",
    "PLI",
    "PRI",
    "MESI",
    "BSRI",
]
INDEX_COLORS = {
    "BSRI": "#4477AA",
    "MultiMP": "#C44E52",
    "MPERI": "#DD8452",
}
DEFAULT_COLOR = "#8C8C8C"
# Metric names are English in packaged panel CSVs.
RANK_METRICS = [
    "Shannon_H'",
    "Simpson_D",
    "Pielou_J'",
    "Availability",
    "quartile_coefficient_of_dispersion",
    "mode_freq_ratio",
    "gini",
]
RANK_ASCENDING = {
    "Shannon_H'": False,
    "Simpson_D": False,
    "Pielou_J'": False,
    "Availability": False,  # higher availability preferred
    "quartile_coefficient_of_dispersion": False,
    "mode_freq_ratio": True,
    "gini": True,
}
SCENARIO_LABELS = {
    "natural": "Natural",
    "intersection": "Intersection",
    "full_equal_split": "Equal-split",
}
UNIT_FILE = {"n/L": "n_L", "n/kg": "n_kg"}
UNIT_LABEL = {"n_L": "n/L", "n_kg": "n/kg"}
# Attribution class labels used in Figure 5/6 panel tables.
DISPUTE_LABEL = {
    "data-sparse": "data-sparse",
    "composition-complex": "composition-complex",
    "mixed": "mixed",
}


def apply_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": 11,
            "axes.linewidth": 1.0,
            "axes.unicode_minus": False,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def here(*parts: str) -> Path:
    return Path(__file__).resolve().parent.joinpath(*parts)


def fig_dir(script_file: str) -> Path:
    return Path(script_file).resolve().parent


def data_dir(script_file: str) -> Path:
    return fig_dir(script_file) / "data"


def index_color(name: str) -> str:
    return INDEX_COLORS.get(name, DEFAULT_COLOR)


def panel_label(ax, text: str, x: float = -0.08, y: float = 1.05) -> None:
    ax.text(
        x,
        y,
        text,
        transform=ax.transAxes,
        fontsize=14,
        fontweight="bold",
        va="bottom",
        ha="left",
    )


def holm_letters(round_matrix: pd.DataFrame) -> dict[str, str]:
    """round_matrix: columns=index names, rows=rounds of mean-rank."""
    names = [c for c in INDEX_ORDER if c in round_matrix.columns]
    mat = round_matrix[names].to_numpy(dtype=float)
    n = len(names)
    p = np.ones((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            a = mat[:, i]
            b = mat[:, j]
            ok = np.isfinite(a) & np.isfinite(b)
            if ok.sum() < 3:
                continue
            p[i, j] = p[j, i] = float(ttest_rel(a[ok], b[ok]).pvalue)
    # Holm
    pairs = [(p[i, j], i, j) for i in range(n) for j in range(i + 1, n)]
    pairs.sort(key=lambda x: x[0])
    m = len(pairs)
    adj = {}
    for rank, (pval, i, j) in enumerate(pairs, start=1):
        adj[(i, j)] = min(1.0, pval * (m - rank + 1))
    not_diff = np.eye(n, dtype=bool)
    for (i, j), ap in adj.items():
        if ap >= 0.05:
            not_diff[i, j] = not_diff[j, i] = True
    letters = [""] * n
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    next_i = 0
    for start in range(n):
        if letters[start]:
            continue
        letter = alphabet[next_i]
        next_i += 1
        letters[start] += letter
        for j in range(start + 1, n):
            if not_diff[start, j] and letter not in letters[j]:
                # assign same letter only if connected through clique-ish rule used in paper scripts
                if all(not_diff[j, k] or k == j for k in range(n) if letter in letters[k]):
                    letters[j] += letter
        if not letters[start]:
            letters[start] = letter
    # simpler compact display: rebuild with transitive-ish paper method
    letters = [""] * n
    next_i = 0
    for start in range(n):
        if letters[start]:
            continue
        letter = alphabet[next_i]
        next_i += 1
        for j in range(start, n):
            if all(not_diff[j, k] for k in range(n) if letter in letters[k]) or j == start:
                if letter not in letters[j]:
                    letters[j] += letter
        if not letters[start]:
            letters[start] = letter
    return {names[i]: letters[i] for i in range(n)}


def mean_rank_by_round(rounds_df: pd.DataFrame, availability: pd.Series) -> pd.DataFrame:
    """Build rounds × index mean-rank matrix from metric rounds + availability ratio.

    Expects ``rounds_df`` to contain an ``index`` column (index short name) and
    one column per metric in ``RANK_METRICS`` except ``Availability``.
    """
    metric_cols = [c for c in RANK_METRICS if c != "Availability"]
    index_col = "index" if "index" in rounds_df.columns else "variable"
    rows = []
    for round_idx, grp in rounds_df.groupby("round"):
        g = grp.set_index(index_col)
        ranks = {}
        for m in metric_cols:
            ascending = RANK_ASCENDING[m]
            s = g[m].reindex(INDEX_ORDER)
            ranks[m] = s.rank(ascending=ascending, method="average")
        # availability is fixed across rounds
        av = availability.reindex(INDEX_ORDER)
        ranks["Availability"] = av.rank(
            ascending=RANK_ASCENDING["Availability"], method="average"
        )
        mean_rank = pd.DataFrame(ranks).mean(axis=1)
        mean_rank.name = round_idx
        rows.append(mean_rank)
    return pd.DataFrame(rows)


def load_world(ax, shared_dir: Path):
    geo = shared_dir / "ne_110m_admin_0_countries.geojson"
    if not geo.is_file():
        return False
    try:
        import json
        from matplotlib.patches import Polygon
        from matplotlib.collections import PatchCollection

        data = json.loads(geo.read_text(encoding="utf-8"))
        patches = []
        for feat in data.get("features", []):
            geom = feat.get("geometry") or {}
            gtype = geom.get("type")
            coords = geom.get("coordinates")
            if gtype == "Polygon":
                rings = [coords]
            elif gtype == "MultiPolygon":
                rings = coords
            else:
                continue
            for poly in rings:
                if not poly:
                    continue
                xy = np.asarray(poly[0], dtype=float)
                if xy.ndim == 2 and len(xy) >= 3:
                    patches.append(Polygon(xy, closed=True))
        coll = PatchCollection(
            patches, facecolor="#f2f2f2", edgecolor="#888888", linewidths=0.3, zorder=0
        )
        ax.add_collection(coll)
        return True
    except Exception:
        return False


def grid_mean(lon, lat, val, res: float = 2.0):
    lon = np.asarray(lon, dtype=float)
    lat = np.asarray(lat, dtype=float)
    val = np.asarray(val, dtype=float)
    ok = np.isfinite(lon) & np.isfinite(lat) & np.isfinite(val)
    lon, lat, val = lon[ok], lat[ok], val[ok]
    if len(val) == 0:
        return None, None, None
    lon_edges = np.arange(-180, 180 + res, res)
    lat_edges = np.arange(-90, 90 + res, res)
    lon_i = np.clip(np.digitize(lon, lon_edges) - 1, 0, len(lon_edges) - 2)
    lat_i = np.clip(np.digitize(lat, lat_edges) - 1, 0, len(lat_edges) - 2)
    sum_z = np.zeros((len(lat_edges) - 1, len(lon_edges) - 1), dtype=float)
    cnt = np.zeros_like(sum_z)
    for i, j, v in zip(lat_i, lon_i, val):
        sum_z[i, j] += v
        cnt[i, j] += 1
    with np.errstate(invalid="ignore", divide="ignore"):
        z = np.where(cnt > 0, sum_z / cnt, np.nan)
    extent = [lon_edges[0], lon_edges[-1], lat_edges[0], lat_edges[-1]]
    return z, extent, cnt


def smooth_grid(z, sigma: float = 1.2):
    mask = np.isfinite(z)
    filled = np.nan_to_num(z, nan=0.0)
    sm = gaussian_filter(filled, sigma=sigma)
    cnt = gaussian_filter(mask.astype(float), sigma=sigma)
    with np.errstate(invalid="ignore", divide="ignore"):
        out = np.where(cnt > 0.05, sm / np.maximum(cnt, 1e-6), np.nan)
    return out
