# App Data

The WSL pipeline publishes generated JSON files into this folder automatically:

```bash
cd /mnt/d/Python/Genetics
bash run_pipeline_wsl.sh
```

Expected files:

- `report_summary.json`
- `shared_snp_quality.json`
- `reference_labels.json`
- `eagle_results_index.json`
- `phasing_qc.json`

If these files are absent, the deployed UI falls back to a preview shell with pending values.
