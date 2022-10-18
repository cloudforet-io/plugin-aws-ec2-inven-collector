from schematics import Model
from schematics.types import ModelType, StringType, BooleanType


class AWSIAMInstanceProfile(Model):
    id = StringType(deserialize_from='Id')
    arn = StringType(deserialize_from='Arn')


class AWS(Model):
    ami_id = StringType()
    ebs_optimized = BooleanType()
    iam_instance_profile = ModelType(AWSIAMInstanceProfile, serialize_when_none=False)
    termination_protection = BooleanType(serialize_when_none=False)
    lifecycle = StringType(choices=('spot', 'scheduled'), serialize_when_none=False)
