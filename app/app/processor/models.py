import logging
from flask import current_app
from sqlalchemy import String, Integer, Text, Boolean, Float, DateTime, CHAR, func, select, case, true, false
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm import column_property
from sqlalchemy.sql.elements import and_
from ..helpers import AnalysisDataIncomplete
from ..processor import cs_utils
from ..database import db


class IdentityMixin(object):
    id = db.Column(Integer, primary_key=True, autoincrement=True)


class ActionStatus(IdentityMixin, db.Model):
    __tablename__ = 'action_statuses'

    # columns
    name = db.Column(String(64), nullable=False, unique=True)

    # relationships
    actions = db.relationship('Action', backref=db.backref('action_status', lazy='joined'), lazy='dynamic')


available_analyses = db.Table(
    'available_analyses',
    db.Column('id', Integer, primary_key=True, autoincrement=True),
    db.Column('model_type_id', Integer, db.ForeignKey('model_types.id')),
    db.Column('person_type_id', Integer, db.ForeignKey('person_types.id'))
)


class ModelType(IdentityMixin, db.Model):
    __tablename__ = 'model_types'

    # columns
    name = db.Column(String(256), nullable=False, unique=True)
    active = db.Column(Boolean, nullable=False)
    complex = db.Column(Boolean, nullable=False, default=False)

    @classmethod
    def valid(cls):
        return db.session.query(cls).filter(cls.active == True)


class PersonType(IdentityMixin, db.Model):
    __tablename__ = 'person_types'

    # columns
    name = db.Column(String(256), nullable=False, unique=True)
    active = db.Column(Boolean, nullable=False)

    # relationships
    available_model_types = db.relationship('ModelType', secondary=available_analyses,
                                            backref=db.backref('available_person_types', lazy='dynamic'))

    @classmethod
    def valid(cls):
        return db.session.query(cls).filter(cls.active == True)


class ModelStatus(IdentityMixin, db.Model):
    __tablename__ = 'model_statuses'

    # columns
    name = db.Column(String(64), nullable=False, unique=True)

    # relationships
    models = db.relationship('Model', backref=db.backref('model_status', lazy='joined'),
                             lazy='dynamic')

    DRAFT = 'draft'             # app only
    WAITING = 'waiting'         # both
    PROCESSING = 'processing'   # app only
    COMPUTING = 'computing'     # server only
    LOADING = 'loading'         # server only
    CONVERTING = 'converting'   # server only
    ERROR = 'error'             # both
    FINISHED = 'finished'       # both

    @classmethod
    def by_name(cls, name):
        return cls.query.filter(cls.name == name).first()

    @classmethod
    def draft_id(cls):
        return cls.by_name(cls.DRAFT).id

    @classmethod
    def names(cls):
        return [cls.DRAFT, cls.WAITING, cls.PROCESSING, cls.ERROR, cls.FINISHED]

    @classmethod
    def unfinished_names(cls):
        return [cls.WAITING, cls.PROCESSING]


