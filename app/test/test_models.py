import unittest
import time
import datetime
import random
from app.database import db, setup_db
from app.helpers import AnalysisDataIncomplete
from app.processor.models import Action, Analysis, Profile, Model, ModelType, PersonType, ModelStatus
from sqlalchemy.exc import IntegrityError
from test.fixtures import add_simple_action, add_analysis_with_coordinates, add_simple_model, add_complex_model_comb, \
    add_complex_model_seg, add_simple_models_analysis
from testing import app

SERVER_PATH = 'app/api/v1'


class ModelsTest(unittest.TestCase):

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


class ModelTypeTest(ModelsTest):

    def test_simple_model_types_available(self):
        with app.app_context():
            model_types_names = ['HorDistIPP', 'ElevChgIPP', 'HorChgIPP',
                                 'DispAngle', 'TrackOffset', 'FindLocation',
                                 'Mobility']
            for mt in model_types_names:
                model_type = ModelType.query.filter_by(name=mt).first()
                self.assertIsNotNone(model_type.id)
                self.assertFalse(model_type.complex)

    def test_complex_model_types_available(self):
        with app.app_context():
            model_types_names = ['CombProb', 'SearchSeg']
            for mt in model_types_names:
                model_type = ModelType.query.filter_by(name=mt).first()
                self.assertIsNotNone(model_type.id)
                self.assertTrue(model_type.complex)


class ModelStatusTest(ModelsTest):

    def test_basic_model_statuses_available(self):
        with app.app_context():
            model_statuses_names = ModelStatus.names()
            for ms in model_statuses_names:
                model_status = ModelStatus.query.filter_by(name=ms).first()
                self.assertIsNotNone(model_status.id)


class ModelTest(ModelsTest):

    def test_model_default_status(self):
        with app.app_context():
            action = add_simple_action(db.session)
            analysis = add_analysis_with_coordinates(db.session, action.id)
            model_type = ModelType.query.filter_by(complex=False).first()
            model = Model(analysis_id=analysis.id, model_type_id=model_type.id)
            db.session.add(model)
            db.session.flush()
            model_status = ModelStatus.query.filter_by(name='draft').one()
            self.assertEquals(model.status_id, model_status.id)

    def test_model_weight_for_non_complex_types(self):
        with app.app_context():
            action = add_simple_action(db.session)
            analysis = add_analysis_with_coordinates(db.session, action.id)
            model_type = ModelType.query.filter_by(complex=False).first()
            model = Model(analysis_id=analysis.id, model_type_id=model_type.id)
            db.session.add(model)
            db.session.flush()
            model.create_weights()
            db.session.flush()
            self.assertEquals(analysis.models.count(), 1)
            self.assertEquals(model.model_weights.count(), 1)
            self.assertEquals(model.weight, app.config['DEFAULT_WEIGHT'])
            new_weight = 5
            model.update_weights(new_weight)
            self.assertEquals(model.model_weights.count(), 1)
            self.assertEquals(model.weight, new_weight)

    def test_model_weight_must_be_associated_with_non_complex_types(self):
        with app.app_context():
            action = add_simple_action(db.session)
            analysis = add_analysis_with_coordinates(db.session, action.id)
            model_type = ModelType.query.filter_by(complex=False).first()
            model = Model(analysis_id=analysis.id, model_type_id=model_type.id)
            db.session.add(model)
            db.session.flush()
            self.assertEquals(analysis.models.count(), 1)
            self.assertEquals(model.model_weights.count(), 0)
            with self.assertRaises(AssertionError):
                getattr(model, 'weight')

    def test_model_weight_for_complex_types(self):
        with app.app_context():
            action = add_simple_action(db.session)
            analysis = add_analysis_with_coordinates(db.session, action.id)
            model_type = ModelType.query.filter_by(complex=True).first()
            model = Model(analysis_id=analysis.id, model_type_id=model_type.id)
            db.session.add(model)
            db.session.flush()
            self.assertEquals(analysis.models.count(), 1)
            self.assertIsNone(model.weight)
            with self.assertRaises(AssertionError):
                model.create_weights()

    def test_model_weight_for_child_model(self):
        with app.app_context():
            action = add_simple_action(db.session)
            analysis = add_analysis_with_coordinates(db.session, action.id)
            model_type = ModelType.query.filter_by(complex=False).first()
            complex_model_type = ModelType.query.filter_by(complex=True).first()
            model = Model(analysis_id=analysis.id, model_type_id=model_type.id)
            complex_model = Model(analysis_id=analysis.id, model_type_id=complex_model_type.id)
            db.session.add(model)
            db.session.add(complex_model)
            db.session.flush()
            model.create_weights(parent_model_id=complex_model.id)
            db.session.flush()
            self.assertEquals(analysis.models.count(), 2)
            self.assertEquals(model.model_weights.count(), 1)
            self.assertEquals(model.child_model_weights.count(), 0)
            self.assertEquals(complex_model.model_weights.count(), 0)
            self.assertEquals(complex_model.child_model_weights.count(), 1)

    def test_model_weight_for_multiple_complex_analyses(self):
        with app.app_context():
            action = add_simple_action(db.session)
            analysis = add_analysis_with_coordinates(db.session, action.id)
            model = add_simple_model(db.session, analysis.id)
            comb_model = add_complex_model_comb(db.session, analysis.id)
            seg_model = add_complex_model_seg(db.session, analysis.id)
            model.create_weights(parent_model_id=comb_model.id)
            model.create_weights(parent_model_id=seg_model.id)
            db.session.flush()
            self.assertEquals(analysis.models.count(), 3)
            self.assertEquals(model.model_weights.count(), 2)
            self.assertEquals(model.child_model_weights.count(), 0)
            self.assertEquals(comb_model.model_weights.count(), 0)
            self.assertEquals(seg_model.model_weights.count(), 0)
            self.assertEquals(comb_model.child_model_weights.count(), 1)
            self.assertEquals(seg_model.child_model_weights.count(), 1)

    def test_model_weight_for_complex_must_be_none(self):
        with app.app_context():
            action = add_simple_action(db.session)
            analysis = add_analysis_with_coordinates(db.session, action.id)
            comb_model = add_complex_model_comb(db.session, analysis.id)
            with self.assertRaises(AssertionError):
                comb_model.create_weights(weight=3)


