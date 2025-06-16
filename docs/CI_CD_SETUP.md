# CI/CD Setup для Whisper Microservice

## Обзор

Проект настроен для автоматического развертывания с использованием GitHub Actions, SSH и docker-compose. Система обеспечивает нулевое время простоя и сохранение состояния контейнеров. Поддерживает гибридную архитекту## Security Considerations

1. **SSH Keys**: Используйте отдельные ключи для CI/CD (не ваши персональные ключи)
2. **Secrets**: Никогда не храните секреты в коде (особенно OPENAI_API_KEY)
3. **Server Access**: Ограничьте доступ только для CI/CD пользователя
4. **Network**: Используйте VPN или firewall для доступа к серверу
5. **Docker**: Регулярно обновляйте базовые образы
6. **API Keys**: Регулярно ротируйте OpenAI API ключи
7. **Monitoring**: Мониторьте использование API и потенциальные атаки
8. **Audit**: Ведите логи всех deployment операцийenAI Whisper API как основным сервисом и локальным Whisper как fallback.

## Архитектура CI/CD

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Developer     │    │   GitHub Actions │    │   Server        │
│                 │    │                  │    │                 │
│ git push main   │───▶│ 1. Run Tests     │───▶│ 1. Pull Code    │
│                 │    │ 2. Build Check   │    │ 2. Pull Images  │
│                 │    │ 3. SSH Deploy    │    │ 3. Restart      │
│                 │    │ 4. Test Health   │    │ 4. Verify APIs  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Компоненты

### 1. GitHub Actions Workflows

#### `.github/workflows/deploy.yml`
- **Триггер**: Push в ветку `main`
- **Задачи**:
  - Запуск тестов
  - Развертывание через SSH
  - Уведомления о статусе
- **Требования**: Настроенные секреты в GitHub

#### `.github/workflows/test.yml`
- **Триггер**: Pull Request в `main`
- **Задачи**:
  - Запуск тестов (включая мок-тестирование OpenAI интеграции)
  - Проверка форматирования кода
  - Сборка Docker образа
  - Проверка работоспособности образа
  - Тестирование гибридной архитектуры
  - Валидация конфигурации OpenAI

### 2. Server-side Script

#### `scripts/deploy.sh`
- Универсальный скрипт для развертывания
- Поддержка production и staging окружений
- Автоматическое резервное копирование
- Проверка здоровья сервисов
- Очистка старых образов

## Настройка

### 1. GitHub Secrets

Необходимо настроить следующие секреты в GitHub репозитории:

```bash
# Обязательные секреты для развертывания
SERVER_HOST=your-server-ip-or-domain
SERVER_USER=your-ssh-username
CI_SSH_KEY=your-private-ssh-key

# Обязательные секреты для OpenAI интеграции
OPENAI_API_KEY=sk-your-openai-api-key

# Опциональные секреты
SERVER_PORT=22                      # По умолчанию 22
PROJECT_PATH=/home/deploy/whisper   # По умолчанию /home/deploy/whisper

# Дополнительные API ключи (если используются)
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
SLACK_WEBHOOK_URL=your-slack-webhook-url
```

### 2. SSH Key Setup

```bash
# На локальной машине или в GitHub Actions
ssh-keygen -t ed25519 -C "ci-cd@whisper-microservice"

# Добавить публичный ключ на сервер
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@your-server

# Добавить приватный ключ в GitHub Secrets как CI_SSH_KEY
cat ~/.ssh/id_ed25519
```

### 3. Server Preparation

```bash
# На сервере создать структуру проекта
mkdir -p /home/deploy/whisper/{logs,storage,data}
cd /home/deploy/whisper

# Клонировать репозиторий
git clone https://github.com/your-org/whisper.git .

# Настроить переменные окружения
cp .env.prod.sample .env
# Отредактировать .env файл, особенно:
# OPENAI_API_KEY=sk-your-openai-api-key
# PRIMARY_SERVICE=openai
# FALLBACK_TO_LOCAL=true

# Первый запуск
docker-compose up -d

# Проверить состояние сервисов
docker-compose ps
curl http://localhost:8000/health
```

### 4. Docker Compose Configuration

Убедитесь, что в `docker-compose.yml` и `docker-compose.prod.yml` настроены:

