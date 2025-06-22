import sqlite3
from utils.db_utils import DB_PATH

def estimate_cost(duration_sec: float, gpt_input: int, gpt_output: int, tts_chars: int) -> float:
    """
    Estimates cost in USD based on usage.
    Whisper (local) and LLaMA (free) are zero; ElevenLabs is charged per 1K chars.
    """
    whisper_cost = 0.0
    gpt_cost = 0.0
    tts_cost = (tts_chars / 1000) * 0.3  # ElevenLabs pricing after free tier

    total = whisper_cost + gpt_cost + tts_cost
    return round(total, 4)

def log_cost(token: str, duration_sec: float, gpt_input: int, gpt_output: int, tts_chars: int):
    """
    Logs usage and estimated cost to the cost_log table.
    """
    cost_usd = estimate_cost(duration_sec, gpt_input, gpt_output, tts_chars)

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO cost_log (
                token, duration_sec, gpt_input, gpt_output, tts_chars, cost_usd
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            token,
            duration_sec,
            gpt_input,
            gpt_output,
            tts_chars,
            cost_usd
        ))
        conn.commit()

    print(f"💸 Cost logged: ${cost_usd} for token {token}")
