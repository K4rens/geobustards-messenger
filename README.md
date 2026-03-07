# Geobustards-Messanger — децентрализованный мессенджер без интернета

> **HEX·TEAM** · Nuclear IT Hack 2026 · НИЯУ МИФИ

---

## Что это

Geobustards-Messanger — система децентрализованной связи, которая работает полностью без интернета и центральных серверов. Узлы сами обнаруживают друг друга, строят mesh-сеть и передают сообщения, файлы и голосовые звонки напрямую — через TCP поверх Wi-Fi.

Разработано с нуля за 30 часов хакатона командой из трёх человек.

---

## Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                         MESH NETWORK                            │
│                                                                 │
│   node1 ──────── node2 ──────── node3                           │
│     │               │               │                           │
│   :9000           :9000           :9000    ← TCP mesh           │
│   :9001           :9001           :9001    ← HTTP API           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                ┌────────▼────────┐
                │  backend/media  │
                │    FastAPI      │
                │     :8080       │  ← WebSocket + REST для фронта
                └────────┬────────┘
                         │
                ┌────────▼────────┐
                │    frontend     │
                │   React + Vite  │
                │     :5173       │
                └─────────────────┘
```

**Три независимых слоя:**

- `backend/network` — TCP mesh-нода: transport, flooding, heartbeat, storage, voice
- `backend/media` — FastAPI-мост: polling событий от сети, WebSocket push на фронт
- `frontend` — React UI: чат, список пиров, файлы, звонки

---

## Что реализовано

### Сетевой слой (`backend/network`)

**Transport (TCP)**
- Асинхронный TCP-транспорт на `asyncio.StreamWriter/StreamReader`
- Подключение к известным пирам при старте
- Авто-реконнект при разрыве с cooldown 10 секунд

**Протокол сообщений**
- Типы: `HELLO` | `HEARTBEAT` | `CHAT` | `FILE_CHUNK` | `SIGNAL`
- Каждое сообщение имеет уникальный `id` (UUID4)
- `TTL` по умолчанию 7 хопов

**Flooding с дедупликацией**
- Класс `FloodRouter` — реализация flooding-маршрутизации
- LRU-кэш просмотренных `message_id` с TTL 5 минут
- При форварде передаётся `exclude=from_addr` — отправитель не получает свой пакет обратно
- При `is_local=True` — `on_chat`/`on_file` не вызываются (нет loopback)

**Heartbeat и обнаружение отказов**
- Каждый узел шлёт `HEARTBEAT` с меткой времени каждую секунду
- Пир считается offline если не отвечал > 4 секунд
- RTT считается по разнице timestamp в heartbeat, хранится скользящее среднее 10 последних замеров
- При возврате пира онлайн — автоматически генерируется событие `peer:joined`

**Персистентное хранилище**
- SQLite (`storage/db.py`) — последние 100 сообщений сохраняются на диск
- Тексты хранятся зашифрованными через `Fernet` (симметричный AES-128-CBC + HMAC)
- Ключ задаётся через `STORAGE_KEY` в env-переменных

**Передача файлов**
- Файл режется на чанки по 32 КБ
- Каждый чанк — отдельное `FILE_CHUNK` сообщение с `file_id`, `chunk_index`, `total_chunks`
- SHA-256 хэш всего файла передаётся с первым чанком
- При получении всех чанков — сборка и верификация хэша
- Если хэш не совпал — файл отбрасывается
- Поддержка retry: эндпоинт `/file/{file_id}/request_retry` возвращает список missing chunks
- Ограничение нагрузки: задержка 50 мс между чанками при отправке
- Максимальный размер: 50 МБ на бэкенде, 200 МБ на фронте

**Голосовые звонки (UDP)**
- Класс `VoiceCall` — UDP-транспорт на порту `:9002`
- PCM 16-bit, 16 кГц, моно, frame 60 мс (960 сэмплов)
- Jitter buffer до 10 фреймов вперёд
- Счётчики: `packets_sent`, `packets_received`, `packets_lost`
- Эндпоинт `/call/stats/{call_id}` — live-метрики: loss rate, duration, latency estimate
- Инвайт через SIGNAL-сообщение (`call:invite`) по mesh

**HTTP API (порт :9001)**

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/health` | Статус ноды, количество пиров |
| GET | `/peers` | Все пиры с `online` флагом и `rtt_ms` |
| GET | `/relay` | Текущий relay (никогда не null) |
| POST | `/send` | Отправить chat-сообщение |
| GET | `/messages` | Последние 100 сообщений |
| GET | `/events` | Очередь событий (polling каждые 2 сек) |
| POST | `/send_file` | Отправить файл чанками |
| GET | `/files` | Список полученных файлов |
| GET | `/file/{id}` | Скачать файл |
| GET | `/file/{id}/status` | Статус сборки с missing chunks |
| POST | `/file/{id}/request_retry` | Запросить повтор чанков |
| POST | `/call/start` | Начать звонок |
| POST | `/call/end` | Завершить звонок |
| GET | `/call/stats/{id}` | Метрики звонка |
| POST | `/signal` | Произвольный сигнал |

