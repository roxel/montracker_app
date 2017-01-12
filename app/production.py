from app import create_app
from app.scheduler import scheduler
from app.processor.models import Model
from waitress import serve
import logging


application = create_app('config.ProductionConfig', config_pyfile='production.py')


def check_server():
    with application.app_context():
        Model.update_state_from_server()

job = scheduler.add_job(check_server, 'interval', seconds=application.config['SCH_INTERVAL_SEC'])

if application.config['ACTIVATE_SCHEDULER']:
    scheduler.start()

logger = logging.basicConfig(level=logging.INFO)
serve(application, host=application.config['SERVER_ADDR'], port=application.config['SERVER_PORT'])


