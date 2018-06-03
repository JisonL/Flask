import re

from flask import Blueprint, make_response, jsonify
from flask import current_app
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from models import db, UserInfo,NewsInfo,NewsCategory



user_blueprint = Blueprint('user', __name__, url_prefix='/user')


@user_blueprint.route('/image_yzm')
def image_yzm():
    from utills.captcha.captcha import captcha
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
    # 接收数据：手机号，图片验证码
    dict1 = request.args
    mobile = dict1.get('mobile')
    yzm = dict1.get('yzm')

    # 对比图片验证码
    if yzm != session['image_yzm']:
        return jsonify(result=1)

    # 随机生成一个4位的验证码
    import random
    yzm2 = random.randint(1000, 9999)

    # 将短信验证码进行保存，用于验证
    session['sms_yzm'] = yzm2

    # 发送短信
    from utills.ytx_sdk.ytx_send import sendTemplateSMS
    # sendTemplateSMS(mobile,{yzm2,5},1)
    print(yzm2)

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
    # 对比短信验证码
    if int(yzm_sms) != session['sms_yzm']:
        return jsonify(result=3)
    # 判断密码的长度
    import re
    if not re.match(r'[a-zA-Z0-9_]{6,20}', pwd):
        return jsonify(result=4)
    # 验证mobile是否存在
    mobile_count = UserInfo.query.filter_by(mobile=mobile).count()
    if mobile_count > 0:
        return jsonify(result=5)

    # 创建对象
    user = UserInfo()
    user.nick_name = mobile
    user.mobile = mobile
    user.password = pwd

    # 提交到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except:
        current_app.logger_xjzx.error('用户注册访问数据库失败')
        return jsonify(result=7)

    # 返回响应
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
            return jsonify(result=4, avatar=user.avatar_url, nick_name=user.nick_name)
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


@user_blueprint.route('/show')
def show():
    if 'user_id' in session:
        return 'ok'
    else:
        return 'no'


@user_blueprint.route('/')
def index():
    user_id = session['user_id']
    user = UserInfo.query.get(user_id)

    return render_template('news/user.html', user=user)


import functools


def f1(f):
    @functools.wraps(f)
    def f2(*args, **kwargs):
        if 'user_id' in session:
            return f(*args, **kwargs)
        else:
            return redirect('/')

    return f2


@user_blueprint.route('/base', methods=['GET', 'POST'])
@f1
def base():
    user_id = session['user_id']
    user = UserInfo.query.get(user_id)
    if request.method == 'GET':
        return render_template('news/user_base_info.html', user=user)
    elif request.method == "POST":
        dict1 = request.form
        signature = dict1.get('signature')
        nick_name = dict1.get('nick_name')
        gender = dict1.get('gender')
        user.signature = signature
        user.nick_name = nick_name
        if gender == 'True':
            user.gender = True
        else:
            user.gender = False
        # 提交数据库
        db.session.commit()
        # 返回响应
        return jsonify(result=1)


@user_blueprint.route('/pic', methods=['POST', 'GET'])
@f1
def pic():
    user_id = session['user_id']
    user = UserInfo.query.get(user_id)
    if request.method == 'GET':
        return render_template('news/user_pic_info.html', user=user)
    elif request.method == 'POST':
        img = request.files.get('avatar')
        # print(img)
        # BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        # img.save(BASE_DIR + '/static/news/head/%d.jpg' % (user_id))
        user.avatar = img.filename
        db.session.commit()
        return jsonify(result=1, avatar=user.avatar_url)


@user_blueprint.route('/follow')
@f1
def follow():
    user_id = session['user_id']
    user = UserInfo.query.get(user_id)
    page = int(request.args.get('page', '1'))

    pagination = user.follow_user.paginate(page, 4, False)
    total_page = pagination.pages
    fol_list = pagination.items

    return render_template('news/user_follow.html', fol_list=fol_list, total_page=total_page, page=page)


