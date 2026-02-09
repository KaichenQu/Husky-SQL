#!/usr/bin/env python3
"""
AIML API Client for GPT-5.1
Wraps the AIML Chat Completions API with retry logic and error handling
"""

import requests
import time
from typing import Optional


class LLMClient:
    """
    AIML API client for GPT-5.1
    Wraps the AIML Chat Completions API
    """

    def __init__(self, model: str, api_key: str, temperature: float = 0.0,
                 max_tokens: int = 512, timeout: int = 60,
                 reasoning_effort: Optional[str] = None):
        """
        Initialize AIML API client

        Args:
            model: Model identifier (e.g., "openai/gpt-5-1")
            api_key: AIML API key
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
            reasoning_effort: Optional reasoning level ("low", "medium", "high")
        """
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.reasoning_effort = reasoning_effort
        self.base_url = "https://api.aimlapi.com/v1/chat/completions"

    def complete(self, prompt: str, system_prompt: str = "You are a helpful AI assistant.") -> str:
        """
        Send completion request to AIML API

        Args:
            prompt: User prompt
            system_prompt: System message

        Returns:
            Generated text or error message string
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

        # Add reasoning_effort if specified
        if self.reasoning_effort:
            payload["reasoning_effort"] = self.reasoning_effort

        max_retries = 3
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                result = response.json()

                # Extract content from response
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content'].strip()
                    return content
                else:
                    return f"ERROR: Unexpected response format: {result}"

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    # Rate limit - retry with backoff
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)
                        print(f"Rate limit hit. Waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return f"ERROR: Rate limit exceeded after {max_retries} retries"
                elif e.response.status_code == 401:
                    return "ERROR: Authentication failed (401). Check your API key."
                elif e.response.status_code == 404:
                    return f"ERROR: Model '{self.model}' not found (404)"
                else:
                    return f"ERROR: HTTP {e.response.status_code}: {e}"

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    print(f"Request timeout. Retrying {attempt + 1}/{max_retries}...")
                    time.sleep(retry_delay)
                    continue
                else:
                    return f"ERROR: Request timed out after {max_retries} attempts"

            except Exception as e:
                return f"ERROR: {str(e)}"

        return "ERROR: Max retries exceeded"


if __name__ == '__main__':
    # Quick test
    import sys

    if len(sys.argv) < 2:
        print("Usage: python llm_client.py YOUR_API_KEY")
        sys.exit(1)

    api_key = sys.argv[1]

    client = LLMClient(
        model="openai/gpt-5-1",
        api_key=api_key,
        temperature=0.0,
        max_tokens=50
    )

    test_prompt = "SELECT * FROM users LIMIT 1"
    result = client.complete(test_prompt, system_prompt="You are a SQL expert.")

    print(f"Test Result: {result}")
