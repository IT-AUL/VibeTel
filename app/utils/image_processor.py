import io
import logging
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self):
        self.max_size = (1024, 1024)
        self.supported_formats = ['JPEG', 'PNG', 'JPG', 'WEBP']
    
    async def process_uploaded_image(self, image_data: bytes) -> Image.Image:
        try:
            image = Image.open(io.BytesIO(image_data))
            
            if image.format not in self.supported_formats:
                logger.warning(f"Неподдерживаемый формат изображения: {image.format}")
            
            if image.mode != 'RGB':
                image = image.convert('RGB')
                logger.info(f"Изображение конвертировано в RGB режим")
            
            image = self._resize_image(image)
            
            logger.info(f"Изображение обработано: размер {image.size}, режим {image.mode}")
            return image
            
        except Exception as e:
            logger.error(f"Ошибка обработки изображения: {e}")
            raise ValueError(f"Не удалось обработать изображение: {e}")
    
    def _resize_image(self, image: Image.Image) -> Image.Image:
        if image.size[0] <= self.max_size[0] and image.size[1] <= self.max_size[1]:
            return image
        
        image.thumbnail(self.max_size, Image.Resampling.LANCZOS)
        logger.info(f"Изображение изменено до размера: {image.size}")
        return image
    
    async def validate_image(self, image_data: bytes) -> bool:
        try:
            image = Image.open(io.BytesIO(image_data))
            
            if image.format not in self.supported_formats:
                return False
            
            if image.size[0] < 32 or image.size[1] < 32:
                logger.warning("Изображение слишком маленькое")
                return False
            
            if image.size[0] > 4096 or image.size[1] > 4096:
                logger.warning("Изображение слишком большое")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка валидации изображения: {e}")
            return False
    
    def get_image_info(self, image: Image.Image) -> dict:
        return {
            'width': image.size[0],
            'height': image.size[1],
            'mode': image.mode,
            'format': getattr(image, 'format', 'Unknown')
        }
    
    async def prepare_for_yolo(self, image: Image.Image) -> np.ndarray:
        try:
            image_array = np.array(image)
            
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                image_array = image_array[:, :, ::-1]
            
            logger.info(f"Изображение подготовлено для YOLO: форма {image_array.shape}")
            return image_array
            
        except Exception as e:
            logger.error(f"Ошибка подготовки изображения для YOLO: {e}")
            raise
