# -*- coding:utf-8 -*-

class Config(object):
    DEBUG = True
    TESTING = False
    DATABASE_URI = 'sqlite://memory:'


class ProductionConfig(Config):
    DATABASE_URI = 'mysql://user@localhost/foo'


class DevelopmentConfig(Config):
    DEBUT = True
