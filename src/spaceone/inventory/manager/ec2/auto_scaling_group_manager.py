from spaceone.core.manager import BaseManager
from spaceone.inventory.model.auto_scaling_group import AutoScalingGroup


class AutoScalingGroupManager(BaseManager):

    def __init__(self, params, ec2_connector=None):
        self.params = params
        self.ec2_connector = ec2_connector

    def get_auto_scaling_info(self, instance_id, auto_scaling_groups, launch_configurations):
        '''
        auto_scaling_group_data = {
            'name': ''
            'arn': '',
            'launch_configuration': {
                'arn': '',
                'name': ''
            },
            'launch_template': {
                'launch_template_id': '',
                'name': ''
                'version': ''
            }
        }
        '''

        auto_scaling_group_data = {}
        match_autoscaling_group, match_launch_configuration = \
            self.get_auto_scaling_group_from_instance_id(instance_id, auto_scaling_groups, launch_configurations)

        if match_autoscaling_group is not None:
            auto_scaling_group_data = {
                'name': match_autoscaling_group.get('AutoScalingGroupName', ''),
                'arn': match_autoscaling_group.get('AutoScalingGroupARN', ''),
            }

            if match_launch_configuration is not None:
                auto_scaling_group_data.update({
                    'launch_configuration': {
                        'name': match_launch_configuration.get('LaunchConfigurationName', ''),
                        'arn': match_launch_configuration.get('LaunchConfigurationARN', '')
                    }
                })

            if 'LaunchTemplate' in match_autoscaling_group:
                auto_scaling_group_data.update({
                    'launch_template': match_autoscaling_group.get('LaunchTemplate')
                })

            return AutoScalingGroup(auto_scaling_group_data, strict=False)
        else:
            return None

    @staticmethod
    def get_auto_scaling_group_from_instance_id(instance_id, auto_scaling_groups, launch_configurations):
        match_auto_scaling_group = None
        match_launch_configuration = None
        match_lc_name = None

        for asg in auto_scaling_groups:
            instances = asg.get('Instances', [])

            for instance in instances:
                if instance_id == instance.get('InstanceId'):
                    match_auto_scaling_group = asg
                    match_lc_name = asg.get('LaunchConfigurationName')

                    break

        for lc in launch_configurations:
            if lc.get('LaunchConfigurationName') == match_lc_name:
                match_launch_configuration = lc
                break

        return match_auto_scaling_group, match_launch_configuration
