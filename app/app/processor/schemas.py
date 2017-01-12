from marshmallow import Schema, fields, validate
from app.processor.fields import TimestampField, LayerURLField, IntegerListField, LatitudeField, LongitudeField, \
    ModelTypeField, PersonTypeField


class ModelBaseSchema(Schema):

    # required on creation/update
    model_type_id = ModelTypeField(required=True)
    weight = fields.Integer(required=True, allow_none=True)


class ModelSchema(ModelBaseSchema):

    # parent key
    analysis_id = fields.Integer(required=True)

    # dump only state fields
    id = fields.Integer(allow_none=False, dump_only=True)
    model_status_id = fields.Integer(allow_none=False, dump_only=True)
    layers = fields.List(LayerURLField, dump_only=True, attribute='layer_urls')


class ModelNestedSchema(ModelSchema):
    analysis_id = fields.Integer(required=False, load_only=True)


class ProfileBaseSchema(Schema):

    # required on creation/update
    person_type_id = PersonTypeField(required=True)
    weight = fields.Integer(required=True, allow_none=False)


class ProfileSchema(ProfileBaseSchema):

    # parent key
    analysis_id = fields.Integer(required=True)

    # dump only state fields
    id = fields.Integer(dump_only=True)


class ProfileNestedSchema(ProfileSchema):
    analysis_id = fields.Integer(required=False, load_only=True)


class AnalysisBaseSchema(Schema):

    # required on creation/update
    name = fields.String(required=True, validate=validate.Length(max=256))

    # optional on creation/update
    ipp_latitude = LatitudeField(allow_none=True)
    ipp_longitude = LongitudeField(allow_none=True)
    rp_latitude = LatitudeField(allow_none=True)
    rp_longitude = LongitudeField(allow_none=True)
    lost_time = TimestampField(allow_none=True)
    description = fields.String(allow_none=True)

    # parent key
    action_id = fields.Integer(required=True)

    # dump only state fields
    id = fields.Integer(dump_only=True)
    creation_time = TimestampField(dump_only=True)
    analysis_status_id = fields.Integer(dump_only=True)

    # post/get nested fields – used on all request but used only for nested objects creation
    models = fields.List(fields.Nested(ModelNestedSchema))
    profiles = fields.List(fields.Nested(ProfileNestedSchema))


class AnalysisSchema(AnalysisBaseSchema):

    # parent key
    action_name = fields.String(dump_only=True)

    # load only action fields
    deleted = fields.Boolean(allow_none=True, load_only=True)
    analysis_id = fields.Boolean(allow_none=True, load_only=True)


class AnalysisNestedSchema(AnalysisBaseSchema):
    action_id = fields.Integer(required=False, load_only=True)


class AnalysisExecutionSchema(Schema):
    started = fields.Boolean(load_only=True)


class ActionBaseSchema(Schema):
    # required on creation/update
    name = fields.String(required=True, validate=validate.Length(max=256, min=1))
    lost_time = TimestampField(required=True)

    # optional on creation/update
    ipp_latitude = LatitudeField(allow_none=True)
    ipp_longitude = LongitudeField(allow_none=True)
    rp_latitude = LatitudeField(allow_none=True)
    rp_longitude = LongitudeField(allow_none=True)
    action_status_id = fields.Integer(required=False, dump_only=True)
    description = fields.String(allow_none=True)

    # dump only state fields
    id = fields.Integer(dump_only=True)
    creation_time = TimestampField(dump_only=True)

    # load only action fields
    deleted = fields.Boolean(allow_none=True, load_only=True)

    # ignored fields
    # user_id = fields.Integer(allow_none=True, dump_only=True)

    # post/get nested fields – used on all request but used only for nested objects creation
    analyses = fields.List(fields.Nested(AnalysisNestedSchema))


class ActionSchema(ActionBaseSchema):
    archived = fields.Boolean(allow_none=True)


class AnalysisActionListSchema(Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String(dump_only=True)
    analysis_status_id = fields.Integer(dump_only=True)
    creation_time = TimestampField(dump_only=True)
    models = fields.List(fields.Nested(ModelNestedSchema), dump_only=True)


class ActionListSchema(Schema):
    name = fields.String(dump_only=True)
    lost_time = TimestampField(allow_none=True, dump_only=True)
    action_status_id = fields.Integer(dump_only=True)
    id = fields.Integer(dump_only=True)
    creation_time = TimestampField(dump_only=True)
    archived = fields.Boolean(allow_none=True, dump_only=True)
    # analyses = fields.List(fields.Nested(AnalysisActionListSchema), dump_only=True)


class BaseQuerySchema(Schema):
    per_page = fields.Integer()
    page_ts = TimestampField()
    created_from = TimestampField()
    created_to = TimestampField()
    lost_from = TimestampField()
    lost_to = TimestampField()


class ActionQuerySchema(BaseQuerySchema):
    status = IntegerListField()
    archived = fields.Boolean()
    name = fields.String()


class AnalysisQuerySchema(BaseQuerySchema):
    status = IntegerListField()
    query = fields.String()







