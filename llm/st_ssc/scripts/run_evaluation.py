#!/usr/bin/env python3
"""
Evaluation Wrapper
Converts ST-SSC outputs to BIRD format and runs evaluation scripts
"""

import os
import sys
import json
import yaml
import argparse
import subprocess

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))
from io_utils import read_jsonl, write_json


def convert_to_bird_format(jsonl_path: str, output_dir: str, data_mode: str = 'dev') -> str:
    """
    Convert JSONL predictions to BIRD evaluation format

    Expected format for evaluation.py:
    {"0": "SELECT ...\t----- bird -----\tdb_id", ...}

    Args:
        jsonl_path: Path to JSONL predictions
        output_dir: Output directory
        data_mode: Data mode (dev/test)

    Returns:
        Path to output directory
    """
    print(f"Converting {jsonl_path} to BIRD format...")

    data = read_jsonl(jsonl_path)

    formatted = {}
    for item in data:
        idx = item['id']
        sql = item['sql']
        db_id = item['db_id']

        # Skip error messages
        if sql.startswith("ERROR:"):
            sql = "SELECT 1"  # Placeholder for failed queries

        # Format: "SQL\t----- bird -----\tdb_id"
        formatted[idx] = f"{sql}\t----- bird -----\t{db_id}"

    # Save as JSON
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"predict_{data_mode}.json")

    write_json(output_path, formatted)

    print(f"✅ Converted {len(formatted)} predictions to {output_path}")
    return output_dir


def run_ex_evaluation(pred_dir: str, config: dict, data_mode: str = 'dev') -> dict:
    """
    Run EX (Execution Accuracy) evaluation

    Args:
        pred_dir: Directory containing predict_dev.json
        config: Configuration dictionary
        data_mode: Data mode

    Returns:
        Evaluation results dictionary
    """
    print()
    print("Running EX (Execution Accuracy) evaluation...")
    print("-" * 60)

    # Get paths from config
    eval_config = config['evaluation']
    data_config = config['data']

    ex_script = eval_config['ex_script']
    gt_path = os.path.dirname(data_config['bird_dev_gold_sql'])
    db_root = data_config['bird_dev_databases']
    diff_json = data_config['bird_dev_json']
    num_cpus = eval_config['num_cpus']
    meta_timeout = eval_config['meta_timeout']

    # Ensure paths end with '/' for evaluation script
    if not pred_dir.endswith('/'):
        pred_dir = pred_dir + '/'
    if not gt_path.endswith('/'):
        gt_path = gt_path + '/'

    # Build command
    cmd = [
        'python3', ex_script,
        '--predicted_sql_path', pred_dir,
        '--ground_truth_path', gt_path,
        '--data_mode', data_mode,
        '--db_root_path', db_root,
        '--diff_json_path', diff_json,
        '--num_cpus', str(num_cpus),
        '--meta_time_out', str(meta_timeout)
    ]

    print(f"Command: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        print(f"❌ EX evaluation failed: {e}")
        return {"error": str(e)}


def run_ves_evaluation(pred_dir: str, config: dict, data_mode: str = 'dev') -> dict:
    """
    Run VES (Valid Efficiency Score) evaluation

    Args:
        pred_dir: Directory containing predict_dev.json
        config: Configuration dictionary
        data_mode: Data mode

    Returns:
        Evaluation results dictionary
    """
    print()
    print("Running VES (Valid Efficiency Score) evaluation...")
    print("-" * 60)

    # Get paths from config
    eval_config = config['evaluation']
    data_config = config['data']

    ves_script = eval_config['ves_script']
    gt_path = os.path.dirname(data_config['bird_dev_gold_sql'])
    db_root = data_config['bird_dev_databases']
    diff_json = data_config['bird_dev_json']
    num_cpus = eval_config['num_cpus']
    meta_timeout = eval_config['meta_timeout']

    # Ensure paths end with '/' for evaluation script
    if not pred_dir.endswith('/'):
        pred_dir = pred_dir + '/'
    if not gt_path.endswith('/'):
        gt_path = gt_path + '/'

    # Build command
    cmd = [
        'python3', ves_script,
        '--predicted_sql_path', pred_dir,
        '--ground_truth_path', gt_path,
        '--data_mode', data_mode,
        '--db_root_path', db_root,
        '--diff_json_path', diff_json,
        '--num_cpus', str(num_cpus),
        '--meta_time_out', str(meta_timeout)
    ]

    print(f"Command: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        print(f"❌ VES evaluation failed: {e}")
        return {"error": str(e)}


def evaluate_pipeline(config_path: str, step: str = 'both', metric: str = 'both') -> None:
    """
    Evaluate ST-SSC pipeline outputs

    Args:
        config_path: Path to config.yaml
        step: Which step to evaluate ('step1', 'step3', or 'both')
        metric: Which metric to compute ('ex', 'ves', or 'both')
    """
    print("=" * 70)
    print("ST-SSC Evaluation")
    print("=" * 70)
    print()

    # Load config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    eval_output_dir = 'outputs/evaluation'
    os.makedirs(eval_output_dir, exist_ok=True)

    # Determine which steps to evaluate
    steps_to_eval = []
    if step in ['step1', 'both']:
        steps_to_eval.append(('step1', config['outputs']['step1_direct']))
    if step in ['step3', 'both']:
        steps_to_eval.append(('step3', config['outputs']['step3_revised']))

    # Evaluate each step
    for step_name, jsonl_path in steps_to_eval:
        print()
        print(f"{'=' * 70}")
        print(f"Evaluating {step_name.upper()}")
        print(f"{'=' * 70}")

        # Convert to BIRD format
        bird_dir = os.path.join(eval_output_dir, f"{step_name}_bird")
        convert_to_bird_format(jsonl_path, bird_dir)

        # Run evaluations
        if metric in ['ex', 'both']:
            ex_result = run_ex_evaluation(bird_dir, config)
            print(ex_result['stdout'])
            if ex_result.get('stderr'):
                print("Errors:", ex_result['stderr'])

        if metric in ['ves', 'both']:
            ves_result = run_ves_evaluation(bird_dir, config)
            print(ves_result['stdout'])
            if ves_result.get('stderr'):
                print("Errors:", ves_result['stderr'])

    print()
    print("=" * 70)
    print("Evaluation Complete!")
    print("=" * 70)
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate ST-SSC pipeline outputs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate both steps (Step 1 and Step 3) with both metrics
  python run_evaluation.py

  # Evaluate only Step 3
  python run_evaluation.py --step step3

  # Evaluate only EX metric
  python run_evaluation.py --metric ex

  # Evaluate Step 1 with VES only
  python run_evaluation.py --step step1 --metric ves
        """
    )

    parser.add_argument('--config', type=str, default='config.yaml',
                        help='Path to config.yaml')
    parser.add_argument('--step', type=str, default='both',
                        choices=['step1', 'step3', 'both'],
                        help='Which step to evaluate')
    parser.add_argument('--metric', type=str, default='both',
                        choices=['ex', 'ves', 'both'],
                        help='Which metric to compute')

    args = parser.parse_args()

    # Run evaluation
    evaluate_pipeline(args.config, args.step, args.metric)


if __name__ == '__main__':
    main()
