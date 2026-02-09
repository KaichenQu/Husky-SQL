# ST-SSC Quick Start Guide

**Completion Status**: ✅ Phase 1 & 2 Complete (Infrastructure + Pipeline)

## 🎉 Completed Work

### Phase 1: Infrastructure ✅
- ✅ Directory structure created
- ✅ Configuration file (`config.yaml`) created
- ✅ 3 prompt templates completed (Step 1/2/3)
- ✅ Core utilities implemented:
  - `llm_client.py` - AIML API client
  - `io_utils.py` - I/O utilities
  - `data_converter.py` - Data converter

### Phase 2: Pipeline Implementation ✅
- ✅ `run_step1.py` - SQL generation
- ✅ `run_step2.py` - Error classification
- ✅ `run_step3.py` - Targeted correction
- ✅ `run_pipeline.py` - End-to-end orchestration
- ✅ `run_evaluation.py` - Evaluation wrapper

## 🚀 Quick Start (3 Steps)

### Step 0: Configure API Key

Edit `config.yaml`:

```bash
cd /Users/kelsonqu/Desktop/new\ bird/bird/llm/st_ssc
nano config.yaml  # or use your preferred editor
```

Find and replace:
```yaml
llm:
  api_key: "YOUR_AIML_API_KEY_HERE"  # ← Replace this!
```

### Step 1: Convert Data (First Run)

```bash
cd /Users/kelsonqu/Desktop/new\ bird/bird/llm/st_ssc

# Small sample test (5 entries)
python3 scripts/data_converter.py \
    --bird_json ../data/dev.json \
    --db_root ../data/dev_databases/ \
    --output data/bird_dev_test.jsonl \
    --limit 5

# Verify
python3 -c "from scripts.io_utils import read_jsonl; print(f'Converted successfully: {len(read_jsonl(\"data/bird_dev_test.jsonl\"))} entries')"
```

### Step 2: Test API Connection

```bash
cd scripts
python3 llm_client.py YOUR_AIML_API_KEY
```

**Expected output**: Should return a SQL query (not an error)

### Step 3: Run Small Sample Test

First, modify `config.yaml` to set test limit:

```yaml
experiment:
  sample_limit: 5  # Test with 5 entries
```

Then run the pipeline:

```bash
cd /Users/kelsonqu/Desktop/new\ bird/bird/llm/st_ssc
python3 scripts/run_pipeline.py
```

**Expected process**:
1. Step 1 generates 5 SQL queries ✅
2. Step 2 classifies 5 error types ✅
3. Step 3 corrects 5 SQL queries ✅

## 📊 View Results

### Check Output Files

```bash
cd /Users/kelsonqu/Desktop/new\ bird/bird/llm/st_ssc

# Step 1 output
cat outputs/step1_direct/predictions.jsonl | head -3

# Step 2 output
cat outputs/step2_classified/classified.jsonl | head -3

# Step 3 output
cat outputs/step3_revised/revised.jsonl | head -3
```

### Quick Statistics

```python
python3 << 'EOF'
from scripts.io_utils import read_jsonl
from collections import Counter

step1 = read_jsonl('outputs/step1_direct/predictions.jsonl')
step2 = read_jsonl('outputs/step2_classified/classified.jsonl')
step3 = read_jsonl('outputs/step3_revised/revised.jsonl')

print(f"Step 1: {len(step1)} predictions")
print(f"Step 2: {len(step2)} classifications")
print(f"Step 3: {len(step3)} revisions")
print()

error_types = Counter(x['error_type'] for x in step2)
print("Error Type Distribution:")
for et, count in error_types.most_common():
    print(f"  {et}: {count}")
EOF
```

## 🔬 Run Evaluation (Optional, requires ground truth)

```bash
cd /Users/kelsonqu/Desktop/new\ bird/bird/llm/st_ssc

# Evaluate Step 1 and Step 3
python3 scripts/run_evaluation.py

# Evaluate Step 3 only
python3 scripts/run_evaluation.py --step step3

# Run EX metric only
python3 scripts/run_evaluation.py --metric ex
```

