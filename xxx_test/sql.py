# -*- coding:utf-8 -*-

'''

导入所有代码
In [1]: from demo3_sqlalchemy import *

添加数据
In [2]: role = Role(name='guanliyuan')
In [3]: db.session.add(role)
In [4]: db.session.commit()

修改数据
In [5]: role.name='admin'
In [6]: db.session.commit()

删除数据
In [7]: db.session.delete(role)
In [8]: db.session.commit()

回滚数据
In [9]: role = Role(name='admin')
In [10]: db.session.add(role)
In [11]: db.session.rollback()
In [12]: db.session.commit()
如果回滚了, 需要重新添加
In [13]: db.session.add(role)
In [14]: db.session.commit()

回滚是回顾未提交之前的所有操作
In [15]: role = Role(name='admin')
In [16]: role2 = Role(name='user')
In [17]: db.session.add(role)
In [18]: db.session.add(role2)
In [19]: db.session.rollback()
In [20]: db.session.commit()

'''


'''
验证关系引用

先退出ipython, 重启项目, 来清空数据库表内容


In [1]: from demo3_sqlalchemy import * 

添加一个角色
In [2]: role = Role(name='admin')
In [3]: db.session.add(role)
In [4]: db.session.commit()

添加2个用户
In [5]: user1 = User(name='zs', role_id=role.id)
In [6]: user2 = User(name='ls', role_id=role.id)
In [7]: db.session.add_all([user1, user2])
In [9]: db.session.commit()


关系引用及反向引用的用法实现
In [11]: role.users
Out[11]: [<User: zs 1 None None>, <User: ls 2 None None>]

In [12]: user1.role
Out[12]: <Role: admin 1>
In [13]: user1.role.name
Out[13]: u'admin'

'''


'''
1. 查询所有用户数据
User.query.all()

2. 查询有多少个用户
User.query.count()

3. 查询第1个用户
User.query.first()

4. 查询id为4的用户[3种方式]
User.query.get(4)
User.query.filter(User.id==4).first()
User.query.filter_by(id=4).first()

filter(模型名.属性名==数据)
filter_by(属性名=数据)
filter比filter_by功能更强大. 基本查询用谁都行. filter支持比较运算符

5. 查询名字结尾字符为g的所有数据[开始/包含]
User.query.filter(User.name.endswith('g')).all()
User.name.startswith
User.name.contains

6. 查询名字不等于wang的所有数据[2种方式]
from sqlalchemy import not_
User.query.filter(not_(User.name=='wang')).all()

User.query.filter(User.name!='wang').all()


7. 查询名字和邮箱都以 li 开头的所有数据[2种方式]
from sqlalchemy import and_
User.query.filter(and_(User.name.startswith('li'), User.email.startswith('li'))).all()

User.query.filter(User.name.startswith('li'), User.email.startswith('li')).all()


8. 查询password是 `123456` 或者 `email` 以 `itheima.com` 结尾的所有数据
User.query.filter(or_(User.password=='123456', User.email.endswith('itheima.com'))).all()


9. 查询id为 [1, 3, 5, 7, 9] 的用户列表
User.query.filter(User.id.in_([1, 3, 5, 7, 9])).all()


10. 查询name为liu的角色数据
关系引用
User.query.filter(User.name=='liu').first().role.name


11. 查询所有用户数据，并以邮箱排序
排序
User.query.order_by('email').all()

12. 查询第2页的数据, 每页只显示3条数据
排序
需要3个参数( 第几页, 分页的数量条件, 如果失败了是否要返回404错误 )
data = User.query.paginate(2, 3, False)
data.items 获取所有的查询数据
data.page 获取当前页数
data.pages 获取总页数
'''