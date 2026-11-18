# Keitaro Campaign Manager - Backend

FastAPI backend для управления кампаниями Keitaro.

## Требования

- Python 3.13+
- pip (менеджер пакетов)

## Установка

```bash
cd backend
python -m venv .venv
.\venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate    # Unix

pip install -e ".[dev,test]"
```

## Конфигурация

Создайте `backend/.env` на основе `.env.example`:

```bash
cp backend/.env.example backend/.env
# Отредактируйте backend/.env со своими значениями
```

**Критически важно:** Никогда не коммить реальные секреты в Git!  
Файлы `.env`, `.env.*` и `backend/.env*` исключены из Git через `.gitignore`.

### Обязательные переменные окружения:

- `APP_NAME` — название приложения
- `KEITARO_BASE_URL` — URL API Keitaro

Для разработки Keitaro API token не требуется. Для production настройте `KEITARO_API_TOKEN`.

## Запуск через Docker (рекомендуется)

Весь стек (приложение + PostgreSQL) запускается одним командой:

```bash
cd backend
docker compose up -d --build   # сборка образа и запуск приложения + БД
docker compose ps              # оба сервиса должны быть healthy
docker compose logs -f app     # логи приложения
docker compose down            # остановить (данные БД сохраняются в volume)
```

- Приложение: `http://localhost:8000` (health: `/health`, docs: `/docs`)
- PostgreSQL: `localhost:5432`, база создаётся автоматически при старте
- Настройки берутся из `backend/.env` (через `env_file`); секреты не попадают
  в образ (исключены через `.dockerignore`)
- Порядок старта: PostgreSQL → healthcheck → приложение; приложение ждёт БД
  и устанавливает подключение в `lifespan`

## Запуск локально (без Docker для приложения)

```bash
cd backend
docker compose up -d           # только PostgreSQL

# В активированном venv
uvicorn app.asgi:app --reload --port 8000
```

API доступно по адресу `http://localhost:8000/api/v1`  
OpenAPI документация (только для dev): `http://localhost:8000/docs`

## PostgreSQL (Docker)

БД поднимается через Docker Compose (файл `docker-compose.yml`):

```bash
cd backend
docker compose up -d     # запуск PostgreSQL
docker compose ps        # статус (healthy)
docker compose down      # остановить (данные сохраняются в volume)
```

Настройки берутся из `backend/.env`: `USE_POSTGRESQL=True` и `POSTGRES_*`
(`POSTGRES_PASSWORD` обязателен и должен совпадать с паролем контейнера).

При старте приложения в `lifespan`:

- создаётся база данных (если её ещё нет);
- устанавливается и проверяется подключение (`SELECT 1`);
- при недоступности БД запуск завершается ошибкой (попытки повторяются,
  пока контейнер стартует);
- при остановке приложения соединение корректно закрывается.

Если `USE_POSTGRESQL=False`, подключение к БД не устанавливается.

## Тестирование

```bash
# В активированном venv
pytest app/tests/ -v --cov=app --cov-report=html
```

Покрытие тестами: **86%** и выше.

## Структура проекта

```
backend/
├── app/
│   ├── main.py              # Точка входа FastAPI
│   ├── api/
│   │   └── v1/              # Маршруты API v1
│   │       ├── router.py
│   │       └── endpoints/
│   │           └── health.py
│   ├── core/
│   │   ├── config.py        # Pydantic Settings
│   │   ├── exceptions.py    # Обработчики исключений
│   │   └── __init__.py
│   └── tests/               # Тесты
├── .env.example             # Пример конфигурации
├── .env                     # Ваши секреты (не коммитить!)
├── Dockerfile               # Образ приложения
├── docker-compose.yml       # Стек: приложение + PostgreSQL
├── pyproject.toml
└── README.md
```

## План разработки

См. [PLAN.md](../PLAN.md) для деталей реализации:

- **Этап 0:** Анализ репозитория ✅
- **Этап 1:** Python окружение ✅
- **Этап 2:** Каркас FastAPI ✅
- **Этап 3:** Конфигурация и безопасность ✅
- **Этап 4+:** В разработке

## Лицензия

[ICVR license](../ICVR_LICENSE)
