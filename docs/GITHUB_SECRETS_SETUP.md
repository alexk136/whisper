# GitHub Secrets Configuration

# This file contains examples of GitHub secrets that need to be configured
# for the CI/CD pipeline to work properly.

# REQUIRED SECRETS
# ================

# Server connection details
SERVER_HOST=your-server-ip-or-domain.com
SERVER_USER=deploy-user
SERVER_PORT=22

# SSH private key for deployment (contents of private key file)
CI_SSH_KEY=|
  -----BEGIN OPENSSH PRIVATE KEY-----
  b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAlwAAAAdzc2gtcn
  ... (your actual private key content) ...
  -----END OPENSSH PRIVATE KEY-----

# OPTIONAL SECRETS
# ===============

# Project path on server (default: /home/user/whisper)
PROJECT_PATH=/opt/whisper-microservice

# Docker registry credentials (if using private registry)
DOCKER_USERNAME=your-docker-username
DOCKER_PASSWORD=your-docker-password
DOCKER_REGISTRY=your-registry.com

# Notification webhooks (optional)
SLACK_WEBHOOK=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX
TELEGRAM_BOT_TOKEN=1234567890:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
TELEGRAM_CHAT_ID=-1001234567890

# Environment specific variables
DATABASE_URL=postgresql://user:password@localhost:5432/whisper_prod
REDIS_URL=redis://localhost:6379/0
API_KEY=your-super-secret-api-key

# Monitoring and alerting
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
NEWRELIC_LICENSE_KEY=your-newrelic-license-key

# HOW TO SET SECRETS IN GITHUB
# ============================

# 1. Go to your GitHub repository
# 2. Navigate to Settings → Secrets and variables → Actions
# 3. Click "New repository secret"
# 4. Add each secret name and value from above
# 5. Make sure secret names match exactly what's used in workflows

# EXAMPLE: Setting up SSH key
# ==========================

# 1. Generate SSH key pair on your local machine:
#    ssh-keygen -t ed25519 -C "ci-cd@whisper-microservice" -f ~/.ssh/whisper_deploy_key

# 2. Add public key to server:
#    ssh-copy-id -i ~/.ssh/whisper_deploy_key.pub deploy-user@your-server.com

# 3. Add private key to GitHub secrets:
#    - Secret name: CI_SSH_KEY
#    - Secret value: Contents of ~/.ssh/whisper_deploy_key file

# 4. Test SSH connection:
#    ssh -i ~/.ssh/whisper_deploy_key deploy-user@your-server.com

# SERVER SETUP COMMANDS
# ====================

# Run these commands on your server to prepare for CI/CD:

# Create deploy user (run as root)
# useradd -m -s /bin/bash deploy-user
# usermod -aG docker deploy-user
# su - deploy-user

# Create project directory
# mkdir -p /opt/whisper-microservice/{logs,storage,models,data}
# cd /opt/whisper-microservice

# Clone repository (first time)
# git clone https://github.com/your-org/whisper-microservice.git .

# Set up environment
# cp .env.prod.sample .env
# nano .env  # Edit configuration

# Create docker network (if needed)
# docker network create whisper-net

# SECURITY NOTES
# ==============

# 1. Never commit this file to git with real values
# 2. Use separate SSH keys for CI/CD (not your personal keys)
# 3. Limit server access for CI/CD user
# 4. Regularly rotate secrets
# 5. Use least privilege principle
# 6. Enable 2FA on GitHub account
# 7. Monitor access logs

# VALIDATION COMMANDS
# ==================

# Test secrets from GitHub Actions (add to workflow for debugging):
# - name: Test Secrets
#   run: |
#     echo "Server: ${{ secrets.SERVER_HOST }}"
#     echo "User: ${{ secrets.SERVER_USER }}"
#     echo "SSH key length: ${#CI_SSH_KEY}"
#     ssh -o StrictHostKeyChecking=no -i <(echo "${{ secrets.CI_SSH_KEY }}") ${{ secrets.SERVER_USER }}@${{ secrets.SERVER_HOST }} "echo 'SSH connection successful'"
