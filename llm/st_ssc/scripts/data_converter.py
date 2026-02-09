#!/usr/bin/env python3
"""
Data Converter: BIRD JSON → JSONL
Converts BIRD dev.json format to ST-SSC pipeline format
"""

import os
import sys
import sqlite3
import argparse
from typing import Dict, List

# Add parent directory to path to import io_utils
sys.path.insert(0, os.path.dirname(__file__))
from io_utils import read_json, write_jsonl


def get_db_schema(db_path: str) -> str:
    """
    Extract CREATE TABLE statements from SQLite database

    Args:
        db_path: Path to SQLite database file

    Returns:
        Concatenated CREATE TABLE statements
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        schemas = []
        for table in tables:
            table_name = table[0]
            if table_name == 'sqlite_sequence':
                continue

            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")
            result = cursor.fetchone()
            if result:
                create_stmt = result[0]
                schemas.append(create_stmt)

        conn.close()
        return "\n\n".join(schemas)

    except sqlite3.Error as e:
        print(f"Warning: Error reading database {db_path}: {e}")
        return ""


def convert_bird_to_jsonl(bird_json_path: str, db_root_path: str, output_path: str, limit: int = 0) -> None:
    """
    Convert BIRD dev.json to JSONL format for ST-SSC pipeline

    Args:
        bird_json_path: Path to dev.json
        db_root_path: Path to dev_databases/
        output_path: Output JSONL path
        limit: Optional limit on number of samples (0 = all)
    """
    print(f"Loading BIRD data from {bird_json_path}...")
    data = read_json(bird_json_path)

    # Apply limit if specified
    if limit > 0:
        data = data[:limit]
        print(f"Processing first {limit} samples (test mode)")
    else:
        print(f"Processing all {len(data)} samples")

    converted = []
    for idx, item in enumerate(data):
        if idx % 100 == 0:
            print(f"Processing sample {idx}/{len(data)}...")

        db_id = item['db_id']
        question = item['question']
        evidence = item.get('evidence', '')
        gold_sql = item.get('SQL', '')

        # Get database schema
        db_path = os.path.join(db_root_path, db_id, f"{db_id}.sqlite")
        if os.path.exists(db_path):
            schema = get_db_schema(db_path)
        else:
            schema = ""
            print(f"Warning: Database not found at {db_path}")

        # Build context: schema + optional evidence
        db_context = schema
        if evidence:
            db_context += f"\n\n-- External Knowledge: {evidence}"

        converted.append({
            "id": str(idx),
            "db_id": db_id,
            "question": question,
            "evidence": evidence,
            "db_context": db_context,
            "gold_sql": gold_sql
        })

    # Create output directory if needed
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write JSONL
    write_jsonl(output_path, converted)

    print(f"\n✅ Successfully converted {len(converted)} samples to {output_path}")
    print(f"   Average db_context length: {sum(len(x['db_context']) for x in converted) / len(converted):.0f} chars")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Convert BIRD dev.json to JSONL format for ST-SSC pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert full dataset
  python data_converter.py --bird_json ../data/dev.json --db_root ../data/dev_databases/ --output data/bird_dev_1534.jsonl

  # Convert first 10 samples for testing
  python data_converter.py --bird_json ../data/dev.json --db_root ../data/dev_databases/ --output data/bird_dev_test.jsonl --limit 10
        """
    )

    parser.add_argument('--bird_json', type=str, required=True, help='Path to BIRD dev.json')
    parser.add_argument('--db_root', type=str, required=True, help='Path to dev_databases/ directory')
    parser.add_argument('--output', type=str, required=True, help='Output JSONL path')
    parser.add_argument('--limit', type=int, default=0, help='Limit number of samples (0 = all)')

    args = parser.parse_args()

    convert_bird_to_jsonl(args.bird_json, args.db_root, args.output, args.limit)
