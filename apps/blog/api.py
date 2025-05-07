import logging # Импортируем logging
from typing import List, Optional
from ninja import Router, Form
from ninja.pagination import paginate, PageNumberPagination # Для пагинации
from ninja.errors import HttpError
from django.http import Http404 # <--- Добавляем импорт

from django.shortcuts import get_object_or_404
# User модель больше не нужна здесь напрямую, так как request.user будет объектом User
# from django.contrib.auth.models import User 

from .models import Article, Category, Comment
from .schemas import (
    ArticleOutSchema, ArticleCreateSchema, ArticleUpdateSchema, CategorySchema,
    CommentOutSchema, CommentCreateSchema, CommentUpdateSchema
)
# Импортируем аутентификатор из приложения users
# Изменяем SimpleTokenAuth на TokenAuthBearer
from apps.users.api import TokenAuthBearer # Убедитесь, что этот импорт корректен

logger = logging.getLogger(__name__) # Получаем логгер

router = Router(tags=["Статьи и Категории"])

# Применяем TokenAuthBearer ко всем эндпоинтам этого роутера, требующим аутентификации
# Для публичных эндпоинтов (list, get) auth не указывается или auth=None

# --- Эндпоинты для Категорий (опционально, но полезно) ---
@router.get("/categories", response=List[CategorySchema], summary="Получить список всех категорий", operation_id="list_categories")
def list_categories(request):
    logger.info("Запрошен список категорий")
    return Category.objects.all()

@router.get("/categories/{category_id}", response=CategorySchema, summary="Получить категорию по ID", operation_id="get_category")
def get_category(request, category_id: int):
    logger.info(f"Запрошена категория с ID: {category_id}")
    category = get_object_or_404(Category, id=category_id)
    return category

# Можно добавить CRUD для категорий, если это требуется админам через API
# Например, @router.post("/categories", response=CategorySchema, auth=SimpleTokenAuth(), summary="Создать категорию (требует аутентификации)")

# --- Эндпоинты для Статей ---

@router.post("/articles", response={201: ArticleOutSchema}, auth=TokenAuthBearer(), summary="Создать новую статью", operation_id="create_article")
def create_article(request, payload: ArticleCreateSchema):
    """
    Создает новую статью. Требуется аутентификация.
    Автор статьи устанавливается автоматически на основе аутентифицированного пользователя.
    """
    logger.info(f"Попытка создания новой статьи пользователем: {request.user.username if request.user and request.user.is_authenticated else 'anonymous'}")
    # request.user должен быть установлен SimpleTokenAuth
    if not request.user or not request.user.is_authenticated:
        logger.warning("Попытка создания статьи без аутентификации или не удалось определить пользователя.")
        raise HttpError(401, "Аутентификация не пройдена или не удалось определить пользователя.")
    
    author = request.user

    try:
        data = payload.dict()
        category = None
        category_id = data.pop("category_id", None)
        if category_id is not None:
            category = get_object_or_404(Category, id=category_id)
        
        article = Article.objects.create(author=author, category=category, **data)
        logger.info(f"Статья '{article.title}' (ID: {article.id}) успешно создана пользователем '{author.username}'.")
        return 201, article
    except Http404: # Обработка get_object_or_404 для категории
        logger.warning(f"Ошибка при создании статьи: категория с ID {category_id} не найдена.")
        raise # Перевыбрасываем, чтобы Ninja вернул 404
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при создании статьи пользователем '{author.username}': {e}", exc_info=True)
        raise HttpError(500, "Внутренняя ошибка сервера при создании статьи.")

@router.get("/articles", response=List[ArticleOutSchema], summary="Получить список всех статей", operation_id="list_articles")
@paginate(PageNumberPagination, page_size=10) # Добавляем пагинацию
def list_articles(request):
    logger.info("Запрошен список статей")
    return Article.objects.all().select_related('author', 'category').order_by('-created_at')

@router.get("/articles/{article_id}", response=ArticleOutSchema, summary="Получить статью по ID", operation_id="get_article")
def get_article(request, article_id: int):
    logger.info(f"Запрошена статья с ID: {article_id}")
    article = get_object_or_404(Article.objects.select_related('author', 'category'), id=article_id)
    return article

