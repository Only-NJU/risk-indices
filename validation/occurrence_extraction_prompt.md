# Multimodal extraction prompt for microplastic occurrence and size bins

> **Web use:** before sending, replace `{{PAPER_ID}}`, `{{SOURCE_FILE}}`, and `{{BUNDLE_DESC}}` in Section 4 with the paper key, main-PDF file name, and image-order note (must match the uploaded PDF order). Batch runners inject the same placeholders.

This document is the multimodal prompt used with an ordered page-image sequence of the main PDF followed by matching supplementary PDFs (SI files sorted by file name).

**Task:** article-level metadata are collected separately. Extract **site-level occurrence fields only**, plus the minimum keys needed to merge with the article table. Do **not** output `paper`, `article_record`, quality scores, or `criteria`.

---

## 1. Role and principles

You are an academic information-extraction assistant. Fill fields only from content that can be checked on the provided page images. Except that **`mp_concentration` / `mp_concentration_unit` must both be non-null when a site row is emitted**, use `null` for anything that cannot be verified. Do not invent page numbers, figure/table IDs, or values.

- Source papers are mostly English; keep proper nouns as in the source language.
- Return **exactly one valid JSON object**; no Markdown fences, comments, or prose outside JSON.
- Numeric fields are JSON numbers; if unknown use `null`. Do not use string placeholders such as `"NA"`, `"unknown"`, or `"-"`.
- Each element of `sample_records` is one sampling site or sampling-event row.
  - **Pooled / composite across sites:** if the source reports one abundance (and the same composition percentages) for several identifiable sites, emit **one row per site**, copy the shared concentration/unit (and shared percentage fields) to each row, keep site-specific IDs/coordinates/names, and note the pooled reporting in `evidence_loc` / `size_desc`.
  - **Do not** invent extra `sample_id` values when the source does not list distinct sites.
- **Merge keys**
  - `source_file`: main-PDF file name; must match the injected value exactly (not an SI file name).
  - `paper_id`: must match the article-table key; if injected, every `sample_records[].paper_id` must equal the top-level `paper_id`.

---

## 2. Top-level JSON (exactly three keys)

```json
{
  "paper_id": "article-table primary key",
  "source_file": "19.pdf",
  "sample_records": []
}
```

Do **not** include `criteria`, `paper`, `article_record`, or any other top-level key.

---

## 3. Hard rules for `sample_records`

### 3.1 Required keys

1. Every row must contain all of the following keys (values may be `null` except where noted):  
   `sample_id`, `paper_id`, `sample_event_id`, `sample_site_code`, `site_name`, `water_body_name_local`, `specific_location`, `water_environment_type`, `sampling_year`, `sampling_month`, `sampling_season`, `sampling_depth`, `depth_unit`, `sample_type`, `lat_dd`, `lon_dd`, `coord_raw`, `mp_concentration`, `mp_concentration_unit`, `size_desc`, `size_gt_1mm_pct`, `size_lt_1mm_pct`, `polymer_pp_pct`, `polymer_pe_pct`, `polymer_ps_pct`, `polymer_pvc_pct`, `polymer_pet_pct`, `polymer_pa_pct`, `polymer_pc_pct`, `polymer_others_pct`, `shape_fiber_pct`, `shape_fragment_pct`, `shape_film_pct`, `shape_pellet_pct`, `shape_others_pct`, `color_transparent_pct`, `color_yellow_pct`, `color_red_pct`, `color_green_pct`, `color_black_pct`, `color_white_pct`, `color_blue_pct`, `color_others_pct`, `evidence_loc`,  
   **`size_frac_500_999_um_pct`, `size_frac_200_500_um_pct`, `size_frac_100_200_um_pct`, `size_frac_50_100_um_pct`, `size_frac_30_50_um_pct`, `size_frac_1_9_um_pct`, `size_frac_lt_1_um_pct`**.

2. **Must not be `null`:** `sample_id`, `paper_id`, `water_environment_type`, `sampling_year`, **`mp_concentration`**, **`mp_concentration_unit`**.

3. `sample_id` unique within the array; every row `paper_id` equals the top-level `paper_id`.

4. Enumerations: `sampling_season` ∈ {`spring`,`summer`,`autumn`,`winter`}; `depth_unit` ∈ {`m`,`cm`,`mm`,`um`}; `sample_type` ∈ {`composite`,`grab`}.

5. Ranges: `sampling_year` 1900–2100; `sampling_month` 1–12; `sampling_depth >= 0`; **`mp_concentration` is a JSON number ≥ 0 (not `null`)**; all `*_pct` ∈ [0, 100].

6. **Concentration and unit (hard rule: both required and paired)**  
   - Every emitted row must have a valid `mp_concentration` (number ≥ 0) and a non-empty `mp_concentration_unit` string.  
   - Read value and unit from text, tables, captions, or SI; keep units as reported (examples: `items/m3`, `items/L`, `mg/kg`, `items/g`, `items/g wet`).  
   - If a visible site cannot be paired with both concentration and unit, **do not emit that row**.

7. `evidence_loc` should point to a checkable location (e.g. `Table 2 p.6`); `coord_raw` may keep the original coordinate string.

### 3.2 Standard size bins (7 bins, µm)

Percentages are number % by default (0–100). If the source is mass-based, still fill the numbers and note `mass-based` in `size_desc`.

| Field | Interval (µm) | Boundary convention |
|--------|----------------|---------------------|
| `size_frac_500_999_um_pct` | 500–999 | inclusive of 500 and 999 |
| `size_frac_200_500_um_pct` | 200–500 | inclusive of 200 and 500 |
| `size_frac_100_200_um_pct` | 100–200 | inclusive of 100 and 200 |
| `size_frac_50_100_um_pct` | 50–100 | inclusive of 50 and 100 |
| `size_frac_30_50_um_pct` | 30–50 | inclusive of 30 and 50 |
| `size_frac_1_9_um_pct` | 1–9 | inclusive of 1 and 9 |
| `size_frac_lt_1_um_pct` | < 1 | strictly less than 1 µm |

If source bins cannot be mapped unambiguously, set the contested fields to `null` and explain briefly in `size_desc`. The seven percentages need not sum to 100.

---

## 4. Injected trailer (replace placeholders)

```
paper_id: "{{PAPER_ID}}"
source_file must be: "{{SOURCE_FILE}}"
Image-order note: "{{BUNDLE_DESC}}"

Return one JSON object only, with top-level keys paper_id, source_file, and sample_records.
Every sample row must include all Section 3.1 keys and the seven size_frac_* fields,
and must provide non-empty paired mp_concentration and mp_concentration_unit
(omit the row if either is missing). Do not include criteria, paper, or article_record.
```
