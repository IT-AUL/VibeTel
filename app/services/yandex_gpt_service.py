import os
import random
import logging
from typing import List, Dict
from yandex_cloud_ml_sdk import AsyncYCloudML
from app.config import settings

logger = logging.getLogger(__name__)

class YandexGPTService:
    def __init__(self):
        self.key_id = settings.yandex_key_id
        self.secret_key = settings.yandex_secret_key
        self.folder_id = settings.yandex_folder_id
        self.sdk = None
        
        if self.key_id and self.secret_key and self.folder_id:
            try:
                self.sdk = AsyncYCloudML(
                    folder_id=self.folder_id,
                    auth=self.secret_key
                )
                logger.info("Yandex Cloud ML SDK инициализирован")
                
            except Exception as e:
                logger.error(f"Ошибка инициализации Yandex Cloud ML SDK: {e}")
                self.sdk = None
        else:
            logger.warning("Yandex GPT сервисный аккаунт не настроен")
    
    async def generate_sentence(self, objects: List[str], previous_sentences: List[str] = None) -> Dict[str, str]:
        if not self.sdk:
            return self._generate_fallback_sentence(objects)
        
        try:
            prompt = self._create_prompt(objects, previous_sentences)
            
            model = self.sdk.models.completions(settings.yandex_model)
            
            result = await model.configure(temperature=0.8, max_tokens=150).run(prompt)
            
            generated_text = result.alternatives[0].text.strip()
            return self._parse_response(generated_text, objects)
                        
        except Exception as e:
            logger.error(f"Ошибка генерации предложения через SDK: {e}")
            return self._generate_fallback_sentence(objects)
    
    def _create_prompt(self, objects: List[str], previous_sentences: List[str] = None) -> str:
        objects_str = ', '.join(objects)
        
        context = ""
        if previous_sentences:
            recent_sentences = previous_sentences[-5:]
            context = f"Предыдущие примеры предложений:\n"
            for sentence in recent_sentences:
                context += f"- {sentence}\n"
            context += "\n"
        
        prompt = f"""
{context}Создай одно творческое предложение на русском языке, которое включает один из этих объектов: {objects_str}.

Требования:
1. Предложение должно быть интересным и создавать яркий образ
2. Выбери ОДИН объект из списка для включения в предложение
3. Предложение должно помочь изучающему русский язык запомнить слово
4. Стиль должен быть живым и эмоциональным
5. Длина: 8-15 слов

Формат ответа:
Предложение: [твое предложение]
Слово: [выбранное слово из объектов]

Пример:
Предложение: Утром я пью ароматный кофе и читаю интересную книгу
Слово: кофе
"""
        
        return prompt
    
    def _parse_response(self, response_text: str, objects: List[str]) -> Dict[str, str]:
        try:
            lines = response_text.strip().split('\n')
            sentence = ""
            target_word = ""
            
            for line in lines:
                if line.startswith('Предложение:'):
                    sentence = line.replace('Предложение:', '').strip()
                elif line.startswith('Слово:'):
                    target_word = line.replace('Слово:', '').strip()
            
            if not sentence or not target_word:
                return self._generate_fallback_sentence(objects)
            
            target_word = target_word.lower()
            if target_word not in [obj.lower() for obj in objects]:
                target_word = random.choice(objects)
            
            return {
                "sentence": sentence,
                "target_word": target_word
            }
            
        except Exception as e:
            logger.error(f"Ошибка парсинга ответа GPT: {e}")
            return self._generate_fallback_sentence(objects)
    
    def _generate_fallback_sentence(self, objects: List[str]) -> Dict[str, str]:
        target_word = random.choice(objects)
        
        sentence_templates = [
            f"Вчера я видел красивый {target_word} в парке",
            f"Моя бабушка любит свой старый {target_word}",
            f"На столе лежит интересный {target_word}",
            f"Дети играют с новым {target_word}",
            f"В магазине я купил отличный {target_word}",
            f"Сегодня утром я нашел забытый {target_word}",
            f"Мой друг подарил мне красивый {target_word}",
            f"В саду растет прекрасный {target_word}"
        ]
        
        sentence = random.choice(sentence_templates)
        
        return {
            "sentence": sentence,
            "target_word": target_word
        }
