from base64 import b64decode
from copy import deepcopy
import json
import time
from typing import Callable
import requests
from .RecursiveMerge import dict_merge
from time import sleep


class ZdtxSession:
    def __init__(self, user: dict, template: dict) -> None:
        self.user = user
        self.template = deepcopy(template['meta'])

        self.template['templateId'] = str(template['meta']['templateId'])
        self.template_content = dict_merge(
            template['content'],
            user['health']['templateOverrides']
        ),
        self.template['content'] = str(self.template_content)

    # 请求前检查token是否失效
    def check_token(func: Callable) -> Callable:
        # 通过请求检验token
        def validator(token: str, phone: str) -> bool:
            try:
                res = requests.post(
                    url='https://api.zdtxapp.com/api/my/version/1',
                    headers={
                        'axy-phone': phone,
                        'axy-token': token
                    }
                )
            except:
                raise ZdtxSessionException('检查token是否有效时发生网络错误')
            if res['status'] and res['status'] == 1:
                return True
            else:
                return False

        def wrapper(self, *args, **kwargs):
            if not self.user['token']['value'] or \
                    time.time() > self.user['token']['expire'] or \
                    not validator(self.user['token']['value'], self.user['basicInfo']['phone']):
                self.renew_token()
            return func(self, *args, **kwargs)
        return wrapper

    # 网络请求重试装饰器
    def retry(cnt: int = 3) -> Callable:
        def outter(func: Callable) -> Callable:
            def wrapper(self, *args, **kwargs):
                for i in range(cnt):
                    try:
                        return func(self, *args, **kwargs)
                    except ZdtxSessionException as e:
                        if i == cnt - 1:
                            raise e
                        sleep(1)
            return wrapper
        return outter

    # 刷新token
    @retry(3)
    def renew_token(self) -> dict:
        try:
            res = requests.post(
                url='https://app.zhidiantianxia.cn/api/Login/pwd',
                headers={
                    'axy-app-version': '1.7.4',
                    'User-Agent': 'okhttp/3.10.0'
                },
                data={
                    'phone': self.user['basicInfo']['phone'],
                    'password': self.user['basicInfo']['encrypedPasswd'],
                    'deviceToken': self.user['basicInfo']['deviceToken']
                }
            ).json()
        except:
            raise ZdtxSessionException('获取token时发生网络错误')
        if res['status'] == 1:
            self.user['token']['value'] = res['data']
            info_b64 = self.user['token']['value'].split('.')[1]
            info_json = json.loads(b64decode(info_b64).decode('utf-8'))
            self.user['token']['expire'] = info_json['exp']
            return res
        else:
            raise ZdtxSessionException('刷新token失败：' + res['msg'])

    # 提交打卡信息
    @check_token
    @retry(5)
    def submit_health_info(self) -> dict:
        try:
            res = requests.post(
                url='https://' + self.user['basicInfo']['college'] +
                    '.zhidiantianxia.cn/api/study/health/mobile/health/apply',
                headers={
                    'axy-phone': self.user['basicInfo']['phone'],
                    'axy-token': self.user['token']['value']
                },
                json=self.template
            ).json()
        except:
            raise ZdtxSessionException('提交打卡信息时发生网络错误')
        if res['status'] == 1:
            return res
        else:
            raise ZdtxSessionException('打卡失败：' + res['msg'])

    def dump(self) -> dict:
        return self.user

    def __str__(self):
        return str(self.user)


class ZdtxSessionException(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg

    def __str__(self):
        return self.msg
