# 1. Используем официальный образ Python нужной версии
FROM python:3.12-slim

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Устанавливаем системные зависимости (если нужны, например, для psycopg2 или других библиотек)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential libpq-dev \
#  && rm -rf /var/lib/apt/lists/*

# Обновляем pip
RUN pip install --upgrade pip

# Копируем файл с зависимостями
COPY requirements.txt requirements.txt

# Устанавливаем зависимости
RUN pip install -r requirements.txt

# Копируем весь проект в рабочую директорию
COPY . .

# (Опционально) Создаем пользователя для запуска приложения (для безопасности)
# RUN addgroup --system app && adduser --system --group app
# USER app

# Открываем порт, на котором будет работать приложение (стандартный для Django runserver)
EXPOSE 8000

# Команда для запуска приложения
# Для разработки:
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
# Для production обычно используют Gunicorn или uWSGI:
# CMD ["gunicorn", "blog_project.wsgi:application", "--bind", "0.0.0.0:8000"] 