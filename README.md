# Bookcrossing Styled

Веб-приложение буккроссинга на **FastAPI + PostgreSQL**.

- HTML-шаблоны: `src/templates`
- API и backend-логика: `src/api`
- Миграции: Alembic (`src/migrations`)
- Изображения книг: Cloudinary (`CLOUDINARY_URL`)

## Возможности

- Каталог книг с фильтрами и пагинацией
- Профиль пользователя и личные записи
- Админ-панель (заявки, записи БД, статистика)
- Загрузка изображений книг
- Светлая/тёмная тема и адаптация под мобильные устройства

## Стек

- Python 3.11
- FastAPI
- SQLAlchemy + asyncpg
- Alembic
- PostgreSQL
- Uvicorn

## Структура проекта

```text
src/
  api/             # роуты FastAPI
  models/          # ORM-модели
  repositories/    # доступ к данным
  services/        # бизнес-логика
  templates/       # HTML-шаблоны
  static/          # общие стили и JS
  imgs/            # старые локальные изображения / fallback
  migrations/      # Alembic-миграции
```

## Локальный запуск (без Docker)

### 1) Установить зависимости

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2) Настроить `.env`

Пример переменных:

```env
DB_NAME=bookcrossing
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASS=root

JWT_SECRET_KEY=change_me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24

SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=mailer@example.com
SMTP_PASS=change_me
SMTP_FROM=mailer@example.com
SMTP_STARTTLS=true
SMTP_SSL=false

CLOUDINARY_URL=cloudinary://your_api_key:your_api_secret@your_cloud_name
CLOUDINARY_UPLOAD_FOLDER=bookcrossing/books
```

### 3) Применить миграции

```bash
alembic upgrade head
```

### 4) Запустить сервер

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Открыть: [http://localhost:8000](http://localhost:8000)

## Запуск через Docker Compose (одной командой)

### 1) Подготовить env

```bash
cp .env.docker.example .env
```

### 2) Запуск

```bash
docker compose up --build
```

Сервисы:

- `backend` — FastAPI
- `db` — PostgreSQL

Доступ:

- Приложение: [http://localhost:8000](http://localhost:8000)
- PostgreSQL с хоста: `localhost:6432`

### 3) Остановка

```bash
docker compose down
```

Полная очистка с volume БД:

```bash
docker compose down -v
```

## Подключение к PostgreSQL (например, DBeaver)

- Host: `localhost`
- Port: `6432`
- Database: `bookcrossing` (или `DB_NAME`)
- Username: `postgres` (или `DB_USER`)
- Password: `root` (или `DB_PASS`)
- SSL: disable

## Загрузка изображений и статика

- Новые загружаемые картинки отправляются в Cloudinary.
- В базе данных в поле `book.image` сохраняется полный `https://...` URL.
- Папка `src/imgs` оставлена для старых локальных изображений и fallback-статики.
- Статика приложения отдаётся через `/static`.

## Полезные команды

```bash
# Создать миграцию
alembic revision --autogenerate -m "message"

# Применить миграции
alembic upgrade head

# Откатить миграцию
alembic downgrade -1
```
