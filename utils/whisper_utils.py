import os
import requests
import ffmpeg

# Deepinfra
API_URL = "https://api.deepinfra.com/v1/inference/openai/whisper-large-v3"
DEEPINFRA_API_KEY = os.environ["DEEPINFRA_API_KEY"]

def get_duration_sec(audio_path: str) -> float:
    """Return the audio duration in seconds using ffmpeg.probe, or 0 if missing."""
    abs_path = os.path.abspath(audio_path).replace("\\", "/")
    try:
        info = ffmpeg.probe(abs_path)
        duration_str = info.get("format", {}).get("duration", None)
        return float(duration_str) if duration_str else 0.0
    except Exception as e:
        print("ffmpeg probe error:", e)
        return 0.0

def transcribe(input_path: str) -> tuple[str, float]:
    """
    Converts any audio file to .flac, then submits to Hugging Face Whisper API.
    Returns transcript and duration in seconds.
    """
    # Convert to .flac for API
    flac_path = os.path.splitext(input_path)[0] + ".flac"
    try:
        ffmpeg.input(input_path).output(flac_path).run(overwrite_output=True, quiet=True)
    except Exception as e:
        print("ffmpeg conversion error:", e)
        raise

    # Read flac as bytes
    with open(flac_path, "rb") as f:
        audio_data = f.read()

    # Prepare headers
    headers = {
        "Authorization": f"Bearer {DEEPINFRA_API_KEY}",
        # Don't set Content-Type here!
    }

    files = {
        "audio": ("audio.flac", audio_data, "audio/flac")
    }

    response = requests.post(API_URL, headers=headers, files=files)


    try:
        response.raise_for_status()
    except Exception as e:
        print("Hugging Face API error:", e)
        print("Response:", response.text)
        raise

    resp_json = response.json()
    text = resp_json.get("text", "").strip()
    duration = get_duration_sec(flac_path)
    return text, round(duration, 2)
