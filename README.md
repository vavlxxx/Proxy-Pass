# Caching Proxy Server

Консольная утилита для кэширующего прокси-сервера на Python. Кэширует HTTP-ответы со статусами `2xx` и `304` для методов `GET` и `HEAD`.

## Возможности

- 🚀 Кэширование HTTP-запросов с настраиваемым TTL
- 🔄 Поддержка множественных серверов на разных портах
- 🌙 Detached режим для фоновой работы
- 📊 Просмотр статуса, ключей кэша и управление
- 🔧 Простой CLI интерфейс

## Установка

```bash
# Синхронизация зависимостей
uv sync

# Установка в editable режиме
pip install -e .

# Теперь команда доступна глобально
caching-proxy --help
```

```
python ./src/caching_proxy/cli.py --help
```

## Быстрый старт

```bash
# Запустить прокси для dummyjson.com на порту 3000
caching-proxy run -o https://dummyjson.com -p 3000

# Запустить в фоновом режиме с TTL 60 секунд
caching-proxy run -o https://dummyjson.com -p 3000 --ttl 60 -d

# Проверить статус
caching-proxy health -p 3000

# Остановить сервер
caching-proxy stop -p 3000
```

## Команды

### `run` - Запуск прокси-сервера

Запускает новый прокси-сервер на указанном порту.

```bash
caching-proxy run -o <ORIGIN_URL> -p <PORT> [OPTIONS]
```

**Обязательные параметры:**
- `-o, --origin` - URL origin сервера (например: `https://dummyjson.com`)
- `-p, --port` - Порт для прокси-сервера (например: `3000`)

**Опциональные параметры:**
- `--ttl` - Время жизни кэша в секундах (по умолчанию: `60`)
- `0` или отрицательные значения = бесконечное хранение
- `-d, --detached` - Запуск в фоновом режиме

**Примеры:**

```bash
# Foreground режим (логи в консоль)
caching-proxy run -o https://dummyjson.com -p 3000

# Background режим с TTL 30 секунд
caching-proxy run -o https://dummyjson.com -p 3000 --ttl 30 -d

# Без TTL (бесконечное хранение)
caching-proxy run -o https://api.github.com -p 3001 --ttl 0 -d
```

**Вывод:**

```bash
Started server in detached mode on http://localhost:3000
Logs: A:\workspace\Caching-Proxy-Server\logs\proxy.log
```

---

### `health` - Статус серверов

Показывает информацию о запущенных прокси-серверах.

```bash
caching-proxy health [-p <PORT>]
```

**Параметры:**
- `-p, --port` (опционально) - Порт конкретного сервера. Если не указан, показывает все запущенные серверы.

**Примеры:**

```bash
# Статус конкретного сервера
caching-proxy health -p 3000

# Статус всех серверов
caching-proxy health
```

**Вывод:**

```bash
proxy server 1 is running
  Host:   http://localhost:3000
  Origin: https://dummyjson.com
  TTL:    30s

proxy server 2 is running
  Host:   http://localhost:3001
  Origin: https://httpbin.org
  TTL:    60s
```

---

### `keys` - Просмотр ключей кэша

Отображает все кэшированные ключи для указанного сервера.

```bash
caching-proxy keys -p <PORT>
```

**Параметры:**
- `-p, --port` - Порт сервера (обязательно)

**Пример:**

```bash
caching-proxy keys -p 3000
```

**Вывод:**

```bash
Cache keys (6):
  1. GET /public/img/icons/github.svg       EXPIRES IN: 15.3s
  2. GET /public/img/icons/bar.svg          EXPIRES IN: 18.7s
  3. GET /public/img/hero-image.svg         EXPIRES IN: 22.1s
  4. GET /public/img/multiple-options.svg   EXPIRES IN: 25.4s
  5. GET /public/img/lorem-placeholder.svg  EXPIRES IN: 28.9s
  6. GET /public/fonts/DM_Sans/DMSans-Bold.ttf  NEVER EXPIRES
```

---

### `clear` - Очистка кэша

Удаляет все кэшированные ключи для указанного сервера.

```bash
caching-proxy clear -p <PORT>
```

**Параметры:**
- `-p, --port` - Порт сервера (обязательно)

**Пример:**

```bash
caching-proxy clear -p 3000
```

**Вывод:**

```bash
Cache cleared on http://localhost:3000
```

---

### `stop` - Остановка сервера

Останавливает прокси-сервер на указанном порту.

```bash
caching-proxy stop -p <PORT>
```

**Параметры:**
- `-p, --port` - Порт сервера для остановки (обязательно)

**Пример:**

```bash
caching-proxy stop -p 3000
```

**Вывод:**

```bash
Server on http://localhost:3000 stopped
```

---

## Конфигурация

Сервера, запущенные в detached режиме, автоматически регистрируются в файле `config.json`:

```json
{
  "servers": [
    {
      "host": "localhost",
      "port": 3000,
      "origin": "https://dummyjson.com",
      "ttl": 30
    },
    {
      "host": "localhost",
      "port": 3001,
      "origin": "https://httpbin.org",
      "ttl": 60
    }
  ]
}
```

> ⚠️ **Важно**: Не модифицируйте `config.json` вручную! Используйте команды CLI для управления серверами. Файл автоматически обновляется при запуске/остановке серверов.

## Логи

При запуске в detached режиме логи сохраняются в `logs/proxy.log`:

```bash
2026-01-01 13:00:00 :: [INFO] :: server :: Running Caching Proxy Server on localhost:3000
2026-01-01 13:00:00 :: [INFO] :: server :: Requests will be proxied from https://dummyjson.com
2026-01-01 13:00:05 :: [INFO] :: middleware :: GET /products STATUS=200 CACHE=MISS TIME=234.56ms
2026-01-01 13:00:06 :: [INFO] :: middleware :: GET /products STATUS=200 CACHE=HIT TIME=2.13ms
```

Просмотр логов в реальном времени:

```bash
# Linux/macOS
tail -f logs/proxy.log

# Windows PowerShell
Get-Content logs\proxy.log -Wait -Tail 50
```

## Примеры использования

### Пример 1: Кэширование API

```bash
# Запускаем прокси для JSONPlaceholder API
caching-proxy run -o https://jsonplaceholder.typicode.com -p 3000 --ttl 300 -d

# Делаем запросы через прокси
curl http://localhost:3000/posts/1
curl http://localhost:3000/users

# Проверяем что попало в кэш
caching-proxy keys -p 3000

# Очищаем кэш
caching-proxy clear -p 3000

# Останавливаем
caching-proxy stop -p 3000
```

### Пример 2: Множественные прокси

```bash
# Запускаем несколько прокси для разных API
caching-proxy run -o https://dummyjson.com -p 3000 -d
caching-proxy run -o https://httpbin.org -p 3001 -d
caching-proxy run -o https://api.github.com -p 3002 -d

# Проверяем статус всех
caching-proxy health

# Останавливаем конкретный
caching-proxy stop -p 3001
```
