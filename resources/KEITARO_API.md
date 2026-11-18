# Keitaro Admin API v1 OAS3

> Документация сформирована автоматически из предоставленного HTML Swagger UI. Сведения, которых нет в исходном HTML, не дополнялись предположениями.

## Общая информация

- **Версия API:** v1
- **Формат спецификации:** OpenAPI 3 (OAS3)
- **Базовый путь:** `/admin_api/v1`
- **Формат данных:** JSON (`application/json`, где указан в исходнике)
- **Полный URL:** зависит от домена вашего Keitaro. К базовому адресу инсталляции добавляется указанный базовый путь.

### Авторизация

В HTML присутствует кнопка `Authorize`, однако схема авторизации, название заголовка и формат токена в доступном содержимом не раскрыты. Перед использованием API необходимо уточнить способ авторизации в настройках/официальной спецификации конкретной инсталляции.

### Общие замечания

- `{id}` — идентификатор ресурса в пути запроса.
- Операции архивации/восстановления выделены отдельно там, где это отражено в описании endpoint.
- Для многих операций HTML содержит только HTTP-метод, путь и краткое описание; параметры, тело запроса и схемы ответов в сохранённом HTML отсутствуют.
- Поэтому для таких операций ниже приведён только подтверждённый исходником контракт верхнего уровня. Неизвестные поля и примеры не выдумывались.

## Сводный список endpoints

### Affiliate networks

| Метод | Endpoint | Назначение |
|---|---|---|
| `GET` | `/affiliate_networks` | List all affiliate networks |
| `POST` | `/affiliate_networks` | Create an affiliate network |
| `GET` | `/affiliate_networks/{id}` | Retrieve Affiliate network details |
| `PUT` | `/affiliate_networks/{id}` | Update Affiliate network |
| `DELETE` | `/affiliate_networks/{id}` | Move affiliate network to the archive |
| `POST` | `/affiliate_networks/{id}/clone` | Clone affiliate network |
| `POST` | `/affiliate_networks/{id}/restore` | Restore affiliate network |
| `POST` | `/affiliate_networks/clean_archive` | Clean archive |
| `GET` | `/affiliate_networks/deleted` | Get deleted affiliate networks |

### Bot list

| Метод | Endpoint | Назначение |
|---|---|---|
| `GET` | `/botlist` | Retrieve rows from the bot list |
| `PUT` | `/botlist` | Update the bot list |
| `DELETE` | `/botlist` | Clear the bot list |
| `POST` | `/botlist/add` | Add IPs to the bot list |
| `POST` | `/botlist/exclude` | Remove IPs from the bot list |

### Campaigns

| Метод | Endpoint | Назначение |
|---|---|---|
| `GET` | `/campaigns` | Get all campaigns |
| `POST` | `/campaigns` | Create campaign |
| `GET` | `/campaigns/{id}` | Get campaign |
| `PUT` | `/campaigns/{id}` | Update campaign |
| `DELETE` | `/campaigns/{id}` | Move campaign to archive |
| `POST` | `/campaigns/{id}/clone` | Clone Campaign |
| `POST` | `/campaigns/{id}/disable` | Disable Campaign |
| `POST` | `/campaigns/{id}/enable` | Enable Campaign |
| `POST` | `/campaigns/{id}/restore` | Restore Campaign |
| `POST` | `/campaigns/{id}/update_costs` | Update costs for campaign |
| `POST` | `/campaigns/clean_archive` | Clean archive |
| `GET` | `/campaigns/deleted` | Get deleted campaigns |

### Flows (Streams)

| Метод | Endpoint | Назначение |
|---|---|---|
| `GET` | `/campaigns/{id}/streams` | Get flows |
| `GET` | `/stream_filters` | Get available flow filters |
| `GET` | `/stream_schemas` | Get available flow schemas |
| `GET` | `/stream_types` | Get list of flows types |
| `GET` | `/stream/{id}/events` | Get flow events |
| `GET` | `/streams_actions` | Get available flows actions |
| `POST` | `/streams` | Create flow |
| `GET` | `/streams/{id}` | Get flow |
| `PUT` | `/streams/{id}` | Update flow |
| `DELETE` | `/streams/{id}` | Delete flow |
| `POST` | `/streams/{id}/disable` | Disable flow |
| `POST` | `/streams/{id}/enable` | Enable flow |
| `POST` | `/streams/{id}/restore` | Restore an Archived Flow |
| `POST` | `/streams/clean_archive` | Clean archive |
| `GET` | `/streams/deleted` | Get deleted flows |
| `GET` | `/streams/search` | Search in flows |

### Clean stats

| Метод | Endpoint | Назначение |
|---|---|---|
| `POST` | `/clicks/clean` | Clean stats |

### Clicks

| Метод | Endpoint | Назначение |
|---|---|---|
| `POST` | `/clicks/log` | Get clicks |
| `POST` | `/clicks/update_costs` | Update costs in bulk |

### Conversions

| Метод | Endpoint | Назначение |
|---|---|---|
| `POST` | `/conversions/log` | Get conversions |

### Domains

| Метод | Endpoint | Назначение |
|---|---|---|
| `GET` | `/domains` | Get the list of domains |
| `POST` | `/domains` | Create domain |
| `GET` | `/domains/{id}` | Get domain |
| `PUT` | `/domains/{id}` | Update domain |
| `DELETE` | `/domains/{id}` | Move Domain to Archive |
| `POST` | `/domains/{id}/check` | Update Domain Status |
| `POST` | `/domains/{id}/restore` | Restore an Archived Domain |
| `POST` | `/domains/clean_archive` | Clean archive |
| `GET` | `/domains/deleted` | Get deleted domains |
| `GET` | `/domains/ip` | Retrieve server ip |
| `POST` | `/domains/register` | Register the domain |

### Groups

| Метод | Endpoint | Назначение |
|---|---|---|
| `GET` | `/groups` | Get groups |
| `POST` | `/groups` | Create croup |
| `PUT` | `/groups/{id}` | Update Group |
| `DELETE` | `/groups/{id}/delete` | Delete Group |

### Third-party integrations

| Метод | Endpoint | Назначение |
|---|---|---|
| `GET` | `/integrations/facebook` | Get Facebook integrations |
| `POST` | `/integrations/facebook` | Create Facebook Integration |
| `GET` | `/integrations/facebook/{id}` | Get Facebook integration |
| `PUT` | `/integrations/facebook/{id}` | Update Facebook integration |
| `DELETE` | `/integrations/facebook/{id}` | Delete Facebook integration |
| `GET` | `/integrations/facebook/{id}/campaign` | Get assigned campaigns. |
| `POST` | `/integrations/facebook/{id}/campaign` | Assign to campaign |
| `DELETE` | `/integrations/facebook/{id}/campaign` | Dissociate campaign |

### Landing pages

| Метод | Endpoint | Назначение |
|---|---|---|
| `GET` | `/landing_pages` | Get landing pages |
| `POST` | `/landing_pages` | Create landing page |
| `GET` | `/landing_pages/{id}` | Get Landing Page |
| `PUT` | `/landing_pages/{id}` | Update Landing Page |
| `DELETE` | `/landing_pages/{id}` | Archive Landing Page |
| `POST` | `/landing_pages/{id}/add_file` | Create a File |
| `PUT` | `/landing_pages/{id}/clone` | Clone Landing Page |
| `GET` | `/landing_pages/{id}/download` | Download |
| `GET` | `/landing_pages/{id}/get_file` | Read File |
| `GET` | `/landing_pages/{id}/get_structure` | Get Files Structure |
| `DELETE` | `/landing_pages/{id}/remove_file` | Remove file |
| `POST` | `/landing_pages/{id}/restore` | Restore landing page |
| `PUT` | `/landing_pages/{id}/update_file` | Save File Data |
| `POST` | `/landing_pages/clean_archive` | Clean archive |
| `GET` | `/landing_pages/deleted` | Get deleted landing pages |

### Logs

| Метод | Endpoint | Назначение |
|---|---|---|
| `GET` | `/logs/{type}` | Get log |
| `DELETE` | `/logs/{type}` | Clean log |
| `POST` | `/logs/types` | Get log types |

### Offers

| Метод | Endpoint | Назначение |
|---|---|---|
| `GET` | `/offers` | Get offers |
| `POST` | `/offers` | Create offer |
| `GET` | `/offers/{id}` | Get offer |
| `PUT` | `/offers/{id}` | Update offer |
| `POST` | `/offers/{id}/add_file` | Create file |
| `DELETE` | `/offers/{id}/archive` | Delete offer |
| `POST` | `/offers/{id}/clone` | Clone offer |
| `GET` | `/offers/{id}/download` | Download |
| `GET` | `/offers/{id}/get_file` | Read File |
| `GET` | `/offers/{id}/get_structure` | Get file structure |
| `DELETE` | `/offers/{id}/remove_file` | Delete file |
| `POST` | `/offers/{id}/restore` | Restore offer |
| `PUT` | `/offers/{id}/update_file` | Upload file |
| `POST` | `/offers/clean_archive` | Clean archive |
| `GET` | `/offers/deleted` | Get deleted offers |

### Reports

