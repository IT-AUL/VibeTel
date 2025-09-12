from pydantic import BaseModel
from typing import List
from datetime import datetime

class ProcessImageResponse(BaseModel):
    objects_ru: List[str]
    objects_tt: List[str] 
    sentence_ru: str
    sentence_tt: str
    target_word_ru: str
    target_word_tt: str

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
