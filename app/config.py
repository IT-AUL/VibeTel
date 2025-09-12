import os
from pydantic import BaseModel

class Settings(BaseModel):
    local: bool = True
    
    yandex_key_id: str = ""
    yandex_secret_key: str = ""
    yandex_folder_id: str = ""
    yandex_model: str = "yandexgpt-lite"
    
    database_url: str = "sqlite:///./vibetel.db"
    
    def __init__(self):
        super().__init__(
            local=os.getenv('LOCAL', 'true').lower() == 'true',
            yandex_key_id=os.getenv('YANDEX_KEY_ID', ''),
            yandex_secret_key=os.getenv('YANDEX_SECRET_KEY', ''),
            yandex_folder_id=os.getenv('YANDEX_FOLDER_ID', ''),
            yandex_model=os.getenv('MODEL', 'yandexgpt-lite'),
            database_url=os.getenv('DATABASE_URL', 'sqlite:///./vibetel.db')
        )

settings = Settings()