class AnalysisTest(ModelsTest):

    def test_analysis_requires_action(self):
        with app.app_context():
            analysis = Analysis(name='Basic')
            with self.assertRaises(IntegrityError):
                db.session.add(analysis)
                db.session.flush()

    def test_adding_analysis(self):
        with app.app_context():
            action = Action(name='Example', lost_time=datetime.datetime.now())
            db.session.add(action)
            db.session.flush()
            analysis = Analysis(name='Basic', action_id=action.id)
            db.session.add(analysis)
            db.session.flush()
            self.assertIsNotNone(analysis.id)

    def test_analysis_inheriting_action_coordinates(self):
        with app.app_context():
            action = Action(name='Example', lost_time=datetime.datetime.now())
            db.session.add(action)
            db.session.flush()
            analysis = Analysis(name='Basic', action_id=action.id)
            db.session.add(analysis)
            db.session.flush()
            self.assertIsNone(analysis.ipp_latitude)
            self.assertIsNotNone(analysis.lost_time)
            self.assertEquals(analysis.lost_time, action.lost_time)
            example_ipp_latitude = 50
            action.ipp_latitude = example_ipp_latitude
            self.assertEquals(analysis.ipp_latitude, example_ipp_latitude)

    def test_adding_analysis_with_basic_model(self):
        with app.app_context():
            action = Action(name='Example', lost_time=datetime.datetime.now())
            db.session.add(action)
            db.session.flush()
            analysis = Analysis(name='Some basic analysis', action_id=action.id,
                                ipp_longitude=80, ipp_latitude=70, rp_latitude=30, rp_longitude=80)
            db.session.add(analysis)
            db.session.flush()
            model_type = ModelType.query.filter_by(complex=False).first()
            self.assertIsNotNone(model_type.id)
            model = Model(analysis_id=analysis.id, model_type_id=model_type.id)
            db.session.add(model)
            db.session.flush()
            self.assertIsNotNone(model.id)
            self.assertEquals(analysis.models.count(), 1)

    def test_analysis_with_profiles(self):
        with app.app_context():
            action = Action(name='Example', lost_time=datetime.datetime.now())
            db.session.add(action)
            db.session.flush()
            analysis = Analysis(name='Some basic analysis', action_id=action.id,
                                ipp_longitude=80, ipp_latitude=70, rp_latitude=30, rp_longitude=80)
            db.session.add(analysis)
            db.session.flush()
            person_type_tourist = PersonType.query.filter_by(name='tourist').first()
            person_type_climber = PersonType.query.filter_by(name='climber').first()
            self.assertIsNotNone(person_type_tourist.id)
            self.assertIsNotNone(person_type_climber.id)
            tourist = Profile(analysis_id=analysis.id, person_type_id=person_type_tourist.id, weight=random.randint(1, 10))
            climber = Profile(analysis_id=analysis.id, person_type_id=person_type_climber.id, weight=random.randint(1, 10))
            db.session.add(tourist)
            db.session.add(climber)
            db.session.flush()
            self.assertIsNotNone(tourist.id)
            self.assertIsNotNone(climber.id)
            self.assertEquals(analysis.profiles.count(), 2)

    def test_adding_complete_analysis(self):
        with app.app_context():
            # add action
            action = Action(name='Rysy', lost_time=datetime.datetime.now())
            db.session.add(action)
            db.session.flush()

            # add analysis
            analysis = Analysis(name='Some basic analysis', action_id=action.id,
                                ipp_longitude=80, ipp_latitude=70, rp_latitude=30, rp_longitude=80)
            db.session.add(analysis)

            # add comb model
            model_type = ModelType.query.filter_by(name='CombProb').first()
            comb_model = Model(analysis_id=analysis.id, model_type_id=model_type.id)
            db.session.add(comb_model)
            db.session.flush()

            # add search seg model
            model_type = ModelType.query.filter_by(name='SearchSeg').first()
            seg_model = Model(analysis_id=analysis.id, model_type_id=model_type.id)
            db.session.add(seg_model)
            db.session.flush()

            # add simple models
            model_type_names = ['HorDistIPP', 'ElevChgIPP', 'HorChgIPP', 'DispAngle',
                                'TrackOffset', 'FindLocation', 'Mobility']
            for mtn in model_type_names:
                model_type = ModelType.query.filter_by(name=mtn).first()
                model = Model(analysis_id=analysis.id, model_type_id=model_type.id)
                db.session.add(model)
                db.session.flush()
                model.create_weights(parent_model_id=comb_model.id)
                model.create_weights(parent_model_id=seg_model.id)

            # add chosen profiles
            person_type_tourist = PersonType.query.filter_by(name='tourist').first()
            person_type_climber = PersonType.query.filter_by(name='climber').first()

            weight_tourist, weight_climber = 3, 7

            tourist = Profile(analysis_id=analysis.id, person_type_id=person_type_tourist.id,
                              weight=weight_tourist)
            climber = Profile(analysis_id=analysis.id, person_type_id=person_type_climber.id,
                              weight=weight_climber)
            db.session.add(tourist)
            db.session.add(climber)
            db.session.flush()

            self.assertEquals(analysis.profiles.count(), 2)
            self.assertEquals(analysis.models.count(), 9)
            self.assertEquals(comb_model.child_model_weights.count(), 7)
            self.assertEquals(seg_model.child_model_weights.count(), 7)

    def test_duplicating_analysis_shallow(self):
        with app.app_context():
            action = add_simple_action(db.session)
            analysis = add_analysis_with_coordinates(db.session, action.id)
            duplicated = analysis.duplicate({'ipp_latitude': 10})
            self.assertNotEqual(analysis.id, duplicated.id)
            self.assertEqual(analysis.name, duplicated.name)
            self.assertEqual(analysis.lost_time, duplicated.lost_time)
            self.assertNotEqual(duplicated.ipp_latitude, analysis.ipp_latitude)
            self.assertEqual(duplicated.ipp_latitude, 10)

    def test_duplicating_analysis_deep(self):
        with app.app_context():
            action = add_simple_action(db.session)
            analysis = add_simple_models_analysis(db.session, action.id)
            duplicated = analysis.duplicate({'name': 'Another'})
            self.assertNotEqual(analysis.id, duplicated.id)
            self.assertEqual(analysis.lost_time, duplicated.lost_time)
            self.assertEqual(analysis.models.count(), duplicated.models.count())

    def test_analysis_status_id_no_models(self):
        with app.app_context():
            action = add_simple_action(db.session)
            analysis = add_analysis_with_coordinates(db.session, action.id)
            analyses_count = Analysis.query.count()
            # only one analysis, no models
            self.assertEquals(analyses_count, 1)
            draft_id = ModelStatus.draft_id()
            # and the one has status draft on class level
            draft_count = Analysis.query.filter(Analysis.analysis_status_id == draft_id).count()
            self.assertEquals(draft_count, 1)
            # as well as on instance level
            self.assertEquals(analysis.analysis_status_id, draft_id)

    def test_analysis_status_id_draft(self):
        with app.app_context():
            action = add_simple_action(db.session)
            analysis = add_simple_models_analysis(db.session, action.id)
            analyses_count = Analysis.query.count()
            draft_id = ModelStatus.draft_id()

            for model in analysis.models:
                model.status_id = draft_id
            # only one analysis, no models
            self.assertEquals(analyses_count, 1)
            # and the one has status draft on class level
            draft_count = Analysis.query.filter(Analysis.analysis_status_id == draft_id).count()
            self.assertEquals(draft_count, 1)
            # as well as on instance level
            self.assertEquals(analysis.analysis_status_id, draft_id)

    def test_analysis_status_id_finished(self):
        with app.app_context():
            action = add_simple_action(db.session)
            analysis = add_simple_models_analysis(db.session, action.id)
            finished_id = ModelStatus.by_name(ModelStatus.FINISHED).id
            for model in analysis.models:
                model.status_id = finished_id
            # only one analysis, all finished
            analyses_count = Analysis.query.count()
            self.assertEquals(analyses_count, 1)
            # and the one has status finished on class level
            analyses_status_count = Analysis.query.filter(Analysis.analysis_status_id == finished_id).count()
            self.assertEquals(analyses_status_count, 1)
            # as well as on instance level
            self.assertEquals(analysis.analysis_status_id, finished_id)

    def test_analysis_status_id_error(self):
        with app.app_context():
            action = add_simple_action(db.session)
            analysis = add_simple_models_analysis(db.session, action.id)
            waiting_id = ModelStatus.by_name(ModelStatus.WAITING).id
            error_id = ModelStatus.by_name(ModelStatus.ERROR).id
            for model in analysis.models:
                model.status_id = waiting_id
            analysis.models.first().status_id = error_id
            # only one analysis, all waiting but one error
            analyses_count = Analysis.query.count()
            self.assertEquals(analyses_count, 1)
            # and the one has status error on class level
            analyses_status_count = Analysis.query.filter(Analysis.analysis_status_id == error_id).count()
            self.assertEquals(analyses_status_count, 1)
            # as well as on instance level
            self.assertEquals(analysis.analysis_status_id, error_id)

    def test_analysis_status_id_waiting(self):
        with app.app_context():
            action = add_simple_action(db.session)
            analysis = add_simple_models_analysis(db.session, action.id)
            processing_id = ModelStatus.by_name(ModelStatus.PROCESSING).id
            waiting_id = ModelStatus.by_name(ModelStatus.WAITING).id
            for model in analysis.models:
                model.status_id = processing_id
            analysis.models.first().status_id = waiting_id
            # only one analysis, all processing but one waiting
            analyses_count = Analysis.query.count()
            self.assertEquals(analyses_count, 1)
            # and the one has status waiting on class level
            analyses_status_count = Analysis.query.filter(Analysis.analysis_status_id == waiting_id).count()
            self.assertEquals(analyses_status_count, 1)
            # as well as on instance level
            self.assertEquals(analysis.analysis_status_id, waiting_id)

    def test_analysis_status_id_processing(self):
        with app.app_context():
            action = add_simple_action(db.session)
            analysis = add_simple_models_analysis(db.session, action.id)
            finished_id = ModelStatus.by_name(ModelStatus.FINISHED).id
            processing_id = ModelStatus.by_name(ModelStatus.PROCESSING).id
            for model in analysis.models:
                model.status_id = finished_id
            analysis.models.first().status_id = processing_id
            # only one analysis, all finished but one processing
            analyses_count = Analysis.query.count()
            self.assertEquals(analyses_count, 1)
            # and the one has status processing on class level
            analyses_status_count = Analysis.query.filter(Analysis.analysis_status_id == processing_id).count()
            self.assertEquals(analyses_status_count, 1)
            # as well as on instance level
            self.assertEquals(analysis.analysis_status_id, processing_id)

    def test_analysis_updating_unfinished(self):
        with app.app_context():
            action = add_simple_action(db.session)
            analysis = add_simple_models_analysis(db.session, action.id)
            processing_id = ModelStatus.by_name(ModelStatus.PROCESSING).id
            for model in analysis.models:
                model.status_id = processing_id
            with self.assertRaises(ValueError):
                analysis_data = {'ipp_latitude': 1123123}
                analysis.update(analysis_data, None, None)


