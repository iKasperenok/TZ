# Builder stage
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Optional: install system dependencies for psycopg2 if needed
# RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Install Python dependencies in isolated prefix
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# Copy project code
COPY . .

# Final stage
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy installed dependencies and code from builder
COPY --from=builder /install /usr/local
COPY --from=builder /app /app

# Создаём группу и пользователя для запуска приложения
RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser

# Собираем статические файлы и устанавливаем права
RUN mkdir -p /app/staticfiles \
    && python manage.py collectstatic --noinput \
    && chown -R appuser:appgroup /app/staticfiles

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Start Gunicorn
CMD ["gunicorn", "blog_project.wsgi:application", "--bind", "0.0.0.0:8000"] 