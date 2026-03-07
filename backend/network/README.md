# HEX.TEAM — Mesh Network Node

Децентрализованная P2P mesh-сеть: TCP-транспорт, flooding-маршрутизация,
шифрованное хранилище SQLite + Fernet, передача файлов с SHA-256, UDP голосовые звонки.

## Быстрый старт

```bash
cd docker
docker-compose up --build
```

Поднимает 4 ноды (node1–node4) в одной Docker-сети.
node1 API: http://localhost:9001

## Архитектура

```
[node1] ←TCP:9000→ [node2]
   ↕                   ↕
[node4] ←TCP:9000→ [node3]

Каждая нода:
  :9000  TCP mesh   — P2P постоянные соединения, JSON newline-delimited
  :9001  HTTP API   — для backend2 (Николай)
  :9002  UDP voice  — голосовые звонки (PCM 16kHz, 60мс фреймы)
```

Протокол: flooding с TTL=7, дедупликация по message_id (LRU 5 мин).
Хранилище: SQLite, текст зашифрован Fernet (AES-128-CBC + HMAC-SHA256).
История переживает перезапуск контейнера.

## ENV переменные

| Переменная | Описание | Пример |
|---|---|---|
| NODE_ID | ID ноды | node1 |
| NODE_NAME | Отображаемое имя | Node 1 |
| PORT | TCP mesh порт | 9000 |
| API_PORT | HTTP API порт | 9001 |
| PEERS | Пиры для подключения | node2:9000,node3:9000 |
| STORAGE_KEY | Fernet ключ (44 символа base64) | генерируется если не задан |
| DB_PATH | Путь к SQLite файлу | /app/data/messages.db |

Генерация ключа: `python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

## API (:9001)

| Метод | Путь | Описание |
|---|---|---|
| GET | /health | Статус ноды |
| GET | /peers | Все пиры (включая offline) |
| GET | /relay | Текущий relay-узел |
| GET | /messages | История (100 последних, из DB) |
| POST | /send | Отправить сообщение |
| GET | /events | Поллинг событий (каждые 2с) |
| POST | /send_file | Отправить файл (multipart, макс 50MB) |
| GET | /files | Список полученных файлов |
| GET | /file/{id} | Скачать файл |
| GET | /file/{id}/status | Статус приёма (missing chunks) |
| POST | /file/{id}/request_retry | Запрос повторной отправки пропущенных чанков |
| POST | /signal | WebRTC signaling relay |
| POST | /call/start | Начать UDP голосовой звонок |
| POST | /call/end | Завершить звонок |
| GET | /call/stats/{id} | Метрики: packets sent/received/lost |
| GET | /call/active | Активные звонки |

## Безопасность

- Хранилище: Fernet (симметричный, pre-shared key через STORAGE_KEY)
- `encrypted: true` в сообщениях = реальное шифрование в DB
- TTL=7 ограничивает flood-шторм
- Макс файл: 50MB, макс незавершённых передач: 10
- Rate-limit через TTL decrement на каждом хопе
