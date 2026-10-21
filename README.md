# Lead Intelligence Hunter

Lead Intelligence Hunter — приложение для сбора и анализа потенциальных заказов и задач, хранения лидов и подбора профилей специалистов. Проект объединяет веб-интерфейс, Flask API, PostgreSQL, фоновые сборщики данных и LLM/ML-анализ.

## Возможности

- Управление лидами: просмотр, поиск, фильтрация, создание, редактирование и удаление.
- Управление профилями специалистов и заметками/задачами.
- Сбор публичных задач с поддерживаемых площадок через фоновые коллекторы.
- Поиск GitHub-репозиториев по поисковым запросам, сбор issues и комментариев.
- LLM-анализ GitHub issues и сопоставление задач с профилями специалистов.
- ML-оценка задач и совместимости профилей с использованием сохранённых моделей.
- Настройка параметров анализа и провайдера LLM через приложение.

## Архитектура

```text
Браузер
  │
  ▼
Frontend: React + Vite, раздача через Nginx (:8080)
  │  /api/*
  ▼
Flask API / Gunicorn (:5000) ─────────── PostgreSQL 16
  │                                         ▲
  ├── GitHub discovery / scheduler ─────────┤
  ├── LLM analysis service (:8000 внутри Docker-сети) ─┤
  └── Collectors для площадок ──────────────┘
                  │
                  └── OpenRouter / Gemini / Ollama
```

### Основные компоненты

| Компонент | Назначение |
|---|---|
| `frontend/` | React-интерфейс. Nginx публикует его на порту `8080` и проксирует запросы `/api/` к сервису `api`. |
| `app/main.py` | Flask API: лиды, профили, заметки, GitHub-репозитории, issues, комментарии, статистика и настройки. |
| `app/models.py`, `app/db.py` | Модели данных SQLAlchemy и подключение к PostgreSQL. |
| `migrations/` | Миграции схемы базы данных Alembic/Flask-Migrate. |
| `app/collectors/collector.py` | Сборщик заданий с поддерживаемых площадок. Его циклический запуск регулируется `RUNNER_COLLECTORS`. |
| `app/services/discovery_scheduler.py` | Фоновый планировщик GitHub discovery и обучения ML-моделей. Параметры запуска задаются через `DISCOVERY_*`. |
| `app/services/repository_discovery.py` | Поиск репозиториев через GitHub API, загрузка issues и комментариев, сохранение результатов и запуск анализа. |
| `app/services/llm_service.py` | Вызовы LLM-провайдеров, генерация поисковых запросов и анализ/сопоставление задач. |
| `app/llm/` | Сервис анализа собранных заданий, подготовка обучающих данных, обучение и предсказание. |
| `issue_score_model.joblib`, `issue_matcher_model.joblib` | Сохранённые ML-модели, используемые для оценки задач и сопоставления профилей. |
| `docker-compose.yaml` | Запуск API, базы данных, фоновых сервисов, интерфейса и опционального Ollama. |

Веб-интерфейс открывается по адресу `http://localhost:8080`. API доступен напрямую на `http://localhost:5000`; проверка состояния — `http://localhost:5000/health`.

## Запуск

### 1. Подготовь конфигурацию

Нужны Docker Engine и Docker Compose v2. Для запуска Ollama в этом Compose-файле также требуется поддержка GPU, доступная Docker.

В корне репозитория выполни:

```bash
cp .env.example .env
```

Открой `.env` и настрой значения под своё окружение. Для доступа к GitHub API укажи собственный `GITHUB_TOKEN`. Ключи `OPENROUTER_KEY` и `GEMINI_KEY` нужны только для соответствующих внешних LLM-провайдеров. Не публикуй `.env` и не добавляй его в Git.

Если локальный SOCKS-прокси недоступен по адресу `host.docker.internal:1338`, измени `PROXY` на адрес своего прокси или оставь параметр пустым.

### 2. Запусти проект

Запускай из корневого каталога проекта:

```bash
sudo bash start.sh
```

