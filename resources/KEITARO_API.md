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
