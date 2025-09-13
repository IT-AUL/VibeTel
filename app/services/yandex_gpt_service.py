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
                if generated_text:
                    # Используем весь ответ LLM как предложение
                    target_word = random.choice(objects)
                    logger.info(f"Предложение создано через YandexGPT: {generated_text}")
                    return {
                        "sentence": generated_text,
                        "target_word": target_word
                    }
                else:
                    logger.warning("Пустой текст от YandexGPT")
            else:
                logger.warning("Пустой ответ от YandexGPT")
            
            logger.info("Используем fallback предложение")
            return self._generate_fallback_sentence(objects)
                        
        except Exception as e:
            logger.error(f"Ошибка генерации предложения через SDK: {e}")
            logger.info("Используем fallback предложение")
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
11. Постарайся сохранить предыдущий контекст предложений, если они есть, чтобы текст выстраивал единую историю

Напиши только само предложение без дополнительного форматирования.

Примеры хороших предложений:
"Мама держит мобильный телефон"
"Папа читает книгу дома"
"Дети играют с мячом"
"Я покупаю новый мобильный телефон"
"Кот спит на стуле"
"На столе лежат чашка и книга"
"Машина стоит возле дома"

Создай аналогичное предложение с объектами: {objects_str}
"""
        
        return prompt
    
    
    def _generate_fallback_sentence(self, objects: List[str]) -> Dict[str, str]:
        target_word = random.choice(objects)
        logger.info("Предложение замокано (fallback)")
        
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
