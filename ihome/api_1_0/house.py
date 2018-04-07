# -*- coding:utf-8 -*-

import logging

from . import api
from ihome.models import Area, House, Facility, HouseImage, User, Order
from flask import jsonify, json, request, g, session
from ihome.utils.response_code import RET
from ihome import redis_store, db
from ihome.utils import constants
from ihome.utils.common import login_required
from ihome.libs.image_storage import storage
from datetime import datetime

'''
{
    "errno": 0,
    "errmsg": "查询城区信息成功",
    "data": {
        "areas": [
            {
                "aid": 1,
                "aname": "东城区"
            }
        ]
    }
}
'''


@api.route('/areas')
def house_areas():
    # 一. redis数据查询
    try:
        area_json = redis_store.get('house_area_info')
    except Exception as e:
        logging.error(e)
        # 这里没有redis,不需要返回报错信息
        # 为了确保数据不出问题, 可以出错时强制设置None
        area_json = None

    # 二. 没有redis数据, 查询数据库
    if area_json is None:
        try:
            areas_list = Area.query.all()
        except Exception as e:
            logging.error(e)
            return jsonify(errno=RET.DBERR, errmsg='mysql查询失败')

        area_dict = {'areas': [area.to_dict() for area in areas_list]}

        # 1L-->ASCII编码 --> 改变编码格式
        area_json = json.dumps(area_dict)

        # 三. 将数据存储到redis中
        try:
            # set: 如果用set也可以,只需要在数据发生改变时,执行删除redis的操作重新保存即可
            redis_store.setex('house_area_info', constants.AREA_INFO_REDIS_EXPIRES, area_json)
        except Exception as e:
            logging.error(e)
            return jsonify(errno=RET.DBERR, errmsg='redis设置失败')

    # 这样用 josn.loads(area_json) 返回信息，也能解决下面的问题
    # return jsonify(errno=RET.OK, errmsg='查询成功', data=json.loads(area_json))

    # 返回数据
    # dict的二次转换问题:第一次已经将字典转换成字符串了. 第二次转换会直接使用字符串
    # return jsonify(errno=RET.OK, errmsg='查询成功', data=area_json)
    # return '{"errno":0,"errmsg":"查询成功","data":%s}' % area_json, 200, {'Content-Type': 'application/json'}
    return '{"errno":0,"errmsg":"查询成功","data":%s}' % area_json


