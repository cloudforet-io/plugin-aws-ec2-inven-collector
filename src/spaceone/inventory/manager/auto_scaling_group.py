class AutoScalingGroup:
    def __init__(self, params):
        self.params = params

    def get_auto_scaling_info(self):
        auto_scaling_group_info ={
            'auto_scaling_group': {}
        }
        auto_scaling_desc = self.resources.get('client_autoscaling').describe_auto_scaling_groups(**{})
        auto_scaling_groups = _.get(auto_scaling_desc, 'AutoScalingGroups', None)

        if auto_scaling_groups:
            for auto_scaling_group in auto_scaling_groups:
                if "Instances" in auto_scaling_group.keys():
                    for asg_instances in auto_scaling_group["Instances"]:
                        if asg_instances["InstanceId"] == self.instance_id:
                            if 'AutoScalingGroupName' in auto_scaling_group:
                                auto_scaling_group_info['auto_scaling_group']["name"] = auto_scaling_group["AutoScalingGroupName"]
                            if 'AutoScalingGroupARN' in auto_scaling_group:
                                auto_scaling_group_info['auto_scaling_group']["arn"] = auto_scaling_group["AutoScalingGroupARN"]

                            if "LaunchConfigurationName" in auto_scaling_group.keys() and 'LaunchConfigurationName' in auto_scaling_group:
                                    auto_scaling_group_info['auto_scaling_group']["launch_configuration_name"] = auto_scaling_group["LaunchConfigurationName"]
                                    extract_key = f'{auto_scaling_group["LaunchConfigurationName"]}.LaunchConfigurationARN'
                                    launch_configuration = _.get(self.au_dic.get('launch_configuration_dic'), extract_key, None)

                                    if launch_configuration:
                                        auto_scaling_group_info['auto_scaling_group']["launch_configuration_arn"] = launch_configuration

                            if "LaunchTemplate" in auto_scaling_group.keys() and 'LaunchTemplate' in auto_scaling_group:
                                    auto_scaling_group_info['auto_scaling_group']["launch_template_name"] = auto_scaling_group["LaunchTemplate"].get('LaunchTemplateName', '')

                                    extract_key = f'{auto_scaling_group["LaunchTemplate"]}.LaunchTemplateName'
                                    launch_template = _.get(self.au_dic.get('launch_template_dic'), extract_key, None)

                                    if launch_template and 'CreatedBy' in launch_template:
                                        auto_scaling_group_info['auto_scaling_group']["launch_template_arn"] = launch_template.get('CreatedBy','')
        return auto_scaling_group_info