#!/usr/bin/env python3
import os
from flask import Flask, json
from flask.helpers import send_from_directory
from .processor import processor
from .auth import auth
import logging


BLUEPRINTS = (
    auth,
    processor,
)


def register_blueprints(app):
    for b in BLUEPRINTS:
        app.register_blueprint(b)


def configure_general(app):
    if app.config['USE_STATIC_FOLDER']:
        @app.route('/', defaults={'file': 'index.html'})
        @app.route('/<string:file>')
        @app.route('/assets/<path:file>', defaults={'assets': True})
        def show_index(file, assets=False):
            file = 'assets/%s' % file if assets else file
            return send_from_directory(app.config['STATIC_FOLDER'], file)

    else:
        @app.route("/")
        def show_index():
            return json.dumps({}), 200, {'ContentType': 'application/json'}


def configure_db(app):
    from .database import db, init_db
    init_db(db, app)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()


def ensure_configs(app):
    required_configs = ['SQLALCHEMY_DATABASE_URI',
                        'MONTRACKER_SERVER_ADDR',
                        'MONTRACKER_SERVER_API_VERSION',
                        'ARCGIS_PATH_PREFIX',
                        'ARCGIS_PATH_SUFFIX']
    for value in required_configs:
        if value not in app.config:
            logging.warning('{} not set. Set its value in /instance directory or config.py'.format(value))


def create_app(config_object, config_pyfile, instance_relative_config=True):
    app = Flask(__name__,
                instance_relative_config=instance_relative_config)
    app.config.from_object(config_object)
    app.config.from_pyfile(config_pyfile)
    register_blueprints(app)
    configure_db(app)
    configure_general(app)
    ensure_configs(app)

    return app

