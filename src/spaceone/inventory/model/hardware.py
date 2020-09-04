from schematics import Model
from schematics.types import IntType, FloatType, StringType, ListType, BooleanType, DateType


class Hardware(Model):
    core = IntType(default=0)
    memory = FloatType(default=0.0)
    # manufacturer = StringType()
    # model = StringType()
    # serial_num = StringType()
    # cpu_model = ListType(StringType())
    # threads_per_core = StringType()
    # core_per_socket = IntType()
    # cpu_socket = IntType()
    # cpu_arch = StringType()
    # hyperthreading = BooleanType()
    # bios_version = StringType()
    # bios_release_at = DateType()
    # is_vm = BooleanType()
    # memory_count = IntType()
