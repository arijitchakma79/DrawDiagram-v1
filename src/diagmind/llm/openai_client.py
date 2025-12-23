import os
from typing import Any, Optional
from openai import OpenAI


def parse(
    system_prompt: str,
    user_prompt: str,
    response_format: Any,
    model: str = "gpt-4o",
    temperature: float = 1.0,
    api_key: Optional[str] = None,
) -> Any:
    """
    Simple wrapper around OpenAI's chat.completions.parse for structured output.
    
    Args:
        system_prompt: System message/instruction
        user_prompt: User message/prompt
        response_format: Pydantic model for structured output
        model: Model name to use
        temperature: Sampling temperature
        api_key: OpenAI API key (uses OPENAI_API_KEY env var if None)
    
    Returns:
        Parsed object matching the response_format
    """
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable must be set")
    
    client = OpenAI(api_key=api_key)
    
    completion = client.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        response_format=response_format,
    )
    
    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ValueError("Failed to parse response from OpenAI API")
    
    return parsed
