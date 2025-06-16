# Whisper - Гибридный микросервис для распознавания речи

## Обзор
Whisper - это современный микросервис для распознавания речи с гибридной архитектурой, который сочетает в себе мощь OpenAI Whisper API и надежность локального fallback. Система обеспечивает голосовую аутентификацию, точное распознавание речи и автоматический перевод.

## Ключевые особенности
- **Гибридная архитектура**: OpenAI Whisper API как основной сервис + локальный Whisper как fallback
- **Голосовая аутентификация**: Верификация пользователей по голосу с использованием голосовых отпечатков
- **Масштабируемость**: Обработка больших файлов с автоматическим разбиением на фрагменты
- **Многоязычность**: Поддержка множества языков и автоматическое определение языка
- **Перевод**: Автоматический перевод речи с одного языка на другой
- **Семантическая валидация**: Сравнение результатов разных моделей для повышения точности
- **Мониторинг**: Проверка состояния всех сервисов и API

## Архитектура

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Audio Input   │    │   Hybrid STT     │    │   Output        │
│                 │    │                  │    │                 │
│ • WAV/MP3/OGG   │───▶│ 1. OpenAI API    │───▶│ • Transcription │
│ • M4A/FLAC      │    │ 2. Local Whisper │    │ • Translation   │
│ • Large Files   │    │ 3. Fallback      │    │ • Speaker ID    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Рабочий процесс
1. **Настройка**: Конфигурация OpenAI API ключа и локального fallback
2. **Обработка аудио**: Получение аудиофайла через API или CLI
3. **Гибридное распознавание**: 
   - Попытка транскрипции через OpenAI Whisper API
   - При неудаче - автоматический fallback на локальную модель
   - Для больших файлов - автоматическое разбиение на фрагменты
4. **Дополнительные возможности**:
   - Голосовая верификация (опционально)
   - Семантическая валидация результатов
   - Автоматический перевод на целевой язык
5. **Возврат результата**: Структурированный ответ с метаданными

## Подробные инструкции

### Установка

#### Быстрый старт (рекомендуется)
```bash
# Клонировать репозиторий
git clone https://github.com/username/whisper.git
cd whisper

# Настроить OpenAI API ключ
export OPENAI_API_KEY="sk-your-openai-api-key-here"

# Быстрый старт для разработчиков
make quick-start

# Или посмотреть все доступные команды
make help
```

#### С использованием Docker
```bash
# Клонировать репозиторий
git clone https://github.com/username/whisper.git
cd whisper

# Настроить переменные окружения
cp .env.sample .env
# Отредактировать .env файл, добавить OPENAI_API_KEY

# Запустить с Docker Compose
docker-compose up -d
# или
make dev
```

#### Ручная установка
```bash
# Клонировать репозиторий
git clone https://github.com/username/whisper.git
cd whisper

# Настроить OpenAI API ключ
export OPENAI_API_KEY="sk-your-openai-api-key-here"

# Запустить скрипт установки
./setup.sh
# или
make setup

# Или вручную:
# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Запустить приложение
python app/main.py
```

### Основные команды разработки

Проект использует Makefile для упрощения основных задач разработки:

```bash
# Показать все доступные команды
make help

# Быстрый старт для новых разработчиков
make quick-start

# Разработка
make dev              # Запустить среду разработки
make build            # Собрать Docker образы
make logs             # Показать логи сервисов
make status           # Показать статус сервисов

# Тестирование
make test             # Запустить все тесты
make test-unit        # Только unit тесты
make test-api         # Только API тесты
make test-coverage    # Тесты с покрытием кода

# Качество кода
make lint             # Проверить код линтерами
make format           # Отформатировать код

# Деплой
make deploy           # Деплой в production
make deploy-staging   # Деплой в staging

# Очистка
make clean            # Очистить контейнеры
make clean-all        # Полная очистка
```

### Настройка голосовой авторизации

```bash
# Запись образцов голоса
./record_samples.py --samples 3 --duration 10

# Регистрация голосового отпечатка
./cli_tests/test_client.py register samples/sample_1.wav samples/sample_2.wav samples/sample_3.wav
```

### Использование API

#### Гибридное распознавание речи (основная функция)
```bash
curl -X POST \
  http://localhost:8000/api/v1/hybrid/stt \
  -H "X-API-Key: your-api-key" \
  -F "audio_file=@./speech.wav" \
  -F "language=ru" \
  -F "prompt=Медицинская консультация" \
  -F "verify_speaker=false" \
  -F "use_semantics=true" \
  -F "semantic_threshold=0.8" \
  -F "return_debug=true"
```

