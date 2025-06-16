# Whisper - Voice Authentication and Analysis Microservice

## Обзор
Whisper - это микросервис, который обеспечивает аутентификацию по голосу и распознавание речи. Он проверяет идентичность говорящего, сравнивая голос с сохраненным голосовым отпечатком, и обрабатывает голосовые команды соответствующим образом.

## Функциональность
- Верификация голоса с использованием сохраненных голосовых отпечатков
- Распознавание речи с использованием модели OpenAI Whisper или других моделей
- Обработка команд на основе авторизации
- Интеграция с сервисами языковых моделей (LLM)
- Поддержка различных аудиоформатов
- Гибридная система распознавания речи с автоматическим переключением между локальной и внешней обработкой

## Рабочий процесс
1. **Запись голосовых образцов**: Пользователь записывает образцы своего голоса
2. **Регистрация голосового отпечатка**: Система создает уникальный голосовой отпечаток
3. **Авторизация по голосу**: Когда пользователь отправляет аудиокоманду, система:
   - Проверяет соответствие голоса с эталонным образцом
   - Распознает речь и преобразует в текст
   - Если голос авторизован - обрабатывает команду и передает в LLM
   - Если голос не авторизован - возвращает ограниченную информацию

## Подробные инструкции

### Установка

#### Быстрый старт (рекомендуется)
```bash
# Клонировать репозиторий
git clone https://github.com/username/whisper.git
cd whisper

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

#### Верификация голоса
```bash
curl -X POST \
  http://localhost:8000/api/v1/voice/verify \
  -H "X-API-Key: your-api-key" \
  -F "audio_file=@./command.wav"
```

#### Гибридное распознавание речи
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

#### Ответ API (стандартный)
```json
{
  "status": "AUTHORIZED",
  "text": "включи свет в спальне",
  "metadata": {
    "confidence": 0.93,
    "speaker_match": 0.97,
    "duration": 7.5,
    "language": "ru"
  }
}
```

#### Ответ API (гибридный)
```json
{
  "source": "local",
  "text": "включи свет в спальне",
  "metadata": {
    "confidence": 0.93,
    "speaker_match": 0.97,
    "duration": 7.5,
    "language": "ru",
    "fallback_used": false,
    "semantic_diff": null
  }
}
```

## Дополнительная документация

Более подробные инструкции доступны в [руководстве пользователя](docs/GUIDE.md), которое включает:

- Детальное описание API endpoints
- Варианты конфигурации
- Инструкции по интеграции с языковыми моделями
- Решение проблем и отладка
- Примеры использования различных скриптов

Для информации об интеграции микросервиса с другими проектами см. [руководство по интеграции](docs/INTEGRATION_GUIDE.md).

Для ручного тестирования компонентов используйте [CLI-утилиты](cli_tests/README.md).

## Требования
- Python 3.12+
- FFmpeg
- Docker (для контейнеризованного развертывания)
- Поддержка GPU (опционально, для более быстрой обработки)

## Лицензия
[MIT License](LICENSE)