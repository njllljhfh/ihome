# -*- coding:utf-8 -*-

# 将注册/登录/退出登录接口放于该文件

"""
errno: 用于前端判断出错的. 应该丰富多彩一些. 后续根据公司的需求, 进行补充
errmsg: 最好用于用户的显示. 方便前后端开发, 他们只需要做转发即可
因此, 有可能errno和errmsg提示的信息不一样. 或者再补充一个参数,专门给用户显示userinfo
"""

import re
import logging
from . import api
from flask import request, jsonify, current_app, session
from ihome.utils.response_code import RET
from ihome import redis_store, db
from ihome.models import User


# URL: /api/v1_0/users?mobile=17612345670&sms_code=1234&password=123456
# 请求参数: mobile / sms_code  / password

@api.route('/users', methods=['POST'])
def register():
    # 一. 获取参数
    # request.data
    # get_data获取的是str数据, 不利于后续的参数解析.
    # 如果要用,需要配合json.loads()转换为字典格式的数据
    # req_data = request.get_data()
    # print req_data.get('mobile')

    """get_json: 方便的获取JSON数据, 同时会自动转换为字典"""
    req_json = request.get_json()  # 得到字典类型数据
    mobile = req_json.get('mobile')
    sms_code = req_json.get('sms_code')
    password = req_json.get('password')

    # 二. 校验参数
    # 1. 完整性
    if not all([mobile, sms_code, password]):
        # resp = {
        #     'errno': RET.PARAMERR,
        #     'errmsg': '参数不全,请重新输入'
        # }
        # return jsonify(resp)

        # 建议以后使用这种写法, 简单一些
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全,请重新输入')

    # 2. 验证手机号 --> import re.match(r"1[3456789]\d{9}", value)
    if not re.match(r"^1[3456789]\d{9}$", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号不正确, 请输入正确手机号')

    # 三. 逻辑处理
    # 1. 从redis中获取数据对比
    # 2. 判断用户是否注册过，没注册就创建并保存用户
    # 3.（注册后直接登录）保存session

    # 1.1 从redis中获取数据
    try:
        real_sms_code = redis_store.get('sms_code_%s' % mobile)
    except Exception as e:
        # logging.error(e)
        # app.logger.error() logger模块默认已经集成到了app中
        current_app.logger.error(e)  # 但是敲代码时候，没有智能提示不好用
        return jsonify(errno=RET.DBERR, errmsg='redis读取失败')

    # 1.2 判断数据是否为None
    if real_sms_code is None:
        return jsonify(errno=RET.NODATA, errmsg='短信验证码过期')

    # 1.3 对比短信验证码
    if real_sms_code != sms_code:
        return jsonify(errno=RET.DATAERR, errmsg='短信验证码填写错误')

    # 1.4 删除短信验证码
    # 这里的1.3和1.4,与之前的短信验证码的步骤刚好相反.
    # 短信验证码:1. 发短信要钱 2. 短信验证码接收可能时间过长或丢失(用户体验会不好)
    try:
        redis_store.delete('sms_code_%s' % mobile)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='redis删除失败')

    # 2. 判断用户是否注册过，没注册就创建并保存用户(密码保存,会在模型中做加密处理)
    try:
        # filter_by直接用属性名，比较用=, filter用类名.属性名，比较用==
        # filter_by用于查询简单的列名，不支持比较运算符
        # filter比filter_by的功能更强大，支持比较运算符，支持or_、in_等语法。
        # ----
        xxx01 = User.query.filter_by(mobile=mobile)
        print xxx01
        # ----
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='mysql查询失败')
    else:
        if user is not None:
            # 用户信息不是None, 说明已存在(已注册)
            return jsonify(errno=RET.DATAEXIST, errmsg='用户手机号已经注册')

        # 用户没有注册过 --> 创建用户对象并保存
        user = User(name=mobile, mobile=mobile)

        # pbkdf2:sha256:50000$ey5Pg8Ie$4fca7afb538b79c4d6c66a4c8c3cae23c192f02bfa97e8c51605d1fa6cd08773
        user.password = password

        # 用户1  123456 + 盐值 salt itcast
        # 用户2  123456 + 盐值 salt hello
        # i1t2c3a4s5t6
        # h1e2l3l4056
        # 希望有一个属性, 传入密码之后, 可以自动处理密码加密,并赋值给password_hash属性
        # user.password_hash = password

        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            # 还需要数据回滚
            db.session.rollback()
            logging.error(e)
            return jsonify(errno=RET.DBERR, errmsg='mysql添加失败')

    # 3.（注册后直接登录）保存session
    try:
        session['user_id'] = user.id
        session['user_name'] = mobile
        session['mobile'] = mobile
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.SESSIONERR, errmsg='session设置失败')

    # 四. 返回数据
    return jsonify(errno=RET.OK, errmsg='注册成功')