@router.put("/articles/{article_id}", response=ArticleOutSchema, auth=TokenAuthBearer(), summary="Обновить статью", operation_id="update_article")
def update_article(request, article_id: int, payload: ArticleUpdateSchema):
    logger.info(f"Попытка обновления статьи ID: {article_id} пользователем: {request.user.username if request.user and request.user.is_authenticated else 'anonymous'}")
    if not request.user or not request.user.is_authenticated:
        logger.warning(f"Обновление статьи ID {article_id}: отказано (401, аутентификация не пройдена).")
        raise HttpError(401, "Аутентификация не пройдена")

    article = get_object_or_404(Article, id=article_id)

    if article.author != request.user:
        logger.warning(f"Обновление статьи ID {article_id} пользователем '{request.user.username}': отказано (403, нет прав).")
        raise HttpError(403, "У вас нет прав на обновление этой статьи")

    try:
        updated_fields_count = 0
        for attr, value in payload.dict(exclude_unset=True).items():
            # Проверка на изменение category_id, если он есть в payload
            if attr == "category_id":
                if value is not None:
                    category = get_object_or_404(Category, id=value)
                    article.category = category
                else:
                    article.category = None # Разрешаем открепление категории
            else:
                setattr(article, attr, value)
            updated_fields_count +=1
        
        if updated_fields_count > 0: # Сохраняем только если были изменения
            article.save()
            logger.info(f"Статья ID {article_id} успешно обновлена пользователем '{request.user.username}'.")
        else:
            logger.info(f"Обновление статьи ID {article_id} пользователем '{request.user.username}': не было полей для обновления.")
        return article
    except Http404: # Обработка get_object_or_404 для категории при обновлении
        logger.warning(f"Ошибка при обновлении статьи ID {article_id}: категория не найдена.")
        raise
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при обновлении статьи ID {article_id} пользователем '{request.user.username}': {e}", exc_info=True)
        raise HttpError(500, "Внутренняя ошибка сервера при обновлении статьи.")

@router.delete("/articles/{article_id}", response={204: None}, auth=TokenAuthBearer(), summary="Удалить статью", operation_id="delete_article")
def delete_article(request, article_id: int):
    logger.info(f"Попытка удаления статьи ID: {article_id} пользователем: {request.user.username if request.user and request.user.is_authenticated else 'anonymous'}")
    if not request.user or not request.user.is_authenticated:
        logger.warning(f"Удаление статьи ID {article_id}: отказано (401, аутентификация не пройдена).")
        raise HttpError(401, "Аутентификация не пройдена")

    article = get_object_or_404(Article, id=article_id)

    if article.author != request.user:
        logger.warning(f"Удаление статьи ID {article_id} пользователем '{request.user.username}': отказано (403, нет прав).")
        raise HttpError(403, "У вас нет прав на удаление этой статьи")
    
    try:
        article_title_for_log = article.title
        article.delete()
        logger.info(f"Статья '{article_title_for_log}' (ID: {article_id}) успешно удалена пользователем '{request.user.username}'.")
        return 204, None
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при удалении статьи ID {article_id} пользователем '{request.user.username}': {e}", exc_info=True)
        raise HttpError(500, "Внутренняя ошибка сервера при удалении статьи.")

# --- Эндпоинты для Комментариев ---

@router.post("/articles/{article_id}/comments", response={201: CommentOutSchema}, auth=TokenAuthBearer(), summary="Добавить комментарий к статье", operation_id="create_comment")
def create_comment(request, article_id: int, payload: CommentCreateSchema):
    logger.info(f"Попытка добавления комментария к статье ID: {article_id} пользователем: {request.user.username if request.user and request.user.is_authenticated else 'anonymous'}")
    if not request.user or not request.user.is_authenticated:
        logger.warning(f"Создание комментария к статье ID {article_id}: отказано (401, аутентификация не пройдена).")
        raise HttpError(401, "Аутентификация не пройдена")
    
    article = get_object_or_404(Article, id=article_id)
    author_for_comment = request.user

    try:
        comment = Comment.objects.create(
            article=article,
            author=author_for_comment,
            content=payload.content
        )
        logger.info(f"Комментарий ID {comment.id} успешно создан к статье ID {article_id} пользователем '{author_for_comment.username}'.")
        return comment
    except Http404: # На случай если get_object_or_404 для article не сработает выше (хотя должен)
        logger.warning(f"Попытка создания комментария к несуществующей статье ID {article_id} пользователем '{author_for_comment.username}'.")
        raise
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при создании комментария к статье ID {article_id} пользователем '{author_for_comment.username}': {e}", exc_info=True)
        raise HttpError(500, "Внутренняя ошибка сервера при создании комментария.")

