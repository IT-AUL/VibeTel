#!/usr/bin/env python3
"""
Скрипт для запуска VibeTel API сервера
"""
import os
from dotenv import load_dotenv

def check_environment():
    """Проверка переменных окружения"""
    load_dotenv()
    
    required_vars = [
        'YANDEX_KEY_ID',
        'YANDEX_SECRET_KEY',
        'YANDEX_FOLDER_ID',
        'TRANSLATER_FOLDER_ID',
        'TRANSLATER_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    local_mode = os.getenv('LOCAL', 'true').lower() == 'true'
    print(f"Режим работы: {'Локальный' if local_mode else 'Серверный'}")
    
    if missing_vars:
        print("Предупреждение: Не настроены переменные окружения:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nСоздайте файл .env с необходимыми переменными")
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
        reload=False,
        log_level="info",
        # Увеличиваем лимиты для больших файлов
        limit_max_requests=1000,
        timeout_keep_alive=30
    )

if __name__ == "__main__":
    main()
