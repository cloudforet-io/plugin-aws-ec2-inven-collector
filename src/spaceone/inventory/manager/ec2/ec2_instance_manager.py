from spaceone.core.manager import BaseManager
from spaceone.inventory.model.compute import Compute
from spaceone.inventory.model.aws import AWS
from spaceone.inventory.model.os import OS
from spaceone.inventory.model.hardware import Hardware
from spaceone.inventory.connector.ec2_connector import EC2Connector

class EC2InstanceManager(BaseManager):

    def __init__(self, params, ec2_connector=None):
        self.params = params
        self.ec2_connector: EC2Connector = ec2_connector

    def get_server_info(self, instance, itypes, images, eips):
        '''
        server_data = {
            "os_type": "LINUX" | "WINDOWS"
            "name": ''
            "ip_addresses": []
            "data":  {
                "os": {
                    "details": "",
                    "os_distro": "",
                    "os_arch": "",
                },
                "aws": {
                    "ebs_optimized": "",
                    "iam_instance_profile": {
                        "id": "",
                        "arn": ""
                    },
                    "lifecycle": "spot" | "scheduled",
                    "tags": {},
                },
                "hardware": {
                    "core": 0,
                    "memory": 0
                },
                "public_ip_address": "",
                "compute": {
                    "eip": [],
                    "keypair": "",
                    "availability_zone": "",
                    "instance_state": "",
                    "instance_type": "",
                    "launched_at": "datetime",
                    "region_name": "",
                    "instance_id": "",
                    "instance_name": "",
                    "security_groups": [],
                    "image": "",
                    "account_id": "",
                },
                "public_dns": ""
            }
        }
        '''

        match_image = self.match_image(instance.get('ImageId'), images)

        server_dic = self.get_server_dic(instance)
        os_data = self.get_os_data(instance, match_image, self.get_os_type(instance))
        aws_data = self.get_aws_data(instance)
        hardware_data = self.get_hardware_data(instance, itypes)
        compute_data = self.get_compute_data(instance, match_image, eips)

        server_dic.update({
            'data': {
                'os': os_data,
                'aws': aws_data,
                'hardware': hardware_data,
                'compute': compute_data,
                'public_dns': instance.get('PublicDnsName', ''),
                'public_ip_address': instance.get('PublicIpAddress', '')
            }
        })

        return server_dic

    def get_server_dic(self, instance):
        server_data = {
            'name': self.generate_name(instance),
            'os_type': self.get_os_type(instance)
        }

        return server_data

    def get_os_data(self, instance, image, os_type):
        os_data = {
            'details': image.get('Description', ''),
            'os_distro': self.get_os_distro(image.get('Name', ''), os_type),
            'os_arch': image.get('Architecture', '')
        }

        return OS(os_data, strict=False)

    def get_aws_data(self, instance):
        aws_data = {
            'ebs_optimized': instance.get('EbsOptimized', False),
            'iam_instance_profile': instance.get('IamInstanceProfile'),
            'lifecycle': instance.get('InstanceLifecycle', 'scheduled'),
            'tags': instance.get('Tags', [])
        }

        return AWS(aws_data, strict=False)

    def get_hardware_data(self, instance, itypes):
        hardware_data = {}
        itype = self.match_instance_type(instance.get('InstanceType'), itypes)

        if itype is not None:
            hardware_data = {
                'core': itype.get('VCpuInfo', {}).get('DefaultVCpus', 0),
                'memory': round(float((itype.get('MemoryInfo', {}).get('SizeInMiB', 0))/1024), 2)  # 2.0
            }

        return Hardware(hardware_data, strict=False)

    def get_compute_data(self, instance, image, eips):
        compute_data = {
            'eip': self.match_eips_from_instance_id(instance.get('InstanceId'), eips),
            'keypair': instance.get('KeyName', ''),
            'az': instance.get('Placement', {}).get('AvailabilityZone', ''),
            'instance_state': instance.get('State', {}).get('Name'),
            'termination_protection': self.get_termination_protection(instance.get('InstanceId')),
            'instance_type': instance.get('InstanceType', ''),
            'launched_at': instance.get('LaunchTime'),
            'region_name': self.params['region_name'],
            'instance_id': instance.get('InstanceId'),
            'instance_name': self.generate_name(instance),
            'security_groups': [sg.get('GroupName') for sg in instance.get('SecurityGroups', []) if sg.get('GroupName') is not None],
            'account_id': '',
            'image': image.get('Name', '')
        }

        return Compute(compute_data)

    def get_termination_protection(self, instance_id):
        return self.ec2_connector.list_instance_attribute(instance_id)

    def get_os_distro(self, image_name, os_type):
        if image_name == '':
            return os_type.lower()
        else:
            return self.extract_os_distro(image_name, os_type)

    def match_image(self, image_id, images):
        for image in images:
            if image.get('ImageId') == image_id:
                return image

        return {}

    @staticmethod
    def match_eips_from_instance_id(instance_id, eips):
        return [eip.get('PublicIp') for eip in eips if instance_id == eip.get('InstanceId', '')]

    @staticmethod
    def match_instance_type(instance_type, itypes):
        for itype in itypes:
            if itype.get('InstanceType') == instance_type:
                return itype

        return None

    @staticmethod
    def generate_name(resource):
        for resource_tag in resource.get('Tags', []):
            if resource_tag['Key'] == "Name":
                return resource_tag["Value"]

        return ''

    @staticmethod
    def get_os_type(instance):
        return instance.get('Platform', 'LINUX').upper()

    @staticmethod
    def extract_os_distro(image_name, os_type):
        if os_type == 'LINUX':
            os_map = {
                'suse': 'suse',
                'rhel': 'redhat',
                'cetnos': 'centos',
                'fedora': 'fedora',
                'ubuntu': 'ubuntu',
                'debian': 'debia',
                'amazon': 'amazonlinux',
                'amzn': 'amazonlinux'
            }

            image_name.lower()
            for key in os_map:
                if key in image_name:
                    return os_map[key]

            return 'linux'

        elif os_type == 'WINDOWS':
            os_distro_string = None
            image_splits = image_name.split('-')

            version_cmps = ['2016', '2019', '2012']

            for version_cmp in version_cmps:
                if version_cmp in image_splits:
                    os_distro_string = f'win{version_cmp}'

            if os_distro_string is not None and 'R2_RTM' in image_splits:
                os_distro_string = f'{os_distro_string}r2'

            if os_distro_string is None:
                os_distro_string = 'windows'

            return os_distro_string


