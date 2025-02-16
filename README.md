# Glif_Nezha

## 插件简介
Glif_Nezha是一款通过简单提示词就能复刻特定角色形象的AI绘图插件，为了庆祝电影《哪吒2之魔童闹海》票房大卖而制作。该插件对chatgpt-on-wechat和dify-on-wechat通用，但由于itchat协议最近被wx官方严厉打击，建议使用gewechat协议下的dify-on-wechat。该插件支持8个与电影相关的角色Lora模型：魔丸哪吒、灵珠哪吒、成年哪吒、太乙真人、申公豹、敖丙、敖光、敖闰。使用该插件之前需要注册glif平台账号并获取API token。该插件仅供娱乐，请勿将生成的图片用于商业用途。

## 基本信息
- 插件名称：Glif_Nezha
- 作者：Lingyuzhou
- 版本：1.0
- 描述：基于个Glif API的免费图像生成插件

## 安装方法

1. 访问glif平台官网 https://glif.app/，注册glif账号（需要谷歌或Discord账号）
2. 登录后访问 https://glif.app/settings/api-tokens 获取API token
3. 下载Glif_t2i插件包，解压后将Glif_t2i文件夹上传至到chatgpt-on-wechat/dify-on-wechat下的plugins目录，确保目录层级符合以下格式：
```
plugins
   └── Glif_Nezha
           └── config.json
           └── Glif_Nezha.py
           └── init.py
```

4. 在插件目录下的config.json中配置你的api_token：
```json
{
    "api_token": "你的API token"
}
```
5. 重启dify-on-wechat项目并输入`#scanp`命令扫描新插件

## 使用方法

### 基本语法
```
[触发词] [提示词描述] --ar [宽高比]
```

### 图片比例说明
使用`--ar`参数指定比例（1:1、16:9、9:16、4:3、3:4），默认为1:1


### 使用示例
```
魔丸哪吒包饺子
灵珠哪吒吃汤圆 --ar 9:16
成年哪吒喝咖啡 --ar 3:4
```

## 注意事项

1. 生成的图片会自动保存在插件目录的images文件夹中
2. 系统会自动清理3天前的图片以节省存储空间
3. 确保网络环境稳定，以保证API调用成功
4. 由于版权保护问题，严禁将该插件生成的图片用于商业用途，否则一切后果由插件使用者自负
