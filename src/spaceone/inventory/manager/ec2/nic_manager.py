from spaceone.core.manager import BaseManager
from spaceone.inventory.model.nic import NIC, NICTags


class NICManager(BaseManager):

    def __init__(self, params, ec2_connector=None):
        self.params = params
        self.ec2_connector = ec2_connector

    def get_nic_info(self, network_interfaces, subnet_vo):
        '''
        nic_data = {
            "device_index": 0,
            "device": "",
            "nic_type": "",
            "ip_addresses": [],
            "cidr": "",
            "mac_address": "",
            "public_ip_address": "",
            "tags": {
                "public_dns": "",
            }
        }
        '''

        nics = []
        for net_inf in network_interfaces:
            nic_tag_obj = NICTags({
                'public_dns': net_inf.get('Association', {}).get('PublicDnsName', ''),
                'eni_id': net_inf.get('NetworkInterfaceId', '')
            }, strict=False)

            nic_data = {
                'ip_addresses': self.get_private_ips(net_inf.get('PrivateIpAddresses', [])),
                'device': self.get_device(net_inf),
                'nic_type': net_inf.get('InterfaceType', ''),
                'cidr': subnet_vo.cidr,
                'mac_address': net_inf.get('MacAddress'),
                'public_ip_address': net_inf.get('Association', {}).get('PublicIp', ''),
                'tags': nic_tag_obj
            }

            if 'Attachment' in net_inf and 'DeviceIndex' in net_inf.get('Attachment'):
                nic_data.update({
                    'device_index': net_inf['Attachment']['DeviceIndex']
                })

            # eip = self.match_eip_from_instance_id(instance_id, eips)
            #
            # if eip is not None:
            #     nic_data.update({
            #         'public_ip_address': eip.get('PublicIp', '')
            #     })

            nics.append(NIC(nic_data, strict=False))

        return nics

    @staticmethod
    def get_private_ips(private_ips):
        return [ip.get('PrivateIpAddress') for ip in private_ips if ip.get('PrivateIpAddress') is not None]

    @staticmethod
    def get_device(net_inf):
        return ""

    @staticmethod
    def match_eip_from_instance_id(instance_id, eips):
        for eip in eips:
            if eip.get('InstanceId') == instance_id:
                return eip

        return None
