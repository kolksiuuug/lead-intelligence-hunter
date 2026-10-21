# Lead Intelligence Hunter — frontend

React + Vite frontend для текущего Flask API. Русский интерфейс, адаптивная тёмная тема.

## Что подключено

- Обзор: метрики, последние лиды, состояние API.
- Лиды: просмотр, поиск/фильтры, создание, редактирование, удаление, выбор нескольких лидов и `/choose` → `/share`.
- Профили специалистов: создание, редактирование, удаление. `stack`, `experience`, `can_solve` необязательны.
- Заметки/задачи: CRUD, назначение профиля и привязка лидов.
- GitHub: репозитории, issues, комментарии, анализ и сопоставление с профилями.
- Подбор профилей, обучающие примеры, найденные признаки.
- Настройки LLM: `/context_provider` и `/app-settings`.

## Запуск всего проекта через один docker-compose.yml

1. Распакуй этот каталог в корне репозитория под именем `frontend/`.
2. Добавь сервис `frontend` в основной `docker-compose.yml` из репозитория (пример полного файла был предоставлен отдельно):

```yaml
  frontend:
    build:
      context: ./frontend
      args:
        VITE_API_URL: /api
    ports:
      - "8080:80"
    depends_on:
      - api
    restart: unless-stopped
```

3. Запусти из корня проекта:

```bash
docker compose up -d --build
```

Открой http://localhost:8080.

Nginx внутри frontend проксирует `/api/...` к сервису Docker `api:5000`, убирая префикс `/api`. Поэтому браузер ходит к тому же origin, CORS отдельно настраивать не требуется. API по-прежнему доступен напрямую на http://localhost:5000 для разработки и диагностики.

## Локальная разработка без сборки Nginx

Нужен Node.js 20+:

```bash
cd frontend
npm install
npm run dev
```

Открой http://localhost:5173. Vite проксирует `/api/...` к `http://localhost:5000`.

## Важно

- В `docker-compose.yml` сервис `frontend` должен собираться из `./frontend`.
- `VITE_API_URL` в Docker должен быть `/api`, не `http://api:5000`: запрос выполняет браузер, а имя `api` доступно только внутри Docker-сети.
- `docker compose up -d --build` поднимет все сервисы без отключённого профиля. В существующем compose сервисы `collector`, `collectors` и `llm` тоже запустятся. Чтобы обновить/запустить только БД, API и интерфейс, используй `docker compose up -d --build db api frontend`.
- Ollama с профилем `ollama` не поднимется по умолчанию; для запуска с ним используй `docker compose --profile ollama up -d --build`.

## API routes

`/health`, `/stats`, `/leads`, `/leads/<id>`, `/profiles`, `/profile`, `/profile/<id>`, `/notes`, `/notes/<id>`, `/choose`, `/share`, `/repositories`, `/repositories/<id>`, `/issues/<id>`, `/issues/<id>/comments`, `/issues/<id>/analysis`, `/profile-matching`, `/training-samples`, `/finded`, `/app-settings`, `/context_provider`.

Форматы данных отдельных route handlers могут отличаться; ошибки API отображаются в интерфейсе.
