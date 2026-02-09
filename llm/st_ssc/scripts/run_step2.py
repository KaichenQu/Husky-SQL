#!/usr/bin/env python3
"""
Step 2: Error Classification
Classify each SQL into ONE error type
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
from io_utils import read_jsonl, write_jsonl, read_json, load_text, format_prompt


# Valid error type labels (10 fine-grained categories)
VALID_ERROR_TYPES = {
    'no_error',
    'missing_school_filter',
    'string_value_mismatch',
    'missing_aggregation',
    'wrong_aggregation',
    'missing_subquery',
    'wrong_query_architecture',
    'output_columns_wrong',
    'missing_join',
    'wrong_filter_logic'
}


def normalize_error_type(label: str) -> str:
    """
    Normalize error type label

    Args:
        label: Raw label from LLM

    Returns:
        Normalized label or default 'logic_error'
    """
    label = label.strip().lower()

    # Remove common prefixes/suffixes
    label = label.replace('error type:', '').replace('label:', '').strip()

    # Extract first word (in case model outputs explanation)
    first_word = label.split()[0] if label else ""

    # Check if valid
    if first_word in VALID_ERROR_TYPES:
        return first_word

    # Check for partial matches (handle underscore variations)
    for valid_type in VALID_ERROR_TYPES:
        if first_word in valid_type or valid_type.replace('_', '') in label.replace('_', '').replace(' ', ''):
            return valid_type

    # Fallback: conservative default
    return 'wrong_filter_logic'


def classify_errors_step2(step1_output_path: str, data_path: str, config: dict, output_path: str) -> None:
    """
    Step 2: Classify error types for each SQL

    Args:
        step1_output_path: Path to Step 1 predictions
        data_path: Path to original JSONL data (for db_context)
        config: Configuration dictionary
        output_path: Output path for classifications
    """
    print("=" * 60)
    print("Step 2: Error Classification")
    print("=" * 60)
    print()

    # Load Step 1 predictions
    print(f"Loading Step 1 predictions from {step1_output_path}...")
    predictions = read_jsonl(step1_output_path)
    print(f"Loaded {len(predictions)} predictions")

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
    prompt_path = config['prompts']['step2']
    prompt_template = load_text(prompt_path)
    print(f"Loaded prompt template from {prompt_path}")
    print()

    # Classify errors
    classifications = []
    errors = 0

    print("Classifying error types...")
    for pred in tqdm(predictions, desc="Step 2"):
        item_id = pred['id']

        # Get original data
        if item_id not in data_dict:
            print(f"Warning: ID {item_id} not found in original data")
            continue

        original_item = data_dict[item_id]

        # Skip if Step 1 failed or returned empty SQL
        if pred['sql'].startswith("ERROR:") or pred['sql'].strip() == "":
            error_type = 'logic_error'  # Default for failed/empty generations
        else:
            # Format prompt
            prompt = format_prompt(
                prompt_template,
                db_context=original_item['db_context'],
                question=original_item['question'],
                sql=pred['sql']
            )

            # Call LLM
            result = client.complete(
                prompt,
                system_prompt="You are an expert SQL error classifier."
            )

            # Normalize error type
            if result.startswith("ERROR:"):
                errors += 1
                error_type = 'logic_error'  # Conservative fallback
            else:
                error_type = normalize_error_type(result)

        # Save classification
        classifications.append({
            "id": pred['id'],
            "db_id": pred['db_id'],
            "question": pred['question'],
            "sql": pred['sql'],
            "error_type": error_type
        })

    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    write_jsonl(output_path, classifications)

    # Compute statistics
    error_type_counts = Counter(c['error_type'] for c in classifications)

    # Print summary
    print()
    print("=" * 60)
    print("Step 2 Complete!")
    print("=" * 60)
    print(f"Total samples: {len(classifications)}")
    print(f"Classification errors: {errors}")
    print()
    print("Error Type Distribution:")
    for error_type in sorted(VALID_ERROR_TYPES):
        count = error_type_counts.get(error_type, 0)
        percentage = (count / len(classifications)) * 100 if classifications else 0
        print(f"  {error_type:15s}: {count:4d} ({percentage:5.1f}%)")
    print()
    print(f"Output saved to: {output_path}")
    print()

    if errors > 0:
        print("⚠️  Warning: Some classifications failed. Using fallback 'logic_error'.")


def main():
    parser = argparse.ArgumentParser(
        description='Step 2: Classify SQL error types',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default config
  python run_step2.py

  # Run with custom paths
  python run_step2.py --step1 ../outputs/step1_direct/predictions.jsonl
        """
    )

    parser.add_argument('--config', type=str, default='config.yaml',
                        help='Path to config.yaml')
    parser.add_argument('--step1', type=str, default=None,
                        help='Override Step 1 output path from config')
    parser.add_argument('--data', type=str, default=None,
                        help='Override original data path from config')
    parser.add_argument('--output', type=str, default=None,
                        help='Override output path from config')

    args = parser.parse_args()

    # Load config
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    # Determine paths
    step1_path = args.step1 if args.step1 else config['outputs']['step1_direct']
    data_path = args.data if args.data else config['data']['converted_jsonl']
    output_path = args.output if args.output else config['outputs']['step2_classified']

    # Run Step 2
    classify_errors_step2(step1_path, data_path, config, output_path)


if __name__ == '__main__':
    main()
