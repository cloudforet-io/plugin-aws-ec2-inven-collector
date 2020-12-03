from schematics import Model
from schematics.types import ModelType, StringType, BooleanType, ListType


class Tags(Model):
    key = StringType(deserialize_from='Key')
    value = StringType(deserialize_from='Value')


class AWSIAMInstanceProfile(Model):
    id = StringType(deserialize_from='Id')
    arn = StringType(deserialize_from='Arn')


class AWS(Model):
    ebs_optimized = BooleanType()
    iam_instance_profile = ModelType(AWSIAMInstanceProfile, serialize_when_none=False)
    termination_protection = BooleanType(serialize_when_none=False)
    lifecycle = StringType(choices=('spot', 'scheduled'), serialize_when_none=False)
    tags = ListType(ModelType(Tags))