class AnalysisComputationTest(ModelsTest):

    def test_starting_analysis_requires_complete_data(self):
        with app.app_context():
            action = add_simple_action(db.session)
            analysis = add_analysis_with_coordinates(db.session, action.id)
            with self.assertRaises(AnalysisDataIncomplete):
                analysis.start_computation()

    def test_cs_profiles_representation(self):
        with app.app_context():
            action = add_simple_action(db.session)
            analysis = add_analysis_with_coordinates(db.session, action.id)

            person_type_tourist = PersonType.query.filter_by(name='tourist').first()
            person_type_climber = PersonType.query.filter_by(name='climber').first()

            weight_tourist, weight_climber = 3, 7

            tourist = Profile(analysis_id=analysis.id, person_type_id=person_type_tourist.id,
                              weight=weight_tourist)
            climber = Profile(analysis_id=analysis.id, person_type_id=person_type_climber.id,
                              weight=weight_climber)
            db.session.add(tourist)
            db.session.add(climber)
            db.session.flush()

            expected = {'tourist': weight_tourist, 'climber': weight_climber}

            self.assertEquals(len(analysis.cs_profiles()), 2)
            self.assertEquals(analysis.cs_profiles(), expected)

    def test_cs_simple_models_representation(self):
        with app.app_context():
            action = add_simple_action(db.session)
            analysis = add_analysis_with_coordinates(db.session, action.id)

            # add simple models
            model_type_names = ['HorDistIPP', 'ElevChgIPP', 'HorChgIPP', 'DispAngle',
                                'TrackOffset', 'FindLocation', 'Mobility']
            for mtn in model_type_names:
                model_type = ModelType.query.filter_by(name=mtn).first()
                model = Model(analysis_id=analysis.id, model_type_id=model_type.id)
                db.session.add(model)
                db.session.flush()

            expected = model_type_names

            self.assertEquals(len(analysis.cs_simple_models()), len(expected))
            self.assertEquals(analysis.cs_simple_models(), expected)

    def test_cs_complex_models_representation(self):
        with app.app_context():
            action = add_simple_action(db.session)
            analysis = add_analysis_with_coordinates(db.session, action.id)

            # add comb model
            model_type = ModelType.query.filter_by(name='CombProb').first()
            comb_model = Model(analysis_id=analysis.id, model_type_id=model_type.id)
            db.session.add(comb_model)
            db.session.flush()

            # add search seg model
            model_type = ModelType.query.filter_by(name='SearchSeg').first()
            seg_model = Model(analysis_id=analysis.id, model_type_id=model_type.id)
            db.session.add(seg_model)
            db.session.flush()

            # add simple models
            model_type_names = ['HorDistIPP', 'FindLocation', 'Mobility']
            result_ids = ['213', '543', '234']
            weight = 4
            for mtn, result_id in zip(model_type_names, result_ids):
                model_type = ModelType.query.filter_by(name=mtn).first()
                model = Model(analysis_id=analysis.id, model_type_id=model_type.id)
                db.session.add(model)
                db.session.flush()
                model.create_weights(parent_model_id=comb_model.id, weight=weight)
                model.create_weights(parent_model_id=seg_model.id, weight=weight)
                model.update_result(result_id)

            expected_complex_analyses = ['CombProb', 'SearchSeg']
            expected_model_weights = {
                'HorDistIPP': {'id': '213', 'weight': weight},
                'FindLocation': {'id': '543', 'weight': weight},
                'Mobility': {'id': '234', 'weight': weight},
            }

            cs_complex_models = analysis.cs_complex_models()
            cs_model_weights = analysis.cs_complex_model_weights()

            self.assertEquals(len(cs_complex_models), len(expected_complex_analyses))
            self.assertEquals(sorted(cs_complex_models), sorted(expected_complex_analyses))

            self.assertEquals(len(cs_model_weights), len(expected_model_weights))
            self.assertEquals(sorted(cs_model_weights), sorted(expected_model_weights))


