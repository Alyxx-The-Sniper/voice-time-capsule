from utils.db_utils import SessionLocal, CostLog  # Import your SQLAlchemy session and model

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
    Logs usage and estimated cost to the cost_log table using SQLAlchemy.
    """
    cost_usd = estimate_cost(duration_sec, gpt_input, gpt_output, tts_chars)

    session = SessionLocal()
    try:
        log = CostLog(
            token=token,
            duration_sec=duration_sec,
            gpt_input=gpt_input,
            gpt_output=gpt_output,
            tts_chars=tts_chars,
            cost_usd=cost_usd
        )
        session.add(log)
        session.commit()
        print(f"💸 Cost logged: ${cost_usd} for token {token}")
    except Exception as e:
        session.rollback()
        print(f"Failed to log cost: {e}")
        raise
    finally:
        session.close()
