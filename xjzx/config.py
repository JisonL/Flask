class Config(object):
    DEBUG=False
    SQLALCHEMY_DATABASE_URI='mysql://root:hellopython@localhost:3306/my_pro'
    SQLALCHEMY_TRACK_MODIFICATIONS=True

# 开发时配置
class DevelopConfig(Config):
    DEBUG = True
