#!/usr/bin/env python3
"""
Test script to validate AIML API connection before running full batch processing.
Usage: python3 test_aiml_api.py --api_key YOUR_AIML_API_KEY
"""

import requests
import json
import argparse


def test_aiml_connection(api_key, model="openai/gpt-5-1"):
    """
    Test basic AIML API connection with a simple SQL query.

    Args:
        api_key: Your AIML API key
        model: AIML model identifier (default: openai/gpt-5-1)
    """
    print("=" * 60)
    print("AIML API Connection Test")
    print("=" * 60)
    print(f"Model: {model}")
    print(f"API Key: {api_key[:10]}..." if len(api_key) > 10 else "API Key: [HIDDEN]")
    print()

    url = "https://api.aimlapi.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Test prompt: simple SQL query generation
    test_prompt = """CREATE TABLE users (
    id INT PRIMARY KEY,
    name TEXT NOT NULL,
    age INT,
    email TEXT
);

-- Using valid SQLite, answer the following questions for the tables provided above.
-- How many users are there?
Generate the SQL after thinking step by step:
SELECT """

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a SQL expert that generates SQLite queries."},
            {"role": "user", "content": test_prompt}
        ],
        "max_tokens": 100,
        "temperature": 0,
        "stop": ['--', '\n\n', ';', '#']
    }

    print("Sending test request to AIML API...")
    print()

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        print(f"Status Code: {response.status_code}")
        print()

        if response.status_code == 200:
            result = response.json()

            print("✅ SUCCESS! API connection is working.")
            print()
            print("Response details:")
            print("-" * 60)

            # Extract the generated SQL
            if 'choices' in result and len(result['choices']) > 0:
                choice = result['choices'][0]
                if 'message' in choice and 'content' in choice['message']:
                    generated_sql = choice['message']['content']
                    print(f"Generated SQL: SELECT{generated_sql}")
                    print()

                    # Show finish reason
                    if 'finish_reason' in choice:
                        print(f"Finish reason: {choice['finish_reason']}")
                else:
                    print("⚠️  Warning: Unexpected response format")
                    print(json.dumps(result, indent=2))

            # Show token usage if available
            if 'usage' in result:
                usage = result['usage']
                print()
                print("Token Usage:")
                print(f"  Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
                print(f"  Completion tokens: {usage.get('completion_tokens', 'N/A')}")
                print(f"  Total tokens: {usage.get('total_tokens', 'N/A')}")

            print()
            print("=" * 60)
            print("✅ Your AIML API is configured correctly!")
            print("You can now proceed to run: ./run/run_gpt51.sh")
            print("=" * 60)

            return True

        elif response.status_code == 401:
            print("❌ ERROR: Authentication failed (401 Unauthorized)")
            print()
            print("Possible issues:")
            print("  1. Invalid API key")
            print("  2. API key has expired")
            print("  3. API key doesn't have access to GPT-5.1")
            print()
            print("Please check your AIML API key and try again.")
            return False

        elif response.status_code == 404:
            print(f"❌ ERROR: Model not found (404)")
            print()
            print("Response:")
            print(json.dumps(response.json(), indent=2))
            print()
            print("Possible issues:")
            print(f"  1. Model identifier '{model}' is incorrect")
            print("  2. Model is not available in your AIML account")
            print()
            print("Try one of these alternatives:")
            print("  - openai/gpt-5-1")
            print("  - openai/gpt-5-1-chat-latest")
            print("  - openai/gpt-5-2")
            return False

        elif response.status_code == 429:
            print("❌ ERROR: Rate limit exceeded (429)")
            print()
            print("You're making too many requests. Please wait and try again.")
            print("The backoff mechanism in aiml_request.py will handle this during batch processing.")
            return False

        else:
            print(f"❌ ERROR: Request failed with status code {response.status_code}")
            print()
            print("Response:")
            print(json.dumps(response.json(), indent=2))
            return False

    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out")
        print()
        print("The API request took too long to respond. This might be a temporary issue.")
        print("Please try again or check your internet connection.")
        return False

    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Connection failed")
        print()
        print("Could not connect to AIML API. Please check:")
        print("  1. Your internet connection")
        print("  2. The API endpoint URL is correct")
        print("  3. No firewall is blocking the connection")
        return False

    except Exception as e:
        print(f"❌ ERROR: Unexpected error occurred")
        print()
        print(f"Error details: {e}")
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Test AIML API connection for GPT-5.1',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 test_aiml_api.py --api_key your_api_key_here
  python3 test_aiml_api.py --api_key your_key --model openai/gpt-5-2
        """
    )

    parser.add_argument(
        '--api_key',
        type=str,
        required=True,
        help='Your AIML API key'
    )

    parser.add_argument(
        '--model',
        type=str,
        default='openai/gpt-5-1',
        help='AIML model identifier (default: openai/gpt-5-1)'
    )

    args = parser.parse_args()

    # Run the test
    success = test_aiml_connection(args.api_key, args.model)

    # Exit with appropriate code
    exit(0 if success else 1)
