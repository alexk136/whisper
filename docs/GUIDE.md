# Whisper Voice Auth Microservice - Руководство пользователя

## Содержание
- [Обзор системы](#обзор-системы)
- [Установка](#установка)
- [Конфигурация](#конфигурация)
- [API Endpoints](#api-endpoints)
- [Гибридное распознавание речи](#гибридное-распознавание-речи)
- [Голосовая аутентификация](#голосовая-аутентификация)
- [CLI интерфейс](#cli-интерфейс)
- [Работа с Docker](#работа-с-docker)
- [Мониторинг и отладка](#мониторинг-и-отладка)
- [Устранение неполадок](#устранение-неполадок)

## Обзор системы

Whisper Voice Auth Microservice - это гибридная система распознавания речи с поддержкой голосовой аутентификации. Ключевые особенности:

### 🚀 Гибридная архитектура STT
- **Основной сервис**: OpenAI Whisper API (gpt-4o-audio)
- **Резервный сервис**: Локальный Whisper (whisper-large-v3)
- **Автоматический fallback**: При недоступности или ошибках OpenAI API

### 🔐 Голосовая аутентификация
- Создание уникальных голосовых отпечатков
- Верификация личности по голосу
- Зашифрованное хранение биометрических данных

### 🎯 Высокое качество
- Semantic validation результатов
- Поддержка 99+ языков
- Контекстные подсказки для улучшения точности

### ⚡ Производительность
- Быстрая обработка через OpenAI API (~2-5 сек)
- Надежный fallback для больших файлов
- Concurrent processing до 10 запросов

## Установка

### Быстрый старт
```bash
# Клонирование репозитория
git clone <repository-url>
cd whisper

# Автоматическая установка
./setup.sh

# Запуск сервиса
make run
```

### Детальная установка

#### 1. Системные требования
- Python 3.12+
- FFmpeg (для обработки аудио)
- 4GB+ RAM (для локального whisper)
- CUDA (опционально, для GPU ускорения)

#### 2. Создание окружения
```bash
# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt
```

#### 3. Конфигурация окружения
```bash
# Копирование примера конфигурации
cp .env.sample .env

# Генерация ключей безопасности
python generate_key.py

# Создание директорий
mkdir -p storage/audio storage/voiceprints
```

#### 4. Настройка OpenAI API (рекомендуется)
```bash
# Добавьте в .env файл
echo "OPENAI_API_KEY=your_openai_api_key_here" >> .env
```

## Конфигурация

### Environment Variables

#### Обязательные переменные
```bash
# Безопасность
WHISPER_API_KEY=your_secure_api_key
ENCRYPTION_KEY=your_encryption_key

# OpenAI Configuration (рекомендуется)
OPENAI_API_KEY=your_openai_api_key
```

#### Опциональные переменные
```bash
# Сервис STT
WHISPER_PRIMARY_SERVICE=openai          # "openai" или "local"
WHISPER_FALLBACK_TO_LOCAL=true          # Включить fallback

# Производительность
WHISPER_MAX_WORKERS=4                   # Concurrent workers
WHISPER_CHUNK_SIZE_MB=10               # Размер chunks

# Semantic validation
WHISPER_HYBRID_STT_USE_SEMANTIC_VALIDATION=false
WHISPER_HYBRID_STT_SEMANTIC_THRESHOLD=0.8
```

### Config.yaml
```yaml
# Основные настройки
primary_service: "openai"
fallback_to_local: true

# OpenAI Whisper API
openai:
  api_key: "${OPENAI_API_KEY}"
  model: "whisper-1"
  max_file_size_mb: 25
  timeout_seconds: 30
  max_retries: 3

# Локальный Whisper
local_whisper:
  model: "large-v3"
  device: "auto"
  compute_type: "float16"

# Семантическая валидация
semantic:
  model: "sentence-transformers/all-MiniLM-L6-v2"
  threshold: 0.8
  enabled: false
```

## API Endpoints

### Базовый URL
```
http://localhost:8000
```

### Аутентификация
Все API запросы требуют заголовок:
```
X-API-Key: your_api_key_here
```

### 1. Гибридная транскрипция - `/api/v1/hybrid/stt`

Основной endpoint для распознавания речи с автоматическим fallback.

#### Метод: POST

#### Параметры:
- `audio_file` (file, required) - Аудиофайл (WAV, MP3, OGG, FLAC, M4A)
- `language` (string, optional) - Код языка (например, "ru", "en")
- `prompt` (string, optional) - Контекстная подсказка
- `verify_speaker` (boolean, optional) - Включить верификацию говорящего
- `user_id` (string, optional) - ID пользователя для верификации
- `use_semantics` (boolean, optional) - Включить семантическую валидацию

#### Пример запроса:
```bash
curl -X POST "http://localhost:8000/api/v1/hybrid/stt" \
  -H "X-API-Key: your_api_key" \
  -F "audio_file=@audio.wav" \
  -F "language=ru" \
  -F "prompt=Это медицинская консультация" \
  -F "verify_speaker=true" \
  -F "user_id=user123"
```

#### Ответ:
```json
{
  "source": "openai",
  "text": "Здравствуйте, у меня болит голова",
  "metadata": {
    "confidence": 0.95,
    "language": "ru",
    "duration": 3.2,
    "speaker_match": 0.87,
    "fallback_used": false,
    "semantic_diff": null,
    "service_used": "openai"
  }
}
```

### 2. Перевод аудио - `/api/v1/hybrid/translate`

Транскрипция с переводом на английский язык.

#### Метод: POST

#### Параметры:
- `audio_file` (file, required) - Аудиофайл
- `prompt` (string, optional) - Контекстная подсказка

#### Пример запроса:
```bash
curl -X POST "http://localhost:8000/api/v1/hybrid/translate" \
  -H "X-API-Key: your_api_key" \
  -F "audio_file=@audio_ru.wav" \
  -F "prompt=Medical consultation"
```

#### Ответ:
```json
{
  "source": "openai",
  "text": "Hello, I have a headache",
  "original_language": "ru",
  "metadata": {
    "confidence": 0.92,
    "duration": 3.2,
    "fallback_used": false
  }
}
```

### 3. Верификация голоса - `/api/v1/voice/verify`

Распознавание речи с обязательной верификацией говорящего.

#### Метод: POST

#### Параметры:
- `audio_file` (file, required) - Аудиофайл
- `user_id` (string, required) - ID пользователя
- `language` (string, optional) - Код языка

#### Ответ:
```json
{
  "text": "Привет, это я",
  "speaker_verified": true,
  "confidence": 0.94,
  "speaker_similarity": 0.89,
  "metadata": {
    "language": "ru",
    "duration": 2.1
  }
}
```

### 4. Регистрация голосового отпечатка - `/api/v1/voice/register`

#### Метод: POST

#### Параметры:
- `audio_file` (file, required) - Аудиофайл для регистрации
- `user_id` (string, required) - ID пользователя

### 5. Health Check - `/health`

Проверка состояния системы и доступности сервисов.

#### Метод: GET

#### Ответ:
```json
{
  "status": "healthy",
  "timestamp": "2025-06-16T12:00:00Z",
  "components": {
    "api": "ready",
    "local_whisper": "ready",
    "openai": "ready",
    "hybrid_stt": "ready"
  },
  "services": {
    "primary_stt": "openai",
    "fallback_available": true,
    "voice_auth": "enabled"
  }
}
```

## Гибридное распознавание речи

### Логика работы

1. **Проверка размера файла**
   - Файлы ≤ 25MB отправляются в OpenAI API
   - Большие файлы обрабатываются локально

2. **Попытка основного сервиса (OpenAI)**
   - Быстрая обработка (~2-5 сек)
   - Высокое качество
   - Автоопределение языка

3. **Fallback при ошибках**
   - Недоступность OpenAI API
   - Превышение лимитов
   - Ошибки обработки

4. **Локальная обработка**
   - Whisper large-v3 модель
   - Полная приватность
   - Поддержка больших файлов

### Управление режимами

#### Только OpenAI API
```bash
export WHISPER_PRIMARY_SERVICE=openai
export WHISPER_FALLBACK_TO_LOCAL=false
```

#### Только локальный Whisper
```bash
export WHISPER_PRIMARY_SERVICE=local
```

#### Гибридный режим (рекомендуется)
```bash
export WHISPER_PRIMARY_SERVICE=openai
export WHISPER_FALLBACK_TO_LOCAL=true
```

### Семантическая валидация

Опциональная функция для сравнения результатов разных STT сервисов:

```bash
export WHISPER_HYBRID_STT_USE_SEMANTIC_VALIDATION=true
export WHISPER_HYBRID_STT_SEMANTIC_THRESHOLD=0.8
```

При включении система:
1. Получает результат от основного сервиса
2. Получает результат от fallback сервиса
3. Сравнивает semantic similarity
4. При низкой схожести помечает результат как потенциально некорректный

## Голосовая аутентификация

### Запись голосовых образцов

Для регистрации голосового отпечатка нужно записать образцы голоса:

```bash
# Интерактивная запись
python record_samples.py --samples 3 --duration 10

# Или используйте существующие аудиофайлы
python record_samples.py --from-files sample1.wav sample2.wav sample3.wav
```

### Регистрация пользователя

```bash
# Через API
curl -X POST "http://localhost:8000/api/v1/voice/register" \
  -H "X-API-Key: your_api_key" \
  -F "audio_file=@voice_sample.wav" \
  -F "user_id=user123"

# Через CLI
python voice_auth.py register --user-id user123 --audio voice_sample.wav
```

### Верификация голоса

```bash
# В составе транскрипции
curl -X POST "http://localhost:8000/api/v1/hybrid/stt" \
  -H "X-API-Key: your_api_key" \
  -F "audio_file=@test_audio.wav" \
  -F "verify_speaker=true" \
  -F "user_id=user123"

# Только верификация
curl -X POST "http://localhost:8000/api/v1/voice/verify" \
  -H "X-API-Key: your_api_key" \
  -F "audio_file=@test_audio.wav" \
  -F "user_id=user123"
```

### Безопасность голосовых отпечатков

- **Шифрование**: Все отпечатки зашифрованы AES-256
- **Хеширование**: ID пользователей хешируются
- **Локальное хранение**: Данные не покидают ваш сервер
- **Удаление**: Возможность удаления отпечатков

## CLI интерфейс

### Hybrid STT CLI

Командная строка для тестирования и автоматизации:

```bash
# Базовая транскрипция
python hybrid_stt.py --file audio.wav

# С параметрами
python hybrid_stt.py \
  --file audio.wav \
  --verify_speaker \
  --use_semantics \
  --semantic_threshold 0.8

# Справка
python hybrid_stt.py --help
```

#### Параметры CLI:
- `--file` - Путь к аудиофайлу (обязательно)
- `--verify_speaker` - Включить верификацию говорящего
- `--use_semantics` - Включить семантическую валидацию
- `--semantic_threshold` - Порог семантической схожести (0.0-1.0)

#### Пример вывода:
```
Processing audio file: audio.wav
Options: verify_speaker=True, use_semantics=True

=== Hybrid STT Results ===
Source: openai
Text: Привет, как дела?

Metadata:
  confidence: 0.95
  duration: 2.3
  language: ru
  fallback_used: False
  speaker_match: 0.87
  semantic_diff: 0.05

JSON Response:
{
  "source": "openai",
  "text": "Привет, как дела?",
  "metadata": {
    "confidence": 0.95,
    "speaker_match": 0.87,
    "duration": 2.3,
    "language": "ru",
    "fallback_used": false,
    "semantic_diff": 0.05
  }
}
```

### Batch Processing

```bash
# Обработка нескольких файлов
for file in *.wav; do
  python hybrid_stt.py --file "$file" >> results.txt
done

# Или с помощью скрипта
python batch_process.py --input-dir ./audio_files --output results.json
```

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
docker compose up -d
```

### Сборка образа
```bash
docker build -t whisper .
```

### Запуск контейнера
```bash
docker run -p 8000:8000 -v $(pwd)/storage:/app/storage whisper
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
