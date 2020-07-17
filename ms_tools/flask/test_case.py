import unittest


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
            doc.save()

    @classmethod
    def tearDownClass(cls):
        """Delete test data and stop Flask app"""
        for doc in cls.test_docs:
            doc.delete()

        # Завершение Flask приложения
        cls.app_context.pop()

    def auth(self, model, email=None, password=None, create_test_user=False, auth_url='/api/login/'):
        """Auth func"""
        auth_url = auth_url

        email = "unit@test.ru" if not email else email
        first_name = "test_user" if not email else email
        password = "test_pass" if not password else password

        auth_user = model.get_by_email(email)
        test_auth_user = None
        if create_test_user and not auth_user:
            test_auth_user = model.objects.create(email=email, first_name=first_name, state='active')
            test_auth_user.set_password(password)
            test_auth_user.save()
        json = {"email": email, "password": password}
        response = self.client.post(auth_url, json=json)
        self.authorized = True if response.status_code == 200 else False
        if test_auth_user:
            self.test_docs.append(test_auth_user)

    def invalid_doc_id(self, url, method, error_type, id_in='url', _id=None):
        args = (url,)
        params = {}
        if id_in == 'data':
            params['json'] = {"id": _id}
        response = method(*args, **params)
        json = self.check_response(response, 400)
        self.assertIn('errors', json)
        self.assertIn('id', json['errors'])
        if error_type == 'not_found':
            self.assertEqual(json['errors']['id'], 'Document not found')
        elif error_type == 'invalid_id':
            self.assertEqual(json['errors']['id'], 'Invalid id')

    def create_success(self, url, model, field_name, data, check_field=True):
        response = self.client.post(url, json=data)
        json = self.check_response(response, 201)
        model = model.objects.filter(id=json['id']).first()
        self.assertNotEqual(model, None)
        self.test_docs.append(model)
        if check_field:
            self.assertEqual(getattr(model, field_name), data[field_name])
        return model

    def create_failed(self, url, field_name, data, valid_type):
        for invalid_param in self.generate_bad_data(valid_type=valid_type):
            data[field_name] = invalid_param
            response = self.client.post(url, json=data)
            json = self.check_response(response, 400)
            self.assertIn('errors', json)
            self.assertIn(field_name, json['errors'])

    def put_success(self, url, edit_obj, edit_field, new_value, check_new_value=True):
        """Success PUT request"""
        data = {edit_field: new_value}
        response = self.client.put(url, json=data)
        json = self.check_response(response)
        self.assertIn('status', json)
        self.assertEqual('success', json['status'])
        edit_obj.reload()
        if check_new_value:
            self.assertEqual(getattr(edit_obj, edit_field), new_value)

    def put_failed(self, url, edit_field=None, bad_data=None):
        """Check error PUT request"""
        if bad_data is None:
            bad_data = []
        for invalid_param in bad_data:
            data = {edit_field: invalid_param}
            response = self.client.put(url, json=data)
            json = self.check_response(response, 400)
            self.assertIn('errors', json)
            self.assertIn(edit_field, json['errors'])

    def delete_success(self, url, delete_obj):
        """Success DELETE request"""
        response = self.client.delete(url, json={"id": delete_obj.id})
        json = self.check_response(response)
        self.assertIn('status', json)
        self.assertEqual('success', json['status'])
        self.assertEqual(getattr(delete_obj, "state"), "hidden")

    def delete_failed(self, url, bad_data, not_found_doc=False):
        """Check error DELETE request"""
        for invalid_param in bad_data:
            response = self.client.delete(url, json={"id": invalid_param})
            json = self.check_response(response, 400)
            self.assertIn('errors', json)
            self.assertIn("id", json['errors'])
            if not_found_doc:
                self.assertEqual(['Неверный формат идентификатора'], json['errors']['id'])

    def check_response(self, response, status_code=200):
        self.assertEqual(response.status_code, status_code)
        self.assertTrue(response.is_json)
        try:
            return response.json
        except Exception:
            self.assertTrue(False)
            return None

    def validate(self, response_json, schema):
        """Validate json response"""
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
            list: [None, "", {}, 123, "string", "string1", {"key": "value"}, 1.45],
            "date": [None, True, {}, [], 1, "string", {"key": "value"}, ["item1"], [1, 2], '2020-01-01 10:10'],
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
