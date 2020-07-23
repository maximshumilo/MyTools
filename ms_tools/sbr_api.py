import requests


__all__ = ["SberbankAPI"]


class SberbankAPI:
    """
    Класс для работы с api платежного шлюза Сбербанка

    Включает в себя методы:
        1. register_order - Регистрация зазказа
        2. get_status_order - Получение статуса об оплате
    """

    def __init__(self, username, password, api_url, redirect_success, redirect_fail):
        """
        Инициализация класса

        :param username: Имя пользователя для интеграции по API
        :param password: Пароль пользователя для интеграции по API
        :param api_url: URL адрес, REST интерфейса API Сбербанка
        :param redirect_success: URL адрес, для перенаправления после успешной оплаты
        :param redirect_fail: URL адрес, для перенаправления после неудачной оплаты
        """
        self.username = username
        self.password = password
        self.main_url = api_url
        self.redirect_success = redirect_success
        self.redirect_fail = redirect_fail

    async def __send_request__(self, method: str, data: dict) -> dict:
        """
        Отправка запроса в платежный шлюз Сбербанка

        :param method: Метод
        :param data: Параметры запроса
        :return: Ответ от платежного шлюза Сбербанка в формате json
        """
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        params = {
            "userName": self.username,
            "password": self.password,
        }
        params.update(data)
        r = requests.post(url=f'{self.main_url}{method}', headers=headers, params=params)
        return r.json()

    async def register_order(
            self,
            order_number: str,
            amount: int,
            return_url: str = None,
            fail_url: str = None
    ) -> dict:
        """
        Метод регистрации заказа в платежном шлюзе Сбербанка

        :param order_number: Уникальный идентификатор заказа в пределах магазина
        :param amount: Общая сумма заказа в минимальных единицах валюты
        :param return_url: URL адрес, на который требуется перенаправить пользователя в случае успешной оплаты.
        :param fail_url: URL адрес, на который требуется перенаправить пользователя в случае неуспешной оплаты.
        :return: Рузультат выполнения функции __send_request__
        """
        return_url = return_url if return_url else self.redirect_success
        fail_url = fail_url if fail_url else self.redirect_fail

        params = {"orderNumber": order_number, "amount": amount, "returnUrl": return_url, "failURL": fail_url}
        return await self.__send_request__("register.do", params)

    async def get_status_order(self, order_id: str, shop_order_id: str) -> dict:
        """
        Получение информации о заказе

        :param order_id: Идентификатор заказа в платежном шлюзе сбербанка
        :param shop_order_id: Идентификатор заказа в магазине
        :return: Рузультат выполнения функции __send_request__
        """
        params = {"orderId": order_id, "orderNumber": shop_order_id}
        return await self.__send_request__("getOrderStatusExtended.do", params)