| Метод | Endpoint | Назначение |
|---|---|---|
| `POST` | `/report/build` | Build custom report |
| `GET` | `/report/labels` | Get Labels |
| `POST` | `/report/labels` | Update Labels |

### Traffic sources

| Метод | Endpoint | Назначение |
|---|---|---|
| `GET` | `/traffic_sources` | Get traffic sources |
| `POST` | `/traffic_sources` | Create traffic source |
| `GET` | `/traffic_sources/{id}` | Get traffic source |
| `PUT` | `/traffic_sources/{id}` | Update traffic source |
| `DELETE` | `/traffic_sources/{id}` | Delete traffic source |
| `POST` | `/traffic_sources/{id}/clone` | Clone trafic source |
| `POST` | `/traffic_sources/clean_archive` | Clean archive |

### Users

| Метод | Endpoint | Назначение |
|---|---|---|
| `GET` | `/users` | Get users |
| `POST` | `/users` | Create user |
| `GET` | `/users/{id}` | Get user |
| `PUT` | `/users/{id}` | Update user |
| `DELETE` | `/users/{id}` | Delete user |
| `PUT` | `/users/{id}/access` | Update access |
| `POST` | `/users/clean_archive` | Clean archive |

## Описание операций

### Affiliate networks

#### `GET /affiliate_networks`

List all affiliate networks

**Параметры:** отсутствуют (согласно исходнику).

**Ответы, указанные в исходнике:**

- **200** — Affiliate networks
- **400** — Bad request
- **401** — Access denied
- **402** — Admin API is not available in that edition
- **500** — Internal error

**Пример успешного ответа из HTML:**

```json
[
{
"id"
:
0
,
"name"
:
"string"
,
"postback_url"
:
"string"
,
"offer_param"
:
"string"
,
"state"
:
"active"
,
"template_name"
:
"string"
,
"notes"
:
"string"
,
"pull_api_options"
:
"string"
,
"created_at"
:
"string"
,
"updated_at"
:
"string"
,
"offers"
:
0
}
]
```

#### `POST /affiliate_networks`

Create an affiliate network

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /affiliate_networks/{id}`

Retrieve Affiliate network details

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `PUT /affiliate_networks/{id}`

Update Affiliate network

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `DELETE /affiliate_networks/{id}`

Move affiliate network to the archive

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /affiliate_networks/{id}/clone`

Clone affiliate network

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /affiliate_networks/{id}/restore`

Restore affiliate network

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /affiliate_networks/clean_archive`

Clean archive

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /affiliate_networks/deleted`

Get deleted affiliate networks

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

### Bot list

#### `GET /botlist`

Retrieve rows from the bot list

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `PUT /botlist`

Update the bot list

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `DELETE /botlist`

Clear the bot list

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /botlist/add`

Add IPs to the bot list

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /botlist/exclude`

Remove IPs from the bot list

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

### Campaigns

#### `GET /campaigns`

Get all campaigns

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /campaigns`

Create campaign

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /campaigns/{id}`

Get campaign

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `PUT /campaigns/{id}`

Update campaign

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `DELETE /campaigns/{id}`

Move campaign to archive

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /campaigns/{id}/clone`

Clone Campaign

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /campaigns/{id}/disable`

Disable Campaign

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /campaigns/{id}/enable`

Enable Campaign

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /campaigns/{id}/restore`

Restore Campaign

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /campaigns/{id}/update_costs`

Update costs for campaign

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /campaigns/clean_archive`

Clean archive

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /campaigns/deleted`

Get deleted campaigns

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

### Flows (Streams)

#### `GET /campaigns/{id}/streams`

Get flows

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /stream_filters`

Get available flow filters

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /stream_schemas`

Get available flow schemas

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /stream_types`

Get list of flows types

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /stream/{id}/events`

Get flow events

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /streams_actions`

Get available flows actions

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /streams`

Create flow

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /streams/{id}`

Get flow

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `PUT /streams/{id}`

Update flow

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `DELETE /streams/{id}`

Delete flow

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /streams/{id}/disable`

Disable flow

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /streams/{id}/enable`

Enable flow

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /streams/{id}/restore`

Restore an Archived Flow

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /streams/clean_archive`

Clean archive

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /streams/deleted`

Get deleted flows

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /streams/search`

Search in flows

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

### Clean stats

#### `POST /clicks/clean`

Clean stats

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

### Clicks

#### `POST /clicks/log`

Get clicks

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /clicks/update_costs`

Update costs in bulk

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

### Conversions

#### `POST /conversions/log`

Get conversions

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

### Domains

#### `GET /domains`

Get the list of domains

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /domains`

Create domain

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /domains/{id}`

Get domain

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `PUT /domains/{id}`

Update domain

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `DELETE /domains/{id}`

Move Domain to Archive

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /domains/{id}/check`

Update Domain Status

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /domains/{id}/restore`

Restore an Archived Domain

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /domains/clean_archive`

Clean archive

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /domains/deleted`

Get deleted domains

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /domains/ip`

Retrieve server ip

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /domains/register`

Register the domain

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

### Groups

#### `GET /groups`

Get groups

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /groups`

Create croup

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `PUT /groups/{id}`

Update Group

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `DELETE /groups/{id}/delete`

Delete Group

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

### Third-party integrations

#### `GET /integrations/facebook`

Get Facebook integrations

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /integrations/facebook`

Create Facebook Integration

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /integrations/facebook/{id}`

Get Facebook integration

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `PUT /integrations/facebook/{id}`

Update Facebook integration

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `DELETE /integrations/facebook/{id}`

Delete Facebook integration

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /integrations/facebook/{id}/campaign`

Get assigned campaigns.

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /integrations/facebook/{id}/campaign`

Assign to campaign

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `DELETE /integrations/facebook/{id}/campaign`

Dissociate campaign

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

### Landing pages

#### `GET /landing_pages`

Get landing pages

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /landing_pages`

Create landing page

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /landing_pages/{id}`

Get Landing Page

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `PUT /landing_pages/{id}`

Update Landing Page

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `DELETE /landing_pages/{id}`

Archive Landing Page

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /landing_pages/{id}/add_file`

Create a File

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `PUT /landing_pages/{id}/clone`

Clone Landing Page

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /landing_pages/{id}/download`

Download

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /landing_pages/{id}/get_file`

Read File

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /landing_pages/{id}/get_structure`

Get Files Structure

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `DELETE /landing_pages/{id}/remove_file`

Remove file

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /landing_pages/{id}/restore`

Restore landing page

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `PUT /landing_pages/{id}/update_file`

Save File Data

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /landing_pages/clean_archive`

Clean archive

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /landing_pages/deleted`

Get deleted landing pages

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

### Logs

#### `GET /logs/{type}`

Get log

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `DELETE /logs/{type}`

Clean log

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /logs/types`

Get log types

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

### Offers

#### `GET /offers`

Get offers

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /offers`

Create offer

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /offers/{id}`

Get offer

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `PUT /offers/{id}`

Update offer

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /offers/{id}/add_file`

Create file

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `DELETE /offers/{id}/archive`

Delete offer

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /offers/{id}/clone`

Clone offer

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /offers/{id}/download`

Download

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /offers/{id}/get_file`

Read File

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /offers/{id}/get_structure`

Get file structure

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `DELETE /offers/{id}/remove_file`

Delete file

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /offers/{id}/restore`

Restore offer

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `PUT /offers/{id}/update_file`

Upload file

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /offers/clean_archive`

Clean archive

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /offers/deleted`

Get deleted offers

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

### Reports

#### `POST /report/build`

Build custom report

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /report/labels`

Get Labels

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /report/labels`

Update Labels

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

### Traffic sources

#### `GET /traffic_sources`

Get traffic sources

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /traffic_sources`

Create traffic source

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /traffic_sources/{id}`

Get traffic source

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `PUT /traffic_sources/{id}`

Update traffic source

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `DELETE /traffic_sources/{id}`

Delete traffic source

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /traffic_sources/{id}/clone`

Clone trafic source

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /traffic_sources/clean_archive`

Clean archive

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

### Users

#### `GET /users`

Get users

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /users`

Create user

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `GET /users/{id}`

Get user

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `PUT /users/{id}`

Update user

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `DELETE /users/{id}`

Delete user

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `PUT /users/{id}/access`

Update access

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

#### `POST /users/clean_archive`

Clean archive

**Параметры, тело запроса и схемы ответа:** в сохранённом HTML для этой операции не раскрыты.

## Модели данных, раскрытые в HTML

### `AffiliateNetwork`

| Поле | Тип / описание типа |
|---|---|
| `id` | integer |
| `name` | string |
| `postback_url` | string |
| `offer_param` | string |
| `state` | string default : active Enum: Array [ 2 ] |
| `template_name` | string |
| `notes` | string |
| `pull_api_options` | string |
| `created_at` | string |
| `updated_at` | string |
| `offers` | integer |

### `Offer`

