from flask import _request_ctx_stack, has_request_context, session
from werkzeug.local import LocalProxy

from data_layer.models import User


def user_loader(user_id):
    try:
        return User.where(state='active', id=user_id).first()
    except:
        return None


def authenticate(email=None, user=None, password=None, token=None):
    """
    Аутентифицирует пользователя по паре username-password

    :rtype : User or None
    :param username: Имя пользователя
    :type username: str
    :param password: Пароль пользователя в открытом виде
    :type password: str
    :return: Аутентифицированный пользователь в случае совпадения пароля, иначе None
    """
    try:
        if not user:
            user = User.get_by_email(email, status='active')
        if not user:
            return None

        if password:
            assert user.check_password(password)
            return user

        if token:
            assert user.check_token(token)
            return user
    except AssertionError:
        pass
    return None


def login(user, remember=False):
    """
    Аутентифицирует пользователя в текущей сессии

    :rtype : bool
    :param user: Пользователь, для которого открывается сессия
    :type user: User
    :param remember: Флаг запоминания пользователя после окончания сессии
    :type remember: bool
    :param force: Флаг принудительного открытия сессии
    :type force: bool
    :return: Результат открытия аутентифицированной сессии
    """
    if not user.active:
        return False

    user_id = user.id
    session['user_id'] = str(user_id)
    if hasattr(_request_ctx_stack.top, 'user'):
        delattr(_request_ctx_stack.top, 'user')

    if remember:
        session['remember'] = remember
    return True


def logout():
    """
    Заканчивает активную пользовательскую сессию

    :rtype : bool
    :return: Результат завершения сессии
    """
    session.pop('user_id', None)

    _request_ctx_stack.top.user = None
    return True


def get_user():
    if has_request_context() and not hasattr(_request_ctx_stack.top, 'user'):
        user_id = session.get('user_id')

        if user_id:
            user = user_loader(user_id)
            _request_ctx_stack.top.user = user

    return getattr(_request_ctx_stack.top, 'user', None)


current_user = LocalProxy(get_user)
