import os
from typing import Tuple
from openai import OpenAI, OpenAIError

# ✅ Get and validate API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Missing OPENAI_API_KEY environment variable.")

client = OpenAI(api_key=api_key)

def respond_as_future_self(original_text: str) -> Tuple[str, int, int]:
    """
    Generates a thoughtful, emotionally intelligent reply from the user's future self.
    Adapts tone based on original message. Returns:
    (response_text, input_tokens_used, output_tokens_used).
    """

    messages = [
        {
            "role": "system",
            "content": (
                "You are the user's older, wiser, and more compassionate future self. "
                "You just received a message from your past self. Respond with warmth, emotional intelligence, "
                "and a tone that matches or gently balances the original message. "
                "You can be playful, thoughtful, serious, or deeply reflective as needed—just make it human and sincere. "
                "Speak with the perspective of someone who remembers how it felt, and wants to encourage or reassure."
            )
        },
        {
            "role": "user",
            "content": original_text
        }
    ]

    try:
        response = client.chat.completions.create(
            # model="gpt-4-turbo",
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.8,
            max_tokens=400,
            top_p=1.0,
            presence_penalty=0.6,
            frequency_penalty=0.3
        )

        reply = response.choices[0].message.content.strip()
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens

        return reply, input_tokens, output_tokens

    except OpenAIError as e:
        error_msg = f"[Error: {str(e)}]"
        return error_msg, 0, 0
