# coding: utf-8
import json
from urllib import request, error
from socket import timeout
from flask import current_app


WAITING = 'waiting'
COMPUTING = 'computing'
LOADING = 'loading'
CONVERTING = 'converting'
FINISHED = 'finished'
ERROR = 'error'

STATUSES = {
    1: WAITING,
    2: COMPUTING,
    3: LOADING,
    4: CONVERTING,
    5: FINISHED,
    6: ERROR,
}


class ServerException(Exception):
    pass


def _execute(req):
    try:
        return request.urlopen(req, timeout=current_app.config['MONTRACKER_SERVER_TIMEOUT']).read().decode('utf8')
    except (error.HTTPError, error.URLError, timeout) as e:
        raise ServerException("Server not available: {}".format(e))


def _get_or_delete(id, method='GET'):
    address = "{address}/{api_version}/analysis/{id}".format(
        address=current_app.config['MONTRACKER_SERVER_ADDR'],
        id=id,
        api_version=current_app.config['MONTRACKER_SERVER_API_VERSION'])
    req = request.Request(address)
    req.method = method
    return _execute(req)


def post(data, url_suffix):
    json_data = json.dumps(data).encode('utf8')
    address = "{address}/{api_version}/{analysis_type}".format(
        address=current_app.config['MONTRACKER_SERVER_ADDR'],
        analysis_type=url_suffix,
        api_version=current_app.config['MONTRACKER_SERVER_API_VERSION'])
    req = request.Request(address, data=json_data, headers={'content-type': 'application/json'})
    return json.loads(_execute(req))


def delete(id):
    return _get_or_delete(id, 'DELETE')


def get_layers(id=''):
    return json.loads(_get_or_delete(id))


def compute_simple(ipp_longitude, ipp_latitude, rp_longitude, rp_latitude, profiles, models):
    """
    Sends to Calculation Server request for simple models calculation

    :type ipp_longitude:
    :type ipp_latitude:
    :type rp_longitude:
    :type rp_latitude:
    :type profiles: dict
    :type models: list
    :param profiles: dict of person_type names and their integer weights
    :param models: list of model_type names
    """
    data = {
        'profiles': profiles,
        'ipp': {
            'longitude': ipp_longitude,
            'latitude': ipp_latitude
        },
        'rp': {
            'longitude': rp_longitude,
            'latitude': rp_latitude
        },
        'models': models
    }

    return post(data, 'analysis')


def compute_complex(model_weights, complex_models):
    """
    Sends to Calculation Server request for complex models calculation.
    All simple models must be requested earlier.

    :type model_weights: dict
    :type complex_models: list
    :param model_weights: dict of model_type name keys and dict with result_id of simple model and their int weight
    :param complex_models: list of model_type names of complex models requested
    """

    data = {
        'model_weights': model_weights,
        'complex_analyses': complex_models
    }

    return post(data, 'complex_analysis')
