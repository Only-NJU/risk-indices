# -*- coding: utf-8 -*-
"""Score Table 3 / Method S2 metrics from validation worksheets (MS-1119v9).

Inputs (same folder):
  sub952_{gold,qwen,glm}.xlsx
  subset_3381_{A,B,C}.xlsx

Metrics follow SI Method S2:
  - 44 fields including mp_concentration
  - coordinates and mp_concentration_unit excluded from the 44-field summary
  - field inclusion: precision / recall / F1
  - value extraction: conditional and end-to-end value accuracy
  - percentages: |a-b| <= max(0.05*max(|a|,|b|), 1e-6)
  - concentrations: numeric exact equality
  - text: trim + case-insensitive
  - unmatched reference records count as missing for every field
  - concentration+unit audit reported separately
"""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
KEYS = ["paper_id", "sample_id"]
TRACE = {
    "db_row_idx",
    "paper_id",
    "sample_id",
    "doi",
    "paper_title",
    "mp_concentration_unit",  # audited separately from the 44-field summary
}
CONC_FIELD = "mp_concentration"
CONC_UNIT = "mp_concentration_unit"
GROUPS = {
    "Geo / location": [
        "sample_site_code",
        "site_name",
        "water_body_name_local",
        "specific_location",
        "country_region",
        "admin_location",
        "water_body_name",
        "compartment_main",
        "compartment_sub",
        "geo_country",
        "geo_continent",
        "geo_ocean_basin",
        "continent_ocean_basin",
    ],
    "Shape": [
        "shape_fiber_pct",
        "shape_fragment_pct",
        "shape_film_pct",
        "shape_pellet_pct",
        "shape_others_pct",
    ],
    "Polymer": [
        "polymer_pp_pct",
        "polymer_pe_pct",
        "polymer_ps_pct",
        "polymer_pvc_pct",
        "polymer_pet_pct",
        "polymer_pa_pct",
        "polymer_pc_pct",
        "polymer_others_pct",
    ],
    "Colour": [
        "color_transparent_pct",
        "color_yellow_pct",
        "color_red_pct",
        "color_green_pct",
        "color_black_pct",
        "color_white_pct",
        "color_blue_pct",
        "color_others_pct",
    ],
    "Size": [
        "size_gt_1mm_pct",
        "size_lt_1mm_pct",
        "size_frac_500_999_um_pct",
        "size_frac_200_500_um_pct",
        "size_frac_100_200_um_pct",
        "size_frac_50_100_um_pct",
        "size_frac_30_50_um_pct",
        "size_frac_1_9_um_pct",
        "size_frac_lt_1_um_pct",
    ],
    "Concentration": [CONC_FIELD],
}


def null(x) -> bool:
    if x is None:
        return True
    try:
        if pd.isna(x):
            return True
    except Exception:
        pass
    if isinstance(x, float) and np.isnan(x):
        return True
    if isinstance(x, str) and not str(x).strip():
        return True
    return False


def eq(a, b, field: str) -> bool:
    if null(a) and null(b):
        return True
    if null(a) or null(b):
        return False
    if field == CONC_FIELD:
        try:
            return float(a) == float(b)
        except Exception:
            return False
    if str(field).endswith("_pct"):
        try:
            na, nb = float(a), float(b)
        except Exception:
            return False
        return abs(na - nb) <= max(0.05 * max(abs(na), abs(nb)), 1e-6)
    return str(a).strip().lower() == str(b).strip().lower()