| Поле | Тип / описание типа |
|---|---|
| `id` | integer |
| `name` | string |
| `group_id` | integer |
| `action_type` | string |
| `action_payload` | { ... } |
| `action_options` | { ... } |
| `affiliate_network_id` | integer |
| `payout_value` | number |
| `payout_currency` | string |
| `payout_type` | string |
| `state` | string |
| `created_at` | string |
| `updated_at` | string |
| `payout_auto` | boolean |
| `payout_upsell` | boolean |
| `country` | [...] |
| `notes` | string |
| `affiliate_network` | string |
| `archive` | string |
| `local_path` | string |
| `preview_path` | string |
| `values` | [...] |

## Коды ошибок и типовые ответы

В раскрытом примере операции `GET /affiliate_networks` указаны следующие ответы:

| HTTP-код | Значение в исходнике |
|---|---|
| `200` | Affiliate networks |
| `400` | Bad request |
| `401` | Access denied |
| `402` | Admin API is not available in that edition |
| `500` | Internal error |

Для ошибок в примерах показан JSON-объект вида:

```json
{
  "error": "string"
}
```

Эти коды и формат ошибки подтверждены раскрытым в HTML endpoint `GET /affiliate_networks`; не следует автоматически считать, что все остальные endpoints возвращают абсолютно тот же набор кодов.

## Что не удалось извлечь из HTML

- Схему авторизации и точный формат токена.
- Детальные параметры, обязательность полей и тела запросов для большинства операций.
- Полные схемы ответов большинства операций.
- Пагинацию, фильтрацию, сортировку и ограничения, если они не отражены в раскрытых фрагментах.

Для полноценной машинно-читаемой спецификации предпочтительно использовать исходный OpenAPI JSON/YAML, а не HTML-рендер Swagger UI.


---

## Схемы данных (Schemas)

> Раздел сформирован по файлу `kt_schemas(1).html`. Поля, типы, описания, значения по умолчанию и обязательность перенесены только там, где они явно отображены в Swagger UI. Для вложенных объектов/массивов указана связанная схема, если её имя видно в HTML. Если структура вложенного значения не раскрыта, она не реконструировалась.

**Обозначения:** `*` — поле помечено обязательным в Swagger UI; `—` — значение не указано в HTML.

### `AffiliateNetwork`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `id` | `integer` | нет / не отмечено | — | — | — |
| `name` | `string` | нет / не отмечено | — | — | — |
| `postback_url` | `string` | нет / не отмечено | — | — | — |
| `offer_param` | `string` | нет / не отмечено | — | — | — |
| `state` | `string` | нет / не отмечено | active | Array                                                                             [ 2 ] | — |
| `template_name` | `string` | нет / не отмечено | — | — | — |
| `notes` | `string` | нет / не отмечено | — | — | — |
| `pull_api_options` | `string` | нет / не отмечено | — | — | — |
| `created_at` | `string` | нет / не отмечено | — | — | — |
| `updated_at` | `string` | нет / не отмечено | — | — | — |
| `offers` | `integer` | нет / не отмечено | — | — | — |

### `AffiliateNetworkObject`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `name` | `string` | нет / не отмечено | — | — | Affiliate network name |
| `postback_url` | `string` | нет / не отмечено | — | — | Postback URL for the Affiliate network |
| `offer_param` | `string` | нет / не отмечено | — | — | These params are appends to offer URLs. Example,                                                                         "sub1={subid}&sub2={campaign_name}" |
| `notes` | `string` | нет / не отмечено | — | — | User Notes for the Affiliate network |

### `AffiliateNetworkPut`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `name` | `string` | нет / не отмечено | — | — | Affiliate network name |
| `postback_url` | `string` | нет / не отмечено | — | — | Postback URL for the Affiliate network |
| `offer_param` | `string` | нет / не отмечено | — | — | These params are appends to offer URLs. Example,                                                                         "sub1={subid}&sub2={campaign_name}" |
| `notes` | `string` | нет / не отмечено | — | — | User Notes for the Affiliate network |

### `AffiliateNetworkRequest`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `name` | `string` | да | — | — | Affiliate network name |
| `postback_url` | `string` | нет / не отмечено | — | — | Postback URL for the Affiliate network |
| `offer_param` | `string` | нет / не отмечено | — | — | These params are appends to offer URLs. Example,                                                                         "sub1={subid}&sub2={campaign_name}" |
| `notes` | `string` | нет / не отмечено | — | — | User Notes for the Affiliate network |

### `BotListRequest`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `value` | `string` | да | — | — | List of IPs. Example, 1.2.3.4                                                                         2.3.4.5 |

### `Campaign`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `id` | `integer` | нет / не отмечено | — | — | — |
| `alias` | `string` | нет / не отмечено | — | — | Leave empty to generate automatically. |
| `type` | `string` | нет / не отмечено | position | Array                                                                             [ 2 ] | Set 'weight' to enable split-testing the flows. |
| `name` | `string` | нет / не отмечено | — | — | — |
| `cookies_ttl` | `integer` | нет / не отмечено | 24 | — | — |
| `position` | `integer` | нет / не отмечено | — | — | — |
| `state` | `string` | нет / не отмечено | active | Array                                                                             [ 3 ] | — |
| `cost_type` | `string` | нет / не отмечено | CPC | Array                                                                             [ 8 ] | — |
| `cost_value` | `number` | нет / не отмечено | 0 | — | — |
| `cost_currency` | `string` | нет / не отмечено | — | — | Leave empty to use tracker currency |
| `group_id` | `integer` | нет / не отмечено | — | — | — |
| `bind_visitors` | `string` | нет / не отмечено | — | Array                                                                             [ 3 ] | 's' for flows. 'sl' for flows and landing pages.                                                                         'slo' for flows, landing pages and offers. |
| `traffic_source_id` | `integer` | нет / не отмечено | — | — | — |
| `token` | `string` | нет / не отмечено | — | — | — |
| `cost_auto` | `boolean` | нет / не отмечено | false | — | — |
| `parameters` | `object[SourceParameters]` | нет / не отмечено | — | — | — |
| `postbacks` | `array` | нет / не отмечено | — | — | — |
| `notes` | `string` | нет / не отмечено | — | — | — |
| `created_at` | `string` | нет / не отмечено | — | — | — |
| `updated_at` | `string` | нет / не отмечено | — | — | — |

### `CampaignCostRequest`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `start_date` | `string` | да | — | — | Start date and time. For example, "2017-09-10                                                                         20:10" |
| `end_date` | `string` | да | — | — | End date and time. For example, "2017-09-10                                                                         20:10" |
| `timezone` | `string` | да | — | — | Timezone for the time range. For example,                                                                         "Europe/Madrid". |
| `cost` | `string` | да | — | — | Cost for the time range. For example, "19.22". |
| `currency` | `string` | да | — | — | Currency of cost. For example "EUR". |
| `only_campaign_uniques` | `boolean` | нет / не отмечено | — | — | Apply new costs to unique clicks only. |
| `filters` | `object[FilterCostRequest]` | нет / не отмечено | — | — | — |

### `CampaignCreateRequired`

В сохранённом HTML для этой модели не отображены свойства (пустая таблица полей).

### `CampaignRequest`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `alias` | `string` | нет / не отмечено | — | — | Campaign Alias which is Used in URL                                                                         http://domain.com/ALIAS |
| `type` | `string` | нет / не отмечено | position | Array                                                                             [ 2 ] | Flow Rotation Type |
| `name` | `string` | нет / не отмечено | — | — | Campaign Name |
| `cookies_ttl` | `integer` | нет / не отмечено | 24 | — | When the Click Gets Unique Status Again, in Hours |
| `state` | `string` | нет / не отмечено | active | Array                                                                             [ 3 ] | Campaign State |
| `cost_type` | `string` | нет / не отмечено | CPC | Array                                                                             [ 3 ] | Cost Type |
| `cost_value` | `number` | нет / не отмечено | — | — | Cost Value |
| `cost_currency` | `string` | нет / не отмечено | — | — | Currency Value EUR/USD/RUB/UAH/GBP. Default Value                                                                         is Taken from the Tracker's Settings. |
| `cost_auto` | `boolean` | нет / не отмечено | false | — | Enable Automatic Costs (0/1) |
| `group_id` | `string` | нет / не отмечено | — | — | Campaign Group ID |
| `bind_visitors` | `string` | нет / не отмечено | — | — | Bind Visitors Feature (null - disabled/ s - only                                                                         to streams/ sl - to streams and LPs/ slo — to                                                                         streams, LPs and offers) |
| `traffic_source_id` | `integer` | нет / не отмечено | — | — | Traffic source ID |
| `parameters` | `object[SourceParameters]` | нет / не отмечено | — | — | — |
| `token` | `string` | нет / не отмечено | — | — | Token to gain access to Click API |
| `domain_id` | `integer` | нет / не отмечено | — | — | Domain ID |
| `postbacks` | `array` | нет / не отмечено | — | — | — |
| `notes` | `string` | нет / не отмечено | — | — | Notes for the campaign |

### `CleanRequest`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `start_date` | `string` | да | — | — | The date and the time for the period to delete,                                                                         e.g. 2017-04-01 10:10 |
| `end_date` | `string` | да | — | — | The date and the time for the period to delete,                                                                         e.g. 2017-04-01 10:10 |
| `campaign_id` | `integer` | нет / не отмечено | — | — | Campaign ID |
| `timezone` | `string` | нет / не отмечено | — | — | Timezone for the dates, e.g., "UTC" or                                                                         "Europe/Madrid" |

