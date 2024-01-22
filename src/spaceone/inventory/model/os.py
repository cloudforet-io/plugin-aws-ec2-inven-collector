from schematics import Model
from schematics.types import StringType


class OS(Model):
    os_distro = StringType()
    os_arch = StringType()
    details = StringType(default="")
    os_type = StringType(choices=('LINUX', 'WINDOWS'))
    # os_details = StringType(choices=('Linux/UNIX', 'Red Hat BYOL Linux', 'Red Hat Enterprise Linux', 'Red Hat Enterprise Linux with HA', 'Red Hat Enterprise Linux with SQL Server Standard and HA', 'Red Hat Enterprise Linux with SQL Server Enterprise and HA', 'Red Hat Enterprise Linux with SQL Server Standard', 'Red Hat Enterprise Linux with SQL Server Web', 'Red Hat Enterprise Linux with SQL Server Enterprise', 'SQL Server Enterprise', 'SQL Server Standard', 'SQL Server Web', 'SUSE Linux', 'Ubuntu Pro', 'Windows', 'Windows BYOL', 'Windows with SQL Server Enterprise', 'Windows with SQL Server Standard', 'Windows with SQL Server Web'))
    os_details = StringType()
