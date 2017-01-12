import datetime

from app.processor.models import Action, Analysis, ModelType, Model, Profile, PersonType


def add_simple_action(session):
    action = Action(name='Example', lost_time=datetime.datetime.now())
    session.add(action)
    session.flush()
    return action


def add_analysis_with_coordinates(session, action_id):
    analysis = Analysis(name='Some basic analysis', action_id=action_id,
                        ipp_longitude=80, ipp_latitude=70, rp_latitude=30, rp_longitude=80)
    session.add(analysis)
    session.flush()
    return analysis


def add_simple_model(session, analysis_id):
    model_type = ModelType.query.filter_by(complex=False).first()
    model = Model(analysis_id=analysis_id, model_type_id=model_type.id)
    session.add(model)
    session.flush()
    return model


def add_complex_model_comb(session, analysis_id):
    model_type = ModelType.query.filter_by(name='CombProb').first()
    model = Model(analysis_id=analysis_id, model_type_id=model_type.id)
    session.add(model)
    session.flush()
    return model


def add_complex_model_seg(session, analysis_id):
    model_type = ModelType.query.filter_by(name='SearchSeg').first()
    model = Model(analysis_id=analysis_id, model_type_id=model_type.id)
    session.add(model)
    session.flush()
    return model


def add_complete_analysis(session, action_id):

    # add analysis
    analysis = Analysis(name='Some basic analysis', action_id=action_id,
                        ipp_longitude=80, ipp_latitude=70, rp_latitude=30, rp_longitude=80)
    session.add(analysis)

    # add comb model
    model_type = ModelType.query.filter_by(name='CombProb').first()
    comb_model = Model(analysis_id=analysis.id, model_type_id=model_type.id)
    session.add(comb_model)
    session.flush()

    # add search seg model
    model_type = ModelType.query.filter_by(name='SearchSeg').first()
    seg_model = Model(analysis_id=analysis.id, model_type_id=model_type.id)
    session.add(seg_model)
    session.flush()

    # add simple models
    model_type_names = ['HorDistIPP', 'ElevChgIPP', 'HorChgIPP', 'DispAngle',
                        'TrackOffset', 'FindLocation', 'Mobility']
    for mtn in model_type_names:
        model_type = ModelType.query.filter_by(name=mtn).first()
        model = Model(analysis_id=analysis.id, model_type_id=model_type.id)
        session.add(model)
        session.flush()
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
    session.add(tourist)
    session.add(climber)
    session.flush()

    return analysis


def add_simple_models_analysis(session, action_id):

    # add analysis
    analysis = Analysis(name='Some basic analysis', action_id=action_id,
                        ipp_longitude=80, ipp_latitude=70, rp_latitude=30, rp_longitude=80)
    session.add(analysis)

    # add simple models
    model_type_names = ['HorDistIPP', 'ElevChgIPP', 'HorChgIPP', 'DispAngle',
                        'TrackOffset', 'FindLocation', 'Mobility']
    for mtn in model_type_names:
        model_type = ModelType.query.filter_by(name=mtn).first()
        model = Model(analysis_id=analysis.id, model_type_id=model_type.id)
        session.add(model)
        session.flush()
        model.create_weights(1, model.id)

    # add chosen profiles
    person_type_tourist = PersonType.query.filter_by(name='tourist').first()
    person_type_climber = PersonType.query.filter_by(name='climber').first()

    weight_tourist, weight_climber = 3, 7

    tourist = Profile(analysis_id=analysis.id, person_type_id=person_type_tourist.id,
                      weight=weight_tourist)
    climber = Profile(analysis_id=analysis.id, person_type_id=person_type_climber.id,
                      weight=weight_climber)
    session.add(tourist)
    session.add(climber)
    session.flush()

    return analysis


def add_complex_models_analysis(session, action_id):

    analysis = add_simple_models_analysis(session, action_id)

    # add complex models
    model_type_names = ['CombProb', 'SearchSeg']
    for mtn in model_type_names:
        model_type = ModelType.query.filter_by(name=mtn).first()
        analysis.create_model(model_type.id, None)

    return analysis








