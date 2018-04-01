# -*- coding:utf-8 -*-

import redis
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from utils.common import RegexConverter

# 所有的Flask扩展都可以延迟加载. 先在函数外部定义对象, 方便别的文件导入, 延迟传入app来加载相关配置
# 一开始不传入app
db = SQLAlchemy()

# 其他模块使用redis_store来操作redis
redis_store = None
'''
开发中使用DEBUG级别, 来输出丰富的调试信息.
发布时使用WARN以上级别, 来显示异常信息
log文件存满, 会自动叠加序号, 并产生新的log文件. 如果文件存满了, 就覆盖原先的文件
'''
# 设置日志的记录等级
logging.basicConfig(level=logging.DEBUG)  # 调试debug级
# 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
# 创建日志记录的格式                 日志等级    输入日志信息的文件名 行数    日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（flask app使用的）添加日志记录器
logging.getLogger().addHandler(file_log_handler)


# 通过提供create_app函数, 实现app创建相关配置的封装
def create_app(config_object):
    """

    :param config_object: 配置类对象
    :return:
    """
    app = Flask(__name__)

    # 配置文件
    app.config.from_object(config_object)

    # 添加正则路由
    app.url_map.converters['re'] = RegexConverter

    # 延迟加载db
    # db中填入app，核心目的是为了获取 config信息
    db.init_app(app)

    # csrf保护, 针对post/put/delete等会修改数据的请求方式, 需要开启保护
    # CSRFProtect(app)

    # 创建redis
    global redis_store
    redis_store = redis.StrictRedis(port=config_object.REDIS_PORT, host=config_object.REDIS_HOST)
    # print config_object.REDIS_HOST
    # print config_object.REDIS_PORT

    # 创建Flask-Session. 将保存在浏览器的cookie中的session信息,同步到你要设置的地方
    Session(app)

    # # 配置数据库
    # db = SQLAlchemy(app)

    # 蓝图的导入, 可以用到时在加载, 以避免循环导入的问题
    # 注册蓝图，注册蓝图时，也可以填入 url前缀
    from ihome.api_1_0 import api
    app.register_blueprint(api, url_prefix='/api/v1_0')

    # 导入并注册蓝图
    import web_html
    app.register_blueprint(web_html.html)

    return app, db
