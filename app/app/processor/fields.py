import datetime

from app.database import db
from app.processor.models import ModelType, PersonType
from flask import current_app
from marshmallow import fields, ValidationError


class TimestampField(fields.Integer):

    default_error_messages = {
        'invalid': 'Not a valid timestamp integer.'
    }

    def _validated(self, value):
        value = super(TimestampField, self)._validated(value)
        if value < 0:
            self.fail('invalid')
        return value

    def _serialize(self, value, attr, obj):
        return int(value.timestamp())

    def _deserialize(self, value, attr, data):
        value = self._validated(value)
        return datetime.datetime.fromtimestamp(int(value)).strftime('%Y-%m-%d %H:%M:%S')


class LatitudeField(fields.Float):

    default_error_messages = {
        'invalid': 'Out of range latitude value'
    }

    def _validated(self, value):
        value = super(LatitudeField, self)._validated(value)
        if value and (value < -90 or value > 90):
            self.fail('invalid')
        return value


class LongitudeField(fields.Float):

    default_error_messages = {
        'invalid': 'Out of range longitude value'
    }

    def _validated(self, value):
        value = super(LongitudeField, self)._validated(value)
        if value and (value < -180 or value > 180):
            self.fail('invalid')
        return value


class LayerURLField(fields.String):

    def _serialize(self, value, attr, obj):
        prefix = current_app.config['ARCGIS_PATH_PREFIX'].strip("/")
        suffix = current_app.config['ARCGIS_PATH_SUFFIX'].strip("/")
        return '{}/{}/{}'.format(prefix, value.strip("/"), suffix)


class ModelTypeField(fields.Integer):

    default_error_messages = {
        'invalid_id': 'Model type id not present in model types options.',
    }

    def _validated(self, value):
        value = super(ModelTypeField, self)._validated(value)
        model_type = ModelType.valid().filter(ModelType.id == value).first()
        if model_type is None:
            self.fail('invalid_id')
        return value


class PersonTypeField(fields.Integer):

    default_error_messages = {
        'invalid_id': 'Person type id not present in person types options.'
    }

    def _validated(self, value):
        value = super(PersonTypeField, self)._validated(value)
        person_type = PersonType.valid().filter(PersonType.id == value).first()
        if person_type is None:
            self.fail('invalid_id')
        return value


class IntegerListField(fields.String):

    default_error_messages = {
        'invalid': 'Not an integer list.'
    }

    def _deserialize(self, value, attr, data):
        try:
            result = [int(i) for i in value.split(',')]
        except (ValueError, TypeError):
            raise ValidationError(self.default_error_messages.get('invalid'))
        return result

