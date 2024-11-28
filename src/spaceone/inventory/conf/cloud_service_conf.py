SUPPORTED_FEATURES = ['garbage_collection']
SUPPORTED_RESOURCE_TYPE = ['inventory.CloudService', 'inventory.Region', 'inventory.CloudServiceType']
SUPPORTED_SCHEDULES = ['hours']
NUMBER_OF_CONCURRENT = 20
DEFAULT_REGION = 'us-east-1'
FILTER_FORMAT = []
BOTO3_HTTPS_VERIFIED = None
DEFAULT_VULNERABLE_PORTS = "22,3306"

REGION_INFO = {
    'us-east-1': {'name': 'US East (N. Virginia)',
                  'tags': {'latitude': '39.028760', 'longitude': '-77.458263', 'continent': 'north_america'}},
    'us-east-2': {'name': 'US East (Ohio)',
                  'tags': {'latitude': '40.103564', 'longitude': '-83.200092', 'continent': 'north_america'}},
    'us-west-1': {'name': 'US West (N. California)',
                  'tags': {'latitude': '37.242183', 'longitude': '-121.783380', 'continent': 'north_america'}},
    'us-west-2': {'name': 'US West (Oregon)',
                  'tags': {'latitude': '45.841046', 'longitude': '-119.658093', 'continent': 'north_america'}},
    'af-south-1': {'name': 'Africa (Cape Town)',
                   'tags': {'latitude': '-33.932268', 'longitude': '18.424434', 'continent': 'africa'}},
    'ap-east-1': {'name': 'Asia Pacific (Hong Kong)',
                  'tags': {'latitude': '22.365560', 'longitude': '114.119420', 'continent': 'asia_pacific'}},
    'ap-south-1': {'name': 'Asia Pacific (Mumbai)',
                   'tags': {'latitude': '19.147428', 'longitude': '73.013805', 'continent': 'asia_pacific'}},
    'ap-northeast-3': {'name': 'Asia Pacific (Osaka-Local)',
                       'tags': {'latitude': '34.675638', 'longitude': '135.495706', 'continent': 'asia_pacific'}},
    'ap-northeast-2': {'name': 'Asia Pacific (Seoul)',
                       'tags': {'latitude': '37.528547', 'longitude': '126.871867', 'continent': 'asia_pacific'}},
    'ap-southeast-1': {'name': 'Asia Pacific (Singapore)',
                       'tags': {'latitude': '1.321259', 'longitude': '103.695942', 'continent': 'asia_pacific'}},
    'ap-southeast-2	': {'name': 'Asia Pacific (Sydney)',
                        'tags': {'latitude': '-33.921423', 'longitude': '151.188076', 'continent': 'asia_pacific'}},
    'ap-northeast-1': {'name': 'Asia Pacific (Tokyo)',
                       'tags': {'latitude': '35.648411', 'longitude': '139.792566', 'continent': 'asia_pacific'}},
    'ca-central-1': {'name': 'Canada (Central)',
                     'tags': {'latitude': '43.650803', 'longitude': '-79.361824', 'continent': 'north_america'}},
    'cn-north-1': {'name': 'China (Beijing)',
                   'tags': {'latitude': '39.919635', 'longitude': '116.307237', 'continent': 'asia_pacific'}},
    'cn-northwest-1': {'name': 'China (Ningxia)',
                       'tags': {'latitude': '37.354511', 'longitude': '106.106147', 'continent': 'asia_pacific'}},
    'eu-central-1': {'name': 'Europe (Frankfurt)',
                     'tags': {'latitude': '50.098645', 'longitude': '8.632262', 'continent': 'europe'}},
    'eu-west-1': {'name': 'Europe (Ireland)',
                  'tags': {'latitude': '53.330893', 'longitude': '-6.362217', 'continent': 'europe'}},
    'eu-west-2': {'name': 'Europe (London)',
                  'tags': {'latitude': '51.519749', 'longitude': '-0.087804', 'continent': 'europe'}},
    'eu-south-1': {'name': 'Europe (Milan)',
                   'tags': {'latitude': '45.448648', 'longitude': '9.147316', 'continent': 'europe'}},
    'eu-west-3': {'name': 'Europe (Paris)',
                  'tags': {'latitude': '48.905302', 'longitude': '2.369778', 'continent': 'europe'}},
    'eu-north-1': {'name': 'Europe (Stockholm)',
                   'tags': {'latitude': '59.263542', 'longitude': '18.104861', 'continent': 'europe'}},
    'me-south-1': {'name': 'Middle East (Bahrain)',
                   'tags': {'latitude': '26.240945', 'longitude': '50.586321', 'continent': 'middle_east'}},
    'sa-east-1': {'name': 'South America (São Paulo)',
                  'tags': {'latitude': '-23.493549', 'longitude': '-46.809319', 'continent': 'south_america'}},
    'us-gov-east-1': {'name': 'AWS GovCloud (US-East)',
                      'tags': {'continent': 'south_america'}},
    'us-gov-west-1': {'name': 'AWS GovCloud (US)',
                      'tags': {'continent': 'south_america'}},
    'global': {'name': 'Global'}
}