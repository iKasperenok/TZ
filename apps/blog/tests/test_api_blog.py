import json
from django.test import TestCase
from django.contrib.auth.models import User
from apps.blog.models import Article, Category, Comment


class BlogAPITests(TestCase):
    def setUp(self):
        self.users_api_base_url = "/api/users"
        self.blog_api_base_url = "/api/blog"

        # URL для регистрации и логина (для получения токенов)
        self.register_url = f"{self.users_api_base_url}/register"
        self.login_url = f"{self.users_api_base_url}/login"  # Не используется напрямую в этих тестах, но для справки

        # URL для статей
        self.articles_url = f"{self.blog_api_base_url}/articles/"
        self.article_detail_url = lambda pk: f"{self.articles_url}{pk}/"

        # URL для комментариев (пример)
        self.comments_for_article_url = (
            lambda article_pk: f"{self.articles_url}{article_pk}/comments/"
        )
        self.comment_detail_url = lambda pk: f"{self.blog_api_base_url}/comments/{pk}/"

        # Создаем двух пользователей для тестов прав доступа
        self.user1_data = {"username": "user1", "password": "password123"}
        self.user2_data = {"username": "user2", "password": "password456"}

        self.user1_token = self._register_and_get_token(self.user1_data)
        self.user2_token = self._register_and_get_token(self.user2_data)

        self.user1 = User.objects.get(username=self.user1_data["username"])
        self.user2 = User.objects.get(username=self.user2_data["username"])

        # Создаем категорию для тестов
        self.category = Category.objects.create(
            name="Test Category", slug="test-category"
        )

    def _register_and_get_token(self, user_payload):
        response = self.client.post(
            self.register_url,
            data=json.dumps(user_payload),
            content_type="application/json",
        )
        self.assertEqual(
            response.status_code,
            201,
            f"Failed to register user {user_payload['username']}. Response: {response.content.decode()}",
        )
        return response.json()["token"]

    def _get_auth_header(self, token):
        return {"Authorization": f"Bearer {token}"}

    # --- Тесты для Статей (Articles) ---

    def test_create_article_authenticated(self):
        """Тест успешного создания статьи аутентифицированным пользователем."""
        article_data = {
            "title": "My Test Article",
            "content": "This is the content.",
            "category_id": self.category.id,
        }
        response = self.client.post(
            self.articles_url,
            data=json.dumps(article_data),
            content_type="application/json",
            headers=self._get_auth_header(self.user1_token),
        )
        self.assertEqual(response.status_code, 201, response.content.decode())
        response_data = response.json()
        self.assertEqual(response_data["title"], article_data["title"])
        self.assertEqual(response_data["author"]["username"], self.user1.username)
        self.assertTrue(
            Article.objects.filter(
                title=article_data["title"], author=self.user1
            ).exists()
        )

    def test_create_article_unauthenticated(self):
        """Тест попытки создания статьи неаутентифицированным пользователем."""
        article_data = {"title": "Unauthorized Article", "content": "Content."}
        response = self.client.post(
            self.articles_url,
            data=json.dumps(article_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_list_articles_public(self):
        """Тест получения списка статей (публичный доступ)."""
        Article.objects.create(
            author=self.user1, title="Public Article 1", content="Content 1"
        )
        Article.objects.create(
            author=self.user2, title="Public Article 2", content="Content 2"
        )
        response = self.client.get(self.articles_url)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        # Django Ninja пагинация возвращает results в results или items, проверим API
        # Судя по коду в apps/blog/api.py используется PageNumberPagination, который по умолчанию кладет в 'items'
        # Но если используется Global NinjaAPI response wrapper, может быть 'results'
        # Давайте предположим, что это стандартный PageNumberPagination, который возвращает список напрямую или в items/results.
        # По умолчанию, PageNumberPagination возвращает объект с полями count, next, previous, results
        self.assertIn("results", response_data)  # Для PageNumberPagination с Ninja
        self.assertEqual(len(response_data["results"]), 2)
        # Убедимся, что пагинация работает, проверив наличие count
        self.assertIn("count", response_data)
        self.assertEqual(response_data["count"], 2)

    def test_get_article_detail_public(self):
        """Тест получения одной статьи (публичный доступ)."""
        article = Article.objects.create(
            author=self.user1, title="Detail Article", content="Detail Content"
        )
        response = self.client.get(self.article_detail_url(article.pk))
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data["title"], article.title)

    def test_update_own_article_authenticated(self):
        """Тест обновления своей статьи аутентифицированным пользователем."""
        article = Article.objects.create(
            author=self.user1, title="Original Title", content="Original Content"
        )
        update_data = {"title": "Updated Title", "content": "Updated Content"}
        response = self.client.put(
            self.article_detail_url(article.pk),
            data=json.dumps(update_data),
            content_type="application/json",
            headers=self._get_auth_header(self.user1_token),
        )
        self.assertEqual(response.status_code, 200, response.content.decode())
        article.refresh_from_db()
        self.assertEqual(article.title, update_data["title"])
        self.assertEqual(article.content, update_data["content"])

    def test_update_other_user_article_forbidden(self):
        """Тест попытки обновления чужой статьи (статус 403)."""
        article_by_user1 = Article.objects.create(
            author=self.user1, title="User1s Article", content="Content"
        )
        update_data = {"title": "Malicious Update"}
        response = self.client.put(
            self.article_detail_url(article_by_user1.pk),
            data=json.dumps(update_data),
            content_type="application/json",
            headers=self._get_auth_header(self.user2_token),
        )
        self.assertEqual(response.status_code, 403)

    def test_update_article_unauthenticated(self):
        """Тест попытки обновления статьи неаутентифицированным пользователем (статус 401)."""
        article = Article.objects.create(
            author=self.user1, title="Some Article", content="Content"
        )
        update_data = {"title": "Anonymous Update"}
        response = self.client.put(
            self.article_detail_url(article.pk),
            data=json.dumps(update_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_delete_own_article_authenticated(self):
        """Тест удаления своей статьи аутентифицированным пользователем."""
        article = Article.objects.create(
            author=self.user1, title="To Be Deleted", content="Content"
        )
        response = self.client.delete(
            self.article_detail_url(article.pk),
            headers=self._get_auth_header(self.user1_token),
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Article.objects.filter(pk=article.pk).exists())

    def test_delete_other_user_article_forbidden(self):
        """Тест попытки удаления чужой статьи (статус 403)."""
        article_by_user1 = Article.objects.create(
            author=self.user1, title="User1s Article To Delete", content="Content"
        )
        response = self.client.delete(
            self.article_detail_url(article_by_user1.pk),
            headers=self._get_auth_header(self.user2_token),
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Article.objects.filter(pk=article_by_user1.pk).exists())

    def test_delete_article_unauthenticated(self):
        """Тест попытки удаления статьи неаутентифицированным пользователем (статус 401)."""
        article = Article.objects.create(
            author=self.user1, title="Another Article", content="Content"
        )
        response = self.client.delete(self.article_detail_url(article.pk))
        self.assertEqual(response.status_code, 401)
        self.assertTrue(Article.objects.filter(pk=article.pk).exists())

    # --- Тесты для Комментариев (Comments) ---

    def test_create_comment_authenticated(self):
        """Тест успешного создания комментария аутентифицированным пользователем."""
        article = Article.objects.create(author=self.user1, title="Art", content="Cnt")
        comment_data = {"content": "Test Comment"}
        response = self.client.post(
            self.comments_for_article_url(article.pk),
            data=json.dumps(comment_data),
            content_type="application/json",
            headers=self._get_auth_header(self.user1_token),
        )
        self.assertEqual(response.status_code, 201, response.content.decode())
        data = response.json()
        self.assertEqual(data["content"], comment_data["content"])
        self.assertTrue(Comment.objects.filter(pk=data["id"], author=self.user1).exists())

    def test_create_comment_unauthenticated(self):
        """Тест создания комментария без аутентификации (401)."""
        article = Article.objects.create(author=self.user1, title="Art2", content="Cnt2")
        comment_data = {"content": "Anon Comment"}
        response = self.client.post(
            self.comments_for_article_url(article.pk),
            data=json.dumps(comment_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_list_comments_public(self):
        """Тест получения списка комментариев к статье (публично)."""
        article = Article.objects.create(author=self.user1, title="Art3", content="Cnt3")
        Comment.objects.create(article=article, author=self.user1, content="C1")
        Comment.objects.create(article=article, author=self.user2, content="C2")
        response = self.client.get(self.comments_for_article_url(article.pk))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("results", data)
        self.assertEqual(len(data["results"]), 2)
        self.assertIn("count", data)
        self.assertEqual(data["count"], 2)

    def test_update_own_comment_authenticated(self):
        """Тест обновления своего комментария."""
        article = Article.objects.create(author=self.user1, title="Art4", content="Cnt4")
        comment = Comment.objects.create(article=article, author=self.user1, content="Orig")
        update_data = {"content": "Updated"}
        response = self.client.put(
            self.comment_detail_url(comment.pk),
            data=json.dumps(update_data),
            content_type="application/json",
            headers=self._get_auth_header(self.user1_token),
        )
        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db()
        self.assertEqual(comment.content, update_data["content"])

    def test_update_other_user_comment_forbidden(self):
        """Тест обновления чужого комментария (403)."""
        article = Article.objects.create(author=self.user1, title="Art5", content="Cnt5")
        comment = Comment.objects.create(article=article, author=self.user1, content="Orig2")
        response = self.client.put(
            self.comment_detail_url(comment.pk),
            data=json.dumps({"content": "Bad"}),
            content_type="application/json",
            headers=self._get_auth_header(self.user2_token),
        )
        self.assertEqual(response.status_code, 403)

    def test_update_comment_unauthenticated(self):
        """Тест обновления комментария без аутентификации (401)."""
        article = Article.objects.create(author=self.user1, title="Art6", content="Cnt6")
        comment = Comment.objects.create(article=article, author=self.user1, content="Orig3")
        response = self.client.put(
            self.comment_detail_url(comment.pk),
            data=json.dumps({"content": "AnonUpdate"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_delete_own_comment_authenticated(self):
        """Тест удаления своего комментария."""
        article = Article.objects.create(author=self.user1, title="Art7", content="Cnt7")
        comment = Comment.objects.create(article=article, author=self.user1, content="Del")
        response = self.client.delete(
            self.comment_detail_url(comment.pk),
            headers=self._get_auth_header(self.user1_token),
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

    def test_delete_other_user_comment_forbidden(self):
        """Тест удаления чужого комментария (403)."""
        article = Article.objects.create(author=self.user1, title="Art8", content="Cnt8")
        comment = Comment.objects.create(article=article, author=self.user1, content="Del2")
        response = self.client.delete(
            self.comment_detail_url(comment.pk),
            headers=self._get_auth_header(self.user2_token),
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())

    def test_delete_comment_unauthenticated(self):
        """Тест удаления комментария без аутентификации (401)."""
        article = Article.objects.create(author=self.user1, title="Art9", content="Cnt9")
        comment = Comment.objects.create(article=article, author=self.user1, content="Del3")
        response = self.client.delete(self.comment_detail_url(comment.pk))
        self.assertEqual(response.status_code, 401)
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())
