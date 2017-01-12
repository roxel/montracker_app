import unittest
import pytest
from app.processor.models import Analysis

from flask import json
from testing import app
from app.database import db, setup_db

SERVER_PATH = 'app/api/v1'


class ApiV1Test(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        with app.app_context():
            db.session.close()
            db.drop_all()
            db.create_all()
            setup_db(db.session)

    def tearDown(self):
        with app.app_context():
            db.session.close()

    def request(self, request_method, path, data=None):
        request_function = getattr(self, request_method, None)
        request = request_function(path, data=data)
        return request, json.loads(request.data.decode('utf-8'))

    def fixture(self, fixture_name):
        _fixtures = getattr(self, '_fixtures')
        value = _fixtures.get(fixture_name, None)
        if not isinstance(value, dict):
            raise AttributeError()
        return value.copy()

    def json_post(self, path='/', data=None, *args, **kwargs):
        return self.app.post(SERVER_PATH + path,
                             data=json.dumps(data),
                             content_type='application/json')

    def json_get(self, path='/',  *args, **kwargs):
        return self.app.get(SERVER_PATH + path)

    def json_patch(self, path='/', data=None, *args, **kwargs):
        return self.app.patch(SERVER_PATH + path,
                              data=json.dumps(data),
                              content_type='application/json')


class GeneralTest(ApiV1Test):

    def test_main_endpoint(self):
        result = self.app.get('/')
        self.assertEqual(result.status_code, 200)
        assert 'text/html' in result.headers.get('Content-Type')

    def test_users_endpoint(self):
        result = self.app.get('/auth/api/v1/users')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.headers.get('Content-Type'), 'application/json')

    def test_404_endpoint(self):
        result = self.app.get('/some/path_that/should_not_exist')
        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.headers.get('Content-Type'), 'application/json')

    def test_config_endpoint(self):
        result, data = self.request('json_get', '/config')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.headers.get('Content-Type'), 'application/json')


