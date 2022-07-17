import os

basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:

    PROJECT_NAME = 'Axas House'
    PROJECT_VERSION = '0.0.1'

    JSON_SORT_KEYS = False
    SECRET_KEY = 'TakovNashParol-NaEzhaSelGoloyZhopoyKorol!!1'

    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USERNAME = 'v.rudomakha@gmail.com'
    MAIL_PASSWORD = 'yvzvbkmcdlcrlkpn'
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True

    BASIC_AUTH_USERNAME = 'axas'
    BASIC_AUTH_PASSWORD = 'exJGAeKb2M5V4Z7q'


class DevConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    PAGE_SIZE = 30


class ProductConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PAGE_SIZE = 30
