#!/usr/bin/env python3
"""
I/O Utilities for ST-SSC Framework
Handles reading/writing JSON, JSONL, and text files
"""

import json
from typing import Dict, List, Iterable, Any


def read_jsonl(path: str) -> List[Dict]:
    """
    Read JSONL file into list of dicts

    Args:
        path: Path to JSONL file

    Returns:
        List of dictionaries
    """
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping invalid JSON line: {line[:50]}...")
                continue
    return rows


def write_jsonl(path: str, rows: Iterable[Dict]) -> None:
    """
    Write list of dicts to JSONL file

    Args:
        path: Output path
        rows: Iterable of dictionaries
    """
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def read_json(path: str) -> Any:
    """
    Read JSON file

    Args:
        path: Path to JSON file

    Returns:
        Parsed JSON data
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, data: Any) -> None:
    """
    Write JSON file

    Args:
        path: Output path
        data: Data to write
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_text(path: str) -> str:
    """
    Load text file

    Args:
        path: Path to text file

    Returns:
        File contents as string
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def format_prompt(template: str, **kwargs) -> str:
    """
    Format prompt template with variables

    Args:
        template: Template string with {var} placeholders
        **kwargs: Variables to substitute

    Returns:
        Formatted string
    """
    return template.format(**kwargs)


if __name__ == '__main__':
    # Quick test
    import tempfile
    import os

    # Test JSONL
    test_data = [
        {"id": "0", "text": "test1"},
        {"id": "1", "text": "test2"}
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        jsonl_path = os.path.join(tmpdir, "test.jsonl")

        # Write and read JSONL
        write_jsonl(jsonl_path, test_data)
        read_data = read_jsonl(jsonl_path)

        assert len(read_data) == 2
        assert read_data[0]["id"] == "0"
        print("✓ JSONL read/write test passed")

        # Test JSON
        json_path = os.path.join(tmpdir, "test.json")
        write_json(json_path, {"key": "value"})
        json_data = read_json(json_path)
        assert json_data["key"] == "value"
        print("✓ JSON read/write test passed")

        # Test template formatting
        template = "Hello {name}, you are {age} years old"
        result = format_prompt(template, name="Alice", age=25)
        assert result == "Hello Alice, you are 25 years old"
        print("✓ Template formatting test passed")

    print("\nAll tests passed! ✅")
