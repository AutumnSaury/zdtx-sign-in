from hashlib import md5
import json
from string import hexdigits
from nonebot import get_driver
from nonebot import on_command
from .config import Config

import requests

global_config = get_driver().config
config = Config.parse_obj(global_config)

# Export something for other plugin
# export = nonebot.export()
# export.foo = "bar"

# @export.xxx
# def some_function():
#     pass

matcher = on_command('myecho')


@matcher.handle()
async def repeat():
    await matcher.finish('233')


def get_token() -> tuple:
    try:
        res = requests.post(
            url='https://app.zhidiantianxia.cn/api/Login/pwd',
            headers={
                'axy-app-version': '1.7.4',
                'User-Agent': 'okhttp/3.10.0'
            },
            json={
                'phone': config.zdtx_phone,
                'password:': md5(('axy_' + config.zdtx_password).encode('utf-8')).hexdigits(),
                'deviceToken': config.zdtx_device_token
            }
        ).json()
    except:
        return False, None
    if res['status'] == 1:
        return True, res['axy-token']
    else:
        return False, res['status']

def submit_health_info(token: str) -> tuple:
    health_json = config.zdtx_health_json_meta
    health_json['content'] = json.dumps(config.zdtx_health_json)
    try:
        res = requests.post(
            url='https://' + config.zdtx_college_prefix + '.zhidiantianxia.cn/api/study/health/mobile/health/apply',
            headers={
                'axy-phone': config.zdtx_phone,
                'axy-token': token
            },
            json=health_json
        ).json()
    except:
        return False, None
    
    if res['status'] != 1:
        return False, res['status']
    else:
        return True, res['status']
