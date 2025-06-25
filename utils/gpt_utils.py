import os
import requests

DEEPINFRA_API_KEY = os.environ.get("DEEPINFRA_API_KEY")
if not DEEPINFRA_API_KEY:
    raise ValueError("Missing DEEPINFRA_API_KEY environment variable.")

DEEPINFRA_CHAT_URL = "https://api.deepinfra.com/v1/openai/chat/completions"

def respond_as_future_self(original_text: str) -> str:
    if not original_text.strip():
        return "🤖 (No message detected — please record a message first.)"

    messages = [
        {
            "role": "system",
            "content": (
                "You are from the future—older, wiser, and more compassionate. "
                "You just received a message from your past self in a time capsule app. "
                "Respond with casual, warmth, honesty, and emotional intelligence. "
                "You can be playful or reflective—just be sincere and human. "
                "Remember you are responding to your past self. "
                "If necessary respond in Taglish, mixing Tagalog and English naturally. "
                "Keep your response focused on their question and give feedback that matches the tone and mood."
            )
        },
        {
            "role": "user",
            "content": original_text
        }
    ]

    payload = {
        "model": "meta-llama/Meta-Llama-3-8B-Instruct",
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": 146,
        "top_p": 0.9,
        "frequency_penalty": 1.0
    }

    headers = {
        "Authorization": f"Bearer {DEEPINFRA_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(DEEPINFRA_CHAT_URL, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    # Check structure and extract content
    return data["choices"][0]["message"]["content"].strip()
