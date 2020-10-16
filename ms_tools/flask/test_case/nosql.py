import json
import os
import random
import string
import unittest
from datetime import datetime, date
from os.path import join as path_join
from typing import Any, Type, Union
from copy import deepcopy

from marshmallow import Schema
from mongoengine.base import TopLevelDocumentMetaclass
from snuff_utils.string_functions import f
from mongoengine import connect


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
    test_docs = []
    test_data_file_name = None
    _base_dir = None
    models_map = None
    counter_map = {}
    user_for_auth = None

    @classmethod
    def setUpClass(cls, create_app, config, db, *args):
        """
        Start Flask app end check test database name in current db

        :param create_app: Function for create Flask app
        :param config: Config for Flask app
        :param db: Database for tests
        """
        # Start flask app
        app = create_app(config)
        cls.client = app.test_client()
        cls.app_context = app.app_context()
        cls.app_context.push()
        cls.db = db
        cls._prepare_database(config=config, db=db)

    @classmethod
    def _prepare_database(cls, config, db):
        """Prepare test database"""
        cls.test_db_name = db.connection._MongoClient__default_database_name

        # Check test database name in test db
        if cls.test_db_name in db.connection.list_database_names():
            db.connection.drop_database(cls.test_db_name)

        # Create all collections from dev db
        for collection_name in list(set([item._get_collection_name() for item in cls.models_map.values()])):
            db.connection[cls.test_db_name].create_collection(name=collection_name)

    @classmethod
    def tearDownClass(cls):
        """Delete test data and stop Flask app"""
        # Удаление тестовой базы и завершение Flask приложения
        cls.db.connection.drop_database(cls.test_db_name)
        cls.app_context.pop()

    @classmethod
    def setUp(cls):
        if not cls.request_method:
            raise AssertionError("Not found request method!")

    @classmethod
    def create_user(cls, key: str, password: str = 'test_pass', **other_data):
        cls.user_for_auth = cls.generate_test_data(key=key, **other_data)
        cls.user_for_auth.set_password(password)
        cls.user_for_auth.save()
        cls.pass_for_auth = password
        return cls.user_for_auth

    def auth(self, auth_url: str = '/api/login/', blocked_user: bool = False, not_found_user: bool = False):
        """
        Authorization function.

        :param auth_url URL for authorization
        :param username Username
        :param password Password
        :param blocked_user
        :param not_found_user
        """
        self.client.cookie_jar.clear()
        self.authorized = False
        username = self.user_for_auth.email
        status_code = 400 if blocked_user or not_found_user else 200
        json_request = {"email": username, "password": self.pass_for_auth}
        json_response = self._send_request(url=auth_url, params=json_request, expected_status_code=status_code,
                                           request_method=self.client.post)
        if blocked_user:
            self.assertIn('errors', json_response)
            self.assertIn("email", json_response['errors'])
            self.assertEqual("The user is blocked.", json_response['errors']["email"])
        elif not_found_user:
            self.assertIn('errors', json_response)
            self.assertIn("email", json_response['errors'])
            self.assertEqual("No user found for this email address.", json_response['errors']["email"])
        else:
            self.authorized = True
            self.assertIn("email", json_response)
            self.assertEqual(username, json_response["email"])

    def validate_invalid_doc_id(self, id_in_data: bool = False, field: str = 'pk', bad_id: str = 'a1',
                                status_code: int = 400, many: bool = False):
        """
        Validate invalid identifier

        :param id_in_data
        :param field
        :param bad_id
        :param status_code
        :param many
        """
        if many:
            bad_id = [bad_id]
        if id_in_data:
            request_data = {field: bad_id}
            url = self.url
        else:
            request_data = {}
            url = '/'.join(self.url.split('/')[:-2] + [bad_id])
        json_response = self._send_request(url=url, params=request_data, expected_status_code=status_code)
        if many:
            return self.assertIn('Could not find document.', json_response['errors'][field])
        self.assertIn('Could not find document.', json_response['errors'][field])

    def validate_not_found_doc(self,
                               id_in_data: bool = False,
                               field: str = 'pk',
                               status_code: int = 400,
                               not_found_id: str = '555555555555555555555555',
                               many: bool = False):
        """
        Validate error: Could not find document.

        :param id_in_data True/False. (False = id in url)
        :param field Field (Only id_in_data=True)
        :param not_found_id Not found id
        :param status_code Expected status code
        :param many
        """
        if id_in_data:
            if many:
                not_found_id = [not_found_id]
            request_data = {field: not_found_id}
            url = self.url
        else:
            request_data = {}
            url = self.template_url.format(**{field: not_found_id})
        json_response = self._send_request(url=url, params=request_data, expected_status_code=status_code)
        if many:
            return self.assertIn(f'Could not find document.', json_response['errors'][field])
        self.assertIn(f'Could not find document.', json_response['errors'][field])

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

    def validate_field_in_bad_request(self,
                                      field_name: str,
                                      valid_type: Any = None,
                                      bad_data: list = None,
                                      field_is_required: bool = False,
                                      required_data: dict = None):
        """
        Success validate field in bad request

        :param field_name Field name
        :param valid_type Valid type for this field
        :param bad_data Bad data
        :param field_is_required Field is required in request? True/False
        :param required_data Required data for request
        """
        data = {}
        bad_data = bad_data if bad_data else self.generate_bad_data(valid_type=valid_type)
        json_response = None
        for invalid_param in bad_data:
            if required_data:
                data.update(required_data)
            data[field_name] = invalid_param

            json_response = self._send_request(params=data, expected_status_code=400)
            self.assertIn('errors', json_response)
            self.assertIn(field_name, json_response['errors'])
        if field_is_required:
            self.validate_required_field(field_name)
        return json_response

    def validate_required_field(self, field_name: str):
        """
        Validate required field

        :param field_name Field is required in request
        """
        json_response = self._send_request(params={"test": "data"}, expected_status_code=400)
        self.assertIn('errors', json_response)
        self.assertIn(field_name, json_response['errors'])
        self.assertIn('Missing data for required field.', json_response['errors'][field_name])

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

    def validate_response(self, return_schema: Type[Schema], limit: int = None):
        """
        Validate response and limit from GET method

        :param return_schema Marshmallow Schema for validate response
        :param limit Check limit
        """
        json_response = self._send_request()
        self.validate_json(json_response, return_schema)
        if limit:
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
                        return_schema: Type[Schema],
                        field: str,
                        value: Union[bool, str, int, list],
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

    def validate_sorting(self, field_name: str, return_schema: Type[Schema], reverse: bool = True):
        """
        Validate sorting

        :param field_name Order by field name
        :param return_schema Return schema
        :param reverse Reverse sorting
        """
        json_response = self._send_request(params={"order_by": f"-{field_name}" if reverse else field_name})
        self.validate_json(json_response, return_schema)
        first_iteration = True
        self.assertGreater(json_response["total_count"], 0)
        prev_value = None
        for item in json_response['items']:
            if first_iteration:
                prev_value = item[field_name]
                first_iteration = False
                continue
            if reverse:
                self.assertLessEqual(item[field_name], prev_value)
            else:
                self.assertGreaterEqual(item[field_name], prev_value)

    def create_success(self, model, required_data):
        """Create success. Only required fields"""
        json_response = self._send_request(params=required_data, expected_status_code=201)
        instance = model.objects.filter(pk=json_response['id']).first()
        self.assertNotEqual(instance, None)
        instance.delete()

    def edit_success(self, edit_obj, edit_field: str, new_value: Union[str, list, int], check_new_value=True):
        """
        Success edit object.

        :param edit_obj Object for edit
        :param edit_field Edit field
        :param new_value New value
        :param check_new_value Check new value in edit field. True/False
        """
        url = '/'.join(self.url.split('/')[:-2] + [str(edit_obj.id)])
        json_response = self._send_request(url=url, params={edit_field: new_value})
        self.assertIn('status', json_response)
        self.assertEqual('success', json_response['status'])
        edit_obj.reload()
        if check_new_value:
            self.assertEqual(getattr(edit_obj, edit_field), new_value)

    def edit_success_all_fields(self, edit_obj, data: dict, check_new_values: bool = True):
        """
        Success edit object. (All fields)

        :param edit_obj Object for edit
        :param data Data
        :param check_new_values Check new values. True/False
        """
        url = '/'.join(self.url.split('/')[:-2] + [str(edit_obj.id)])
        json_response = self._send_request(url=url, params=data)
        self.assertIn('status', json_response)
        self.assertEqual('success', json_response['status'])
        edit_obj.reload()
        if check_new_values:
            self._check_new_values(edit_obj, expected_values=data)

    def delete_success(self, delete_obj, deleted_state='deleted'):
        """
        Success delete object

        :param delete_obj Object for delete
        :param deleted_state Deleted state. For check deleted doc.
        """
        json_response = self._send_request(params={"id": str(delete_obj.id)})
        self.assertIn('status', json_response)
        self.assertEqual('success', json_response['status'])
        delete_obj.reload()
        self.assertEqual(getattr(delete_obj, "state"), deleted_state)

    def check_response(self, response, status_code=200):
        self.assertEqual(status_code, response.status_code)
        self.assertTrue(response.is_json)
        try:
            return response.json
        except Exception:
            self.assertTrue(False)
            return None

    @classmethod
    def generate_test_data(cls, key: str, many: bool = False, count: int = 21, **other_fields):
        """
        Generate test data for devices tests. This method reading file ./test_data.json

        :param key Model name in data json
        :param many Create many instances. True/False
        :param count Count create instances. Only many=True.
        :param other_fields Other data for create or update default data

        """
        if not cls.test_data_file_name or not cls._base_dir:
            raise AssertionError("Error! ")
        if not (model := cls.models_map.get(key)):
            raise AssertionError("Error! ")

        other_data = other_fields if other_fields else {}
        count_create = count if many else 1
        instance = None
        instances = []

        def get_data_from_file():
            """Read data in json file"""
            path = path_join(cls._base_dir, "backend", 'app', 'tests', cls.test_data_file_name)
            if os.path.exists(path) and os.path.isfile(path):
                with open(path, encoding='utf-8') as file:
                    return json.load(file).get(key)
            else:
                raise AssertionError(f'File not found! {path}')

        raw_data = get_data_from_file()
        raw_data.update(other_data)
        for i in range(count_create):
            data = cls._counter_data(key_object=key, raw_data=raw_data)
            instance = model.objects.create(**data)
            instances.append(instance)
            cls.test_docs.append(instance)
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
            "email": [1, None, True, [], {}, "", "string", {"k": "v"}, ["i"], [1], 1.2],
            "doc_id": [None, True, {}, [], {"key": "value"}, ["item1"], [1, 2]],
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

    @classmethod
    def _counter_data(cls, key_object, raw_data):
        new_data = {}
        for field, value in deepcopy(raw_data).items():
            if isinstance(value, str) and '{i}' in value:
                cls.counter_map.setdefault(key_object, {})
                last_count = cls.counter_map[key_object].get(field, 0)
                cls.counter_map[key_object][field] = last_count + 1
                new_data[field] = value.format(i=cls.counter_map[key_object][field])
            else:
                new_data[field] = value
        return new_data

    def _send_request(self,
                      url: str = None,
                      params: dict = None,
                      return_to_json: bool = True,
                      expected_status_code: int = 200,
                      request_method: Any = None):
        """
        Send request method.

        :param url String url for request
        :param params Parameters for request
        :param return_to_json True/False
        :param expected_status_code Allowed status code in response
        :return Response or json_response
        """
        url_for_request = url if url else self.url
        request_method = request_method if request_method else self.request_method
        if params:
            request_params = {"json": params}
            if request_method == self.client.get:
                request_params['query_string'] = request_params.pop('json', {})
        else:
            request_params = {}
        response = request_method(url_for_request, **request_params)
        self.assertEqual(expected_status_code, response.status_code)
        if return_to_json:
            return self.check_response(response, status_code=expected_status_code)
        return response

    def _check_new_values(self, document, expected_values):
        """
        Check new values in document.

        :param document Document for check
        :param expected_values Expected values
        """

        def convert_value_to_str(value):
            if isinstance(value, str):
                return value
            elif isinstance(value.__class__, TopLevelDocumentMetaclass):
                return str(value.id)
            else:
                raise AssertionError("Error convert to string: unknown type")

        document.reload()
        for field, exp_value in expected_values.items():
            cur_value = getattr(document, field)
            if isinstance(cur_value, list) and isinstance(exp_value, list):
                for sub_value in cur_value:
                    self.assertIn(convert_value_to_str(sub_value), exp_value)
            elif isinstance(cur_value, datetime):
                self.assertEqual(datetime.strptime(exp_value, "%Y-%m-%dT%H:%M:%S.%fZ"), cur_value)
            elif isinstance(cur_value, date):
                self.assertEqual(datetime.strptime(exp_value, "%Y-%m-%d").date(), cur_value)
            elif field == 'password':
                self.assertEqual(document.check_password(exp_value), True)
            else:
                self.assertEqual(exp_value, convert_value_to_str(cur_value))
