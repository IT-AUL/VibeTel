import asyncio
from typing import List, Dict, Any
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

    async def classify_objects(self, image: Image.Image) -> List[Dict[str, Any]]:
        """Возвращает до 10 самых уверенных детекций со следующей структурой:
        { 'class_ru': str, 'confidence': float, 'bbox': [x1, y1, x2, y2] }
        """
        if self.model is None:
            raise RuntimeError("YOLO модель не загружена")

        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self._run_inference,
                image
            )

            detections = []
            for result in results:
                boxes = getattr(result, 'boxes', None)
                if boxes is None or len(boxes) == 0:
                    continue
                cls_list = boxes.cls.tolist()
                conf_list = boxes.conf.tolist()
                xyxy_list = boxes.xyxy.tolist()
                for cls_id, conf, xyxy in zip(cls_list, conf_list, xyxy_list):
                    class_en = self.model.names[int(cls_id)]
                    detections.append({
                        'class_en': class_en,
                        'confidence': float(conf),
                        'bbox': [float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])]
                    })

            # Переводим имена классов на русский
            if detections:
                translated = self.translate_class_names([d['class_en'] for d in detections])
                for d, name_ru in zip(detections, translated):
                    d['class_ru'] = name_ru
                    d.pop('class_en', None)

            logger.info(f"Детекции (до 10): {detections}")
            return detections

        except Exception as e:
            logger.error(f"Ошибка классификации объектов: {e}")
            raise

    def _run_inference(self, image: Image.Image):
        image_array = np.array(image)
        # Ограничиваем до 10 детекций и фильтруем по conf=0.5 встроенными параметрами
        return self.model(image_array, verbose=False, conf=0.5, max_det=10)

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
