from typing import Dict, List


def tags_dict(tags: List[Dict]) -> Dict:
    ret = dict()
    for item in tags:
        key = item['key']
        if "type" not in item:
            value = item['value']
        elif item["type"].startswith("int"):
            value = int(item['value'])
        elif item["type"].startswith("float"):
            value = float(item['value'])
        elif item["type"].startswith("bool"):
            value = bool(item['value'])
        else:
            value = str(item['value'])
        ret[key] = value
    return ret
