from spaceone.core.manager import BaseManager
from spaceone.inventory.model.disk import Disk


class DiskManager(BaseManager):

    def __init__(self, params, ec2_connector=None):
        self.params = params
        self.ec2_connector = ec2_connector

    def get_disk_info(self, volume_ids, volumes):
        '''
        disk_data = {
            "volume_id": "",
            "disk_type": "EBS",
            "volume_type": ""
            "device_index": 0,
            "device": "",
            "iops": 0,
            "encrypted": true | false
            "size": 100,
            "tags": {}
        }
        '''
        disks = []
        match_volumes = self.get_volumes_from_ids(volume_ids, volumes)

        index = 0
        for match_volume in match_volumes:
            volume_data = {
                'volume_id': match_volume.get('VolumeId'),
                'volume_type': match_volume.get('VolumeType'),
                'device_index': index,
                'device': self.get_device(match_volume),
                'encrypted': match_volume.get('Encrypted'),
                'size': match_volume.get('Size'),
            }

            if 'iops' in match_volume:
                volume_data.update({
                    'iops': match_volume.get('iops')
                })

            disks.append(Disk(volume_data, strict=False))
            index += 1

        return disks

    @staticmethod
    def get_volumes_from_ids(volume_ids, volumes):
        return [volume for volume in volumes if volume['VolumeId'] in volume_ids]

    @staticmethod
    def get_device(volume):
        attachments = volume.get('Attachments', [])

        for attachment in attachments:
            return attachment.get('Device')

        return ''
