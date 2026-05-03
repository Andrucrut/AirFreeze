# ✈️ AirFreeze API

API сервис для поиска авиабилетов, заморозки цен и бронирования с JWT-аутентификацией.

---

## 🚀 Быстрый запуск (Docker)

### Запустить базу данных
docker compose up -d

### Установить зависимости (локально)
pip install -r requirements.txt

### Применить миграции
alembic upgrade head

### Запустить сервер
uvicorn main:app --reload --host 0.0.0.0 --port 8000


## Проверка работы

Swagger документация: http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc