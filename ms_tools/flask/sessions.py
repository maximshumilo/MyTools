from functools import wraps

from flask import _request_ctx_stack, has_request_context, session


class UserSession:
    User = None

    def __init__(self, user_model, type_db):
        """
        :param user_model Модель пользователя, для аунтификации
        :param type_db Тип базы данных (sql/nosql)
        """
        self.User = user_model
        self.type_db = type_db

    @staticmethod
    def authenticate(user_instance=None, email: str = None, password: str = None, token: str = None):
        """
        Аутентифицирует пользователя по паре email-password

        :param user_instance: Пользователь
        :param email: Email пользователя
        :param password: Пароль пользователя в открытом виде
        :param token: Токен пользователя
        :return: Аутентифицированный пользователь в случае совпадения пароля, иначе None
        """
        try:
            if not user_instance:
                user_instance = user_instance.get_by_email(email, status='active')
            if not user_instance:
                return None

            if password:
                assert user_instance.check_password(password)
                return user_instance

            if token:
                assert user_instance.check_token(token)
                return user_instance
        except AssertionError:
            pass
        return None

    @staticmethod
    def login(user_instance, remember: bool = False) -> bool:
        """
        Аутентифицирует пользователя в текущей сессии

        :param user_instance: Пользователь, для которого открывается сессия
        :param remember: Флаг запоминания пользователя после окончания сессии
        :return: Результат открытия аутентифицированной сессии
        """
        if not user_instance.active:
            return False

        user_id = user_instance.id
        session['user_id'] = str(user_id)
        if hasattr(_request_ctx_stack.top, 'user'):
            delattr(_request_ctx_stack.top, 'user')

        if remember:
            session['remember'] = remember
        return True

    @staticmethod
    def logout():
        """
        Заканчивает активную пользовательскую сессию

        :return: Результат завершения сессии
        """
        session.pop('user_id', None)
        _request_ctx_stack.top.user = None
        return True

    def current_user(self):
        if has_request_context() and not hasattr(_request_ctx_stack.top, 'user'):
            user_id = session.get('user_id')
            if user_id:
                user = None
                if self.type_db == 'nosql':
                    user = self.User.objects.filter(state='active', id=user_id).first()
                elif self.type_db == 'sql':
                    user = self.User.where(state='active', id=user_id).first()
                _request_ctx_stack.top.user = user

        return getattr(_request_ctx_stack.top, 'user', None)

    def login_required(self):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.current_user():
                    return {'errors': {"auth": 'Not authenticated'}}, 401
                return func(*args, **kwargs)
            return wrapper
        return decorator
