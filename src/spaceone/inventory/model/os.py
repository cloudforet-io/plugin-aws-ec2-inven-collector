from schematics import Model
from schematics.types import StringType


class OS(Model):
    details = StringType()
    os_distro = StringType()
    os_arch = StringType()
