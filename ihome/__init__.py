# -*- coding:utf-8 -*-

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# 所有的Flask扩展都可以延迟加载. 先在函数外部定义对象, 方便别的文件导入, 延迟传入app来加载相关配置
# 一开始不传入app
db = SQLAlchemy()


# 通过提供create_app函数, 实现app创建相关配置的封装
def create_app(config_object):
    """

    :param config_object: 配置类对象
    :return:
    """
    app = Flask(__name__)

    # 配置文件
    app.config.from_object(config_object)

    # 延迟加载db
    # db中填入app，核心目的是为了获取 config信息
    db.init_app(app)

    # # 配置数据库
    # db = SQLAlchemy(app)

    # 蓝图的导入, 可以用到时在加载, 以避免循环导入的问题
    # 注册蓝图，注册蓝图时，也可以填入 url前缀
    from ihome.api_1_0 import api
    app.register_blueprint(api, url_prefix='/api/v1_0')

    return app, db
