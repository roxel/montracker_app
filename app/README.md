# Montracker
Projekt i implementacja systemu webowego do wspomagania poszukiwań osób zaginionych w górach.

## Montracker App

### Installation

To run application Python 3 is required. 
Recommended Python version is 3.5.2, also tested on version 3.4.3.

Application uses stantard Python package manager `pip`. All required packages are listed in `requirements.txt` file. Using Python virtualization tool `virtualenv` is recommended. 

Example commands to install necessary packages and extensions on Linux/Mac OS X:

    $ pip install virtualenv
    $ virtualenv venv
    $ source venv/bin/activate
    $ pip install -r requirements.txt

On Windows virtual environment of `virtualenv` can be activated using:
    
    $ .\venv\Scripts\activate.bat
 
### Configuration

Some presets for app configuration are located in `config.py`. Nonetheless, it is required to manually supply database url. All configuration can be done using `instance/` directory.

1. Create `instance/` directory in application root folder.
2. Create separate files for each configured environment: `instance/development.py`, `instance/production.py` and `instance/test.py`.
3. Write config key-value pairs: `CONFIG_KEY = value`

List of configuration keys:

* `SQLALCHEMY_DATABASE_URI` – mandatory; path to database as string, e.g.: `'postgresql://user:password@localhost/database_name'`
* `MONTRACKER_SERVER_ADDR` – server address, e.g.: `'http://127.0.0.1:8700/server'`
* `ARCGIS_PATH_PREFIX` – prefix of path returned by calculation server leading to individual ArcGIS layers, e.g.: `'http://localhost:8700/models'` 
* `ARCGIS_PATH_SUFFIX` – ArcGIS suffix, as above.
* `USE_STATIC_FOLDER` – if application server should register path to AngularJS static files; if set to `True` then `STATIC_FOLDER` is required
* `STATIC_FOLDER` – if `USE_STATIC_FOLDER` is set to True, then it specifies absolute path to AngularJS static files directory; only files available directly in `/<STATIC_FOLDER>` or anywhere under `/<STATIC_FOLDER>/assets` will be available. 
* `ACTIVATE_SCHEDULER` – if models state update from server should be run by the background scheduler

### Database
    
Application can be set up only in development mode. To do this set correct `SQLALCHEMY_DATABASE_URI` config and then create database, calling for example:

    $ psql --username=montracker_app
    $ postgres=# CREATE DATABASE montracker_app;
    
After database is created it can be setup using (in proper virtualenv):

    $ python manage.py db upgrade
    $ python manage.py setupdb

### Running

To run properly configured application:

1. First activate virtualenv: `source venv/bin/activate` or `.\venv\Scripts\activate.bat`
2. Then call `python development.py` or `python production.py`, depending on the used environment.