- **Volumes**: Для сохранения данных между перезапусками
- **Networks**: Для коммуникации между сервисами
- **Health checks**: Для проверки состояния сервисов
- **Restart policies**: Для автоматического восстановления

```yaml
services:
  whisper-api:
    # ... другие настройки
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PRIMARY_SERVICE=openai
      - FALLBACK_TO_LOCAL=true
    volumes:
      - ./storage:/app/storage
      - ./logs:/app/logs
      - ./models:/app/models
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s  # Дополнительное время для загрузки моделей
```

## Workflow Process

### 1. Feature Development
```bash
# Создание feature ветки
git checkout -b feature/new-feature
# ... разработка
git add .
git commit -m "feat: Add new feature"
git push origin feature/new-feature
```

### 2. Pull Request
- Создание PR в main
- Автоматический запуск `test.yml`
- Проверка тестов и Docker сборки
- Code review

### 3. Deployment
```bash
# Merge PR или direct push в main
git checkout main
git merge feature/new-feature
git push origin main
```

Автоматически запускается:
1. **Tests**: Проверка всех тестов (включая OpenAI интеграцию)
2. **Deploy**: SSH подключение к серверу
3. **Server Actions**:
   - Backup текущего состояния
   - Pull latest code
   - Update environment variables (OPENAI_API_KEY)
   - Pull Docker images
   - Restart services with zero downtime
   - Health check (включая проверку OpenAI API статуса)
   - Cleanup old images
4. **Validation**: Проверка доступности API эндпоинтов
5. **Notifications**: Уведомления о статусе

## Troubleshooting

### 1. SSH Connection Issues
```bash
# Проверка подключения
ssh -T git@github.com

# Проверка SSH ключей на сервере
cat ~/.ssh/authorized_keys

# Проверка SSH агента
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

### 2. Docker Issues
```bash
# Проверка статуса контейнеров
docker-compose ps

# Просмотр логов
docker-compose logs -f

# Проверка переменных окружения
docker-compose exec whisper-api env | grep OPENAI

# Полная пересборка
docker-compose down
docker-compose up -d --build --force-recreate

# Проверка health endpoint
curl http://localhost:8000/health
```

### 3. Deployment Issues
```bash
# Ручной запуск скрипта развертывания
./scripts/deploy.sh production

# Проверка GitHub Actions логов
# Перейти в GitHub → Actions → View workflow run
```

## Мониторинг

### 1. Health Checks
- Встроенные health checks в Docker
- Проверка доступности API эндпоинтов
- Мониторинг статуса OpenAI API connectivity
- Проверка fallback механизмов
- Мониторинг логов приложения

### 2. Logs Management
```bash
# Просмотр логов deployment
ls -la logs/deployment-*.log

# Просмотр логов приложения
docker-compose logs -f --tail=100

# Просмотр логов OpenAI API запросов
docker-compose logs whisper-api | grep -i openai

# Просмотр логов fallback активации
docker-compose logs whisper-api | grep -i fallback
```

### 3. Notifications (Опционально)

Можно добавить уведомления в:
- Slack
- Telegram
- Email
- Discord

Пример для Slack:
```yaml
- name: Notify Slack
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

## Security Considerations

1. **SSH Keys**: Используйте отдельные ключи для CI/CD
2. **Secrets**: Никогда не храните секреты в коде
3. **Server Access**: Ограничьте доступ только для CI/CD пользователя
4. **Network**: Используйте VPN или firewall для доступа к серверу
5. **Docker**: Регулярно обновляйте базовые образы

## Best Practices

1. **Feature Branches**: Всегда работайте в feature ветках
2. **Testing**: Все изменения должны проходить тесты
3. **Code Review**: Используйте PR для code review
4. **Rollback**: Держите готовый план отката
5. **Monitoring**: Следите за метриками после развертывания
6. **Backup**: Регулярно создавайте бэкапы данных

## Расширение

### 1. Multi-Environment Setup
- Добавление staging окружения
- Настройка dev/test/prod pipeline
- Environment-specific configurations

### 2. Advanced Monitoring
- Prometheus + Grafana
- ELK Stack для логов
- Alerting система

### 3. Container Orchestration
- Kubernetes deployment
- Docker Swarm
- Service mesh (Istio)