---

### Медиа-слой (`backend/media`)

- FastAPI на порту `:8080`
- `EventBridge` — polling `/events` у network-ноды каждые 2 секунды
- `WsHub` — broadcast событий всем подключённым WebSocket-клиентам
- Абстракция `NetworkClient` — переключение между real/mock через `USE_MOCK`
- CORS для dev-сервера фронта

**WebSocket события (порт :8080/ws):**

| Тип | Когда |
|-----|-------|
| `peers:update` | Каждые 2 сек — полный список пиров + relay |
| `message:received` | Новое сообщение в сети |
| `peer:joined` | Пир появился |
| `peer:left` | Пир пропал |
| `file:progress` | Прогресс сборки файла |
| `file:received` | Файл собран и верифицирован |

---

### Фронтенд (`frontend`)

- React 18 + TypeScript + Vite
- Tailwind CSS
- Zustand store для состояния
- `useWebSocket` — подключение к WS, авто-реконнект
- `useWebRTC` / `WebRTCContext` — управление звонками
- Компоненты: `PeerList`, `PeerCard`, `ChatWindow`, `MessageInput`, `FileTransfer`, `CallUI`, `RelayBadge`
- Mock-режим для разработки без бэкенда

---

## Тесты

6 unit-тестов для `FloodRouter` (`pytest-asyncio`):

```
test_flood_deduplication         — дубликат не форвардится
test_flood_ttl_decrement         — TTL уменьшается на каждом хопе
test_flood_ttl_zero_drops        — TTL=0 дропает пакет
test_flood_calls_on_chat         — входящий CHAT вызывает on_chat
test_flood_local_no_callback     — is_local=True не вызывает on_chat
test_flood_exclude_sender        — broadcast вызван с exclude=from_addr
```

Запуск:
```bash
cd backend/network
pip install pytest pytest-asyncio
pytest tests/ -v
```

---

## Безопасность

**Шифрование хранилища**
- Все сообщения в SQLite зашифрованы Fernet (AES-128-CBC + HMAC-SHA256)
- Ключ передаётся через `STORAGE_KEY` env-переменную

**Аутентификация узлов**
- При подключении каждый узел отправляет `HELLO` с `node_id`, `name`, `address`
- `node_id` задаётся при деплое в env-переменных

**Защита от петель и спама**
- LRU-дедупликация по `message_id` — один пакет не может пройти через узел дважды
- TTL=7 — максимум 7 хопов, гарантированное затухание

**Модель угроз**
- Защищаемся от: replay-атак (дедупликация), flooding-петель (TTL), случайной утечки сообщений на диске (шифрование хранилища)
- Не защищаемся в данной версии: E2E-шифрование передачи (запланировано)

---

## Запуск

### Docker (рекомендуется)

```bash
cd docker
docker-compose up --build
```

Поднимает 4 mesh-ноды + media API. Фронт запускается отдельно.

