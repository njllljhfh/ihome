# -*- coding:utf-8 -*-
import logging

from flask import request, g, jsonify, session

from ihome.utils.response_code import RET
from . import api
from ihome.utils.common import login_required
from ihome.libs.image_storage import storage
from ihome import db
from ihome.models import User
from ihome.utils import constants

"""更改了.js文件后，记得要清理浏览器的缓存"""


# 上传用户头像
@api.route('/users/avatar', methods=['POST'])
@login_required
def set_user_avatar():
    # 图片是以表单 提交的

    # 一 获取数据
    # 获取用户id
    user_id = g.user_id

    # 获取 用户头像
    # post表单上传的 文件数据，要用request.files来获取
    image_file = request.files.get('avatar')

    # 二 校验数据
    if image_file is None:
        return jsonify(errno=RET.DATAERR, errmsg='图片上传错误')

    # 三 逻辑处理
    # 1 调用工具类上传头像
    image_data = image_file.read()

    try:
        # file_name是存在 七牛云上的文件名
        image_file_name = storage(image_data)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='七牛云存储错误')

    # 2. 保存文件名到数据库中
    # 完整的网址是 ozcxm6oo6.bkt.clouddn.com + 文件名
    # user = User.query.filter_by(id=user_id).first()
    # user.avatar_url = file_name
    # db.session.add(user)
    # db.session.commit()
    try:
        User.query.filter_by(id=user_id).update({'avatar_url': image_file_name})
        # 这里要提交，否则mysql数据库中没有图片名字的数据
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logging.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='七牛云存储错误')

    # 四 返回数据
    # 拼接图片的完整url路径
    image_url = constants.QINIU_URL_DOMAIN + image_file_name

    return jsonify(errno=RET.OK, errmsg='请求成功', data={'avatar_url': image_url})


# 修改用户名
@api.route("/users/name", methods=["PUT"])
@login_required
def change_user_name():
    """修改用户名"""
    # 使用了login_required装饰器后，可以从g对象中获取用户user_id
    user_id = g.user_id

    # 获取用户想要设置的用户名
    req_data = request.get_json()
    if not req_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    name = req_data.get("name")  # 用户想要设置的名字
    if not name:
        return jsonify(errno=RET.PARAMERR, errmsg="名字不能为空")

    # 保存用户昵称name，并同时判断name是否重复（利用数据库的唯一索引)
    try:
        User.query.filter_by(id=user_id).update({"name": name})
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="设置用户错误")

    # 修改session数据中的name字段
    session["user_name"] = name
    return jsonify(errno=RET.OK, errmsg="OK", data={"name": name})


# 显示用户个人信息
@api.route("/users", methods=["GET"])
@login_required
def get_user_profile():
    """获取用户个人信息"""
    user_id = g.user_id
    # 查询数据库获取个人信息
    try:
        user = User.query.get(user_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")

    if user is None:
        return jsonify(errno=RET.NODATA, errmsg="无效操作")
    # {手机号:value;用户名:value;图像url:value}
    return jsonify(errno=RET.OK, errmsg="OK", data=user.to_dict())


# 增加实名认真窗口
@api.route("/users/auth", methods=["POST"])
@login_required
def set_user_auth():
    """保存实名认证信息"""
    user_id = g.user_id

    # 获取参数
    req_data = request.get_json()
    if not req_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    real_name = req_data.get("real_name")  # 真实姓名
    id_card = req_data.get("id_card")  # 身份证号

    # 参数校验
    if not all([real_name, id_card]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 保存用户的姓名与身份证号
    try:
        User.query.filter_by(id=user_id, real_name=None, id_card=None) \
            .update({"real_name": real_name, "id_card": id_card})
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存用户实名信息失败")

    return jsonify(errno=RET.OK, errmsg="OK")


# 查询实名认证信息
@api.route("/users/auth", methods=["GET"])
@login_required
def get_user_auth():
    """获取用户 的实名认证信息"""
    user_id = g.user_id

    # 在数据库中查询信息
    try:
        user = User.query.get(user_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户实名信息失败")

    if user is None:
        return jsonify(errno=RET.NODATA, errmsg="无效操作")

    return jsonify(errno=RET.OK, errmsg="OK", data=user.auth_to_dict())
