# AI Books Portal 📚

Портал для управления электронной библиотекой с возможностью загрузки и чтения книг, управления авторами, издательствами и комментариями.

## Возможности ✨

### Управление книгами 📖
- Создание, редактирование и удаление книг
- Загрузка файлов книг и обложек
- Поиск книг по различным параметрам
- Поддержка различных языков
- Связь с авторами и издательствами

### Управление авторами ✍️
- Создание и редактирование информации об авторах
- Загрузка фотографий авторов
- Поиск авторов
- Просмотр списка книг автора

### Управление издательствами 🏢
- Создание и редактирование информации об издательствах
- Загрузка логотипов
- Поиск издательств
- Просмотр каталога книг издательства

### Комментарии и обсуждения 💬
- Добавление комментариев к книгам
- Древовидная структура комментариев (ответы)
- Модерация комментариев
- Уведомления о новых комментариях

### Пользователи и роли 👥
- Регистрация и аутентификация
- Различные роли (admin, editor, moderator, user)
- Управление профилями
- Блокировка пользователей

### Отчеты и статистика 📊
- Статистика по книгам (общее количество, новые, по языкам)
- Статистика по пользователям (активность, роли)
- Статистика по комментариям
- Статистика использования хранилища

## Технический стек 🛠️

### Backend 🔧
- Python 3.11+
- FastAPI
- SQLAlchemy (async)
- Pydantic
- Alembic

### База данных и кэширование 💾
- PostgreSQL
- Redis
- Elasticsearch

### Хранение файлов 📂
- MinIO

### Коммуникация 📡
- JWT для аутентификации
- SMTP для email уведомлений
- Telegram Bot API для уведомлений администраторов

### Мониторинг 📈
- Prometheus
- Grafana
- Node Exporter
- cAdvisor

## Архитектура 🏗️

Проект следует принципам Clean Architecture и разделен на следующие слои:

```
src/books_portal/
├── domain/
│   ├── entities/       # Бизнес-сущности
│   ├── interfaces/     # Интерфейсы репозиториев и сервисов
│   └── use_cases/      # Бизнес-логика
├── infrastructure/
│   ├── database/       # Модели БД и сессии
│   └── services/       # Реализации сервисов
└── api/
    └── v1/
        ├── endpoints/  # Эндпоинты API
        ├── schemas/    # Pydantic модели
        └── dependencies/  # Зависимости FastAPI
```

## Метрики и мониторинг 📊

### HTTP метрики 🌐
- Количество запросов
- Латентность запросов
- Ошибки

### Бизнес метрики 📈
- Количество книг/авторов/издательств
- Активность пользователей
- Использование хранилища

### Технические метрики ⚙️
- Использование CPU/RAM
- Метрики базы данных
- Метрики кэша
- Метрики хранилища

## CI/CD 🚀

### GitHub Actions ⚡
- Тестирование
- Линтинг (ruff, black, mypy)
- Сборка Docker образов
- Автоматический деплой

### Тестирование 🧪

### Запуск тестов
```bash
# Все тесты с подробным выводом
pytest -v

# С покрытием и HTML отчетом
pytest --cov=src --cov-report=html

# Параллельный запуск тестов
pytest -n auto

# Только failed тесты
pytest --last-failed

# С отображением print() и логов
pytest -v --capture=no
```

### Примеры тестов 📝

#### Тестирование API
```python
async def test_create_book(client: AsyncClient, editor_token: str):
    response = await client.post(
        "/api/v1/books",
        headers={"Authorization": f"Bearer {editor_token}"},
        json={
            "title": "Test Book",
            "description": "Test Description",
            "isbn": "1234567890",
            "language": "ru",
            "page_count": 100,
            "publisher_id": "550e8400-e29b-41d4-a716-446655440000",
            "author_ids": ["550e8400-e29b-41d4-a716-446655440001"]
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Book"
```

#### Тестирование репозиториев
```python
async def test_search_authors_by_name(session: AsyncSession):
    repository = SQLAuthorRepository(session)
    authors = await repository.search_by_name(
        name="Толстой",
        skip=0,
        limit=10
    )
    assert len(authors) > 0
    assert "Толстой" in authors[0].name
```

