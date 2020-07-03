import requests


class EventMessenger:

    def __init__(self, url, secret=None, host=None, chat_id=None):
        self.url = url
        self.secret = secret
        self.host = host
        self.chat_id = chat_id
        super().__init__()

    def send_message(self, message):
        json = {
            'secret': self.secret,
            'chat_id': self.chat_id,
            'message': message
        }
        if self.host:
            json['host'] = self.host
        requests.post(self.url, json=json)
