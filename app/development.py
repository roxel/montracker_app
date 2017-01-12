import logging

from app import create_app
from app.scheduler import scheduler
from app.processor.models import Model


app = create_app('config.DevelopmentConfig', config_pyfile='development.py')
logging.basicConfig(level=logging.INFO)


def check_server():
    with app.app_context():
        Model.update_state_from_server()

job = scheduler.add_job(check_server, 'interval', seconds=app.config['SCH_INTERVAL_SEC'])

if app.config['ACTIVATE_SCHEDULER']:
    scheduler.start()

app.run(host=app.config['SERVER_ADDR'], port=app.config['SERVER_PORT'], threaded=True)