#### Тестирование сервисов
```python
async def test_upload_file_to_storage(storage_service: StorageService):
    file_content = b"Test content"
    file = BytesIO(file_content)
    file_url = await storage_service.upload_file(
        file=file,
        filename="test.txt",
        content_type="text/plain",
        entity_type="books",
        entity_id=UUID("550e8400-e29b-41d4-a716-446655440000")
    )
    assert file_url.startswith("http")
```

### Фикстуры 🛠️

```python
@pytest.fixture
async def editor_token(client: AsyncClient) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "editor@example.com",
            "password": "password"
        }
    )
    return response.json()["access_token"]

@pytest.fixture
def test_book_data() -> dict:
    return {
        "title": "Test Book",
        "description": "Test Description",
        "isbn": "1234567890",
        "language": "ru",
        "page_count": 100
    }
```

### Моки и патчи 🎭

```python
@pytest.mark.asyncio
async def test_send_email_notification(mocker):
    mock_send = mocker.patch("aiosmtplib.send")
    email_service = EmailService()
    await email_service.send_registration_email(
        email="test@example.com",
        username="test_user"
    )
    mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_cache_service(mocker):
    mock_redis = mocker.patch("redis.asyncio.Redis")
    mock_redis.return_value.get.return_value = b'{"key": "value"}'
    cache_service = RedisCacheService()
    result = await cache_service.get("test_key")
    assert result == {"key": "value"}
```

### Параметризованные тесты 🔄

```python
@pytest.mark.parametrize("role,expected_status", [
    ("admin", 200),
    ("editor", 200),
    ("user", 403),
    (None, 401),
])
async def test_access_rights(
    client: AsyncClient,
    get_token: Callable[[str], str],
    role: Optional[str],
    expected_status: int
):
    token = get_token(role) if role else ""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = await client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == expected_status
```

### Тестирование ошибок 🐛

```python
async def test_book_not_found(client: AsyncClient, user_token: str):
    response = await client.get(
        f"/api/v1/books/{uuid4()}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Book not found"

async def test_invalid_isbn(client: AsyncClient, editor_token: str):
    response = await client.post(
        "/api/v1/books",
        headers={"Authorization": f"Bearer {editor_token}"},
        json={"isbn": "invalid"}
    )
    assert response.status_code == 422
```

## Развертывание 🚀

### Требования 📋
- Docker
- Docker Compose
- Минимум 2GB RAM
- 20GB свободного места

### Установка 💻

1. Клонировать репозиторий:
```bash
git clone https://github.com/username/ai-books-portal.git
cd ai-books-portal
```

2. Создать файл .env на основе .env.example:
```bash
cp .env.example .env
```

3. Настроить переменные окружения в .env

4. Запустить сервисы:
```bash
docker compose up -d
```

5. Применить миграции:
```bash
docker compose exec app alembic upgrade head
```

## Разработка 👨‍💻

### Настройка окружения ⚙️

1. Установить Poetry:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Установить зависимости:
```bash
poetry install
```

3. Активировать виртуальное окружение:
```bash
poetry shell
```

### Запуск тестов 🧪
```bash
# Все тесты
pytest

# С покрытием
pytest --cov=src

# Конкретный тест
pytest tests/api/v1/test_books.py -v
```

### Линтинг и форматирование ✨
```bash
# Проверка типов
mypy src

# Форматирование
black src tests

# Проверка стиля
ruff check src tests
```

### Миграции 🔄
```bash
# Создать миграцию
alembic revision --autogenerate -m "description"

# Применить миграции
alembic upgrade head

# Откатить миграцию
alembic downgrade -1
```

### Примеры использования API 📝

#### Работа с авторами ✍️
```bash
# Поиск авторов
curl "http://localhost:8000/api/v1/authors?query=Толстой&skip=0&limit=10" \
  -H "Authorization: Bearer ${TOKEN}"

# Создание автора
curl -X POST http://localhost:8000/api/v1/authors \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Лев Толстой",
    "biography": "Русский писатель...",
    "birth_date": "1828-09-09"
  }'

# Загрузка фото автора
curl -X POST http://localhost:8000/api/v1/authors/${author_id}/photo \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "file=@photo.jpg"
```

