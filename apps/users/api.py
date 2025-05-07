import logging # Импортируем logging
from ninja import Router
from ninja.errors import HttpError
from django.contrib.auth.models import User # Нужен для type hinting и для SimpleTokenAuth
from django.http import HttpRequest # Для AuthBase

from .schemas import UserRegisterSchema, UserLoginSchema, TokenSchema, UserSchema
from .services import create_user_service, authenticate_user_service
from .models import AuthToken # Импортируем AuthToken для аутентификатора

logger = logging.getLogger(__name__) # Получаем логгер для текущего модуля

from ninja.security import HttpBearer # Используем HttpBearer

class TokenAuthBearer(HttpBearer):
    def authenticate(self, request, token: str): # token здесь уже извлечен HttpBearer
        logger.debug(f"TokenAuthBearer.authenticate: CALLED with token = '{token}'")
        try:
            token_obj = AuthToken.objects.select_related('user').get(key=token)
            logger.info(f"TokenAuthBearer: Аутентифицирован пользователь '{token_obj.user.username}' (ID: {token_obj.user.id}).")
            request.user = token_obj.user # Явно устанавливаем request.user
            return token_obj.user
        except AuthToken.DoesNotExist:
            logger.warning(f"TokenAuthBearer: Недействительный токен: {token[:20]}...")
            return None
        except Exception as e:
            logger.error(f"TokenAuthBearer: Ошибка при аутентификации по токену: {e}", exc_info=True)
            return None

# Убираем auth с инициализации Router
router = Router(tags=["Пользователи"])

@router.post("/register", response={201: TokenSchema, 409: None, 422: None, 500: None}, auth=None, summary="Регистрация нового пользователя", operation_id="users_register")
def register_user(request, payload: UserRegisterSchema):
    """
    Регистрирует нового пользователя и возвращает токен.
    - **username**: Имя пользователя (уникальное)
    - **password**: Пароль (минимум 8 символов)
    """
    logger.info(f"Попытка регистрации пользователя: {payload.username}")
    try:
        user, token_key = create_user_service(payload.username, payload.password)
        logger.info(f"Пользователь '{user.username}' успешно зарегистрирован. Токен сохранен в БД.")
        return 201, {"token": token_key}
    except HttpError as e:
        logger.warning(f"Ошибка регистрации пользователя '{payload.username}': {e.message} (HTTP {e.status_code})")
        raise e 
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при регистрации пользователя '{payload.username}': {e}", exc_info=True)
        raise HttpError(500, f"Внутренняя ошибка сервера: {str(e)}")

@router.post("/login", response={200: TokenSchema, 401: None}, auth=None, summary="Аутентификация пользователя", operation_id="users_login")
def login_user(request, payload: UserLoginSchema):
    """
    Аутентифицирует пользователя и возвращает токен.
    - **username**: Имя пользователя
    - **password**: Пароль
    """
    logger.info(f"Попытка входа пользователя: {payload.username}")
    try:
        user, token_key = authenticate_user_service(payload.username, payload.password)
        logger.info(f"Пользователь '{user.username}' успешно вошел в систему. Токен обновлен/создан в БД.")
        return {"token": token_key}
    except HttpError as e:
        level_to_log = logging.WARNING if e.status_code == 401 else logging.ERROR
        logger.log(level_to_log, f"Ошибка входа пользователя '{payload.username}': {e.message} (HTTP {e.status_code})")
        raise e
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при входе пользователя '{payload.username}': {e}", exc_info=True)
        raise HttpError(500, f"Внутренняя ошибка сервера: {str(e)}")

# Применяем auth=TokenAuthBearer() непосредственно к эндпоинту /me
@router.get("/me", response=UserSchema, auth=TokenAuthBearer(), summary="Получить информацию о текущем пользователе", operation_id="users_get_me")
def get_current_user(request):
    """Возвращает информацию об аутентифицированном пользователе (id, username, email, etc. согласно UserSchema)."""
    logger.info(f"Эндпоинт /me: request.user = {request.user}, request.user.id = {getattr(request.user, 'id', 'N/A')}")
    logger.info(f"Эндпоинт /me: request.user type = {type(request.user)}")
    if hasattr(request.user, 'is_authenticated'):
        logger.info(f"Эндпоинт /me: request.user.is_authenticated = {request.user.is_authenticated}")
    # Если аутентификация на уровне роутера не сработала и не вернула пользователя,
    # то Ninja вернет 401 еще до вызова этого view. 
    # Поэтому здесь request.user должен быть аутентифицированным пользователем.
    if not request.user or not request.user.is_authenticated: # Доп. проверка, хотя должна быть избыточной
        raise HttpError(401, "Пользователь не аутентифицирован или не удалось определить пользователя.")
    return request.user 