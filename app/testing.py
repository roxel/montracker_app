from app import create_app

app = create_app('config.TestConfig', config_pyfile='test.py')
