from schematics import Model
from schematics.types import StringType, ListType


class OS(Model):
    # os_details = StringType()
    os_distro = StringType()
    os_arch = StringType()
    # os_license = ListType(StringType())
    # kernel = StringType()
