from schematics import Model
from schematics.types import StringType


class Subnet(Model):
    subnet_arn = StringType()
    vpc_id = StringType()
    subnet_id = StringType()
    cidr = StringType()
    subnet_name = StringType()
