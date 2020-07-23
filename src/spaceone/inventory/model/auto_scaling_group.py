from schematics import Model
from schematics.types import StringType, ModelType


class LaunchConfiguration(Model):
    arn = StringType()
    name = StringType()


class LaunchTemplate(Model):
    launch_template_id = StringType(deserialize_from='LaunchTemplateId')
    name = StringType(deserialize_from='LaunchTemplateName')
    version = StringType(deserialize_from='Version')


class AutoScalingGroup(Model):
    arn = StringType()
    name = StringType()
    launch_configuration = ModelType(LaunchConfiguration, serialize_when_none=False)
    launch_template = ModelType(LaunchTemplate, serialize_when_none=False)