# 设置房屋信息
@api.route("/houses/info", methods=["POST"])
@login_required
def save_house_info():
    """保存房屋的基本信息
    前端发送过来的json数据
    {
        "title":"",
        "price":"",
        "area_id":"1",
        "address":"",
        "room_count":"",
        "acreage":"",
        "unit":"",
        "capacity":"",
        "beds":"",
        "deposit":"",
        "min_days":"",
        "max_days":"",
        "area_id":"1",
        "facility":["7","8"]
    }
    """
    # 一. 获取参数
    house_data = request.get_json()
    if house_data is None:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    title = house_data.get("title")  # 房屋名称标题
    price = house_data.get("price")  # 房屋单价
    area_id = house_data.get("area_id")  # 房屋所属城区的编号
    address = house_data.get("address")  # 房屋地址
    room_count = house_data.get("room_count")  # 房屋包含的房间数目
    acreage = house_data.get("acreage")  # 房屋面积
    unit = house_data.get("unit")  # 房屋布局（几室几厅)
    capacity = house_data.get("capacity")  # 房屋容纳人数
    beds = house_data.get("beds")  # 房屋卧床数目
    deposit = house_data.get("deposit")  # 押金
    min_days = house_data.get("min_days")  # 最小入住天数
    max_days = house_data.get("max_days")  # 最大入住天数

    # 二. 校验参数
    if not all(
            [title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 判断单价和押金格式是否正确
    # 前端传送过来的金额参数是以元为单位，浮点数，数据库中保存的是以分为单位，整数
    try:
        price = int(float(price) * 100)
        deposit = int(float(deposit) * 100)
    except Exception as e:
        return jsonify(errno=RET.DATAERR, errmsg="参数有误")

    # 三. 保存信息
    # 1. 创建房屋对象
    user_id = g.user_id
    house = House(
        user_id=user_id,
        area_id=area_id,
        title=title,
        price=price,
        address=address,
        room_count=room_count,
        acreage=acreage,
        unit=unit,
        capacity=capacity,
        beds=beds,
        deposit=deposit,
        min_days=min_days,
        max_days=max_days
    )

    # 2. 处理房屋的设施信息
    # 后续如果遇到选填数据.可以先获取必填数据,校验并创建模型数据.然后针对可选数据做判断
    facility_id_list = house_data.get("facility")
    if facility_id_list:
        # 表示用户勾选了房屋设施
        # 过滤用户传送的不合理的设施id
        # select * from facility where id in (facility_id_list)
        try:
            facility_list = Facility.query.filter(Facility.id.in_(facility_id_list)).all()
        except Exception as e:
            logging.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据库异常")

        # 为房屋添加设施信息
        if facility_list:
            house.facilities = facility_list

    # 3. 保存数据库
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")

    # 四. 返回
    return jsonify(errno=RET.OK, errmsg="保存成功", data={"house_id": house.id})


# 发布房屋图片接口
# 房屋id / 图片
# 逻辑: 1. 上传到七牛云 2. 保存数据库:需要2个地方 house/houser_image
@api.route("/houses/image", methods=["POST"])
@login_required
def save_house_image():
    """保存房屋的图片"""
    # 获取参数 房屋的图片、房屋编号
    house_id = request.form.get("house_id")
    image_file = request.files.get("house_image")

    # 校验参数
    if not all([house_id, image_file]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 1. 还需要对house_id做判断
    try:
        house = House.query.get(house_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if house is None:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 2. 使用工具类上传(读取图片的二进制数据)
    image_data = image_file.read()
    try:
        file_name = storage(image_data)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="保存房屋图片失败")

    # 3. 保存数据库:需要2个地方 house/houser_image
    # 专门存储房屋图片的表
    house_image = HouseImage(
        house_id=house_id,
        url=file_name
    )
    db.session.add(house_image)

    # 增加房屋模型的字段数据
    if not house.index_image_url:
        # 没有房屋的主图信息,才应该添加
        house.index_image_url = file_name
        db.session.add(house)

    # 统一进行提交
    try:
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存图片信息失败")

    # 4. 返回数据
    image_url = constants.QINIU_URL_DOMAIN + file_name
    return jsonify(errno=RET.OK, errmsg="保存图片成功", data={'image_url': image_url})


@api.route("/users/houses", methods=["GET"])
@login_required
def get_user_houses():
    """获取房东发布的房源信息条目"""
    user_id = g.user_id

    try:
        user = User.query.get(user_id)
        houses = user.houses

        # houses = House.query.filter_by(user_id=user_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取数据失败")

    # 将查询到的房屋信息转换为字典存放到列表中
    houses_list = []
    if houses:
        for house in houses:
            houses_list.append(house.to_basic_dict())
    return jsonify(errno=RET.OK, errmsg="OK", data={"houses": houses_list})


@api.route("/houses/index", methods=["GET"])
def get_house_index():
    """获取主页幻灯片展示的房屋基本信息"""
    # 从缓存中尝试获取数据
    try:
        ret = redis_store.get("home_page_data")
    except Exception as e:
        logging.error(e)
        ret = None
    if ret:
        logging.info("hit house index info redis")
        # 因为redis中保存的是json字符串，所以直接进行字符串拼接返回
        return '{"errno":0, "errmsg":"OK", "data":%s}' % ret
    else:
        try:
            # 查询数据库，返回房屋订单数目最多的5条数据
            houses = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_HOUSES)
        except Exception as e:
            logging.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

        if not houses:
            return jsonify(errno=RET.NODATA, errmsg="查询无数据")

        # 一般不会出现主图没设置的情况(1. 后端接口做好处理, 必须填) 2. 如果真的没有数据, 可以让前端/移动端显示默认图片
        houses_list = []
        for house in houses:
            # 如果房屋未设置主图片，则跳过
            if not house.index_image_url:
                continue
            houses_list.append(house.to_basic_dict())

        # 将数据转换为json，并保存到redis缓存
        json_houses = json.dumps(houses_list)
        try:
            redis_store.setex("home_page_data", constants.HOME_PAGE_DATA_REDIS_EXPIRES, json_houses)
        except Exception as e:
            logging.error(e)

        return '{"errno":0, "errmsg":"OK", "data":%s}' % json_houses


@api.route("/houses/<int:house_id>", methods=["GET"])
def get_house_detail(house_id):
    """获取房屋详情"""
    # 前端在房屋详情页面展示时，如果浏览页面的用户不是该房屋的房东，则展示预定按钮，否则不展示，
    # 所以需要后端返回登录用户的user_id
    # 尝试获取用户登录的信息，若登录，则返回给前端登录用户的user_id，否则返回user_id=-1
    user_id = session.get("user_id", "-1")

    # 校验参数
    if not house_id:
        return jsonify(errno=RET.PARAMERR, errmsg="参数缺失")

    # 先从redis缓存中获取信息
    try:
        ret = redis_store.get("house_info_%s" % house_id)
    except Exception as e:
        logging.error(e)
        ret = None
    if ret:
        logging.info("hit house info redis")
        return '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, ret), 200, {
            "Content-Type": "application/json"}

    # 查询数据库
    try:
        house = House.query.get(house_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not house:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 将房屋对象数据转换为字典
    try:
        house_data = house.to_full_dict()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据出错")

    # 存入到redis中
    json_house = json.dumps(house_data)
    try:
        redis_store.setex("house_info_%s" % house_id, constants.HOUSE_DETAIL_REDIS_EXPIRE_SECOND, json_house)
    except Exception as e:
        logging.error(e)

    resp = '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, json_house)
    return resp


# /api/v1_0/houses?sd=xxxx-xx-xx&ed=xxxx-xx-xx&aid=xx&sk=new&p=1
@api.route("/houses", methods=["GET"])
def get_house_list():
    """获取房屋列表信息"""
    # 一. 获取参数
    # 注意: 参数可以不传, 不传就把参数设为空值或者默认值
    start_date_str = request.args.get("sd", "")  # 想要查询的起始时间
    end_date_str = request.args.get("ed", "")  # 想要查询的终止时间
    area_id = request.args.get("aid", "")  # 区域id
    sort_key = request.args.get("sk", "new")  # 排序关键字
    page = request.args.get("p", 1)  # 页数

    # 二. 校验参数
    # 2.1判断日期
    # 需要确保能够转换成日期类, 且开始时间不能小于结束时间
    try:
        start_date = None
        end_date = None

        if start_date_str:
            # 将字符串转化为日期
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')

        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

        if start_date and end_date:
            assert start_date <= end_date
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='日期参数有误')

    # 2.2判断页数
    # 需要确保页数能够转为int类型
    try:
        page = int(page)
    except Exception as e:
        page = 1

    # 三. 业务逻辑处理

    # 3.1 先从redis缓存中获取数据
    # 如果获取了数据, 可以直接返回, 不需要执行下面逻辑
    try:
        # 将所有的参数条件当做Key(除了页码)
        redis_key = "houses_%s_%s_%s_%s" % (start_date_str, end_date_str, area_id, sort_key)
        resp_json = redis_store.hget(redis_key, page)
    except Exception as e:
        logging.error(e)
        resp_json = None

    # 有缓存直接返回数据
    if resp_json:
        return resp_json

    # 3.2 定义查询数据的参数空列表
    # 为了方便设置过滤条件, 先定义空列表, 然后逐步判断添加进来
    filter_params = []

    # 3.3 处理区域信息--> 拼接查询条件
    if area_id:
        # 常规后面的内容,可能会存储为true或false.
        # 而我们需要的保存查询的条件, 以便于后面展开
        # ==:__eq__ 底层会调用该函数,如果重写了__eq__, 比较的结果就会不一样
        # SQLAlchemy重写了__eq__函数,对比之后,只会返回查询的条件
        filter_params.append(House.area_id == area_id)

    print 'filter_params=', filter_params

    # 3.4 处理时间, 获取不冲突的房屋信息
    # 需要根据传入的时间参数不同, 获取冲突的房屋, 再从房屋中获取对应的房屋ID
    try:
        conflict_orders_li = []
        if start_date and end_date:
            # 从订单表中查询冲突的订单，进而获取冲突的房屋id
            conflict_orders_li = Order.query.filter(Order.begin_date <= end_date, Order.end_date >= start_date).all()
        elif start_date:
            # 从订单表中查询冲突的订单，进而获取冲突的房屋id
            conflict_orders_li = Order.query.filter(Order.end_date >= start_date).all()
        elif end_date:
            # 从订单表中查询冲突的订单，进而获取冲突的房屋id
            conflict_orders_li = Order.query.filter(Order.begin_date <= end_date).all()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if conflict_orders_li:
        # 找到了冲突的订单信息, 就找到了冲突的房屋ID
        # conflict_house_id_list = [order.house_id for order in conflict_order_list]
        conflict_house_id_li = [order.house_id for order in conflict_orders_li]

        # 查询不冲突的房屋ID  House.query.filter(Houser.id.notin_([3,5,7]))
        filter_params.append(House.id.notin_(conflict_house_id_li))

    print 'filter_params=', filter_params

    # 3.5 排序
    # 不同的排序, 过滤条件不同
    # 排序将来可能是字符串或者是排序ID(排序ID更为多见)
    """
      <li class="active" sort-key="new">最新上线</li>
        <li sort-key="booking">入住最多</li>
        <li sort-key="price-inc">价格 低-高</li>
        <li sort-key="price-des">价格 高-低</li>
    """
    if sort_key == 'booking':
        # 创建查询条件语句（入住最多）
        house_query = House.query.filter(*filter_params).order_by(House.order_count.desc())
    elif sort_key == 'price-inc':
        # 创建查询条件语句(价格 低-高)
        house_query = House.query.filter(*filter_params).order_by(House.price.asc())
    elif sort_key == 'price-des':
        # 创建查询条件语句(价格 高-低)
        house_query = House.query.filter(*filter_params).order_by(House.price.desc())
    else:
        # 创建查询条件语句(最新上线)
        house_query = House.query.filter(*filter_params).order_by(House.create_time.desc())

    # 3.6 分页  sqlalchemy的分页
    # 在之前房屋的过滤条件后面, 使用paginate设置分页
    try:
        house_data = house_query.paginate(page, constants.HOUSE_LIST_PAGE_CAPACITY, False)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    # house_data.page  当前页码
    house_li = house_data.items  # 当前页码的数据内容
    total_page = house_data.pages  # 总页数

    # 3.7 将数据转为JSON
    houses = []
    for house in house_li:
        houses.append(house.to_basic_dict())

    # 将结果转换json字符串
    # 将整个响应结果封装. 而非值封装data
    resp = dict(errno=RET.OK, errmsg="查询成功",
                data={"houses": houses, "total_page": total_page, "current_page": page})
    resp_json = json.dumps(resp)

    # 3.8 将结果缓存到redis中
    # 用redis的哈希类型保存分页数据, 并使用事务提交保存
    if page <= total_page:
        # 用redis的哈希类型保存分页数据
        redis_key = "houses_%s_%s_%s_%s" % (start_date_str, end_date_str, area_id, sort_key)
        try:
            # 使用redis中的事务
            pipeline = redis_store.pipeline()
            # 开启事务
            pipeline.multi()
            pipeline.hset(redis_key, page, resp_json)
            pipeline.expire(redis_key, constants.HOUSE_LIST_PAGE_REDIS_EXPIRES)
            # 执行事务
            pipeline.execute()
        except Exception as e:
            logging.error(e)

            # 四. 数据返回
    return resp_json
