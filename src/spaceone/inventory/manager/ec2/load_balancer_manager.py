from spaceone.core.manager import BaseManager
from spaceone.inventory.model.load_balancer import LoadBalancer
from spaceone.inventory.connector.ec2_connector import EC2Connector


class LoadBalancerManager(BaseManager):

    def __init__(self, params, ec2_connector=None, **kwargs):
        self.params = params
        self.ec2_connector: EC2Connector = ec2_connector

    def get_load_balancer_info(self, load_balancers, target_groups, instance_id=None, instance_ip=None):
        '''
        load_balancer_data_list = [{
                "endpoint": "",
                "type": "network" | "application"
                "arn": "",
                "scheme": 'internet-facing'|'internal,
                "name": "",
                "port": [
                    50051
                ],
                "protocol": [
                    "TCP"
                ],
                 "tags": {
                    "arn": ""
                 },
            },
            ...
        ]
        '''
        load_balancer_data_list = []
        match_load_balancers = self.get_load_balancers_from_instance_id(instance_id, instance_ip,
                                                                        load_balancers, target_groups)

        for match_load_balancer in match_load_balancers:
            load_balancer_data = {
                'endpoint': match_load_balancer.get('DNSName', ''),
                'type': match_load_balancer.get('Type'),
                'scheme': match_load_balancer.get('Scheme'),
                'name': match_load_balancer.get('LoadBalancerName', ''),
                'protocol': [listener.get('Protocol') for listener in match_load_balancer.get('listeners', []) if listener.get('Protocol') is not None],
                'port': [listener.get('Port') for listener in match_load_balancer.get('listeners', []) if listener.get('Port') is not None],
                'tags': {
                    'arn': match_load_balancer.get('LoadBalancerArn'),
                }
            }

            load_balancer_data_list.append(LoadBalancer(load_balancer_data, strict=False))

        return load_balancer_data_list

    def get_load_balancers_from_instance_id(self, instance_id, instance_ip, load_balancers, target_groups):
        matched_lb_arns = []
        match_load_balancers = []
        match_target_groups = self.match_target_groups(target_groups, instance_id, instance_ip)

        for match_tg in match_target_groups:
            for lb in self.match_load_balancers(load_balancers, match_tg.get('LoadBalancerArns', [])):
                if lb.get('LoadBalancerArn') not in matched_lb_arns:
                    match_load_balancers.append(lb)
                    matched_lb_arns.append(lb.get('LoadBalancerArn'))

        return match_load_balancers

    def set_listeners_into_load_balancers(self, load_balancers):
        for lb in load_balancers:
            lb_arn = lb.get('LoadBalancerArn', '')
            listeners = self.ec2_connector.list_listeners(lb_arn)
            lb.update({
                'listeners': listeners
            })

    @staticmethod
    def match_target_groups(target_groups, instance_id, instance_ip):
        match_target_groups = []

        for target_group in target_groups:
            target_group_arn = target_group.get('TargetGroupArn')
            target_type = target_group.get('TargetType')  # instance | ip | lambda

            for th in target_group.get('target_healths'):
                target = th.get('Target', {})
                target_id = target.get('Id')

                if target_id is not None and target_id not in match_target_groups:
                    if target_type == 'instance' and instance_id == target_id:
                        match_target_groups.append(target_group)
                    elif target_type == 'ip' and instance_ip == target_id:
                        match_target_groups.append(target_group)

        return match_target_groups

    @staticmethod
    def match_load_balancers(load_balancers, lb_arns):
        match_load_balancers = []

        for lb_arn in lb_arns:
            for lb in load_balancers:
                if lb.get('LoadBalancerArn') == lb_arn:
                    match_load_balancers.append(lb)

        return match_load_balancers

