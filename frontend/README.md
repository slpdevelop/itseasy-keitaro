# Frontend — Keitaro Companies UI

React + Vite интерфейс для backend (FastAPI + Keitaro). Позволяет просматривать и создавать кампании, редактировать привязки офферов в потоках и запускать синхронизацию с Keitaro.

> **Запуск всего проекта через Docker описан в [корневом README](../README.md).** В Docker интерфейс доступен на `http://localhost:5173`.

## Как устроен запуск в Docker

[`Dockerfile`](Dockerfile) содержит два целевых этапа, выбор делается переменной `ENV` в корневом `.env`:

| `ENV` | Этап | Что работает |
|---|---|---|
| `development` | `development` | Vite dev server с hot reload. `/api` проксируется на `http://app:8000` (`vite.config.js`) |
| `production` | `production` | Статичная сборка (`npm run build`), раздаётся nginx. `/api/` проксируется на backend (`nginx.conf`) |

В обоих случаях браузер обращается к API по относительному пути `/api/v1` (`VITE_API_BASE_URL=/api/v1`), то есть на тот же origin, поэтому CORS не нужен.

## Запуск без Docker

Нужен Node.js 20.19+ (или 22.12+) и запущенный backend на `http://localhost:8000` (см. [`backend/README.md`](../backend/README.md#запуск-без-docker)).

```bash
cd frontend
npm install
npm run dev -- --port 5173
```

Откройте `http://localhost:5173`.

- Порт `5173` указан явно, потому что в `vite.config.js` по умолчанию задан порт `80` (он нужен контейнеру).
- Если `VITE_API_BASE_URL` не задана, фронтенд обращается к `http://localhost:8000/api/v1`. Это работает, пока backend разрешает origin `http://localhost:5173` (`CORS_ALLOWED_ORIGINS`, значение по умолчанию в `.env.example` подходит).
- Чтобы указать другой адрес API, задайте переменную перед запуском. Значение должно включать префикс версии:

  ```bash
  VITE_API_BASE_URL=http://localhost:8000/api/v1 npm run dev -- --port 5173
  ```

Продакшн-сборка без Docker:

```bash
npm run build      # результат в dist/
npm run preview
```

## Используемые вызовы API

Все пути относительно `/api/v1` (определены в `src/api.js`).

| Действие в интерфейсе | Запрос |
|---|---|
| Список кампаний | `GET /campaigns` |
| Детали кампании и потоки | `GET /campaigns/{campaign_id}` |
| Создание кампании | `POST /campaigns` |
| Выпадающий список офферов Keitaro | `GET /offers` |
| Локально сохранённые офферы | `GET /offers/local` |
| Сохранение привязок офферов потока (локально) | `PUT /campaigns/streams/{flow_id}` |
| Fetch: загрузить кампанию из Keitaro | `POST /campaigns/{campaign_id}/fetch` |
| Sync: отправить локальные правки в Keitaro | `POST /campaigns/{campaign_id}/sync` |

Форма создания отправляет:

```json
{
  "name": "test_company_de",
  "country_code": "DE",
  "offer_id_list": [123, 456]
}
```

Описание контракта и семантики синхронизации — в [`backend/README.md`](../backend/README.md#api).

## Заметки

- Правки офферов в потоке сохраняются локально в БД backend, а в Keitaro уходят только после нажатия Sync.
- Если состояние потока в Keitaro изменилось после последнего Fetch, Sync не перезапишет его и вернёт конфликт: сначала выполните Fetch.
- Интерфейс нормализует типичные варианты формата ответов (`items`, `data`, `flows`/`streams`, `offers`/`offer_bindings`). Вспомогательные функции находятся в `src/api.js` и `src/App.jsx`.
- Фронтенд не хранит учётные данные: токен Keitaro остаётся только на backend.