class Action(IdentityMixin, db.Model):
    __tablename__ = 'actions'

    # columns
    #

    name = db.Column(String(256), nullable=False)
    description = db.Column(Text, nullable=True)
    user_id = db.Column(Integer, db.ForeignKey('users.id'), nullable=True)
    _action_status_id = db.Column('action_status_id', Integer, db.ForeignKey('action_statuses.id'), nullable=True)
    ipp_latitude = db.Column(Float, nullable=True)
    ipp_longitude = db.Column(Float, nullable=True)
    rp_latitude = db.Column(Float, nullable=True)
    rp_longitude = db.Column(Float, nullable=True)
    lost_time = db.Column(DateTime, nullable=False)
    creation_time = db.Column(DateTime, nullable=False, default=func.now())
    _deleted = db.Column('deleted', Boolean, nullable=False, default=False)
    archived = db.Column(Boolean, nullable=False, default=False)

    # relationships
    #

    analyses = db.relationship('Analysis', cascade="all,delete", lazy='dynamic',
                               primaryjoin="and_(Action.id==Analysis.action_id, Analysis.deleted == False)",
                               order_by='Analysis.creation_time.desc()')

    # queries
    #

    @classmethod
    def filtered(cls, deleted=False, statuses=None, archived=None, name_search=None,
                 created_from=None, created_to=None, lost_from=None, lost_to=None):
        res = cls.query
        if deleted is not None:
            res = res.filter(cls.deleted == True) if deleted else res.filter(cls.deleted == False)
        if statuses:
            res = res.filter(cls.action_status_id.in_(statuses))
        if archived is not None:
            res = res.filter(cls.archived == True) if archived else res.filter(cls.archived == False)
        if name_search:
            res = res.filter(cls.name.ilike('%'+name_search+'%'))
        if created_from is not None:
            res = res.filter(cls.creation_time >= created_from)
        if created_to is not None:
            res = res.filter(cls.creation_time <= created_to)
        if lost_from is not None:
            res = res.filter(cls.lost_time >= lost_from)
        if lost_to is not None:
            res = res.filter(cls.lost_time <= lost_to)
        return res

    # properties
    #

    @hybrid_property
    def deleted(self):
        return self._deleted

    @deleted.setter
    def deleted(self, deleted):
        self._deleted = deleted
        for analysis in self.analyses:
            analysis.deleted = True

    @hybrid_property
    def analyses_count(self):
        return self.analyses.count()

    @analyses_count.expression
    def analyses_count(cls):
        return select([func.count(Analysis.id)]).where(Analysis.action_id == cls.id).label("analyses_count")

    @hybrid_method
    def analyses_by_status_count(self, status_id):
        return self.analyses.filter(Analysis.analysis_status_id == status_id).count()

    @analyses_by_status_count.expression
    def analyses_by_status_count(cls, status_id):
        return select([func.count(Analysis.id)]).select_from(ModelStatus) \
            .where(and_(Analysis.action_id == cls.id, Analysis.analysis_status_id == status_id)).label('analyses_by_status_count')

    @hybrid_property
    def action_status_id(self):
        error_status_id = ModelStatus.by_name(ModelStatus.ERROR).id
        waiting_status_id = ModelStatus.by_name(ModelStatus.WAITING).id
        finished_status_id = ModelStatus.by_name(ModelStatus.FINISHED).id
        draft_status_id = ModelStatus.by_name(ModelStatus.DRAFT).id
        processing_status_id = ModelStatus.by_name(ModelStatus.PROCESSING).id

        if self.analyses_count == 0:
            return draft_status_id
        elif self.analyses.filter_by(analysis_status_id=error_status_id).count():
            return error_status_id
        elif self.analyses.filter_by(analysis_status_id=waiting_status_id).count():
            return waiting_status_id
        elif self.analyses.filter_by(analysis_status_id=processing_status_id).count():
            return processing_status_id
        elif self.analyses.filter_by(analysis_status_id=finished_status_id).count():
            return finished_status_id
        elif self.analyses.filter_by(analysis_status_id=draft_status_id).count() == self.analyses_count:
            return draft_status_id
        else:
            return processing_status_id

    @action_status_id.expression
    def analysis_status_id(cls):
        error_status_id = ModelStatus.by_name(ModelStatus.ERROR).id
        waiting_status_id = ModelStatus.by_name(ModelStatus.WAITING).id
        finished_status_id = ModelStatus.by_name(ModelStatus.FINISHED).id
        draft_status_id = ModelStatus.by_name(ModelStatus.DRAFT).id
        processing_status_id = ModelStatus.by_name(ModelStatus.PROCESSING).id

        analyses_count = cls.analyses_count
        draft_count = cls.analyses_by_status_count(draft_status_id)
        finished_count = cls.analyses_by_status_count(finished_status_id)
        error_count = cls.analyses_by_status_count(error_status_id)
        waiting_count = cls.analyses_by_status_count(waiting_status_id)
        processing_count = cls.analyses_by_status_count(processing_status_id)

        return case([
            (analyses_count == 0, draft_status_id),
            (error_count > 0, error_status_id),
            (waiting_count > 0, waiting_status_id),
            (processing_count > 0, processing_status_id),
            (finished_count > 0, finished_status_id),
            (draft_count >= analyses_count, draft_status_id),
        ], else_=processing_status_id)

    # api create/update methods
    #

    def create_analyses(self, session, analyses):
        for analysis_data in analyses:
            analysis_data['action_id'] = self.id
            models = analysis_data.pop('models', None)
            profiles = analysis_data.pop('profiles', None)
            analysis = Analysis(**analysis_data)
            session.add(analysis)
            session.flush()
            if models:
                analysis.create_or_update_models(models)
            if profiles:
                analysis.create_or_update_profiles(profiles)


