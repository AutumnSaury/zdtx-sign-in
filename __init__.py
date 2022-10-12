from typing import Coroutine
from nonebot_plugin_apscheduler import scheduler
from nonebot import get_driver
from nonebot import on_command
from nonebot import require
from nonebot import get_bot
import nonebot.params as nbparam
from nonebot.adapters.mirai2.message import MessageChain
from .config import Config
from .classes.ZdtxSession import ZdtxSession, ZdtxSessionException
from .classes.JsonLoader import templates, users, dialogs, dump_json
from nonebot.log import logger
import hashlib
import uuid
import time

require("nonebot_plugin_apscheduler")

global_config = get_driver().config
config = Config.parse_obj(global_config)

tutorial = on_command("配置打卡信息", priority=5, block=True)
scheduled_test = on_command("scheduled_test", priority=5, block=True)


async def user_checker(event) -> bool:
    return event.get_user_id() in config.zdtx_valid_users

@scheduled_test.handle()
@scheduler.scheduled_job("cron", hour=config.zdtx_hour, id="zdtx")
async def scheduled_daka():
    bot = get_bot()
    for user in users:
        template = next(filter(
            lambda x: x['meta']['templateId'] == user['health']['templateId'], templates))
        await daka(bot, user, template, dialogs)
    dump_json('users.json', users)

# 发起打卡
async def daka(bot, user: dict, template: dict, dialogs: dict):
    logger.info('正在为用户 QQ:{}进行打卡'.format(user['id']))
    await bot.send_friend_message(
        target=user['id'],
        message_chain=MessageChain(dialogs['greetings'])
    )
    session = ZdtxSession(user, template)
    try:
        result = session.submit_health_info()
    except ZdtxSessionException as e:
        logger.warning('用户 QQ:{}打卡失败：{}'.format(user['id'], e))
        await bot.send_friend_message(
            target=user['id'],
            message_chain=MessageChain(e.msg)
        )
        return

    if result['status'] == 1:
        logger.success('用户 QQ:{}打卡成功'.format(user['id']))
        await bot.send_friend_message(
            target=user['id'],
            message_chain=MessageChain(dialogs['succeeded'])
        )
    else:
        await bot.send_friend_message(
            target=user['id'],
            message_chain=MessageChain(dialogs['failed'])
        )
    user.update(session.dump())

