import asyncio
from typing import List, Dict, Any
from ultralytics import YOLO
import numpy as np
from PIL import Image
import logging
from app.config import settings
from pathlib import Path

logger = logging.getLogger(__name__)


class YOLOService:
    def __init__(self):
        self.model = None
        self.class_translations: Dict[str, str] = {}
        self._load_model()
        self._load_class_translations()

    def _load_model(self):
        try:
            if settings.local:
                self.model = YOLO("yolo11n.pt")
                logger.info("YOLO модель загружена (локально): yolo11n.pt")
            else:
                self.model = YOLO("yolov8n-oiv7_openvino_model/")
                logger.info("YOLO модель загружена (сервер): yolo11n_openvino_model/")
        except Exception as e:
            logger.error(f"Ошибка загрузки YOLO модели: {e}")
            raise

    def _load_class_translations(self) -> None:
        """Загружает словарь классов из файла classes.txt в формате 'original:translation'."""
        try:
            service_dir = Path(__file__).resolve().parent
            project_root = service_dir.parent.parent
            classes_path = project_root / "classes.txt"

            if not classes_path.exists():
                logger.warning(f"Файл со списком классов не найден: {classes_path}")
                self.class_translations = {}
                return

            translations: Dict[str, str] = {}
            with classes_path.open("r", encoding="utf-8") as f:
                for i, raw_line in enumerate(f, start=1):
                    line = raw_line.strip()
                    # Пропускаем пустые строки и комментарии
                    if not line or line.startswith("#"):
                        continue
                    if ":" not in line:
                        logger.warning(f"Строка {i} в {classes_path} пропущена: нет разделителя ':'")
                        continue
                    original, translation = line.split(":", 1)
                    original = original.strip()
                    translation = translation.strip()
                    if not original:
                        logger.warning(f"Строка {i} в {classes_path} пропущена: пустой original")
                        continue
                    # Ключи приводим к нижнему регистру для устойчивого поиска
                    translations[original.lower()] = translation or original

            self.class_translations = translations
            logger.info(
                f"Загружено классов для перевода: {len(self.class_translations)} из {classes_path}"
            )
        except Exception as e:
            logger.error(f"Ошибка загрузки classes.txt: {e}")
            self.class_translations = {}

    async def classify_objects(self, image: Image.Image) -> List[Dict[str, Any]]:
        """Возвращает до 10 детекций: [{class_ru, confidence, bbox[x1,y1,x2,y2]}]."""
        if self.model is None:
            raise RuntimeError("YOLO модель не загружена")

        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self._run_inference,
                image
            )

            detections: List[Dict[str, Any]] = []
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

            # Переводим на русский и убираем class_en
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

    def _run_inference(self, image: Image.Image, conf: float = 0.5, max_det: int = 10):
        image_array = np.array(image)
        # Ограничиваем до 10 детекций и фильтруем по conf встроенными параметрами
        return self.model(image_array, verbose=False, conf=conf, max_det=max_det)

    def translate_class_names(self, objects: List[str]) -> List[str]:
        """Переводит список английских названий классов в русские по classes.txt.
        Если перевод не найден, возвращает оригинал.
        """
        translated: List[str] = []
        for obj in objects:
            key = (obj or "").lower()
            translated_name = self.class_translations.get(key, obj)
            translated.append(translated_name)

        return translated
