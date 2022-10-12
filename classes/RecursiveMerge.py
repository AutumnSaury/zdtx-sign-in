from copy import deepcopy


def dict_merge(d1: dict, d2: dict) -> dict:
    d = deepcopy(d1)
    for k, v in d2.items():
        if k in d:
            if isinstance(d[k], dict) and isinstance(v, dict):
                d[k] = dict_merge(d[k], v)
            else:
                d[k] = v
        else:
            d[k] = v
    return d