import unittest

from app import create_app, db
from app.configs.configs import TestConfig
from data_layer import User


class CommonTestCase(unittest.TestCase):
    client = None
    app_context = None
    maxDiff = None
    test_docs = []
    authorized = False

    @classmethod
    def setUpClass(cls):
        """Запуск Flask приложения и создание тестовых данных"""
        cls.app = create_app(TestConfig)
        cls.client = cls.app.test_client()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

        # Создание тестовых данных
        for doc in cls.test_docs:
            db.session.add(doc)
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        """Удаление тестовых данных и завершение Flask приложения"""
        for doc in cls.test_docs:
            doc.delete()
        db.session.commit()

        # Завершение Flask приложения
        cls.app_context.pop()

    @classmethod
    def auth(cls, email=None, password=None, create_test_user=False):
        """ Функция авторизации """
        auth_url = '/api/login/'

        email = "unit@test.ru" if not email else email
        password = "test_pass" if not password else password

        user = User.get_by_email(email)
        if create_test_user and not user:
            User.create(email=email, state='active').set_password(password)
            db.session.commit()
        json = {"email": email, "password": password}
        response = cls.client.post(auth_url, json=json)
        cls.authorized = True if response.status_code == 200 else False
        if user:
            cls.test_docs.append(user)

    def put_success(self, url, edit_obj, edit_field, new_value, check_new_value=True):
        """Успешное выполнение PUT запроса"""
        data = {"id": edit_obj.id, edit_field: new_value}
        response = self.client.put(url, json=data)
        json = self.check_response(response)
        self.assertIn('status', json)
        self.assertEqual('success', json['status'])
        if check_new_value:
            self.assertEqual(getattr(edit_obj, edit_field), new_value)

    def put_failed(self, url, edit_obj, edit_field=None, bad_data=None, not_found_doc=False):
        """Проверка PUT запроса с ошибкой"""
        if bad_data is None:
            bad_data = []
        for invalid_param in bad_data:
            if not_found_doc:
                edit_field = "id"
                data = {edit_field: invalid_param}
            else:
                data = {"id": edit_obj.id, edit_field: invalid_param}
            response = self.client.put(url, json=data)
            json = self.check_response(response, 400)
            self.assertIn('errors', json)
            self.assertIn(edit_field, json['errors'])
            if not_found_doc:
                self.assertEqual(['Не найден документ с таким идентификатором'], json['errors'][edit_field])

    def delete_success(self, url, delete_obj):
        """Успешное выполнение DELETE запроса"""
        response = self.client.delete(url, json={"id": delete_obj.id})
        json = self.check_response(response)
        self.assertIn('status', json)
        self.assertEqual('success', json['status'])
        self.assertEqual(getattr(delete_obj, "state"), "deleted")

    def delete_failed(self, url, bad_data, not_found_doc=False):
        """Проверка DELETE запроса с ошибкой"""
        for invalid_param in bad_data:
            response = self.client.delete(url, json={"id": invalid_param})
            json = self.check_response(response, 400)
            self.assertIn('errors', json)
            self.assertIn("id", json['errors'])
            if not_found_doc:
                self.assertEqual(['Не найден документ с таким идентификатором'], json['errors']['id'])

    def check_response(self, response, status_code=200):
        self.assertEqual(response.status_code, status_code)
        self.assertTrue(response.is_json)
        try:
            return response.json
        except Exception:
            self.assertTrue(False)
            return None

    def validate(self, response_json, schema):
        """ Валидация json ответа """
        self.assertIsNotNone(response_json)
        validation_errors = schema(unknown='exclude').validate(response_json)
        if validation_errors:
            print(f"Ошибки при валидации ответа: \n{validation_errors}")
        self.assertDictEqual(validation_errors, {})

    def generate_bad_data(self, valid_type=None, max_length=None, min_length=None):
        self.assertIsNotNone(valid_type)
        invalid_data_map = {
            int: [None, True, "", {}, [], "string", "string1", {"key": "value"}, ["item1"], [1, 2], 1.45],
            float: [None, True, "", {}, [], "string", "string1", {"key": "value"}, ["item1"], [1, 2]],
            str: [None, True, {}, [], 1, {"key": "value"}, ["item1"], [1, 2]],
            bool: [None, "", {}, [], 123, "string", "string1", {"key": "value"}, ["item1"], [1, 2], 1.45],
            list: [None, "", {}, 123, "string", "string1", {"key": "value"}, 1.45]
        }
        bad_data = invalid_data_map[valid_type]

        # TODO Сделать более универсальным max_length min_length
        if max_length is not None:
            bad_item = ""
            for item in range(max_length + 1):
                bad_item += "s"
            bad_data.append(bad_item)

        if min_length is not None:
            bad_data.append(0)

        return bad_data
