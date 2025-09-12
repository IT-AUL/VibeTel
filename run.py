#!/usr/bin/env python3
"""
Скрипт для запуска VibeTel API сервера
"""
import os
import sys
from dotenv import load_dotenv

def check_environment():
    """Проверка переменных окружения"""
    load_dotenv()
    
    required_vars = [
        'YANDEX_GPT_API_KEY',
        'YANDEX_GPT_FOLDER_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("Предупреждение: Не настроены переменные окружения:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nSoздайте файл .env с необходимыми переменными")
        print("Приложение будет работать с ограниченным функционалом")
        print("-" * 50)

def main():
    check_environment()

    print("Запуск VibeTel API...")
    print("Сервер будет доступен на: http://localhost:8000")
    print("Документация API: http://localhost:8000/docs")
    print("Для остановки нажмите Ctrl+C")
    print("-" * 50)
    
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
