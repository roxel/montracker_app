Example contents of files in instance directory.

`intance/development.py`
========================

```
SQLALCHEMY_DATABASE_URI = 'postgresql://montracker_app:montracker@localhost/montracker_app'
MONTRACKER_SERVER_ADDR = 'http://127.0.0.1:8700/server'
ARCGIS_PATH_PREFIX = 'http://localhost:8700/models'
ARCGIS_PATH_SUFFIX = '/server'
USE_STATIC_FOLDER = True
STATIC_FOLDER = '/Users/piotr/Documents/montracker/2016-pp-montracker/ui/dist/'
ACTIVATE_SCHEDULER = False
SERVER_ADDR = '127.0.0.1'
SERVER_PORT = 8084
```

`intance/production.py`
=======================

```
SQLALCHEMY_DATABASE_URI = 'postgresql://montracker_app:montracker@localhost/montracker_app'
MONTRACKER_SERVER_ADDR = 'http://localhost:8700/server'
MONTRACKER_SERVER_TIMEOUT = 0.5
SERVER_ADDR = '127.0.0.1'
SERVER_PORT = 8084
SECRET_KEY = "montracker_really_secret_key"
USE_STATIC_FOLDER = True
STATIC_FOLDER = '/Users/piotr/Documents/montracker/2016-pp-montracker/ui/dist/'
```

`intance/test.py`
=================

```
SQLALCHEMY_DATABASE_URI = 'postgresql://montracker_app:montracker@localhost/montracker_app_test'
```