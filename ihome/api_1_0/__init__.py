# -*- coding:utf-8 -*-

from flask import Blueprint

# 创建蓝图
api = Blueprint('api', __name__)
# api = Blueprint('api', __name__,url_prefix='/api/v1_0')

import index, verify_code, passport
