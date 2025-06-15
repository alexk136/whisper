# Whisper Voice Auth Microservice - Руководство

## Содержание
- [Установка](#установка)
- [Запись голосовых образцов](#запись-голосовых-образцов)
- [Регистрация голосового отпечатка](#регистрация-голосового-отпечатка)
- [Проверка авторизации голосом](#проверка-авторизации-голосом)
- [Гибридное распознавание речи](#гибридное-распознавание-речи)
- [API Endpoints](#api-endpoints)
- [Интеграция с языковыми моделями](#интеграция-с-языковыми-моделями)
- [Конфигурация](#конфигурация)
- [Работа с Docker](#работа-с-docker)
- [Устранение неполадок](#устранение-неполадок)

## Установка

### Автоматическая установка
```bash
./setup.sh
```

### Ручная установка
```bash
# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt

# Создание необходимых директорий
mkdir -p storage/audio storage/voiceprints

# Генерация ключа шифрования
python generate_key.py
```

## Запись голосовых образцов

Для регистрации голосового отпечатка нужно записать несколько образцов вашего голоса:

```bash
./record_samples.py --samples 3 --duration 10
```

Это запишет 3 аудиофайла по 10 секунд каждый в директорию `samples/`.

## Регистрация голосового отпечатка

После записи образцов зарегистрируйте ваш голосовой отпечаток:

```bash
./test_client.py register samples/sample_1.wav samples/sample_2.wav samples/sample_3.wav
```

## Проверка авторизации голосом

Запишите команду и проверьте авторизацию:

```bash
# Запись тестовой команды
./record_samples.py --samples 1 --duration 5 --output-dir test_commands

# Проверка авторизации
./test_client.py verify test_commands/sample_1.wav
```

## Гибридное распознавание речи

Микросервис поддерживает гибридный подход к распознаванию речи, который использует как локальную модель Whisper, так и внешний API для повышения качества и надежности.

### Принцип работы

1. **Локальная обработка (первичная):**
   - Аудиофайл сначала обрабатывается локальной моделью Whisper
   - Проверяется уверенность распознавания (`confidence`)
   - Если включена верификация голоса, проверяется соответствие голосовому отпечатку (`speaker_match`)

2. **Внешняя обработка (резервная):**
   - Используется в случаях, когда:
     - Локальная обработка выдала ошибку
     - Уверенность распознавания (`confidence`) ниже порогового значения
     - Соответствие голосу (`speaker_match`) ниже порогового значения
     - Язык не поддерживается локальной моделью

3. **Выбор лучшего результата:**
   - При включенной семантической валидации сравнивается смысл результатов
   - Выбирается результат с наилучшими показателями

### Использование через CLI

Для тестирования гибридного распознавания речи можно использовать CLI-скрипт:

```bash
./hybrid_stt.py --file ./samples/command.wav --verify_speaker --use_semantics --semantic_threshold 0.8
```

Параметры:
- `--file` - путь к аудиофайлу (обязательный)
- `--verify_speaker` - включить проверку голоса
- `--use_semantics` - включить семантическую валидацию результатов
- `--semantic_threshold` - порог семантической близости (0.0-1.0)

### Настройка гибридной системы

Настройка осуществляется через файл `config.yaml` в секции `hybrid_stt`:

```yaml
hybrid_stt:
  whisper_url: "http://localhost:8000"  # URL локального сервиса
  remote_api_url: "https://api.example.com/stt"  # URL внешнего API
  min_confidence: 0.85  # Минимальный порог уверенности
  min_speaker_match: 0.90  # Минимальный порог соответствия голоса
  timeout_local: 5  # Таймаут для локального сервиса в секундах
  use_semantic_validation: false  # Использовать семантическую валидацию
  semantic_model: "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"  # Модель для семантического сравнения
  semantic_threshold: 0.75  # Минимальная семантическая близость для предпочтения локального результата
```

Также можно использовать переменные окружения:
```
WHISPER_HYBRID_STT_WHISPER_URL=http://localhost:8000
WHISPER_HYBRID_STT_REMOTE_API_URL=https://api.example.com/stt
WHISPER_HYBRID_STT_MIN_CONFIDENCE=0.85
WHISPER_HYBRID_STT_MIN_SPEAKER_MATCH=0.90
WHISPER_HYBRID_STT_TIMEOUT_LOCAL=5
WHISPER_HYBRID_STT_USE_SEMANTIC_VALIDATION=true
WHISPER_HYBRID_STT_SEMANTIC_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
WHISPER_HYBRID_STT_SEMANTIC_THRESHOLD=0.75
```

### Формат ответа

```json
{
  "source": "local",  // или "remote" в зависимости от источника
  "text": "распознанный текст",
  "metadata": {
    "confidence": 0.93,  // уверенность распознавания
    "speaker_match": 0.97,  // соответствие голосовому отпечатку (если применимо)
    "duration": 7.5,  // длительность аудио в секундах
    "language": "ru",  // определенный язык
    "fallback_used": false,  // был ли использован резервный метод
    "semantic_diff": 0.12  // семантическая разница между результатами (если применимо)
  }
}
```

### Семантическая валидация

При включенной семантической валидации используется модель `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` для сравнения семантической близости результатов локальной и внешней обработки. Это позволяет выбрать более качественный результат даже при близких показателях уверенности распознавания.

Для использования этой функции необходимо установить дополнительные зависимости:
```bash
pip install sentence-transformers
```

## API Endpoints

### GET `/health`
Проверка работоспособности сервиса.

### POST `/api/v1/voice/verify`
Проверка голоса и обработка команды.

**Пример запроса:**
```bash
curl -X POST \
  http://localhost:8000/api/v1/voice/verify \
  -H "X-API-Key: your-api-key" \
  -F "audio_file=@./command.wav"
```

### POST `/api/v1/voice/register`
Регистрация голосового отпечатка.

**Пример запроса:**
```bash
curl -X POST \
  http://localhost:8000/api/v1/voice/register \
  -H "X-API-Key: your-api-key" \
  -F "audio_files=@./sample1.wav" \
  -F "audio_files=@./sample2.wav" \
  -F "audio_files=@./sample3.wav"
```

### POST `/api/v1/hybrid/stt`
Распознавание речи с использованием гибридного подхода (локальное + внешнее API).

**Пример запроса:**
```bash
curl -X POST \
  http://localhost:8000/api/v1/hybrid/stt \
  -H "X-API-Key: your-api-key" \
  -F "audio_file=@./command.wav" \
  -F "verify_speaker=false" \
  -F "use_semantics=true" \
  -F "semantic_threshold=0.8" \
  -F "return_debug=true"
```

**Параметры:**
- `verify_speaker` - проверять ли голос на соответствие эталонному (по умолчанию false)
- `use_semantics` - использовать ли семантическую валидацию (по умолчанию false)
- `semantic_threshold` - порог семантической близости (0.0-1.0)
- `return_debug` - включать ли дополнительную отладочную информацию (по умолчанию false)

## Интеграция с языковыми моделями

Для интеграции с языковой моделью необходимо указать URL API и ключ в конфигурации:

```yaml
# config.yaml
llm:
  api_url: "http://your-llm-service/api/v1/process"
  api_key: "your-llm-api-key"
  timeout: 30
```

Или через переменные окружения:
```
WHISPER_LLM_API_URL=http://your-llm-service/api/v1/process
WHISPER_LLM_API_KEY=your-llm-api-key
```

## Конфигурация

Настройка сервиса осуществляется через файл `config.yaml` или переменные окружения:

| Параметр | Переменная окружения | Описание |
|----------|----------------------|----------|
| API ключ | WHISPER_API_KEY | Ключ для доступа к API |
| Порог верификации | WHISPER_AUTH_SPEAKER_VERIFICATION_THRESHOLD | Минимальный порог схожести голоса (0.0-1.0) |
| Модель Whisper | WHISPER_TRANSCRIPTION_WHISPER_MODEL | Размер модели (tiny, base, small, medium, large) |
| Язык | WHISPER_TRANSCRIPTION_LANGUAGE | Код языка или null для автоопределения |

## Работа с Docker

### Запуск с Docker Compose
```bash
docker-compose up -d
```

### Сборка образа
```bash
docker build -t whisper-voice-auth .
```

### Запуск контейнера
```bash
docker run -p 8000:8000 -v $(pwd)/storage:/app/storage whisper-voice-auth
```

## Устранение неполадок

### Проблемы с распознаванием речи

Для отладки распознавания речи без проверки голоса используйте:
```bash
./test_whisper.py your_audio_file.wav --model base
```

### Низкое качество верификации

1. Убедитесь, что образцы голоса записаны в тихом помещении
2. Используйте более длинные образцы (10+ секунд)
3. Настройте порог верификации в конфигурации

### Проблемы с FFmpeg

Убедитесь, что FFmpeg установлен и доступен в системе:
```bash
ffmpeg -version
```
