# Развёртывание AirFreeze (FastAPI + PostgreSQL)

Требование: API доступен по публичному HTTPS, не только `localhost`.

## Вариант A — Render (проще всего для учебного проекта)

1. Зарегистрируйтесь на [render.com](https://render.com), подключите GitHub-репозиторий (корень репозитория — папка `ios_front`, внутри неё лежит `AirFreeze`).

2. **PostgreSQL**  
   - Dashboard → **New** → **PostgreSQL**  
   - Создайте базу, запомните **Internal Database URL** (или External, если нужен доступ снаружи).

3. **Web Service**  
   - **New** → **Web Service** → тот же репозиторий  
   - **Root Directory**: `AirFreeze`  
   - **Runtime**: Python 3.11  
   - **Build Command**:  
     `pip install -r requirements.txt && alembic upgrade head`  
   - **Start Command**:  
     `uvicorn app.main:app --host 0.0.0.0 --port $PORT`  

4. **Переменные окружения** (Environment → Environment Variables):

   | Key | Значение |
   |-----|----------|
   | `DATABASE_URL` | Вставьте **External** URL из шага 2 (Render подставит `postgresql://...` — приложение само переведёт в `asyncpg`). |
   | `SECRET_KEY` | Длинная случайная строка (например `openssl rand -hex 32`). |
   | `CORS_ORIGINS` | URL вашего фронта через запятую, напр. `https://имя.vercel.app` (без этого браузер заблокирует запросы с прод-фронта). |
   | `BOOTSTRAP_ADMIN_EMAIL` | (опционально) email первого админа при регистрации. |

5. **Deploy**. После сборки откройте URL вида `https://airfreeze-api.onrender.com` — должны открываться `/docs`.

6. **Моковые рейсы**: зарегистрируйте админа (если задали `BOOTSTRAP_ADMIN_EMAIL`) → в Swagger авторизуйтесь → `POST /admin/flights` или раздел «Админ» на фронте, если фронт уже смотрит на этот API (`REACT_APP_API_URL`).

### Blueprint из репозитория

В корне `ios_front` лежит `render.yaml`. Можно: **New** → **Blueprint** → выбрать репозиторий; при необходимости вручную допишите `CORS_ORIGINS` в настройках сервиса после первого деплоя.

---

## Вариант B — Railway

1. [railway.app](https://railway.app) → New Project → Deploy from GitHub.  
2. Добавьте плагин **PostgreSQL**; в сервисе API в переменных появится `DATABASE_URL`.  
3. Сервис из папки `AirFreeze`: **Settings** → Root Directory / Watch Paths — укажите `AirFreeze`.  
4. **Deploy** → Custom Start Command:  
   `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`  
   (или используйте Dockerfile из `AirFreeze`.)  
5. Задайте `SECRET_KEY`, `CORS_ORIGINS`, при необходимости `BOOTSTRAP_ADMIN_EMAIL`.

---

## Вариант C — Docker (свой VPS / облако с Docker)

На сервере из папки `AirFreeze`:

```bash
docker build -t airfreeze-api .
docker run -e DATABASE_URL="postgresql+asyncpg://..." -e SECRET_KEY="..." -e CORS_ORIGINS="https://..." -p 8000:8000 airfreeze-api
```

(`DATABASE_URL` можно передать как `postgresql://...` от облачной БД.)

---

## Фронтенд после деплоя API

В `.env` фронта:

```env
REACT_APP_API_URL=https://ваш-сервис.onrender.com
```

Пересоберите/задеплойте фронт (Vercel/Netlify и т.д.).

---

## Проверка

- `GET https://.../docs` — Swagger.  
- Регистрация/логин с фронта — только если `CORS_ORIGINS` содержит точный origin фронта (со схемой `https://`, без лишнего слэша в конце).
