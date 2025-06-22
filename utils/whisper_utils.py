import os
import ffmpeg
from huggingface_hub import InferenceClient

HF_TOKEN = os.environ.get("HF_TOKEN", "")

# Create a global client
client = InferenceClient(
    model="openai/whisper-large-v3",
    token=HF_TOKEN,
    # provider="fal-ai"  # No longer needed for standard Inference Endpoints
)

def get_duration_sec(audio_path: str) -> float:
    """Return the audio duration in seconds using ffmpeg.probe, or 0 if missing."""
    abs_path = os.path.abspath(audio_path).replace("\\", "/")
    info = ffmpeg.probe(abs_path)
    duration_str = info.get("format", {}).get("duration", None)
    try:
        return float(duration_str) if duration_str else 0.0
    except Exception:
        return 0.0

def transcribe(input_path: str) -> tuple[str, float]:
    """
    Transcribes the audio at input_path using Hugging Face InferenceClient and returns:
      • text: the transcript
      • duration: length in seconds, rounded to 2dp
    """
    abs_path = os.path.abspath(input_path).replace("\\", "/")
    # This function automatically detects file format (wav, mp3, m4a, flac, etc.)
    result = client.automatic_speech_recognition(abs_path)
    # Result is just a dict: {'text': "..."}
    text = result.get("text", "").strip()
    duration = get_duration_sec(input_path)
    return text, round(duration, 2)