### `ClickRequest`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `range` | `object[RangeRequest]` | нет / не отмечено | — | — | — |
| `limit` | `number` | нет / не отмечено | — | — | Clicks Request Limit. Either 'limit' or 'range'                                                                         Parameters are a Must. |
| `offset` | `number` | нет / не отмечено | — | — | Offset rows |
| `columns` | `array` | нет / не отмечено | — | — | — |
| `filters` | `array` | нет / не отмечено | — | — | — |
| `sort` | `array` | нет / не отмечено | — | — | — |

### `ClicksUpdateCostsPayload`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `start_date` | `string` | да | — | — | Start date and time, e.g., “2017-09-10 20:10” |
| `end_date` | `string` | да | — | — | End date and time, e.g., “2017-09-10 20:10” |
| `cost` | `number` | да | — | — | Cost value, e.g., 19.22 |
| `filters` | `object[FilterCostRequest]` | нет / не отмечено | — | — | — |

### `ClicksUpdateCostsRequest`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `campaign_ids` | `array` | да | — | — | — |
| `costs` | `array` | да | — | — | — |
| `timezone` | `string` | нет / не отмечено | — | — | Timezone, e.g., Europe/Madrid |
| `currency` | `string` | нет / не отмечено | — | — | Currency, e.g., EUR |
| `only_campaign_uniques` | `integer` | нет / не отмечено | — | — | Apply costs only to unique clicks (1 or 0) |

### `ConversionRequest`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `range` | `object[RangeRequest]` | нет / не отмечено | — | — | — |
| `limit` | `number` | нет / не отмечено | — | — | Limit result |
| `offset` | `number` | нет / не отмечено | — | — | Offset for results |
| `columns` | `array` | нет / не отмечено | — | — | — |
| `filters` | `array` | нет / не отмечено | — | — | — |
| `sort` | `array` | нет / не отмечено | — | — | — |

### `Domain`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `id` | `integer` | нет / не отмечено | — | — | — |
| `name` | `string` | нет / не отмечено | — | — | — |
| `network_status` | `string` | нет / не отмечено | — | — | — |
| `default_campaign` | `string` | нет / не отмечено | — | — | — |
| `default_campaign_id` | `integer` | нет / не отмечено | — | — | — |
| `state` | `string` | нет / не отмечено | active | Array                                                                             [ 2 ] | — |
| `created_at` | `string` | нет / не отмечено | — | — | — |
| `updated_at` | `string` | нет / не отмечено | — | — | — |
| `catch_not_found` | `boolean` | нет / не отмечено | — | — | — |
| `campaigns_count` | `integer` | нет / не отмечено | — | — | — |
| `ssl_redirect` | `boolean` | нет / не отмечено | — | — | — |
| `allow_indexing` | `boolean` | нет / не отмечено | — | — | — |
| `admin_dashboard` | `boolean` | нет / не отмечено | — | — | — |
| `cloudflare_proxy` | `boolean` | нет / не отмечено | — | — | — |
| `group_id` | `integer` | нет / не отмечено | — | — | — |
| `group` | `string` | нет / не отмечено | — | — | — |
| `is_ssl` | `boolean` | нет / не отмечено | — | — | — |
| `dns_provider` | `string` | нет / не отмечено | — | — | — |
| `error_solution` | `string` | нет / не отмечено | — | — | — |
| `status` | `string` | нет / не отмечено | — | — | — |
| `notes` | `string` | нет / не отмечено | — | — | — |

### `DomainCreateRequired`

В сохранённом HTML для этой модели не отображены свойства (пустая таблица полей).

### `DomainRegister`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `registrar` | `string` | нет / не отмечено | — | — | — |
| `external_id` | `integer` | нет / не отмечено | — | — | — |

### `DomainRequest`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `name` | `string` | нет / не отмечено | — | — | Domain name |
| `default_campaign_id` | `integer` | нет / не отмечено | — | — | Run campaign on the domain |
| `group_id` | `string` | нет / не отмечено | — | — | Group ID |
| `catch_not_found` | `boolean` | нет / не отмечено | false | — | Catch the traffic of non-existent URLs |
| `notes` | `string` | нет / не отмечено | — | — | Notes for the domain |
| `ssl_redirect` | `boolean` | нет / не отмечено | false | — | Force browsers to redirect from HTTP to HTTPS |
| `allow_indexing` | `boolean` | нет / не отмечено | true | — | Allow robots to index the domain content |
| `admin_dashboard` | `boolean` | нет / не отмечено | false | — | Allow access to admin dashboard |

### `EditorFiles`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `name` | `string` | нет / не отмечено | — | — | — |
| `type` | `string` | нет / не отмечено | — | — | — |
| `ext` | `string` | нет / не отмечено | — | — | — |
| `path` | `string` | нет / не отмечено | — | — | — |
| `children` | `array` | нет / не отмечено | — | — | — |

### `Error`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `error` | `string` | да | — | — | — |

### `Facebook`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `id` | `integer` | нет / не отмечено | — | — | Intergration ID |
| `integration` | `string` | нет / не отмечено | — | — | The integration name |
| `proxy_enabled` | `boolean` | нет / не отмечено | — | — | Use proxy |
| `name` | `string` | нет / не отмечено | — | — | The integration name |
| `ad_account_id` | `string` | нет / не отмечено | — | — | Facebook account ID |
| `token` | `string` | нет / не отмечено | — | — | Facebook token |
| `last_error` | `string` | нет / не отмечено | — | — | Last error |
| `last_raw_error` | `string` | нет / не отмечено | — | — | Error message from facebook |
| `proxy` | `object` | нет / не отмечено | — | Array                                                                                                         [ 3 ] | Protocol |

### `FacebookRequest`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `name` | `string` | нет / не отмечено | — | — | The integration name |
| `ad_account_id` | `string` | нет / не отмечено | — | — | Facebook account ID |
| `token` | `string` | нет / не отмечено | — | — | Facebook yoken |
| `proxy_enabled` | `boolean` | нет / не отмечено | — | — | Use proxy to connect |
| `proxy` | `object` | нет / не отмечено | — | [ http,                                                                                                     https,                                                                                                     socks5 ] | Protocol |

### `Filter`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `id` | `integer` | нет / не отмечено | — | — | — |
| `stream_id` | `integer` | нет / не отмечено | — | — | — |
| `name` | `string` | нет / не отмечено | — | — | — |
| `mode` | `string` | нет / не отмечено | — | — | — |
| `payload` | `string` | нет / не отмечено | — | — | — |
| `oid` | `string` | нет / не отмечено | — | — | — |

### `FilterCostRequest`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `description:` | `не указан` | нет / не отмечено | — | — | Send a key-value object to apply filters to clicks. For                                                                 example, {"sub_id_1": "1,2,3", "source": "site.ru"}. |
| `keyword` | `string` | нет / не отмечено | — | — | — |
| `external_id` | `string` | нет / не отмечено | — | — | — |
| `creative_id` | `string` | нет / не отмечено | — | — | — |
| `ad_campaign_id` | `string` | нет / не отмечено | — | — | — |
| `source` | `string` | нет / не отмечено | — | — | — |
| `sub_id_1` | `string` | нет / не отмечено | — | — | — |
| `sub_id_2` | `string` | нет / не отмечено | — | — | — |
| `sub_id_3` | `string` | нет / не отмечено | — | — | — |
| `sub_id_4` | `string` | нет / не отмечено | — | — | — |
| `sub_id_5` | `string` | нет / не отмечено | — | — | — |
| `sub_id_6` | `string` | нет / не отмечено | — | — | — |
| `sub_id_7` | `string` | нет / не отмечено | — | — | — |
| `sub_id_8` | `string` | нет / не отмечено | — | — | — |
| `sub_id_9` | `string` | нет / не отмечено | — | — | — |
| `sub_id_10` | `string` | нет / не отмечено | — | — | — |
| `sub_id_11` | `string` | нет / не отмечено | — | — | — |
| `sub_id_12` | `string` | нет / не отмечено | — | — | — |
| `sub_id_13` | `string` | нет / не отмечено | — | — | — |
| `sub_id_14` | `string` | нет / не отмечено | — | — | — |
| `sub_id_15` | `string` | нет / не отмечено | — | — | — |
| `sub_id_16` | `string` | нет / не отмечено | — | — | — |
| `sub_id_17` | `string` | нет / не отмечено | — | — | — |
| `sub_id_18` | `string` | нет / не отмечено | — | — | — |
| `sub_id_19` | `string` | нет / не отмечено | — | — | — |
| `sub_id_20` | `string` | нет / не отмечено | — | — | — |
| `sub_id_21` | `string` | нет / не отмечено | — | — | — |
| `sub_id_22` | `string` | нет / не отмечено | — | — | — |
| `sub_id_23` | `string` | нет / не отмечено | — | — | — |
| `sub_id_24` | `string` | нет / не отмечено | — | — | — |
| `sub_id_25` | `string` | нет / не отмечено | — | — | — |
| `sub_id_26` | `string` | нет / не отмечено | — | — | — |
| `sub_id_27` | `string` | нет / не отмечено | — | — | — |
| `sub_id_28` | `string` | нет / не отмечено | — | — | — |
| `sub_id_29` | `string` | нет / не отмечено | — | — | — |
| `sub_id_30` | `string` | нет / не отмечено | — | — | — |

