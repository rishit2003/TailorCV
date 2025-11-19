# Infrastructure Configuration Files

This directory contains configuration files for infrastructure services and application settings.

## Purpose

Store **non-secret** configuration files here:
- Service configuration templates
- Logging configurations
- Database initialization scripts
- Message queue settings
- Nginx/reverse proxy configs

## Important Notes

⚠️ **DO NOT store secrets here!**
- API keys → use `.env` file in root
- Passwords → use `.env` file in root
- Tokens → use `.env` file in root

✅ **Safe to store:**
- Logging formats and levels (templates)
- Service discovery configurations
- Database schema initialization scripts
- Default settings and templates

## Files in This Directory

- `logging-config.yaml` - Logging configuration for all services
- `mongodb-init.js` - MongoDB initialization script (collections, indexes)
- `rabbitmq-config.json` - RabbitMQ exchange and queue configurations

## Usage

These files are referenced by:
1. `docker-compose.yml` - Mounted as volumes into containers
2. Service code - Loaded during application startup
3. CI/CD pipelines - For deployment configurations

