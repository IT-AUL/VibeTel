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
{context}Создай одно простое предложение на русском языке для изучающих язык, которое включает один из этих объектов: {objects_str}.

Требования:
1. Предложение должно быть ОЧЕНЬ ПРОСТЫМ и понятным для начинающих
2. Используй только базовую лексику (слова из первых 1000 самых частых русских слов)
3. Используй настоящее время или простое прошедшее время
4. Предложение должно звучать ЕСТЕСТВЕННО для носителя русского языка
5. Выбери ОДИН объект из списка для включения в предложение
6. ВАЖНО: Используй в предложении ТОЧНО ТО ЖЕ слово, которое указываешь как целевое
7. НЕ сокращай слова (если объект "мобильный телефон", то в предложении тоже должно быть "мобильный телефон", а не просто "телефон")
8. Предложение должно описывать простую повседневную ситуацию
9. Длина: 4-8 слов (можно чуть длиннее для точности)
10. Избегай сложных метафор, поэтических образов и редких слов
11. Используй простые конструкции: субъект + глагол + объект

Формат ответа:
Предложение: [твое простое предложение]
Слово: [выбранное слово из объектов]

Примеры ОТЛИЧНЫХ простых предложений:
Предложение: Мама держит мобильный телефон
Слово: мобильный телефон

Предложение: Папа читает книгу дома
Слово: книга

Предложение: Дети играют с мячом
Слово: мяч

Предложение: Я покупаю новый мобильный телефон
Слово: мобильный телефон

Предложение: Кот спит на стуле
Слово: кот

ПРАВИЛЬНО: "Я держу мобильный телефон" (целевое слово: мобильный телефон)
НЕПРАВИЛЬНО: "Я держу телефон" (целевое слово: мобильный телефон)
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
            
            # Проверяем, что target_word точно соответствует одному из объектов
            target_word_lower = target_word.lower()
            objects_lower = [obj.lower() for obj in objects]
            
            if target_word_lower not in objects_lower:
                # Если не нашли точное совпадение, генерируем fallback
                return self._generate_fallback_sentence(objects)
            else:
                # Возвращаем оригинальное написание из списка объектов
                target_word = objects[objects_lower.index(target_word_lower)]
            
            # Проверяем, что целевое слово действительно есть в предложении
            if target_word.lower() not in sentence.lower():
                # Если целевого слова нет в предложении, генерируем fallback
                return self._generate_fallback_sentence(objects)
            
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
            f"Я вижу {target_word}",
            f"Мама держит {target_word}",
            f"Дети играют с {target_word}",
            f"У меня есть {target_word}",
            f"Папа покупает {target_word}",
            f"Это мой {target_word}",
            f"Бабушка любит {target_word}",
            f"Вот новый {target_word}"
        ]
        
        sentence = random.choice(sentence_templates)
        
        return {
            "sentence": sentence,
            "target_word": target_word
        }
