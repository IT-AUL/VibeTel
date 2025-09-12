import asyncio
import logging
from typing import Optional
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

class TranslatorService:
    def __init__(self):
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
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            result = translator.translate(text)
            return result
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
            # deep_translator не имеет встроенного определения языка
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
