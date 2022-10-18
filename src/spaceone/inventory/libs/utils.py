import yaml

def get_data_from_yaml(file_path):
    with open(file_path) as f:
        dict = yaml.load(f, Loader=yaml.FullLoader)

    return dict

def convert_tags(tags):
    dict_tags = {}

    for _tag in tags:
        dict_tags[_tag.get('Key')] = _tag.get('Value')

    return dict_tags
