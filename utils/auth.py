"""
Модуль для работы с аутентификацией и авторизацией
"""

import random
from datetime import datetime
from functools import wraps
import re
from typing import Optional

from flask import request, g

from app.models import Token
from utils.helpers import make_response


def gen_token(length: int = 64, fixed_prefix: str = '00') -> str:
    """
    :param length: длина токена
    :param fixed_prefix: фиксированный префикс
    :return: сгенерированный токен

    Генерирует случайный токен. Уникальность не гарантируется
    """
    rnd_len = length - len(fixed_prefix)
    return fixed_prefix + hex(random.getrandbits(rnd_len * 4))[2:].rjust(rnd_len, '0')


def auth():
    """

    :param is_admin: Должен ли обладать пользователь правами администратора
    :return: декоратор для view - функции

    Формирует декоратор для авторизации, основанной на токенах доступа
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = None
            token_pair = None
            if 'Authorization' not in request.headers:
                return make_response(
                    errors=[
                        {
                            'code': 1,
                            'message': 'Header "Authorization" not provided',
                            'source': 'headers',
                            'path': '$',
                            'additional': None
                        }
                    ],
                    status=401,
                    description='Вы пытаетесь войти в учетную запись которая была активированная '
                                'на другом устройстве! Это запрещено правилами использования приложения !'
                )
            if 'Authorization' in request.headers:
                regexp = r"^Token [\da-f]{64}$"
                if re.match(regexp, request.headers['Authorization']) is None:
                    return make_response(
                        errors=[
                            {
                                'code': 2,
                                'message': 'Invalid value of header "Authorization"',
                                'source': 'headers',
                                'path': '$',
                                'additional': {
                                    'regexp': regexp
                                }
                            }
                        ],
                        status=401,
                        description='Вы пытаетесь войти в учетную запись которая была активированная '
                                    'на другом устройстве! Это запрещено правилами использования приложения !'
                    )
                token_value = request.headers['Authorization'][6:]
                token: Optional[Token] = Token.query.filter(
                    Token.value == token_value,
                    Token.as_access != None
                ).first()

                if token is None:

                    return make_response(
                        errors=[
                            {
                                'code': 3,
                                'message': 'Incorrect value of header "Authorization"',
                                'source': 'headers',
                                'path': '$',
                                'additional': request.headers['Authorization']
                            }
                        ],
                        status=401,
                        description='Вы пытаетесь войти в учетную запись которая была активированная '
                                    'на другом устройстве! Это запрещено правилами использования приложения !'
                    )

                # if token.expires_at < datetime.utcnow():
                #     return make_response(
                #         errors=[
                #             {
                #                 'code': 4,
                #                 'message': 'Token Expired',
                #                 'source': 'headers',
                #                 'path': '$',
                #                 'additional': None
                #             }
                #         ],
                #         status=401,
                #         description='Время жизни авторизационного токена истекло'
                #     )

                token_pair = token.as_access
                user = token_pair.user

            g.user = user

            g.token_pair = token_pair

            return f(*args, **kwargs)

        return decorated_function

    return decorator



