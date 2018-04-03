# -*- coding:utf-8 -*-
import logging

from flask import request, g, jsonify

from ihome.utils.response_code import RET
from . import api
from ihome.utils.common import login_required
from ihome.libs.image_storage import storage
from ihome import db
from ihome.models import User
from ihome.utils import constants


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
