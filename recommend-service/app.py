from flask import Flask, request, jsonify
from models import db, Job
from sqlalchemy import or_

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='mysql+pymysql://root:Zzf0829.@mysql:3306/job_db'
db.init_app(app)

def parse_skills(s): return [x.strip().lower() for x in (s or '').split(',')]

@app.route('/recommend')
def recommend():
    kw=request.args.get('keyword','')
    q=Job.query
    if kw: q=q.filter(or_(Job.job_name.like(f"%{kw}%"),Job.skills.like(f"%{kw}%")))
    res=[]
    for j in q.limit(200):
        score=5+len(set(parse_skills(kw))&set(parse_skills(j.skills)))
        res.append({"job_name":j.job_name,"score":score})
    res.sort(key=lambda x:x['score'],reverse=True)
    return jsonify({"code":200,"data":res[:100]})
