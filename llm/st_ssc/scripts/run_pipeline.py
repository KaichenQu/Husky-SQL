#!/usr/bin/env python3
"""
ST-SSC Pipeline Orchestrator
Runs all three steps sequentially: Generation → Classification → Correction
"""

import os
import sys
import yaml
import argparse
import time
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import step modules
from run_step1 import generate_sql_step1
from run_step2 import classify_errors_step2
from run_step3 import correct_sql_step3


def run_full_pipeline(config_path: str, skip_steps: list = None) -> None:
    """
    Run complete ST-SSC pipeline

    Args:
        config_path: Path to config.yaml
        skip_steps: Optional list of steps to skip (e.g., ['step1'])
    """
    if skip_steps is None:
        skip_steps = []

    print("=" * 70)
    print("ST-SSC Pipeline: Step-wise Single-type Self-Correction")
    print("=" * 70)
    print()
    print(f"Config: {config_path}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Print configuration summary
    print("Configuration Summary:")
    print(f"  Model: {config['llm']['model']}")
    print(f"  Temperature: {config['llm']['temperature']}")
    print(f"  Reasoning effort: {config['llm'].get('reasoning_effort', 'none')}")
    print(f"  Sample limit: {config['experiment']['sample_limit']} (0 = all)")
    print()

    # Paths
    data_path = config['data']['converted_jsonl']
    step1_output = config['outputs']['step1_direct']
    step2_output = config['outputs']['step2_classified']
    step3_output = config['outputs']['step3_revised']

    # Track timing
    step_times = {}
    total_start = time.time()

    # Step 1: SQL Generation
    if 'step1' not in skip_steps:
        print()
        print("▶️  Starting Step 1: SQL Generation")
        print("-" * 70)
        step1_start = time.time()

        try:
            generate_sql_step1(data_path, config, step1_output)
            step_times['step1'] = time.time() - step1_start
            print(f"✅ Step 1 completed in {step_times['step1']:.1f}s")
        except Exception as e:
            print(f"❌ Step 1 failed: {e}")
            return
    else:
        print(f"\n⏭️  Skipping Step 1 (using existing: {step1_output})")

    # Step 2: Error Classification
    if 'step2' not in skip_steps:
        print()
        print("▶️  Starting Step 2: Error Classification")
        print("-" * 70)
        step2_start = time.time()

        try:
            classify_errors_step2(step1_output, data_path, config, step2_output)
            step_times['step2'] = time.time() - step2_start
            print(f"✅ Step 2 completed in {step_times['step2']:.1f}s")
        except Exception as e:
            print(f"❌ Step 2 failed: {e}")
            return
    else:
        print(f"\n⏭️  Skipping Step 2 (using existing: {step2_output})")

    # Step 3: Targeted Correction
    if 'step3' not in skip_steps:
        print()
        print("▶️  Starting Step 3: Targeted Correction")
        print("-" * 70)
        step3_start = time.time()

        try:
            correct_sql_step3(step2_output, data_path, config, step3_output)
            step_times['step3'] = time.time() - step3_start
            print(f"✅ Step 3 completed in {step_times['step3']:.1f}s")
        except Exception as e:
            print(f"❌ Step 3 failed: {e}")
            return
    else:
        print(f"\n⏭️  Skipping Step 3 (using existing: {step3_output})")

    # Final summary
    total_time = time.time() - total_start

    print()
    print("=" * 70)
    print("Pipeline Complete! 🎉")
    print("=" * 70)
    print()
    print("Timing Summary:")
    for step, duration in step_times.items():
        print(f"  {step}: {duration:.1f}s ({duration/60:.1f}m)")
    print(f"  Total: {total_time:.1f}s ({total_time/60:.1f}m)")
    print()
    print("Output Files:")
    print(f"  Step 1 (Direct): {step1_output}")
    print(f"  Step 2 (Classified): {step2_output}")
    print(f"  Step 3 (Revised): {step3_output}")
    print()
    print("Next steps:")
    print("  1. Run evaluation: python run_evaluation.py")
    print("  2. Compare results: Check EX/VES metrics")
    print("  3. Generate tables: python summarize_results.py")
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Run complete ST-SSC pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline
  python run_pipeline.py

  # Run with custom config
  python run_pipeline.py --config ../config.yaml

  # Skip Step 1 (use existing predictions)
  python run_pipeline.py --skip step1

  # Resume from Step 2
  python run_pipeline.py --skip step1 --skip step2
        """
    )

    parser.add_argument('--config', type=str, default='config.yaml',
                        help='Path to config.yaml')
    parser.add_argument('--skip', type=str, action='append', default=[],
                        choices=['step1', 'step2', 'step3'],
                        help='Skip specific steps (can be used multiple times)')

    args = parser.parse_args()

    # Run pipeline
    run_full_pipeline(args.config, args.skip)


if __name__ == '__main__':
    main()
