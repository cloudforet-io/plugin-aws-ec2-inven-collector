import unittest
import os
from datetime import datetime, timedelta
from unittest.mock import patch

from spaceone.core.unittest.result import print_data
from spaceone.core.unittest.runner import RichTestRunner
from spaceone.core import config
from spaceone.core import utils
from spaceone.core.transaction import Transaction

from spaceone.inventory.connector.ec2_connector import EC2Connector

AKI = os.environ.get('AWS_ACCESS_KEY_ID', None)
SAK = os.environ.get('AWS_SECRET_ACCESS_KEY', None)
ROLE_ARN = os.environ.get('ROLE_ARN', None)
DEFAULT_REGION = 'ap-northeast-2'


if AKI == None or SAK == None:
    print("""
##################################################
# ERROR 
#
# Configure your AWS credential first for test
##################################################
example)

export AWS_ACCESS_KEY_ID=<YOUR_AWS_ACCESS_KEY_ID>
export AWS_SECRET_ACCESS_KEY=<YOUR_AWS_SECRET_ACCESS_KEY>

""")
    exit


class TestAWSBotoConnector(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        secret = cls.get_secret()
        region = cls.get_region()

        cls.ec2_connector = EC2Connector(Transaction(), {})
        print('SET CLIENT')
        cls.ec2_connector.set_client(secret, region)

        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()

    @staticmethod
    def get_secret():
        secret_data = {
            'aws_access_key_id': AKI,
            'aws_secret_access_key': SAK
        }

        if ROLE_ARN:
            secret_data.update({
                'role_arn': ROLE_ARN
            })

        return secret_data

    @staticmethod
    def get_region():
        return DEFAULT_REGION

    def test_list_load_balancers(self):
        for i in range(2000):
            print(f'[COUNT: {i}]')
            lb_info = self.ec2_connector.list_load_balancers()
            print(lb_info, 'test_list_load_balancers')

    def test_list_listeners(self):
        lb_info = self.ec2_connector.list_load_balancers()

        for lb in lb_info:
            for i in range(2000):
                print(f'[COUNT: {i}]')
                listeners_info = self.ec2_connector.list_listeners(lb['LoadBalancerArn'])
                print(listeners_info, 'test_list_listeners')


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
