import requests


class AvitoAPI:

    """Класс для работы с API avito.ru"""

    def __init__(self, client_id, client_secret, user_id=None):
        """
        Инициализация класса

        :param client_id Идентификатор магазина
        :param client_secret Секретный ключ магазина
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_id = user_id if user_id else None

    def get_access_token(self):
        """Получение токена в авито"""
        url_get_token = f"https://api.avito.ru/token/?grant_type=client_credentials&" \
                        f"client_id={self.client_id}&client_secret={self.client_secret}"
        r = requests.get(url=url_get_token)
        if 'error' not in r.text:
            access_token = r.json()['access_token']
            self.access_token = access_token
            return r.json()['access_token']
        return r.json()

    def get_last_report(self):
        """Последний отчет по выгрузке"""
        if not self.user_id:
            return {'errors': {'api_avito': 'Не указан user_id'}}
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url_last_report = f"https://api.avito.ru/autoload/v1/accounts/{self.user_id}/reports/last_report/"
        r = requests.get(url=url_last_report, headers=headers)
        return r.json()

    def get_reports(self, per_page=10, page=1):
        """Получение всех отчетов по выгрузкам"""
        if not self.user_id:
            return {'errors': {'api_avito': 'Не указан user_id'}}
        url_reports = f"https://api.avito.ru/autoload/v1/accounts/{self.user_id}/reports/?per_page={per_page}&page={page}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        r = requests.get(url=url_reports, headers=headers)
        return r.json()