### `FilterRequest`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `name` | `string` | да | — | — | Name of the field |
| `operator` | `string` | да | — | — | One of the available operators ( operators ) |
| `expression` | `object` | нет / не отмечено | — | — | Expression for the filter |

### `FilterStreamRequest`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `id` | `integer` | нет / не отмечено | — | — | Flow filter ID. Provide it if you update the                                                                         filter. |
| `name` | `string` | да | — | — | Flow filter name, see 'retrive-stream-filters'                                                                         section |
| `mode` | `string` | да | — | [ accept,                                                                         reject ] | Filter mode |
| `payload` | `array` | нет / не отмечено | — | — | Flow payload. This field contains values for                                                                         filters. For example, for a "keyword" Filter an                                                                         Array ["value1", "value2"] must be provided |

### `Group`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `id` | `integer` | нет / не отмечено | — | — | — |
| `name` | `string` | нет / не отмечено | — | — | — |
| `position` | `integer` | нет / не отмечено | — | — | — |
| `type` | `string` | нет / не отмечено | — | — | — |

### `GroupCreateRequired`

В сохранённом HTML для этой модели не отображены свойства (пустая таблица полей).

### `GroupRequest`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `name` | `string` | нет / не отмечено | — | — | Group name |
| `type` | `string` | нет / не отмечено | — | [ campaigns,                                                                         offers, landings,                                                                         domains ] | Group type |

### `LabelRequestPost`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `campaign_id` | `integer` | да | — | — | Campaign ID |
| `ref_name` | `string` | да | — | — | List of available ref                                                                     names: ip source ad_campaign_id creative_id keyword ad_campaign_idn sub_id_1..10 |
| `items` | `object` | да | — | — | An Object like a                                                                                                     {"value":"blacklist"} |

### `Labels`

В сохранённом HTML для этой модели не отображены свойства (пустая таблица полей).

### `Landing`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `id` | `integer` | нет / не отмечено | — | — | — |
| `landing_type` | `string` | нет / не отмечено | — | — | — |
| `action_type` | `string` | нет / не отмечено | — | — | — |
| `action_payload` | `object` | нет / не отмечено | — | — | — |
| `action_options` | `object` | нет / не отмечено | — | — | — |
| `name` | `string` | нет / не отмечено | — | — | — |
| `group_id` | `integer` | нет / не отмечено | — | — | — |
| `offer_count` | `integer` | нет / не отмечено | — | — | — |
| `notes` | `string` | нет / не отмечено | — | — | — |
| `state` | `string` | нет / не отмечено | — | — | — |
| `created_at` | `string` | нет / не отмечено | — | — | — |
| `updated_at` | `string` | нет / не отмечено | — | — | — |
| `archive` | `string` | нет / не отмечено | — | — | — |
| `local_path` | `string` | нет / не отмечено | — | — | — |
| `preview_path` | `string` | нет / не отмечено | — | — | — |

### `LandingCreateRequired`

В сохранённом HTML для этой модели не отображены свойства (пустая таблица полей).

### `LandingRequest`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `name` | `string` | нет / не отмечено | — | — | Landing page name |
| `action_payload` | `object` | нет / не отмечено | — | — | — |
| `group_id` | `string` | нет / не отмечено | — | — | Group ID |
| `state` | `string` | нет / не отмечено | active | Array                                                                             [ 3 ] | — |
| `landing_type` | `string` | нет / не отмечено | local | Array                                                                             [ 4 ] | Landing page type |
| `action_type` | `string` | нет / не отмечено | local_file | Array                                                                             [ 6 ] | Action type |
| `url` | `string` | нет / не отмечено | — | — | URL |
| `archive` | `string` | нет / не отмечено | — | — | ZIP-file encoded to base64. |
| `notes` | `string` | нет / не отмечено | — | — | Notes |

### `LandingStream`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `id` | `integer` | нет / не отмечено | — | — | — |
| `stream_id` | `integer` | нет / не отмечено | — | — | — |
| `landing_id` | `integer` | нет / не отмечено | — | — | — |
| `state` | `string` | нет / не отмечено | — | — | — |
| `share` | `integer` | нет / не отмечено | — | — | — |
| `created_at` | `string` | нет / не отмечено | — | — | — |
| `updated_at` | `string` | нет / не отмечено | — | — | — |

### `LandingStreamRequest`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `landing_id` | `integer` | да | — | — | Landing Page ID |
| `share` | `integer` | да | — | — | Share among others |
| `state` | `string` | нет / не отмечено | — | [ active,                                                                         disabled ] | — |

### `Logs`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `datetime` | `string` | нет / не отмечено | — | — | — |
| `jid` | `string` | нет / не отмечено | — | — | — |
| `message` | `string` | нет / не отмечено | — | — | — |

### `Offer`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `id` | `integer` | нет / не отмечено | — | — | — |
| `name` | `string` | нет / не отмечено | — | — | — |
| `group_id` | `integer` | нет / не отмечено | — | — | — |
| `action_type` | `string` | нет / не отмечено | — | — | — |
| `action_payload` | `object` | нет / не отмечено | — | — | — |
| `action_options` | `object` | нет / не отмечено | — | — | — |
| `affiliate_network_id` | `integer` | нет / не отмечено | — | — | — |
| `payout_value` | `number` | нет / не отмечено | — | — | — |
| `payout_currency` | `string` | нет / не отмечено | — | — | — |
| `payout_type` | `string` | нет / не отмечено | — | — | — |
| `state` | `string` | нет / не отмечено | — | — | — |
| `created_at` | `string` | нет / не отмечено | — | — | — |
| `updated_at` | `string` | нет / не отмечено | — | — | — |
| `payout_auto` | `boolean` | нет / не отмечено | — | — | — |
| `payout_upsell` | `boolean` | нет / не отмечено | — | — | — |
| `country` | `array` | нет / не отмечено | — | — | — |
| `notes` | `string` | нет / не отмечено | — | — | — |
| `affiliate_network` | `string` | нет / не отмечено | — | — | — |
| `archive` | `string` | нет / не отмечено | — | — | — |
| `local_path` | `string` | нет / не отмечено | — | — | — |
| `preview_path` | `string` | нет / не отмечено | — | — | — |
| `values` | `array` | нет / не отмечено | — | — | — |

### `OfferCreateRequired`

В сохранённом HTML для этой модели не отображены свойства (пустая таблица полей).

### `OfferRequest`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `name` | `string` | нет / не отмечено | — | — | Offer name |
| `group_id` | `integer` | нет / не отмечено | — | — | Offer group ID |
| `offer_type` | `string` | нет / не отмечено | — | — | Offer Type                                                                         ('local'/'external'/'preloaded'/'action') |
| `action_type` | `string` | нет / не отмечено | — | — | Action or redirect type |
| `action_payload` | `object` | нет / не отмечено | — | — | — |
| `affiliate_network_id` | `integer` | нет / не отмечено | — | — | Affiliate network ID |
| `payout_value` | `number` | нет / не отмечено | — | — | Payout value |
| `payout_currency` | `string` | нет / не отмечено | — | — | Payout currency |
| `payout_type` | `string` | нет / не отмечено | — | Array                                                                             [ 2 ] | Payout type |
| `state` | `string` | нет / не отмечено | active | Array                                                                             [ 2 ] | Offer State |
| `payout_auto` | `boolean` | нет / не отмечено | false | — | If true, offer receives payout value from                                                                         postback |
| `payout_upsell` | `boolean` | нет / не отмечено | false | — | Allow offer to get upsells |
| `country` | `array` | нет / не отмечено | — | — | — |
| `notes` | `string` | нет / не отмечено | — | — | Notes |
| `archive` | `string` | нет / не отмечено | — | — | ZIP-file encoded to base64 |
| `conversion_cap_enabled` | `boolean` | нет / не отмечено | false | — | Turn on that feature if the offer limit                                                                         conversions per day |
| `daily_cap` | `number` | нет / не отмечено | — | — | Daily limit of conversions, after which the                                                                         tracker will send traffic to another offer |
| `conversion_timezone` | `string` | нет / не отмечено | — | — | Which timezone is being used by the Affiliate                                                                         network for calculating conversions, e.g. UTC or                                                                         Europe/Madrid |
| `alternative_offer_id` | `number` | нет / не отмечено | — | — | Offer id, where to send traffic when daily limit                                                                         is reached |

### `OfferStream`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `id` | `integer` | нет / не отмечено | — | — | — |
| `stream_id` | `integer` | нет / не отмечено | — | — | — |
| `offer_id` | `integer` | нет / не отмечено | — | — | — |
| `state` | `string` | нет / не отмечено | — | — | — |
| `share` | `integer` | нет / не отмечено | — | — | — |
| `created_at` | `string` | нет / не отмечено | — | — | — |
| `updated_at` | `string` | нет / не отмечено | — | — | — |