class ActionTest(ApiV1Test):

    _fixtures = {
        'simple_action': {
            'name': 'Example action name',
            'lost_time': 1414141414,
        },
        'coordinates_action': {
            'name': 'Example action name',
            'lost_time': 1414141414,
            'ipp_latitude': 90,
            'ipp_longitude': -100,
            'rp_latitude': -50.5,
            'rp_longitude': 49.95,
        },
    }

    def test_actions_endpoint_correct(self):
        result = self.app.get('/app/api/v1/actions')
        self.assertEqual(result.status_code, 200)

    def test_actions_post_data(self):
        action = self.fixture('simple_action')
        action_response, action_data_post = self.request('json_post', '/actions', action)
        self.assertEqual(action_response.status_code, 201)
        action_response, action_data_get = self.request('json_get', '/actions/' + str(action_data_post['id']))
        self.assertEquals(action_response.status_code, 200)
        self.assertDictEqual(action_data_post, action_data_get)

    def test_actions_post_response(self):
        action = self.fixture('simple_action')
        action_response, action_data = self.request('json_post', '/actions', action)
        self.assertEqual(action_response.status_code, 201)
        response_keys = ['id', 'name', 'archived', 'creation_time', 'action_status_id',
                         'lost_time', 'analyses', 'description',
                         'rp_latitude', 'rp_longitude', 'ipp_latitude', 'ipp_longitude']
        self.assertListEqual(sorted(response_keys), sorted(action_data.keys()))

    def test_actions_post_action_must_have_name(self):
        action = {'lost_time': 1414141414}
        action_response, action_data = self.request('json_post', '/actions', action)
        self.assertEqual(action_response.status_code, 422, msg="Must have a name")

    def test_actions_post_action_must_have_valid_name(self):
        action = {'name': '', 'lost_time': 1414141414}
        result, _ = self.request('json_post', '/actions', action)
        self.assertEqual(result.status_code, 422, msg="Mustn't allow empty name")

    def test_actions_post_action_must_not_have_negative_lost_time(self):
        action = {'name': 'Example action', 'lost_time': -1}
        result, _ = self.request('json_post', '/actions', action)
        self.assertEqual(result.status_code, 422, msg="Mustn't allow negative integers")

    def test_actions_post_action_must_not_have_empty_lost_time(self):
        action = {'name': 'Example action', 'lost_time': ''}
        result, _ = self.request('json_post', '/actions', action)
        self.assertEqual(result.status_code, 422, msg="Mustn't allow empty value")

    def test_actions_post_action_must_not_have_datetime_string_lost_time(self):
        action = {'name': 'Example action', 'lost_time': '2016-10-20 13:18:52.524962'}
        result, _ = self.request('json_post', '/actions', action)
        self.assertEqual(result.status_code, 422, msg="Mustn't allow datetime string")

    def test_actions_patch_action_can_be_archived(self):
        action = self.fixture('simple_action')
        action_response, action_data = self.request('json_post', '/actions', action)
        action_id = action_data['id']
        action_response, action_data = self.request('json_get', '/actions/' + str(action_id))
        self.assertEquals(action_response.status_code, 200)
        self.assertEquals(action_data['archived'], False)
        _, _ = self.request('json_patch', '/actions/' + str(action_id), data={'archived': True})
        action_response, action_data = self.request('json_get', '/actions/' + str(action_id))
        self.assertEquals(action_response.status_code, 200)
        self.assertEquals(action_data['archived'], True)

    def test_actions_patch_action_can_be_deleted(self):
        action = self.fixture('simple_action')
        action_response, action_data = self.request('json_post', '/actions', action)
        action_id = action_data['id']
        action_response, action_data = self.request('json_get', '/actions/' + str(action_id))
        self.assertEquals(action_response.status_code, 200)
        self.assertRaises(KeyError, lambda: action_data['deleted'])
        _, _ = self.request('json_patch', '/actions/' + str(action_id), data={'deleted': True})
        action_response, action_data = self.request('json_get', '/actions/' + str(action_id))
        self.assertEquals(action_response.status_code, 404)

    def test_actions_post_action_may_have_float_coordinates(self):
        action = self.fixture('coordinates_action')
        action_response, _ = self.request('json_post', '/actions', action)
        self.assertEquals(action_response.status_code, 201)

    def test_actions_post_action_must_not_have_string_coordinates(self):
        action = self.fixture('coordinates_action')
        action['ipp_latitude'] = 'word instead of integer/float'
        action_response, _ = self.request('json_post', '/actions', action)
        self.assertEquals(action_response.status_code, 422)

    def test_actions_post_action_must_not_have_out_of_range_coordinates(self):
        action = self.fixture('coordinates_action')
        action['ipp_latitude'] = -91
        action['ipp_longitude'] = 180.1
        action_response, _ = self.request('json_post', '/actions', action)
        self.assertEquals(action_response.status_code, 422)


