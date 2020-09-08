from spaceone.core.manager import BaseManager
from spaceone.inventory.model.cloudwatch import CloudWatch, CloudWatchDemension


class CloudWatchManager(BaseManager):

    def __init__(self, params, ec2_connector=None):
        self.params = params
        self.ec2_connector = ec2_connector

    def get_cloudwatch_info(self, instance_id, region_name):
        '''
        cloudwatch_data = {
            "namespace": "AWS/EC2",
            "dimensions": [
                {
                    "Name": "InstanceId",
                    "Value": instacne_id
                }
            ],
            "region_name": region_name
        }
        '''

        cloudwatch_data = {
            'namespace': 'AWS/EC2',
            'region_name': region_name,
            'dimensions': self.get_dimensions(instance_id)
        }

        return CloudWatch(cloudwatch_data, strict=False)

    @staticmethod
    def get_dimensions(instance_id):
        '''
        "dimensions": [
            {
                "Name": "InstanceId",
                "Value": instacne_id
            }
        ]
        '''

        dimension = {
            'name': 'InstanceId',
            'value': instance_id
        }

        return [CloudWatchDemension(dimension, strict=False)]