#### Перевод аудио
```bash
curl -X POST \
  http://localhost:8000/api/v1/hybrid/translate \
  -H "X-API-Key: your-api-key" \
  -F "audio_file=@./speech.wav" \
  -F "target_language=en" \
  -F "source_language=ru"
```

#### Верификация голоса
```bash
curl -X POST \
  http://localhost:8000/api/v1/voice/verify \
  -H "X-API-Key: your-api-key" \
  -F "audio_file=@./command.wav"
```

#### Проверка состояния сервиса
```bash
curl -X GET http://localhost:8000/health
```

#### Ответ API (гибридная архитектура)
```json
{
  "source": "openai",  // "openai", "local", или "fallback"
  "text": "включи свет в спальне",
  "metadata": {
    "confidence": 0.93,  // только для локальной модели
    "speaker_match": 0.97,  // если включена верификация
    "duration": 7.5,
    "language": "ru",
    "fallback_used": false,  // был ли использован fallback
    "semantic_diff": null,   // семантическая разница (если применимо)
    "chunks_processed": 1,   // количество фрагментов для больших файлов
    "model_used": "gpt-4o-transcribe",  // используемая модель
    "processing_time": 2.1   // время обработки в секундах
  },
  "debug": {  // только при return_debug=true
    "openai_response": {...},
    "chunk_details": [...],
    "fallback_reason": null
  }
}
```

#### Ответ API (перевод)
```json
{
  "source": "openai",
  "original_text": "включи свет в спальне",
  "translated_text": "turn on the light in the bedroom",
  "source_language": "ru",
  "target_language": "en",
  "metadata": {
    "duration": 7.5,
    "chunks_processed": 1,
    "processing_time": 3.2
  }
}
```

## Дополнительная документация

Более подробные инструкции доступны в [руководстве пользователя](docs/GUIDE.md), которое включает:

- Детальное описание гибридной архитектуры
- Настройка OpenAI API и локального fallback
- Описание всех API endpoints и параметров
- Конфигурация семантической валидации
- Работа с большими аудиофайлами
- Варианты конфигурации системы
- Решение проблем и отладка
- Примеры использования CLI и API

Для архитектурного обзора см. [документацию архитектуры](docs/ARCHITECTURE.md).

Для информации об интеграции микросервиса с другими проектами см. [руководство по интеграции](docs/INTEGRATION_GUIDE.md).

Для ручного тестирования компонентов используйте [CLI-утилиты](cli_tests/README.md).

Для настройки CI/CD и автоматического развертывания см. [руководство по CI/CD](docs/CI_CD_SETUP.md).

## CI/CD и автоматическое развертывание

Проект настроен для автоматического развертывания через GitHub Actions. При пуше в ветку `main` автоматически:

1. Код загружается на сервер
2. Обновляются Docker образы
3. Перезапускаются сервисы
4. Выполняется проверка работоспособности

### Настройка GitHub Secrets

Для работы CI/CD и гибридной архитектуры необходимо настроить следующие секреты в GitHub:

**Обязательные секреты**:
- `OPENAI_API_KEY` - API ключ для OpenAI Whisper API
- `SSH_HOST` - IP адрес или домен сервера
- `SSH_USER` - пользователь для SSH подключения (например, `deploy`)  
- `SSH_KEY` - приватный SSH ключ для подключения к серверу

**Опциональные секреты**:
- `SSH_PORT` - порт SSH (опционально, по умолчанию 22)
- `PROJECT_PATH` - путь к проекту на сервере
- `PRIMARY_SERVICE` - основной сервис (openai/local)
- `FALLBACK_TO_LOCAL` - включить fallback на локальную модель

Подробные инструкции в [docs/GITHUB_SECRETS_SETUP.md](docs/GITHUB_SECRETS_SETUP.md).

## Требования
- Python 3.12+
- FFmpeg для обработки аудиофайлов
- OpenAI API ключ (для основного сервиса)
- Docker (для контейнеризованного развертывания)
- Поддержка GPU (опционально, для ускорения локального fallback)
- Интернет-соединение (для OpenAI API)

## Поддерживаемые форматы аудио
- WAV, MP3, OGG, FLAC, M4A
- Максимальный размер файла: 25 МБ для OpenAI API
- Автоматическое разбиение больших файлов на фрагменты
- Поддержка различных кодеков и битрейтов

## Лицензия
[MIT License](LICENSE)