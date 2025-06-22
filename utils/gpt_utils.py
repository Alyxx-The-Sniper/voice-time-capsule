import os
from huggingface_hub import InferenceClient

# ✅ Set your Hugging Face token
api_key = os.environ.get("HF_API_KEY")
if not api_key:
    raise ValueError("Missing HF_API_KEY environment variable.")

# ✅ Initialize client for Meta-LLaMA-3-8B-Instruct
client = InferenceClient(
    model="meta-llama/Meta-Llama-3-8B-Instruct",
    token=api_key,
    timeout=30  # optional: avoids hanging forever
)

def respond_as_future_self(original_text: str) -> str:
    """
    Responds as the user's future self using Meta-LLaMA-3-8B.
    """
    if not original_text.strip():
        return "🤖 (No message detected — please record a message first.)"

    messages = [
        {
            "role": "system",
            "content": (
                "You are from the future—older, wiser, and more compassionate. "
                "You just received a message from your past self in a time capsule app. "
                "Respond with casual,  warmth, honesty, and emotional intelligence. "
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


    response = client.chat_completion(
        messages=messages,
        temperature=0.8,
        max_tokens=146,
        top_p=0.9,
        frequency_penalty=1.0
    )

    return response.choices[0].message.content.strip()
