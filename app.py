from threading import Thread
from flask import Flask, jsonify, request
from models import db, Job, User, UserProfile, BrowseHistory
import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from spider import run_spider_task, spider_status
from sqlalchemy import or_
import logging
from flask_cors import CORS


# ==========================================
# 日志过滤器配置
# ==========================================
class StatusFilter(logging.Filter):
    def filter(self, record):
        return '/api/spider/status' not in record.getMessage()


log = logging.getLogger('werkzeug')
log.addFilter(StatusFilter())

# ==========================================
# App 初始化
# ==========================================
app = Flask(__name__)

# 🔥【核心修复 1】使用最宽松的 CORS 配置，允许所有来源访问
CORS(app, supports_credentials=True)


# 🔥【核心修复 2】手动强行注入请求头 (双重保险)
@app.after_request
def after_request(response):
    # 允许所有域名访问
    response.headers['Access-Control-Allow-Origin'] = '*'
    # 允许的请求头
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    # 允许的请求方法
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    return response


# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Zzf0829.@127.0.0.1:3306/job_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'my_secret_key_666'

db.init_app(app)


# ==========================================
# 接口区域
# ==========================================

@app.route('/api/hello', methods=['GET'])
def hello_world():
    return jsonify({"message": "后台运行正常！", "status": 200})


# 统计分析接口
@app.route('/api/analysis/city', methods=['GET'])
def get_city_analysis():
    try:
        # ==========================================
        # 1. 计算全局统计数据
        # ==========================================

        real_total_jobs = Job.query.count()

        # 计算真实平均薪资
        all_salaries = db.session.query(Job.salary_min).filter(Job.salary_min > 0).all()
        real_avg_salary = 0
        if all_salaries and len(all_salaries) > 0:
            total_sum = sum([s[0] for s in all_salaries if s[0] is not None])
            real_avg_salary = int(total_sum / len(all_salaries))

        # ==========================================
        # 2. 图表数据处理 (城市清洗核心逻辑)
        # ==========================================
        jobs = db.session.query(Job.city, Job.salary_min).all()
        city_stats = {}

        for j_city, j_salary in jobs:
            if not j_city: continue

            # 1. 把各种奇怪的分隔符 (·, 空格, _) 都替换成减号 -
            # 2. 然后再用 - 分割，取第一个
            # 例子: "武汉·东湖" -> "武汉-东湖" -> "武汉"
            clean_city = j_city.replace('·', '-').replace(' ', '-').replace('_', '-')
            simple_city = clean_city.split('-')[0]

            # 统计逻辑
            if simple_city not in city_stats:
                city_stats[simple_city] = {'count': 0, 'salary_sum': 0}

            city_stats[simple_city]['count'] += 1
            if j_salary and j_salary > 0:
                city_stats[simple_city]['salary_sum'] += j_salary

        # 3. 真实城市覆盖数 (清洗后的去重数量)
        real_total_cities = len(city_stats)

        # 转换为图表列表
        chart_data = []
        for city_name, stats in city_stats.items():
            avg_sal = 0
            if stats['count'] > 0:
                avg_sal = int(stats['salary_sum'] / stats['count'])

            chart_data.append({
                "name": city_name,
                "value": stats['count'],
                "avg_salary": avg_sal
            })


        # 排序取前 15
        chart_data.sort(key=lambda x: x['value'], reverse=True)

        return jsonify({
            "code": 200,
            "msg": "查询成功",
            "data": chart_data[:15],
            "report": {
                "total_jobs": real_total_jobs,
                "total_cities": real_total_cities,
                "avg_salary": real_avg_salary
            }
        })

    except Exception as e:
        print(f"❌ 统计接口报错: {e}")
        return jsonify({"code": 500, "msg": str(e), "data": []})


# 辅助函数
def parse_skills(skill_str):
    if not skill_str: return []
    return [s.strip().lower() for s in skill_str.replace('，', ',').split(',')]


