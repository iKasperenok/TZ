from django.urls import reverse
from django.contrib.auth.models import User
from django.test import TestCase
import json

# Предполагается, что AuthToken модель существует и используется
from apps.users.models import AuthToken
from apps.users.schemas import UserSchema # Для проверки ответа /me

class UserAPITests(TestCase):
    def setUp(self):
        self.base_api_url = "/api/users" # Общий префикс из urls.py
        self.register_url = f"{self.base_api_url}/register"
        self.login_url = f"{self.base_api_url}/login"
        self.me_url = f"{self.base_api_url}/me" # URL для эндпоинта /me

        self.user_data = {
            "username": "testuser",
            "password": "testpassword123"
        }
        self.another_user_data = { # Для тестов, где нужен второй пользователь
            "username": "anotheruser",
            "password": "anotherpassword456"
        }
        self.wrong_user_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }

    def _get_token_for_user(self, user_payload):
        """Вспомогательный метод для регистрации и получения токена."""
        response = self.client.post(self.register_url, data=json.dumps(user_payload), content_type='application/json')
        self.assertEqual(response.status_code, 201, f"Failed to register user for token retrieval. Response: {response.content.decode()}")
        return response.json()["token"]

    def test_register_success(self):
        """Тест успешной регистрации пользователя."""
        response = self.client.post(self.register_url, data=json.dumps(self.user_data), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        response_data = response.json()
        self.assertIn("token", response_data)
        self.assertTrue(User.objects.filter(username=self.user_data["username"]).exists())
        self.assertTrue(AuthToken.objects.filter(user__username=self.user_data["username"]).exists())
        token_in_db = AuthToken.objects.get(user__username=self.user_data["username"]).key
        self.assertEqual(response_data["token"], token_in_db)

    def test_register_existing_user(self):
        """Тест регистрации с уже существующим именем пользователя."""
        User.objects.create_user(username=self.user_data["username"], password=self.user_data["password"])
        response = self.client.post(self.register_url, data=json.dumps(self.user_data), content_type='application/json')
        self.assertEqual(response.status_code, 409)

    def test_register_invalid_data_empty_password(self):
        """Тест регистрации с невалидными данными (пустой пароль)."""
        invalid_data = {"username": "newuser", "password": ""}
        response = self.client.post(self.register_url, data=json.dumps(invalid_data), content_type='application/json')
        # Pydantic должен вернуть 422, если поле обязательно и пусто (зависит от схемы UserRegisterSchema)
        # Если UserRegisterSchema не имеет валидаторов на мин. длину или непустое значение, Django может создать пользователя с пустым паролем,
        # но create_user_service должен это обработать или модель User.
        # В нашем UserRegisterSchema (из предыдущих файлов) не было явных валидаторов длины.
        # Однако, create_user_service проверяет: if not username or not password:
        self.assertEqual(response.status_code, 422)

    def test_login_success(self):
        """Тест успешного входа пользователя."""
        reg_response = self.client.post(self.register_url, data=json.dumps(self.user_data), content_type='application/json')
        self.assertEqual(reg_response.status_code, 201)
        original_token = reg_response.json()["token"]

        login_response = self.client.post(self.login_url, data=json.dumps(self.user_data), content_type='application/json')
        self.assertEqual(login_response.status_code, 200)
        login_data = login_response.json()
        self.assertIn("token", login_data)
        self.assertNotEqual(original_token, login_data["token"])
        self.assertTrue(AuthToken.objects.filter(user__username=self.user_data["username"], key=login_data["token"]).exists())

    def test_login_wrong_password(self):
        """Тест входа с неверным паролем."""
        User.objects.create_user(username=self.user_data["username"], password=self.user_data["password"])
        response = self.client.post(self.login_url, data=json.dumps(self.wrong_user_data), content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_login_non_existent_user(self):
        """Тест входа с несуществующим пользователем."""
        non_existent_user_data = {"username": "nouser", "password": "anypassword"}
        response = self.client.post(self.login_url, data=json.dumps(non_existent_user_data), content_type='application/json')
        self.assertEqual(response.status_code, 401)

    # Тесты для эндпоинта /me
    def test_me_endpoint_with_valid_token(self):
        """Тест доступа к защищенному эндпоинту /me с валидным токеном."""
        # 1. Создаем пользователя и токен напрямую в БД
        user = User.objects.create_user(username="fixeduser", password="password")
        fixed_token_value = "fixedtesttoken12345"
        AuthToken.objects.create(user=user, key=fixed_token_value)

        auth_header = f"Bearer {fixed_token_value}"
        response = self.client.get(self.me_url, headers={"Authorization": auth_header})
        
        self.assertEqual(response.status_code, 200, f"Response content: {response.content.decode()}")
        response_data = response.json()
        self.assertEqual(response_data["username"], "fixeduser")
        self.assertIn("id", response_data)
        self.assertEqual(response_data["id"], user.id)
        self.assertNotIn("password", response_data)

    def test_me_endpoint_with_invalid_token(self):
        """Тест доступа к /me с невалидным токеном."""
        auth_header = "Bearer invalidtoken123"
        response = self.client.get(self.me_url, headers={"Authorization": auth_header})
        self.assertEqual(response.status_code, 401)

    def test_me_endpoint_without_token(self):
        """Тест доступа к /me без токена."""
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, 401) 