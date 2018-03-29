# -*- coding:utf-8 -*-
import logging
from flask import session
from . import api  # api在init中
from ihome import db
from ihome import models


@api.route('/')
def hello_world():
    session['name'] = 'lixiaolong'
    logging.debug('debug')
    return 'Hello World!'


@api.route('/demo', methods=['GET', 'POST'])
def demo():
    return 'demo'
