from app.auth.models import User
from app.processor.models import ModelStatus, PersonType, ModelType, ActionStatus
from app.database import db
from flask import url_for
from flask_script import Manager, Command
from flask_migrate import Migrate, MigrateCommand
from app import create_app
from app.database import db

app = create_app('config.DevelopmentConfig', config_pyfile='development.py')
migrate = Migrate(app, db)
manager = Manager(app)


class Routes(Command):
    """
     Adds Flask-Script command listing all available routes from the app.
     Does not show routes requiring any parameters (e.g. needing object IDs).
     """

    help = description = 'Lists all route rules added to the app'

    @staticmethod
    def _has_no_empty_params(rule):
        defaults = rule.defaults if rule.defaults is not None else ()
        arguments = rule.arguments if rule.arguments is not None else ()
        return len(defaults) >= len(arguments)

    def run(self):
        links = []
        for rule in app.url_map.iter_rules():
            # Filter out rules we can't navigate to in a browser
            # and rules that require parameters
            if "GET" in rule.methods and Routes._has_no_empty_params(rule):
                url = url_for(rule.endpoint, **(rule.defaults or {}))
                links.append((url, rule.endpoint))
                # links is now a list of url, endpoint tuples
        for l in links:
            print(l)


class SetupDatabase(Command):
    """
    Only for using in development environment
    """

    def run(self):
        from app.database import db, setup_db
        with app.app_context():
            setup_db(db.session)

manager.add_command('db', MigrateCommand)
manager.add_command('routes', Routes)
manager.add_command('setupdb', SetupDatabase)


if __name__ == '__main__':
    manager.run()
