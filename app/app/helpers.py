from app.database import db
from flask_restful import abort


def resource_does_not_exist():
    abort(404, message='Resource does not exist.', internal_code='error_does_not_exist')


def server_not_available():
    abort(503, message='Server not available', internal_code='error_server_not_available')


def analysis_data_incomplete():
    abort(400, message='Analysis data is incomplete for computation', internal_code='error_analysis_data_incomplete')


def request_resource_unavailable():
    abort(405, message='Request to resource unavailable.', internal_code='error_request_unavailable')


def validation_failed(invalid_fields=None):
    abort(422, message='Validation failed.', internal_code='error_validation_failed', invalid_fields=invalid_fields)


class AnalysisDataIncomplete(Exception):
    pass

