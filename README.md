# High-Traffic Lead Capture Platform

Full-stack reference implementation for a lightning-fast landing page that captures mobile numbers, validates them, and processes each submission asynchronously with Django, Celery, Redis, PostgreSQL, and MongoDB logging. The React front end delivers the supplied hero/CTA experience with <100 ms perceived feedback.

## Stack Overview

- **Backend**: Django 5, Celery 5, Redis cache/broker, PostgreSQL for durable leads, MongoDB for structured request logs.
- **Frontend**: React 18 + Vite + TailwindCSS with lucide-react icons.
- **Ops**: Docker multi-stage build (Node + Python) plus docker-compose services for web, Celery worker, Nginx edge, Postgres, Redis, and Mongo.

## Project Layout

```
backend/        # Django project (settings, leads app, Celery config)
frontend/       # Vite React app (Tailwind UI, API wiring)
docker/         # runtime scripts
Dockerfile      # multi-stage build (frontend -> backend)
docker-compose.yml
nginx.conf
```

## Backend Setup (local)

1. **Install dependencies**
   ```bash
   cd backend
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
   On Windows (PowerShell):
   ```powershell
   cd backend
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. **Environment variables**
   If you have an `.env` file, it will be loaded automatically. Not required for local sqlite.
3. **Database migrations**
   ```bash
   python manage.py migrate
   ```
4. **Run services**
   ```bash
   # Django API (local dev)
   python manage.py runserver 0.0.0.0:8010

   # Celery worker (separate terminal)
   celery -A high_traffic worker --loglevel=info --queues=leads
   ```
   Notes:
   - To run without Redis locally, set `USE_LOCAL_CACHE=1` (rate limit disabled):
     - Unix/mac: `export USE_LOCAL_CACHE=1`
     - Windows PowerShell: `$env:USE_LOCAL_CACHE="1"`
   - The `/api/health/` endpoint will report "degraded" if Redis, Mongo, or Celery are not running. This does not affect basic lead submission functionality.

5. **API Docs (Swagger UI)**
   - Visit `http://localhost:8010/docs/` for interactive API documentation.
   - Docs are powered by a static OpenAPI file at `backend/static/openapi.json`.

## Frontend Setup

```bash
cd frontend
npm install
# Example (PowerShell) – point frontend to local backend on 8010
$env:VITE_API_BASE_URL="http://localhost:8010"
npm run dev -- --host          # http://localhost:5173 → http://localhost:8010
npm run build                  # outputs dist/ consumed by Django/Whitenoise
```

After `npm run build`, Django automatically serves the compiled assets (`frontend/dist`) through `LandingPageView`. Until then, a fallback placeholder template is shown.

For Vite, you can set `VITE_API_BASE_URL` (and/or `VITE_API_PROXY`) in `.env.local` to point at any backend origin, for example:

```bash
VITE_API_BASE_URL=http://localhost:8010
VITE_API_PROXY=http://localhost:8010
```

## Docker Workflow

Builds React + Django inside one image and runs the full stack (Postgres, Redis, Mongo, Celery worker, Nginx edge).

```bash
docker compose build
docker compose up
```

Services:

- `web`: Gunicorn + Django + Whitenoise (runs migrations on start)
- `worker`: Celery worker (leads queue)
- `nginx`: Lightweight reverse proxy on port 80
- `db`, `redis`, `mongo`: backing data stores with persisted volumes

If you maintain a Docker env file, place it at `backend/.env.docker` (optional). The repository does not include one by default.

## API Surface

| Method | Path          | Description                                         |
| ------ | ------------- | --------------------------------------------------- |
| GET    | `/`           | Cached landing page (serves React build)            |
| POST   | `/api/leads/` | Accepts `{ "phone": "09123456789" }`, queues Celery |
| GET    | `/api/health/`| Checks Postgres, Redis, Mongo, Celery ping          |

Rate limiting: 10 POST requests per IP per minute (configurable via `django_ratelimit`).

## API Documentation

- Swagger UI: `http://localhost:8010/docs/`
- OpenAPI schema source: `backend/static/openapi.json`

## Observability & Logging

- Lead submissions persisted in PostgreSQL with status + timestamps.
- Request metadata (IP, UA, method, Celery task state) streamed to MongoDB collection `request_logs`.
- Redis cache stores the landing HTML for 5 minutes to keep TTFB sub-second.
- `/api/health/` surfaces dependency status for uptime monitoring without enqueuing dummy tasks.

### Realtime logs during registration (local)

- **Django runserver terminal**
  - Shows each HTTP request, including `POST /api/leads/` with status code (for example `202` on success or `400` on validation error).
  - Any exceptions or validation errors are printed here immediately while you test the landing page.

