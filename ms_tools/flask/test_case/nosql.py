import json
import random
import string
import unittest
from os import getcwd
from os.path import dirname
from typing import Any

from marshmallow import Schema


class CommonTestCase(unittest.TestCase):
    test_db_name = None
    db = None
    client = None
    app_context = None
    maxDiff = None
    authorized = False
    url = None
    request_method = None
    user_model = None

    @classmethod
    def setUpClass(cls, *args):
        """
        Start Flask app end check test database name in current db

        Please pass three arguments:
            args[0] - Function for create flask app
            args[1] - Test config for flask app
            args[2] - DB
        """
        if len(args) < 3:
            raise AssertionError('Please pass three arguments')
        create_flask_func = args[0]
        config = args[1]
        cls.db = args[2]

        # Start flask app
        app = create_flask_func(config)
        cls.client = app.test_client()
        cls.app_context = app.app_context()
        cls.app_context.push()

        # Check test database name in current db
        cls.test_db_name = app.config['TEST_DB_NAME']
        dev_db_name = app.config['DEV_DB_NAME']
        if cls.test_db_name in cls.db.connection.database_names():
            cls.db.connection.drop_database(cls.test_db_name)

        # Create all collections from dev db
        for collection_name in cls.db.connection[dev_db_name].list_collection_names():
            cls.db.connection[cls.test_db_name].create_collection(name=collection_name)

    @classmethod
    def tearDownClass(cls):
        """Delete test data and stop Flask app"""
        # Удаление тестовой базы и завершение Flask приложения
        cls.db.connection.drop_database(cls.test_db_name)
        cls.app_context.pop()

    @classmethod
    def create_user(cls, username='unit@test.ru', password='test_pass', first_name='test', **other_data):
        user_data = {"email": username, "first_name": first_name, "phone": '+1234567890', **other_data}
        if not (auth_user := cls.user_model.objects(**user_data).first()):
            auth_user = cls.user_model.objects.create(**user_data)
        auth_user.set_password(password)
        auth_user.save()
        return auth_user

    def auth(self, auth_url: str = '/api/login/', username: str = 'unit@test.ru', password: str = 'test_pass'):
        """
        Authorization function.

        :param auth_url URL for authorization
        :param username Username
        :param password Password
        """
        json_request = {"email": username, "password": password}
        response = self.client.post(auth_url, json=json_request)
        self.authorized = response.status_code == 200

    def validate_invalid_doc_id(self, error_type='bad_id', error_message_substr='',
                                id_in='url', _id=None, data=None, doc_field='id', status_code=400):
        """
        Validate invalid identifier

        :param error_type
        :param error_message_substr
        :param id_in
        :param _id
        :param data
        :param doc_field
        :param status_code
        """

        args = (self.url,)
        params = {}
        if id_in == 'data':
            params['json'] = {doc_field: _id} if data is None else data
        response = self.request_method(*args, **params)
        json_response = self.check_response(response, status_code)
        self.assertIn('errors', json_response)
        self.assertIn(doc_field, json_response['errors'])
        if error_type == 'not_found':
            self.assertIn('Could not find document.', json_response['errors'][doc_field])
        elif error_type == 'bad_id':
            self.assertEqual(json_response['errors'][doc_field], ['Invalid identifier'])
        if error_message_substr:
            self.assertIn(error_message_substr, json_response['errors'][doc_field])

    def validate_forbidden_access(self, role_keys: list):
        """
        Validate forbidden access

        :param role_keys List not allowed roles
        """
        for role in role_keys:
            self.client.cookie_jar.clear()
            user = self.create_user(username=f'{role}@forbidden.com', password='pass', role=role)
            self.auth(username=user.email, password='pass')
            json_response = self._send_request(expected_status_code=403)
            self.assertIn('errors', json_response)
            self.assertIn("role", json_response['errors'])
            self.assertEqual(f"insufficient rights for {role} role", json_response['errors']['role'])

    def validate_field_in_bad_request(self, field_name: str, valid_type: Any, field_is_required: bool = False):
        """
        Success validate field in bad request

        :param field_name Field name
        :param valid_type Valid type for this field
        :param field_is_required Field is required in request? True/False
        """
        data = {}
        for invalid_param in self.generate_bad_data(valid_type=valid_type):
            data[field_name] = invalid_param
            json_response = self._send_request(params=data, expected_status_code=400)
            self.assertIn('errors', json_response)
            self.assertIn(field_name, json_response['errors'])
        if field_is_required:
            self.validate_required_field(field_name)

    def validate_required_field(self, field_name: str):
        """
        Validate required field

        :param field_name Field is required in request
        """
        json_response = self._send_request(params={}, expected_status_code=400)
        self.assertIn('errors', json_response)
        self.assertIn(field_name, json_response['errors'])

    def validate_error_parse_json(self):
        """Check request. Error, if not json in request"""
        json_response = self._send_request(expected_status_code=400)
        self.assertIn('errors', json_response)
        self.assertIn('common', json_response['errors'])
        self.assertIn('Cannot parse json', json_response['errors']['common'])

    def validate_json(self, response_json, schema):
        """Validate json response"""
        self.assertIsNotNone(response_json)
        validation_errors = schema(unknown='exclude').validate(response_json)
        if validation_errors:
            print(f"Ошибки при валидации ответа: \n{validation_errors}")
        self.assertDictEqual(validation_errors, {})

    def validate_limit(self, return_schema: Schema, limit: int = 20):
        """
        Validate response and limit from GET method

        :param return_schema Marshmallow Schema for validate response
        :param limit Check limit
        """
        json_response = self._send_request()
        self.validate_json(json_response, return_schema)
        self.assertEqual(len(json_response['items']), limit)

    def validate_offset(self, return_schema):
        """
        Validate offset. GET Method

        :param return_schema Marshmallow Schema for validate response
        """
        json_response = self._send_request(params={'limit': 2})
        self.validate_json(json_response, return_schema)
        total_count = json_response['total_count']

        # Set second identifier to var
        self.assertEqual(len(json_response['items']), 2)
        second_doc_id = json_response['items'][1]['id']

        # Request offset=1&limit=1, the identifier specified in second_doc_id is expected
        json_response = self._send_request(params={'limit': 1, 'offset': 1})
        self.validate_json(json_response, return_schema)
        self.assertEqual(json_response['total_count'], total_count)
        self.assertEqual(len(json_response['items']), 1)
        self.assertEqual(json_response['items'][0]['id'], second_doc_id)

    def validate_filter(self,
                        return_schema: Schema,
                        field: str,
                        value: str,
                        check_value: bool = True,
                        icontains: bool = False):
        """
        Validate filtered response

        :param return_schema Marshmallow Schema for validate response
        :param field Filter by field
        :param value value filter
        :param check_value Check value in response
        :param icontains True/False
        """
        json_response = self._send_request(params={field: value})
        self.validate_json(json_response, return_schema)
        items = json_response['items']
        if check_value:
            for item in items:
                self.assertIn(value, item[field]) if icontains else self.assertEqual(value, item[field])
        return items

    def create_success(self, model, required_data):
        """Create success. Only required fields"""
        json_response = self._send_request(params=required_data, expected_status_code=201)
        instance = model.objects.filter(pk=json_response['id']).first()
        self.assertNotEqual(instance, None)
        instance.delete()

    def edit_success(self, edit_obj, edit_field: str, new_value: str, check_new_value=True):
        """
        Success edit object.

        :param edit_obj Object for edit
        :param edit_field Edit field
        :param new_value New value
        :param check_new_value Check new value in edit field. True/False
        """
        json_response = self._send_request(params={edit_field: new_value})
        self.assertIn('status', json_response)
        self.assertEqual('success', json_response['status'])
        edit_obj.reload()
        if check_new_value:
            self.assertEqual(getattr(edit_obj, edit_field), new_value)

    def delete_success(self, delete_obj, deleted_state='hidden'):
        """
        Success delete object

        :param delete_obj Object for delete
        :param deleted_state Deleted state. For check deleted doc.
        """
        json_response = self._send_request(params={"id": delete_obj.id})
        self.assertIn('status', json_response)
        self.assertEqual('success', json_response['status'])
        self.assertEqual(getattr(delete_obj, "state"), deleted_state)

    def check_response(self, response, status_code=200):
        self.assertEqual(response.status_code, status_code)
        self.assertTrue(response.is_json)
        try:
            return response.json
        except Exception:
            self.assertTrue(False)
            return None

    @staticmethod
    def generate_test_data(model, key: str, many: bool = False, count: int = 21, other_data: dict = None):
        """
        Generate test data for devices tests. This method reading file ./test_data.json

        :param model Model instance
        :param key Key in data json
        :param many Create many instances. True/False
        :param count Count create instances. Only many=True.
        :param other_data Other data for create or update default data

        """
        other_data = other_data if other_data else {}
        count_create = count if many else 1
        instance = None
        instances = []

        def get_data_from_file():
            """Read data in json file"""
            test_dir = getcwd()
            if test_dir.split('/')[-1] != 'tests':
                test_dir = dirname(test_dir)
            with open(f'{test_dir}/test_data.json', encoding='utf-8') as file:
                return json.load(file).get(key)

        data = get_data_from_file()
        data.update(other_data)
        for i in range(count_create):
            data = {key: f(value, i=i) if isinstance(value, str) else value for key, value in data.items()}
            if not (instance := model.objects(**data).first()):
                instance = model.objects.create(**data)
            instances.append(instance)
        if not many or count_create == 1:
            return instance
        else:
            return instances

    def generate_bad_data(self, valid_type=None, max_length=None, min_length=None):
        self.assertIsNotNone(valid_type)
        invalid_data_map = {
            int: [None, True, "", {}, [], "string", "string1", {"key": "value"}, ["item1"], [1, 2], 1.45],
            float: [None, True, "", {}, [], "string", "string1", {"key": "value"}, ["item1"], [1, 2]],
            str: [None, True, {}, [], 1, {"key": "value"}, ["item1"], [1, 2]],
            bool: [None, "", {}, [], 123, "string", "string1", {"key": "value"}, ["item1"], [1, 2], 1.45],
            list: [None, "", {}, 123, "string", "string1", {"key": "value"}, 1.45],
            "date": [None, True, {}, [], 1, "string", {"key": "value"}, ["item1"], [1, 2], '2020-01-01 10:10'],
            "datetime": [None, True, {}, [], 1, "string", {"key": "value"}, ["item1"], [1, 2], '2020-01-01'],
            "email": [1, None, True, [], {}, "", "string", {"k": "v"}, ["i"], [1], 1.2]
        }
        bad_data = invalid_data_map[valid_type]

        # TODO Сделать более универсальным max_length min_length
        if max_length is not None:
            bad_item = ""
            for item in range(max_length + 1):
                bad_item += "s"
            bad_data.append(bad_item)

        if min_length is not None:
            if valid_type == str:
                bad_item = ''.join(random.choice(string.ascii_letters + string.digits)
                                   for _ in range(1, min_length))
                bad_data.append(bad_item)
            else:
                bad_data.append(0)

        return bad_data

    def _send_request(self,
                      url: str = None,
                      params: dict = None,
                      return_to_json: bool = True,
                      expected_status_code: int = 200):
        """
        Send request method.

        :param url String url for request
        :param params Parameters for request
        :param return_to_json True/False
        :param expected_status_code Allowed status code in response
        :return Response or json_response
        """
        url_for_request = url if url else self.url
        request_params = {"json": params}
        if self.request_method == self.client.get:
            request_params['params'] = request_params.pop('json', {})
        response = self.request_method(url_for_request, **request_params)
        if return_to_json:
            return self.check_response(response, status_code=expected_status_code)
        return response