Скрипт читает `.env`, собирает образы и запускает сервисы в фоне. При `OLLAMA=true` включается Compose-профиль `ollama`; сервис загрузит модель `qwen3.5:4b` при первом запуске. При `OLLAMA=false` профиль Ollama не используется — настрой как минимум один доступный внешний провайдер LLM (`OPENROUTER_KEY` или `GEMINI_KEY`).

Открой интерфейс:

- **Frontend:** `http://localhost:8080`
- **API health check:** `http://localhost:5000/health`

### 3. Примени миграции базы данных при первом запуске

Если база данных новая или схема ещё не создана, после старта сервисов выполни:

```bash
sudo docker compose exec api flask --app app.main db upgrade
```

Команду обычно достаточно выполнить один раз для новой базы, а затем повторять после обновления проекта, если добавились новые миграции.

### 4. Логи и состояние сервисов

```bash
sudo docker compose ps
sudo docker compose logs -f api
sudo docker compose logs -f collector
sudo docker compose logs -f collectors
sudo docker compose logs -f llm
```

Чтобы смотреть все логи, используй `sudo docker compose logs -f`.

## Остановка

Используй команду, соответствующую значению `OLLAMA` в файле `.env`.

Если `OLLAMA=true`:

```bash
sudo docker compose --profile ollama down
```

Если `OLLAMA=false`:

```bash
sudo docker compose down
```

Эти команды останавливают контейнеры и удаляют сеть Compose, но сохраняют именованные тома с данными. Не добавляй `-v`, если не собираешься удалить данные PostgreSQL и хранилище Ollama.

## Основные параметры `.env`

Подробные настройки находятся в `.env.example`. Наиболее важные:

- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` — база данных и учётные данные PostgreSQL.
- `GITHUB_TOKEN` — токен для GitHub API.
- `PROXY`, `PROXY_COLLECTORS`, `PROXY_GITHUB` — прокси для LLM-запросов, сборщиков площадок и GitHub соответственно.
- `RUNNER_COLLECTORS` — включает (`true`) или выключает (`false`) периодический запуск сборщика заданий с площадок.
- `DISCOVERY_RUN_ON_START` — запускать ли GitHub discovery при старте планировщика.
- `DISCOVERY_RUN_WORK` — включает периодические запуски GitHub discovery; при `false` планировщик завершает работу без повторных запусков.
- `DISCOVERY_INTERVAL_MINUTES` — интервал между запусками GitHub discovery в минутах.
- `MAX_REPOSITORIES_PER_WORD`, `MAX_ISSUES_PER_WORD`, `MAX_COMMENTS_PER_WORD`, `MAX_GITHUB_REQUESTS_PER_RUN` — ограничения объёма сбора с GitHub.
- `OPENROUTER_KEY`, `OPENROUTER_MODEL`, `GEMINI_KEY`, `OLLAMA` — доступные LLM-провайдеры и настройки.
- `LLM_SELF_PROFILE_ANALITIC` — включает дополнительное LLM-сопоставление профилей, когда значение равно `true`.

`OLLAMA=true` управляет запуском контейнера Ollama через `start.sh` и одновременно делает Ollama доступным LLM-провайдером. Если указаны ключи внешних провайдеров, приложение также может использовать их; выбранный провайдер может настраиваться в самом приложении.

#ВНИМАНИЕ (ДЛЯ ПЕРВОГО ЗАПУСКА)
#1 step
DISCOVERY_RUN_ON_START=false
RUNNER_COLLECTORS=false
sudo bash start.sh
создаем профили, чтобы llm активно анализировала их
дальше docker compose --profile ollama down
#2 step
DISCOVERY_RUN_ON_START=true
OLLAMA=true
sudo bash start.sh
дальше docker compose --profile ollama down
#3 step
после завершения pipeline пересобираем с флагом
RUNNER_COLLECTORS=true

## Безопасность

- Храни реальные пароли, GitHub PAT и API-ключи только в локальном `.env` или секрет-хранилище.
- Не коммить `.env`, токены, ключи, дампы базы и персональные данные.
- Выдавай GitHub PAT минимально необходимые разрешения и отзывай токены, которые могли попасть в публичные сообщения или репозитории.
