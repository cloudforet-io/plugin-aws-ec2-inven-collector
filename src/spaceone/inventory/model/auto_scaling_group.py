from schematics import Model
from schematics.types import StringType


class AutoScalingGroup(Model):
    arn = StringType()
    launch_template_name = StringType()
    name = StringType()
