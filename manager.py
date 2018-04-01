# -*- coding:utf-8 -*-
# manger文件主要管理文件启动: config配置/app创建/路由实现都不需要关心
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from ihome import create_app
from config import DevelopmentConfig, ProductionConfig

# 程序的启动是调试模式,还是发布模式, 我们也希望由manager文件来管理
app, db = create_app(DevelopmentConfig)

manager = Manager(app)

Migrate(app, db)

manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    print app.url_map
    manager.run()
