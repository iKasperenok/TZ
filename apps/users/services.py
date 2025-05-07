import uuid  # Для генерации UUID токенов

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction

from ninja.errors import HttpError
from .models import AuthToken  # Импортируем модель AuthToken

# Временное хранилище токенов (для демонстрации, в реальном приложении нужна БД)
# Ключ - username, значение - token. Либо ключ - token, значение - user_id.
# Для простоты и соответствия ТЗ "сервер генерирует токен",
# мы будем генерировать его при регистрации и логине, но не будем хранить персистентно
# в этой базовой реализации без отдельной модели Token.
# Если бы токен сохранялся, здесь была бы работа с моделью AuthToken.


def generate_auth_token_for_user(user: User) -> str:
    """
    Генерирует, сохраняет (или обновляет) UUID токен для пользователя и возвращает его ключ.
    Если у пользователя уже есть токен, он будет удален и создан новый.
    """
    # Генерируем UUID4 и берем его hex представление
    token_key = uuid.uuid4().hex

    with transaction.atomic():
        # Удаляем старый токен, если он существует, чтобы гарантировать OneToOne
        AuthToken.objects.filter(user=user).delete()
        # Создаем новый токен
        token_obj = AuthToken.objects.create(user=user, key=token_key)
    return token_obj.key


def create_user_service(username, password):
    """Создает нового пользователя и возвращает кортеж (user, token_key)."""
    if not username or not password:
        raise HttpError(422, "Имя пользователя и пароль не могут быть пустыми.")
    try:
        with transaction.atomic():  # Используем транзакцию для создания пользователя и токена
            user = User.objects.create_user(username=username, password=password)
            token_key = generate_auth_token_for_user(user)
        return user, token_key
    except IntegrityError:  # Если пользователь уже существует
        raise HttpError(409, f"Пользователь с именем '{username}' уже существует.")
    except Exception as e:
        # Логирование ошибки здесь было бы полезно
        raise HttpError(
            500, f"Внутренняя ошибка сервера при создании пользователя: {str(e)}"
        )


def authenticate_user_service(username, password):
    """Аутентифицирует пользователя и возвращает кортеж (user, token_key), если успешно."""
    user = authenticate(username=username, password=password)
    if user is not None:
        token_key = generate_auth_token_for_user(user)
        return user, token_key
    else:
        # Не уточняем, неправильный логин или пароль, для безопасности
        raise HttpError(401, "Неверные учетные данные.")