## 🎯 Full Dataset Run

After successful testing, run on complete dataset:

### 1. Convert Complete Data

```bash
cd /Users/kelsonqu/Desktop/new\ bird/bird/llm/st_ssc

python3 scripts/data_converter.py \
    --bird_json ../data/dev.json \
    --db_root ../data/dev_databases/ \
    --output data/bird_dev_1534.jsonl
```

### 2. Modify Configuration

Edit `config.yaml`:

```yaml
experiment:
  sample_limit: 0  # 0 = process all data
```

### 3. Run Complete Pipeline

```bash
python3 scripts/run_pipeline.py
```

**Estimated time**: 2-4 hours (depending on API speed and 1,534 entries)

## 🛠️ Common Commands

### Run Each Step Individually

```bash
cd /Users/kelsonqu/Desktop/new\ bird/bird/llm/st_ssc

# Step 1 only
python3 scripts/run_step1.py

# Step 2 only
python3 scripts/run_step2.py

# Step 3 only
python3 scripts/run_step3.py
```

### Skip Completed Steps

```bash
# Skip Step 1 (use existing predictions)
python3 scripts/run_pipeline.py --skip step1

# Start from Step 3
python3 scripts/run_pipeline.py --skip step1 --skip step2
```

### Verify Setup

```bash
cd /Users/kelsonqu/Desktop/new\ bird/bird/llm/st_ssc
./test_setup.sh
```

## 📁 Output Files Description

| File | Description |
|------|------|
| `outputs/step1_direct/predictions.jsonl` | Initial SQL predictions |
| `outputs/step2_classified/classified.jsonl` | SQL with error type labels |
| `outputs/step3_revised/revised.jsonl` | Corrected SQL |
| `outputs/evaluation/step1_bird/predict_dev.json` | Step 1 BIRD format (for evaluation) |
| `outputs/evaluation/step3_bird/predict_dev.json` | Step 3 BIRD format (for evaluation) |

## 🔍 Debugging Tips

### View Detailed Errors

If a step fails, check error messages:

```bash
# Check Step 1 errors
python3 << 'EOF'
from scripts.io_utils import read_jsonl
step1 = read_jsonl('outputs/step1_direct/predictions.jsonl')
errors = [x for x in step1 if x['sql'].startswith('ERROR:')]
print(f"Found {len(errors)} errors")
for err in errors[:3]:  # Show first 3
    print(f"ID {err['id']}: {err['sql']}")
EOF
```

### Test API Connection

```bash
cd scripts
python3 llm_client.py YOUR_API_KEY
```

### Check YAML Configuration

```bash
python3 -c "import yaml; print(yaml.safe_load(open('config.yaml')))"
```

## 📊 Next Steps: Results Analysis (TODO)

After completing the pipeline run:

1. **Implement `summarize_results.py`**:
   - Generate comparison tables
   - Analyze improvements by error type
   - Generate markdown reports

2. **Run ablation experiments**:
   - Direct correction without classification
   - Multiple error types simultaneously

3. **Prepare research report**:
   - Main results table
   - Ablation results
   - Error analysis

## 🆘 Troubleshooting

### API Key Error (401)
Check if the API key in `config.yaml` is correct.

### Model Not Found (404)
Confirm the model name is `openai/gpt-5-1` (use forward slash, not dot).

### Rate Limit (429)
The client will automatically retry. If it persists, wait or contact AIML support.

### Database Not Found
Confirm the `../data/dev_databases/` path is correct.

## 📞 Get Help

- View detailed plan: `/Users/kelsonqu/.claude/plans/stateless-gliding-parasol.md`
- View README: `README.md`
- Run setup verification: `./test_setup.sh`

---

**Current Version**: Phase 1 & 2 Complete ✅
**Last Updated**: Just now
