# Itseasy Keitaro

Веб-приложение для управления кампаниями в трекере [Keitaro](https://keitaro.io): создание кампаний с GEO- и OFFER-потоками, локальное редактирование привязок офферов и синхронизация с Keitaro.

| Компонент | Стек | Где живёт |
|---|---|---|
| Backend | FastAPI, SQLAlchemy (async), Alembic | [`backend/`](backend/README.md) |
| Frontend | React + Vite (в production — nginx) | [`frontend/`](frontend/README.md) |
| База данных | PostgreSQL 16 | контейнер `postgres` |

Весь стек поднимается одной командой из корня репозитория.

## Требования

- Docker с Compose v2 (Docker Desktop или Docker Engine + compose-плагин). Проверка: `docker compose version`
- Адрес вашего Keitaro и API-токен администратора
- Свободные порты `5173` (UI), `8000` (API), `5432` (PostgreSQL, только `127.0.0.1`)

## Быстрый старт

Все команды выполняются **из корня репозитория**.

**1. Создайте файл конфигурации**

```bash
cp .env.example .env          # Windows PowerShell: Copy-Item .env.example .env
```

**2. Заполните в `.env` обязательные значения**

| Переменная | Что указать |
|---|---|
| `KEITARO_BASE_URL` | Адрес Keitaro с `http://` или `https://`, например `https://keitaro.example.com` |
| `KEITARO_API_TOKEN` | API-токен администратора Keitaro |
| `POSTGRES_PASSWORD` | Любой пароль для БД (буквы и цифры) |
| `POSTGRES_DB_URL` | Нужен только для запуска без Docker. В Docker его можно не трогать |

Остальные переменные имеют рабочие значения по умолчанию. Полный список: [Конфигурация](#конфигурация).

**3. Соберите и запустите**

```bash
docker compose up -d --build
```

Первая сборка занимает несколько минут. Порядок старта: PostgreSQL → backend (сначала применяются миграции Alembic, затем запускается Uvicorn) → frontend (ждёт, пока backend станет healthy).

**4. Проверьте, что всё поднялось**

```bash
docker compose ps
```

Все три сервиса (`postgres`, `app`, `frontend`) должны быть в статусе `running`/`healthy`.

| Что | Адрес |
|---|---|
| Интерфейс | http://localhost:5173 |
| API (через frontend) | http://localhost:5173/api/v1/campaigns |
| API напрямую | http://localhost:8000/api/v1 |
| Health-check (проверяет БД) | http://localhost:8000/health |
| Swagger UI (только `ENV=development`) | http://localhost:8000/docs |

Если `/health` отвечает `{"status":"ok"}`, backend работает и подключён к БД.

## Режимы: development и production

Режим задаётся переменной `ENV` в `.env`.

| | `ENV=development` (по умолчанию в примере) | `ENV=production` |
|---|---|---|
| Backend | `uvicorn --reload`, правки в `backend/app` подхватываются без пересборки | `uvicorn` без reload |
| Frontend | Vite dev server с hot reload | статичная сборка, раздаётся nginx |
| Swagger `/docs` | доступен | отключён |

После смены `ENV` пересоберите стек: `docker compose up -d --build`.

> В Docker поддерживаются только значения `development` и `production`. Другое значение (например, `staging`) сломает сборку frontend.

## Повседневные команды

```bash
docker compose up -d                 # запустить (без пересборки)
docker compose up -d --build         # пересобрать образы и запустить
docker compose ps                    # статус сервисов
docker compose logs -f app           # логи backend
docker compose logs -f frontend      # логи frontend
docker compose logs -f postgres      # логи БД
docker compose restart app           # перезапустить backend
docker compose down                  # остановить (данные БД сохраняются)
docker compose down -v               # остановить и УДАЛИТЬ данные БД
```

Дополнительно:

```bash
# Статус миграций / ручное применение (миграции и так применяются при старте backend)
docker compose exec app alembic current
docker compose exec app alembic upgrade head

# Консоль PostgreSQL (значения по умолчанию; подставьте свои из .env)
docker compose exec postgres psql -U postgres -d keitaro_app
```

## Конфигурация

Единый файл — `.env` в корне. Compose использует его и для подстановки значений в `docker-compose.yml`, и как `env_file` для backend. Секреты в образы не попадают (`.env` исключён через `.dockerignore`).

| Переменная | По умолчанию | Описание |
|---|---|---|
| `ENV` | `development` | Режим, см. выше |
| `DEBUG` | `False` | Расширенная отладка backend |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `KEITARO_BASE_URL` | — (обязательно) | Адрес Keitaro (`http://` или `https://`) |
| `KEITARO_API_TOKEN` | — (обязательно) | API-токен Keitaro |
| `KEITARO_TIMEOUT_SECONDS` | `30` в коде, `60` в примере | Таймаут запросов к Keitaro |
| `CAMPAIGN_NAME_PREFIX` | `test_zhestkov_` | Префикс создаваемых кампаний. В списке показываются только кампании с этим префиксом |
| `CAMPAIGN_GROUP_ID` | `10332` | Группа Keitaro для новых кампаний |
| `CAMPAIGN_DOMAIN_ID` | `1813` | Домен Keitaro для новых кампаний |
| `CAMPAIGN_TRAFFIC_SOURCE_ID` | `836` | Источник трафика для новых кампаний |
| `POSTGRES_USER` | `postgres` | Пользователь БД |
| `POSTGRES_PASSWORD` | — (обязательно) | Пароль БД |
| `POSTGRES_DATABASE` | `keitaro_app` | Имя БД |
| `POSTGRES_PORT` | `5432` | Порт БД на хосте |
| `POSTGRES_DB_URL` | — | DSN для запуска без Docker. В Docker перекрывается значением из compose |
| `CORS_ALLOWED_ORIGINS` | `[]` | JSON-массив. В Docker фиксируется на `["http://localhost:5173"]` |

**Значения по умолчанию для `CAMPAIGN_*` — это идентификаторы конкретной установки Keitaro.** Перед использованием на другом Keitaro замените их на свои.

## Частые проблемы

**`POSTGRES_PASSWORD` is required / `Set POSTGRES_PASSWORD in .env`**
Вы не создали `.env` или не задали пароль. Выполните шаги 1–2 из быстрого старта.

**Сервис `app` не становится healthy, в логах `ValidationError`**
Не заданы или некорректны обязательные переменные. Смотрите `docker compose logs app`. Чаще всего это `KEITARO_BASE_URL` без `http(s)://` или пустой `KEITARO_API_TOKEN`.

**В логах `password authentication failed for user "postgres"`**
Пароль БД фиксируется при первом создании тома. Вы изменили `POSTGRES_PASSWORD` в `.env` после первого запуска. Либо верните старый пароль, либо пересоздайте БД: `docker compose down -v`, затем `docker compose up -d --build` (данные БД будут потеряны).

**`port is already allocated` / порт занят**
Для PostgreSQL измените `POSTGRES_PORT` в `.env`. Для `8000` и `5173` измените левую часть в `ports:` в `docker-compose.yml`. Для `5173` также измените `CORS_ALLOWED_ORIGINS` в compose.

**UI открывается, но списки пустые или ошибки запросов**
Проверьте `docker compose logs app`. Ошибки вида `401/403` от Keitaro означают неверный токен, а таймауты — недоступный `KEITARO_BASE_URL` из контейнера.

**Правки кода не подхватываются на Windows/macOS**
Это ожидаемо в `ENV=production`. В `development` включён polling (`WATCHFILES_FORCE_POLLING`, `CHOKIDAR_USEPOLLING`), правки подхватываются автоматически.

## Запуск без Docker (для разработки)

Подробные инструкции — в [`backend/README.md`](backend/README.md#запуск-без-docker) и [`frontend/README.md`](frontend/README.md#запуск-без-docker). Кратко: PostgreSQL можно поднять из того же compose (`docker compose up -d postgres`), а backend и frontend запускать локально.

## Структура проекта

```
.
├── docker-compose.yml        # весь стек: postgres + app (backend) + frontend
├── .env.example              # шаблон конфигурации (копируется в .env)
├── backend/                  # FastAPI-приложение
│   ├── app/                  # код: api, core, domain, integrations, models, repositories, schemas, services
│   ├── alembic/              # миграции БД
│   ├── Dockerfile
│   └── pyproject.toml
└── frontend/                 # React + Vite
    ├── src/
    ├── Dockerfile            # этапы: development (Vite) и production (nginx)
    └── nginx.conf            # проксирует /api на backend, SPA fallback
```

## Документация по компонентам

- [Backend](backend/README.md): API, настройки, миграции, синхронизация, локальная разработка
- [Frontend](frontend/README.md): интерфейс, используемые API-вызовы, локальная разработка
