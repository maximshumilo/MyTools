import requests


class EventMessenger:

    """
    Класс для отправки событий в чат ТГ
    """

    def __init__(self, url: str, secret: str = None, host: str = None, chat_id: str = None):
        """
        :param url Ссылка на облачную функцию
        :param secret Секретный ключ
        :param host Хост
        :param chat_id Идентификатор чата
        """
        self.url = url
        self.secret = secret
        self.host = host
        self.chat_id = chat_id
        super().__init__()

    def send_message(self, message: str):
        """
        Отправка сообщения

        :param message Тело сообщения
        """
        json = {
            'secret': self.secret,
            'chat_id': self.chat_id,
            'message': message
        }
        if self.host:
            json['host'] = self.host
        requests.post(self.url, json=json)
