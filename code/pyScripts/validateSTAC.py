import json


def validateJSON(stac_file):
    try:
        json.loads(stac_file)
    except ValueError as err:
        return False
    return True
