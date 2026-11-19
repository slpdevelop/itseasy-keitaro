# AGENTS.md — контекст и правила разработки

Этот файл — краткая карта backend-проекта **Keitaro Campaign Manager**. Прочитай его перед анализом задачи или изменением кода. Он описывает фактическую структуру репозитория и текущие реализации, а не желаемую архитектуру.

## 1. Назначение проекта

Backend на FastAPI для управления рекламными кампаниями в Keitaro через Admin API v1.

Основной сценарий создания кампании:
1. Принять параметры кампании от клиента.
2. Создать кампанию в Keitaro.
3. Создать GEO-поток (stream) для перенаправления.
4. Создать поток с офферами.
5. Сохранить кампанию, потоки и связи с офферами в локальную PostgreSQL.

Keitaro — внешняя система и источник идентификаторов `keitaro_id`. Локальная БД хранит собственные UUID и связанные данные.

## 2. Технологии

- Python; фактическая конфигурация проекта ориентирована на Python 3.13.
- FastAPI, Uvicorn.
- Pydantic v2 и pydantic-settings.
- SQLAlchemy 2.x async ORM, `asyncpg`.
- Alembic для миграций.
- HTTPX `AsyncClient` для запросов к Keitaro.
- PostgreSQL.
- Pytest, pytest-asyncio, HTTPX, Respx.
- Docker / Docker Compose.
- Ruff и mypy.

Зависимости и настройки инструментов находятся в `pyproject.toml`.

## 3. Карта проекта

```text
app/
├── asgi.py                     # ASGI entry point: uvicorn app.asgi:app
├── main.py                     # FastAPI application factory и lifespan
├── api/
│   ├── dependencies.py         # FastAPI dependencies и сборка объектов приложения
│   ├── endpoints/
│   │   └── health.py           # GET /health
│   └── v1/
│       ├── router.py           # сборка API v1
│       └── endpoints/
│           ├── campaigns.py    # GET/POST /api/v1/campaigns
│           ├── offers.py       # GET /api/v1/offers, GET /api/v1/offers/{id}
│           └── resources.py    # справочники Keitaro
├── core/
│   ├── config.py               # Settings, загрузка и валидация конфигурации
│   ├── database.py             # создание/проверка/закрытие PostgreSQL engine
│   └── exceptions.py           # прикладные исключения и HTTP handlers
├── integrations/
│   ├── keitaro.py              # HTTP-клиент-обёртка для Keitaro
│   ├── campaign_gateway.py     # Keitaro implementation для кампаний
│   └── flow_gateway.py         # Keitaro implementation для потоков
├── interfaces/
│   ├── campaign_gateway.py     # CampaignGateway Protocol
│   └── flow_gateway.py         # FlowGateway Protocol
├── models/
│   └── models.py               # SQLAlchemy Base и ORM-модели
├── repositories/
│   └── campaign_repository.py  # сохранение кампании, flows и flow-offers
├── schemas/
│   ├── campaign.py             # входные/выходные схемы кампаний и payload Keitaro
│   ├── flow.py                 # схема потока и вложенных фильтров/офферов
│   └── offer.py                # схемы офферов
├── services/
│   ├── campaign_service.py     # сценарий создания и получения кампаний
│   └── flow_service.py         # подготовка и создание GEO/offer flows
└── tests/
    ├── conftest.py
    └── api/v1_test.py

alembic/
├── env.py
└── versions/                   # версии миграций

alembic.ini
Dockerfile
docker-compose.yml
pyproject.toml
.env.example
README.md
```

Не ориентируйся на устаревшую схему каталогов в README: сверяйся с реальными файлами репозитория.

## 4. Архитектура и направление зависимостей

Используется разделение на API, services, interfaces, integrations и repositories.

### API layer — `app/api/`

Отвечает за HTTP-контракт:
- объявляет маршруты и HTTP-методы;
- принимает и валидирует входные Pydantic-схемы;
- получает зависимости через FastAPI `Depends`;
- вызывает сервисы или gateway для простых прокси-операций;
- возвращает результат.

Не размещай здесь бизнес-сценарии, SQL-запросы, детали HTTP-вызовов к Keitaro или сборку сложных payload.

### Services — `app/services/`