class Analysis(IdentityMixin, db.Model):
    __tablename__ = 'analyses'

    # columns
    #

    action_id = db.Column(Integer, db.ForeignKey('actions.id'), nullable=False)
    name = db.Column(String(256), nullable=False)
    description = db.Column(Text, nullable=True)
    _ipp_latitude = db.Column("ipp_latitude", Float, nullable=True)
    _ipp_longitude = db.Column("ipp_longitude", Float, nullable=True)
    _rp_latitude = db.Column("rp_latitude", Float, nullable=True)
    _rp_longitude = db.Column("rp_longitude", Float, nullable=True)
    active = db.Column(Boolean, nullable=False, default=True)
    _lost_time = db.Column("lost_time", DateTime, nullable=True)
    creation_time = db.Column(DateTime, nullable=False, default=func.now())
    deleted = db.Column(Boolean, nullable=False, default=False)

    action = db.relationship('Action', primaryjoin='Action.id==Analysis.action_id')

    # relationships
    #

    models = db.relationship('Model', backref='analysis', cascade="all,delete",
                             lazy='dynamic')
    profiles = db.relationship('Profile', backref='analysis', cascade="all,delete",
                               lazy='dynamic')

    # queries
    #

    def simple_models(self):
        return self.models.join(Model.model_type).filter(ModelType.complex == False)

    def complex_models(self):
        return self.models.join(Model.model_type).filter(ModelType.complex == True)

    def draft_models(self):
        draft_status = ModelStatus.by_name(ModelStatus.DRAFT)
        return self.models.filter(Model.status_id == draft_status.id)

    @classmethod
    def filtered(cls, deleted=False, statuses=None, name_search=None,
                 created_from=None, created_to=None, lost_from=None, lost_to=None):
        res = cls.query
        res = res.filter(cls.archived == False)
        if deleted is not None:
            res = res.filter(cls.deleted == True) if deleted else res.filter(cls.deleted == False)
        if statuses:
            res = res.filter(cls.analysis_status_id.in_(statuses))
        if name_search:
            res = res.filter(cls.name.contains(name_search))
        if created_from is not None:
            res = res.filter(cls.creation_time >= created_from)
        if created_to is not None:
            res = res.filter(cls.creation_time <= created_to)
        if lost_from is not None:
            res = res.filter(cls.lost_time >= lost_from)
        if lost_to is not None:
            res = res.filter(cls.lost_time <= lost_to)
        return res

    # properties
    #

    @hybrid_property
    def archived(self):
        return self.action.archived

    @archived.expression
    def archived(cls):
        return select([Action.archived]).\
            where(Action.id == cls.action_id).\
            label('archived')

    @hybrid_property
    def model_count(self):
        return self.models.count()

    @model_count.expression
    def model_count(cls):
        return select([func.count(Model.id)]).\
            where(Model.analysis_id == cls.id).\
            label("model_count")

    @hybrid_method
    def model_by_status_count(self, model_status_id):
        return self.models.filter(Model.status_id == model_status_id).count()

    @model_by_status_count.expression
    def model_by_status_count(cls, model_status_id):
        return select([func.count(Model.id)])\
            .select_from(ModelStatus) \
            .where(and_(Model.analysis_id == cls.id, Model.status_id == model_status_id))\
            .label('model_by_status_count')

    @hybrid_property
    def ipp_latitude(self):
        return self._ipp_latitude or self.action.ipp_latitude

    @ipp_latitude.setter
    def ipp_latitude(self, ipp_latitude):
        self._ipp_latitude = ipp_latitude

    @hybrid_property
    def ipp_longitude(self):
        return self._ipp_longitude or self.action.ipp_longitude

    @ipp_longitude.setter
    def ipp_longitude(self, ipp_longitude):
        self._ipp_longitude = ipp_longitude

    @hybrid_property
    def rp_latitude(self):
        return self._rp_latitude or self.action.rp_latitude

    @rp_latitude.setter
    def rp_latitude(self, rp_latitude):
        self._rp_latitude = rp_latitude

    @hybrid_property
    def rp_longitude(self):
        return self._rp_longitude or self.action.rp_longitude

    @rp_longitude.setter
    def rp_longitude(self, rp_longitude):
        self._rp_longitude = rp_longitude

    @hybrid_property
    def lost_time(self):
        return self._lost_time or self.action.lost_time

    @lost_time.expression
    def lost_time(cls):
        return case([
            (cls._lost_time != None, cls._lost_time.label("lost_time")),
            (cls.action_id != None, select([Action.lost_time]).where(Action.id == cls.action_id).label('lost_time'))
        ], else_ = cls._lost_time.label("lost_time"))

    @lost_time.setter
    def lost_time(self, lost_time):
        self._lost_time = lost_time

    @hybrid_property
    def action_name(self):
        return self.action.name

    # analysis_status_id
    #

    @hybrid_property
    def analysis_status_id(self):
        error_status_id = ModelStatus.by_name(ModelStatus.ERROR).id
        waiting_status_id = ModelStatus.by_name(ModelStatus.WAITING).id
        finished_status_id = ModelStatus.by_name(ModelStatus.FINISHED).id
        draft_status_id = ModelStatus.by_name(ModelStatus.DRAFT).id
        processing_status_id = ModelStatus.by_name(ModelStatus.PROCESSING).id

        if self.model_count == 0:
            return draft_status_id
        elif self.models.filter_by(status_id=error_status_id).count():
            return error_status_id
        elif self.models.filter_by(status_id=waiting_status_id).count():
            return waiting_status_id
        elif self.models.filter_by(status_id=processing_status_id).count():
            return processing_status_id
        elif self.models.filter_by(status_id=finished_status_id).count():
            return finished_status_id
        elif self.models.filter_by(status_id=draft_status_id).count() == self.model_count:
            return draft_status_id
        else:
            return processing_status_id

    @analysis_status_id.expression
    def analysis_status_id(cls):
        error_status_id = ModelStatus.by_name(ModelStatus.ERROR).id
        waiting_status_id = ModelStatus.by_name(ModelStatus.WAITING).id
        finished_status_id = ModelStatus.by_name(ModelStatus.FINISHED).id
        draft_status_id = ModelStatus.by_name(ModelStatus.DRAFT).id
        processing_status_id = ModelStatus.by_name(ModelStatus.PROCESSING).id

        model_count = cls.model_count
        draft_count = cls.model_by_status_count(draft_status_id)
        finished_count = cls.model_by_status_count(finished_status_id)
        error_count = cls.model_by_status_count(error_status_id)
        waiting_count = cls.model_by_status_count(waiting_status_id)
        processing_count = cls.model_by_status_count(processing_status_id)

        return case([
            (model_count == 0, draft_status_id),
            (error_count > 0, error_status_id),
            (waiting_count > 0, waiting_status_id),
            (processing_count > 0, processing_status_id),
            (finished_count > 0, finished_status_id),
            (draft_count >= model_count, draft_status_id),
        ], else_=processing_status_id)

    # api create/update methods
    #

    def update(self, analysis_data, models, profiles):
        status = ModelStatus.query.get(self.analysis_status_id)
        if status.name in ModelStatus.unfinished_names():
            raise ValueError('Cannot update unfinished analysis')
        if analysis_data:
            for k, v in analysis_data.items():
                setattr(self, k, v)
        self.create_or_update_models(models)
        self.create_or_update_profiles(profiles)

    def create_or_update_profiles(self, profiles):
        if not self.analysis_status_id == ModelStatus.by_name(ModelStatus.DRAFT).id:
            RuntimeError("can only update models if analysis is a draft")
        profiles_data = {profile['person_type_id']: profile['weight'] for profile in profiles}
        existing_profiles = {profile.person_type_id: profile for profile in self.profiles}

        for person_type_id, profile in existing_profiles.items():
            if person_type_id in profiles_data.keys():
                profile.weight = profiles_data[person_type_id]
                del profiles_data[person_type_id]
            else:
                db.session.delete(profile)
            db.session.flush()

        for person_type_id, weight in profiles_data.items():
            profile = Profile(analysis_id=self.id, person_type_id=person_type_id, weight=weight)
            db.session.add(profile)
            db.session.flush()

    def create_or_update_models(self, models):
        """
        Updates action models based on models data. Basically it compares models given as a dictionary
        and analysis previous models.

        Five different strategies are applied:
        1. Deleting model and its weights (by model_id and child_model_id) if not present in models. For simple it deletes
         its model_weights, for complex it check if it is the only complex, if so changes child_model_id to model_id,
         otherwise deletes by child_model_id.
        2. Updating complex models is just keeping it as is
        3. Updating simple models is iteration on all its weights (through model_id) and changing their weight attribute
        4. Creating complex models is creating model and iterating over all simple models and adding new weights for them
         for cases where model_id == child_model_id or child_model_id is belongs to other complex model.
        5. Creating simple models is creating its weight where model_id and child_model_id comes from iteration
         on all complex models.

        :param models: dictionary of model_type_id and weight integers
        """
        if not self.analysis_status_id == ModelStatus.by_name(ModelStatus.DRAFT).id:
            RuntimeError("can only update models if analysis is a draft")
        models_data = {model['model_type_id']: model['weight'] for model in models}
        existing_models = {model.model_type_id: model for model in self.models}

        for model_type_id, model in existing_models.items():
            if model_type_id in models_data.keys():
                if models_data[model_type_id] is not None:
                    model.update_weights(models_data[model_type_id])
                del models_data[model_type_id]
            else:
                self._delete_model(model)
            db.session.flush()

        for model_type_id, weight in models_data.items():
            self.create_model(model_type_id, weight)

    def create_model(self, model_type_id, weight):
        model_status_id = ModelStatus.draft_id()
        model = Model(status_id=model_status_id,
                      model_type_id=model_type_id,
                      analysis_id=self.id)
        db.session.add(model)
        db.session.flush()
        if model.complex:
            self.create_complex_model_weights(model)
        else:
            self.create_simple_model_weights(model, weight)
        db.session.flush()

    def create_complex_model_weights(self, model):
        for simple_model in self.simple_models():
            assert simple_model.model_weights.count() > 0
            model_weight = simple_model.model_weights[0]
            for mw in simple_model.model_weights:
                assert mw.weight == model_weight.weight
            if model_weight.model_id == model_weight.child_model_id:
                model_weight.child_model_id = model.id
            else:
                weight = model_weight.weight
                simple_model.create_weights(weight, model.id)

    def create_simple_model_weights(self, model, weight):
        if self.complex_models().count() == 0:
            model.create_weights(weight, model.id)
        else:
            for complex_model in self.complex_models():
                model.create_weights(weight, complex_model.id)

    def _delete_model(self, model):
        if model.complex:
            self._delete_complex_model_weights(model)
        else:
            self._delete_simple_model_weights(model)
        db.session.delete(model)

    def _delete_complex_model_weights(self, model):
        if self.complex_models().count() == 1:
            for simple_model in model.child_model_weights:
                simple_model.child_model_id = simple_model.model_id
        else:
            for model_weight in model.child_model_weights:
                db.session.delete(model_weight)
        assert model.child_model_weights.count() == 0

    def _delete_simple_model_weights(self, model):
        for model_weight in model.model_weights:
            db.session.delete(model_weight)

    # duplication methods
    #

    def duplicate(self, items):
        data = dict()
        attrs = ['name', 'description', 'lost_time', 'action_id', 'deleted',
                 'ipp_latitude', 'ipp_longitude', 'rp_latitude', 'rp_longitude']
        for attr in attrs:
            data[attr] = items.get(attr) or getattr(self, attr, None)

        analysis = Analysis(**data)
        db.session.add(analysis)
        db.session.flush()

        self._duplicate_models(analysis)
        for profile in self.profiles:
            profile.duplicate(analysis.id)

        return analysis

    def _duplicate_models(self, analysis):
        for simple_model in self.simple_models():
            duplicated_model = simple_model.duplicate(analysis.id)
            analysis.create_simple_model_weights(duplicated_model, simple_model.weight)
        for complex_model in self.complex_models():
            duplicated_model = complex_model.duplicate(analysis.id)
            analysis.create_complex_model_weights(duplicated_model)

    # computation methods
    #

    def cs_profiles(self):
        return {profile.name: profile.weight for profile in self.profiles}

    def cs_simple_models(self):
        return [model.name for model in self.simple_models()]

    def cs_complex_model_weights(self):
        # assuming all complex models from analysis have the same weight sets
        chosen_model = self.complex_models().first()
        return chosen_model.cs_model_weights()

    def cs_complex_models(self):
        return [model.name for model in self.complex_models()]

    def assert_ready_for_computation(self):
        try:
            assert self.ipp_latitude is not None
            assert self.ipp_longitude is not None
            assert self.rp_latitude is not None
            assert self.rp_longitude is not None
            assert self.lost_time is not None
            assert self.profiles.count() > 0
            assert self.simple_models().count() > 0
        except AssertionError:
            raise AnalysisDataIncomplete("Data for the analysis is incomplete")

    def start_computation(self):
        self.assert_ready_for_computation()
        draft_simple_models = self.draft_models().join(Model.model_type).filter(ModelType.complex == False)
        draft_complex_models = self.draft_models().join(Model.model_type).filter(ModelType.complex == True)
        if draft_simple_models.count():
            self.compute_simple_models()
        if self.complex_models().count() and draft_complex_models.count():
            self.compute_complex_models()

    def compute_simple_models(self):
        result_ids = cs_utils.compute_simple(ipp_longitude=self.ipp_longitude,
                                             ipp_latitude=self.ipp_latitude,
                                             rp_longitude=self.rp_longitude,
                                             rp_latitude=self.rp_latitude,
                                             profiles=self.cs_profiles(),
                                             models=self.cs_simple_models())

        for model in self.simple_models():
            model.update_result(result_ids[model.name])

    def compute_complex_models(self):
        result_ids = cs_utils.compute_complex(self.cs_complex_model_weights(), self.cs_complex_models())
        for model in self.complex_models():
            model.update_result(result_ids[model.name])

    # result methods
    #

    def update_result(self):
        for model in self.models:
            model.update_result()


