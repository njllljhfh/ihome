# -*- coding:utf-8 -*-

from flask import Blueprint

# 创建蓝图
api = Blueprint('api', __name__)
# api = Blueprint('api', __name__,url_prefix='/api/v1_0')

import index, verify_code, passport, profile, house


# 增加请求钩子函数，统一处理数据，返回为JSON格式
@api.after_request
def after_request(response):
    # 为例避免个别接口的类型获取出现异常,需要做好判断
    # 默认: text/html text/plain
    # print response.headers.get('Content-Type')
    if response.headers.get('Content-Type').startswith('text'):
        response.headers['Content-Type'] = 'application/json'
    return response