Оркестрируют бизнес-сценарии:
- `CampaignService` управляет последовательностью создания кампании;
- `FlowService` формирует данные GEO- и offer-потоков и передаёт их gateway.

Сервис зависит от интерфейса/контракта внешнего взаимодействия, настроек и репозитория, а не должен самостоятельно создавать HTTP-клиент или управлять FastAPI Request.

### Interfaces — `app/interfaces/`

Содержат `Protocol`-контракты gateway. Это граница между бизнес-логикой и конкретной реализацией интеграции.

При добавлении новой реализации сохраняй совместимость с соответствующим Protocol.

### Integrations — `app/integrations/`

Содержат реализацию взаимодействия с Keitaro:
- `KeitaroGateway` — общая HTTP-обёртка;
- `KeitaroCampaignGateway` — операции с кампаниями;
- `KeitaroFlowGateway` — операции с потоками.

Не дублируй обработку HTTP-ошибок и транспортную логику в endpoint/service.

### Repositories — `app/repositories/`

Отвечают за локальное хранение и ORM-запросы. Сейчас `CampaignRepository` сохраняет кампанию, два потока и связи потоков с офферами в одной транзакции.

Не помещай SQLAlchemy-запросы в endpoint или integration.

### Models и schemas

- `models/` — ORM-модели SQLAlchemy и структура локальной БД.
- `schemas/` — Pydantic-контракты API и payload, передаваемых Keitaro.

Не путай Pydantic-схему с ORM-моделью: это разные уровни и разные задачи.

## 5. Как проходит создание кампании

Текущий маршрут: `POST /api/v1/campaigns`.

Последовательность:

```text
HTTP client
  -> app/api/v1/endpoints/campaigns.py
  -> CampaignServiceDep (app/api/dependencies.py)
  -> CampaignService.create_campaign()
       -> Checkpoint.run("create_campaign")
            -> CampaignGateway
                 -> KeitaroCampaignGateway
                      -> KeitaroGateway
                           -> Keitaro Admin API
       -> Checkpoint.run("create_geo_flow")
            -> FlowService.create_geo_flow()
                 -> FlowGateway -> KeitaroFlowGateway -> KeitaroGateway
       -> Checkpoint.run("create_offer_flow")
            -> FlowService.create_offer_flow()
                 -> FlowGateway -> KeitaroFlowGateway -> KeitaroGateway
       -> Checkpoint.run("save_to_db")
            -> CampaignRepository.save_created_campaign()
                 -> SQLAlchemy AsyncSession -> PostgreSQL
  -> KTCampaignCreateResponse
```

### Детали сценария

`CampaignService.create_campaign()`:
1. Формирует имя через `_build_campaign_name()`. Используется `settings.campaign_name_prefix` (по умолчанию `test_zhestkov_`).
2. Создаёт кампанию через `CampaignGateway`.
3. Создаёт GEO flow через `FlowService`.
4. Создаёт offer flow через `FlowService`.
5. Сохраняет результат в локальную БД через `CampaignRepository`.
6. Возвращает `KTCampaignCreateResponse`.

Для шагов используется `Checkpoint` из `campaign_service.py`. По умолчанию файл чекпоинта находится в системной temp-директории (`campaign_checkpoint.json`), ключ — итоговое имя кампании. Успешный результат шага сохраняется в JSON и используется при повторном запросе. `clear()` сбрасывает запись для ключа, но автоматически в сценарии не вызывается.

При изменении этого сценария учитывай частично выполненные внешние операции: повторный запрос может продолжить выполнение с сохранённого шага, а не начать с нуля.

`CampaignRepository.save_created_campaign()` выполняет upsert по `keitaro_id` и использует одну транзакцию для кампании, flows и flow-offers. Не разбивай эту запись на независимые commit без явной причины.

## 6. Текущие модели данных

Все основные сущности используют UUID как локальный первичный ключ через `BaseModel.id`. Для сущностей Keitaro используется `KeitaroEntityMixin.keitaro_id` — уникальный индексируемый integer ID внешней системы.

### Campaign

Таблица `campaigns`:
- `id` — локальный UUID;
- `keitaro_id` — ID кампании в Keitaro;
- `name`;
- `domain_keitaro_id`, `group_keitaro_id`, `traffic_source_keitaro_id`;
- `fetched_at`;
- общие поля `created_at`, `updated_at`, `synced`, `deleted`;
- relationship `flows`.