### `OfferStreamRequest`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `offer_id` | `integer` | да | — | — | Offer ID |
| `share` | `integer` | да | — | — | Percentage of Traffic Sent to This Offer |
| `state` | `string` | нет / не отмечено | — | [ active,                                                                         disabled ] | — |

### `OptionNumber`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `name` | `string` | да | — | — | — |
| `value` | `number` | да | — | — | — |

### `PlaceholderObject`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `name` | `string` | нет / не отмечено | — | — | — |
| `placeholder` | `string` | нет / не отмечено | — | — | — |
| `alias` | `string` | нет / не отмечено | — | — | — |

### `RangeRequest`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `from` | `string` | нет / не отмечено | — | — | Start Date, e.g., '2017-09-10' |
| `to` | `string` | нет / не отмечено | — | — | End Date, e.g., '2017-09-10' |
| `timezone` | `string` | нет / не отмечено | — | — | E.g., Europe/Madrid |
| `interval` | `object` | нет / не отмечено | — | — | One of the intervals can be                                                                                             used: today, yesterday,                                                                                             7_days_ago,                                                                                             first_day_of_this_week,                                                                                             1_month_ago,                                                                                             first_day_of_this_month,                                                                                             1_year_ago,                                                                                             first_day_of_this_year,                                                                                             all_time |

### `Report`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `rows` | `array` | нет / не отмечено | — | — | — |
| `total` | `integer` | нет / не отмечено | — | — | — |
| `meta` | `array` | нет / не отмечено | — | — | — |

### `ReportsRequest`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `range` | `object[RangeRequest]` | нет / не отмечено | — | — | — |
| `dimensions` | `array` | нет / не отмечено | — | — | — |
| `measures` | `array` | нет / не отмечено | — | — | — |
| `filters` | `array[FilterRequest]` | нет / не отмечено | — | — | Filters can contain OR and AND logical operators. |
| `sort` | `array[SortRequest]` | нет / не отмечено | — | [ ASC,                                                                                                                 DESC ] | Column or                                                                                                                 metric                                                                                                                 name |

### `S2SPostback`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `campaign_id` | `integer` | нет / не отмечено | — | — | Campaign ID |
| `id` | `integer` | нет / не отмечено | — | — | Postback ID |
| `method` | `string` | нет / не отмечено | — | [ GET,                                                                         POST ] | Request method |
| `statuses` | `array` | нет / не отмечено | — | [ lead,                                                                                     sale, rejected,                                                                                     rebill ] | Conversion status |
| `url` | `string` | нет / не отмечено | — | — | Postback URL |

### `SortRequest`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `name` | `string` | да | — | — | Column or metric name |
| `order` | `string` | да | — | [ ASC,                                                                         DESC ] | Order |

### `Source`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `id` | `integer` | нет / не отмечено | — | — | — |
| `name` | `string` | нет / не отмечено | — | — | — |
| `postback_url` | `string` | нет / не отмечено | — | — | — |
| `postback_statuses` | `array` | нет / не отмечено | — | — | — |
| `template_name` | `string` | нет / не отмечено | — | — | — |
| `accept_parameters` | `boolean` | нет / не отмечено | — | — | — |
| `parameters` | `object[SourceParameters]` | нет / не отмечено | — | — | — |
| `notes` | `string` | нет / не отмечено | — | — | — |
| `state` | `string` | нет / не отмечено | — | — | — |
| `created_at` | `string` | нет / не отмечено | — | — | — |
| `updated_at` | `string` | нет / не отмечено | — | — | — |
| `traffic_loss` | `number` | нет / не отмечено | — | — | — |
| `update_in_campaigns` | `string` | нет / не отмечено | — | — | — |

### `SourceParameters`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `keyword` | `object[PlaceholderObject]` | нет / не отмечено | — | — | — |
| `cost` | `object[PlaceholderObject]` | нет / не отмечено | — | — | — |
| `currency` | `object[PlaceholderObject]` | нет / не отмечено | — | — | — |
| `external_id` | `object[PlaceholderObject]` | нет / не отмечено | — | — | — |
| `creative_id` | `object[PlaceholderObject]` | нет / не отмечено | — | — | — |
| `ad_campaign_id` | `object[PlaceholderObject]` | нет / не отмечено | — | — | — |
| `source` | `object[PlaceholderObject]` | нет / не отмечено | — | — | — |
| `sub_id_1` | `object[PlaceholderObject]` | нет / не отмечено | — | — | — |
| `sub_id_2` | `object[PlaceholderObject]` | нет / не отмечено | — | — | — |
| `sub_id_3` | `object[PlaceholderObject]` | нет / не отмечено | — | — | — |
| `sub_id_4` | `object[PlaceholderObject]` | нет / не отмечено | — | — | — |
| `sub_id_5` | `object[PlaceholderObject]` | нет / не отмечено | — | — | — |
| `sub_id_6` | `object[PlaceholderObject]` | нет / не отмечено | — | — | — |
| `sub_id_7` | `object[PlaceholderObject]` | нет / не отмечено | — | — | — |
| `sub_id_8` | `object[PlaceholderObject]` | нет / не отмечено | — | — | — |
| `sub_id_9` | `object[PlaceholderObject]` | нет / не отмечено | — | — | — |
| `sub_id_10` | `object[PlaceholderObject]` | нет / не отмечено | — | — | — |
| `sub_id_11` | `object[PlaceholderObject]` | нет / не отмечено | — | — | — |
| `sub_id_12` | `object[PlaceholderObject]` | нет / не отмечено | — | — | — |
| `sub_id_13` | `object[PlaceholderObject]` | нет / не отмечено | — | — | — |
| `sub_id_14` | `object[PlaceholderObject]` | нет / не отмечено | — | — | — |
| `sub_id_15` | `object[PlaceholderObject]` | нет / не отмечено | — | — | — |

### `SourceRequest`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `name` | `string` | нет / не отмечено | — | — | — |
| `postback_url` | `string` | нет / не отмечено | — | — | — |
| `postback_statuses` | `array` | нет / не отмечено | — | — | — |
| `template_name` | `string` | нет / не отмечено | — | — | — |
| `accept_parameters` | `boolean` | нет / не отмечено | — | — | — |
| `parameters` | `object[SourceParameters]` | нет / не отмечено | — | — | — |
| `notes` | `string` | нет / не отмечено | — | — | — |
| `state` | `string` | нет / не отмечено | — | — | — |
| `traffic_loss` | `number` | нет / не отмечено | — | — | — |

### `Stream`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `id` | `integer` | нет / не отмечено | — | — | — |
| `type` | `string` | нет / не отмечено | — | — | — |
| `name` | `string` | нет / не отмечено | — | — | — |
| `campaign_id` | `integer` | нет / не отмечено | — | — | — |
| `position` | `integer` | нет / не отмечено | — | — | — |
| `weight` | `number` | нет / не отмечено | — | — | — |
| `action_options` | `object` | нет / не отмечено | — | — | — |
| `comments` | `string` | нет / не отмечено | — | — | — |
| `state` | `string` | нет / не отмечено | — | — | — |
| `updated_at` | `string` | нет / не отмечено | — | — | — |
| `action_type` | `string` | нет / не отмечено | — | — | — |
| `action_payload` | `object` | нет / не отмечено | — | — | — |
| `schema` | `string` | нет / не отмечено | — | — | — |
| `collect_clicks` | `boolean` | нет / не отмечено | — | — | — |
| `filter_or` | `boolean` | нет / не отмечено | — | — | — |
| `filters` | `array[Filter]` | нет / не отмечено | — | — | — |
| `triggers` | `array[Trigger]` | нет / не отмечено | — | — | — |
| `landings` | `array[LandingStream]` | нет / не отмечено | — | — | — |
| `offers` | `array[OfferStream]` | нет / не отмечено | — | — | — |
| `offer_selection` | `string` | нет / не отмечено | before_click | [ before_click,                                                                         after_click ] | — |

### `StreamAction`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `key` | `string` | нет / не отмечено | — | — | — |
| `name` | `string` | нет / не отмечено | — | — | — |
| `field` | `string` | нет / не отмечено | — | — | — |
| `type` | `string` | нет / не отмечено | — | — | — |
| `description` | `string` | нет / не отмечено | — | — | — |

### `StreamFilter`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `value` | `string` | нет / не отмечено | — | — | Filter Name |
| `tooltip` | `string` | нет / не отмечено | — | — | Filter Description |
| `modes` | `object` | нет / не отмечено | — | — | Accept mode |
| `group` | `string` | нет / не отмечено | — | — | Group ID. It's used to group filters in a filters                                                                         dropdown menu. |
| `template` | `string` | нет / не отмечено | — | — | HTML code for rendering filter body view (Not                                                                         recommended to use) |
| `header_template` | `string` | нет / не отмечено | — | — | HTML code for rendering filter body view (Not                                                                         recommended to use) |
| `defaults` | `string` | нет / не отмечено | — | — | Default values |

