import asyncio
import logging
from typing import Optional
from googletrans import Translator

logger = logging.getLogger(__name__)

class TranslatorService:
    def __init__(self):
        self.translator = Translator()
        self.source_language = 'ru'  # Исходный язык по умолчанию - русский
        self.target_language = 'tt'  # Целевой язык по умолчанию - татарский
    
    async def translate_text(self, text: str, target_lang: str = None, source_lang: str = None) -> str:
        if not text:
            return ""
        
        target_lang = target_lang or self.target_language
        source_lang = source_lang or self.source_language
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._translate_sync,
                text,
                target_lang,
                source_lang
            )
            
            logger.info(f"Переведен текст: '{text}' ({source_lang} -> {target_lang}) -> '{result}'")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка перевода текста '{text}': {e}")
            return text
    
    def _translate_sync(self, text: str, target_lang: str, source_lang: str = None) -> str:
        try:
            source_lang = source_lang or self.source_language
            result = self.translator.translate(text, src=source_lang, dest=target_lang)
            return result.text
        except Exception as e:
            logger.error(f"Ошибка синхронного перевода: {e}")
            return text
    
    async def translate_multiple(self, texts: list, target_lang: str = None) -> list:
        if not texts:
            return []
        
        target_lang = target_lang or self.target_language
        
        try:
            tasks = []
            for text in texts:
                task = self.translate_text(text, target_lang)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            translated_texts = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Ошибка перевода текста {i}: {result}")
                    translated_texts.append(texts[i])
                else:
                    translated_texts.append(result)
            
            return translated_texts
            
        except Exception as e:
            logger.error(f"Ошибка множественного перевода: {e}")
            return texts
    
    async def detect_language(self, text: str) -> Optional[str]:
        if not text:
            return None
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._detect_language_sync,
                text
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка определения языка для '{text}': {e}")
            return None
    
    def _detect_language_sync(self, text: str) -> Optional[str]:
        try:
            result = self.translator.detect(text)
            return result.lang
        except Exception as e:
            logger.error(f"Ошибка синхронного определения языка: {e}")
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
            'ru': 'Русский',
            'en': 'English',
            'de': 'Deutsch',
            'fr': 'Français', 
            'es': 'Español',
            'it': 'Italiano',
            'pt': 'Português',
            'zh': '中文',
            'ja': '日本語',
            'ko': '한국어',
            'ar': 'العربية',
            'hi': 'हिन्दी',
            'tr': 'Türkçe',
            'pl': 'Polski',
            'nl': 'Nederlands',
            'sv': 'Svenska',
            'da': 'Dansk',
            'no': 'Norsk',
            'fi': 'Suomi',
            'tt': 'Татарча'
        }
