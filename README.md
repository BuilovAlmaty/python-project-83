# Page Analyzer

Веб-приложение для анализа веб-страниц: проверка доступности страницы и извлечение SEO-параметров (title, h1, description).

Проект написан на Flask, использует PostgreSQL и менеджер зависимостей uv.

## Требования

Перед установкой убедитесь, что у вас установлены:

Python >= 3.12

PostgreSQL >= 13

uv
```bash
pip install uv
```

## Установка
### Клонирование репозитория
```bash
git clone https://github.com/<ваш-username>/python-project-83.git
cd python-project-83
```
### Установка зависимостей
```bash
make install
```

### Настройка переменных окружения

Создайте файл .env в корне проекта:
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/page_analyzer
SECRET_KEY=your_secret_key
```
Замените ```user```, ```password``` и имя базы данных на свои значения.

## Запуск приложения
### Запуск 
```bash
make start
```
### Запуск в режиме разработки
```bash
make dev
```


### Hexlet tests and linter status:
[![Actions Status](https://github.com/BuilovAlmaty/python-project-83/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/BuilovAlmaty/python-project-83/actions)

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=BuilovAlmaty_python-project-83&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=BuilovAlmaty_python-project-83)
[![Quality gate](https://sonarcloud.io/api/project_badges/quality_gate?project=BuilovAlmaty_python-project-83)](https://sonarcloud.io/summary/new_code?id=BuilovAlmaty_python-project-83)
## url:
https://python-project-83-4ei7.onrender.com/
