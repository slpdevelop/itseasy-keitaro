# Backend — Keitaro Campaign Manager

FastAPI-сервис для управления кампаниями Keitaro. Хранит локальную проекцию кампаний, потоков (flows) и привязок офферов в PostgreSQL и синхронизирует её с Keitaro через Admin API.

> **Запуск всего проекта через Docker описан в [корневом README](../README.md).** Этот документ — про backend: настройки, API, миграции и локальная разработка.

## Стек

Python 3.11+ (в Docker-образе 3.13), FastAPI, Pydantic v2 / pydantic-settings, SQLAlchemy 2 (async) + asyncpg, Alembic, httpx.

## Конфигурация

Настройки читаются из переменных окружения и из файла `backend/.env` (`app/core/config.py`). В Docker переменные приходят из корневого `.env` через compose, отдельный `backend/.env` не нужен.

Полный список переменных и их значения по умолчанию — в [корневом README](../README.md#конфигурация), шаблон — [`../.env.example`](../.env.example). Для backend обязательны: `KEITARO_BASE_URL`, `KEITARO_API_TOKEN`, `POSTGRES_DB_URL`. При отсутствии или невалидном значении приложение не стартует (ошибка валидации Pydantic).

## Запуск без Docker

Backend запускается локально, PostgreSQL — из Docker.

```bash
# 1. Из корня репозитория: поднять только PostgreSQL
cp .env.example .env              # если ещё не создан; заполните значения
docker compose up -d postgres

# 2. Backend читает backend/.env, поэтому скопируйте туда конфигурацию
cp .env backend/.env              # Windows PowerShell: Copy-Item .env backend\.env
# В backend/.env проверьте POSTGRES_DB_URL: хост должен быть localhost,
# а пароль и порт совпадать с POSTGRES_PASSWORD и POSTGRES_PORT.

# 3. Окружение и зависимости
cd backend
python -m venv .venv
source .venv/bin/activate         # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# 4. Миграции и запуск
alembic upgrade head
uvicorn app.asgi:app --reload --port 8000
```

API: `http://localhost:8000/api/v1`. Swagger UI (только при `ENV=development`): `http://localhost:8000/docs`.

## API

Базовый префикс: `/api/v1`.

| Метод | Путь | Описание |
|---|---|---|
| GET | `/health` | Проверка приложения и БД (`SELECT 1`). 503, если БД недоступна. Без префикса `/api` |
| GET | `/campaigns` | Список кампаний из Keitaro. Только с префиксом `CAMPAIGN_NAME_PREFIX` |
| GET | `/campaigns/{campaign_id}` | Кампания с потоками и офферами. Если локальной проекции нет, импортируется из Keitaro |
| POST | `/campaigns` | Создать кампанию с GEO- и OFFER-потоками (201) |
| POST | `/campaigns/{campaign_id}/fetch` | Загрузить кампанию с потоками и офферами из Keitaro в локальную БД |
| POST | `/campaigns/{campaign_id}/sync` | Отправить накопленные локальные правки в Keitaro. 207, если есть ошибки по отдельным потокам |
| PUT | `/campaigns/streams/{flow_id}` | Изменить локальные привязки офферов потока (`flow_id` — UUID). В Keitaro не отправляется |
| GET | `/offers` | Каталог офферов из Keitaro |
| GET | `/offers/local` | Локально сохранённые офферы (`?include_deleted=true` — включая удалённые) |

`campaign_id` в путях — числовой ID кампании в Keitaro.

Тело запроса `POST /campaigns`:

```json
{
  "name": "test_zhestkov_de_offers",
  "country_code": "DE",
  "offer_id_list": [123, 456]
}
```

- `name` — 1–255 символов. К имени добавляется `CAMPAIGN_NAME_PREFIX`, если его там ещё нет.
- `country_code` — две латинские буквы.
- `offer_id_list` — от 1 до 100 уникальных положительных ID офферов Keitaro. Трафик делится поровну.

## Синхронизация и согласованность

- Создание кампании проверяет ID офферов до создания ресурсов в Keitaro. Чекпоинты и состояние идемпотентности хранятся в PostgreSQL 24 часа, поэтому повторный запрос клиента безопасен и создание возобновляется с места сбоя.
- Локальные правки (`PUT /campaigns/streams/{flow_id}`) накапливаются в PostgreSQL и уходят в Keitaro только вызовом `POST /campaigns/{id}/sync`.
- `fetch` загружает из Keitaro актуальное состояние, но не перезаписывает привязки с неотправленными локальными правками.
- Перед отправкой `sync` сравнивает текущее состояние потока в Keitaro с локальным снимком. Если они различаются, поток не перезаписывается, а в ответе появляется ошибка стадии `conflict`: сначала нужно сделать `fetch`.
- Каждый поток синхронизируется отдельно: сбой одного не блокирует остальные. Результат содержит счётчики, потоки, оставшиеся в ожидании (`flows_still_pending`), потоки, удалённые за время операции (`flows_not_found`), и ошибки по потокам с указанием стадии.
- В распределении 100% трафика участвуют только неудалённые офферы в состоянии ACTIVE. Офферы DISABLED сохраняются с нулевой долей.
- Приложением управляются только кампании с префиксом `CAMPAIGN_NAME_PREFIX`.

## Миграции

Alembic берёт DSN из настроек приложения (`POSTGRES_DB_URL`). В Docker миграции применяются автоматически при старте контейнера `app`.

```bash
alembic upgrade head                                  # применить все миграции
alembic current                                       # текущая ревизия
alembic revision --autogenerate -m "describe change"  # новая миграция по изменениям моделей
alembic downgrade -1                                  # откатить одну миграцию
```

## Качество кода и тесты

Инструменты входят в extras `dev`: `ruff` (линтер/форматтер), `mypy` (строгая типизация), `pytest` + `pytest-asyncio` + `respx`.

```bash
ruff check app
ruff format app
mypy app
pytest                       # каталог tests/ в поставку не включён
```

## Структура

```
backend/
├── app/
│   ├── main.py              # фабрика приложения, lifespan (БД, httpx-клиент), CORS
│   ├── asgi.py              # точка входа ASGI: uvicorn app.asgi:app
│   ├── api/                 # роутеры: /health и /api/v1 (campaigns, offers), зависимости
│   ├── core/                # настройки, подключение к БД, исключения и обработчики
│   ├── domain/              # доменная логика распределения офферов в потоке
│   ├── integrations/        # клиент Keitaro Admin API (keitaro_api, keitaro_gateway)
│   ├── models/              # SQLAlchemy-модели
│   ├── repositories/        # доступ к данным
│   ├── schemas/             # Pydantic-схемы запросов и ответов
│   └── services/            # бизнес-логика (service.py) и чекпоинты создания (checkpoint.py)
├── alembic/                 # миграции БД
├── alembic.ini
├── Dockerfile               # образ backend (собирается из корневого docker-compose.yml)
├── pyproject.toml
└── requirements.txt
```
