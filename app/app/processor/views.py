from flask import Blueprint, request
from flask_restful import Api, Resource
from ..helpers import resource_does_not_exist, validation_failed, request_resource_unavailable, server_not_available, \
    AnalysisDataIncomplete, analysis_data_incomplete
from ..processor.config_api import ConfigApi
from ..processor.cs_utils import ServerException
from ..processor.schemas import ActionSchema, AnalysisSchema, ModelSchema, ActionQuerySchema, ActionListSchema, \
    ProfileSchema, AnalysisQuerySchema, AnalysisExecutionSchema, ActionBaseSchema, ModelBaseSchema, ProfileBaseSchema
from ..database import db
from .models import Action, Analysis, ModelStatus, Model, ActionStatus, Profile, ModelWeight

processor = Blueprint('processor', __name__, url_prefix='/app/api/v1')
api = Api(processor, catch_all_404s=True)
api.add_resource(ConfigApi, '/config', endpoint='config')


@processor.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,PATCH,DELETE')
    return response


@api.resource('/actions', endpoint='actions')
class ActionListApi(Resource):

    def get(self):
        schema = ActionQuerySchema()
        data, errors = schema.load(request.args)
        if errors:
            validation_failed(errors)

        statuses = data.get('status')
        archived = data.get('archived')
        name_query = data.get('name')
        created_from, created_to = data.get('created_from'), data.get('created_to')
        lost_from, lost_to = data.get('lost_from'), data.get('lost_to')
        action_query = Action.filtered(statuses=statuses, archived=archived,
                                       name_search=name_query,
                                       created_from=created_from, created_to=created_to,
                                       lost_from=lost_from, lost_to=lost_to)
        limit = None

        # pagination
        per_page, page_ts = data.get('per_page'), data.get('page_ts')
        if per_page and page_ts:
            action_query = action_query.filter(Action.creation_time <= page_ts)
            limit = per_page

        # general: limits and default order
        if limit:
            actions = action_query.limit(per_page).all()
        else:
            actions = action_query.order_by(Action.creation_time.desc()).all()

        schema = ActionListSchema(many=True)
        data, _ = schema.dump(actions)
        return data, 200

    def post(self):
        """
        Returns created action item with its shortened analysis data items.
        """
        creation_schema, schema = ActionBaseSchema(), ActionSchema()
        input_data = request.get_json()
        data, errors = creation_schema.load(input_data)
        if errors:
            validation_failed(errors)
        analyses_data = data.pop('analyses', None)
        action = Action(**data)
        db.session.add(action)
        db.session.flush()
        if analyses_data:
            action.create_analyses(db.session, analyses_data)
        db.session.commit()
        data, _ = schema.dump(action)
        return data, 201


@api.resource('/actions/<int:action_id>')
class ActionApi(Resource):

    def get(self, action_id):
        """
        Returns complete action item: with all nested analyses,
        their models and other nested data items.
        """
        action = Action.query.get(action_id)
        if action is None or action.deleted:
            resource_does_not_exist()
        schema = ActionSchema()
        data, _ = schema.dump(action)
        return data, 200

    def patch(self, action_id):
        action = Action.query.get(action_id)
        if action is None:
            resource_does_not_exist()
        schema = ActionSchema()
        data, _ = schema.dump(action)
        for key, value in request.get_json().items():
            data[key] = value
        data.pop('analyses', None)
        action_data, errors = ActionSchema().load(data)
        if errors:
            validation_failed(errors)
        for k, v in action_data.items():
            setattr(action, k, v)
        db.session.commit()
        schema = ActionSchema()
        action_data, _ = schema.dump(action)
        return action_data, 200

    def delete(self, action_id):
        action = Action.query.get(action_id)
        if action is None or action.deleted:
            resource_does_not_exist()
        action.deleted = True
        db.session.commit()
        return None, 204


@api.resource('/analyses', endpoint='analyses')
class AnalysisListApi(Resource):

    def get(self):
        schema = AnalysisQuerySchema()
        data, errors = schema.load(request.args)
        if errors:
            validation_failed(errors)

        statuses = data.get('status')
        name_query = data.get('query')
        created_from, created_to = data.get('created_from'), data.get('created_to')
        lost_from, lost_to = data.get('lost_from'), data.get('lost_to')
        analysis_query = Analysis.filtered(
            statuses=statuses,
            name_search=name_query,
            created_from=created_from,
            created_to=created_to,
            lost_from=lost_from,
            lost_to=lost_to)
        limit = None

        # pagination
        per_page, page_ts = data.get('per_page'), data.get('page_ts')
        if per_page and page_ts:
            analysis_query = analysis_query.filter(Analysis.creation_time <= page_ts)
            limit = per_page

        # general: limits and default order
        if limit:
            analyses = analysis_query.limit(per_page).all()
        else:
            analyses = analysis_query.order_by(Analysis.creation_time.desc()).all()

        schema = AnalysisSchema(many=True)
        data, _ = schema.dump(analyses)
        return data, 200

    def post(self):
        """
        Creates and returns created analysis by full representation
        """
        schema = AnalysisSchema()
        input_data = request.get_json()
        data, errors = schema.load(input_data)
        if errors:
            validation_failed(errors)
        analysis_id = data.pop('analysis_id', None)
        models_data = data.pop('models', None)
        profiles_data = data.pop('profiles', None)
        if analysis_id is None:
            analysis = Analysis(**data)
            db.session.add(analysis)
            db.session.flush()
        else:   # duplicate analysis
            analysis = Analysis.query.get(int(analysis_id))
            if analysis is None:
                resource_does_not_exist()
            analysis = analysis.duplicate(data)
        if models_data:
            analysis.create_or_update_models(models_data)
        if profiles_data:
            analysis.create_or_update_profiles(profiles_data)
        db.session.commit()
        data, _ = schema.dump(analysis)
        return data, 201


