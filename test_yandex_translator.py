#!/usr/bin/env python3
"""
Тест нового Yandex Translate API
"""
import asyncio
import os
from dotenv import load_dotenv
from app.services.translator_service import TranslatorService

async def test_yandex_translator():
    load_dotenv()
    
    translator = TranslatorService()
    
    print("Тестирование Yandex Translate API")
    print("=" * 40)
    
    # Проверяем настройки
    if not translator.api_key:
        print("❌ TRANSLATER_API_KEY не настроен")
        return False
    
    if not translator.folder_id:
        print("❌ TRANSLATER_FOLDER_ID не настроен")
        return False
    
    print(f"✅ API ключ: {translator.api_key[:10]}...")
    print(f"✅ Folder ID: {translator.folder_id}")
    print()
    
    # Тестируем перевод одного текста
    test_text = "Привет, мир!"
    print(f"Тестируем перевод: '{test_text}'")
    
    try:
        result = await translator.translate_text(test_text)
        print(f"✅ Результат: '{result}'")
        
        # Тестируем множественный перевод
        test_texts = ["собака", "кот", "дом"]
        print(f"\nТестируем множественный перевод: {test_texts}")
        
        results = await translator.translate_multiple(test_texts)
        print(f"✅ Результаты: {results}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_yandex_translator())
    
    if success:
        print("\n🎉 Yandex Translate API работает!")
    else:
        print("\n💥 Есть проблемы с настройкой")
        print("\nПроверьте .env файл:")
        print("TRANSLATER_API_KEY=ваш_api_ключ")
        print("TRANSLATER_FOLDER_ID=ваш_folder_id")
