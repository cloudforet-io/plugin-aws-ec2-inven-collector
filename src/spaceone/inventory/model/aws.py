from schematics import Model
from schematics.types import ModelType, StringType, BooleanType, ListType


class Tags(Model):
    Key = StringType()
    Value = StringType()


class AWSIAMInstanceProfile(Model):
    id = StringType(deserialize_from='Id')
    arn = StringType(deserialize_from='Arn')


class AWS(Model):
    ebs_optimized = BooleanType()
    iam_instance_profile = ModelType(AWSIAMInstanceProfile)
    lifecycle = StringType(choices=('spot', 'scheduled'), serialize_when_none=False)
    tags = ListType(ModelType(Tags))