def parse_edu_level(edu_text):
    edu_text = str(edu_text)
    if '博士' in edu_text: return 4
    if '硕士' in edu_text: return 3
    if '本科' in edu_text: return 2
    if '大专' in edu_text: return 1
    return 0


# 推荐接口
@app.route('/api/recommend', methods=['GET'])
def recommend_jobs():
    user_id = request.args.get('user_id', '')
    keyword = request.args.get('keyword', '').strip()
    target_city = request.args.get('city', '')
    target_skill = request.args.get('skill', '')
    target_salary = request.args.get('salary', 0, type=int)
    target_exp = request.args.get('experience', '')
    target_edu = request.args.get('education', '')

    # 如果用户登录了，把他的搜索偏好存入 UserProfile 表
    if user_id:
        try:
            # 1. 先查有没有这个人的画像
            profile = UserProfile.query.filter_by(user_id=user_id).first()

            # 2. 如果没有，就新建一个
            if not profile:
                profile = UserProfile(user_id=user_id)
                db.session.add(profile)

            # 3. 智能更新 (只有当用户传了值的时候才更新，传空值不覆盖原有的偏好)
            # 这样用户如果只搜了 "Python" 没选城市，之前的 "上海" 偏好还会保留
            if target_city:
                profile.expect_city = target_city

            if target_skill:
                # 简单的追加或覆盖逻辑，这里演示覆盖，代表“最新兴趣”
                profile.expect_skills = target_skill

            if target_salary and target_salary > 0:
                profile.expect_salary = target_salary

            # 更新最后修改时间
            profile.update_time = datetime.now()

            db.session.commit()
            # print(f"✅ 画像已动态修正: {profile.expect_city} | {profile.expect_skills}")

        except Exception as e:
            db.session.rollback()
            # print(f"画像更新忽略错误: {e}")

    try:
        query = Job.query
        if keyword:
            query = query.filter(or_(Job.job_name.like(f"%{keyword}%"), Job.skills.like(f"%{keyword}%")))
        if target_city:
            query = query.filter(Job.city.like(f"%{target_city}%"))

        candidates = query.all()
        user_skills = parse_skills(target_skill)
        if keyword: user_skills.append(keyword.lower())

        results = []
        for job in candidates:
            score = 0
            match_reasons = []
            job_skills = parse_skills(job.skills)

            if keyword:
                score = 5.0 if keyword in job.job_name else 4.0
            else:
                score = 5.0

            if user_skills and job_skills:
                matched = set(user_skills) & set(job_skills)
                if matched:
                    score += min(len(matched) * 1.5, 4.5)
                    match_reasons.append(f"技能: {','.join(list(matched)[:3])}")

            if target_salary and job.salary_max and job.salary_max >= target_salary:
                score += 1.0

            score = min(score, 10.0)

            results.append({
                "id": job.id, "job_name": job.job_name, "company": job.company,
                "salary": job.salary, "city": job.city, "experience": job.experience,
                "education": job.education, "skills": job.skills, "score": round(score, 1),
                "detail_url": job.detail_url, "match_reasons": match_reasons
            })

        results.sort(key=lambda x: (x['score'], x['salary']), reverse=True)
        return jsonify({"code": 200, "msg": "ok", "data": results[:100]})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e), "data": []})


@app.route('/api/cities', methods=['GET'])
def get_city_list():
    try:
        # 查询数据库中所有城市
        raw_cities = db.session.query(Job.city).distinct().all()

        # 使用 set 集合进行去重 (因为清洗后 "武汉-洪山" 和 "武汉·东湖" 都会变成 "武汉")
        clean_city_set = set()

        for c in raw_cities:
            if c[0]:
                # 🔥 同样的清洗逻辑
                clean_name = c[0].replace('·', '-').replace(' ', '-').replace('_', '-').split('-')[0]
                clean_city_set.add(clean_name)

        # 转回列表并排序
        city_list = sorted(list(clean_city_set))

        return jsonify({
            "code": 200,
            "msg": "查询成功",
            "data": city_list
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"查询失败: {str(e)}",
            "data": []
        })


