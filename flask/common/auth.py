from functools import wraps
from flask import _request_ctx_stack, has_request_context, session


def authenticate(user_model, user=None, email: str = None, password: str = None, token: str = None):
    """
    Аутентифицирует пользователя по паре email-password

    :param user_model: Модель пользователя
    :param user: Пользователь
    :param email: Email пользователя
    :param password: Пароль пользователя в открытом виде
    :param token: Токен пользователя
    :return: Аутентифицированный пользователь в случае совпадения пароля, иначе None
    """
    try:
        if not user:
            user = user_model.get_by_email(email, status='active')
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


def login(user, remember: bool = False) -> bool:
    """
    Аутентифицирует пользователя в текущей сессии

    :param user: Пользователь, для которого открывается сессия
    :param remember: Флаг запоминания пользователя после окончания сессии
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

    :return: Результат завершения сессии
    """
    session.pop('user_id', None)

    _request_ctx_stack.top.user = None
    return True


def current_user(user_model):
    if has_request_context() and not hasattr(_request_ctx_stack.top, 'user'):
        user_id = session.get('user_id')

        if user_id:
            user = user_model.where(state='active', id=user_id).first()
            _request_ctx_stack.top.user = user

    return getattr(_request_ctx_stack.top, 'user', None)


def login_required(model):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user(model):
                return {'errors': {"auth": 'Not authenticated'}}, 401
            return func(*args, **kwargs)
        return wrapper
    return decorator