@api.resource('/analyses/<int:analysis_id>')
class AnalysisApi(Resource):

    def get(self, analysis_id):
        analysis = Analysis.query.get(analysis_id)
        if analysis is None or analysis.deleted:
            resource_does_not_exist()
        schema = AnalysisSchema(strict=True)
        data, _ = schema.dump(analysis)
        return data, 200

    def post(self, analysis_id):

        # find requested resource
        analysis = Analysis.query.get(analysis_id)
        if analysis is None or analysis.deleted:
            resource_does_not_exist()

        # retrieve execution parameters
        schema = AnalysisExecutionSchema()
        data, errors = schema.load(request.get_json())
        if errors:
            validation_failed(errors)

        try:
            started = data.get('started', None)
            if started:
                analysis.start_computation()
            elif started is not None:
                analysis.stop_computation()
            else:
                request_resource_unavailable()
            db.session.commit()
            analysis = Analysis.query.get(analysis_id)
            data, _ = AnalysisSchema().dump(analysis)
            return data, 200
        except AnalysisDataIncomplete:
            analysis_data_incomplete()
        except ServerException:
            server_not_available()

    def patch(self, analysis_id):

        # retrieve analysis
        analysis = Analysis.query.get(analysis_id)
        if analysis is None:
            resource_does_not_exist()

        # load analysis
        analysis_schema = AnalysisSchema(dump_only=('models', 'profiles'))
        analysis_data, _ = analysis_schema.dump(analysis)

        # read request data
        request_analysis = request.get_json()
        models = request_analysis.pop('models', [])
        profiles = request_analysis.pop('profiles', [])

        # accumulate data
        analysis_data.update(request_analysis.items())

        # validate analysis data
        data, errors = analysis_schema.load(analysis_data)
        if errors:
            validation_failed(errors)

        # validate nested objects
        model_schema = ModelBaseSchema(many=True)
        profile_schema = ProfileBaseSchema(many=True)
        models, models_errors = model_schema.load(models)
        profiles, profiles_errors = profile_schema.load(profiles)

        # update analysis
        analysis.update(data, models, profiles)
        db.session.commit()

        # return analysis
        analysis_schema = AnalysisSchema()
        analysis_data, _ = analysis_schema.dump(analysis)
        return analysis_data, 200

    def delete(self, analysis_id):
        analysis = Analysis.query.get(analysis_id)
        if analysis is None or analysis.deleted:
            resource_does_not_exist()
        analysis.deleted = True
        db.session.commit()
        return None, 204


@api.resource('/models', endpoint='models')
class ModelListApi(Resource):

    def post(self):
        schema = ModelSchema()
        data, errors = schema.load(request.get_json())
        if errors:
            validation_failed(errors)
        analysis = Analysis.query.get(data.get("analysis_id"))
        if analysis is None or analysis.deleted:
            raise Exception("Related analysis doesn't exist.")
        if analysis.analysis_status_id != ModelStatus.draft_id():
            raise Exception("Analysis must be a draft to add models.")
        if Model.query.filter_by(analysis_id=data['analysis_id'], model_type_id=data['model_type_id']).first():
            raise Exception("Can't add multiple models of the same type to one analysis.")
        model_status_id = ModelStatus.draft_id()
        weight = data.pop('weight')
        model = Model(status_id=model_status_id, **data)
        db.session.add(model)
        db.session.flush()
        model_weight = ModelWeight(weight=weight, child_model_id=model.id, model_id=model.id)
        db.session.add(model_weight)
        db.session.commit()
        data, _ = schema.dump(model)
        return data, 201


@api.resource('/models/<int:model_id>')
class ModelApi(Resource):

    def delete(self, model_id):
        model = Model.query.get(model_id)
        if model is None or model.analysis.deleted:
            resource_does_not_exist()
        if model.analysis.analysis_status_id != ModelStatus.draft_id():
            raise Exception("Analysis must be a draft to deleted models.")
        db.session.delete(model)
        db.session.commit()
        return None, 204


@api.resource('/profiles', endpoint='profiles')
class ProfileListApi(Resource):

    def post(self):
        schema = ProfileSchema()
        data, errors = schema.load(request.get_json())
        if errors:
            validation_failed(errors)
        analysis = Analysis.query.get(data.get("analysis_id"))
        if analysis is None or analysis.deleted:
            raise Exception("Related analysis doesn't exist.")
        if analysis.analysis_status_id != ModelStatus.draft_id():
            raise Exception("Analysis must be a draft to add profiles.")
        if Profile.query.filter_by(analysis_id=data['analysis_id'], person_type_id=data['person_type_id']).first():
            raise Exception("Can't add multiple profiles of the same type to one analysis.")
        profile = Profile(**data)
        db.session.add(profile)
        db.session.commit()
        data, _ = schema.dump(profile)
        return data, 201


@api.resource('/profiles/<int:profile_id>')
class ProfileApi(Resource):

    def delete(self, profile_id):
        profile = Profile.query.get(profile_id)
        if profile is None or profile.analysis.deleted:
            resource_does_not_exist()
        if profile.analysis.analysis_status_id != ModelStatus.draft_id():
            raise Exception("Analysis must be a draft to delete profiles.")
        db.session.delete(profile)
        db.session.commit()
        return None, 204


@api.resource('/notifications', endpoint='notifications')
class NotificationsApi(Resource):

    def get(self):
        return [], 200
