# Бэкенд для блога

## Описание
API для управления блогом: пользователи, статьи, комментарии.

## Требования
- Docker & Docker Compose
- Python 3.10+

## Переменные окружения
Создайте файл `.env` в корне проекта со следующими переменными:
```
SECRET_KEY=ваш_secret_key
DEBUG=True
DB_ENGINE=django.db.backends.postgresql
DB_NAME=blog_db_project
DB_USER=blog_user_project
DB_PASSWORD=blog_password_project
DB_HOST=db
DB_PORT=5432
ALLOWED_HOSTS=localhost,127.0.0.1
```

## Запуск локально через Docker Compose
1. docker-compose up -d --build
2. docker-compose exec web python manage.py migrate
3. docker-compose exec web python manage.py collectstatic --noinput

API доступно по http://localhost:8000/api/
Документация Swagger — http://localhost:8000/api/docs

## Основные эндпоинты
- POST /api/users/register
- POST /api/users/login
- GET /api/users/me
- GET /api/blog/categories
- GET /api/blog/categories/{id}
- POST /api/blog/articles
- GET /api/blog/articles
- GET /api/blog/articles/{id}
- PUT /api/blog/articles/{id}
- DELETE /api/blog/articles/{id}
- POST /api/blog/articles/{id}/comments
- GET /api/blog/articles/{id}/comments
- PUT /api/blog/comments/{id}
- DELETE /api/blog/comments/{id}
- GET /api/blog/comments/{id} 