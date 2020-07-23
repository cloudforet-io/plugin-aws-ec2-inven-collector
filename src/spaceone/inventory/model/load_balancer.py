from schematics import Model
from schematics.types import StringType, IntType, DictType, ListType


class LoadBalancer(Model):
    type = StringType(choices=('application', 'network'))
    dns = StringType()
    port = ListType(IntType())
    name = StringType()
    protocol = ListType(StringType())
    scheme = StringType(choices=('internet-facing', 'internal'))
    arn = StringType()
    tags = DictType(StringType, default={})