class AnalysisTest(ApiV1Test):

    _fixtures = {
        'simple_action': {
            'name': 'Example action',
            'lost_time': 1000000
        },
        'simple_analysis': {
            'name': 'Simple analysis'
        },
        'complete_analysis': {
            'name': 'Example',
            'lost_time': 124124124,
            'ipp_latitude': 90,
            'ipp_longitude': -100,
            'rp_latitude': -50.5,
            'rp_longitude': 49.95,
        },
    }

    def setUp(self):
        super(AnalysisTest, self).setUp()
        action = self.fixture('simple_action')
        action_response, action_data = self.request('json_post', '/actions', action)
        self.action_id = action_data['id']

    def test_analyses_endpoint_correct(self):
        result = self.app.get('/app/api/v1/analyses')
        self.assertEqual(result.status_code, 200)

    def test_analyses_post_data(self):
        action = self.fixture('simple_action')
        analysis = self.fixture('simple_analysis')
        _, action_data = self.request('json_post', '/actions', action)
        action_id = action_data['id']
        analysis['action_id'] = str(action_id)
        _, analysis_data = self.request('json_post', '/analyses', analysis)
        analysis_id = analysis_data['id']
        _, analysis_data = self.request('json_get', '/analyses/' + str(analysis_id))
        self.assertEquals(analysis_data['lost_time'], 1000000)

    def test_actions_post_action_with_analysis(self):
        action = self.fixture('simple_action')
        analysis = self.fixture('simple_analysis')
        analyses = [analysis]
        action['analyses'] = analyses
        action_response, action_data = self.request('json_post', '/actions', action)
        self.assertEquals(action_response.status_code, 201)
        self.assertEquals(len(action_data['analyses']), 1)
        self.assertEquals(action_data['analyses'][0]['name'], analysis['name'])

    def test_actions_post_complete_analysis(self):
        action = self.fixture('simple_action')
        analysis = self.fixture('complete_analysis')
        _, config = self.request('json_get', '/config')
        complex_model_id = None
        for mt in config['model_types']:
            if mt['complex']:
                complex_model_id = mt['id']
        self.assertIsNotNone(complex_model_id)
        models = [
            {'model_type_id': config['model_types'][1]['id'], 'weight': 5},
            {'model_type_id': config['model_types'][2]['id'], 'weight': 2},
            {'model_type_id': complex_model_id, 'weight': None},
        ]
        profiles = [
            {'person_type_id': config['person_types'][3]['id'], 'weight': 1},
            {'person_type_id': config['person_types'][4]['id'], 'weight': 5},
        ]
        analysis['models'] = models
        analysis['profiles'] = profiles
        analyses = [analysis]
        action['analyses'] = analyses
        action_response, action_data = self.request('json_post', '/actions', action)
        self.assertEquals(action_response.status_code, 201)
        self.assertEquals(len(action_data['analyses']), 1)
        self.assertEquals(action_data['analyses'][0]['name'], analysis['name'])
        self.assertEquals(len(action_data['analyses'][0]['models']), len(models))
        self.assertEquals(len(action_data['analyses'][0]['profiles']), len(profiles))

    def test_analyses_patch_analysis_data(self):
        analysis = self.fixture('complete_analysis')
        analysis['action_id'] = self.action_id
        analysis_response, analysis_data = self.request('json_post', '/analyses', analysis)
        self.assertEquals(analysis_response.status_code, 201)
        analysis_id = analysis_data['id']
        analysis_lost_time = 123123
        analysis_ipp_latitude = 45.13
        analysis = {'lost_time': analysis_lost_time, 'ipp_latitude': analysis_ipp_latitude}
        analysis_response, analysis_data = self.request('json_patch', '/analyses/%s' % analysis_id, analysis)
        self.assertEquals(analysis_response.status_code, 200)
        analysis_response, analysis_data = self.request('json_get', '/analyses/%s' % analysis_id)
        self.assertEquals(analysis_response.status_code, 200)
        self.assertEquals(analysis_data['lost_time'], analysis_lost_time)
        self.assertEquals(analysis_data['ipp_latitude'], analysis_ipp_latitude)