### Flow

Таблица `flows`:
- `id`, `keitaro_id`;
- `campaign_id` — FK на `campaigns.id`, `ON DELETE CASCADE`;
- `name`, `type`, `position`;
- `schema`, `action_type`, `action_payload`, `country`;
- `fetched_at` и общие поля.

`FlowType`: `geo`, `offer`. Для `country` задано ограничение: NULL или ровно два символа.

### Offer

Таблица `offers`:
- `id`, `keitaro_id`;
- `name`, `fetched_at`;
- общие поля.

### FlowOffer

Таблица `flow_offers` связывает `Flow` и `Offer`:
- `flow_id` — FK на `flows.id`, `ON DELETE CASCADE`;
- `offer_id` — FK на `offers.id`, `ON DELETE RESTRICT`;
- `share` — CHECK от 0 до 100;
- `state` — `active` или `disabled`;
- уникальная пара `(flow_id, offer_id)`.

При изменении ORM-моделей проверь необходимость новой Alembic-миграции. Не редактируй уже применённые миграции без отдельного согласованного решения.

## 7. Keitaro API и HTTP-клиент

`app/main.py` создаёт один `httpx.AsyncClient` на lifespan приложения:
- `base_url` строится как `{KEITARO_BASE_URL}/admin_api/v1`;
- API key передаётся заголовком `Api-Key`;
- timeout задаётся `KEITARO_TIMEOUT_SECONDS`.

`KeitaroGateway.request()`:
- выполняет запрос;
- преобразует timeout в `KeitaroTimeoutError`;
- преобразует транспортные и HTTP-ошибки Keitaro в `KeitaroError`;
- возвращает `None` для 204/пустого ответа;
- ожидает JSON для непустого успешного ответа.

Новые вызовы Keitaro добавляй через gateway-слой и соответствующий Protocol, если это отдельная операция/область ответственности. Учитывай, что успешный HTTP-ответ не гарантирует ожидаемую структуру JSON: проверяй необходимые поля на уровне бизнес-сценария.

Не логируй API key, пароль БД, полный URL с секретами или содержимое чувствительных заголовков.

## 8. API endpoints

Префиксы собираются так:
- `app/main.py`: `application.include_router(v1_router, prefix="/api")`;
- `app/api/v1/router.py`: `APIRouter(prefix="/v1")`.

Фактические маршруты:

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/health` | Health check приложения |
| GET | `/api/v1/campaigns` | Получить кампании с фильтрацией по настроенному префиксу имени |
| POST | `/api/v1/campaigns` | Создать кампанию, GEO flow, offer flow и сохранить локально |
| GET | `/api/v1/offers` | Получить офферы из Keitaro |
| GET | `/api/v1/offers/{offer_id}` | Получить один оффер |
| GET | `/api/v1/domains` | Справочник доменов |
| GET | `/api/v1/groups` | Справочник групп |
| GET | `/api/v1/traffic-sources` | Справочник источников трафика |
| GET | `/api/v1/stream-filters` | Справочник stream filters |
| GET | `/api/v1/stream-schemas` | Справочник stream schemas |
| GET | `/api/v1/stream-types` | Справочник stream types |
| GET | `/api/v1/streams-actions` | Справочник stream actions |

Документация OpenAPI доступна в development-режиме по `/docs` и `/openapi.json`. В production эти URL отключены настройками `get_app()`.

## 9. Dependency Injection

Фабрики зависимостей расположены в `app/api/dependencies.py`.

Основные зависимости:
- `KeitaroDep` — `KeitaroGateway`, использующий `request.app.state.http_client`;
- `FlowServiceDep` — `FlowService` с `KeitaroFlowGateway`;
- `CampaignRepositoryDep` — `CampaignRepository`, созданный из `request.app.state.db_engine`;
- `CampaignServiceDep` — `CampaignService` с gateway, flow service, settings и repository.

При добавлении зависимости:
1. Создай функцию-провайдер в `app/api/dependencies.py`, если это зависимость уровня приложения/API.
2. Объяви тип через `Annotated[..., Depends(...)]`.
3. Инжектируй dependency в endpoint/service factory через типизированный параметр.
4. Не создавай новый HTTP client или engine на каждый запрос — используй ресурсы lifespan.

Важно: сейчас `get_campaign_repository()` предполагает, что `request.app.state.db_engine` уже создан. Но создание engine в lifespan условное (`settings.use_postgresql`). При `USE_POSTGRESQL=False` dependency для campaign service не сможет получить engine. Перед использованием/изменением этого поведения сначала уточни ожидаемый режим хранения и исправь конфигурацию/DI согласованно.

## 10. Конфигурация и запуск

Настройки описаны в `app/core/config.py`, загружаются из `.env` в корне backend-проекта. Не читай и не выводи реальные `.env`/секреты в логах или ответах.

Основные параметры:
- `KEITARO_BASE_URL`;
- `KEITARO_API_TOKEN`;
- `KEITARO_TIMEOUT_SECONDS`;
- `CAMPAIGN_NAME_PREFIX`;
- `CAMPAIGN_GROUP_ID`;
- `CAMPAIGN_DOMAIN_ID`;
- `CAMPAIGN_TRAFFIC_SOURCE_ID`;
- `USE_POSTGRESQL`;
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DATABASE`, `POSTGRES_USER`, `POSTGRES_PASSWORD`;
- `CORS_ALLOWED_ORIGINS`, `CORS_ALLOW_CREDENTIALS`;
- `ENV`, `DEBUG`, `LOG_LEVEL`.

