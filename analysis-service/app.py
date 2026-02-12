from flask import Flask, jsonify
from models import db, Job

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='mysql+pymysql://root:Zzf0829.@mysql:3306/job_db'
db.init_app(app)

@app.route('/city')
def city():
    jobs = db.session.query(Job.city, Job.salary_min).all()
    stats={}
    for c,s in jobs:
        if not c: continue
        c=c.replace('·','-').split('-')[0]
        stats.setdefault(c,{'count':0,'sum':0})
        stats[c]['count']+=1
        stats[c]['sum']+=s or 0
    data=[{"name":k,"value":v['count'],"avg_salary":int(v['sum']/v['count'])} for k,v in stats.items()]
    data.sort(key=lambda x:x['value'],reverse=True)
    return jsonify({"code":200,"data":data[:15]})
