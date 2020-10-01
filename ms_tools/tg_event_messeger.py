import requests


class EventMessenger:

    """
    Класс для отправки событий в чат ТГ
    """

    def __init__(self, url: str, secret: str = None, host: str = None, chat_id: str = None):
        """
        :param url Ссылка на облачную функцию
        """
        self.url = url

    def send_message(self, message: str, recipient_id: str):
        """
        Отправка сообщения

        :param recipient_id Идентификатор получателя
        :param message Тело сообщения
        """
        json = {
            'chat_id': recipient_id,
            'message': message
        }
        requests.post(self.url, json=json)
