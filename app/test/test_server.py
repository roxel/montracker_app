import json
import unittest

import requests
from app.processor import cs_utils
from app.processor.models import ModelStatus, Model, ModelType
from flask import current_app
from test.fixtures import add_simple_action, add_analysis_with_coordinates, add_complete_analysis, \
    add_simple_models_analysis, add_complex_models_analysis, add_simple_model
from testing import app
from app.database import db, setup_db
import httpretty

SERVER_PATH = 'app/api/v1'


class ModelsTest(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        with app.app_context():
            db.session.close()
            db.drop_all()
            db.create_all()
            setup_db(db.session)
            app.config['MONTRACKER_SERVER_ADDR'] = 'http://127.0.0.1:10000'
            app.config['MONTRACKER_SERVER_API_VERSION'] = 'v1'
            app.config['ARCGIS_PATH_PREFIX'] = 'http://127.0.0.1:11000'
            app.config['ARCGIS_PATH_SUFFIX'] = '/maps'

    def tearDown(self):
        with app.app_context():
            db.session.close()


class AnalysisComputationTest(ModelsTest):

    def setUp(self):
        super(AnalysisComputationTest, self).setUp()

    @httpretty.activate
    def test_starting_analysis_with_simple_models(self):
        expected_content = {
            "HorDistIPP": "3897890975230495710",
            "ElevChgIPP": "4709831647259734695",
            "HorChgIPP": "4375692374598762347",
            "TrackOffset": "3476273469987234659",
            "DispAngle": "3892345235423495710",
            "FindLocation": "4709831647263434695",
            "Mobility": "4375692374598762346",
        }

        httpretty.register_uri(httpretty.POST, server_path('analysis'),
                               body=json.dumps(expected_content), content_type="application/json")

        with app.app_context():
            action = add_simple_action(db.session)
            analysis = add_simple_models_analysis(db.session, action.id)
            analysis.start_computation()
            for model in analysis.simple_models():
                self.assertEquals(model.result_id, expected_content[model.name])

    @httpretty.activate
    def test_starting_analysis_with_complex_models(self):
        result_ids = {
            "HorDistIPP": "3897890975230495710",
            "ElevChgIPP": "4709831647259734695",
            "HorChgIPP": "4375692374598762347",
            "TrackOffset": "3476273469987234659",
            "DispAngle": "3892345235423495710",
            "FindLocation": "4709831647263434695",
            "Mobility": "4375692374598762346",
        }
        expected_content = {
            "CombProb": "3897890975230495710",
            "SearchSeg": "3476273469987234659",
        }

        httpretty.register_uri(httpretty.POST, server_path('complex_analysis'),
                               body=json.dumps(expected_content), content_type="application/json")

        with app.app_context():
            action = add_simple_action(db.session)
            analysis = add_complex_models_analysis(db.session, action.id)
            for model in analysis.simple_models():
                model.update_result(result_ids[model.name])
            draft_simple_models = analysis.draft_models().join(Model.model_type).filter(ModelType.complex == False)
            assert draft_simple_models.count() == 0
            analysis.start_computation()
            for model in analysis.complex_models():
                self.assertEquals(model.result_id, expected_content[model.name])

    @httpretty.activate
    def test_updating_state(self):
        expected_content = {
            "status": "converting",
        }
        result_ids = {
            "HorDistIPP": "3897890975230495710",
            "ElevChgIPP": "4709831647259734695",
            "HorChgIPP": "4375692374598762347",
            "TrackOffset": "3476273469987234659",
            "DispAngle": "3892345235423495710",
            "FindLocation": "4709831647263434695",
            "Mobility": "4375692374598762346",
            "CombProb": "3897890975230495710",
            "SearchSeg": "3476273469987234659",
        }

        for id in result_ids.values():
            path = server_path('analysis/%s' % id)
            httpretty.register_uri(httpretty.GET, path,
                                   body=json.dumps(expected_content), content_type="application/json")

        with app.app_context():
            action = add_simple_action(db.session)
            analysis = add_complex_models_analysis(db.session, action.id)

            draft_id = ModelStatus.draft_id()
            for model in analysis.models:
                assert model.model_status.id == draft_id
            assert analysis.analysis_status_id == draft_id

            for model in analysis.models:
                model.update_result(result_ids[model.name])

            waiting_status_id = ModelStatus.by_name(ModelStatus.WAITING).id
            for model in analysis.models:
                assert model.status_id == waiting_status_id
            assert analysis.analysis_status_id == waiting_status_id

            analysis.update_result()

            processing_id = ModelStatus.by_name(ModelStatus.PROCESSING).id
            for model in analysis.models:
                assert model.status_id == processing_id
            assert analysis.analysis_status_id == processing_id

    @httpretty.activate
    def test_updating_layers(self):
        expected_content = {
            "status": "finished",
            "layer_ids": [
                "432542345",
                "785642345",
                "434567678",
                "969824586"
            ]
        }

        layers_count = 4
        result_id = "3897890975230495710"
        path = server_path('analysis/%s' % result_id)
        httpretty.register_uri(httpretty.GET, path,
                               body=json.dumps(expected_content), content_type="application/json")

        with app.app_context():
            action = add_simple_action(db.session)
            analysis = add_analysis_with_coordinates(db.session, action.id)
            model = add_simple_model(db.session, analysis.id)

            # mocking starting computation
            model.update_result(result_id)

            analysis.update_result()

            finished_id = ModelStatus.by_name(ModelStatus.FINISHED).id
            assert model.status_id == finished_id
            assert analysis.analysis_status_id == finished_id
            assert len(model.layer_urls()) == layers_count
            layer_paths = [layer_path(layers_id) for layers_id in expected_content['layer_ids']]
            for l in model.layer_urls():
                assert l in layer_paths


def server_path(endpoint):
    with app.app_context():
        return "{}/{}/{}".format(current_app.config['MONTRACKER_SERVER_ADDR'],
                                 current_app.config['MONTRACKER_SERVER_API_VERSION'],
                                 endpoint)


def layer_path(layers_id):
    with app.app_context():
        return "{}/{}{}".format(current_app.config['ARCGIS_PATH_PREFIX'],
                                layers_id,
                                current_app.config['ARCGIS_PATH_SUFFIX'])

if __name__ == '__main__':
    unittest.main()
