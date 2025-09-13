import asyncio
from typing import List
from ultralytics import YOLO
import numpy as np
from PIL import Image
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class YOLOService:
    def __init__(self):
        self.model = None
        self._load_model()

    def _load_model(self):
        try:
            if settings.local:
                self.model = YOLO("yolo11n.pt")
                logger.info("YOLO модель загружена (локально): yolo11n.pt")
            else:
                self.model = YOLO("yolo11n_openvino_model/")
                logger.info("YOLO модель загружена (сервер): yolo11n_openvino_model/")
        except Exception as e:
            logger.error(f"Ошибка загрузки YOLO модели: {e}")
            raise

    async def classify_objects(self, image: Image.Image) -> List[str]:
        if self.model is None:
            raise RuntimeError("YOLO модель не загружена")

        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self._run_inference,
                image
            )

            detected_objects = []
            for result in results:
                if result.boxes is not None:
                    for cls in result.boxes.cls:
                        class_name = self.model.names[int(cls)]
                        detected_objects.append(class_name)

            translated_objects = self.translate_class_names(detected_objects)
            logger.info(f"Обнаружены объекты (до 10): {detected_objects} -> {translated_objects}")
            return translated_objects

        except Exception as e:
            logger.error(f"Ошибка классификации объектов: {e}")
            raise

    def _run_inference(self, image: Image.Image, conf=0.5, max_det=10):
        image_array = np.array(image)
        # Встроенные параметры YOLO: ограничиваем до 10 самых уверенных детекций и порог 0.5
        return self.model(image_array, verbose=False, conf=conf, max_det=max_det)

    def translate_class_names(self, objects: List[str]) -> List[str]:
        class_translations = {
            'person': 'человек',
            'bicycle': 'велосипед',
            'car': 'машина',
            'motorcycle': 'мотоцикл',
            'airplane': 'самолет',
            'bus': 'автобус',
            'train': 'поезд',
            'truck': 'грузовик',
            'boat': 'лодка',
            'traffic light': 'светофор',
            'fire hydrant': 'пожарный гидрант',
            'stop sign': 'знак стоп',
            'parking meter': 'парковочный счетчик',
            'bench': 'скамейка',
            'bird': 'птица',
            'cat': 'кот',
            'dog': 'собака',
            'horse': 'лошадь',
            'sheep': 'овца',
            'cow': 'корова',
            'elephant': 'слон',
            'bear': 'медведь',
            'zebra': 'зебра',
            'giraffe': 'жираф',
            'backpack': 'рюкзак',
            'umbrella': 'зонт',
            'handbag': 'сумка',
            'tie': 'галстук',
            'suitcase': 'чемодан',
            'frisbee': 'фрисби',
            'skis': 'лыжи',
            'snowboard': 'сноуборд',
            'sports ball': 'спортивный мяч',
            'kite': 'воздушный змей',
            'baseball bat': 'бейсбольная бита',
            'baseball glove': 'бейсбольная перчатка',
            'skateboard': 'скейтборд',
            'surfboard': 'доска для серфинга',
            'tennis racket': 'теннисная ракетка',
            'bottle': 'бутылка',
            'wine glass': 'бокал',
            'cup': 'чашка',
            'fork': 'вилка',
            'knife': 'нож',
            'spoon': 'ложка',
            'bowl': 'миска',
            'banana': 'банан',
            'apple': 'яблоко',
            'sandwich': 'сэндвич',
            'orange': 'апельсин',
            'broccoli': 'брокколи',
            'carrot': 'морковь',
            'hot dog': 'хот-дог',
            'pizza': 'пицца',
            'donut': 'пончик',
            'cake': 'торт',
            'chair': 'стул',
            'couch': 'диван',
            'potted plant': 'горшечное растение',
            'bed': 'кровать',
            'dining table': 'обеденный стол',
            'toilet': 'туалет',
            'tv': 'телевизор',
            'laptop': 'ноутбук',
            'mouse': 'мышь',
            'remote': 'пульт',
            'keyboard': 'клавиатура',
            'cell phone': 'мобильный телефон',
            'microwave': 'микроволновка',
            'oven': 'духовка',
            'toaster': 'тостер',
            'sink': 'раковина',
            'refrigerator': 'холодильник',
            'book': 'книга',
            'clock': 'часы',
            'vase': 'ваза',
            'scissors': 'ножницы',
            'teddy bear': 'плюшевый медведь',
            'hair drier': 'фен',
            'toothbrush': 'зубная щетка'
        }

        translated = []
        for obj in objects:
            translated_name = class_translations.get(obj.lower(), obj)
            translated.append(translated_name)

        return translated
