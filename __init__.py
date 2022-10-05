from email.message import Message
from nonebot_plugin_apscheduler import scheduler
from hashlib import md5
import json
from time import ctime
from nonebot import get_driver
from nonebot import on_command
from nonebot import require
from nonebot import get_bot
from nonebot.adapters.mirai2.message import MessageChain
from .config import Config

import requests

require("nonebot_plugin_apscheduler")

global_config = get_driver().config
config = Config.parse_obj(global_config)


async def user_checker(event) -> bool:
    return event.get_user_id() in config.zdtx_valid_users

signin = on_command('指点天下签到', rule=user_checker)
# schedule_test = on_command('定时任务测试', rule=user_checker)

@signin.handle()
async def daka():
    login_res = get_token()
    if not login_res['success']:
        await signin.send('尝试登录时发生错误')
        await signin.send('错误代码：' + str(login_res['status']))
        await signin.send('错误信息：' + login_res['msg'])
        return False
    submit_res = submit_health_info(login_res['token'])
    if not submit_res['success']:
        await signin.send('提交健康信息时发生错误')
        await signin.send('错误代码: ' + str(submit_res['status']))
        await signin.send('错误信息：' + submit_res['msg'])
        return False
    else:
        await signin.send('打卡成功，当前时间：' + ctime())
        return True

# @schedule_test.handle()
@scheduler.scheduled_job("cron", hour=config.zdtx_hour, id="zdtx")
async def scheduled_daka():
    bot = get_bot()
    if not await daka():
        await bot.send_group_message(
            target=config.zdtx_info_group,
            message_chain=MessageChain('打卡失败，请检查日志')
        )
    else:
        await bot.send_group_message(
            target=config.zdtx_info_group,
            message_chain=MessageChain('本日打卡已完成')
        )

# 登录获取axy-token
def get_token() -> dict:
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
        return {
            'success': False,
            'status': 'None',
            'msg': '网络错误'
        }
    if res['status'] == 1:
        return {
            'success': True,
            'token': res['data']
        }
    else:
        return {
            'success': False,
            'status': res['status'],
            'msg': res['msg']
        }


# 提交打卡信息
def submit_health_info(token: str) -> dict:
    health_json = config.zdtx_health_json_meta
    health_json['content'] = json.dumps(config.zdtx_health_json)
    try:
        res = requests.post(
            url='https://' + config.zdtx_college_prefix +
                '.zhidiantianxia.cn/api/study/health/mobile/health/apply',
            headers={
                'axy-phone': config.zdtx_phone,
                'axy-token': token
            },
            json=health_json
        ).json()
    except:
        return {
            'success': False,
            'status': 'None',
            'msg': '网络错误'
        }

    if res['status'] == 1:
        return {
            'success': True,
            'status': res['status'],
            'msg': res['msg']
        }
    else:
        return {
            'success': False,
            'status': res['status'],
            'msg': res['msg']
        }
