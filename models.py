from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# 1. 用户表 (User) - 基础鉴权
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)
    # 关联
    profile = db.relationship('UserProfile', backref='user', uselist=False)

# 2. 用户画像表 (UserProfile) - 推荐算法核心 (基于内容)
class UserProfile(db.Model):
    __tablename__ = 'user_profile'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    expect_city = db.Column(db.String(50))
    expect_salary = db.Column(db.Integer)
    expect_skills = db.Column(db.String(255))
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

# 3. 岗位表 (Job) - 核心数据资产
class Job(db.Model):
    __tablename__ = 'job'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    job_name = db.Column(db.String(100), nullable=False)
    salary = db.Column(db.String(50))
    salary_min = db.Column(db.Integer)
    salary_max = db.Column(db.Integer)
    city = db.Column(db.String(50))
    education = db.Column(db.String(50))
    experience = db.Column(db.String(50))
    skills = db.Column(db.Text)
    company = db.Column(db.String(100))
    detail_url = db.Column(db.String(255))
    create_time = db.Column(db.DateTime, default=datetime.now)
    hash = db.Column(db.String(64))

# 4. 收藏表
class Favorite(db.Model):
    __tablename__ = 'favorite'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))
    create_time = db.Column(db.DateTime, default=datetime.now)

# 5. 浏览历史表 (BrowseHistory) - 隐式反馈 (Implicit Feedback)
# 作用：记录用户看过了哪些岗位，用于优化推荐，且能展示“足迹”功能
class BrowseHistory(db.Model):
    __tablename__ = 'browse_history'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))
    view_time = db.Column(db.DateTime, default=datetime.now) # 浏览时间

# 6. 分析结果缓存表 (AnalysisResult) - 性能优化
# 作用：每天半夜算一次全站的平均薪资、词云数据，存到这里。
# 前端请求时，直接从这里取JSON，速度快100倍。
class AnalysisResult(db.Model):
    __tablename__ = 'analysis_result'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(50))  # 类型：例如 'city_salary_avg', 'skill_cloud'
    result_json = db.Column(db.Text)  # 存算好的 JSON 字符串
    create_time = db.Column(db.DateTime, default=datetime.now)


































