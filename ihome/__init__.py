# -*- coding:utf-8 -*-

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import DevelopmentConfig, ProductionConfig


# 通过提供create_app函数, 实现app创建相关配置的封装
def create_app(config_object):
    """

    :param config_object: 配置类对象
    :return:
    """
    app = Flask(__name__)

    # 配置文件
    app.config.from_object(config_object)

    db = SQLAlchemy(app)

    return app, db


# @app.route('/')
# def hello_world():
#     return 'Hello World!'
