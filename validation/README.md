# Validation worksheets and scoring

English materials supporting manuscript Table 3 and SI Method S2.

## Files

| File | Role |
|------|------|
| `sub952_gold.xlsx` | Expert gold standard |
| `sub952_qwen.xlsx` | qwen3.7-plus extractions on the gold cohort |
| `sub952_glm.xlsx` | glm-5.3-flash extractions on the gold cohort |
| `subset_3381_{A,B,C}.xlsx` | Three independent qwen3.7-plus feature tables |
| `publications_1436.xlsx` | Publication list for the curated corpus |
| `occurrence_extraction_prompt.md` | Multimodal occurrence-extraction prompt (English) |
| `score_table3.py` | Recompute nested availability / value / inter-model / repeatability metrics |

## Reproduce

```bash
pip install pandas numpy openpyxl
python score_table3.py
```

Outputs are written under `metrics/` next to this script when present, or printed as JSON.
