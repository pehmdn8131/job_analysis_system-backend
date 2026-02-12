from flask import Flask, request, jsonify
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
import jwt, datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Zzf0829.@mysql:3306/job_db'
app.config['SECRET_KEY'] = 'secret'
db.init_app(app)

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"msg":"exists"}),400
    u = User(username=data['username'],password=generate_password_hash(data['password']))
    db.session.add(u); db.session.commit()
    return jsonify({"msg":"ok"})

@app.route('/login', methods=['POST'])
def login():
    u = User.query.filter_by(username=request.json['username']).first()
    if u and check_password_hash(u.password, request.json['password']):
        token = jwt.encode({'uid':u.id,'exp':datetime.datetime.utcnow()+datetime.timedelta(hours=24)},
                           app.config['SECRET_KEY'],algorithm='HS256')
        return jsonify({"token":token})
    return jsonify({"msg":"error"}),401
