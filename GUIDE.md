# Whisper Voice Auth Microservice - Руководство

## Содержание
- [Установка](#установка)
- [Запись голосовых образцов](#запись-голосовых-образцов)
- [Регистрация голосового отпечатка](#регистрация-голосового-отпечатка)
- [Проверка авторизации голосом](#проверка-авторизации-голосом)
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
