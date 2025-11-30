#!/bin/bash
echo "🔄 Обновление системы..."
sudo apt update && sudo apt upgrade -y
echo "🐳 Установка Docker..."
sudo apt install docker.io -y
sudo usermod -aG docker $USER
echo "📁 Копирование файлов проекта..."
docker build -t deadline-bot .
docker run -d -p 80:8000 --name deadline-container deadline-bot
echo "✅ Деплой завершен! Приложение доступно по http://IP_СЕРВЕРА"
