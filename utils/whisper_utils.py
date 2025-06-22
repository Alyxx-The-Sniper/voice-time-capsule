import os
import whisper
import ffmpeg

# Load the Whisper model once
model = whisper.load_model("base")  # or “small” / “medium” / “large”

def get_duration_sec(audio_path: str) -> float:
    """Return the audio duration in seconds using ffmpeg.probe, or 0 if missing."""
    abs_path = os.path.abspath(audio_path).replace("\\", "/")
    info = ffmpeg.probe(abs_path)
    # Use .get to avoid KeyError, and fallback to 0.0 if not found
    duration_str = info.get("format", {}).get("duration", None)
    try:
        return float(duration_str) if duration_str else 0.0
    except Exception:
        return 0.0

def transcribe(input_path: str) -> tuple[str, float]:
    """
    Transcribes the audio at input_path and returns:
      • text: the transcript
      • duration: length in seconds, rounded to 2dp
    """
    # normalize to absolute, Unix-style path
    abs_path = os.path.abspath(input_path).replace("\\", "/")

    # Let Whisper handle decoding directly
    result = model.transcribe(abs_path)
    text = result["text"].strip()

    # Get duration via ffmpeg.probe
    duration = get_duration_sec(input_path)
    return text, round(duration, 2)