- **Celery worker terminal** (optional but recommended)
  - Run `celery -A high_traffic worker --loglevel=info --queues=leads` in a separate terminal.
  - A log entry is emitted whenever a lead-processing task is received and completed, so you can confirm background processing.

- **MongoDB logging**
  - When MongoDB is configured, structured request logs (IP, user agent, path, timestamps) for each lead submission are written into the configured Mongo database (see `MONGO_URI` / `MONGO_DB_NAME`).
  - Inspect these with your Mongo GUI/CLI to trace registrations over time.

## Development Tips

- Update `.env` / `.env.docker` whenever backing service hosts or credentials change.
- Rebuild the frontend whenever UI code changes so Django serves the latest bundle (`npm run build`).
- `LandingPageView` caches the rendered HTML string; flush via `python manage.py shell` and `from django.core.cache import cache; cache.delete('landing_page_html')` after deployments if needed.
- Run `npm run lint` and `python -m django check` before submitting changes.
- No Redis handy? export `USE_LOCAL_CACHE=1` to fall back to Django’s local cache (rate limiting is disabled in this mode).

## Testing

The project currently focuses on infrastructure scaffolding. Add Django tests under `backend/leads/tests.py` as business rules evolve (validation, rate limit behavior, Celery task success paths, etc.).

---

## راهنمای سریع اجرا (فارسی)

### اجرای بک‌اند (محلی)

1. **نصب پیش‌نیازها (Windows PowerShell)**
   ```powershell
   cd C:\Users\RED\land\landing_page\backend
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **اعمال مایگریشن‌ها و ساخت ادمین**
   ```powershell
   python manage.py migrate
   $env:DJANGO_SUPERUSER_USERNAME="admin"
   $env:DJANGO_SUPERUSER_EMAIL="admin@example.com"
   $env:DJANGO_SUPERUSER_PASSWORD="adminadmin"
   python manage.py createsuperuser --noinput
   ```

3. **اجرای سرور جنگو روی پورت 8010**
   ```powershell
   $env:SECRET_KEY="dev-local-secret"
   $env:DEBUG="1"
   $env:USE_LOCAL_CACHE="1"
   python manage.py runserver 0.0.0.0:8010
   ```

4. **مشاهده داکیومنتیشن API (Swagger)**
   - مرورگر را باز کنید و به آدرس `http://localhost:8010/docs/` بروید.

### اجرای فرانت‌اند (Vite + React)

1. **نصب پکیج‌های فرانت‌اند**
   ```powershell
   cd C:\Users\RED\land\landing_page\frontend
   npm install
   ```

2. **اتصال فرانت‌اند به بک‌اند محلی**
   قبل از اجرای dev server، آدرس API را ست کنید:
   ```powershell
   $env:VITE_API_BASE_URL="http://localhost:8010"
   npm run dev -- --host   # آدرس فرانت‌اند: http://localhost:5173
   ```

3. **تست صفحه لندینگ**
   - در مرورگر به آدرس `http://localhost:5173` بروید.
   - شماره موبایل را به فرمت `09123456789` وارد کنید.
   - روی دکمه Submit کلیک کنید؛ در صورت موفقیت، پیام سبز رنگ «Your number has been registered successfully!» نمایش داده می‌شود.

### لاگ‌های لحظه‌ای ثبت شماره (Realtime Logs)

- **ترمینال جنگو (runserver)**
  - هر درخواست `POST /api/leads/` همراه با کد وضعیت (مثلاً `202`) را به صورت لحظه‌ای نشان می‌دهد.
  - اگر ولیدیشن شماره اشتباه باشد یا خطایی رخ دهد، همان‌جا پیام خطا را می‌بینید.

- **ترمینال Celery worker** (در صورت اجرای Celery)
  - در یک ترمینال جداگانه این دستورات را اجرا کنید:
    ```powershell
    cd C:\Users\RED\land\landing_page\backend
    .\.venv\Scripts\Activate.ps1
    celery -A high_traffic worker --loglevel=info --queues=leads
    ```
  - هر بار که شماره موبایل در فرانت‌اند ثبت می‌شود، یک تسک جدید در این ترمینال لاگ می‌شود.

- **لاگ‌های MongoDB**
  - در محیط کامل (Docker یا سرور واقعی) متادیتای درخواست‌ها در MongoDB ذخیره می‌شود (`MONGO_URI` و `MONGO_DB_NAME`).
  - می‌توانید با ابزارهای Mongo (Compass، mongosh و غیره) این لاگ‌ها را برای مشاهده رفتار سیستم در زمان واقعی بررسی کنید.
