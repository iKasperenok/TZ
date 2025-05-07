from ninja import Schema
from pydantic import Field
from typing import Optional, List
import datetime


# Схема для вывода информации о категории
class CategorySchema(Schema):
    id: int
    name: str
    slug: str


# Схема для вывода информации об авторе (можно использовать UserSchema из apps.users)
# Чтобы избежать циклического импорта или для кастомизации, можно определить здесь урезанную версию
class AuthorSchema(Schema):
    id: int
    username: str


# Схема для вывода статьи
class ArticleOutSchema(Schema):
    id: int
    title: str
    content: str
    author: AuthorSchema  # Используем AuthorSchema для информации об авторе
    category: Optional[CategorySchema] = None  # Категория может отсутствовать
    created_at: datetime.datetime
    updated_at: datetime.datetime
    # slug: Optional[str] = None # Если slug есть в модели Article


# Схема для создания статьи
class ArticleCreateSchema(Schema):
    title: str = Field(..., min_length=5, max_length=200)
    content: str = Field(..., min_length=10)
    category_id: Optional[int] = None  # ID существующей категории


# Схема для обновления статьи
class ArticleUpdateSchema(Schema):
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    content: Optional[str] = Field(None, min_length=10)
    category_id: Optional[int] = None
    # Если нужно разрешить "отвязывать" категорию, передав null


# --- Схемы для Комментариев ---


# Схема для вывода комментария
class CommentOutSchema(Schema):
    id: int
    article_id: int  # ID статьи, к которой относится комментарий
    author: AuthorSchema  # Используем AuthorSchema для информации об авторе
    content: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


# Схема для создания комментария
class CommentCreateSchema(Schema):
    # article_id будет браться из URL
    content: str = Field(..., min_length=1)


# Схема для обновления комментария
class CommentUpdateSchema(Schema):
    content: Optional[str] = Field(None, min_length=1)


# Схема для листинга статей (count + results)
class ArticleListSchema(Schema):
    count: int
    results: List[ArticleOutSchema]
