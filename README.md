# VibeTel - API для изучения языка через ассоциации

FastAPI приложение для обучения языку через обработку изображений, классификацию объектов YOLO и генерацию предложений с помощью Yandex GPT, с переводом на татарский язык.

## Возможности

- Загрузка и обработка изображений
- Классификация объектов с помощью YOLO (переводы на татарский)
- Генерация обучающих предложений на татарском языке через Yandex GPT
- Перевод предложений с татарского на разные языки (русский, английский и др.)
- Хранение истории предложений на татарском
- Статистика обучения

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd VibeTel
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Настройте переменные окружения:

```bash
cp env.example .env
```

Отредактируйте файл `.env` и добавьте ваши API ключи:

```bash
YANDEX_GPT_API_KEY=ваш_api_ключ_yandex_gpt
YANDEX_GPT_FOLDER_ID=ваш_folder_id_yandex
YANDEX_GPT_MODEL_URI=gpt://ваш_folder_id/yandexgpt-lite/latest
DATABASE_URL=sqlite:///./vibetel.db
```

### Получение API ключей Yandex GPT:

1. Перейдите на [Yandex Cloud](https://cloud.yandex.ru/)
2. Создайте каталог и сервисный аккаунт
3. Назначьте роль `ai.languageModels.user`
4. Создайте API ключ
5. Скопируйте `folder_id` из URL консоли

## Запуск

```bash
python main.py
```

Приложение будет доступно по адресу: `http://localhost:8000`

## Тестирование

**Подробная инструкция по тестированию:** [TESTING.md](./TESTING.md)

### Быстрый тест:

```bash
python example_client.py
```

## API Endpoints

### POST /process-image
Обработка изображения и генерация предложения на татарском языке
- Принимает: файл изображения
- Возвращает: объекты (на татарском), предложение (на татарском), целевое слово и их переводы

### GET /sentences
Получение списка сохраненных предложений

### GET /sentences/search?word=слово
Поиск предложений по ключевому слову

### GET /statistics
Статистика использования

### POST /translator/language?language_code=en
Установка языка перевода

### GET /translator/languages
Список поддерживаемых языков

### GET /health
Проверка состояния сервисов

## Документация API

После запуска сервера документация доступна по адресу:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Архитектура

```
app/
├── services/          # Бизнес-логика
│   ├── yolo_service.py      # Классификация изображений
│   ├── yandex_gpt_service.py # Генерация предложений
│   ├── translator_service.py # Перевод текста
│   └── database_service.py   # Работа с БД
├── models/            # Pydantic модели
│   └── responses.py
├── utils/             # Утилиты
│   └── image_processor.py
└── __init__.py

main.py               # Главный файл приложения
requirements.txt      # Зависимости
```

## Технологии

- **FastAPI** - веб-фреймворк
- **YOLO** (ultralytics) - классификация объектов с переводом на татарский
- **Yandex GPT** - генерация предложений на татарском языке
- **Google Translate** - перевод с татарского на другие языки
- **SQLite** - база данных
- **Pillow** - обработка изображений