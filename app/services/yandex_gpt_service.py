import random
import logging
from typing import List, Dict, Any
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
            context = f"Предыдущие предложений для связанной истории:\n"
            for sentence in recent_sentences:
                context += f"- {sentence}\n"
            context += "\n"

        prompt = f"""
Создай одно простое предложение на русском языке для изучающих язык, используя объекты: {objects_str}.

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
11. Каждое добавленное предложение должно учитывать контекст предыдущих предложений (если есть), для выстраивания связного повествования
Напиши только само предложение без дополнительного форматирования.

Примеры хороших предложений:
"Мама держит мобильный телефон"
"Папа читает книгу дома"
"Дети играют с мячом"
"Я покупаю новый мобильный телефон"
"Кот спит на стуле"
"На столе лежат чашка и книга"
"Машина стоит возле дома"

Создай аналогичное предложение с объектами: {objects_str}. {context}
"""
        logger.info(prompt)
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
    
    async def generate_album_memory(self, objects: List[str], album_theme: str = "") -> Dict[str, Any]:
        """Генерирует абзац-воспоминание для альбома фотографий"""
        if not self.sdk:
            logger.info("Используем fallback для абзаца-воспоминания")
            return self._generate_fallback_memory(objects, album_theme)
        
        try:
            prompt = self._create_memory_prompt(objects, album_theme)
            model = self.sdk.models.completions(settings.yandex_model)
            result = await model.configure(temperature=0.9, max_tokens=500).run(prompt)
            
            if result and hasattr(result, 'alternatives') and result.alternatives:
                generated_text = result.alternatives[0].text.strip()
                if generated_text:
                    # Определяем какие объекты были использованы
                    used_objects = []
                    text_lower = generated_text.lower()
                    for obj in objects:
                        if obj.lower() in text_lower:
                            used_objects.append(obj)
                    
                    logger.info(f"Абзац-воспоминание создан через YandexGPT: {generated_text[:50]}...")
                    return {
                        "memory": generated_text,
                        "used_objects": used_objects or objects[:3]  # Fallback если не найдены
                    }
                else:
                    logger.warning("Пустой текст от YandexGPT для абзаца")
            else:
                logger.warning("Пустой ответ от YandexGPT для абзаца")
            
            logger.info("Используем fallback для абзаца-воспоминания")
            return self._generate_fallback_memory(objects, album_theme)
                        
        except Exception as e:
            logger.error(f"Ошибка генерации абзаца-воспоминания через SDK: {e}")
            logger.info("Используем fallback для абзаца-воспоминания")
            return self._generate_fallback_memory(objects, album_theme)
    
    def _create_memory_prompt(self, objects: List[str], album_theme: str) -> str:
        objects_str = ', '.join(objects)
        theme_context = f" на тему '{album_theme}'" if album_theme else ""
        
        prompt = f"""
Создай интересную историю-сказку для фотоальбома{theme_context}, используя эти объекты: {objects_str}.

ЗАДАЧА: Напиши увлекательную историю объемом 70-100 слов, как детская сказка или книжка, которая объединит эти объекты в интересный рассказ.

Требования:
1. Длина текста: 70-100 слов (не больше и не меньше)
2. Стиль: интересная история, как простая детская сказка или книжка
3. Используй как можно больше объектов из списка: {objects_str}
4. Очень простая лексика для изучающих язык (как для детей)
5. Добавь действия, события, небольшие приключения
6. Сделай историю живой и увлекательной для чтения
7. Избегай сложных слов и конструкций
8. Пиши в прошедшем времени
9. Создай завязку, развитие и приятный финал
10. Пусть объекты играют роль в истории, а не просто упоминаются

Примеры интересных историй-сказок (70-100 слов):
"Однажды маленький кот нашел волшебную книгу на старом столе. Когда он открыл её лапкой, из страниц вылетела золотая бабочка! Мама услышала шум и пришла на кухню. Вместе они смотрели, как бабочка танцевала вокруг чашки с молоком. Солнце светило в окно, и весь дом наполнился волшебством. Кот мурлыкал от счастья, а мама улыбалась. С тех пор каждое утро они читали эту особенную книгу, и каждый день приносил новые чудеса и радость."

"В небольшом доме жила дружная семья. Папа любил читать книги в большом кресле, а мама готовила вкусный суп на кухне. Дети играли с мячом во дворе, и даже старый пёс бегал за ними. Когда наступал вечер, все садились за круглый стол. Мама приносила горячий чай в красивых чашках. Тогда папа рассказывал удивительные истории из своих книг. Дети слушали с открытыми ртами, а пёс спал у их ног. Так проходили самые счастливые дни."

Напиши интересную историю-сказку длиной 70-100 слов с объектами: {objects_str}"""
        
        return prompt
    
    def _generate_fallback_memory(self, objects: List[str], album_theme: str) -> Dict[str, Any]:
        """Генерирует fallback абзац-воспоминание"""
        logger.info("Абзац-воспоминание замокан (fallback)")
        
        # Выбираем 3-4 объекта для истории
        selected_objects = objects[:min(4, len(objects))]
        
        # Шаблоны интересных историй-сказок для разных тем (70-100 слов)
        if "семья" in album_theme.lower() or "дом" in album_theme.lower():
            memory_templates = [
                f"Однажды в нашем доме случилось что-то особенное. Мама готовила ужин на кухне, когда вдруг {selected_objects[0] if len(selected_objects) > 0 else 'кот'} начал громко мяукать. Все собрались посмотреть, что произошло. Оказалось, что {selected_objects[1] if len(selected_objects) > 1 else 'маленький котёнок'} застрял под большим {selected_objects[2] if len(selected_objects) > 2 else 'столом'}! Папа аккуратно вытащил его, а дети дали ему молока из красивой чашки. С тех пор котёнок стал частью нашей семьи. Каждый вечер он спал рядом с детьми, и дом наполнился ещё большей радостью и смехом.",
                f"В нашем доме жила дружная семья, и у каждого была своя любимая вещь. Папа всегда читал интересные книги в большом кресле. Мама любила свою красивую {selected_objects[0] if len(selected_objects) > 0 else 'чашку'} для утреннего чая. Дети играли с {selected_objects[1] if len(selected_objects) > 1 else 'мячом'} во дворе после школы. Даже старый {selected_objects[2] if len(selected_objects) > 2 else 'пёс'} имел свою любимую подушку у камина. Когда наступал вечер, все собирались за большим столом. Мама готовила вкусный ужин, папа рассказывал смешные истории, а дети делились новостями из школы. Так проходили самые счастливые дни."
            ]
        elif "отдых" in album_theme.lower() or "поездка" in album_theme.lower():
            memory_templates = [
                f"Началось всё с простой идеи - поехать на дачу. Но эта поездка превратилась в настоящее приключение! Сначала мы увидели красивую {selected_objects[0] if len(selected_objects) > 0 else 'бабочку'}, которая села на {selected_objects[1] if len(selected_objects) > 1 else 'цветок'}. Потом нашли старый {selected_objects[2] if len(selected_objects) > 2 else 'мяч'} в траве и стали играть всей семьёй. Солнце светило ярко, птицы пели песни, а мы смеялись и бегали по зелёной траве. Когда устали, сели под большое дерево и ели вкусные бутерброды. Это был самый весёлый день лета!",
                f"На отдыхе с нами произошла удивительная история. Мы гуляли по парку, когда папа заметил необычный {selected_objects[0] if len(selected_objects) > 0 else 'камень'}. Мама сказала, что это может быть сокровище! Дети начали искать ещё такие камни возле {selected_objects[1] if len(selected_objects) > 1 else 'дерева'}. Вскоре мы нашли целую коллекцию красивых камешков. Вечером в отеле мы разложили их на {selected_objects[2] if len(selected_objects) > 2 else 'столе'} и придумывали, на что они похожи. Один был как сердечко, другой - как звёздочка. Эти камешки стали нашими талисманами удачи."
            ]
        else:
            # Универсальные интересные истории-сказки (70-100 слов)
            memory_templates = [
                f"Жили-были в одном доме необычные вещи. Старый {selected_objects[0] if len(selected_objects) > 0 else 'стол'} хранил много секретов, а {selected_objects[1] if len(selected_objects) > 1 else 'книга'} на полке рассказывала удивительные истории. Однажды маленький {selected_objects[2] if len(selected_objects) > 2 else 'котёнок'} решил исследовать весь дом. Он лазил под стульями, прыгал на диван и даже заглядывал в шкафы. Каждая комната была как новый мир, полный интересных открытий. Когда котёнок устал, он заснул рядом с большими книгами. Во сне ему снились волшебные приключения и новые друзья.",
                f"В одном доме случилась волшебная история. Каждое утро {selected_objects[0] if len(selected_objects) > 0 else 'солнышко'} светило в окно и будило всех жителей. Первым просыпался {selected_objects[1] if len(selected_objects) > 1 else 'петушок'} и начинал петь свою песню. Потом вставала бабушка и варила вкусную кашу в большой кастрюле. {selected_objects[2] if len(selected_objects) > 2 else 'Дети'} бежали завтракать и слушали интересные сказки. После завтрака все шли в сад, где росли красивые цветы и пели птички. Каждый день был полон радости, смеха и маленьких чудес, которые делали жизнь особенной."
            ]
        
        memory = random.choice(memory_templates)
        
        return {
            "memory": memory,
            "used_objects": selected_objects
        }
