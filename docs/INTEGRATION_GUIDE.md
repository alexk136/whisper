# Руководство по интеграции Whisper с другими проектами

Данное руководство содержит информацию, необходимую для интеграции микросервиса Whisper с гибридной архитектурой (OpenAI Whisper API + локальный fallback) в другие проекты.

## Необходимая информация для интеграции

### 1. Интерфейс существующего механизма распознавания речи

#### Какой API/интерфейс использует текущий механизм распознавания речи?
Микросервис Whisper предоставляет REST API для распознавания речи с гибридной архитектурой. Основные эндпоинты:
- `/api/v1/hybrid/stt` - гибридное распознавание речи (OpenAI Whisper API → локальный fallback)
- `/api/v1/hybrid/translate` - перевод аудио с автоматической транскрипцией и переводом
- `/api/v1/voice/verify` - распознавание речи с верификацией говорящего
- `/health` - проверка состояния сервиса и статуса OpenAI API

#### Какие методы/функции вызываются для обработки аудио?
Основные внутренние функции для распознавания речи:
- `transcribe_audio_hybrid(audio_path, **kwargs)` - основной метод гибридной обработки аудио
- `transcribe_with_openai(audio_path, **kwargs)` - транскрипция через OpenAI Whisper API
- `translate_audio(audio_path, target_language, **kwargs)` - перевод аудио с транскрипцией
- `transcribe_audio(audio_path, detailed)` - локальное распознавание через Whisper (fallback)
- `chunk_large_audio(audio_path, chunk_size_mb)` - разбиение больших файлов на части

#### Какой формат входных и выходных данных ожидается?

**Входные данные:**
- Аудиофайлы в форматах WAV, MP3, OGG, FLAC, M4A
- Поддерживается отправка как файла, так и URL на аудиофайл
- Максимальный размер файла: 25 МБ (для OpenAI API), больше автоматически разбивается на части
- Дополнительные параметры: язык транскрипции, промпт, верификация говорящего, семантическая валидация

**Выходные данные (гибридная архитектура):**
```json
{
  "source": "openai",  // "openai", "local", или "fallback"
  "text": "распознанный текст",
  "metadata": {
    "confidence": 0.93,  // уверенность распознавания (для локальной модели)
    "speaker_match": 0.97,  // соответствие голосовому отпечатку (если применимо)
    "duration": 7.5,  // длительность аудио в секундах
    "language": "ru",  // определенный язык
    "fallback_used": false,  // был ли использован fallback на локальную модель
    "semantic_diff": 0.12,  // семантическая разница между результатами (если применимо)
    "chunks_processed": 1,  // количество обработанных фрагментов для больших файлов
    "model_used": "gpt-4o-transcribe",  // используемая модель
    "processing_time": 2.3  // время обработки в секундах
  },
  "debug": {  // только при return_debug=true
    "openai_response": {...},  // полный ответ от OpenAI API
    "chunk_details": [...],    // детали обработки фрагментов
    "fallback_reason": "api_timeout"  // причина fallback (если применимо)
  }
}
```

### 2. Архитектурные особенности проекта

#### Это монолитное приложение или микросервисная архитектура?
Whisper реализован как отдельный микросервис, который может быть интегрирован в более крупную микросервисную архитектуру или использоваться как самостоятельный сервис.

#### Какой язык программирования используется в проекте?
Проект написан на Python 3.12+ с использованием следующих основных технологий:
- FastAPI для REST API
- OpenAI Python SDK для интеграции с OpenAI Whisper API
- PyTorch и локальный OpenAI Whisper для fallback обработки
- SpeechBrain и Resemblyzer для верификации голоса
- Sentence-Transformers для семантической валидации (опционально)
- aiohttp для асинхронных HTTP запросов
- pydub для обработки и разбиения аудиофайлов

#### Какие механизмы обмена данными поддерживаются?
- REST API (основной метод взаимодействия)
- CLI-интерфейс для локального тестирования и интеграции через скрипты
- Возможность расширения для поддержки других протоколов (WebSockets, gRPC)

### 3. Требования к производительности

#### Нужна ли обработка в реальном времени или допустима асинхронная обработка?
Текущая реализация поддерживает асинхронную обработку аудиофайлов. Обработка в реальном времени (потоковая обработка аудио) не реализована напрямую, но может быть добавлена как расширение.

#### Какие ограничения по времени отклика?
- OpenAI Whisper API: в среднем 2-10 секунд на файл (зависит от размера и очереди)
- Локальное распознавание (fallback): в среднем 0.5-2 секунды на 10 секунд аудио (зависит от модели и наличия GPU)
- Гибридное распознавание: время OpenAI API + до 5 секунд fallback при необходимости
- Настраиваемые таймауты: OpenAI API (30 сек по умолчанию), локальная обработка (5 сек)
- Большие файлы (>25 МБ): автоматическое разбиение на фрагменты для параллельной обработки

#### Ожидаемая нагрузка (запросов в секунду/минуту)?
- OpenAI Whisper API: лимиты согласно тарифному плану OpenAI (обычно 50-500 RPM)
- Локальная обработка (fallback): На CPU до 10 запросов в минуту, на GPU до 60 запросов в минуту
- Гибридная архитектура позволяет масштабировать нагрузку через OpenAI при высоком трафике
- Масштабирование через развертывание нескольких инстансов с балансировкой нагрузки