### `StreamObject`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `campaign_id` | `integer` | нет / не отмечено | — | — | Campaign ID |
| `type` | `string` | нет / не отмечено | — | [ forced,                                                                         regular,                                                                         default ] | Flow type |
| `name` | `string` | нет / не отмечено | — | — | Flow name |
| `position` | `integer` | нет / не отмечено | — | — | Position of a flow among other flows. |
| `weight` | `number` | нет / не отмечено | — | — | Flow weight. |
| `action_options` | `object` | нет / не отмечено | — | — | Action options. |
| `comments` | `string` | нет / не отмечено | — | — | Comments or notes for the flow |
| `state` | `string` | нет / не отмечено | active | [ active,                                                                         disabled,                                                                         deleted ] | State of the flow |
| `action_type` | `string` | нет / не отмечено | — | — | Action to perform (see 'Retrieve available flow                                                                         action types') |
| `schema` | `string` | нет / не отмечено | — | [ landings,                                                                         redirect,                                                                         action ] | — |
| `collect_clicks` | `boolean` | нет / не отмечено | false | — | Flow saves clicks (true/false) |
| `filter_or` | `boolean` | нет / не отмечено | false | — | Use 'OR' operator between filters |
| `filters` | `array[FilterStreamRequest]` | нет / не отмечено | — | [ accept,                                                                                                                 reject ] | Flow                                                                                                                 filter                                                                                                                 ID.                                                                                                                 Provide                                                                                                                 it if                                                                                                                 you                                                                                                                 update                                                                                                                 the                                                                                                                 filter. |
| `triggers` | `array[TriggersStreamRequest]` | нет / не отмечено | — | [ not_respond,                                                                                                                 always,                                                                                                                 not_contains,                                                                                                                 av_detected ] | Trigger                                                                                                                 ID. |
| `landings` | `array[LandingStreamRequest]` | нет / не отмечено | — | [ active,                                                                                                                 disabled ] | Landing                                                                                                                 Page ID |
| `offers` | `array[OfferStreamRequest]` | нет / не отмечено | — | [ active,                                                                                                                 disabled ] | Offer ID |

### `StreamRequest`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `campaign_id` | `integer` | да | — | — | Campaign ID |
| `type` | `string` | да | — | [ forced,                                                                         regular,                                                                         default ] | Flow type |
| `name` | `string` | да | — | — | Flow name |
| `position` | `integer` | нет / не отмечено | — | — | Position of a flow among other flows. |
| `weight` | `number` | нет / не отмечено | — | — | Flow weight. |
| `action_options` | `object` | нет / не отмечено | — | — | Action options. |
| `comments` | `string` | нет / не отмечено | — | — | Comments or notes for the flow |
| `state` | `string` | нет / не отмечено | active | [ active,                                                                         disabled,                                                                         deleted ] | State of the flow |
| `action_type` | `string` | да | — | — | Action to perform (see 'Retrieve available flow                                                                         action types') |
| `schema` | `string` | да | — | [ landings,                                                                         redirect,                                                                         action ] | — |
| `collect_clicks` | `boolean` | нет / не отмечено | false | — | Flow saves clicks (true/false) |
| `filter_or` | `boolean` | нет / не отмечено | false | — | Use 'OR' operator between filters |
| `filters` | `array[FilterStreamRequest]` | нет / не отмечено | — | [ accept,                                                                                                                 reject ] | Flow                                                                                                                 filter                                                                                                                 ID.                                                                                                                 Provide                                                                                                                 it if                                                                                                                 you                                                                                                                 update                                                                                                                 the                                                                                                                 filter. |
| `triggers` | `array[TriggersStreamRequest]` | нет / не отмечено | — | [ not_respond,                                                                                                                 always,                                                                                                                 not_contains,                                                                                                                 av_detected ] | Trigger                                                                                                                 ID. |
| `landings` | `array[LandingStreamRequest]` | нет / не отмечено | — | [ active,                                                                                                                 disabled ] | Landing                                                                                                                 Page ID |
| `offers` | `array[OfferStreamRequest]` | нет / не отмечено | — | [ active,                                                                                                                 disabled ] | Offer ID |

### `StreamRequestPut`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `campaign_id` | `integer` | нет / не отмечено | — | — | Campaign ID |
| `type` | `string` | нет / не отмечено | — | [ forced,                                                                         regular,                                                                         default ] | Flow type |
| `name` | `string` | нет / не отмечено | — | — | Flow name |
| `position` | `integer` | нет / не отмечено | — | — | Position of a flow among other flows. |
| `weight` | `number` | нет / не отмечено | — | — | Flow weight. |
| `action_options` | `object` | нет / не отмечено | — | — | Action options. |
| `comments` | `string` | нет / не отмечено | — | — | Comments or notes for the flow |
| `state` | `string` | нет / не отмечено | active | [ active,                                                                         disabled,                                                                         deleted ] | State of the flow |
| `action_type` | `string` | нет / не отмечено | — | — | Action to perform (see 'Retrieve available flow                                                                         action types') |
| `schema` | `string` | нет / не отмечено | — | [ landings,                                                                         redirect,                                                                         action ] | — |
| `collect_clicks` | `boolean` | нет / не отмечено | false | — | Flow saves clicks (true/false) |
| `filter_or` | `boolean` | нет / не отмечено | false | — | Use 'OR' operator between filters |
| `filters` | `array[FilterStreamRequest]` | нет / не отмечено | — | [ accept,                                                                                                                 reject ] | Flow                                                                                                                 filter                                                                                                                 ID.                                                                                                                 Provide                                                                                                                 it if                                                                                                                 you                                                                                                                 update                                                                                                                 the                                                                                                                 filter. |
| `triggers` | `array[TriggersStreamRequest]` | нет / не отмечено | — | [ not_respond,                                                                                                                 always,                                                                                                                 not_contains,                                                                                                                 av_detected ] | Trigger                                                                                                                 ID. |
| `landings` | `array[LandingStreamRequest]` | нет / не отмечено | — | [ active,                                                                                                                 disabled ] | Landing                                                                                                                 Page ID |
| `offers` | `array[OfferStreamRequest]` | нет / не отмечено | — | [ active,                                                                                                                 disabled ] | Offer ID |

### `Success`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `success` | `boolean` | нет / не отмечено | — | — | — |

### `Time`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `date` | `string` | нет / не отмечено | — | — | — |
| `timezone_type` | `integer` | нет / не отмечено | — | — | — |
| `timezone` | `string` | нет / не отмечено | — | — | — |

### `Trigger`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `id` | `integer` | нет / не отмечено | — | — | — |
| `oid` | `integer` | нет / не отмечено | — | — | — |
| `stream_id` | `integer` | нет / не отмечено | — | — | — |
| `taget` | `string` | нет / не отмечено | — | — | — |
| `condition` | `string` | нет / не отмечено | — | — | — |
| `selected_page` | `string` | нет / не отмечено | — | — | — |
| `pattern` | `string` | нет / не отмечено | — | — | — |
| `action` | `string` | нет / не отмечено | — | — | — |
| `interval` | `integer` | нет / не отмечено | — | — | — |
| `next_run_at` | `integer` | нет / не отмечено | — | — | — |
| `alternative_urls` | `string` | нет / не отмечено | — | — | — |
| `grab_from_page` | `string` | нет / не отмечено | — | — | — |
| `av_settings` | `string` | нет / не отмечено | — | — | — |
| `reverse` | `boolean` | нет / не отмечено | — | — | — |
| `enabled` | `boolean` | нет / не отмечено | — | — | — |
| `scan_page` | `boolean` | нет / не отмечено | — | — | — |

### `TriggersStreamRequest`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `id` | `integer` | нет / не отмечено | — | — | Trigger ID. |
| `stream_id` | `integer` | да | — | — | Flow ID |
| `condition` | `string` | да | — | [ not_respond,                                                                         always, not_contains,                                                                         av_detected ] | Condition |
| `target` | `string` | да | — | [ stream,                                                                         landings, offers,                                                                         selected_page ] | Target |
| `selected_page` | `string` | нет / не отмечено | — | — | The URL of the Page to Check |
| `pattern` | `string` | нет / не отмечено | — | — | Text Pattern to Check |
| `action` | `string` | да | — | [ disable,                                                                         replace_url,                                                                         grab_from_page ] | Action |
| `interval` | `integer` | нет / не отмечено | — | — | Interval between Checks |
| `alternative_urls` | `string` | нет / не отмечено | — | — | URLs for replacement (split by \n) |
| `grab_from_page` | `string` | нет / не отмечено | — | — | URL of the page that contains a new URL |
| `av_settings` | `string` | нет / не отмечено | — | — | Settings for AV Scanners |
| `reverse` | `boolean` | нет / не отмечено | — | — | Perform also in a reverse mode (true/false) |
| `scan_page` | `boolean` | нет / не отмечено | — | — | Tell AV scanner to scan the page content |

### `UnprocessableEntity`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `name` | `string` | да | — | — | — |

