# CLI Testing Utilities

Эта папка содержит утилиты командной строки для ручного тестирования различных компонентов микросервиса Whisper.

## Доступные утилиты

### test_client.py
Утилита для тестирования API клиента микросервиса.

**Функции:**
- Регистрация голосового отпечатка
- Верификация голоса
- Тестирование API endpoints

**Использование:**
```bash
# Регистрация голосового отпечатка
./cli_tests/test_client.py register samples/sample_1.wav samples/sample_2.wav samples/sample_3.wav

# Верификация голоса
./cli_tests/test_client.py verify test_commands/sample_1.wav
```

### test_whisper.py
Утилита для прямого тестирования модели Whisper без использования API.

**Функции:**
- Транскрипция аудиофайлов
- Тестирование различных моделей Whisper
- Проверка производительности

**Использование:**
```bash
# Транскрипция с моделью base
./cli_tests/test_whisper.py audio_file.wav --model base

# Транскрипция с указанием языка
./cli_tests/test_whisper.py audio_file.wav --model small --language ru
```

### test_llm.py
Утилита для тестирования интеграции с языковыми моделями (LLM).

**Функции:**
- Тестирование подключения к LLM API
- Проверка обработки команд
- Валидация ответов LLM

**Использование:**
```bash
# Тестирование LLM интеграции
./cli_tests/test_llm.py --text "включи свет в спальне"

# Тестирование с кастомным API
./cli_tests/test_llm.py --text "выключи музыку" --api-url "http://your-llm-api/process"
```

## Примечания

- Убедитесь, что микросервис запущен перед использованием test_client.py
- Для test_whisper.py требуется установка torch и whisper
- Для test_llm.py необходимо настроить переменные окружения или передать параметры API

## Связанные файлы

- [hybrid_stt.py](../hybrid_stt.py) - CLI для тестирования гибридной STT системы
- [record_samples.py](../record_samples.py) - Утилита для записи аудио образцов
