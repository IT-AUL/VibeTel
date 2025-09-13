import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.services.yolo_service import YOLOService
from app.services.yandex_gpt_service import YandexGPTService
from app.services.translator_service import TranslatorService
from app.services.database_service import DatabaseService
from app.models.responses import (
    ProcessImageResponse, SentencesResponse, TranslationDirectionResponse,
    TranslationDirectionRequest, ObjectsResponse, SentenceGenerationRequest,
    SentenceGenerationResponse, TranslationRequest, TranslationResponse, AudioRequest, AudioResponse
)
from app.utils.image_processor import ImageProcessor
# Импортируем модуль сервиса аудио, чтобы избежать конфликта имён функции
from app.services import audio_generator

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database_service.init_db()
    yield
    await database_service.close()


app = FastAPI(
    title="VibeTel API",
    description="API для обучения языку через ассоциации и истории",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

yolo_service = YOLOService()
yandex_gpt_service = YandexGPTService()
translator_service = TranslatorService()
database_service = DatabaseService()
image_processor = ImageProcessor()


@app.get("/")
async def root():
    return {"message": "VibeTel API работает!"}


@app.post("/process-image", response_model=ProcessImageResponse)
async def process_image(file: UploadFile = File(...)):
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Файл должен быть изображением")

        image_data = await file.read()

        image = await image_processor.process_uploaded_image(image_data)

        # Получаем детекции с координатами
        detections = await yolo_service.classify_objects(image)
        if not detections:
            raise HTTPException(status_code=400, detail="Объекты на изображении не обнаружены")

        # Список уникальных русских названий объектов по убыванию уверенности
        objects_ru = []
        for d in detections:
            name = d.get('class_ru')
            if name and name not in objects_ru:
                objects_ru.append(name)

        previous_sentences = await database_service.get_recent_sentences(limit=10)

        sentence_data = await yandex_gpt_service.generate_sentence(
            objects=objects_ru,
            previous_sentences=previous_sentences
        )

        # Переводим с русского на татарский
        objects_tt = await translator_service.translate_multiple(objects_ru)
        sentence_tt = await translator_service.translate_text(sentence_data["sentence"])
        target_word_tt = await translator_service.translate_text(sentence_data["target_word"])

        await database_service.save_sentence(
            sentence=sentence_data["sentence"],
            target_word=sentence_data["target_word"],
            objects=objects_ru
        )

        return ProcessImageResponse(
            objects_ru=objects_ru,
            objects_tt=objects_tt,
            sentence_ru=sentence_data["sentence"],
            sentence_tt=sentence_tt,
            target_word_ru=sentence_data["target_word"],
            target_word_tt=target_word_tt,
            detections=detections
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {str(e)}")


# Новые разделенные ручки для фронта

@app.post("/extract-objects", response_model=ObjectsResponse)
async def extract_objects(file: UploadFile = File(...)):
    """Ручка для выделения объектов из изображения с координатами bbox"""
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Файл должен быть изображением")

        image_data = await file.read()
        image = await image_processor.process_uploaded_image(image_data)

        detections = await yolo_service.classify_objects(image)
        if not detections:
            raise HTTPException(status_code=400, detail="Объекты на изображении не обнаружены")

        objects_ru = []
        for d in detections:
            name = d.get('class_ru')
            if name and name not in objects_ru:
                objects_ru.append(name)

        return ObjectsResponse(objects=objects_ru, detections=detections)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {str(e)}")


@app.post("/generate-sentence", response_model=SentenceGenerationResponse)
async def generate_sentence(request: SentenceGenerationRequest):
    """Ручка для составления предложений по объектам"""
    try:
        if not request.objects:
            raise HTTPException(status_code=400, detail="Список объектов не может быть пустым")

        previous_sentences = request.previous_sentences if request.previous_sentences else await database_service.get_recent_sentences(
            limit=10)

        sentence_data = await yandex_gpt_service.generate_sentence(
            objects=request.objects,
            previous_sentences=previous_sentences
        )

        # Сохраняем предложение в базу данных
        await database_service.save_sentence(
            sentence=sentence_data["sentence"],
            target_word=sentence_data["target_word"],
            objects=request.objects
        )

        return SentenceGenerationResponse(
            sentence=sentence_data["sentence"],
            target_word=sentence_data["target_word"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации предложения: {str(e)}")


@app.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """Ручка для перевода текста"""
    try:
        if not request.text:
            raise HTTPException(status_code=400, detail="Текст для перевода не может быть пустым")

        translated_text = await translator_service.translate_text(
            text=request.text,
            source_lang=request.source_language,
            target_lang=request.target_language
        )

        return TranslationResponse(
            original_text=request.text,
            translated_text=translated_text,
            source_language=request.source_language,
            target_language=request.target_language
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка перевода: {str(e)}")


@app.get("/sentences")
async def get_sentences(limit: int = 20):
    sentences = await database_service.get_sentences_with_details(limit=limit)
    return SentencesResponse(sentences=sentences)


@app.get("/sentences/search")
async def search_sentences(word: str = Query(..., description="Слово для поиска"), limit: int = 10):
    sentences = await database_service.get_sentences_by_word(word=word, limit=limit)
    return {"sentences": sentences}


@app.get("/statistics")
async def get_statistics():
    stats = await database_service.get_statistics()
    return stats


@app.post("/translator/language")
async def set_translation_language(language_code: str = Query(..., description="Код языка (например: en, de, fr)")):
    supported_languages = translator_service.get_supported_languages()

    if language_code not in supported_languages:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый язык. Доступные языки: {list(supported_languages.keys())}"
        )

    translator_service.set_target_language(language_code)
    return {
        "message": f"Язык перевода изменен на: {supported_languages[language_code]}",
        "language_code": language_code
    }


@app.get("/translator/languages")
async def get_supported_languages():
    return translator_service.get_supported_languages()


@app.get("/translator/direction", response_model=TranslationDirectionResponse)
async def get_translation_direction():
    direction = translator_service.get_translation_direction()
    return TranslationDirectionResponse(**direction)


@app.post("/translator/direction")
async def set_translation_direction(request: TranslationDirectionRequest):
    supported_languages = translator_service.get_supported_languages()

    if request.source_language not in supported_languages:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый исходный язык. Доступные языки: {list(supported_languages.keys())}"
        )

    if request.target_language not in supported_languages:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый целевой язык. Доступные языки: {list(supported_languages.keys())}"
        )

    translator_service.set_translation_direction(
        request.source_language,
        request.target_language
    )

    return {
        "message": f"Направление перевода изменено: {supported_languages[request.source_language]} -> {supported_languages[request.target_language]}",
        "source_language": request.source_language,
        "target_language": request.target_language
    }


@app.post("/audio", response_model=AudioResponse)
async def generate_audio(request: AudioRequest):
    try:
        result = await audio_generator.generate_audio(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        # Ошибки внешнего TTS сервиса
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации аудио: {str(e)}")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "yolo": "OK" if yolo_service.model else "ERROR",
            "database": "OK" if database_service.connection else "ERROR",
            "yandex_gpt": "OK" if yandex_gpt_service.sdk else "NOT_CONFIGURED"
        }
    }
