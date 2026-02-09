#!/bin/bash
# Complete evaluation and HTML generation workflow - GPT-5.1

# Activate conda environment (if exists)
if [ -f "/opt/homebrew/anaconda3/bin/activate" ]; then
    source /opt/homebrew/anaconda3/bin/activate cv
fi

cd "$(dirname "$0")/.."

db_root_path='./data/dev_databases/'
data_mode='dev'
diff_json_path='./data/dev.json'
predicted_sql_path_kg='./exp_result/gpt51_output_kg/'
predicted_sql_path='./exp_result/gpt51_output/'
ground_truth_path='./data/'
num_cpus=16
meta_time_out=30.0
mode_gt='gt'
mode_predict='gpt51'

echo "=========================================="
echo "🚀 GPT-5.1 Complete Evaluation Pipeline"
echo "=========================================="
echo ""

# Step 1: Clean SQL format
echo "📝 Step 1/4: Cleaning SQL format..."
python3 fix_sql_format.py --input ${predicted_sql_path}predict_dev.json --output ${predicted_sql_path}predict_dev.json
python3 fix_sql_format.py --input ${predicted_sql_path_kg}predict_dev.json --output ${predicted_sql_path_kg}predict_dev.json
echo "✅ SQL format cleaning complete"
echo ""

# Step 2: Run evaluation
echo "📊 Step 2/4: Running evaluation (EX and VES)..."
echo ""

echo "--- Evaluating with knowledge (EX) ---"
# Use tee to simultaneously display progress and save logs
python3 -u ./src/evaluation.py --db_root_path ${db_root_path} --predicted_sql_path ${predicted_sql_path_kg} --data_mode ${data_mode} \
--ground_truth_path ${ground_truth_path} --num_cpus ${num_cpus} --mode_gt ${mode_gt} --mode_predict ${mode_predict} \
--diff_json_path ${diff_json_path} --meta_time_out ${meta_time_out} 2>&1 | tee ${predicted_sql_path_kg}eval_ex.log

echo ""
echo "--- Evaluating without knowledge (EX) ---"
python3 -u ./src/evaluation.py --db_root_path ${db_root_path} --predicted_sql_path ${predicted_sql_path} --data_mode ${data_mode} \
--ground_truth_path ${ground_truth_path} --num_cpus ${num_cpus} --mode_gt ${mode_gt} --mode_predict ${mode_predict} \
--diff_json_path ${diff_json_path} --meta_time_out ${meta_time_out} 2>&1 | tee ${predicted_sql_path}eval_ex.log

echo ""
echo "--- Evaluating with knowledge (VES) ---"
echo "⚠️  Note: VES evaluation is slower, each query requires multiple iterations..."
python3 -u ./src/evaluation_ves.py --db_root_path ${db_root_path} --predicted_sql_path ${predicted_sql_path_kg} --data_mode ${data_mode} \
--ground_truth_path ${ground_truth_path} --num_cpus ${num_cpus} --mode_gt ${mode_gt} --mode_predict ${mode_predict} \
--diff_json_path ${diff_json_path} --meta_time_out ${meta_time_out} 2>&1 | tee ${predicted_sql_path_kg}eval_ves.log

echo ""
echo "--- Evaluating without knowledge (VES) ---"
python3 -u ./src/evaluation_ves.py --db_root_path ${db_root_path} --predicted_sql_path ${predicted_sql_path} --data_mode ${data_mode} \
--ground_truth_path ${ground_truth_path} --num_cpus ${num_cpus} --mode_gt ${mode_gt} --mode_predict ${mode_predict} \
--diff_json_path ${diff_json_path} --meta_time_out ${meta_time_out} 2>&1 | tee ${predicted_sql_path}eval_ves.log

echo "✅ Evaluation complete"
echo ""

# Step 3: Extract evaluation results and save as JSON
echo "📋 Step 3/4: Extracting evaluation results..."
python3 << 'PYTHON_SCRIPT'
import json
import re
import os