class Layer(db.Model, IdentityMixin):
    __tablename__ = 'layers'

    # columns
    layers_id = db.Column(String(256), nullable=False)
    model_id = db.Column(Integer, db.ForeignKey('models.id'), nullable=False)

    def duplicate(self):
        layer = Layer(layers_id=self.layers_id, model_id=self.model_id)
        db.session.add(layer)
        db.session.flush()
        return layer


class Model(IdentityMixin, db.Model):
    __tablename__ = 'models'

    # columns
    analysis_id = db.Column(Integer, db.ForeignKey('analyses.id'), nullable=False)
    model_type_id = db.Column(Integer, db.ForeignKey('model_types.id'), nullable=False)
    status_id = db.Column(Integer, db.ForeignKey('model_statuses.id'), nullable=False)
    _result_id = db.Column('result_id', CHAR(64), nullable=True)

    def __init__(self, analysis_id, model_type_id, status_id=None, result_id=None):
        self.analysis_id = analysis_id
        self.model_type_id = model_type_id
        if status_id:
            self.status_id = status_id
        else:
            draft = ModelStatus.query.filter_by(name='draft').first()
            self.status_id = draft.id
        if result_id:
            self._result_id = result_id

    # relationships
    #

    layers = db.relationship('Layer', backref='model', lazy='dynamic', cascade="all,delete")
    model_type = db.relationship('ModelType', backref='models')

    # child_model_weights should have high count for complex model types, at most 1 for simple
    child_model_weights = db.relationship('ModelWeight', backref='parent_model',
                                          foreign_keys="[ModelWeight.child_model_id]", lazy='dynamic')

    # model_weights should be empty for complex and have high count for simple
    model_weights = db.relationship('ModelWeight', backref='model', cascade="all,delete",
                                    foreign_keys="[ModelWeight.model_id]", lazy='dynamic')

    # properties
    #

    name = column_property(select([ModelType.name]).
                           where(ModelType.id == model_type_id).
                           correlate_except(ModelType))
    complex = column_property(select([ModelType.complex]).
                              where(ModelType.id == model_type_id).
                              correlate_except(ModelType))

    @property
    def result_id(self):
        if not isinstance(self._result_id, str):
            return None
        return self._result_id.strip()

    @property
    def weight(self):
        if self.complex:
            return None
        assert self.model_weights.count() > 0
        model_weight = db.session.query(ModelWeight).filter(ModelWeight.model_id == self.id).first()
        return model_weight.weight if model_weight is not None else None

    # api create/update methods
    #

    def create_weights(self, weight=None, parent_model_id=None):
        assert not self.model_type.complex
        weight = weight or current_app.config['DEFAULT_WEIGHT']
        parent_model_id = parent_model_id or self.id
        self.model_weights.append(ModelWeight(child_model_id=parent_model_id, weight=weight))

    def update_weights(self, weight):
        assert not self.model_type.complex
        self.model_weights.update({'weight': weight})

    def duplicate(self, analysis_id):
        model = Model(analysis_id=analysis_id,
                      model_type_id=self.model_type_id,
                      status_id=self.status_id,
                      result_id=self.result_id)
        db.session.add(model)
        db.session.flush()
        for layer in self.layers:
            layer.duplicate()
        return model

    # computation methods
    #

    def cs_model_weights(self):
        return {weight.model.name: {'id': weight.model.result_id, 'weight': weight.weight}
                for weight in self.child_model_weights}

    # result methods
    #

    def layer_urls(self):
        return [l.layers_id for l in self.layers]

    def update_result(self, result_id=None):
        if self.status_id == ModelStatus.draft_id():
            assert result_id is not None
            self._result_id = result_id
            self.status_id = ModelStatus.by_name(ModelStatus.WAITING).id
        else:
            model_result = cs_utils.get_layers(self.result_id)
            if model_result['status'] in ModelStatus.names():
                status = ModelStatus.by_name(model_result['status'])
            else:
                status = ModelStatus.by_name(ModelStatus.PROCESSING)
            if status.id != self.status_id:
                logging.info('{} changing state from {} to {}'.
                             format(self.id, self.status_id, status.id))
                self.status_id = status.id
                if status.name == cs_utils.FINISHED:
                    for layer_id in model_result['layer_ids']:
                        layer = Layer(layers_id=layer_id, model_id=self.id)
                        db.session.add(layer)

    @classmethod
    def unfinished_models(cls):
        unfinished_statuses_ids = [ModelStatus.by_name(name).id for name in ModelStatus.unfinished_names()]
        return cls.query.filter(cls.status_id.in_(unfinished_statuses_ids))

    @classmethod
    def update_state_from_server(cls):
        for model in cls.unfinished_models():
            model.update_result()


class ModelWeight(IdentityMixin, db.Model):
    __tablename__ = 'model_weights'

    # columns
    model_id = db.Column(Integer, db.ForeignKey('models.id'), nullable=False)   # always simple model
    child_model_id = db.Column(Integer, db.ForeignKey('models.id'), nullable=False)
    weight = db.Column(Integer, nullable=False)


class Profile(IdentityMixin, db.Model):
    __tablename__ = 'profiles'

    # columns
    analysis_id = db.Column(Integer, db.ForeignKey('analyses.id'), nullable=False)
    person_type_id = db.Column(Integer, db.ForeignKey('person_types.id'), nullable=False)
    weight = db.Column(Integer, nullable=False)

    # relationships
    person_type = db.relationship('PersonType', backref='profiles')

    # properties
    @hybrid_property
    def name(self):
        return self.person_type.name

    # api create/update methods
    #

    def duplicate(self, analysis_id):
        profile = Profile(analysis_id=analysis_id,
                          person_type_id=self.person_type_id,
                          weight=self.weight)
        db.session.add(profile)
        db.session.flush()
        return profile
