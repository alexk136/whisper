#!/bin/bash

# Скрипт для автоматического развертывания Whisper микросервиса
# Использование: ./scripts/deploy.sh [production|staging]

set -e  # Остановить выполнение при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для логирования
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Проверка аргументов
ENVIRONMENT=${1:-production}
PROJECT_DIR=${PROJECT_DIR:-$(pwd)}
COMPOSE_FILE=${COMPOSE_FILE:-docker-compose.yml}

if [ "$ENVIRONMENT" = "production" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
elif [ "$ENVIRONMENT" = "staging" ]; then
    COMPOSE_FILE="docker-compose.yml"
fi

log "🚀 Starting deployment for environment: $ENVIRONMENT"
log "📁 Project directory: $PROJECT_DIR"
log "🐳 Using compose file: $COMPOSE_FILE"

# Переход в директорию проекта
cd "$PROJECT_DIR"

# Проверка существования файла docker-compose
if [ ! -f "$COMPOSE_FILE" ]; then
    error "Docker compose file '$COMPOSE_FILE' not found!"
    exit 1
fi

# Создание директории для логов
mkdir -p logs

# Backup текущего состояния
log "📦 Creating backup of current state..."
if docker compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
    docker compose -f "$COMPOSE_FILE" logs --tail=100 > "logs/backup-$(date +%Y%m%d_%H%M%S).log" 2>/dev/null || true
    success "Backup created successfully"
else
    warning "No running containers found, skipping backup"
fi

# Обновление кода
log "📥 Updating code from Git..."
git fetch origin
CURRENT_BRANCH=$(git branch --show-current)
git reset --hard "origin/$CURRENT_BRANCH"
success "Code updated successfully"

# Обновление Docker образов
log "🐳 Pulling latest Docker images..."
docker compose -f "$COMPOSE_FILE" pull
success "Docker images updated"

# Остановка старых контейнеров (graceful shutdown)
log "⏸️ Stopping old containers..."
docker compose -f "$COMPOSE_FILE" down --remove-orphans
success "Old containers stopped"

# Запуск новых контейнеров
log "▶️ Starting new containers..."
docker compose -f "$COMPOSE_FILE" up -d
success "New containers started"

# Ожидание готовности сервисов
log "🏥 Waiting for services to be ready..."
sleep 15

# Проверка здоровья сервисов
log "🔍 Checking service health..."
if docker compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
    success "Services are running"
    docker compose -f "$COMPOSE_FILE" ps
else
    error "Some services failed to start!"
    docker compose -f "$COMPOSE_FILE" logs --tail=50
    exit 1
fi

# Тест API (если сервис доступен)
log "🧪 Testing API endpoint..."
sleep 5
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health | grep -q "200"; then
    success "API health check passed"
else
    warning "API health check failed - service might still be starting"
fi

# Очистка старых образов и контейнеров
log "🧹 Cleaning up old Docker resources..."
docker image prune -f
docker container prune -f
success "Cleanup completed"

# Финальная информация
log "📊 Deployment Summary:"
echo "================================="
echo "Environment: $ENVIRONMENT"
echo "Compose file: $COMPOSE_FILE"
echo "Git branch: $CURRENT_BRANCH"
echo "Git commit: $(git rev-parse --short HEAD)"
echo "Deployment time: $(date)"
echo "================================="

success "🎉 Deployment completed successfully!"

# Сохранение информации о развертывании
echo "$(date): Deployed $CURRENT_BRANCH ($(git rev-parse --short HEAD)) to $ENVIRONMENT" >> logs/deployment-history.log
