# -*- coding:utf-8 -*-
import redis


class Config(object):
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1/ihome'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 随机生成一个SECRET_KEY
    # In[1]: import os
    # In[2]: import base64
    # In[3]: base64.b64encode(os.urandom(24))
    # Out[3]: b'C56b2AtlYpOrtPaQCCwcGM0E3Ed3mxQq'
    SECRET_KEY = 'C56b2AtlYpOrtPaQCCwcGM0E3Ed3mxQq'

    # 创建redis实例用到的参数
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    # 配置Flask-Session信息
    SESSION_TYPE = 'redis'  # 设置数据库类型
    SESSION_USE_SIGNER = True

    # 扩展默认会有redis的地址信息(127.0.0.1, 6379), 以及前缀信息(session)
    SESSION_REDIS = redis.StrictRedis(port=REDIS_PORT, host=REDIS_HOST)
    # 设置 session的过期时间（默认是31天)
    PERMANENT_SESSION_LIFETIME = 86400 * 2


class ProductionConfig(Config):
    DEBUG = False


class DevelopmentConfig(Config):
    DEBUG = True
