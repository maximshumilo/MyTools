import logging
import boto3

logger = logging.getLogger(__name__)


class YandexBucket:

    """Класс для работы с облычным хранилищем YandexBucket"""

    def __init__(self, id_key: str, secret_key: str):
        """
        Инициализация класса

        :param id_key Идентификатор
        :param secret_key Секретный ключ
        """

        if not id_key or not secret_key:
            logger.error('Не указаны данные для входа в сервисный аккаунт Yandex Cloud.')
        session = boto3.session.Session()
        self.bucket_client = session.client(service_name='s3', endpoint_url='https://storage.yandexcloud.net',
                                            aws_access_key_id=id_key,
                                            aws_secret_access_key=secret_key)
        self.authorized = self.check_auth()

    def check_auth(self):
        """Получить 1 объект в бакете, для проверки авторизации"""
        try:
            self.bucket_client.list_objects(Bucket='shtab-photos', MaxKeys=1).get('Contents')
        except Exception:
            logger.error('Ошибка авторизации в сервисный аккаунт Yandex Cloud.')
            return False
        return True

    def get_objects(self, bucket_name: str, previous_element: str = '', limit: int = 1000) -> list:
        """
        Получить список объектов в бакете

        :param bucket_name Имя бакета
        :param previous_element:
        :param limit: Лимит выдачи (По умолчанию 1000)
        :return Список объектов бакета
        """
        try:
            result = self.bucket_client.list_objects(Bucket=bucket_name,
                                                     Marker=previous_element, MaxKeys=limit).get('Contents')
        except Exception:
            self.authorized = self.check_auth()
            if self.authorized:
                logger.error('Ошибка при получении списка объектов.')
            return []
        return [] if result is None else result

    def remove_objects(self, bucket_name, data):
        """
            Data list example:
            [{'Key': 'object_name'}, {'Key': 'script/py_script.py'}]
        """
        objects = []
        for obj in data:
            for key, value in obj.items():
                if key == 'Key':
                    objects.append({key: value})
        try:
            self.bucket_client.delete_objects(Bucket=bucket_name, Delete={'Objects': objects})
        except Exception:
            self.authorized = self.check_auth()
            if self.authorized:
                logger.error('Ошибка при удалении списка объектов.')
            return None

    def clear_bucket(self, bucket_name):
        while True:
            objects = self.bucket_client.get_objects(bucket_name)
            if not objects:
                break
            try:
                self.bucket_client.remove_objects(bucket_name, objects)
            except Exception:
                self.authorized = self.check_auth()
                if self.authorized:
                    logger.error('Ошибка при очистке бакета.')
                return None
            logger.info(f"Удалено {str(len(objects))} фотографий.")
        return True

    def upload_file(self, bucket_name, file_name, file_content):
        try:
            response = self.bucket_client.put_object(Bucket=bucket_name, Key=file_name, Body=file_content)
        except Exception:
            self.authorized = self.check_auth()
            if self.authorized:
                logger.error(f"Ошибка при загрузке файла: {file_name}")
            return False
        else:
            if response['ResponseMetadata']['HTTPStatusCode'] != 200:
                logger.error(f"Ошибка при загрузке файла: {file_name}")
                return False
            return True
