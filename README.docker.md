# Docker run

## 1. Prepare env

Create env file from example:

```bash
cp .env.docker.example .env
```

Adjust values if needed.

## 2. Run project

```bash
docker compose up --build
```

App will be available at:

- http://localhost:8000

## Notes

- Two containers are used:
  - `db` (PostgreSQL)
  - `backend` (FastAPI serving both backend and HTML/templates/static)
- DB migrations are applied automatically on backend start (`alembic upgrade head`).
- New uploaded images are sent to Cloudinary via `CLOUDINARY_URL`.
- The local bind mount `./src/imgs -> /app/src/imgs` is kept only for old local images and fallback static files.

## Stop

```bash
docker compose down
```

To also remove DB data volume:

```bash
docker compose down -v
```
