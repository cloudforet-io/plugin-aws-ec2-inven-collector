from schematics import Model
from schematics.types import StringType


class VPC(Model):
    vpc_arn = StringType()
    vpc_id = StringType()
    cidr = StringType()
    vpc_name = StringType(default="")
