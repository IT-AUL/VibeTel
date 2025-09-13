from enum import Enum

from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime


class ProcessImageResponse(BaseModel):
    objects_ru: List[str]
    objects_tt: List[str]
    sentence_ru: str
    sentence_tt: str
    target_word_ru: str
    target_word_tt: str
    detections: List[Dict[str, Any]]


class SentenceRecord(BaseModel):
    id: int
    sentence: str
    target_word: str
    objects: List[str]
    created_at: datetime


class SentencesResponse(BaseModel):
    sentences: List[SentenceRecord]


class TranslationDirectionResponse(BaseModel):
    source_language: str
    target_language: str


class TranslationDirectionRequest(BaseModel):
    source_language: str
    target_language: str


class ObjectsResponse(BaseModel):
    objects: List[str]
    objects_tt: List[str] = []  # переводы на татарский
    detections: List[Dict[str, Any]]


class SentenceGenerationRequest(BaseModel):
    objects: List[str]
    previous_sentences: List[str] = []


class SentenceGenerationResponse(BaseModel):
    sentence: str
    target_word: str


# Новая модель ответа: сразу две версии предложения (RU и TT)
class BilingualSentenceResponse(BaseModel):
    sentence_ru: str
    sentence_tt: str
    target_word_ru: str
    target_word_tt: str


class TranslationRequest(BaseModel):
    text: str
    source_language: str = "ru"
    target_language: str = "tt"


class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str


class Speaker(Enum):
    ALSU = "alsu"
    ALMAZ = "almaz"


class AudioRequest(BaseModel):
    text: str
    speaker: Speaker = Speaker.ALSU


class AudioResponse(BaseModel):
    audio_base64: str