### `User`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `id` | `integer` | нет / не отмечено | — | — | User ID |
| `login` | `string` | нет / не отмечено | — | — | User login |
| `type` | `string` | нет / не отмечено | — | [ USER,                                                                         ADMIN ] | User type |
| `access_data` | `object` | нет / не отмечено | — | [ offers,                                                                                                                 landings,                                                                                                                 groups,                                                                                                                 affiliate_networks,                                                                                                                 traffic_sources,                                                                                                                 streams,                                                                                                                 groups,                                                                                                                 domains,                                                                                                                 archive,                                                                                                                 geo_profiles,                                                                                                                 integrations,                                                                                                                 logs,                                                                                                                 geo_dbs,                                                                                                                 campaigns,                                                                                                                 api_keys,                                                                                                                 reports,                                                                                                                 clicks,                                                                                                                 conversions,                                                                                                                 trends,                                                                                                                 cleaner,                                                                                                                 dashboard ] | User access data |
| `preferences` | `object[UserPreferences]` | нет / не отмечено | — | [ ru,                                                                                                     en ] | User language |

### `UserAccessData`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `description:` | `не указан` | нет / не отмечено | — | — | User access data |
| `resources` | `array` | нет / не отмечено | — | [ offers,                                                                                     landings, groups,                                                                                     affiliate_networks, traffic_sources,                                                                                     streams, groups, domains, archive,                                                                                     geo_profiles, integrations, logs,                                                                                     geo_dbs, campaigns, api_keys,                                                                                     reports, clicks, conversions,                                                                                     trends, cleaner,                                                                                     dashboard ] | — |
| `offers_access_type` | `string` | нет / не отмечено | — | [ full_access,                                                                         read_only, to_groups_and_selected,                                                                         created_by_user_groups_and_selected ] | Offers access type |
| `campaigns_access_type` | `string` | нет / не отмечено | — | [ full_access,                                                                         read_only, to_groups_and_selected,                                                                         created_by_user_groups_and_selected ] | Campaigns access type |
| `landings_access_type` | `string` | нет / не отмечено | — | [ full_access,                                                                         read_only, to_groups_and_selected,                                                                         created_by_user_groups_and_selected ] | Landing pages access type |
| `traffic_sources_access_type` | `string` | нет / не отмечено | — | [ full_access,                                                                         read_only, to_groups_and_selected,                                                                         created_by_user_groups_and_selected ] | Traffic sources access type |
| `streams_access_type` | `string` | нет / не отмечено | — | [ full_access,                                                                         read_only, to_groups_and_selected,                                                                         created_by_user_groups_and_selected ] | Flows access type |
| `affiliate_networks_access_type` | `string` | нет / не отмечено | — | [ full_access,                                                                         read_only, to_groups_and_selected,                                                                         created_by_user_groups_and_selected ] | Affiliate networks access type |
| `domains_access_type` | `string` | нет / не отмечено | — | [ full_access,                                                                         read_only, to_groups_and_selected,                                                                         created_by_user_groups_and_selected ] | Domains access type |
| `offers_selected_entities` | `array` | нет / не отмечено | — | — | List of available ID offers |
| `campaigns_selected_entities` | `array` | нет / не отмечено | — | — | List of available ID campaigns |
| `landings_selected_entities` | `array` | нет / не отмечено | — | — | List of available ID landings |
| `traffic_sources_selected_entities` | `array` | нет / не отмечено | — | — | List of available ID traffic sources |
| `affiliate_networks_selected_entities` | `array` | нет / не отмечено | — | — | List of available ID affiliate networks |
| `domains_selected_entities` | `array` | нет / не отмечено | — | — | List of available ID domains |
| `offers_selected_groups` | `array` | нет / не отмечено | — | — | List of available group ID |
| `campaigns_selected_groups` | `array` | нет / не отмечено | — | — | List of available groups ID |
| `landings_selected_groups` | `array` | нет / не отмечено | — | — | List of available groups ID |
| `traffic_sources_selected_groups` | `array` | нет / не отмечено | — | — | List of available groups ID |
| `affiliate_networks_selected_groups` | `array` | нет / не отмечено | — | — | List of available groups ID |
| `domains_selected_groups` | `array` | нет / не отмечено | — | — | List of available group ID |
| `reports` | `array` | нет / не отмечено | — | — | List of fields to which access is restricted |

### `UserPreferences`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `language` | `string` | нет / не отмечено | — | [ ru,                                                                         en ] | User language |
| `timezone` | `string` | нет / не отмечено | — | — | User timezone in UTC, e.g., "Europe/Minsk" |

### `UserRequest`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `login` | `string` | да | — | — | User login |
| `new_password` | `string` | да | — | — | User password |
| `new_password_confirmation` | `string` | да | — | — | Repeat user password |
| `type` | `string` | да | — | [ USER,                                                                         ADMIN ] | User type |
| `preferences` | `object[UserPreferences]` | нет / не отмечено | — | [ ru,                                                                                                     en ] | User language |

### `UserRequestAccess`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `access_data` | `object` | нет / не отмечено | — | [ offers,                                                                                                                 landings,                                                                                                                 groups,                                                                                                                 affiliate_networks,                                                                                                                 traffic_sources,                                                                                                                 streams,                                                                                                                 groups,                                                                                                                 domains,                                                                                                                 archive,                                                                                                                 geo_profiles,                                                                                                                 integrations,                                                                                                                 logs,                                                                                                                 geo_dbs,                                                                                                                 campaigns,                                                                                                                 api_keys,                                                                                                                 reports,                                                                                                                 clicks,                                                                                                                 conversions,                                                                                                                 trends,                                                                                                                 cleaner,                                                                                                                 dashboard ] | User access data |

### `UserRequestUpdate`

| Поле | Тип | Обязательное | По умолчанию | Enum | Описание |
|---|---|:---:|---|---|---|
| `login` | `string` | нет / не отмечено | — | — | User login |
| `new_password` | `string` | нет / не отмечено | — | — | User password |
| `new_password_confirmation` | `string` | нет / не отмечено | — | — | User password repeat |
| `type` | `string` | нет / не отмечено | — | [ USER,                                                                         ADMIN ] | User type |
| `keyCount` | `integer` | нет / не отмечено | — | — | API keys count |
| `preferences` | `object[UserPreferences]` | нет / не отмечено | — | [ ru,                                                                                                     en ] | User language |

## Важные замечания по интерпретации схем
- Отметка «нет / не отмечено» означает только то, что поле не выделено красной звёздочкой в сохранённом Swagger HTML. Это не доказывает, что поле всегда необязательно для конкретного endpoint.
- `CampaignCreateRequired`, `DomainCreateRequired`, `GroupCreateRequired` и другие пустые модели не содержат видимых полей в сохранённом HTML. Возможно, Swagger описывает их через композицию схем или внешние ссылки; эти связи не восстанавливались по догадке.
- У `CampaignRequest` и `Campaign` показаны поля кампании, но это не означает, что все поля `Campaign` принимаются при создании. Для тела `POST /campaigns` следует ориентироваться на схему запроса, а не на модель ответа.
- Для создания потока используется `StreamRequest`; для обновления — `StreamRequestPut`. Это разные модели и наборы обязательных полей.
- Поля `filters`, `triggers`, `landings`, `offers` у потока являются вложенными коллекциями. Их элементы описаны отдельными схемами (`FilterStreamRequest`, `TriggersStreamRequest`, `LandingStreamRequest`, `OfferStreamRequest` и связанными моделями).
- HTML не раскрывает все вложенные схемы и некоторые значения enum (в интерфейсе виден только счётчик элементов). Такие значения намеренно не перечислены.

## Схемы, наиболее важные для сценариев Campaign / Offers

### Создание кампании
Для тела запроса `POST /campaigns` в HTML отображается модель `CampaignRequest`. В ней присутствуют `name`, `alias`, `type`, `cookies_ttl`, `state`, `cost_type`, `cost_value`, `cost_currency`, `cost_auto`, `group_id`, `bind_visitors`, `traffic_source_id`, `parameters`, `token`, `domain_id`, `postbacks`, `notes`. Красными звёздочками эти поля в `CampaignRequest` не отмечены. `Campaign` — модель объекта кампании и дополнительно содержит `id`, `position`, `created_at`, `updated_at`.

### Создание потока
Модель `StreamRequest` помечает обязательными `campaign_id`, `type`, `name`, `action_type` и `schema`. Остальные поля, которые видны в HTML: `position`, `weight`, `action_options`, `comments`, `state`, `collect_clicks`, `filter_or`, `filters`, `triggers`, `landings`, `offers`. Для обновления существует `StreamRequestPut`, где обязательные звёздочки в HTML не отображены.

### Привязка оффера к потоку
Модель `OfferStreamRequest` содержит обязательные `offer_id` (integer) и `share` (integer, процент трафика, направляемого на этот оффер); `state` — строка со значениями enum `active` и `disabled`. Это модель элемента `offers` внутри потока, а не отдельная операция добавления оффера к кампании.

### Получение офферов
Модель ответа `Offer` включает `id`, `name`, `group_id`, `action_type`, `action_payload`, `action_options`, `affiliate_network_id`, `payout_value`, `payout_currency`, `payout_type`, `state`, даты создания/обновления, payout-настройки, `country`, `notes`, данные affiliate network, архивные/локальные пути и `values`. Для создания/обновления оффера используется отдельная модель `OfferRequest`.

