import asyncio
import aiohttp
import logging
from typing import Optional, List
from app.config import settings

logger = logging.getLogger(__name__)

class TranslatorService:
    def __init__(self):
        self.source_language = 'ru'  # Исходный язык по умолчанию - русский
        self.target_language = 'tt'  # Целевой язык по умолчанию - татарский
        self.api_key = settings.translater_api_key
        self.folder_id = settings.translater_folder_id
        self.api_url = "https://translate.api.cloud.yandex.net/translate/v2/translate"
    
    async def translate_text(self, text: str, target_lang: str = None, source_lang: str = None) -> str:
        if not text:
            return ""
        
        if not self.api_key or not self.folder_id:
            logger.warning("Yandex Translate API не настроен")
            return text
        
        target_lang = target_lang or self.target_language
        source_lang = source_lang or self.source_language
        
        try:
            result = await self._translate_yandex([text], target_lang, source_lang)
            translated_text = result[0] if result else text
            
            logger.info(f"Переведен текст: '{text}' ({source_lang} -> {target_lang}) -> '{translated_text}'")
            return translated_text
            
        except Exception as e:
            logger.error(f"Ошибка перевода текста '{text}': {e}")
            return text
    
    async def _translate_yandex(self, texts: List[str], target_lang: str, source_lang: str) -> List[str]:
        """Переводит список текстов через Yandex Translate API"""
        body = {
            "targetLanguageCode": target_lang,
            "texts": texts,
            "folderId": self.folder_id,
            "sourceLanguageCode": source_lang,
            "speller": True
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {self.api_key}",
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, json=body, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return [translation["text"] for translation in data["translations"]]
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка Yandex Translate API: {response.status} - {error_text}")
                    return texts
    
    async def translate_multiple(self, texts: list, target_lang: str = None) -> list:
        if not texts:
            return []
        
        if not self.api_key or not self.folder_id:
            logger.warning("Yandex Translate API не настроен")
            return texts
        
        target_lang = target_lang or self.target_language
        source_lang = self.source_language
        
        try:
            # Yandex API может обрабатывать множественные тексты в одном запросе
            results = await self._translate_yandex(texts, target_lang, source_lang)
            logger.info(f"Переведено {len(texts)} текстов ({source_lang} -> {target_lang})")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка множественного перевода: {e}")
            return texts
    
    async def detect_language(self, text: str) -> Optional[str]:
        if not text:
            return None
        
        try:
            # Yandex Translate API не предоставляет определение языка в этом эндпоинте
            # Возвращаем source_language по умолчанию
            return self.source_language
            
        except Exception as e:
            logger.error(f"Ошибка определения языка для '{text}': {e}")
            return None
    
    def set_target_language(self, language_code: str):
        self.target_language = language_code
        logger.info(f"Целевой язык изменен на: {language_code}")
    
    def set_source_language(self, language_code: str):
        self.source_language = language_code
        logger.info(f"Исходный язык изменен на: {language_code}")
    
    def set_translation_direction(self, source_lang: str, target_lang: str):
        self.source_language = source_lang
        self.target_language = target_lang
        logger.info(f"Направление перевода: {source_lang} -> {target_lang}")
    
    def get_translation_direction(self) -> dict:
        return {
            'source_language': self.source_language,
            'target_language': self.target_language
        }
    
    def get_supported_languages(self) -> dict:
        return {
            'ru': 'Russian',
            'en': 'English',
            'de': 'German',
            'fr': 'French', 
            'es': 'Spanish',
            'it': 'Italian',
            'pt': 'Portuguese',
            'zh': 'Chinese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'tr': 'Turkish',
            'pl': 'Polish',
            'nl': 'Dutch',
            'sv': 'Swedish',
            'da': 'Danish',
            'no': 'Norwegian',
            'fi': 'Finnish',
            'tt': 'Tatar'
        }