### Вручную

```bash
# Нода 1
cd backend/network
pip install -r requirements.txt
NODE_ID=node1 NODE_NAME="Node 1" PORT=9000 API_PORT=9001 \
  PEERS="node2:9000,node3:9000" python main.py

# Media API
cd backend/media
pip install -r requirements.txt
API_PORT=8080 NETWORK_HOST=node1 NETWORK_PORT=9001 python main.py

# Frontend
cd frontend
npm install
npm run dev
```

### Переменные окружения

| Переменная | Где | Описание |
|------------|-----|----------|
| `NODE_ID` | network | ID ноды (node1, node2...) |
| `NODE_NAME` | network | Отображаемое имя |
| `PORT` | network | TCP mesh порт (9000) |
| `API_PORT` | network/media | HTTP API порт |
| `PEERS` | network | Список пиров `host:port,...` |
| `STORAGE_KEY` | network | Fernet-ключ для шифрования БД |
| `DB_PATH` | network | Путь к SQLite файлу |
| `NETWORK_HOST` | media | Хост network-ноды |
| `NETWORK_PORT` | media | Порт API network-ноды |
| `USE_MOCK` | media | `true` — использовать mock вместо реального бэкенда |

---

## Проверка интеграции

```bash
# Healthcheck
curl http://localhost:9001/health
# → {"status":"ok","node_id":"node1","peers_count":3}

# Список пиров с RTT
curl http://localhost:9001/peers
# → [{"peer_id":"node2","name":"Node 2","address":"...","online":true,"rtt_ms":1.4}]

# Relay
curl http://localhost:9001/relay
# → {"peer_id":"node2","name":"Node 2"}

# Отправить сообщение
curl -X POST http://localhost:9001/send \
  -H "Content-Type: application/json" \
  -d '{"to":"broadcast","text":"hello mesh"}'
# → {"message_id":"..."}

# Проверить события
curl http://localhost:9001/events
# → [{"type":"message:received","data":{...}}]
```

---

## Структура репозитория

```
.
├── backend/
│   ├── network/            # TCP mesh-нода (Python/asyncio)
│   │   ├── core/
│   │   │   ├── transport.py    # TCP соединения
│   │   │   ├── node.py         # Управление пирами, heartbeat
│   │   │   └── voice.py        # UDP голосовые звонки
│   │   ├── routing/
│   │   │   └── flooding.py     # Flood-маршрутизация + LRU-дедуп
│   │   ├── storage/
│   │   │   └── db.py           # SQLite + Fernet-шифрование
│   │   ├── api/
│   │   │   └── server.py       # FastAPI, file assembler, события
│   │   └── tests/
│   │       └── test_flooding.py
│   └── media/              # WebSocket-мост (Python/FastAPI)
│       ├── bridge.py           # Polling + WS broadcast
│       ├── ws/hub.py           # WebSocket hub
│       ├── network/client.py   # HTTP-клиент к network API
│       └── api/router.py       # REST эндпоинты для фронта
├── frontend/               # React 18 + TypeScript + Vite
│   └── src/
│       ├── components/     # Chat, PeerList, CallUI, FileTransfer
│       ├── hooks/          # useWebSocket, useWebRTC
│       ├── store/          # Zustand
│       └── api/            # client + mock
└── docker/
    └── docker-compose.yml  # 4 mesh-ноды + media API
```

---

## Команда

**GeoBastards / HEX·TEAM** — НИЯУ МИФИ, 2026

| Участник | Роль | Зона ответственности |
|----------|------|----------------------|
| Афромеев И. А. | Backend Network | TCP transport, flooding, heartbeat, RTT, file chunks, voice UDP, SQLite+Fernet, HTTP API `:9001` |
| Князьков Н. Д. | Backend Media | FastAPI bridge, WebSocket hub, event polling, mock/real client, HTTP API `:8080` |
| Баштовой Н. В. | Frontend | React UI, WebSocket хук, WebRTC контекст, компоненты чата, звонков и файлов |