class AnalysisModelsProfilesTest(ApiV1Test):

    _fixtures = {
        'simple_action': {
            'name': 'Example action name',
            'lost_time': 1414141414,
        },
        'complete_analysis': {
            'name': 'Example',
            'lost_time': 124124124,
            'ipp_latitude': 90,
            'ipp_longitude': -100,
            'rp_latitude': -50.5,
            'rp_longitude': 49.95,
        },
    }

    def setUp(self):
        super(AnalysisModelsProfilesTest, self).setUp()
        action = self.fixture('simple_action')
        action_response, action_data = self.request('json_post', '/actions', action)
        self.action_id = action_data['id']

    def test_analyses_post_models(self):
        analysis = self.fixture('complete_analysis')
        _, config = self.request('json_get', '/config')
        models = [
            {'model_type_id': config['model_types'][0]['id'], 'weight': 9},
            {'model_type_id': config['model_types'][1]['id'], 'weight': 2},
        ]
        analysis['models'] = models
        analysis['action_id'] = self.action_id
        analysis_response, analysis_data = self.request('json_post', '/analyses', analysis)
        self.assertEquals(analysis_response.status_code, 201)
        self.assertEquals(len(analysis_data['models']), len(models))
        analysis_response, analysis_data = self.request('json_get', '/analyses/' + str(analysis_data['id']))
        self.assertEquals(analysis_response.status_code, 200)
        self.assertIsNotNone(analysis_data['models'][0]['model_type_id'])
        ps = analysis_data['models']
        cs = config['model_types']
        if ps[0]['model_type_id'] == cs[0]['id']:
            self.assertEquals(ps[0]['weight'], models[0]['weight'])
            self.assertEquals(ps[1]['weight'], models[1]['weight'])
        else:
            self.assertEquals(ps[1]['weight'], models[0]['weight'])
            self.assertEquals(ps[0]['weight'], models[1]['weight'])

    def test_analyses_post_models_invalid_model_types(self):
        analysis = self.fixture('complete_analysis')
        _, config = self.request('json_get', '/config')
        imaginary_model_type_id = 1231234
        for mt in config['model_types']:
            assert imaginary_model_type_id != mt['id']
        models = [
            {'model_type_id': imaginary_model_type_id, 'weight': 5},
        ]
        analysis['models'] = models
        analysis['action_id'] = self.action_id
        analysis_response, analysis_data = self.request('json_post', '/analyses', analysis)
        self.assertEquals(analysis_response.status_code, 422)
        self.assertDictEqual(analysis_data['invalid_fields']['models']['0'],
                             {'model_type_id': ['Model type id not present in model types options.']})

    def test_analyses_post_profiles(self):
        analysis = self.fixture('complete_analysis')
        _, config = self.request('json_get', '/config')
        profiles = [
            {'person_type_id': config['person_types'][0]['id'], 'weight': 3},
            {'person_type_id': config['person_types'][1]['id'], 'weight': 20},
        ]
        analysis['profiles'] = profiles
        analysis['action_id'] = self.action_id
        analysis_response, analysis_data = self.request('json_post', '/analyses', analysis)
        self.assertEquals(analysis_response.status_code, 201)
        self.assertEquals(len(analysis_data['profiles']), len(profiles))
        analysis_response, analysis_data = self.request('json_get', '/analyses/%s' % str(analysis_data['id']))
        self.assertEquals(analysis_response.status_code, 200)
        self.assertIsNotNone(analysis_data['profiles'][0]['person_type_id'])
        ps = analysis_data['profiles']
        cs = config['person_types']
        if ps[0]['person_type_id'] == cs[0]['id']:
            self.assertEquals(ps[0]['weight'], profiles[0]['weight'])
            self.assertEquals(ps[1]['weight'], profiles[1]['weight'])
        else:
            self.assertEquals(ps[1]['weight'], profiles[0]['weight'])
            self.assertEquals(ps[0]['weight'], profiles[1]['weight'])

    def test_analyses_post_profiles_invalid_person_types(self):
        analysis = self.fixture('complete_analysis')
        _, config = self.request('json_get', '/config')
        imaginary_person_type_id = 1231234
        for mt in config['person_types']:
            assert imaginary_person_type_id != mt['id']
        profiles = [
            {'person_type_id': imaginary_person_type_id, 'weight': 5},
        ]
        analysis['profiles'] = profiles
        analysis['action_id'] = self.action_id
        analysis_response, analysis_data = self.request('json_post', '/analyses', analysis)
        self.assertEquals(analysis_response.status_code, 422)
        self.assertDictEqual(analysis_data['invalid_fields']['profiles']['0'],
                             {'person_type_id': ['Person type id not present in person types options.']})

    def test_analyses_patch_profiles(self):

        # create analysis
        analysis = self.fixture('complete_analysis')
        _, config = self.request('json_get', '/config')
        analysis['action_id'] = self.action_id
        analysis_response, analysis_data = self.request('json_post', '/analyses', analysis)
        analysis_id = analysis_data['id']

        # confirm no models or profiles
        self.assertEquals(analysis_response.status_code, 201)
        self.assertEquals(len(analysis_data['models']), 0)
        self.assertEquals(len(analysis_data['profiles']), 0)

        # add one profile
        profile_1_weight = 7
        profiles = [
            {'person_type_id': config['person_types'][1]['id'], 'weight': profile_1_weight},
        ]

        analysis = {'profiles': profiles}
        analysis_response, analysis_data = self.request('json_patch', '/analyses/%s' % analysis_id, analysis)

        # confirm one profile
        self.assertEquals(analysis_response.status_code, 200)
        self.assertEquals(len(analysis_data['models']), 0)
        self.assertEquals(len(analysis_data['profiles']), 1)
        self.assertEquals(analysis_data['profiles'][0]['weight'], profile_1_weight)

        # add second profile
        profile_2_weight = 4
        profiles = analysis_data['profiles']
        profiles.append({'person_type_id': config['person_types'][2]['id'], 'weight': profile_2_weight})

        analysis = {'profiles': profiles}
        analysis_response, analysis_data = self.request('json_patch', '/analyses/%s' % analysis_id, analysis)

        # confirm two profiles
        self.assertEquals(analysis_response.status_code, 200)
        self.assertEquals(len(analysis_data['models']), 0)
        self.assertEquals(len(analysis_data['profiles']), 2)
        self.assertEquals(analysis_data['profiles'][0]['weight'], profile_1_weight)
        self.assertEquals(analysis_data['profiles'][1]['weight'], profile_2_weight)

        # edit existing profile
        profile_3_weight = 5
        profiles = sorted(analysis_data['profiles'], key=lambda item: item['person_type_id'])
        profiles[0]['weight'] = profile_3_weight

        analysis = {'profiles': profiles}
        analysis_response, analysis_data = self.request('json_patch', '/analyses/%s' % analysis_id, analysis)

        # confirm two profiles
        self.assertEquals(analysis_response.status_code, 200)
        self.assertEquals(len(analysis_data['models']), 0)
        self.assertEquals(len(analysis_data['profiles']), 2)
        profiles = sorted(analysis_data['profiles'], key=lambda item: item['person_type_id'])
        self.assertEquals(profiles[0]['weight'], profile_3_weight)
        self.assertEquals(profiles[1]['weight'], profile_2_weight)

        # delete one profile and edit other
        profile_4_weight = 8
        profiles = sorted(analysis_data['profiles'], key=lambda item: item['person_type_id'])[:1]   # keep only first
        profiles[0]['weight'] = profile_4_weight              # change weight of first

        analysis = {'profiles': profiles}
        analysis_response, analysis_data = self.request('json_patch', '/analyses/%s' % analysis_id, analysis)

        # confirm one profile
        self.assertEquals(analysis_response.status_code, 200)
        self.assertEquals(len(analysis_data['models']), 0)
        self.assertEquals(len(analysis_data['profiles']), 1)
        self.assertEquals(analysis_data['profiles'][0]['weight'], profile_4_weight)

        # delete last profile
        analysis = {'profiles': []}
        analysis_response, analysis_data = self.request('json_patch', '/analyses/%s' % analysis_id, analysis)

        # confirm no profiles
        self.assertEquals(analysis_response.status_code, 200)
        self.assertEquals(len(analysis_data['models']), 0)
        self.assertEquals(len(analysis_data['profiles']), 0)

    def test_analyses_patch_models(self):

        # create analysis
        analysis = self.fixture('complete_analysis')
        _, config = self.request('json_get', '/config')
        analysis['action_id'] = self.action_id
        analysis_response, analysis_data = self.request('json_post', '/analyses', analysis)
        analysis_id = analysis_data['id']

        # confirm no models or profiles
        self.assertEquals(analysis_response.status_code, 201)
        self.assertEquals(len(analysis_data['models']), 0)
        self.assertEquals(len(analysis_data['profiles']), 0)

        # add one model
        model_1_weight = 7
        models = [
            {'model_type_id': config['model_types'][1]['id'], 'weight': model_1_weight},
        ]

        analysis = {'models': models}
        analysis_response, analysis_data = self.request('json_patch', '/analyses/%s' % analysis_id, analysis)

        # confirm one model
        self.assertEquals(analysis_response.status_code, 200)
        self.assertEquals(len(analysis_data['models']), 1)
        self.assertEquals(len(analysis_data['profiles']), 0)
        self.assertEquals(analysis_data['models'][0]['weight'], model_1_weight)

        # add second model
        model_2_weight = 4
        models = analysis_data['models']
        models.append({'model_type_id': config['model_types'][2]['id'], 'weight': model_2_weight})

        analysis = {'models': models}
        analysis_response, analysis_data = self.request('json_patch', '/analyses/%s' % analysis_id, analysis)

        # confirm two models
        self.assertEquals(analysis_response.status_code, 200)
        self.assertEquals(len(analysis_data['models']), 2)
        self.assertEquals(len(analysis_data['profiles']), 0)
        self.assertEquals(analysis_data['models'][0]['weight'], model_1_weight)
        self.assertEquals(analysis_data['models'][1]['weight'], model_2_weight)

        # edit existing model
        model_3_weight = 5
        models = sorted(analysis_data['models'], key=lambda item: item['model_type_id'])
        models[0]['weight'] = model_3_weight

        analysis = {'models': models}
        analysis_response, analysis_data = self.request('json_patch', '/analyses/%s' % analysis_id, analysis)

        # confirm two models
        self.assertEquals(analysis_response.status_code, 200)
        self.assertEquals(len(analysis_data['models']), 2)
        self.assertEquals(len(analysis_data['profiles']), 0)
        models = sorted(analysis_data['models'], key=lambda item: item['model_type_id'])
        self.assertEquals(models[0]['weight'], model_3_weight)
        self.assertEquals(models[1]['weight'], model_2_weight)

        # delete one model and edit other
        model_4_weight = 8
        models = sorted(analysis_data['models'], key=lambda item: item['model_type_id'])[:1]  # keep only first
        models[0]['weight'] = model_4_weight  # change weight of first

        analysis = {'models': models}
        analysis_response, analysis_data = self.request('json_patch', '/analyses/%s' % analysis_id, analysis)

        # confirm one model
        self.assertEquals(analysis_response.status_code, 200)
        self.assertEquals(len(analysis_data['models']), 1)
        self.assertEquals(len(analysis_data['profiles']), 0)
        self.assertEquals(analysis_data['models'][0]['weight'], model_4_weight)

        # delete last model
        analysis = {'models': []}
        analysis_response, analysis_data = self.request('json_patch', '/analyses/%s' % analysis_id, analysis)

        # confirm no models
        self.assertEquals(analysis_response.status_code, 200)
        self.assertEquals(len(analysis_data['models']), 0)
        self.assertEquals(len(analysis_data['profiles']), 0)

    def test_analyses_post_duplicate(self):

        # create analysis
        analysis = self.fixture('complete_analysis')
        _, config = self.request('json_get', '/config')

        complex_model_id = None
        for mt in config['model_types']:
            if mt['complex']:
                complex_model_id = mt['id']
        self.assertIsNotNone(complex_model_id)

        analysis['action_id'] = self.action_id
        model_1_weight, model_2_weight = 7, 5
        models = [
            {'model_type_id': config['model_types'][1]['id'], 'weight': model_1_weight},
            {'model_type_id': config['model_types'][2]['id'], 'weight': model_2_weight},
            {'model_type_id': complex_model_id, 'weight': None},
        ]
        person_1_weight, person_2_weight = 3, 6
        profiles = [
            {'person_type_id': config['person_types'][1]['id'], 'weight': person_1_weight},
            {'person_type_id': config['person_types'][2]['id'], 'weight': person_2_weight},
        ]
        analysis['models'] = models
        analysis['profiles'] = profiles
        analysis_response, analysis_data = self.request('json_post', '/analyses', analysis)
        self.assertEqual(analysis_response.status_code, 201)
        analysis_id = analysis_data['id']
        analysis_duplicated = {
            'name': 'Another example',
            'action_id': self.action_id,
            'analysis_id': analysis_id,
        }
        analysis_duplicated_response, analysis_duplicated_data = self.request('json_post',
                                                                              '/analyses',
                                                                              analysis_duplicated)
        self.assertEqual(analysis_duplicated_response.status_code, 201)
        analysis_duplicated_id = analysis_duplicated_data['id']

        analysis_response, analysis_data = self.request('json_get',
                                                        '/analyses/%s' % analysis_id)
        analysis_duplicated_response, analysis_duplicated_data = self.request('json_get',
                                                                              '/analyses/%s' % analysis_duplicated_id)

        self.assertNotEqual(analysis_data.pop('id'), analysis_duplicated_data.pop('id'))
        self.assertEqual(analysis_data.pop('name'), self.fixture('complete_analysis')['name'])
        self.assertEqual(analysis_duplicated_data.pop('name'), analysis_duplicated['name'])

        models = analysis_data.pop('models')
        duplicated_models = analysis_duplicated_data.pop('models')
        profiles = analysis_data.pop('profiles')
        duplicated_profiles = analysis_duplicated_data.pop('profiles')

        for _list in [models, duplicated_models]:
            for _dict in _list:
                del _dict['id']

        for _list in [profiles, duplicated_profiles]:
            for _dict in _list:
                del _dict['id']

        del analysis_data['creation_time']
        del analysis_duplicated_data['creation_time']

        for m, dm in zip(sorted(models, key=lambda k: k['model_type_id']),
                         sorted(duplicated_models, key=lambda k: k['model_type_id'])):
            self.assertDictEqual(m, dm)
        for p, dp in zip(sorted(profiles, key=lambda k: k['person_type_id']),
                         sorted(duplicated_profiles, key=lambda k: k['person_type_id'])):
            self.assertDictEqual(p, dp)

if __name__ == '__main__':
    unittest.main()
