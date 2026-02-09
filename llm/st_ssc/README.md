# ST-SSC: Step-wise Single-type Self-Correction Framework

A research framework for SQL error classification and targeted correction using GPT-5.1.

## Overview

**ST-SSC (Step-wise Single-type Self-Correction)** is a three-step pipeline:

1. **Step 1**: Generate initial SQL from questions
2. **Step 2**: Classify error type (10 fine-grained categories)
3. **Step 3**: Apply targeted single-type correction

**Key Innovation**: Fine-grained error classification (10 types) enables targeted corrections, avoiding pattern-based fixes and correction drift.

## Quick Start

### 1. Setup Configuration

Copy the example config and add your AIML API key:

```bash
cd llm/st_ssc
cp config.example.yaml config.yaml
# Edit config.yaml and replace YOUR_AIML_API_KEY_HERE with your actual key
```

### 2. Convert BIRD Data to JSONL

```bash
cd llm/st_ssc

# Test with 10 samples first
python3 scripts/data_converter.py \
    --bird_json ../data/dev.json \
    --db_root ../data/dev_databases/ \
    --output data/bird_dev_test.jsonl \
    --limit 10

# Full dataset (1534 samples)
python3 scripts/data_converter.py \
    --bird_json ../data/dev.json \
    --db_root ../data/dev_databases/ \
    --output data/bird_dev_1534.jsonl
```

### 3. Test API Connection

```bash
cd scripts
python3 llm_client.py YOUR_AIML_API_KEY
```

Expected output: A generated SQL query

### 4. Run the Pipeline

```bash
# Option 1: Run full pipeline (all 3 steps)
python3 scripts/run_pipeline.py

# Option 2: Run individual steps
python3 scripts/run_step1.py      # Generate SQL
python3 scripts/run_step2.py      # Classify errors
python3 scripts/run_step3.py      # Apply corrections

# Option 3: Skip step1 (reuse existing predictions)
python3 scripts/run_pipeline.py --skip step1

# Evaluate results
python3 scripts/run_evaluation.py              # Evaluate both Step 1 and Step 3
python3 scripts/run_evaluation.py --step step1 # Evaluate only Step 1 (baseline)
python3 scripts/run_evaluation.py --step step3 # Evaluate only Step 3 (after correction)
```

## Directory Structure

```
st_ssc/
├── README.md                  # This file
├── config.yaml                # Configuration
├── prompts/                   # Prompt templates
│   ├── step1_generate_sql.txt
│   ├── step2_classify_error.txt
│   └── step3_fix_one_type.txt
├── data/                      # Processed data
│   └── bird_dev_1534.jsonl    # Converted BIRD data
├── scripts/                   # Core logic
│   ├── llm_client.py          # AIML API wrapper
│   ├── io_utils.py            # I/O utilities
│   ├── data_converter.py      # Data converter
│   ├── run_step1.py           # TODO
│   ├── run_step2.py           # TODO
│   ├── run_step3.py           # TODO
│   ├── run_pipeline.py        # TODO
│   └── run_evaluation.py      # TODO
├── outputs/                   # Experiment outputs
│   ├── step1_direct/          # Step 1 predictions
│   ├── step2_classified/      # Step 2 classifications
│   ├── step3_revised/         # Step 3 corrections
│   ├── evaluation/            # EX/VES results
│   └── ablations/             # Ablation experiments
└── results/                   # Final comparison tables
    ├── main_results.md        # TODO
    └── ablation_results.md    # TODO
```

## Current Status

✅ **Phase 1 Complete**: Infrastructure Setup
- Directory structure created
- Configuration file ready (use config.example.yaml as template)
- Core utilities implemented (llm_client, io_utils, data_converter)

✅ **Phase 2 Complete**: Pipeline Implementation
- Implemented run_step1.py, run_step2.py, run_step3.py
- Implemented run_pipeline.py
- Fine-grained 10-category error classification

✅ **Phase 3 Complete**: Evaluation Integration
- Implemented run_evaluation.py
- Integrated BIRD evaluation.py and evaluation_ves.py

🔲 **Phase 4 TODO**: Experiments
- Run full pipeline on 1,534 samples
- Run ablation experiments
- Compare with baselines

🔲 **Phase 5 TODO**: Results Analysis
- Implement summarize_results.py
- Generate comparison tables
- Analyze improvement over baseline

## Testing

### Test I/O Utilities

```bash
cd scripts
python3 io_utils.py
```

Expected: All tests pass ✅

### Test Data Conversion (Small Sample)

```bash
python3 scripts/data_converter.py \
    --bird_json ../data/dev.json \
    --db_root ../data/dev_databases/ \
    --output data/bird_dev_test.jsonl \
    --limit 5
```

Expected: Creates `data/bird_dev_test.jsonl` with 5 samples

### Test API Connection

```bash
python3 scripts/llm_client.py YOUR_API_KEY
```

Expected: Returns a generated SQL query (not an error)

## Configuration Options

See `config.yaml` for all configuration options:

- **llm.model**: AIML model identifier (default: `openai/gpt-5-1`)
- **llm.temperature**: Sampling temperature (default: 0.0 for deterministic)
- **llm.reasoning_effort**: Reasoning level (low/medium/high)
- **experiment.sample_limit**: Limit samples for testing (0 = all data)

## Error Types (Fine-grained 10 Categories)

The framework classifies SQL errors into 10 specific types for targeted corrections:

1. **no_error**: SQL is completely correct (no correction needed)
2. **missing_school_filter**: Missing `rtype='S'` or `rtype='D'` filter (common in BIRD california_schools)
3. **string_value_mismatch**: String literals don't match actual database values
4. **missing_aggregation**: Needs SUM/COUNT/AVG/MAX/MIN but missing
5. **wrong_aggregation**: Wrong aggregation function or aggregating already-aggregated data
6. **missing_subquery**: Needs nested query for comparisons (e.g., "above average")
7. **wrong_query_architecture**: Fundamental structure error (JOIN vs subquery)
8. **output_columns_wrong**: SELECT returns wrong columns (too many, too few, or wrong ones)
9. **missing_join**: Multi-table query missing necessary JOIN
10. **wrong_filter_logic**: WHERE conditions incorrect, missing, or excessive

**Why 10 categories?** Coarse-grained classification (4 types) led to pattern-based fixes that made errors worse. Fine-grained classification enables precise, targeted corrections.

## Troubleshooting

### API Key Error (401)

Check that your API key in `config.yaml` is correct and has GPT-5.1 access.

### Model Not Found (404)

Verify model name is `openai/gpt-5-1` (with forward slash, not dot).

### Rate Limiting (429)

The client automatically retries with backoff. If persistent, contact AIML support.

### Database Not Found

Ensure `../data/dev_databases/` path is correct relative to `st_ssc/` directory.

## Next Steps

1. **Implement Pipeline Scripts** (run_step1.py, run_step2.py, run_step3.py)
2. **Test with Small Sample** (5-10 samples)
3. **Run Full Pipeline** (1,534 samples)
4. **Evaluate Results** (EX/VES metrics)
5. **Run Ablations** (compare with baselines)
6. **Generate Tables** (for paper/report)

## Contact

For issues or questions about this framework, please consult the implementation plan at:
`/Users/kelsonqu/.claude/plans/stateless-gliding-parasol.md`
