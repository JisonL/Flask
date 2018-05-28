import random

from flask import Blueprint, jsonify
from flask import current_app
from flask import make_response
from flask import request
from flask import session
from models import db, UserInfo

user_blueprint = Blueprint('user', __name__, url_prefix='/user')


@user_blueprint.route('/image_yzm')
def image_yzm():
    from utils.captcha.captcha import captcha
    name, yzm, image = captcha.generate_captcha()
    # yzm表示随机生成的验证码字符串
    # 将数据进行保存，方便方面对比
    session['image_yzm'] = yzm
    # image表示图片的二进制数据
    response = make_response(image)
    # 默认浏览器将数据作为text/html解析
    # 需要告诉浏览器当前数据的类型为image/png
    response.mimetype = 'image/png'
    return response


@user_blueprint.route('/sms_yzm')
def sms_yzm():
    from utils.ytx_sdk.ytx_send import sendTemplateSMS
    # 接受用户输入的短信和验证码
    dit1 = request.args
    mobile = dit1.get('mobile')
    yzm_img = dit1.get('yzm')
    if yzm_img.upper() != session['image_yzm'].upper():
        return jsonify(result=1)
    yzm_mob = random.randint(1111, 9999)
    # 将短信验证码保存
    session['sms_yzm'] = yzm_mob
    # 先不发
    # sendTemplateSMS(mobile, {yzm_mob, 5}, 1)
    print(yzm_mob)
    return jsonify(result=2)


@user_blueprint.route('/register', methods=['POST'])
def register():
    # 接收数据
    dict1 = request.form
    mobile = dict1.get('mobile')
    yzm_image = dict1.get('yzm_image')
    yzm_sms = dict1.get('yzm_sms')
    pwd = dict1.get('pwd')

    # 验证数据的有效性
    # 保证所有的数据都被填写,列表中只要有一个值为False,则结果为False
    if not all([mobile, yzm_image, yzm_sms, pwd]):
        return jsonify(result=1)
    # 对比图片验证码
    if yzm_image != session['image_yzm']:
        return jsonify(result=2)
    # 对比短信验证码,需要转换一下类型，因为http传送的都是字符串
    if int(yzm_sms) != session['sms_yzm']:
        return jsonify(result=3)
    # 判断密码的长度
    import re
    if not re.match(r'[a-zA-Z0-9_]{6,20}', pwd):
        return jsonify(result=4)
    # 验证mobile是否存在,用count判断数量判断是否有
    mobile_count = UserInfo.query.filter_by(mobile=mobile).count()
    if mobile_count > 0:
        return jsonify(result=5)

    # 创建对象
    user = UserInfo()
    # 默认昵称为手机号码
    user.nick_name = mobile
    user.mobile = mobile
    user.password = pwd

    # 提交到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except:
        current_app.logger_xjzx.error('用户注册期间访问数据库失败')
        return jsonify(result=7)

    # 返回相应
    return jsonify(result=6)


@user_blueprint.route('/login', methods=['POST'])
def login():
    # 接收数据
    dict1 = request.form
    mobile = dict1.get('mobile')
    pwd = dict1.get('pwd')

    # 验证有效性
    if not all([mobile, pwd]):
        return jsonify(result=1)
    # 查询判断、响应
    user = UserInfo.query.filter_by(mobile=mobile).first()

    # 判断mobile是否正确
    if user:
        # 进行密码对比，flask内部提供了密码加密、对比的函数
        if user.check_pwd(pwd):
            # 状态保持
            session['user_id'] = user.id
            # 返回成功的结果
            return jsonify(result=4, avatar=user.avatar, nick_name=user.nick_name)
        else:
            # 密码错误
            return jsonify(result=3)
    else:
        # 如果查询不到数据返回None，表示mobile错误
        return jsonify(result=2)


@user_blueprint.route('/logout', methods=['POST'])
def logout():
    del session['user_id']
    return jsonify(result=1)