### 4. Инфраструктурные детали

#### Где размещается проект?
Проект может быть развернут:
- Локально (для разработки и тестирования)
- На серверах компании (on-premise)
- В облачных средах (AWS, GCP, Azure)
- С использованием Docker и Kubernetes для оркестрации

#### Доступны ли GPU для ускорения распознавания речи?
Проект поддерживает как CPU, так и GPU для ускорения распознавания:
- Для GPU: поддержка CUDA через PyTorch
- В docker-compose.yml предусмотрена конфигурация для подключения GPU
- Автоматическое использование GPU, если он доступен

#### Есть ли ограничения по использованию памяти/дискового пространства?
- Память: 
  - Минимум 4 ГБ RAM для базовой работы с OpenAI API
  - Для локального fallback: 4-8 ГБ (модель base), 16+ ГБ (модель large)
  - Дополнительная память для обработки больших файлов (разбиение на фрагменты)
- Дисковое пространство: 
  - ~2-4 ГБ для локальных моделей Whisper и зависимостей
  - Временное хранение аудиофайлов и фрагментов
  - Дополнительное пространство для голосовых отпечатков (зависит от использования)
- Сетевой трафик: учитывать загрузку файлов в OpenAI API (до 25 МБ на запрос)

## Варианты интеграции

### 1. API-интеграция
Наиболее простой способ интеграции - использование REST API. Примеры запросов:

```bash
# Гибридное распознавание речи (OpenAI API + локальный fallback)
curl -X POST \
  http://whisper-service:8000/api/v1/hybrid/stt \
  -H "X-API-Key: your-api-key" \
  -F "audio_file=@./command.wav" \
  -F "language=ru" \
  -F "prompt=Это медицинская консультация" \
  -F "verify_speaker=false" \
  -F "use_semantics=true" \
  -F "semantic_threshold=0.8"

# Перевод аудио с транскрипцией
curl -X POST \
  http://whisper-service:8000/api/v1/hybrid/translate \
  -H "X-API-Key: your-api-key" \
  -F "audio_file=@./speech.wav" \
  -F "target_language=en" \
  -F "source_language=ru"

# Проверка состояния сервиса и OpenAI API
curl -X GET \
  http://whisper-service:8000/health
```

### 2. Библиотечная интеграция
Для более тесной интеграции можно использовать внутренние компоненты как библиотеку:

```python
from whisper.app.transcription.openai_whisper import transcribe_audio_hybrid, translate_audio
from whisper.app.transcription.speech_recognition import transcribe_audio
from whisper.app.audio.processor import process_audio_file
from pathlib import Path

async def recognize_speech_hybrid(audio_path, language="ru", prompt=None):
    """Гибридное распознавание с OpenAI API и локальным fallback"""
    processed_audio = await process_audio_file(Path(audio_path))
    result = await transcribe_audio_hybrid(
        audio_path=processed_audio,
        language=language,
        prompt=prompt,
        return_debug=True
    )
    return result

async def translate_speech(audio_path, target_language="en", source_language="ru"):
    """Перевод аудио с транскрипцией"""
    processed_audio = await process_audio_file(Path(audio_path))
    result = await translate_audio(
        audio_path=processed_audio,
        target_language=target_language,
        source_language=source_language
    )
    return result

async def recognize_speech_local_only(audio_path):
    """Только локальное распознавание (без OpenAI API)"""
    processed_audio = await process_audio_file(Path(audio_path))
    result = await transcribe_audio(
        audio_path=processed_audio,
        detailed=True
    )
    return result
```

### 3. Контейнерная интеграция
Интеграция через Docker и Docker Compose:

```yaml
# docker-compose.yml
services:
  your_service:
    # Конфигурация вашего сервиса
    depends_on:
      - whisper
  
  whisper:
    image: whisper-voice-auth
    # Конфигурация из docker-compose.yml проекта Whisper
```

## Контрольный список для интеграции

1. **Выбрать метод интеграции** (API, библиотека, контейнеры)
2. **Настроить конфигурацию** (`config.yaml`) под требования проекта
3. **Настроить OpenAI API**:
   - Получить API ключ OpenAI
   - Установить переменную окружения `OPENAI_API_KEY`
   - Выбрать модель (gpt-4o-transcribe, whisper-1)
   - Настроить таймауты и лимиты
4. **Настроить локальный fallback**:
   - Выбрать модель Whisper (tiny, base, small, medium, large)
   - Настроить GPU поддержку (если доступно)
   - Установить пороговые значения для fallback
5. **Обеспечить доступ к аудиофайлам** и настроить форматы
6. **Определить стратегию обработки ошибок** и fallback логику
7. **Настроить мониторинг и логирование**:
   - Мониторинг статуса OpenAI API
   - Логирование использования primary/fallback сервисов
   - Метрики производительности и cost tracking
8. **Провести тестирование**:
   - Тестирование с OpenAI API
   - Тестирование fallback сценариев
   - Нагрузочное тестирование
   - Интеграционное тестирование
9. **Настроить CI/CD** для автоматического развертывания
10. **Документировать интеграцию** и создать runbook для support team

## Контакты для поддержки

По вопросам интеграции и технической поддержки обращайтесь к команде разработки:
- Email: support@elrise.whisper.example.com
- Внутренний канал: #whisper-integration
