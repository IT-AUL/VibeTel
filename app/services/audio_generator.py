from aiohttp import ClientSession, ClientTimeout

from app.config import settings
from app.models.responses import AudioRequest, AudioResponse


async def generate_audio(request: AudioRequest) -> AudioResponse:
    if not request.text:
        raise ValueError("Текст для генерации не может быть пустым")

    base_url = settings.tts_base_url
    if not base_url:
        raise ValueError("TTS_BASE_URL не сконфигурирован")

    url = base_url.rstrip('/') + '/listening/'
    params = {
        'speaker': request.speaker.value,
        'text': request.text,
    }

    timeout = ClientTimeout(total=20)
    async with ClientSession(timeout=timeout) as session:
        async with session.get(url, params=params) as resp:
            body_text = await resp.text()
            if resp.status != 200:
                raise RuntimeError(f"Ошибка TTS API {resp.status}: {body_text}")
            try:
                data = await resp.json()
            except Exception:
                raise RuntimeError("Некорректный JSON ответ от TTS API")

    audio_b64 = data.get('wav_base64') or data.get('audio_base64') or data.get('audio')
    if not audio_b64:
        raise RuntimeError("В ответе TTS API отсутствует wav_base64")

    return AudioResponse(audio_base64=audio_b64)
