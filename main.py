import asyncio
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv

from app.services.yolo_service import YOLOService
from app.services.yandex_gpt_service import YandexGPTService
from app.services.translator_service import TranslatorService
from app.services.database_service import DatabaseService
from app.models.responses import ProcessImageResponse, SentencesResponse, TranslationDirectionResponse, TranslationDirectionRequest
from app.utils.image_processor import ImageProcessor

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
        
        objects_ru = await yolo_service.classify_objects(image)
        if not objects_ru:
            raise HTTPException(status_code=400, detail="Объекты на изображении не обнаружены")
        
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
            target_word_tt=target_word_tt
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {str(e)}")

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

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "yolo": "активен" if yolo_service.model else "недоступен",
            "database": "активен" if database_service.connection else "недоступен",
            "yandex_gpt": "активен" if yandex_gpt_service.api_key else "не настроен"
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
