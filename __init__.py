import json
from nonebot_plugin_apscheduler import scheduler
from nonebot import get_driver
from nonebot import on_command
from nonebot import require
from nonebot import get_bot
import nonebot.params as nbparam
from nonebot.adapters.mirai2.message import MessageChain
from nonebot.typing import T_State
from .config import Config
from .classes.ZdtxSession import ZdtxSession, ZdtxSessionException
from .classes.JsonLoader import templates, users, dialogs, dump_json
from nonebot.log import logger
import hashlib
import uuid
from nonebot.adapters import Event
import time

require("nonebot_plugin_apscheduler")

global_config = get_driver().config
config = Config.parse_obj(global_config)

tutorial = on_command("配置打卡信息", priority=5, block=True)
scheduled_test = on_command("scheduled_test", priority=5, block=True)


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


@tutorial.handle()
async def _(status: T_State, e: Event):

    async def send_with_sleep(msg: str) -> None:
        await tutorial.send(msg)
        time.sleep(len(msg) // 10)

    status['user'] = {
        'platform': 'QQ',
        'id': int(e.get_user_id()),
        'basicInfo': {
            'college': None,
            'deviceToken': None,
            'phone': None,
            'encrypedPasswd': None
        },
        'token': {
            'value': None,
            'expire': None
        },
        'health': {
            'templateId': None,
            'templateOverrides': {},
        }
    }

    if int(e.get_user_id()) in [user['id'] for user in users]:
        await tutorial.finish('您已经配置过打卡信息了')

    await send_with_sleep('欢迎试用指点天下打卡功能')
    await send_with_sleep('在本交互式配置向导中，您将被要求输入您的指点天下账号信息与包括位置信息在内的隐私信息，这些信息将被安全地存储在我们的服务器上，并在打卡时上传至指点天下平台')
    await send_with_sleep('我们承诺您的信息不会被用于任何其他用途，并尽力保证不将其泄露给任何第三方')
    await send_with_sleep('请保证您输入的信息准确无误，并在其发生变更时及时更新，由错误健康信息造成的一切风险由您自行承担')
    await send_with_sleep('此外，由于本功能仍在开发中，稳定性尚无法保证，故我们不对因使用本功能对您造成的包括错过当日打卡在内的任何损失负责')
    await send_with_sleep('若您愿在承担上述风险的情况下试用本功能，请输入“同意”')
    await send_with_sleep('若不愿意，请发送任意消息以退出本向导')


@tutorial.got(key='affirmed')
async def _(key=nbparam.ArgPlainText('affirmed')):
    if key == '同意':
        await tutorial.send('配置向导将继续运行')
        await tutorial.send('现在，您需要跟随本向导录入您的指点天下账户基本信息。')
    else:
        await tutorial.finish('配置向导已结束')


@tutorial.got('college', prompt='请输入您所在学校的英文缩写（小写）\n指点天下目前仅接入郑州航空管理学院（zua）和华北水利水电大学（ncwu）')
async def _(status: T_State, key=nbparam.ArgPlainText('college')):
    if key not in ['zua', 'ncwu']:
        await tutorial.reject('您输入的学校似乎不受支持，请重新输入')
    status['user']['basicInfo']['college'] = key


@tutorial.got('phone', prompt='请输入您的指点天下账户绑定的手机号')
async def _(status: T_State, key=nbparam.ArgPlainText('phone')):
    if len(key) != 11:
        await tutorial.reject('请输入正确的手机号')
    status['user']['basicInfo']['phone'] = key


@tutorial.got('passwd', prompt='请输入您的指点天下账户的密码，本向导结束时您的密码将被加密保存')
async def _(status: T_State, key=nbparam.ArgPlainText('passwd')):
    e_passwd = hashlib.md5(('axy_' + key).encode('utf-8')).hexdigest()
    status['user']['basicInfo']['encrypedPasswd'] = e_passwd


@tutorial.got(
    'device_token', prompt="""
    在这一步，您需要输入您的设备标识(deviceToken)
    这是一个19位的十六进制数（字母使用小写），用于标识登录时使用的设备
    由于指点天下同一账户每日仅能切换一次设备的限制，我们建议您通过抓包等方式获取您日常使用的手机的设备标识
    您也可以输入“自动生成”来生成一个随机的19位十六进制数作为您的设备标识
    """
)
async def _(status: T_State, key=nbparam.ArgPlainText('device_token')):

    if key == '自动生成':
        key = hex(int(uuid.uuid1()) // 0x1e13 % 0xFFFFFFFFFFFFFFFFFFF)[2:]
        await tutorial.send('自动生成的设备标识：' + key)
    elif len(key) != 19:
        await tutorial.reject('您输入的设备标识有误，请重新输入')
    status['user']['basicInfo']['deviceToken'] = key


@tutorial.handle()
async def _():
    await tutorial.send('现在，您需要从下面的模板中选择一个健康信息模板，并在其基础上完善信息。您需要输入您选择的模板的编号')
    chart = '编号\t简介'
    for template in templates:
        chart += f'\n{template["meta"]["templateId"]}\t{template["description"]["brief"]}'
    await tutorial.send(chart)


@tutorial.got('template_id')
async def _(status: T_State, key=nbparam.ArgPlainText('template_id')):
    if int(key) not in [template['meta']['templateId'] for template in templates]:
        await tutorial.reject('您输入的编号有误，请重新输入')
    status['user']['health']['templateId'] = int(key)


"""
TODO: 根据模板的描述信息进行信息录入
"""


@tutorial.got('address', prompt='请输入您目前所处位置的地址\n例：北京市西城区西长安街174号')
async def _(status: T_State, key=nbparam.ArgPlainText('address')):
    status['user']['health']['templateOverrides']['location'] = {}
    status['user']['health']['templateOverrides']['location']['address'] = key


@tutorial.got('lng', prompt='请输入您所处位置的经度，经度和纬度可通过高德地图提供的坐标拾取器获取\n该坐标拾取器可通过https://lbs.gaode.com/console/show/picker访问\n例：111.111')
async def _(status: T_State, key=nbparam.ArgPlainText('lng')):
    status['user']['health']['templateOverrides']['location']['lng'] = float(
        key)


@tutorial.got('lat', prompt='请输入您所处位置的纬度\n例：111.111')
async def _(status: T_State, key=nbparam.ArgPlainText('lat')):
    status['user']['health']['templateOverrides']['location']['lat'] = float(
        key)


@tutorial.got('nowLocation', prompt='请输入您目前精确至县级行政区的位置，格式为：省-市-区/（直辖）市-市辖区-区')
async def _(status: T_State, key=nbparam.ArgPlainText('nowLocation')):
    status['user']['health']['templateOverrides']['nowLocation'] = key


@tutorial.handle()
async def _(status: T_State):
    s = json.dumps(status['user'], indent=4, ensure_ascii=False)
    users.append(status['user'])
    dump_json('users.json', users)
    await tutorial.send('您已完成信息录入，我们将在服务器上保存如下信息：')
    await tutorial.finish(s)