class ActionTest(ModelsTest):

    def test_action_status_id_no_analyses(self):
        with app.app_context():
            action = add_simple_action(db.session)
            analyses_count = Analysis.query.count()
            # only one analysis, no models
            self.assertEquals(analyses_count, 0)
            draft_id = ModelStatus.draft_id()
            # and the one has status draft on class level
            draft_count = Action.query.filter(Action.action_status_id == draft_id).count()
            self.assertEquals(draft_count, 1)
            # as well as on instance level
            self.assertEquals(action.action_status_id, draft_id)

    def test_action_status_id_finished(self):
        with app.app_context():
            action = add_simple_action(db.session)
            analysis = add_simple_models_analysis(db.session, action.id)
            finished_id = ModelStatus.by_name(ModelStatus.FINISHED).id
            for model in analysis.models:
                model.status_id = finished_id

            analysis = add_simple_models_analysis(db.session, action.id)
            finished_id = ModelStatus.by_name(ModelStatus.FINISHED).id
            for model in analysis.models:
                model.status_id = finished_id
            # two analyses, all finished
            analyses_count = Analysis.query.count()
            self.assertEquals(analyses_count, 2)

            action_status_count = Action.query.filter(Action.action_status_id == finished_id).count()
            self.assertEquals(action_status_count, 1)

            # as well as on instance level
            self.assertEquals(action.action_status_id, finished_id)

    def test_action_status_id_error(self):
        with app.app_context():
            action = add_simple_action(db.session)
            waiting_id = ModelStatus.by_name(ModelStatus.WAITING).id
            error_id = ModelStatus.by_name(ModelStatus.ERROR).id

            analysis = add_simple_models_analysis(db.session, action.id)
            for model in analysis.models:
                model.status_id = waiting_id

            analysis = add_simple_models_analysis(db.session, action.id)
            for model in analysis.models:
                model.status_id = error_id

            action_status_count = Action.query.filter(Action.action_status_id == error_id).count()
            self.assertEquals(action_status_count, 1)
            self.assertEquals(action.action_status_id, error_id)

    def test_action_status_id_waiting(self):
        with app.app_context():
            action = add_simple_action(db.session)
            processing_id = ModelStatus.by_name(ModelStatus.PROCESSING).id
            waiting_id = ModelStatus.by_name(ModelStatus.WAITING).id

            analysis = add_simple_models_analysis(db.session, action.id)
            for model in analysis.models:
                model.status_id = waiting_id

            analysis = add_simple_models_analysis(db.session, action.id)
            for model in analysis.models:
                model.status_id = processing_id

            action_status_count = Action.query.filter(Action.action_status_id == waiting_id).count()
            self.assertEquals(action_status_count, 1)
            self.assertEquals(action.action_status_id, waiting_id)

    def test_action_status_id_processing(self):
        with app.app_context():
            action = add_simple_action(db.session)
            processing_id = ModelStatus.by_name(ModelStatus.PROCESSING).id
            finished_id = ModelStatus.by_name(ModelStatus.FINISHED).id

            analysis = add_simple_models_analysis(db.session, action.id)
            for model in analysis.models:
                model.status_id = finished_id

            analysis = add_simple_models_analysis(db.session, action.id)
            for model in analysis.models:
                model.status_id = processing_id

            action_status_count = Action.query.filter(Action.action_status_id == processing_id).count()
            self.assertEquals(action_status_count, 1)
            self.assertEquals(action.action_status_id, processing_id)


if __name__ == '__main__':
    unittest.main()
