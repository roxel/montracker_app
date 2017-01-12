from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(database, app):
    database.init_app(app)


def setup_db(database_session):
    from app.processor.models import ModelType, PersonType, ActionStatus, ModelStatus
    from app.auth.models import User

    def _get_or_create(model, instance, **kwargs):
        obj = db.session.query(model).filter_by(**kwargs).first() or None
        if not obj:
            db.session.add(instance)

    model_types = [
        ModelType(name='HorDistIPP', active=True, complex=False),
        ModelType(name='ElevChgIPP', active=True, complex=False),
        ModelType(name='HorChgIPP', active=True, complex=False),
        ModelType(name='DispAngle', active=True, complex=False),
        ModelType(name='TrackOffset', active=True, complex=False),
        ModelType(name='FindLocation', active=True, complex=False),
        ModelType(name='Mobility', active=True, complex=False),
        ModelType(name='CombProb', active=True, complex=True),
        ModelType(name='SearchSeg', active=True, complex=True)
    ]
    person_types = [
        PersonType(name='tourist', active=True),
        PersonType(name='hunter', active=True),
        PersonType(name='fisherman', active=True),
        PersonType(name='atv', active=True),
        PersonType(name='autistic', active=True),
        PersonType(name='child_1_3', active=True),
        PersonType(name='child_4_6', active=True),
        PersonType(name='child_7_9', active=True),
        PersonType(name='child_10_12', active=True),
        PersonType(name='child_13_15', active=True),
        PersonType(name='climber', active=True),
        PersonType(name='dementia', active=True),
        PersonType(name='depressed', active=True),
        PersonType(name='collector', active=True),
        PersonType(name='horseman', active=True),
        PersonType(name='mentally_ill', active=True),
        PersonType(name='mentally_disabled', active=True),
        PersonType(name='mountain_cyclist', active=True),
        PersonType(name='extreme_sports', active=True),
        PersonType(name='motorcyclist', active=True),
        PersonType(name='runner', active=True),
        PersonType(name='alpine_skier', active=True),
        PersonType(name='classic_skier', active=True),
        PersonType(name='snowboarder', active=True),
        PersonType(name='snowmobile', active=True),
        PersonType(name='psychoactive', active=True),
        PersonType(name='vehicle', active=True),
        PersonType(name='manual_worker', active=True),
    ]
    model_statuses = [ModelStatus(name=name) for name in ModelStatus.names()]

    demo_user = User(login='demo', password='demo')
    for item in model_types:
        _get_or_create(ModelType, item, name=item.name)
    for item in person_types:
        _get_or_create(PersonType, item, name=item.name)
    for item in model_statuses:
        _get_or_create(ModelStatus, item, name=item.name)
    _get_or_create(User, demo_user, login=demo_user.login)
    database_session.commit()
