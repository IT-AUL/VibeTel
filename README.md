# VibeTel API

API для изучения татарского языка через ассоциации с изображениями.

## Описание

VibeTel - это FastAPI приложение, которое помогает русскоязычным пользователям изучать татарский язык через визуальные ассоциации:

1. **Загружается изображение**
2. **YOLO находит объекты**
3. **YandexGPT создает предложение**
4. **Переводчик переводит на татарский**
5. **Сохраняется в базу данных**

## Установка и запуск

### 1. Создание виртуального окружения
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# или
venv\Scripts\activate     # Windows
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения
Создайте файл `.env`:
```bash
# Режим работы
LOCAL=true

# Yandex Cloud настройки
YANDEX_KEY_ID=ваш_key_id
YANDEX_SECRET_KEY=ваш_secret_key  
YANDEX_FOLDER_ID=ваш_folder_id
TRANSLATER_FOLDER_ID=ваш_translate_folder_id
TRANSLATER_API_KEY=ваш_translate_api_key

# Модель (опционально)
MODEL=yandexgpt-lite

# База данных
DATABASE_URL=sqlite:///./vibetel.db
```

### 4. Запуск сервера
```bash
python run.py
```

Сервер будет доступен на: `http://localhost:8000`

Файл `run.py` - единственная точка входа. Он:
- Проверяет переменные окружения
- Выводит информацию о режиме работы (локальный/серверный)  
- Запускает FastAPI приложение из `main.py`

## API Endpoints

### Новые разделенные ручки для фронтенда

#### 1. Выделение объектов из изображения
```http
POST /extract-objects
Content-Type: multipart/form-data
```
**Параметры:** `file` (изображение)
**Ответ:** `{"objects": ["человек", "стул", "книга"]}`

#### 2. Генерация предложений
```http
POST /generate-sentence  
Content-Type: application/json
```
**Тело запроса:**
```json
{
  "objects": ["человек", "стул"],
  "previous_sentences": []
}
```
**Ответ:**
```json
{
  "sentence": "Человек сидит на удобном стуле",
  "target_word": "человек"
}
```

#### 3. Перевод текста
```http
POST /translate
Content-Type: application/json
```
**Тело запроса:**
```json
{
  "text": "Человек сидит на удобном стуле",
  "source_language": "ru",
  "target_language": "tt"
}
```
**Ответ:**
```json
{
  "original_text": "Человек сидит на удобном стуле",
  "translated_text": "Кеше уңайлы урындыкта утыра",
  "source_language": "ru",
  "target_language": "tt"
}
```

### Старая объединенная ручка:
```http
POST /process-image
```
Выполняет все этапы сразу: объекты → предложение → перевод.

### Дополнительные ручки:
- `GET /health` - проверка состояния сервисов
- `GET /sentences` - получение сохраненных предложений  
- `GET /sentences/search?word=кот` - поиск по слову
- `GET /statistics` - статистика
- `GET /translator/languages` - поддерживаемые языки
- `GET /docs` - Swagger документация

## Тестирование

### Финальный тест всех ручек:
```bash
python final_test.py
```

### Тест-клиент для новых ручек:
```bash
python test_new_api.py
```

## Архитектура

- **FastAPI** - веб-фреймворк
- **YOLO (ultralytics)** - распознавание объектов
- **YandexGPT** - генерация предложений через Yandex Cloud ML SDK
- **Yandex Translate API** - перевод текстов
- **SQLite** - база данных
- **Pydantic** - валидация данных

## Настройки

### Локальный/Серверный режим
- `LOCAL=true` - использует `yolo11n.pt`
- `LOCAL=false` - использует `yolo11n_openvino_model/`

### Yandex Cloud
Получите ключи в [консоли Yandex Cloud](https://console.cloud.yandex.ru/):
1. **Для YandexGPT:** IAM → Сервисные аккаунты → Создайте ключ
   - Скопируйте `KEY_ID`, `SECRET_KEY`, `FOLDER_ID`
2. **Для Yandex Translate:** API ключ для Translate API
   - Скопируйте `TRANSLATER_API_KEY`

## Структура проекта

```
VibeTel/
├── app/
│   ├── models/
│   │   └── responses.py       # Pydantic модели
│   ├── services/
│   │   ├── yolo_service.py    # YOLO классификация
│   │   ├── yandex_gpt_service.py # Генерация предложений
│   │   ├── translator_service.py # Перевод
│   │   └── database_service.py   # База данных
│   ├── utils/
│   │   └── image_processor.py    # Обработка изображений
│   └── config.py              # Настройки
├── main.py                    # FastAPI приложение (только определение app)
├── run.py                     # Единственная точка входа с проверками
├── requirements.txt           # Зависимости
└── README.md                  # Документация
```

## Готово к production

- Все сервисы работают
- Fallback система для Yandex GPT
- Обработка ошибок
- Логирование
- Валидация данных
- API документация
- Тесты

## Результат

**API готово для интеграции с фронтендом!**

Русскоязычные пользователи могут изучать татарский язык через:
- Загрузку изображений
- Автоматическое выделение объектов
- Генерацию творческих предложений
- Перевод на татарский язык
- Сохранение прогресса обучения