# URL: /api/v1_0/sessions
# 参数: mobile / password
@api.route('/sessions', methods=['POST'])
def login():
    # 一. 获取参数
    req_json = request.get_json()
    mobile = req_json.get('mobile')
    password = req_json.get('password')

    # 二. 校验参数
    # 1. 完整性
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全,请重新输入')

    # 2. 验证手机号
    if not re.match(r"^1[3456789]\d{9}$", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号不正确, 请输入正确手机号')

    # 三. 逻辑处理
    # 1. 从redis中获取登录的错误次数 --> 如果超过最大次数,直接返回.
    user_ip = request.remote_addr
    print 'user_ip= ', user_ip
    try:
        user_error_count = redis_store.get('user_error_count_%s' % user_ip)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='redis读取失败')

    # 2. 没有超过最大次数(0~4), 查询用户是否存在或密码是否正确, 如果有问题返回错误,同时增加错误次数
    # 如果用户存在 并且 错误次数大于等于5
    if user_error_count is not None and int(user_error_count) >= 5:
        return jsonify(errno=RET.REQERR, errmsg='登录次数过于频繁')

    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='mysql查询失败')

    # 用户不存在 或者 检查密码没通过
    if user is None or not user.check_password_hash(password):

        # 记录错误次数,再返回
        try:
            # 会将 'user_error_count_%s' % user_ip 这个键存在redis中，并记录次数
            redis_store.incr('user_error_count_%s' % user_ip)
            redis_store.expire('user_error_count_%s' % user_ip, 86400)
        except Exception as e:
            logging.error(e)
            # return jsonify(errno=RET.DBERR, errmsg='redis设置失败')

        return jsonify(errno=RET.DATAERR, errmsg='用户名或密码填写错误')

    # 3. 设置session数据
    try:
        session['user_id'] = user.id
        session['user_name'] = user.name
        session['mobile'] = user.mobile
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.SESSIONERR, errmsg='session设置失败')

    # 4. 用户登录成功后 删除redis的错误次数
    try:
        redis_store.delete('user_error_count_%s' % user_ip)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='redis删除失败')

    # 四. 返回数据
    return jsonify(errno=RET.OK, errmsg='登录成功')


# 检查登录状态
@api.route("/sessions", methods=["GET"])
def check_login():
    """检查登陆状态"""
    # 尝试从session中获取用户的名字
    name = session.get("user_name")
    # 如果session中数据name名字存在，则表示用户已登录，否则未登录
    if name is not None:
        return jsonify(errno=RET.OK, errmsg="true", data={"name": name})
    else:
        return jsonify(errno=RET.SESSIONERR, errmsg="false")


# 退出
@api.route("/sessions", methods=["DELETE"])
# @login_required
def logout():
    """登出"""
    # 清除session数据, csrf_token需要保留.
    # csrf_token = session['csrf_token']
    session.clear()
    # session['csrf_token'] = csrf_token
    return jsonify(errno=RET.OK, errmsg="OK")
