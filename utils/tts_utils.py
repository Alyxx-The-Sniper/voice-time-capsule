import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

# Clone your own voice from 30-second samples with Instant Voice Cloning
# elevenlabs documentation here: https://elevenlabs.io/docs/product-guides/voices/voice-cloning
# reference: https://elevenlabs.io/docs/api-reference/voices/ivc/create
def upload_user_voice(name: str, audio_path: str) -> str:
    # temp file (close after use)
    with open(audio_path, "rb") as f:
        voice = client.voices.ivc.create(
            name=name,
            description="Cloned from time capsule submission",
            files=[f]
        )
    return voice.voice_id


def synthesize(text: str, output_path: str, voice_id: str) -> str:
    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id,
        output_format="mp3_44100_128",
        text=text,
        model_id="eleven_multilingual_v2",

    )
    with open(output_path, "wb") as f:
        for chunk in audio_stream:
            f.write(chunk)

    return output_path