@user_blueprint.route('/collect')
@f1
def collect():
    user_id = session['user_id']
    user = UserInfo.query.get(user_id)
    page = int(request.args.get('page', '1'))

    pagination = user.news_collect.paginate(page, 5, False)
    total_page = pagination.pages
    news_list = pagination.items
    return render_template('news/user_collection.html',news_list=news_list, total_page=total_page, page=page)


@user_blueprint.route('/pwd',methods=['GET', 'POST'])
@f1
def pwd():
    user_id = session['user_id']
    user = UserInfo.query.get(user_id)

    if request.method == 'GET':
        return render_template('news/user_pass_info.html')

    elif request.method == 'POST':
        current_psw = request.form.get('current_psw')
        new_psw = request.form.get('new_psw')
        conf_psw = request.form.get('conf_psw')

        # 进行数据判别
        if not all([current_psw,new_psw,conf_psw]):
            return render_template('news/user_pass_info.html',msg='请将信息填写完成')
        if new_psw == conf_psw:
            if not re.match(r'[0-9a-zA-Z]{6,20}',new_psw):
                return render_template('news/user_pass_info.html', msg='密码格式不正确')
        else:
            return render_template('news/user_pass_info.html',msg='两次密码不一致')

        # 查询数据库密码并进行对比
        if user.check_pwd(current_psw):
            return render_template('news/user_pass_info.html', msg='当前密码错误')

        user.password = new_psw
        db.session.commit()
        return render_template('news/user_pass_info.html')


@user_blueprint.route('/newslist')
@f1
def newslist():
    user_id = session['user_id']
    user = UserInfo.query.get(user_id)
    page = int(request.args.get('page', '1'))

    pagination = user.news.order_by(NewsInfo.update_time.desc()).paginate(page, 6, False)
    total_page = pagination.pages
    news_list = pagination.items
    # print(news_list)

    return render_template('news/user_news_list.html',news_list=news_list, total_page=total_page, page=page)


@user_blueprint.route('/release', methods=['GET', 'POST'])
@f1
def release():
    category_list = NewsCategory.query.all()
    if request.method == 'GET':
        return render_template('news/user_news_release.html', category_list=category_list)
    elif request.method == 'POST':
        # 接收用户输入的数据
        dict1 = request.form
        title = dict1.get('title')
        category_id = int(dict1.get('category'))
        summary = dict1.get('summary')
        content = dict1.get('content')
        # 接收文件
        news_pic = request.files.get('pic')

        if not all([title,category_id,summary,content]):
            return render_template('news/user_news_release.html', category_list=category_list,msg='数据不能为空')
        news = NewsInfo()
        news.pic = news_pic.filename
        news.title = title
        news.category_id = category_id
        news.summary=summary
        news.content=content
        news.user_id = session['user_id']

        db.session.add(news)
        db.session.commit()
        # 提交完转到文章列表
        return redirect('/user/newslist')


@user_blueprint.route('/modify/<int:news_id>', methods=['GET', 'POST'])
def modify(news_id):
    news = NewsInfo.query.get(news_id)
    category_list = NewsCategory.query.all()
    if request.method == 'GET':
        return render_template('news/news_update.html', category_list=category_list,news=news)
    elif request.method == 'POST':
        # 接收用户输入的数据
        dict1 = request.form
        title = dict1.get('title')
        category_id = int(dict1.get('category'))
        summary = dict1.get('summary')
        content = dict1.get('content')
        # 接收文件
        news_pic = request.files.get('pic')

        if not all([title, category_id, summary, content]):
            return render_template('news/user_news_release.html', category_list=category_list, msg='数据不能为空')
        news = NewsInfo()

        news.pic = news_pic.filename
        news.title = title
        news.category_id = category_id
        news.summary = summary
        news.content = content
        news.user_id = session['user_id']
        db.session.commit()
        # 提交完转到文章列表
        return redirect('/user/newslist')


