import os
import requests
from dotenv import load_dotenv

load_dotenv()


class EventMessenger():

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


def get_default_event_messenger():
    url = os.getenv('EVENT_MESSENGER_URL')
    secret = os.getenv('EVENT_MESSENGER_SECRET')
    chat_id = os.getenv('EVENT_MESSENGER_CHAT_ID')
    host = os.getenv('HOST')

    if not url or not secret:
        return None

    return EventMessenger(url=url, secret=secret, host=host, chat_id=chat_id)


if __name__ == '__main__':
    import argparse
    import logging
    import sys

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('integers', metavar='N', type=int, nargs='+',
                        help='an integer for the accumulator')
    parser.add_argument('--sum', dest='accumulate', action='store_const', const=sum, default=max,
                        help='sum the integers (default: find the max)')

    args = parser.parse_args()
    print(args.accumulate(args.integers))

    # logging config
    logging.basicConfig(
        format='[%(asctime)s %(levelname)s] %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO)
    logger = logging.getLogger()

    messenger = get_default_event_messenger()
    if not messenger:
        logger.info('There is no event messenger variable defined in environment file.')
        sys.exit(0)
    messenger.send_message('Hello world!')
