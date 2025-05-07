from ninja import Schema
from pydantic import field_validator, Field


class UserRegisterSchema(Schema):
    username: str = Field(..., min_length=3, max_length=150)
    password: str = Field(..., min_length=8)

    @field_validator("username")
    def username_alphanumeric(cls, value):
        if not value.isalnum():
            # В Django стандартный валидатор для username разрешает @/./+/-/_
            # Здесь для примера более строгая проверка, можно адаптировать
            # или использовать regex для соответствия Django User.username
            allowed_chars = set(
                "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@.+-_"
            )
            if not all(c in allowed_chars for c in value):
                raise ValueError(
                    "Имя пользователя должно содержать только буквы, цифры и символы @.+-_ "
                )
        return value


class UserLoginSchema(Schema):
    username: str
    password: str


class TokenSchema(Schema):
    token: str


class UserSchema(Schema):
    id: int
    username: str
    # email: str | None = None # Если нужно возвращать email
    # first_name: str | None = None
    # last_name: str | None = None

    # Конфигурация для Pydantic V2, чтобы схема могла быть создана из атрибутов ORM объекта
    model_config = {
        "from_attributes": True,
    }
