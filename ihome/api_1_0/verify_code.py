# -*- coding:utf-8 -*-
import logging
import random

from flask import jsonify, make_response, request

from ihome.libs.yuntongxun.sms import CCP
from ihome.models import User
from ihome.utils.captcha.captcha import captcha
from ihome.utils.response_code import RET  # 错误码
from . import api
from ihome import redis_store  # 将验证码的数据和编号存在redis中


# 获取图形验证码
# 请求方式: GET
# 路由: image_codes
@api.route('/image_codes/<image_code_id>')
def get_image_code(image_code_id):
    # 1. 使用工具类生成图形验证码
    # （名字，文本，图像数据）
    name, text, image_data = captcha.generate_captcha()

    # 2. 将验证码的数据和编号存储到redis中
    try:
        # redis_store.set()
        # redis_store.expires()
        # setex:设置数据同时设置有效期.
        # 第一位:KEY ,第二位:有效期  第三位:VALUE
        redis_store.setex('image_code_%s' % image_code_id, 300, text)
    except Exception as e:
        # 记录日志
        logging.error(e)
        resp = {
            'errno': RET.DBERR,
            'errmsg': 'redis保存出错'
        }
        return jsonify(resp)

    # return image_data (默认响应头中的文本信息类型是text/html)
    # 3. 返回图像
    resp = make_response(image_data)

    # 更改响应头中的内容类型
    resp.headers['Content-Type'] = 'image/jpg'
    return resp


# 获取短信验证码
# 请求方式: GET
# 路由: sms_codes
# 参数: 手机号 / 图像验证码 / 编号
# URL: /api/v1_0/sms_codes/17612345678?image_code=abcd&image_code_id=UUID
@api.route('/sms_codes/<re(r"1[3456789][0-9]{9}"):mobile>')
def get_sms_codes(mobile):
    # 一. 获取参数: 图像验证码 / 编号
    image_code = request.args.get('image_code')
    image_code_id = request.args.get('image_code_id')
    # ---------------
    # global xxx
    # xxx = [image_code_id]

    # 二. 校验参数: 完整性
    if not all([image_code, image_code_id]):
        resp = {
            'errno': RET.PARAMERR,
            'errmsg': '参数不全'
        }
        return jsonify(resp)

    # 三  逻辑处理
    # 1.从redis中获取数据对比
    # 2.判断用户是否注册过
    # 3.调用第三方SDK发短信

    # 1.从redis中获取数据对比
    # 1_1 获取redis数据
    try:
        real_image_code = redis_store.get('image_code_%s' % image_code_id)
    except Exception as e:
        logging.error(e)
        resp = {
            'errno': RET.DBERR,
            'errmsg': 'redis读取失败'
        }
        return jsonify(resp)

    # 1_2 判断数据是否为None
    # 数据库获取操作, 一定要判断None. 只要查询不出数据,就是返回None
    if real_image_code is None:
        resp = {
            'errno': RET.DBERR,
            'errmsg': '验证码过期, 请重新刷新获取'
        }
        return jsonify(resp)

    # 1_3 无论是否对比成功, 先删除服务器的验证码 --> 图像验证码只能验证一次
    try:
        redis_store.delete('image_code_%s' % image_code_id)
    except Exception as e:
        logging.error(e)
        resp = {
            'errno': RET.DBERR,
            'errmsg': 'redis删除失败'
        }
        return jsonify(resp)

    # 1_4 对比验证码数据
    # ABCD = abcd
    if real_image_code.lower() != image_code.lower():
        resp = {
            'errno': RET.DATAERR,
            'errmsg': '验证码填写错误, 请刷新后重试'
        }
        return jsonify(resp)

    # print xxx

    # 2.判断用户是否注册过
    # 2_1 查询数据库的操作
    # 2_2 判断数据是否为None
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        logging.error(e)
        resp = {
            'errno': RET.DBERR,
            'errmsg': 'mysql查询失败'
        }
        return jsonify(resp)
    else:
        # 执行成功走else
        if user is not None:
            # 用户已经注册过
            resp = {
                'errno': RET.DATAEXIST,
                'errmsg': '该用户的手机号已注册,请更换手机号'
            }
            # print '该用户的手机号已注册'
            return jsonify(resp)

    # 3.调用第三方SDK发短信
    # 3_1 创建6位短信验证码  000000 0000
    # import random
    # random.randint(0, 999999)
    # %06d: 6位数字, 不足以0补齐
    sms_code = '%06d' % random.randint(0, 999999)

    # 3_2 保存到redis中
    try:
        redis_store.setex('sms_code_%s' % mobile, 300, sms_code)
    except Exception as e:
        logging.error(e)
        resp = {
            'errno': RET.DBERR,
            'errmsg': 'redis保存失败'
        }
        return jsonify(resp)

    # 3_3 发送验证码(第三方工具）
    ccp = CCP()
    # 参数1 电话号码
    # 参数2 验证码，验证码过期时间(分钟)，
    # 参数3 SKD的模板类型
    result = ccp.send_template_sms(mobile, [sms_code, '5'], 1)

    # 四  返回数据
    if result == '000000':
        resp = {
            'errno': RET.OK,
            'errmsg': '发送短信成功'
        }
        return jsonify(resp)
    else:
        resp = {
            'errno': RET.THIRDERR,
            'errmsg': '发送短信失败'
        }
        return jsonify(resp)
