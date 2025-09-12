import aiosqlite
import json
import os
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.db_path = os.getenv('DATABASE_URL', 'sqlite:///./vibetel.db').replace('sqlite:///', '')
        self.connection = None
    
    async def init_db(self):
        try:
            self.connection = await aiosqlite.connect(self.db_path)
            await self._create_tables()
            logger.info("База данных инициализирована")
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            raise
    
    async def _create_tables(self):
        create_sentences_table = """
        CREATE TABLE IF NOT EXISTS sentences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sentence TEXT NOT NULL,
            target_word TEXT NOT NULL,
            objects TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        await self.connection.execute(create_sentences_table)
        await self.connection.commit()
    
    async def save_sentence(self, sentence: str, target_word: str, objects: List[str]):
        try:
            objects_json = json.dumps(objects, ensure_ascii=False)
            
            query = """
            INSERT INTO sentences (sentence, target_word, objects)
            VALUES (?, ?, ?)
            """
            
            await self.connection.execute(query, (sentence, target_word, objects_json))
            await self.connection.commit()
            
            logger.info(f"Предложение сохранено: {sentence}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения предложения: {e}")
            raise
    
    async def get_recent_sentences(self, limit: int = 10) -> List[str]:
        try:
            query = """
            SELECT sentence FROM sentences 
            ORDER BY created_at DESC 
            LIMIT ?
            """
            
            cursor = await self.connection.execute(query, (limit,))
            rows = await cursor.fetchall()
            
            sentences = [row[0] for row in rows]
            return sentences
            
        except Exception as e:
            logger.error(f"Ошибка получения предложений: {e}")
            return []
    
    async def get_sentences_with_details(self, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            query = """
            SELECT id, sentence, target_word, objects, created_at 
            FROM sentences 
            ORDER BY created_at DESC 
            LIMIT ?
            """
            
            cursor = await self.connection.execute(query, (limit,))
            rows = await cursor.fetchall()
            
            sentences = []
            for row in rows:
                sentence_data = {
                    'id': row[0],
                    'sentence': row[1],
                    'target_word': row[2],
                    'objects': json.loads(row[3]),
                    'created_at': row[4]
                }
                sentences.append(sentence_data)
            
            return sentences
            
        except Exception as e:
            logger.error(f"Ошибка получения детальных данных предложений: {e}")
            return []
    
    async def get_sentences_by_word(self, word: str, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            query = """
            SELECT id, sentence, target_word, objects, created_at 
            FROM sentences 
            WHERE target_word LIKE ? 
            ORDER BY created_at DESC 
            LIMIT ?
            """
            
            cursor = await self.connection.execute(query, (f'%{word}%', limit))
            rows = await cursor.fetchall()
            
            sentences = []
            for row in rows:
                sentence_data = {
                    'id': row[0],
                    'sentence': row[1],
                    'target_word': row[2],
                    'objects': json.loads(row[3]),
                    'created_at': row[4]
                }
                sentences.append(sentence_data)
            
            return sentences
            
        except Exception as e:
            logger.error(f"Ошибка поиска предложений по слову: {e}")
            return []
    
    async def get_statistics(self) -> Dict[str, Any]:
        try:
            total_query = "SELECT COUNT(*) FROM sentences"
            cursor = await self.connection.execute(total_query)
            total_sentences = (await cursor.fetchone())[0]
            
            words_query = "SELECT COUNT(DISTINCT target_word) FROM sentences"
            cursor = await self.connection.execute(words_query)
            unique_words = (await cursor.fetchone())[0]
            
            recent_query = """
            SELECT COUNT(*) FROM sentences 
            WHERE created_at >= datetime('now', '-24 hours')
            """
            cursor = await self.connection.execute(recent_query)
            recent_sentences = (await cursor.fetchone())[0]
            
            return {
                'total_sentences': total_sentences,
                'unique_words': unique_words,
                'sentences_today': recent_sentences
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {
                'total_sentences': 0,
                'unique_words': 0,
                'sentences_today': 0
            }
    
    async def close(self):
        if self.connection:
            await self.connection.close()
            logger.info("Соединение с базой данных закрыто")
