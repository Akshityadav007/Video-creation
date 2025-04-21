import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from elevenlabs import save
from elevenlabs.client import ElevenLabs
import logging
import random

load_dotenv()
audio_api_key = os.getenv("ELEVEN_LABS_API_KEY")

# Initialize client
_client = ElevenLabs(api_key=audio_api_key)
_all_voices = []
FEMALE_VOICE = 'Rachel'
MALE_VOICE = 'George'

def _load_voices():
    """Fetch and pick one female and one male voice."""
    global _all_voices, FEMALE_VOICE, MALE_VOICE
    try:
        resp = _client.voices.search(include_total_count=True)
        _all_voices = resp.voices or []
    except Exception as e:
        logging.error(f"Error fetching voices: {e}")
        _all_voices = []

    female = [v for v in _all_voices if getattr(v, 'gender', '').lower() == 'female']
    male   = [v for v in _all_voices if getattr(v, 'gender', '').lower() == 'male']

    # Pick first available or fallback
    FEMALE_VOICE = female[0] if female else (_all_voices[0] if _all_voices else None)
    MALE_VOICE   = male[0]   if male   else (_all_voices[1] if len(_all_voices) > 1 else FEMALE_VOICE)

_load_voices()


def generateAudio(script: str, output_path: str = None, gender: str = None) -> str:
    """
    Generate audio with ElevenLabs.
    gender: 'female' or 'male' to pick the pre-chosen voices.
    """
    # Prepare output path
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(f"audio/{timestamp}")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "story.mp3"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # Pick voice
    if gender == 'female' and FEMALE_VOICE:
        voice = FEMALE_VOICE
    elif gender == 'male' and MALE_VOICE:
        voice = MALE_VOICE
    else:
        voice = random.choice(_all_voices) if _all_voices else None

    if not voice:
        raise RuntimeError("No available voice for audio generation.")

    voice_name = voice.name if hasattr(voice, 'name') else str(voice)
    logging.info(f"Selected voice ({gender or 'random'}): {voice_name}")

    try:
        audio = _client.generate(
            text=script[:500],
            voice=voice_name,
            model="eleven_turbo_v2"
        )
        save(audio, str(output_path))
        logging.info(f"Audio saved to: {output_path}")
        return str(output_path)
    except Exception as e:
        logging.error(f"Audio generation failed: {e}")
        raise