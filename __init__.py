from hashlib import md5
import json
from time import ctime
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

async def user_checker(event) -> bool:
    return event.get_user_id() in config.zdtx_valid_users

signin = on_command('指点天下签到', rule=user_checker)

@signin.handle()
async def daka():
    login_status, token = get_token()
    if not login_status:
        await signin.send('尝试登录时发生错误')
        await signin.finish(token)
    
    submit_status, submit_code = submit_health_info(token)
    if not submit_status:
        await signin.finish('提交健康信息时发生错误\n错误代码: ' + str(submit_code))

    await signin.finish('打卡成功，当前时间：' + ctime())

# 登录获取axy-token
def get_token() -> tuple:
    try:
        res = requests.post(
            url='https://app.zhidiantianxia.cn/api/Login/pwd',
            headers={
                'axy-app-version': '1.7.4',
                'User-Agent': 'okhttp/3.10.0'
            },
            data={
                'phone': config.zdtx_phone,
                'password': md5(('axy_' + config.zdtx_password).encode('utf-8')).hexdigest(),
                'deviceToken': config.zdtx_device_token
            }
        ).json()
    except:
        return False, 'Network Error'
    if res['status'] == 1:
        return True, str(res)
    else:
        return False, str(res)


# 提交打卡信息
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