@router.get("/articles/{article_id}/comments", response=List[CommentOutSchema], summary="Получить комментарии к статье", operation_id="list_comments")
@paginate(PageNumberPagination, page_size=10)
def list_comments_for_article(request, article_id: int):
    logger.info(f"Запрошены комментарии для статьи ID: {article_id}")
    article = get_object_or_404(Article, id=article_id)
    return Comment.objects.filter(article=article).select_related('author').order_by('created_at')

@router.get("/comments/{comment_id}", response=CommentOutSchema, summary="Получить комментарий по ID", operation_id="get_comment")
def get_comment(request, comment_id: int):
    logger.info(f"Запрошен комментарий с ID: {comment_id}")
    comment = get_object_or_404(Comment.objects.select_related('author', 'article'), id=comment_id)
    return comment

@router.put("/comments/{comment_id}", response=CommentOutSchema, auth=TokenAuthBearer(), summary="Обновить комментарий", operation_id="update_comment")
def update_comment(request, comment_id: int, payload: CommentUpdateSchema):
    logger.info(f"Попытка обновления комментария ID: {comment_id} пользователем: {request.user.username if request.user and request.user.is_authenticated else 'anonymous'}")
    if not request.user or not request.user.is_authenticated:
        logger.warning(f"Обновление комментария ID {comment_id}: отказано (401, аутентификация не пройдена).")
        raise HttpError(401, "Аутентификация не пройдена")

    comment = get_object_or_404(Comment, id=comment_id)

    if comment.author != request.user:
        logger.warning(f"Обновление комментария ID {comment_id} пользователем '{request.user.username}': отказано (403, нет прав).")
        raise HttpError(403, "У вас нет прав на обновление этого комментария")
    
    try:
        if payload.content:
            comment.content = payload.content
            comment.save()
            logger.info(f"Комментарий ID {comment_id} успешно обновлен пользователем '{request.user.username}'.")
        else:
            logger.info(f"Обновление комментария ID {comment_id} пользователем '{request.user.username}': не было данных для обновления (content был пустым).")
        return comment
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при обновлении комментария ID {comment_id} пользователем '{request.user.username}': {e}", exc_info=True)
        raise HttpError(500, "Внутренняя ошибка сервера при обновлении комментария.")

@router.delete("/comments/{comment_id}", response={204: None}, auth=TokenAuthBearer(), summary="Удалить комментарий", operation_id="delete_comment")
def delete_comment(request, comment_id: int):
    logger.info(f"Попытка удаления комментария ID: {comment_id} пользователем: {request.user.username if request.user and request.user.is_authenticated else 'anonymous'}")
    if not request.user or not request.user.is_authenticated:
        logger.warning(f"Удаление комментария ID {comment_id}: отказано (401, аутентификация не пройдена).")
        raise HttpError(401, "Аутентификация не пройдена")

    comment = get_object_or_404(Comment, id=comment_id)

    if comment.author != request.user:
        logger.warning(f"Удаление комментария ID {comment_id} пользователем '{request.user.username}': отказано (403, нет прав).")
        raise HttpError(403, "У вас нет прав на удаление этого комментария")

    try:
        comment.delete()
        logger.info(f"Комментарий ID {comment_id} успешно удален пользователем '{request.user.username}'.")
        return 204, None
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при удалении комментария ID {comment_id} пользователем '{request.user.username}': {e}", exc_info=True)
        raise HttpError(500, "Внутренняя ошибка сервера при удалении комментария.") 