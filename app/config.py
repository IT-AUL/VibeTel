import os
from pydantic import BaseModel


class Settings(BaseModel):
    local: bool = True

    yandex_key_id: str = ""
    yandex_secret_key: str = ""
    yandex_folder_id: str = ""
    yandex_model: str = "yandexgpt-lite"
    translater_api_key: str = ""
    translater_folder_id: str = ""

    database_url: str = "sqlite:///./vibetel.db"

    tts_base_url: str = ""

    def __init__(self):
        super().__init__(
            local=os.getenv('LOCAL', 'true').lower() == 'true',
            yandex_key_id=os.getenv('YANDEX_KEY_ID', ''),
            yandex_secret_key=os.getenv('YANDEX_SECRET_KEY', ''),
            yandex_folder_id=os.getenv('YANDEX_FOLDER_ID', ''),
            yandex_model=os.getenv('MODEL', 'yandexgpt-lite'),
            translater_api_key=os.getenv('TRANSLATER_API_KEY', ''),
            translater_folder_id=os.getenv('TRANSLATER_FOLDER_ID', ''),
            database_url=os.getenv('DATABASE_URL', 'sqlite:///./vibetel.db'),
            tts_base_url=os.getenv('TTS_BASE_URL', '')
        )


settings = Settings()
