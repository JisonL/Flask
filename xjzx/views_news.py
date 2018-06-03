from flask import Blueprint, render_template, jsonify
from flask import abort
from flask import request
from flask import session
from models import db, UserInfo, NewsCategory, NewsInfo

news_blueprint = Blueprint('news', __name__)


@news_blueprint.route('/')
def index():
    # 判断是否登录
    if 'user_id' in session:
        user = UserInfo.query.get(session['user_id'])
    else:
        user = None
    # 查询已经通过审核的，然后点击量高的前六个
    count_list = NewsInfo.query.filter_by(status=2).order_by(NewsInfo.click_count.desc())[0:6]

    category_list = NewsCategory.query.all()
    return render_template('news/index.html', user=user, category_list=category_list,count_list=count_list)


@news_blueprint.route('/newslist', methods=['POST', 'GET'])
def newslist():
    page = int(request.args.get('page', '1'))
    category_id = int(request.args.get('category_id','0'))
    if category_id:
        pagination = NewsInfo.query.filter_by(category_id=category_id).order_by(NewsInfo.update_time.desc()).paginate(page, 4, False)
    else:
        pagination = NewsInfo.query.order_by(NewsInfo.update_time.desc()).paginate(page, 4, False)
    # 拿取分页对象数据

    news_list = pagination.items

    news_list2 = []
    for news in news_list:
        dict1 = {
            'id': news.id,
            'pic': news.pic_url,
            'title': news.title,
            'summary': news.summary,
            'user_avatar': news.user.avatar_url,
            'user_nick_name': news.user.nick_name,
            'update_time': news.update_time.strftime('%Y-%m-%d'),
            'category_id': news.category_id
        }
        news_list2.append(dict1)
    return jsonify(news_list=news_list2)

@news_blueprint.route('/<int:news_id>')
def detail(news_id):
    news = NewsInfo.query.get(news_id)
    if news is None:
        abort(404)
    return render_template(
        'news/detail.html',
        news=news
    )