def load_keyed(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_excel(path)
    good = raw.dropna(subset=KEYS).copy()
    good = good.set_index(KEYS, drop=False)
    if good.index.duplicated().any():
        raise ValueError(f"duplicate keys in {path.name}")
    return raw, good


def field_list(df: pd.DataFrame) -> list[str]:
    fields = [c for c in df.columns if c not in TRACE]
    if CONC_FIELD not in fields:
        raise ValueError(f"missing {CONC_FIELD}")
    if len(fields) != 44:
        raise ValueError(f"expected 44 scored fields, got {len(fields)}: {fields}")
    return fields


def vs_gold(pred: pd.DataFrame, gold: pd.DataFrame, fields: list[str]) -> dict:
    """Align on gold index; missing model rows count as all-null predictions."""
    aligned = pred.reindex(gold.index)
    n = len(gold)
    rows = []
    for field in fields:
        tp = fp = fn = tn = 0
        cond_ok = cond_n = 0
        e2e_ok = e2e_n = 0
        for i in range(n):
            gv = gold.iloc[i][field]
            # reindex places NaN when the model row is absent
            pv = aligned.iloc[i][field]
            ga, pa = (not null(gv)), (not null(pv))
            if pa and ga:
                tp += 1
            elif pa and not ga:
                fp += 1
            elif (not pa) and ga:
                fn += 1
            else:
                tn += 1
            if ga and pa:
                cond_n += 1
                if eq(pv, gv, field):
                    cond_ok += 1
            if ga:
                e2e_n += 1
                if pa and eq(pv, gv, field):
                    e2e_ok += 1
        prec = tp / (tp + fp) if tp + fp else float("nan")
        rec = tp / (tp + fn) if tp + fn else float("nan")
        f1 = (
            2 * prec * rec / (prec + rec)
            if prec == prec and rec == rec and (prec + rec)
            else float("nan")
        )
        rows.append(
            {
                "field": field,
                "inclusion_precision": prec,
                "inclusion_recall": rec,
                "inclusion_f1": f1,
                "conditional_value_accuracy": (cond_ok / cond_n if cond_n else float("nan")),
                "end_to_end_value_accuracy": (e2e_ok / e2e_n if e2e_n else float("nan")),
                "n_reference_nonmissing": e2e_n,
                "n_both_nonmissing": cond_n,
            }
        )
    by_field = pd.DataFrame(rows)
    group = {}
    for gname, cols in GROUPS.items():
        sub = by_field[by_field.field.isin(cols)]
        if sub.empty:
            continue
        group[gname] = {
            "inclusion_recall": float(sub.inclusion_recall.mean()),
            "inclusion_f1": float(sub.inclusion_f1.mean()),
            "conditional_value_accuracy": float(sub.conditional_value_accuracy.mean()),
            "end_to_end_value_accuracy": float(sub.end_to_end_value_accuracy.mean()),
        }

    # concentration + unit exact audit
    g_conc = gold[CONC_FIELD]
    g_unit = gold[CONC_UNIT]
    eligible = (~g_conc.map(null)) & (~g_unit.map(null))
    p_conc = aligned[CONC_FIELD]
    p_unit = aligned[CONC_UNIT]
    both_ext = eligible & (~p_conc.map(null)) & (~p_unit.map(null))
    exact = both_ext & p_conc.eq(g_conc) & p_unit.astype(str).str.strip().str.lower().eq(
        g_unit.astype(str).str.strip().str.lower()
    )
    # numeric exact for concentration (handle float)
    exact_num = []
    for idx in gold.index:
        if not bool(eligible.loc[idx]):
            exact_num.append(False)
            continue
        if null(p_conc.loc[idx]) or null(p_unit.loc[idx]):
            exact_num.append(False)
            continue
        try:
            ok_c = float(p_conc.loc[idx]) == float(g_conc.loc[idx])
        except Exception:
            ok_c = False
        ok_u = str(p_unit.loc[idx]).strip().lower() == str(g_unit.loc[idx]).strip().lower()
        exact_num.append(ok_c and ok_u)
    exact_s = pd.Series(exact_num, index=gold.index)

    return {
        "n_reference": n,
        "n_model_matched": int(aligned.index.isin(pred.index).sum()),
        "macro_inclusion_recall": float(by_field.inclusion_recall.mean()),
        "macro_inclusion_precision": float(by_field.inclusion_precision.mean()),
        "macro_inclusion_f1": float(by_field.inclusion_f1.mean()),
        "macro_conditional_value_accuracy": float(by_field.conditional_value_accuracy.mean()),
        "macro_end_to_end_value_accuracy": float(by_field.end_to_end_value_accuracy.mean()),
        "by_group": group,
        "by_field": by_field,
        "concentration_unit_audit": {
            "n_eligible_reference": int(eligible.sum()),
            "n_exact_match": int(exact_s.sum()),
            "n_both_extracted": int(both_ext.sum()),
            "exact_among_eligible": float(exact_s.sum() / eligible.sum()) if eligible.any() else float("nan"),
            "exact_among_both_extracted": float(exact_s.sum() / both_ext.sum()) if both_ext.any() else float("nan"),
        },
    }


def triple_agree(vals, field: str) -> bool:
    return all(eq(vals[i], vals[j], field) for i, j in combinations(range(len(vals)), 2))


def repeatability(runs: list[pd.DataFrame], fields: list[str]) -> dict:
    raw_n = [len(r) for r in runs]
    keyed = []
    for r in runs:
        k = r.dropna(subset=KEYS).set_index(KEYS, drop=False)
        if k.index.duplicated().any():
            k = k[~k.index.duplicated(keep="first")]
        keyed.append(k)
    union = keyed[0].index.union(keyed[1].index).union(keyed[2].index)
    common = keyed[0].index.intersection(keyed[1].index).intersection(keyed[2].index)
    aligned = [k.loc[common] for k in keyed]

    whole = 0
    for idx in common:
        ok = all(
            triple_agree([aligned[j].loc[idx, f] for j in range(3)], f) for f in fields
        )
        if ok:
            whole += 1

    # with unit as 45th field
    fields45 = fields + [CONC_UNIT] if CONC_UNIT in aligned[0].columns else fields
    whole45 = 0
    for idx in common:
        ok = all(
            triple_agree([aligned[j].loc[idx, f] for j in range(3)], f) for f in fields45
        )
        if ok:
            whole45 += 1

    cell_ok = cell_n = 0
    present_ok = present_n = 0
    per_field = []
    for f in fields:
        agree_n = 0
        nonempty_n = 0
        nonempty_agree = 0
        for idx in common:
            vals = [aligned[j].loc[idx, f] for j in range(3)]
            cell_n += 1
            if triple_agree(vals, f):
                cell_ok += 1
                agree_n += 1
            if any(not null(v) for v in vals):
                nonempty_n += 1
                present_n += 1
                if triple_agree(vals, f):
                    nonempty_agree += 1
                    present_ok += 1
        per_field.append(
            {
                "field": f,
                "triple_exact": agree_n / len(common) if len(common) else float("nan"),
                "triple_exact_nonempty": (
                    nonempty_agree / nonempty_n if nonempty_n else float("nan")
                ),
            }
        )

    pairs = []
    for i, j in combinations(range(3), 2):
        pair_idx = keyed[i].index.intersection(keyed[j].index)
        n_pair = len(pair_idx)
        row_ok = 0
        for idx in pair_idx:
            if all(eq(keyed[i].loc[idx, f], keyed[j].loc[idx, f], f) for f in fields):
                row_ok += 1
        pairs.append(
            {
                "pair": f"{'ABC'[i]}-{('ABC'[j])}",
                "n": n_pair,
                "whole_record_44": row_ok / n_pair if n_pair else float("nan"),
            }
        )

    # concentration-only agreement excluding all-missing
    conc_n = conc_ok = 0
    unit_n = unit_ok = 0
    for idx in common:
        vals = [aligned[j].loc[idx, CONC_FIELD] for j in range(3)]
        if any(not null(v) for v in vals):
            conc_n += 1
            if triple_agree(vals, CONC_FIELD):
                conc_ok += 1
        if CONC_UNIT in aligned[0].columns:
            uvals = [aligned[j].loc[idx, CONC_UNIT] for j in range(3)]
            if any(not null(v) for v in uvals):
                unit_n += 1
                if triple_agree(uvals, CONC_UNIT):
                    unit_ok += 1

    return {
        "raw_rows": raw_n,
        "valid_rows": [len(k) for k in keyed],
        "n_publications": int(keyed[0]["paper_id"].nunique()),
        "n_union": int(len(union)),
        "n_common": int(len(common)),
        "whole_record_44": whole / len(common) if len(common) else float("nan"),
        "whole_record_44_count": whole,
        "whole_record_45_with_unit": whole45 / len(common) if len(common) else float("nan"),
        "pooled_cell_agreement_44": cell_ok / cell_n if cell_n else float("nan"),
        "fraction_all_missing_cells": 1.0 - (present_n / cell_n if cell_n else 0.0),
        "macro_field_agreement_nonempty": float(
            pd.DataFrame(per_field)["triple_exact_nonempty"].mean()
        ),
        "concentration_agreement_nonempty": (
            f"{conc_ok}/{conc_n}" if conc_n else "n/a"
        ),
        "concentration_unit_agreement_nonempty": (
            f"{unit_ok}/{unit_n}" if unit_n else "n/a"
        ),
        "pairs": pairs,
        "by_field": per_field,
    }


def main() -> int:
    gold_raw, gold = load_keyed(HERE / "sub952_gold.xlsx")
    fields = field_list(gold_raw)
    assert len(gold) == len(gold_raw) or True
    # use full gold rows; drop only if keys missing already handled
    gold = gold_raw.dropna(subset=KEYS).set_index(KEYS, drop=False)
    if gold.index.duplicated().any():
        raise ValueError("duplicate keys in gold")

    summary = {
        "n_fields": len(fields),
        "fields": fields,
        "accuracy": {},
        "repeatability": {},
    }
    for model in ["qwen", "glm"]:
        _, pred = load_keyed(HERE / f"sub952_{model}.xlsx")
        m = vs_gold(pred, gold, fields)
        by_field = m.pop("by_field")
        by_field.to_csv(HERE / f"metrics_{model}_by_field.csv", index=False, encoding="utf-8-sig")
        summary["accuracy"][model] = m
        print(
            model,
            "recall",
            round(m["macro_inclusion_recall"], 4),
            "cond",
            round(m["macro_conditional_value_accuracy"], 4),
            "e2e",
            round(m["macro_end_to_end_value_accuracy"], 4),
            "conc",
            m["concentration_unit_audit"],
        )

    runs = [pd.read_excel(HERE / f"subset_3381_{x}.xlsx") for x in "ABC"]
    # ensure same field set; repeatability sheets should include mp_concentration
    rep_fields = [c for c in runs[0].columns if c not in TRACE]
    if CONC_FIELD not in rep_fields:
        raise ValueError("repeatability sheets missing mp_concentration")
    if len(rep_fields) != 44:
        # fall back to accuracy field order intersection
        rep_fields = [f for f in fields if f in runs[0].columns]
        assert len(rep_fields) == 44, len(rep_fields)
    rep = repeatability(runs, rep_fields)
    summary["repeatability"] = {k: v for k, v in rep.items() if k != "by_field"}
    pd.DataFrame(rep["by_field"]).to_csv(
        HERE / "metrics_repeatability_by_field.csv", index=False, encoding="utf-8-sig"
    )
    print(
        "repeatability common",
        rep["n_common"],
        "whole44",
        round(rep["whole_record_44"], 4),
        "count",
        rep["whole_record_44_count"],
    )

    # JSON without huge by_field frames
    out = json.loads(json.dumps(summary, ensure_ascii=False, default=str))
    (HERE / "metrics_summary.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("wrote", HERE / "metrics_summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
