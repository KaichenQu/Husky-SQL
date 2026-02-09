#!/usr/bin/env python3
"""
Step 3: Targeted Correction
Revise SQL to fix ONLY the classified error type
"""

import os
import sys
import yaml
import argparse
from tqdm import tqdm
from collections import Counter

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))
from llm_client import LLMClient
from io_utils import read_jsonl, write_jsonl, load_text, format_prompt


def correct_sql_step3(step2_output_path: str, data_path: str, config: dict, output_path: str) -> None:
    """
    Step 3: Apply targeted correction based on error type

    Args:
        step2_output_path: Path to Step 2 classifications
        data_path: Path to original JSONL data (for db_context)
        config: Configuration dictionary
        output_path: Output path for revised SQL
    """
    print("=" * 60)
    print("Step 3: Targeted Correction")
    print("=" * 60)
    print()

    # Load Step 2 classifications
    print(f"Loading Step 2 classifications from {step2_output_path}...")
    classifications = read_jsonl(step2_output_path)
    print(f"Loaded {len(classifications)} classifications")

    # Load original data for db_context
    print(f"Loading original data from {data_path}...")
    data = read_jsonl(data_path)
    data_dict = {item['id']: item for item in data}
    print(f"Loaded {len(data)} data items")
    print()

    # Initialize LLM client
    llm_config = config['llm']
    client = LLMClient(
        model=llm_config['model'],
        api_key=llm_config['api_key'],
        temperature=llm_config['temperature'],
        max_tokens=llm_config['max_tokens'],
        timeout=llm_config['timeout'],
        reasoning_effort=llm_config.get('reasoning_effort')
    )
    print(f"Model: {llm_config['model']}")
    print()

    # Load prompt template
    prompt_path = config['prompts']['step3']
    prompt_template = load_text(prompt_path)
    print(f"Loaded prompt template from {prompt_path}")
    print()

    # Apply corrections
    revisions = []
    errors = 0
    no_error_count = 0
    skipped_empty = 0
    changed_count = 0

    print("Applying targeted corrections...")
    for item in tqdm(classifications, desc="Step 3"):
        item_id = item['id']

        # Get original data
        if item_id not in data_dict:
            print(f"Warning: ID {item_id} not found in original data")
            continue

        original_item = data_dict[item_id]

        # If no_error, keep original SQL unchanged
        if item['error_type'] == 'no_error':
            revised_sql = item['sql']
            no_error_count += 1
        elif item['sql'].startswith("ERROR:") or item['sql'].strip() == "":
            # Skip corrections for failed/empty generations (NO-OP)
            revised_sql = item['sql']
            skipped_empty += 1
        else:
            # Format prompt with error type
            prompt = format_prompt(
                prompt_template,
                error_type=item['error_type'],
                db_context=original_item['db_context'],
                question=original_item['question'],
                sql=item['sql']
            )

            # Call LLM
            result = client.complete(
                prompt,
                system_prompt="You are an expert SQL corrector that fixes errors precisely."
            )

            # Check for errors or empty results
            if result.startswith("ERROR:"):
                errors += 1
                revised_sql = item['sql']  # Keep original on error
            elif result.strip() == "":
                errors += 1
                revised_sql = item['sql']  # Keep original on empty result (don't clear SQL)
            else:
                revised_sql = result.strip()

                # Check if SQL changed
                if revised_sql != item['sql']:
                    changed_count += 1

        # Save revision
        revisions.append({
            "id": item['id'],
            "db_id": item['db_id'],
            "question": item['question'],
            "original_sql": item['sql'],
            "error_type": item['error_type'],
            "sql": revised_sql
        })

    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    write_jsonl(output_path, revisions)

    # Compute statistics
    error_type_counts = Counter(r['error_type'] for r in revisions)

    # Print summary
    print()
    print("=" * 60)
    print("Step 3 Complete!")
    print("=" * 60)
    print(f"Total samples: {len(revisions)}")
    print(f"Correction errors: {errors}")
    print(f"No-error (unchanged): {no_error_count}")
    print(f"Skipped empty/failed SQL: {skipped_empty}")
    print(f"Changed by correction: {changed_count}")
    print()
    print("Error Type Distribution:")
    for error_type, count in error_type_counts.most_common():
        percentage = (count / len(revisions)) * 100 if revisions else 0
        print(f"  {error_type:15s}: {count:4d} ({percentage:5.1f}%)")
    print()
    print(f"Output saved to: {output_path}")
    print()

    if errors > 0:
        print("⚠️  Warning: Some corrections failed. Original SQL kept.")


def main():
    parser = argparse.ArgumentParser(
        description='Step 3: Apply targeted SQL corrections',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default config
  python run_step3.py

  # Run with custom paths
  python run_step3.py --step2 ../outputs/step2_classified/classified.jsonl
        """
    )

    parser.add_argument('--config', type=str, default='config.yaml',
                        help='Path to config.yaml')
    parser.add_argument('--step2', type=str, default=None,
                        help='Override Step 2 output path from config')
    parser.add_argument('--data', type=str, default=None,
                        help='Override original data path from config')
    parser.add_argument('--output', type=str, default=None,
                        help='Override output path from config')

    args = parser.parse_args()

    # Load config
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    # Determine paths
    step2_path = args.step2 if args.step2 else config['outputs']['step2_classified']
    data_path = args.data if args.data else config['data']['converted_jsonl']
    output_path = args.output if args.output else config['outputs']['step3_revised']

    # Run Step 3
    correct_sql_step3(step2_path, data_path, config, output_path)


if __name__ == '__main__':
    main()