def extract_eval_results(log_file):
    """Extract results from evaluation log"""
    if not os.path.exists(log_file):
        return None

    with open(log_file, 'r') as f:
        content = f.read()

    results = {}

    # Extract EX results
    if 'ACCURACY' in content:
        ex_match = re.search(r'accuracy\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)', content)
        count_match = re.search(r'count\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)', content)
        
        if ex_match and count_match:
            results['ex'] = {
                'simple': {'count': int(count_match.group(1)), 'accuracy': float(ex_match.group(1))},
                'moderate': {'count': int(count_match.group(2)), 'accuracy': float(ex_match.group(2))},
                'challenging': {'count': int(count_match.group(3)), 'accuracy': float(ex_match.group(3))},
                'total': {'count': int(count_match.group(4)), 'accuracy': float(ex_match.group(4))}
            }

    # Extract VES results
    if 'VES' in content:
        ves_match = re.search(r'ves\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)', content)
        count_match = re.search(r'count\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)', content)
        
        if ves_match and count_match:
            results['ves'] = {
                'simple': {'count': int(count_match.group(1)), 'ves': float(ves_match.group(1))},
                'moderate': {'count': int(count_match.group(2)), 'ves': float(ves_match.group(2))},
                'challenging': {'count': int(count_match.group(3)), 'ves': float(ves_match.group(3))},
                'total': {'count': int(count_match.group(4)), 'ves': float(ves_match.group(4))}
            }
    
    return results if results else None

# Extract results
results_kg = {}
results_no_kg = {}

# With knowledge version
ex_log_kg = './exp_result/gpt51_output_kg/eval_ex.log'
ves_log_kg = './exp_result/gpt51_output_kg/eval_ves.log'

ex_kg = extract_eval_results(ex_log_kg)
ves_kg = extract_eval_results(ves_log_kg)

if ex_kg:
    results_kg.update(ex_kg)
if ves_kg:
    results_kg.update(ves_kg)

# Without knowledge version
ex_log = './exp_result/gpt51_output/eval_ex.log'
ves_log = './exp_result/gpt51_output/eval_ves.log'

ex = extract_eval_results(ex_log)
ves = extract_eval_results(ves_log)

if ex:
    results_no_kg.update(ex)
if ves:
    results_no_kg.update(ves)

# Save results
if results_kg:
    with open('./exp_result/gpt51_output_kg/eval_results.json', 'w') as f:
        json.dump(results_kg, f, indent=4)
    print("✅ Evaluation results with knowledge saved: exp_result/gpt51_output_kg/eval_results.json")

if results_no_kg:
    with open('./exp_result/gpt51_output/eval_results.json', 'w') as f:
        json.dump(results_no_kg, f, indent=4)
    print("✅ Evaluation results without knowledge saved: exp_result/gpt51_output/eval_results.json")

PYTHON_SCRIPT

echo ""

# Step 4: Generate HTML files
echo "🌐 Step 4/4: Generating HTML files..."
cd ../json_to_html

# Generate HTML for with knowledge version
python3 json_to_html.py \
    --input ../llm/exp_result/gpt51_output_kg/predict_dev.json \
    --output ../llm/exp_result/gpt51_output_kg/predict_dev.html \
    --title "GPT-5.1 Predictions (with Knowledge)" \
    --questions ../llm/data/dev.json \
    --eval-results ../llm/exp_result/gpt51_output_kg/eval_results.json

# Generate HTML for without knowledge version
python3 json_to_html.py \
    --input ../llm/exp_result/gpt51_output/predict_dev.json \
    --output ../llm/exp_result/gpt51_output/predict_dev.html \
    --title "GPT-5.1 Predictions (without Knowledge)" \
    --questions ../llm/data/dev.json \
    --eval-results ../llm/exp_result/gpt51_output/eval_results.json

echo ""
echo "=========================================="
echo "✅ Complete!"
echo "=========================================="
echo ""
echo "📊 Evaluation results saved:"
echo "   - exp_result/gpt51_output_kg/eval_results.json"
echo "   - exp_result/gpt51_output/eval_results.json"
echo ""
echo "🌐 HTML files generated:"
echo "   - exp_result/gpt51_output_kg/predict_dev.html"
echo "   - exp_result/gpt51_output/predict_dev.html"
echo ""
echo "💡 Open HTML files in browser to view results"