Некоторые campaign defaults имеют значения по умолчанию в `Settings`; сверяйся с `config.py`, а не предполагай, что все они обязательно заданы в `.env.example`.

### Локальный запуск

```bash
# Из корня backend
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Установка приложения и dev-зависимостей
pip install -e ".[dev]"

# Запуск API
uvicorn app.asgi:app --reload --port 8000
```

### Docker

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f app
docker compose down
```

Compose поднимает PostgreSQL и приложение. В контейнерной сети приложение подключается к хосту БД `postgres`.

### Миграции Alembic

`alembic/env.py` импортирует `Base.metadata` из `app.models.models` и получает DSN через `get_settings()` + `build_database_url()` при `USE_POSTGRESQL=True`.

```bash
# Из корня backend, при активном venv и настроенном .env
alembic upgrade head

# Создать миграцию после изменения ORM-моделей
alembic revision --autogenerate -m "describe_schema_change"

# Откатить одну ревизию
alembic downgrade -1

# Текущая ревизия БД
alembic current

# История
alembic history
```

После autogenerate обязательно просмотри миграцию: Alembic не заменяет code review и может не распознать переименование или смысловое изменение.

## 11. Тестирование и качество кода

Тесты находятся в `app/tests/`. Текущий `conftest.py` создаёт `TestClient` через `get_app()`. Текущий набор API-тестов проверяет health/API setup/OpenAPI/CORS, но не является полным покрытием бизнес-сценария создания кампании и сохранения в БД.

Запуск:

```bash
pytest app/tests/ -v
pytest app/tests/ -v --cov=app --cov-report=term-missing
ruff check .
ruff format .
mypy app/
```

При изменении бизнес-логики добавляй тесты на:
- успешный сценарий;
- ошибочный ответ/исключение Keitaro;
- невалидный или неполный ответ внешнего API;
- повторный запуск/поведение checkpoint, если затронуты шаги создания;
- запись в БД и rollback транзакции, если затронут repository;
- DI и режимы включённой/отключённой БД, если меняется lifecycle.

Используй HTTP mocking (в проекте присутствует Respx) вместо реальных запросов к Keitaro в unit/integration тестах.

## 12. Правила разработки для AI-агента

1. **Сначала исследуй, потом редактируй.** Перед изменением прочитай целевой модуль, его интерфейс, вызывающие места и тесты.
2. **Не ломай направление зависимостей.** Endpoint → service → interface/gateway/repository. Интеграционная HTTP-деталь не должна проникать в бизнес-сервис.
3. **Не смешивай внешние и локальные ID.** `keitaro_id` — ID Keitaro; `id` — локальный UUID. Не подменяй один другим.
4. **Не обходи Pydantic-контракты без причины.** Для payload используй схемы и `model_dump(...)` с нужными `by_alias`/`exclude_none`.
5. **Соблюдай async.** Для SQLAlchemy и HTTPX используй async API; не блокируй event loop синхронными сетевыми/DB-вызовами.
6. **Транзакции должны быть явными.** Несколько связанных записей в repository выполняй атомарно, если бизнес-операция требует целостности.
7. **Миграции обязательны при изменении схемы БД.** ORM-модель и миграция должны соответствовать друг другу.
8. **Не добавляй скрытые fallback-и.** Если БД или Keitaro недоступны, поведение должно быть явным и соответствовать контракту.
9. **Не делай широких рефакторингов в рамках точечной задачи.** Меняй минимальный набор файлов, необходимый для решения.
10. **Не выдумывай API Keitaro.** Проверяй существующие схемы/документацию проекта и реальные контракты; не угадывай названия полей и endpoint.
11. **Не коммить секреты и локальные данные.** Не добавляй `.env`, токены, пароли, дампы, `dev.db`, временные checkpoint-файлы.
12. **Не скрывай ошибки.** Не заменяй исключения на `None`/успешный ответ без явного бизнес-решения.
13. **Сохраняй совместимость.** При изменении API проверь response model, status code, валидацию и существующих клиентов/тесты.
14. **После изменений проверяй результат.** Запусти релевантные тесты и статические проверки; если не запускались — явно сообщи об этом.

## 13. Известные несоответствия и места для проверки

Это наблюдения по текущему снимку репозитория, а не разрешение автоматически менять их при любой задаче:

- `README.md` содержит устаревшее описание структуры и упоминает health под `/api/v1/`; фактический health route объявлен как `/health`.
- В README указана установка `.[dev,test]`, но в `pyproject.toml` определён optional extra `dev`, а отдельного `test` extra нет. Используй `.[dev]`, пока конфигурация не изменена.
- В `pyproject.toml` указано `requires-python = ">=3.9"`, но настройки Ruff/mypy и фактический код ориентированы на Python 3.13 и используют современный синтаксис типов. Не обещай поддержку Python 3.9 без отдельной проверки и корректировки метаданных/кода.
- `USE_POSTGRESQL` по умолчанию `False`, но `CampaignRepositoryDep` требует `request.app.state.db_engine`, который создаётся только при включённой PostgreSQL. Это влияет на `GET/POST /api/v1/campaigns` через текущую сборку `CampaignServiceDep`.
- `CampaignRepository._upsert_flow()` использует `CampaignCreationError`, но в текущем файле `campaign_repository.py` этот символ не импортирован. При ветке невалидного ID потока возможен `NameError`; при работе с этим кодом проверь и исправь импорт.
- В `CampaignOffersUpdateResponse` в `schemas/offer.py` поля `added` и `removed` объявлены дважды. Схема сейчас не используется в показанных endpoints; при работе с ней проверь и приведи к одному объявлению с `default_factory`.
- `Checkpoint` хранит результаты в одном JSON-файле системной temp-директории. Это локальный механизм возобновления, не распределённое/межпроцессное хранилище. Не считай его безопасным механизмом конкурентной координации нескольких workers.
- В `CampaignRepository._upsert_flow_offers()` текущая реализация обновляет/добавляет связи, но не удаляет связи, отсутствующие в новом списке. Не предполагай, что это полноценная синхронизация состава офферов.
- Тесты в `app/tests/api/v1_test.py` содержат проверки `/api/v1/` и health response, тогда как текущий health router регистрирует `/health`. Перед изменением тестов сначала установи фактический ожидаемый контракт и проверь запуск тестового набора.

Не исправляй все перечисленные пункты автоматически. Выбирай только те, которые относятся к задаче, и сообщай о побочных исправлениях отдельно.

## 14. Как агенту начинать новую задачу

Перед реализацией:
1. Сформулируй, какой пользовательский сценарий и API/данные затрагиваются.
2. Найди endpoint и проследи вызовы до service, gateway/repository и модели.
3. Проверь Pydantic-схемы и реальные payload/response-контракты.
4. Найди существующие тесты и связанные миграции.
5. Определи минимальный набор изменений.

В завершении:
1. Перечисли изменённые файлы и роль каждого изменения.
2. Укажи миграции, если менялась БД.
3. Укажи команды тестов/проверок и их результат.
4. Отдельно перечисли оставшиеся риски или непроверенные сценарии.

Если задача требует решения, которого текущая архитектура явно не поддерживает, сначала объясни конфликт и предложи минимальный вариант, не перестраивая проект самовольно.