@app.route('/api/skills', methods=['GET'])
@app.route('/api/skills', methods=['GET'])
def skill_list():
    try:
        all_jobs = Job.query.all()
        skill_set = set()

        # 定义“福利/非技能”黑名单
        # 只要包含这些字，统统不要
        blacklist_keywords = [
            "险", "金", "假", "补", "休", "餐", "房", "游", "检", "节", "包",
            "奖", "红", "薪", "权", "票", "晋", "训", "队", "车", "费",
            "医疗", "子女", "弹性", "氛围", "扁平", "零食", "下午茶", "生日",
            "五险", "社保", "双休", "周末", "全勤", "年底", "年终", "定期",
            "免费", "交通", "通讯", "采暖", "高温", "带薪", "无责任", "底薪",
            "提成", "绩效", "补助", "津贴", "福利", "待遇", "环境", "老板",
            "nice", "NICE", "Nice", "美女", "帅哥", "团建", "旅游"
        ]

        for job in all_jobs:
            if job.skills:
                # 拆分技能
                raw_skills = [s.strip() for s in job.skills.replace('，', ',').split(',')]

                for s in raw_skills:
                    # 1. 长度过滤 (太长的通常是废话，比如 '团队氛围好')
                    # 技能通常很短，比如 'Java', 'Spring Boot'
                    if len(s) > 15 or len(s) < 2:
                        continue

                    # 2. 关键词黑名单过滤
                    is_bad = False
                    for bad in blacklist_keywords:
                        if bad in s:
                            is_bad = True
                            break

                    if not is_bad:

                        skill_set.add(s.title())

        # 排序后返回
        return jsonify({"code": 200, "msg": "ok", "data": sorted(list(skill_set))})

    except Exception as e:
        return jsonify({"code": 500, "msg": f"查询失败: {str(e)}", "data": []})


@app.route('/api/spider/start', methods=['POST'])
def start_spider_api():
    data = request.json
    keyword = data.get('keyword', '')
    city = data.get('city', '')  # 🔥 接收城市参数

    if not keyword: return jsonify({"code": 400, "msg": "无关键字"})
    if spider_status['is_running']: return jsonify({"code": 400, "msg": "运行中"})

    def thread_task(app_context, kw, ct):  # 🔥 增加参数 ct (city)
        with app_context:
            # 传递给爬虫函数
            run_spider_task(kw, ct, target_pages=2)

    # 启动线程时带上 city
    t = Thread(target=thread_task, args=(app.app_context(), keyword, city))
    t.start()

    return jsonify({"code": 200, "msg": "started"})


@app.route('/api/spider/status', methods=['GET'])
def get_spider_status():
    return jsonify({"code": 200, "data": spider_status})


# 注册接口
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"code": 400, "msg": "空"})
    if User.query.filter_by(username=username).first():
        return jsonify({"code": 400, "msg": "已存在"})
    new_user = User(username=username, password=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"code": 200, "msg": "ok"})


# 登录接口
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        token = jwt.encode({'user_id': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
                           app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({
            "code": 200,
            "msg": "ok",
            "token": token,
            "username": username,
            "user_id": user.id
        })
    return jsonify({"code": 401, "msg": "error"})


# “记录浏览历史”接口
@app.route('/api/history', methods=['POST'])
def add_history():
    """前端点击卡片时调用此接口"""
    data = request.json
    user_id = data.get('user_id')
    job_id = data.get('job_id')

    if not user_id or not job_id:
        return jsonify({"code": 400, "msg": "参数错误"})

    try:
        # 记录一条历史
        history = BrowseHistory(user_id=user_id, job_id=job_id, view_time=datetime.datetime.now())
        db.session.add(history)
        db.session.commit()
        return jsonify({"code": 200, "msg": "已记录浏览历史"})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})

if __name__ == '__main__':
    # 注意：这里也开启了 debug 模式
    app.run(debug=True, port=5000)