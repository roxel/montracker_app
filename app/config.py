import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))+os.path.sep


class Config(object):
    SECRET_KEY = "montracker_secret_key"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MONTRACKER_SERVER_TIMEOUT = 3           # timeout for app-server communication in seconds
    MONTRACKER_SERVER_API_VERSION = 'v1'
    TESTING = False
    DEBUG = False
    SERVER_ADDR = '127.0.0.1'
    SERVER_PORT = 8084
    DEFAULT_WEIGHT = 1              # default weight for non complex models and profiles
    USE_STATIC_FOLDER = False
    ACTIVATE_SCHEDULER = True
    SCH_INTERVAL_SEC = 10


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    pass


class TestConfig(Config):
    DEBUG = False
    TESTING = True

