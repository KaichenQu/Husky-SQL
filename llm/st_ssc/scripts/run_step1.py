#!/usr/bin/env python3
"""
Step 1: SQL Generation
Generate initial SQL predictions from questions using GPT-5.1
"""

import os
import sys
import yaml
import argparse
from tqdm import tqdm

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))
from llm_client import LLMClient
from io_utils import read_jsonl, write_jsonl, load_text, format_prompt


def generate_sql_step1(data_path: str, config: dict, output_path: str) -> None:
    """
    Step 1: Generate SQL from questions

    Args:
        data_path: Path to JSONL data file
        config: Configuration dictionary
        output_path: Output path for predictions
    """
    print("=" * 60)
    print("Step 1: SQL Generation")
    print("=" * 60)
    print()

    # Load data
    print(f"Loading data from {data_path}...")
    data = read_jsonl(data_path)

    # Apply sample limit if configured
    sample_limit = config['experiment']['sample_limit']
    if sample_limit > 0:
        data = data[:sample_limit]
        print(f"⚠️  Test mode: Processing first {sample_limit} samples")
    else:
        print(f"Processing all {len(data)} samples")

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
    print(f"Reasoning effort: {llm_config.get('reasoning_effort', 'none')}")
    print()

    # Load prompt template
    prompt_path = config['prompts']['step1']
    prompt_template = load_text(prompt_path)
    print(f"Loaded prompt template from {prompt_path}")
    print()

    # Generate SQL predictions
    predictions = []
    errors = 0

    print("Generating SQL predictions...")
    for item in tqdm(data, desc="Step 1"):
        # Format prompt
        prompt = format_prompt(
            prompt_template,
            db_context=item['db_context'],
            question=item['question']
        )

        # Call LLM
        result = client.complete(
            prompt,
            system_prompt="You are an expert text-to-SQL system that generates SQLite queries."
        )

        # Check for errors
        if result.startswith("ERROR:"):
            errors += 1
            sql = result  # Keep error message for debugging
        else:
            sql = result.strip()

        # Save prediction
        predictions.append({
            "id": item['id'],
            "db_id": item['db_id'],
            "question": item['question'],
            "sql": sql
        })

    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    write_jsonl(output_path, predictions)

    # Print summary
    print()
    print("=" * 60)
    print("Step 1 Complete!")
    print("=" * 60)
    print(f"Total samples: {len(predictions)}")
    print(f"Successful: {len(predictions) - errors}")
    print(f"Errors: {errors}")
    print(f"Output saved to: {output_path}")
    print()

    if errors > 0:
        print("⚠️  Warning: Some predictions failed. Check error messages in output.")


def main():
    parser = argparse.ArgumentParser(
        description='Step 1: Generate SQL predictions from questions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default config
  python run_step1.py

  # Run with custom config
  python run_step1.py --config ../config.yaml

  # Override data path
  python run_step1.py --data ../data/bird_dev_test.jsonl
        """
    )

    parser.add_argument('--config', type=str, default='config.yaml',
                        help='Path to config.yaml')
    parser.add_argument('--data', type=str, default=None,
                        help='Override data path from config')
    parser.add_argument('--output', type=str, default=None,
                        help='Override output path from config')

    args = parser.parse_args()

    # Load config
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    # Determine paths
    data_path = args.data if args.data else config['data']['converted_jsonl']
    output_path = args.output if args.output else config['outputs']['step1_direct']

    # Run Step 1
    generate_sql_step1(data_path, config, output_path)


if __name__ == '__main__':
    main()