#### Работа с издательствами 🏢
```bash
# Поиск издательств
curl "http://localhost:8000/api/v1/publishers?query=ЭКСМО&skip=0&limit=10" \
  -H "Authorization: Bearer ${TOKEN}"

# Создание издательства
curl -X POST http://localhost:8000/api/v1/publishers \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ЭКСМО",
    "description": "Крупное издательство...",
    "website": "https://eksmo.ru"
  }'

# Загрузка логотипа
curl -X POST http://localhost:8000/api/v1/publishers/${publisher_id}/logo \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "file=@logo.png"
```

#### Работа с комментариями 💬
```bash
# Создание комментария
curl -X POST http://localhost:8000/api/v1/comments \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Отличная книга!",
    "book_id": "${book_id}"
  }'

# Ответ на комментарий
curl -X POST http://localhost:8000/api/v1/comments \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Согласен с вами",
    "book_id": "${book_id}",
    "parent_id": "${comment_id}"
  }'

# Получение комментариев к книге
curl "http://localhost:8000/api/v1/comments?book_id=${book_id}&skip=0&limit=10" \
  -H "Authorization: Bearer ${TOKEN}"

# Жалоба на комментарий
curl -X POST http://localhost:8000/api/v1/comments/${comment_id}/report \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"reason": "spam"}'
```

#### Управление пользователями 👥
```bash
# Поиск пользователей
curl "http://localhost:8000/api/v1/users?query=admin&role=editor&skip=0&limit=10" \
  -H "Authorization: Bearer ${TOKEN}"

# Изменение роли пользователя
curl -X PUT http://localhost:8000/api/v1/users/${user_id}/role \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"role": "editor"}'

# Блокировка пользователя
curl -X PUT http://localhost:8000/api/v1/users/${user_id}/block \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Нарушение правил"}'
```

### Рекомендуемые плагины для VS Code 🔌
- Python
- Pylance
- Python Type Hint
- Python Test Explorer
- Docker
- YAML
- PostgreSQL
- Redis
- REST Client
- GitLens
- Git Graph

### Рекомендуемые плагины для PyCharm 🔧
- Poetry
- Ruff
- Black Formatter
- Mypy
- Docker
- Database Tools and SQL
- Redis

### Профилирование 📊
```bash
# Профилирование SQL запросов
SQLALCHEMY_ECHO=True uvicorn src.books_portal.main:app --reload

# Анализ результатов профилирования
python -m cProfile -o output.prof scripts/analyze_performance.py
python -m pstats output.prof
```

### Отладка 🐛
```bash
# Настройка логирования
export LOG_LEVEL=DEBUG

# Использование debugger
python -m debugpy --listen 5678 --wait-for-client -m uvicorn src.books_portal.main:app
```

### Git-flow 🌊
- `main` - основная ветка
- `develop` - ветка разработки
- `feature/*` - ветки для новых функций
- `bugfix/*` - ветки для исправления ошибок
- `release/*` - ветки для релизов
- `hotfix/*` - ветки для срочных исправлений

## Конфигурация ⚙️

### Основные настройки (.env) 🔑
```bash
# Приложение
APP_NAME=AI Books Portal
APP_VERSION=0.1.0
DEBUG=False
ENVIRONMENT=production

# База данных
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=books_portal
POSTGRES_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_HOST=localhost
MINIO_PORT=9000
MINIO_SECURE=False
MINIO_BUCKET_NAME=books-portal

# Email
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=noreply@example.com

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_ADMIN_CHAT_IDS=["123456789"]

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
```

### Docker Compose для разработки 🐳
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: books_portal
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  elasticsearch:
    image: elasticsearch:8.8.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data

  mailhog:
    image: mailhog/mailhog
    ports:
      - "1025:1025"
      - "8025:8025"

volumes:
  postgres_data:
  minio_data:
```

## Лицензия 📄

MIT License
