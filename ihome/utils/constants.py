# -*- coding:utf-8 -*-

IMAGE_CODE_REDIS_EXPIRE = 180  # 图片验证码redis保存的有效期，单位秒

IMAGE_CODE_YTX_EXPIRE = '5'  # 图片验证码redis保存的有效期，单位秒

SMS_CODE_REDIS_EXPIRE = 300  # 短信验证码redis保存的有效期，单位秒

QINIU_URL_DOMAIN = "http://p6lb5gox3.bkt.clouddn.com/"  # 七牛的访问域名(改成自己的)

LOGIN_ERROR_MAX_NUM = 5  # 登录的最大错误次数

LOGIN_ERROR_FORBID_TIME = 86400  # 登录错误封ip的时间，单位：秒

AREA_INFO_REDIS_EXPIRES = 3600  # 城区信息的redis缓存时间， 单位：秒

HOME_PAGE_MAX_HOUSES = 5  # 首页展示最多的房屋数量

HOME_PAGE_DATA_REDIS_EXPIRES = 7200  # 首页房屋数据的Redis缓存时间，单位：秒

HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS = 30  # 房屋详情页展示的评论最大数

HOUSE_DETAIL_REDIS_EXPIRE_SECOND = 7200  # 房屋详情页面数据Redis缓存时间，单位：秒

HOUSE_LIST_PAGE_CAPACITY = 2  # 房屋列表页面每页的数量

HOUSE_LIST_PAGE_REDIS_EXPIRES = 3600  # 房屋列表页面数据Redis缓存时间
