import json
import os

dir = os.path.dirname(__file__)
json_dir = os.path.abspath(dir + '/../json' )

def __load_json(filename: str) -> dict:
    with open(json_dir + '/' + filename, 'rb+') as f:
        return json.load(f)

def dump_json(filename: str, data: dict) -> None:
    with open(json_dir + '/' + filename, 'w+') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

templates = __load_json('templates.json')
users = __load_json('users.json')
dialogs = __load_json('dialogs.json')