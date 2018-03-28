# -*- coding:utf-8 -*-
from . import api  # api在init中
from ihome import db


@api.route('/')
def hello_world():
    return 'Hello World!'
