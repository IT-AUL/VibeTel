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
            
            if result and hasattr(result, 'alternatives') and result.alternatives:
                generated_text = result.alternatives[0].text.strip()
                parsed_result = self._parse_response(generated_text, objects)
                if parsed_result:
                    logger.info(f"Предложение создано: {parsed_result['sentence']}")
                    return parsed_result
                else:
                    logger.warning("Не удалось распарсить ответ GPT")
            else:
                logger.warning("Пустой ответ от YandexGPT")
            
            return self._generate_fallback_sentence(objects)
                        
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
{context}Создай одно простое предложение на русском языке для изучающих язык, используя объекты: {objects_str}.

ЦЕЛЬ: Включи в предложение МАКСИМАЛЬНОЕ количество объектов из списка, но сохрани простоту для новичков.

Требования:
1. Предложение должно быть ОЧЕНЬ ПРОСТЫМ и понятным для начинающих
2. Используй только базовую лексику (слова из первых 1000 самых частых русских слов)
3. По возможности включи НЕСКОЛЬКО объектов из списка: {objects_str}
4. Если объектов много, выбери 2-3 самых важных
5. Предложение должно звучать ЕСТЕСТВЕННО
6. ВАЖНО: Используй в предложении ТОЧНО ТЕ ЖЕ слова, что в списке объектов
7. НЕ сокращай слова
8. Описывай простую повседневную ситуацию
9. Длина: 4-10 слов
10. Используй простые конструкции: субъект + глагол + объект(ы)

Формат ответа:
Предложение: [простое предложение с объектами]
Слово: [главный объект из предложения]

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
                return None
            
            # Проверяем, что target_word точно соответствует одному из объектов
            target_word_lower = target_word.lower()
            objects_lower = [obj.lower() for obj in objects]
            
            if target_word_lower not in objects_lower:
                return None
            else:
                # Возвращаем оригинальное написание из списка объектов
                target_word = objects[objects_lower.index(target_word_lower)]
            
            # Проверяем, что целевое слово действительно есть в предложении
            if target_word.lower() not in sentence.lower():
                return None
            
            return {
                "sentence": sentence,
                "target_word": target_word
            }
            
        except Exception as e:
            logger.error(f"Ошибка парсинга ответа GPT: {e}")
            return None
    
    def _generate_fallback_sentence(self, objects: List[str]) -> Dict[str, str]:
        target_word = random.choice(objects)
        
        # Если несколько объектов, пытаемся создать предложение с 2-3 объектами
        if len(objects) >= 2:
            # Берем 2-3 объекта включая главный
            selected_objects = [target_word]
            other_objects = [obj for obj in objects if obj != target_word]
            selected_objects.extend(other_objects[:2])  # Добавляем до 2 других
            
            # Шаблоны для нескольких объектов
            if len(selected_objects) >= 2:
                templates = [
                    f"Я вижу {selected_objects[0]} и {selected_objects[1]}",
                    f"На столе лежат {selected_objects[0]} и {selected_objects[1]}",
                    f"Мама держит {selected_objects[0]} и {selected_objects[1]}",
                    f"Здесь есть {selected_objects[0]} и {selected_objects[1]}"
                ]
                if len(selected_objects) >= 3:
                    templates.extend([
                        f"Я вижу {selected_objects[0]}, {selected_objects[1]} и {selected_objects[2]}",
                        f"На картинке {selected_objects[0]}, {selected_objects[1]} и {selected_objects[2]}"
                    ])
                
                sentence = random.choice(templates)
                return {"sentence": sentence, "target_word": target_word}
        
        # Fallback для одного объекта
        single_templates = [
            f"Я вижу {target_word}",
            f"Мама держит {target_word}",
            f"У меня есть {target_word}",
            f"Это мой {target_word}",
            f"Вот новый {target_word}"
        ]
        
        sentence = random.choice(single_templates)
        return {"sentence": sentence, "target_word": target_word}
