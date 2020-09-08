from spaceone.core.manager import BaseManager
from spaceone.inventory.model.security_group import SecurityGroup


class SecurityGroupManager(BaseManager):

    def __init__(self, params, ec2_connector=None):
        self.params = params
        self.ec2_connector = ec2_connector

    def get_security_group_info(self, security_group_ids, security_groups):
        '''
        "data.security_group" = [
                    {
                        "protocol": "",
                        "security_group_name": "",
                        "port_range_min": 0,
                        "port_range_max": 65535,
                        "security_group_id": "",
                        "description": "",
                        "direction": "inbound" | "outbound",
                        "port": "",
                        "remote": "",
                        "remote_id": "",
                        "remote_cidr": "",
                    }
                ],
        '''

        sg = []
        match_security_groups = self.match_security_group_from_ids(security_group_ids, security_groups)

        for match_sg in match_security_groups:
            # INBOUND
            for inbound_rule in match_sg.get('IpPermissions', []):
                sg_data = self.set_sg_base_data(match_sg, 'inbound', inbound_rule)

                for ip_range in inbound_rule.get('IpRanges', []):
                    sg_data.update(self.set_ip_range_data(ip_range))
                    sg.append(SecurityGroup(sg_data, strict=False))

                for group_pair in inbound_rule.get('UserIdGroupPairs', []):
                    sg_data.update(self.set_group_pairs_data(group_pair))
                    sg.append(SecurityGroup(sg_data, strict=False))

            # OUTBOUND
            for outbound_rules in match_sg.get('IpPermissionsEgress', []):
                sg_data = self.set_sg_base_data(match_sg, 'outbound', outbound_rules)

                for ip_range in outbound_rules.get('IpRanges', []):
                    sg_data.update(self.set_ip_range_data(ip_range))
                    sg.append(SecurityGroup(sg_data, strict=False))

                for group_pair in outbound_rules.get('UserIdGroupPairs', []):
                    sg_data.update(self.set_group_pairs_data(group_pair))
                    sg.append(SecurityGroup(sg_data, strict=False))

        return sg

    def set_sg_base_data(self, sg, direction, rule):
        sg_data = {
            'direction': direction,
            'protocol': self._get_protocol(rule.get('IpProtocol')),
            'security_group_name': sg.get('GroupName', ''),
            'security_group_id': sg.get('GroupId'),
        }

        from_port, to_port, port = self._get_port(rule)

        if from_port is not None:
            sg_data.update({
                'port_range_min': from_port,
                'port_range_max': to_port,
                'port': port
            })

        return sg_data

    @staticmethod
    def set_ip_range_data(ip_range):
        return {
            'remote_cidr': ip_range.get('CidrIp'),
            'remote': ip_range.get('CidrIp'),
            'description': ip_range.get('Description', '')
        }

    @staticmethod
    def set_group_pairs_data(group_pair):
        return {
            'remote_id': group_pair.get('GroupId'),
            'remote': group_pair.get('GroupId'),
            'description': group_pair.get('Description', '')
        }

    @staticmethod
    def match_security_group_from_ids(sg_ids, security_groups):
        return [security_group for security_group in security_groups if security_group['GroupId'] in sg_ids]

    @staticmethod
    def _get_protocol(protocol):
        if protocol == '-1':
            return 'ALL'
        elif protocol == 'tcp':
            return 'TCP'
        elif protocol == 'udp':
            return 'UDP'
        elif protocol == 'icmp':
            return 'ICMP'
        else:
            return protocol

    @staticmethod
    def _get_port(rule):
        protocol = rule.get('IpProtocol')

        if protocol == '-1':
            return 0, 65535, '0 - 65535'
        elif protocol in ['tcp', 'udp', 'icmp']:
            from_port = rule.get('FromPort')
            to_port = rule.get('ToPort')

            if from_port == to_port:
                port = from_port
            else:
                port = f'{from_port} - {to_port}'

            return from_port, to_port, port
        else:
            return None, None, None
