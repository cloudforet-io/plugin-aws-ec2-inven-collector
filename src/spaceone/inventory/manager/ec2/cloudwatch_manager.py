from spaceone.core.manager import BaseManager
from spaceone.inventory.model.cloudwatch import CloudWatch, CloudWatchMetricInfo, CloudWatchDimension


class CloudWatchManager(BaseManager):

    def set_cloudwatch_info(self, instance_id, region_name):
        '''
        data.cloudwatch: {
            "metrics_info": [
                {
                    "Namespace": "AWS/EC2",
                    "Dimensions": [
                        {
                            "Name": "InstanceId",
                            "Value": "i-xxxxxx"
                        }
                    ]
                },
                {
                    "Namespace": "CWAgent",
                    "Dimensions": [
                        {
                            "Name": "InstanceId",
                            "Value": "i-xxxxxx"
                        }
                    ]
                }
            ]
            "region_name": region_name
        }
        '''

        cloudwatch_data = {
            'region_name': region_name,
            'metrics_info': self.set_metrics_info(instance_id)
        }

        return CloudWatch(cloudwatch_data, strict=False)

    def set_metrics_info(self, instance_id):
        return [
            CloudWatchMetricInfo({
                'Namespace': 'AWS/EC2',
                'Dimensions': self.set_dimensions(instance_id)
            }, strict=False),
            CloudWatchMetricInfo({
                'Namespace': 'CWAgent',
                'Dimensions': self.set_dimensions(instance_id)
            }, strict=False)
        ]

    @staticmethod
    def set_dimensions(instance_id):
        dimension = {
            'Name': 'InstanceId',
            'Value': instance_id
        }

        return [CloudWatchDimension(dimension, strict=False)]
