# zdtx-auto-sign-in

这是一个用于在指点天下平台进行自动签到的Nonebot2插件。

## 配置说明

此插件需要提供以下配置项以供正常运行：

```json
ZDTX_COLLEGE_PREFIX="xxx" # 指点天下域名前缀
ZDTX_DEVICE_TOKEN="abccdef1234567890abc" # 长度为19位，供设备识别用
ZDTX_PHONE="111xxxxxxxx" # 注册指点天下时使用的手机
ZDTX_PASSWORD="xxx" # 指点天下账户密码
ZDTX_HEALTH_JSON_META={} # 包含健康信息元数据的JSON，可通过抓包获取，或参考下文手写一份
ZDTX_HEALTH_JSON={} # 包含健康信息数据的JSON，将被转为字符串并放进ZDTX_HEALTH_JSON_META的content属性，可通过抓包获取或参考下文手写一份
ZDTX_VALID_USERS=[] # 合法用户ID，值为字符串
```

ZDTX_HEALTH_JSON参考：
```json
{
  # 位置信息可通过高德地图开放平台获取（https://lbs.gaode.com/console/show/picker）
  "location": {
    # 地址可以随便写
    "address": "",
    "code": "0",
    "lng": 116.395711,
    "lat": 39.908993
  },
  "temperature": "36.7",
  "health": "是",
  "observation": "否",
  "confirmed": "否",
  "haveCOVIDInPlaceOfAbode": "否",
  "goToHuiBei": "否",
  "contactIllPerson": "否",
  "haveYouEverBeenAbroad": "否",
  "familyPeopleNum": "1919",
  "isFamilyHealth": "否",
  "isFamilyStatus": "否",
  "familyPeopleIsAway": "否",
  "hasYourFamilyEverBeenAbroad": "否",
  "leave": "否",
  "isYesterdayMove": "否",
  "admission": "是",
  "help": "否",
  "nowLocation": "xx省-xx市-xx区"
}
```

ZDTX_HEALTH_JSON_META参考：
```json
{
  "health": 0,
  "student": 1,
  "templateId": "4"
}
```

注意以上两个JSON在放进env的时候都需要缩成一行